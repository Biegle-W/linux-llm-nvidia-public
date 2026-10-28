"""Persistence checks with synthetic boot images/journals; no GPU or root writes."""
import hashlib
import json
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest
from unittest.mock import patch

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'scripts'))
import gpu_unlock_health as health
import install_gpu_unlock_health as installer

TARGETS = {'0000:01:00.0', '0000:06:00.0'}


def logs():
    return [
        {'MESSAGE': 'pci 0000:01:00.0: gpu_unlock: unlocked', '__MONOTONIC_TIMESTAMP': '100'},
        {'MESSAGE': 'pci 0000:06:00.0: gpu_unlock: unlocked', '__MONOTONIC_TIMESTAMP': '200'},
        {'MESSAGE': 'nvidia-nvlink: Nvlink Core is being initialized', '__MONOTONIC_TIMESTAMP': '300'},
        {'MESSAGE': 'NVRM: loading NVIDIA UNIX Open Kernel Module', '__MONOTONIC_TIMESTAMP': '400'}]


class BootEvidence(unittest.TestCase):
    def test_both_selected_cards_must_unlock_before_nvidia(self):
        r = health.evaluate_boot(logs(), TARGETS, {x: '595.99.02' for x in TARGETS})
        self.assertEqual(r['unlocked_before_nvidia'], sorted(TARGETS))

    def test_one_missing_unlock_is_not_success(self):
        with self.assertRaises(ValueError): health.evaluate_boot(logs()[1:], TARGETS, dict.fromkeys(TARGETS, '595'))

    def test_unlock_after_driver_initialization_fails(self):
        rows = logs(); rows[0]['__MONOTONIC_TIMESTAMP'] = '350'
        with self.assertRaises(ValueError): health.evaluate_boot(rows, TARGETS, dict.fromkeys(TARGETS, '595'))

    def test_missing_timestamps_or_driver_evidence_fails(self):
        for rows in [logs()[:2], [{'MESSAGE': r['MESSAGE']} for r in logs()]]:
            with self.assertRaises(ValueError): health.evaluate_boot(rows, TARGETS, dict.fromkeys(TARGETS, '595'))

    def test_card_absent_from_nvidia_smi_fails(self):
        with self.assertRaises(ValueError): health.evaluate_boot(logs(), TARGETS, {'0000:01:00.0': '595'})

    def test_explicit_firmware_failure_is_not_ignored(self):
        rows = logs() + [{'MESSAGE': 'gpu_unlock: firmware failed', '__MONOTONIC_TIMESTAMP': '150'}]
        with self.assertRaises(ValueError): health.evaluate_boot(rows, TARGETS, dict.fromkeys(TARGETS, '595'))

    def test_nvidia_errors_are_visible(self):
        rows = logs() + [{'MESSAGE': 'NVRM: Xid (PCI:0000:01:00): 79', '__MONOTONIC_TIMESTAMP': '500'}]
        with self.assertRaises(ValueError): health.evaluate_boot(rows, TARGETS, dict.fromkeys(TARGETS, '595'))

    def test_permitted_unsigned_module_warning_is_not_an_unlock_failure(self):
        rows = logs() + [{'MESSAGE': 'gpu_unlock: module verification failed: signature and/or required key missing - tainting kernel', '__MONOTONIC_TIMESTAMP': '50'}]
        self.assertEqual(health.evaluate_boot(rows, TARGETS, dict.fromkeys(TARGETS, '595'))['unlocked_before_nvidia'], sorted(TARGETS))

    def test_smi_domain_normalization(self):
        self.assertEqual(health.normalize_bdf('00000000:06:00.0'), '0000:06:00.0')


class StateHandling(unittest.TestCase):
    def test_prior_boot_success_is_not_current_boot_success(self):
        name, _ = health.state_view({'boot_id': 'old', 'status': 'verified'}, None, 'new')
        self.assertEqual(name, 'PENDING BOOT CHECK')

    def test_new_update_fingerprint_requires_postboot_verification(self):
        boot = {'boot_id': 'boot', 'status': 'verified', 'fingerprint': 'old'}
        update = {'status': 'ready_pending_boot', 'fingerprint': 'new'}
        self.assertEqual(health.state_view(boot, update, 'boot')[0], 'PENDING REBOOT VERIFICATION')

    def test_matching_postboot_success_resolves_previous_update_pending(self):
        boot = {'boot_id': 'boot', 'status': 'verified', 'fingerprint': 'new'}
        update = {'status': 'ready_pending_boot', 'fingerprint': 'new'}
        self.assertEqual(health.state_view(boot, update, 'boot')[0], 'VERIFIED')

    def test_failed_update_remains_visible_despite_prior_success(self):
        boot = {'boot_id': 'boot', 'status': 'verified', 'fingerprint': 'old'}
        self.assertEqual(health.state_view(boot, {'status': 'failed'}, 'boot')[0], 'FAILED')

    def test_in_progress_checks_cannot_display_old_success(self):
        boot = {'boot_id': 'boot', 'status': 'verified', 'fingerprint': 'old'}
        self.assertEqual(health.state_view(boot, {'status': 'checking'}, 'boot')[0], 'UPDATE CHECK PENDING')

    def test_next_default_kernel_pending_is_not_running_kernel_verified(self):
        boot = {'boot_id': 'boot', 'status': 'verified', 'boot': {'next_boot_pending': True}}
        self.assertEqual(health.state_view(boot, None, 'boot')[0], 'PENDING REBOOT VERIFICATION')

    def test_new_successful_boot_resolves_old_failed_or_incomplete_update(self):
        boot = {'boot_id': 'new', 'status': 'verified', 'time': 20, 'fingerprint': 'ok'}
        for state in ['failed', 'checking', 'pending_transaction', 'ready_pending_boot']:
            update = {'boot_id': 'old', 'status': state, 'time': 10, 'fingerprint': 'old'}
            self.assertEqual(health.state_view(boot, update, 'new')[0], 'VERIFIED')

    def test_half_configured_relevant_package_fails(self):
        with self.assertRaises(ValueError): health.package_versions('nvidia-driver\t596\thalf-configured\n')

    def test_package_fingerprint_excludes_unrelated_and_removed_packages(self):
        data = 'vim\t1\tinstalled\nnvidia-utils\t595\tinstalled\nlinux-image-k\t1\tinstalled\nlibnvidia-old\t2\tconfig-files\n'
        self.assertEqual(health.package_versions(data), [['linux-image-k', '1'], ['nvidia-utils', '595']])

    def test_explicit_targets_reject_all_duplicate_and_multiple_arguments(self):
        for value in ['all', '0000:01:00.0,0000:01:00.0', '0000:01:00.0 gpu_unlock.targets=0000:06:00.0']:
            with self.assertRaises(ValueError): health.targets_from('gpu_unlock.targets='+value)


class BootImage(unittest.TestCase):
    def fixture(self, root):
        config = {'targets': [{'bdf': b, 'vendor': '0x10de', 'device': '0x2208'} for b in sorted(TARGETS)],
                  'unlock_version': '1.0.0', 'grub_dropin': str(root/'grub.cfg'), 'dracut_dropin': str(root/'dracut.conf')}
        args = 'gpu_unlock.targets=' + ','.join(sorted(TARGETS))
        (root/'grub.cfg').write_text(args)
        (root/'dracut.conf').write_text('force_drivers+=" gpu_unlock "\n')
        path = root/'boot/grub';path.mkdir(parents=True)
        (path/'grub.cfg').write_text('linux /boot/vmlinuz-test-kernel '+args+'\n')
        for target in TARGETS:
            p=root/'sys/bus/pci/devices'/target;p.mkdir(parents=True);(p/'vendor').write_text('0x10de');(p/'device').write_text('0x2208')
        def paths(value):
            value=Path(value)
            return root/value.relative_to('/') if str(value).startswith(('/boot/', '/sys/')) else value
        listing=['usr/lib/modules/test-kernel/updates/dkms/gpu_unlock.ko.zst',
                 'usr/lib/firmware/gpu-unlock/test.bin', 'usr/lib/systemd/system/dracut-pre-udev.service']
        values={'listing':listing, 'dkms':'gpu-unlock/1.0.0, test-kernel, x86_64: installed\n',
                'early':'rd.driver.pre=gpu_unlock\n'}
        def run(name,*args,**kwargs):
            if name=='dkms':return values['dkms']
            if name=='lsinitramfs':return '\n'.join(values['listing'])
            if name=='lsinitrd':return values['early']
            if name=='modinfo':
                if args[-2]=='firmware':return 'gpu-unlock/test.bin\n'
                return '1.0.0' if args[-1]=='gpu_unlock' else '595.99.02'
            raise AssertionError((name,args))
        return config, paths, run, values

    def check_case(self, mutation, expected_success=False):
        with tempfile.TemporaryDirectory() as directory:
            root=Path(directory);config,paths,run,values=self.fixture(root);mutation(root,values)
            with patch.object(health,'Path',side_effect=paths),patch.object(health,'run',side_effect=run):
                if expected_success:self.assertTrue(health.check_preboot(config,'test-kernel')['initramfs_verified'])
                else:
                    with self.assertRaises(ValueError):health.check_preboot(config,'test-kernel')

    def test_complete_target_image_and_grub_pass(self): self.check_case(lambda r,v:None,True)
    def test_missing_target_module_fails(self): self.check_case(lambda r,v:v['listing'].pop(0))
    def test_missing_declared_firmware_fails(self): self.check_case(lambda r,v:v['listing'].pop(1))
    def test_missing_pre_udev_service_fails(self): self.check_case(lambda r,v:v['listing'].pop(2))
    def test_missing_early_load_request_fails(self): self.check_case(lambda r,v:v.update(early=''))
    def test_dkms_unbuilt_target_fails(self): self.check_case(lambda r,v:v.update(dkms='gpu-unlock/1.0.0: added'))
    def test_generated_grub_without_unlock_fails(self): self.check_case(lambda r,v:(r/'boot/grub/grub.cfg').write_text('linux /boot/vmlinuz-test-kernel quiet\n'))
    def test_changed_gpu_identity_fails(self): self.check_case(lambda r,v:(r/'sys/bus/pci/devices/0000:01:00.0/device').write_text('0x9999'))


class InstallationBundle(unittest.TestCase):
    def test_every_event_uses_root_owned_installed_checker(self):
        values=installer.payloads({'managed_by':'test'}, b'checker')
        self.assertEqual(set(values), installer.DESTINATIONS)
        self.assertIn(b'PathChanged=/var/lib/dpkg/status',values['/etc/systemd/system/gpu-unlock-health.path'][0])
        self.assertIn(b'DPkg::Post-Invoke',values['/etc/apt/apt.conf.d/99-local-llm-gpu-unlock-health'][0])
        for event in ['boot','update']:
            unit=values[f'/etc/systemd/system/gpu-unlock-health-{event}.service'][0]
            self.assertIn(b'/usr/bin/python3 -I /usr/local/libexec/gpu-unlock-health.py',unit)
            self.assertNotIn(str(Path.home()).encode(),unit)
            self.assertIn(b'ProtectSystem=strict',unit)
            self.assertNotIn(b'ProtectKernelModules=yes',unit)
            self.assertIn(b'ReadOnlyPaths=/usr/lib/modules',unit)
            self.assertIn(b'CapabilityBoundingSet=~CAP_SYS_MODULE',unit)
            self.assertIn(b'SystemCallFilter=~@module',unit)

    def test_bundle_changes_and_extra_destinations_are_refused(self):
        with tempfile.TemporaryDirectory() as directory:
            root=Path(directory);files=[]
            for i,target in enumerate(sorted(installer.DESTINATIONS)):
                name=str(i);raw=b'payload';(root/name).write_bytes(raw)
                files.append({'source':name,'target':target,'sha256':hashlib.sha256(raw).hexdigest(),'mode':0o644})
            manifest={'files':files};raw=json.dumps(manifest).encode();(root/'manifest.json').write_bytes(raw);expected=hashlib.sha256(raw).hexdigest()
            self.assertEqual(set(installer.read_bundle(root,expected)[0]),installer.DESTINATIONS)
            (root/'0').write_bytes(b'changed')
            with self.assertRaises(ValueError):installer.read_bundle(root,expected)
            with self.assertRaises(ValueError):installer.read_bundle(root,'0'*64)
            files.append(dict(files[0],target='/etc/unrelated'));raw=json.dumps({'files':files}).encode();(root/'manifest.json').write_bytes(raw)
            with self.assertRaises(ValueError):installer.read_bundle(root,hashlib.sha256(raw).hexdigest())


if __name__ == '__main__': unittest.main()
