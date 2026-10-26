"""Host-only safety/rollback tests; no real driver, boot image or GPU access."""
import importlib.util
from pathlib import Path
import subprocess
import tempfile
import unittest
import shutil
from unittest.mock import patch

spec = importlib.util.spec_from_file_location("unlock", Path(__file__).with_name("native_linux_gpu_unlock.py"))
unlock = importlib.util.module_from_spec(spec)
spec.loader.exec_module(unlock)


class Guards(unittest.TestCase):
    @staticmethod
    def shell():
        git_bash = Path("C:/Program Files/Git/bin/bash.exe")
        return str(git_bash) if git_bash.is_file() else shutil.which("bash")

    def test_generated_shell_syntax(self):
        shell = self.shell()
        if not shell:
            self.skipTest("bash not installed")
        for content in unlock.boot_files("0000:01:00.0").values():
            if content is None:
                continue
            subprocess.run([shell, "-n"], input=content, text=True, check=True)

    def test_grub_retains_existing_arguments(self):
        shell = self.shell()
        if not shell:
            self.skipTest("bash not installed")
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "owned.cfg"
            path.write_text(unlock.boot_files("0000:01:00.0")[unlock.GRUB])
            result = subprocess.run([shell, "-c", 'GRUB_CMDLINE_LINUX_DEFAULT="quiet splash test=existing"; '
                                     '. "$1"; printf "%s" "$GRUB_CMDLINE_LINUX_DEFAULT"', "check",
                                     str(path).replace("\\", "/")], check=True, capture_output=True, text=True)
            self.assertEqual(result.stdout, "quiet splash test=existing gpu_unlock.targets=0000:01:00.0")

    def test_windows_and_wsl_refused_before_mutation(self):
        for system, release in (("Windows", "11"), ("Linux", "6.18-microsoft-standard-WSL2")):
            with self.subTest(system=system), patch.object(unlock.platform, "system", return_value=system), \
                 patch.object(unlock.platform, "release", return_value=release), patch.object(unlock, "run") as run:
                with self.assertRaises(RuntimeError):
                    unlock.install()
                run.assert_not_called()

    def test_retail_targets_and_rejected_engineering_model(self):
        cards = [{"bdf": "0000:01:00.0", "device": "2503"},
                 {"bdf": "0000:02:00.0", "device": "2208"},
                 {"bdf": "0000:03:00.0", "device": "2205"}]
        self.assertEqual(unlock.targets("0000:01:00.0,0000:02:00.0", cards),
                         "0000:01:00.0,0000:02:00.0")
        for value in ("all", "0000:03:00.0", "0000:04:00.0", "0000:01:00.0,0000:01:00.0",
                      "0000:01:00.0;reboot"):
            with self.subTest(value=value), self.assertRaises(RuntimeError):
                unlock.targets(value, cards)

    def test_audio_function_is_not_a_gpu(self):
        with tempfile.TemporaryDirectory() as tmp:
            for bdf, pci_class in (("gpu0", "0x030000"), ("audio0", "0x040300")):
                folder = Path(tmp) / bdf
                folder.mkdir()
                for name, value in (("vendor", "0x10de"), ("class", pci_class), ("device", "0x2503")):
                    (folder / name).write_text(value)
            self.assertEqual([card["bdf"] for card in unlock.devices(Path(tmp))], ["gpu0"])

    def test_planned_pair_and_trio_use_current_explicit_addresses(self):
        cards = [{"bdf": "0000:07:00.0", "device": "2208"},
                 {"bdf": "0000:0b:00.0", "device": "2206"},
                 {"bdf": "0000:12:00.0", "device": "2503"}]
        pair = "0000:07:00.0,0000:0b:00.0"
        self.assertEqual(unlock.targets(pair, cards), pair)
        trio = pair + ",0000:12:00.0"
        self.assertEqual(unlock.targets(trio, cards), trio)
        for value in ("all", "0000:01:00.0", pair + ",0000:07:00.0"):
            with self.subTest(value=value), self.assertRaises(RuntimeError):
                unlock.targets(value, cards)

    def test_secure_boot_enabled_or_unknown_blocks_install(self):
        for state in ("enabled", "unknown"):
            with patch.object(unlock, "prerequisites"), patch.object(unlock, "secure_boot", return_value=state), \
                 patch.object(unlock, "prepare_source") as source:
                with self.assertRaises(RuntimeError):
                    unlock.install()
                source.assert_not_called()

    def test_generation_failure_restores_dropin_and_rebuilds(self):
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "owned.cfg"
            original = unlock.MARKER + "original options\n"
            path.write_text(original)
            failure = subprocess.CalledProcessError(1, "update-grub")
            with patch.object(unlock, "run", side_effect=["", failure, "", ""]) as run:
                with self.assertRaises(subprocess.CalledProcessError):
                    unlock.transactional_update({path: unlock.MARKER + "new options\n"})
                self.assertEqual(path.read_text(), original)
                self.assertEqual(run.call_count, 4)

    def test_unowned_configuration_is_preserved(self):
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "other.cfg"
            path.write_text("user configuration\n")
            with patch.object(unlock, "run") as run:
                with self.assertRaises(RuntimeError):
                    unlock.transactional_update({path: None})
                run.assert_not_called()
            self.assertEqual(path.read_text(), "user configuration\n")

    def test_missing_module_in_image_rolls_back_before_grub(self):
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "owned.cfg"
            with patch.object(unlock, "run", return_value="") as run:
                with self.assertRaises(RuntimeError):
                    unlock.transactional_update({path: unlock.MARKER}, verify_image=True)
                self.assertFalse(path.exists())
                self.assertEqual(run.call_args_list[2].args, ("update-initramfs", "-u", "-k", "all"))

    def test_dracut_wrapper_detection_and_fail_closed(self):
        for wrapper, expected in (("if dracut ${OPTS}; then", "dracut"),
                                  ("mkinitramfs -o image", "initramfs-tools")):
            with patch.object(unlock, "read", return_value=wrapper), \
                 patch.object(unlock.shutil, "which", return_value="/usr/bin/tool"):
                self.assertEqual(unlock.initramfs_backend(), expected)
        with patch.object(unlock, "read", return_value="unknown generator"):
            with self.assertRaises(RuntimeError):
                unlock.initramfs_backend()

    def test_dracut_uses_force_load_and_removes_inactive_hooks(self):
        files = unlock.boot_files("0000:01:00.0", "dracut")
        self.assertIn('force_drivers+=" gpu_unlock "', files[unlock.DRACUT])
        self.assertIsNone(files[unlock.HOOK])
        self.assertIsNone(files[unlock.EARLY])
        self.assertIn("gpu_unlock.targets=0000:01:00.0", files[unlock.GRUB])
        self.assertIsNone(unlock.boot_files("0000:01:00.0")[unlock.DRACUT])

    def test_dracut_missing_early_load_rolls_back(self):
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "dracut.conf"
            listing = "usr/lib/modules/test/gpu_unlock.ko.zst\nusr/lib/systemd/system/dracut-pre-udev.service"
            with patch.object(unlock, "DRACUT", path), \
                 patch.object(unlock, "run", side_effect=["", listing, "", "", ""]) as run:
                with self.assertRaisesRegex(RuntimeError, "early gpu_unlock"):
                    unlock.transactional_update({path: unlock.MARKER}, verify_image=True)
                self.assertFalse(path.exists())
                self.assertEqual(run.call_count, 5)

    def test_dracut_image_and_firmware_verified_before_grub(self):
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "dracut.conf"
            listing = ("usr/lib/modules/test/gpu_unlock.ko.zst\n"
                       "usr/lib/systemd/system/dracut-pre-udev.service\n"
                       "usr/lib/firmware/gpu-unlock/test.bin")
            with patch.object(unlock, "DRACUT", path), \
                 patch.object(unlock, "run", side_effect=["", listing, "rd.driver.pre=gpu_unlock",
                                                         "gpu-unlock/test.bin", ""]) as run:
                unlock.transactional_update({path: unlock.MARKER}, verify_image=True)
                self.assertEqual(run.call_args_list[-1].args, ("update-grub",))
                self.assertEqual(path.stat().st_mode & 0o777, 0o644)

    def test_disable_needs_no_gpu_or_secure_boot_checks(self):
        with patch.object(unlock, "native_only"), patch.object(unlock.os, "geteuid", return_value=0, create=True), \
             patch.object(unlock, "transactional_update") as update, patch.object(unlock, "mutation_gate") as gate:
            unlock.disable()
            gate.assert_not_called()
            self.assertEqual(set(update.call_args.args[0].values()), {None})


if __name__ == "__main__":
    unittest.main()
