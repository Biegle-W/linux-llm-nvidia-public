import sys
import tempfile
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'scripts'))
from update_native_builders import preserve_maya_vision
from update_transaction import sha


class VisionPreservationTests(unittest.TestCase):
    def test_encoder_and_stamp_survive_staging_with_protected_hashes(self):
        with tempfile.TemporaryDirectory() as directory:
            old = Path(directory) / 'selected'
            source = Path(directory) / 'candidate'
            encoder = old / 'build-vision' / 'bin' / 'maya-vision'
            encoder.parent.mkdir(parents=True)
            encoder.write_bytes(b'installed encoder')
            encoder.chmod(0o755)
            stamp = old / 'build-vision' / 'MAYA-BUILD.json'
            stamp.write_text('{}')
            source.mkdir()
            receipt = {}
            preserve_maya_vision(old, source, receipt)
            copied = source / 'build-vision' / 'bin' / 'maya-vision'
            self.assertEqual(copied.read_bytes(), encoder.read_bytes())
            self.assertTrue(copied.stat().st_mode & 0o111)
            self.assertEqual((source / 'build-vision' / stamp.name).read_text(), '{}')
            self.assertEqual({entry['path']: entry['sha256']
                              for entry in receipt['protected_files']},
                             {str(encoder): sha(encoder), str(stamp): sha(stamp)})

    def test_installation_without_optional_encoder_is_preserved(self):
        with tempfile.TemporaryDirectory() as directory:
            receipt = {}
            preserve_maya_vision(Path(directory) / 'old',
                                 Path(directory) / 'candidate', receipt)
            self.assertEqual(receipt, {})


if __name__ == '__main__':
    unittest.main()
