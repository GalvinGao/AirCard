import contextlib
import hashlib
import io
import json
from pathlib import Path
import sys
import tempfile
import unittest
from unittest.mock import patch

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
import card_backup as backup
import aircard_backend as backend


def ok(**values):
    return {'exitCode': 0, 'targetGatePassed': True, 'operation': {'ok': True, **values}}


class BackupTests(unittest.TestCase):
    def setUp(self):
        self.temporary = tempfile.TemporaryDirectory()
        self.root = Path(self.temporary.name)
        self.patch = patch.object(backup, 'BACKUP_ROOT', self.root)
        self.patch.start()
        self.addCleanup(self.patch.stop)
        self.addCleanup(self.temporary.cleanup)

    def snapshot(self, udid, card, destination):
        destination.mkdir(parents=True)
        files = {}
        for name in backup.ASSETS:
            present = not name.endswith('.pdf')
            files[name] = {'present': present}
            if present:
                data = b'original:' + name.encode()
                (destination / name).write_bytes(data)
                files[name].update(size=len(data), sha256=backup.digest(data))
        return files

    def create_backup(self):
        with patch.object(backup, 'snapshot_files', side_effect=self.snapshot):
            return backup.backup_card('device', 'card')

    def test_bytes_absence_and_distinct_snapshots(self):
        first, second = self.create_backup(), self.create_backup()
        self.assertNotEqual(first, second)
        manifest, payloads = backup.load_backup('device', first)
        self.assertEqual(len(payloads), 2)
        self.assertFalse(manifest['files'][backup.ASSETS[2]]['present'])
        self.assertEqual(payloads[backup.ASSETS[0]], b'original:' + backup.ASSETS[0].encode())

    def test_corrupt_backup_rejected_before_restore_writes(self):
        path = self.create_backup()
        (path.parent / backup.ASSETS[0]).write_bytes(b'damaged')
        with patch.object(backup, 'write_file') as write, patch.object(backup, 'backup_card') as snapshot:
            with self.assertRaisesRegex(ValueError, 'checksum'):
                backup.restore_card('device', path)
            write.assert_not_called()
            snapshot.assert_not_called()

    def test_wrong_device_and_unsafe_card_are_rejected(self):
        path = self.create_backup()
        with self.assertRaisesRegex(ValueError, 'device'):
            backup.load_backup('another-device', path)
        for card in ['../Preferences', 'card/file', '']:
            with self.assertRaises(ValueError):
                backup.card_directory(card)

    def test_incomplete_manifest_rejected(self):
        path = self.create_backup()
        manifest = json.loads(path.read_text())
        del manifest['files'][backup.ASSETS[0]]
        path.write_text(json.dumps(manifest))
        with self.assertRaisesRegex(ValueError, 'incomplete'):
            backup.load_backup('device', path)

    def test_backup_failure_blocks_flash(self):
        image = self.root / 'image.png'
        image.write_bytes(b'png')
        with patch.object(backend, 'device_lock', return_value=contextlib.nullcontext()), \
             patch.object(backend, 'prepare_card_assets', return_value={}), \
             patch.object(backend, 'backup_card', side_effect=RuntimeError('permission denied')), \
             patch.object(backend, 'write_file') as write, contextlib.redirect_stdout(io.StringIO()) as output:
            self.assertFalse(backend.cmd_flash('device', 'card', str(image)))
            write.assert_not_called()
            self.assertNotIn('"type": "success"', output.getvalue())

    def test_flash_never_writes_an_unverified_asset(self):
        image = self.root / 'image.png'
        image.write_bytes(b'png')
        files = {name: {'present': True if name == backup.ASSETS[1] else None} for name in backup.ASSETS}
        with patch.object(backend, 'device_lock', return_value=contextlib.nullcontext()), \
             patch.object(backend, 'prepare_card_assets', return_value={n: b'new' for n in backup.ASSETS}), \
             patch.object(backend, 'backup_card', return_value=Path('/backup/manifest.json')), \
             patch.object(backend, 'load_backup', return_value=({'files': files}, {})), \
             patch.object(backend, 'write_file', return_value=True) as write, \
             contextlib.redirect_stdout(io.StringIO()) as output:
            self.assertTrue(backend.cmd_flash('device', 'card', str(image)))
        artwork_calls = [c for c in write.call_args_list if c.args[1].endswith('.pkpass')]
        self.assertEqual([c.args[2] for c in artwork_calls], [backup.ASSETS[1]])
        self.assertIn('Leaving unverified artwork untouched', output.getvalue())

    def test_no_readable_artwork_blocks_backup(self):
        with patch.object(backup, 'snapshot_files', return_value={n: {'present': False} for n in backup.ASSETS}):
            with self.assertRaisesRegex(RuntimeError, 'No recognized'):
                backup.backup_card('device', 'card')

    def test_restore_verifies_and_removes_previously_absent_asset(self):
        original = self.create_backup()
        current = self.create_backup()
        manifest = json.loads(current.read_text())
        data = b'new PDF'
        (current.parent / backup.ASSETS[2]).write_bytes(data)
        manifest['files'][backup.ASSETS[2]] = {'present': True, 'size': len(data), 'sha256': backup.digest(data)}
        current.write_text(json.dumps(manifest))
        original_files = json.loads(original.read_text())['files']
        with patch.object(backup, 'backup_card', return_value=current), \
             patch.object(backup, 'write_file', return_value=True) as write, \
             patch.object(backup, 'card_access', return_value=contextlib.nullcontext('link')), \
             patch.object(backup, 'native', return_value=ok()) as native, \
             patch.object(backup, 'snapshot_files', return_value=original_files):
            self.assertEqual(backup.restore_card('device', original), current)
            native.assert_called_once_with('remove-card-artwork', 'device', 'link', backup.ASSETS[2])
            self.assertEqual(len(write.call_args_list), 8)

    def test_restore_readback_mismatch_is_failure(self):
        original = self.create_backup()
        with patch.object(backup, 'backup_card', return_value=original), \
             patch.object(backup, 'write_file', return_value=True), \
             patch.object(backup, 'snapshot_files', return_value={}):
            with self.assertRaisesRegex(RuntimeError, 'did not verify'):
                backup.restore_card('device', original)

    def test_device_lock_prevents_parallel_writers(self):
        with backup.device_lock('device'):
            with self.assertRaisesRegex(RuntimeError, 'Another artwork'):
                with backup.device_lock('device'):
                    pass

    def test_interrupted_session_recovered_before_next_operation(self):
        work = backup.device_root('device') / 'sessions' / ('a' * 20)
        work.mkdir(parents=True)
        (work / 'pending.json').write_text('{}')
        with patch.object(backup, 'native', return_value=ok()) as native:
            with backup.device_lock('device'):
                self.assertFalse((work / 'pending.json').exists())
            self.assertEqual(native.call_args.args[0], 'finish-write')

    def test_failed_recovery_retains_journal_and_blocks_operation(self):
        work = backup.device_root('device') / 'sessions' / ('b' * 20)
        work.mkdir(parents=True)
        pending = work / 'pending.json'
        pending.write_text('{}')
        with patch.object(backup, 'native', return_value={}):
            with self.assertRaisesRegex(RuntimeError, 'Session retained'):
                with backup.device_lock('device'):
                    self.fail('Recovery must block the operation')
        self.assertTrue(pending.exists())

    def test_link_session_is_cleaned_after_read_exception(self):
        with patch.object(backup, 'native', return_value=ok()) as native, \
             patch.object(backup, 'run_json', return_value={'exitCode': 0, 'ok': True}):
            with self.assertRaisesRegex(RuntimeError, 'read failure'):
                with backup.card_access('device', 'card'):
                    raise RuntimeError('read failure')
        self.assertEqual(native.call_args.args[0], 'finish-write')
        self.assertFalse(list(self.root.glob('**/pending.json')))

    def test_denied_directory_read_is_not_missing_artwork(self):
        with patch.object(backup, 'card_access', return_value=contextlib.nullcontext('link')), \
             patch.object(backup, 'native', return_value={'operation': {'ok': False, 'status': 8, 'error': 'denied'}}), \
             patch.object(backup, 'indirect_snapshot') as indirect:
            with self.assertRaisesRegex(RuntimeError, 'overwrite blocked'):
                backup.snapshot_files('device', 'card', self.root / 'snapshot')
            indirect.assert_not_called()


class IndirectBackupTests(unittest.TestCase):
    setUp = BackupTests.setUp
    def test_moves_return_original_and_unavailable_files_stay_unknown(self):
        token = 'c' * 20
        work = backup.device_root('device') / 'sessions' / token
        work.mkdir(parents=True)
        (work / 'pending.json').write_text(json.dumps({'card': 'card'}))
        destination = self.root / 'artwork'
        destination.mkdir()
        recovered = {}
        originals = {backup.ASSETS[0]: b'original PNG', backup.ASSETS[2]: b'original PDF'}
        expected = dict(originals)

        def move(udid, folder, identifier, target):
            if target.startswith('airlift-recovered-'):
                name = identifier.rsplit('/', 1)[-1]
                if name in originals:
                    recovered['bytes'] = originals.pop(name)
            else:
                originals[target.rsplit('/', 1)[-1]] = recovered.pop('bytes')

        def native(command, udid, *args):
            if command == 'recovered-state':
                return ok(present='bytes' in recovered)
            if command == 'read-recovered':
                if 'bytes' not in recovered:
                    return ok(present=False)
                Path(args[1]).write_bytes(recovered['bytes'])
                return ok(present=True, size=len(recovered['bytes']))
            raise AssertionError(command)

        with patch.object(backup, 'sync_move', side_effect=move), patch.object(backup, 'native', side_effect=native):
            files = backup.indirect_snapshot('device', 'card', 'airlift-link-' + token, destination)
        self.assertEqual(originals, expected)
        self.assertFalse(recovered)
        self.assertIsNone(files[backup.ASSETS[1]]['present'])
        self.assertIsNone(json.loads((work / 'pending.json').read_text())['active_leaf'])

    def test_stranded_original_returned_before_cleanup(self):
        work = backup.device_root('device') / 'sessions' / ('d' * 20)
        work.mkdir(parents=True)
        (work / 'pending.json').write_text(json.dumps({'card': 'card', 'active_leaf': backup.ASSETS[0], 'move_uncertain': True}))
        states = [ok(present=True), ok(present=False), ok()]
        with patch.object(backup, 'native', side_effect=states), patch.object(backup, 'sync_move') as move:
            backup.cleanup_session('device', work)
        self.assertEqual(move.call_args.args[-1], 'airlift-link-' + work.name + '/' + backup.ASSETS[0])
        self.assertFalse((work / 'pending.json').exists())

    def test_failed_return_keeps_original_and_journal(self):
        work = backup.device_root('device') / 'sessions' / ('e' * 20)
        work.mkdir(parents=True)
        pending = work / 'pending.json'
        pending.write_text(json.dumps({'card': 'card', 'active_leaf': backup.ASSETS[0]}))
        with patch.object(backup, 'native', return_value=ok(present=True)) as native, \
             patch.object(backup, 'sync_move', side_effect=RuntimeError('disconnected')):
            with self.assertRaisesRegex(RuntimeError, 'disconnected'):
                backup.cleanup_session('device', work)
        self.assertTrue(pending.exists())
        self.assertFalse(any(call.args[0] == 'finish-write' for call in native.call_args_list))
