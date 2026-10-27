"""Check physical storage policy, including links and mixed-device checkpoints."""
from pathlib import Path
import sys
import tempfile
import unittest
from unittest.mock import patch
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'scripts'))
from storage_policy import verify_storage, ensure_sata_mount
from subprocess import CompletedProcess


class StoragePolicy(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        self.folder = self.root / 'weights'
        self.folder.mkdir()
        (self.folder / 'model.safetensors').write_bytes(b'fixture')
        self.profile = {'id': 'dense', 'storage': {'checkpoint_directory': 'weights', 'required_transport': 'sata'}}

    def transport(self, name):
        return patch('storage_policy.subprocess.check_output', side_effect=['/dev/test1\n', f'part\ndisk {name}\n'])

    def test_dense_on_sata_passes(self):
        with self.transport('sata'):
            self.assertEqual(verify_storage(self.profile, self.root)['transport'], 'sata')

    def test_dense_on_nvme_is_refused(self):
        with self.transport('nvme'), self.assertRaisesRegex(RuntimeError, 'requires sata'):
            verify_storage(self.profile, self.root)

    def test_streaming_on_sata_is_refused(self):
        self.profile['storage']['required_transport'] = 'nvme'
        with self.transport('sata'), self.assertRaisesRegex(RuntimeError, 'requires nvme'):
            verify_storage(self.profile, self.root)

    def test_links_resolve_before_mount_lookup(self):
        alias = self.root / 'alias'
        alias.symlink_to(self.folder, target_is_directory=True)
        self.profile['storage']['checkpoint_directory'] = 'alias'
        with self.transport('sata') as run:
            verify_storage(self.profile, self.root)
        self.assertEqual(run.call_args_list[0].args[0][-1], str(self.folder / 'model.safetensors'))

    def test_a_shard_on_another_transport_is_refused(self):
        (self.folder / 'second.safetensors').write_bytes(b'second')
        replies = ['/dev/test1\n', 'part\ndisk sata\n', '/dev/test2\n', 'part\ndisk nvme\n']
        with patch('storage_policy.subprocess.check_output', side_effect=replies), self.assertRaisesRegex(RuntimeError, 'requires sata'):
            verify_storage(self.profile, self.root)

    def test_missing_mount_target_is_refused(self):
        self.profile['storage']['checkpoint_directory'] = 'missing'
        with self.assertRaises(FileNotFoundError):
            verify_storage(self.profile, self.root)


class MountPolicy(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        (self.root / 'data').mkdir()
        (self.root / 'data/storage-mount.json').write_text('{"uuid":"ABCD-1234","mountpoint":"/media/models"}')

    def result(self, status=0, text=''):
        return CompletedProcess([], status, stdout=text, stderr='')

    def test_expected_mount_does_not_attempt_remount(self):
        with patch('storage_policy.subprocess.run', return_value=self.result(text='ABCD-1234\n')) as run:
            ensure_sata_mount(self.root)
        self.assertEqual(run.call_count, 1)

    def test_unexpected_drive_is_preserved(self):
        with patch('storage_policy.subprocess.run', return_value=self.result(text='EEEE-5678\n')) as run:
            with self.assertRaisesRegex(RuntimeError, 'Unexpected drive'):
                ensure_sata_mount(self.root)
        self.assertEqual(run.call_count, 1)

    def test_missing_mount_uses_known_uuid_without_prompting(self):
        with patch('storage_policy.subprocess.run', side_effect=[self.result(1), self.result(), self.result(text='ABCD-1234\n')]) as run:
            ensure_sata_mount(self.root)
        self.assertEqual(run.call_args_list[1].args[0], ['udisksctl', 'mount', '--block-device', '/dev/disk/by-uuid/ABCD-1234', '--no-user-interaction'])

    def test_denied_mount_stops_loading(self):
        with patch('storage_policy.subprocess.run', side_effect=[self.result(1), self.result(1)]):
            with self.assertRaisesRegex(RuntimeError, 'Mount it in Files/Disks'):
                ensure_sata_mount(self.root)


if __name__ == '__main__':
    unittest.main()
