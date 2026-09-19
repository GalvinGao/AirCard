"""Verified Wallet artwork backups with journaled recovery of temporary moves."""
from contextlib import contextmanager
from datetime import datetime, timezone
import fcntl
import hashlib
import json
import os
import posixpath
from pathlib import Path
import re
import secrets

from apply_card_skin import (
    AIRTRAFFIC_HOST, AIRLOCK_ROOT, build_archive, build_books, native, operation_ok,
    run_json, write_file,
)

ASSETS = ("cardBackgroundCombined@3x.png", "cardBackgroundCombined@2x.png",
          "cardBackgroundCombined.pdf")
BACKUP_ROOT = Path.home() / "Library/Application Support/AirCard/Backups"


def digest(data):
    return hashlib.sha256(data).hexdigest()


def save_json(path, value):
    temporary = path.with_suffix('.tmp')
    with temporary.open('w') as stream:
        json.dump(value, stream, indent=2)
        stream.flush()
        os.fsync(stream.fileno())
    temporary.replace(path)


def card_directory(card):
    if not re.fullmatch(r'[A-Za-z0-9_+=-]{1,128}', card):
        raise ValueError('Invalid card identifier')
    return f'/var/mobile/Library/Passes/Cards/{card}.pkpass'


def device_root(udid):
    return BACKUP_ROOT / digest(udid.encode())


@contextmanager
def device_lock(udid):
    root = device_root(udid)
    root.mkdir(parents=True, exist_ok=True, mode=0o700)
    with (root / '.lock').open('a') as lock:
        try:
            fcntl.flock(lock, fcntl.LOCK_EX | fcntl.LOCK_NB)
        except BlockingIOError:
            raise RuntimeError('Another artwork operation is running for this device')
        try:
            recover_sessions(udid)
            yield
        finally:
            fcntl.flock(lock, fcntl.LOCK_UN)


def cleanup_session(udid, work):
    token = work.name
    if not re.fullmatch('[0-9a-f]{20}', token):
        raise ValueError('Invalid backup session')
    recover_original(udid, work)
    result = native('finish-write', udid, 'airlift-src-' + token,
                    'airlift-link-' + token, 'airlift-recovered-' + token,
                    str(work / 'books-snapshot'))
    if not operation_ok(result):
        raise RuntimeError(f'Could not restore Books sync state. Session retained at {work}; reconnect and retry.')
    (work / 'pending.json').unlink()


def sync_move(udid, work, identifier, destination):
    books = work / 'move-books.plist'
    books.write_bytes(build_books([identifier]))
    if not operation_ok(native('backup-metadata', udid, str(books))):
        raise RuntimeError('Could not prepare backup move metadata')
    result = run_json([str(AIRTRAFFIC_HOST), udid, identifier, destination], timeout=120)
    if result.get('exitCode') != 0 or not result.get('ok'):
        raise RuntimeError('Backup move failed: ' + str(result.get('error', 'sync failed')))


def recover_original(udid, work):
    pending = work / 'pending.json'
    journal = json.loads(pending.read_text())
    leaf = journal.get('active_leaf')
    if not leaf:
        return
    if leaf not in ASSETS:
        raise ValueError('Invalid pending artwork filename')
    card_directory(journal['card'])
    recovered = 'airlift-recovered-' + work.name
    state = native('recovered-state', udid, recovered)
    if not operation_ok(state):
        raise RuntimeError(f'Cannot establish original location. Recovery session retained: {work}')
    if state['operation']['present']:
        sync_move(udid, work, '../../' + recovered,
                  'airlift-link-' + work.name + '/' + leaf)
        state = native('recovered-state', udid, recovered)
        if not operation_ok(state) or state['operation']['present']:
            raise RuntimeError(f'Original artwork is retained on the phone. Reconnect and retry: {work}')
    elif journal.get('move_uncertain'):
        raise RuntimeError(f'Interrupted move has an uncertain outcome; session retained for recovery: {work}')
    journal['active_leaf'] = None
    save_json(pending, journal)


def indirect_snapshot(udid, card, link, destination):
    work = device_root(udid) / 'sessions' / link.removeprefix('airlift-link-')
    pending = work / 'pending.json'
    recovered = 'airlift-recovered-' + work.name
    files = {}
    for leaf in ASSETS:
        state = native('recovered-state', udid, recovered)
        if not operation_ok(state) or state['operation']['present']:
            raise RuntimeError('Backup staging location is not confirmed empty')
        journal = json.loads(pending.read_text())
        journal.update(active_leaf=leaf, move_uncertain=True)
        save_json(pending, journal)
        # Give each sync a unique asset identifier while resolving to the same
        # original. AirTraffic may remember completion of a reused identifier.
        staging = '/var/mobile/Media/airlift-src-' + work.name + '/p0'
        relative = posixpath.relpath(card_directory(card) + '/' + leaf, staging)
        identifier = '../../airlift-src-' + work.name + '/p0/' + relative
        sync_move(udid, work, identifier, recovered)
        journal['move_uncertain'] = False
        save_json(pending, journal)
        result = native('read-recovered', udid, recovered, str(destination / leaf))
        if not operation_ok(result):
            raise RuntimeError('Could not back up original artwork; returning it before aborting')
        entry = result['operation']
        if entry['present']:
            files[leaf] = {'present': True, 'size': entry['size']}
        else:
            # No recovered file does not prove the source was absent. Never
            # overwrite this asset, or remove it during a later restore.
            files[leaf] = {'present': None}
        recover_original(udid, work)
    return files


def recover_sessions(udid):
    for pending in sorted((device_root(udid) / 'sessions').glob('*/pending.json')):
        cleanup_session(udid, pending.parent)


@contextmanager
def card_access(udid, card):
    target = card_directory(card)
    token = secrets.token_hex(10)
    work = device_root(udid) / 'sessions' / token
    work.mkdir(parents=True, mode=0o700)
    snapshot = work / 'books-snapshot'
    snapshot.mkdir()
    source, link, recovered = ('airlift-src-' + token, 'airlift-link-' + token,
                               'airlift-recovered-' + token)
    identifier = f'../../{source}/p0/p1/p2/link'
    archive, books = work / 'payload.zip', work / 'Books.plist'
    archive.write_bytes(build_archive(target, b'backup-link-only'))
    books.write_bytes(build_books([identifier]))
    if not operation_ok(native('snapshot-books', udid, str(snapshot))):
        raise RuntimeError('Could not preserve Books sync state; artwork was not touched')
    # Persist recovery information before staging changes to the sync metadata.
    save_json(work / 'pending.json', {'card': card, 'created': datetime.now(timezone.utc).isoformat()})
    try:
        result = native('stage', udid, source, link, recovered,
                        str(archive), str(books), str(snapshot))
        if not operation_ok(result):
            raise RuntimeError('Could not stage artwork backup')
        result = run_json([str(AIRTRAFFIC_HOST), udid, identifier, link], timeout=120)
        if result.get('exitCode') != 0 or not result.get('ok'):
            raise RuntimeError('Could not expose artwork for backup: ' + str(result.get('error', 'unknown sync failure')))
        yield link
    finally:
        # Only generated links/staging files are cleaned, never live artwork.
        cleanup_session(udid, work)


def snapshot_files(udid, card, destination):
    destination.mkdir(parents=True, mode=0o700)
    with card_access(udid, card) as link:
        result = native('snapshot-card', udid, link, str(destination))
        if operation_ok(result):
            files = result['operation']['files']
        else:
            reason = result.get('operation', {}).get('error', 'Artwork read failed')
            raise RuntimeError(reason + '; overwrite blocked')
    if set(files) != set(ASSETS):
        raise RuntimeError('Incomplete artwork inventory')
    for name, entry in files.items():
        if entry['present']:
            data = (destination / name).read_bytes()
            if len(data) != entry['size']:
                raise RuntimeError('Backup size mismatch')
            entry['sha256'] = digest(data)
    return files


def backup_card(udid, card):
    card_directory(card)
    stamp = datetime.now(timezone.utc).strftime('%Y%m%dT%H%M%S.%fZ')
    destination = device_root(udid) / digest(card.encode()) / (stamp + '-' + secrets.token_hex(4))
    files = snapshot_files(udid, card, destination)
    if not any(entry['present'] for entry in files.values()):
        raise RuntimeError('No recognized original artwork found; overwrite blocked')
    manifest = {'version': 1, 'device': udid, 'card': card,
                'created': datetime.now(timezone.utc).isoformat(), 'files': files}
    save_json(destination / 'manifest.json', manifest)
    load_backup(udid, destination / 'manifest.json')
    return destination / 'manifest.json'


def load_backup(udid, manifest_path):
    path = Path(manifest_path)
    manifest = json.loads(path.read_text())
    if manifest.get('version') != 1 or manifest.get('device') != udid:
        raise ValueError('Backup version or device does not match')
    card_directory(manifest['card'])
    if set(manifest['files']) != set(ASSETS):
        raise ValueError('Backup has an incomplete or unexpected file list')
    payloads = {}
    for name, entry in manifest['files'].items():
        if entry.get('present') is not None and type(entry.get('present')) is not bool:
            raise ValueError('Invalid file presence record')
        if entry['present']:
            data = (path.parent / name).read_bytes()
            if len(data) != entry['size'] or digest(data) != entry['sha256']:
                raise ValueError(f'Backup checksum failed: {name}')
            payloads[name] = data
    if not payloads:
        raise ValueError('Backup contains no artwork')
    return manifest, payloads


def restore_card(udid, manifest_path):
    # Validate all bytes before any device operation.
    manifest, payloads = load_backup(udid, manifest_path)
    card = manifest['card']
    rollback = backup_card(udid, card)
    for name, data in payloads.items():
        if not write_file(udid, card_directory(card), name, data):
            raise RuntimeError(f'Restore failed for {name}; current-artwork backup: {rollback}')
    # Remove files introduced by flashing which were absent in the original.
    current, _ = load_backup(udid, rollback)
    absent = [name for name in ASSETS if manifest['files'][name]['present'] is False and current['files'][name]['present']]
    if absent:
        with card_access(udid, card) as link:
            for name in absent:
                if not operation_ok(native('remove-card-artwork', udid, link, name)):
                    raise RuntimeError(f'Could not restore absence of {name}; backup: {rollback}')
    check = Path(rollback).parent / 'restore-verification'
    observed = snapshot_files(udid, card, check)
    if any(observed.get(name) != entry for name, entry in manifest['files'].items()
           if entry['present'] is not None):
        raise RuntimeError(f'Restored artwork did not verify; current-artwork backup: {rollback}')
    for ext in ('.cache', '.pkcache'):
        for name in ('FrontFace', 'PlaceHolder', 'Preview'):
            if not write_file(udid, f'/var/mobile/Library/Passes/Cards/{card}{ext}', name, b'corrupted'):
                raise RuntimeError('Artwork restored and verified, but Wallet cache invalidation failed')
    return rollback
