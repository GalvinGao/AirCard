import contextlib
import io
import json
from pathlib import Path
import sys
import tempfile
import unittest
from contextlib import nullcontext
from unittest.mock import patch

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
import aircard
import aircard_backend as backend


class CardArtworkTests(unittest.TestCase):
    def flash(self, failure=None):
        with tempfile.TemporaryDirectory() as directory:
            image = Path(directory) / 'skin.png'
            image.write_bytes(b'png')
            assets = {name: b'%PDF-test' if name.endswith('.pdf') else b'png'
                      for name in aircard.TARGET_ASSETS}
            output = io.StringIO()
            with patch.object(backend, 'device_lock', return_value=nullcontext()), \
                 patch.object(backend, 'backup_card', return_value=Path('/backup/manifest.json')), \
                 patch.object(backend, 'load_backup', return_value=({'files': {n: {'present': True} for n in assets}}, {})), \
                 patch.object(backend, 'prepare_card_assets', return_value=assets), \
                 patch.object(backend, 'write_file', side_effect=lambda u, d, n, p: n != failure) as write, \
                 contextlib.redirect_stdout(output):
                result = backend.cmd_flash('device', 'card', str(image))
            return result, write.call_args_list, [json.loads(line) for line in output.getvalue().splitlines()]

    def test_writes_real_format_payload_and_all_caches(self):
        result, calls, events = self.flash()
        self.assertTrue(result)
        self.assertEqual(len(calls), 9)
        payloads = {call.args[2]: call.args[3] for call in calls[:3]}
        self.assertEqual(payloads['cardBackgroundCombined.pdf'], b'%PDF-test')
        self.assertEqual(payloads['cardBackgroundCombined@3x.png'], b'png')
        self.assertEqual({(c.args[1], c.args[2]) for c in calls[3:]},
                         {(f'/var/mobile/Library/Passes/Cards/card{ext}', leaf)
                          for ext in ['.cache', '.pkcache']
                          for leaf in ['FrontFace', 'PlaceHolder', 'Preview']})
        self.assertEqual(events[-1]['type'], 'success')
        self.assertEqual(events[-1]['step'], events[-1]['total'])

    def test_asset_and_cache_failures_do_not_report_success(self):
        for failure in ['cardBackgroundCombined.pdf', 'cardBackgroundCombined@2x.png', 'PlaceHolder']:
            with self.subTest(failure=failure):
                result, _, events = self.flash(failure)
                self.assertFalse(result)
                self.assertNotIn('success', [e['type'] for e in events])
                self.assertIn(failure, events[-1]['message'])

    def test_conversion_failure_never_writes_to_device(self):
        with tempfile.NamedTemporaryFile() as image:
            with patch.object(backend, 'device_lock', return_value=nullcontext()), \
                 patch.object(backend, 'prepare_card_assets', side_effect=ValueError('invalid')), \
                 patch.object(backend, 'write_file') as write, \
                 contextlib.redirect_stdout(io.StringIO()):
                self.assertFalse(backend.cmd_flash('device', 'card', image.name))
                write.assert_not_called()

    def test_converter_output_must_be_pdf(self):
        def invalid_output(args, **kwargs):
            Path(args[2]).write_bytes(b'not a PDF')
        with patch.object(aircard.subprocess, 'run', side_effect=invalid_output):
            with self.assertRaisesRegex(ValueError, 'did not produce a PDF'):
                aircard.prepare_card_assets(b'png')


if __name__ == '__main__':
    unittest.main()
