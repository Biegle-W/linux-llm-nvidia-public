# Automatic GPU unlock health checks

Installed and verified October 27, 2026. Ten root-owned files are deployed; the boot
service and package/boot-image watcher are enabled. Both the boot audit and the
package-hook queue check passed on kernel 7.0.0-38-generic with NVIDIA 595.99.02.
Current `gpu-unlock-health status --brief` reports `GPU unlock: VERIFIED`.

## Events and ownership

The installer deploys a root-owned copy of the checker, independent of
this checkout, Codex or a logged-in user. It verifies the existing unlock; it does
not apply updates, rebuild modules/images, change the unlock source, reboot,
change GPU settings, or run compute/inference benchmarks.

- `gpu-unlock-health-boot.service` runs at every system boot.
- `gpu-unlock-health-update.service` runs after APT's dpkg invocation and a late
  local kernel post-install hook. Hooks only queue a service and return; health
  failures do not fail a package transaction.
- `gpu-unlock-health.path` also watches the dpkg status file and `/boot`, covering
  direct dpkg package changes and changed boot images. It requires systemd to be
  running; offline/chroot changes are checked at the next boot.

The update service waits for package locks and stable package state before
inspection. Long transactions retain pending status and retry. An unchanged
successful kernel/driver/image fingerprint avoids expensive reinspection on
unrelated package transactions; failed checks are retried rather than cached as
success. These are OS event hooks, not a recurring updater or an agent reminder.
The [systemd path mechanism](https://freedesktop.org/software/systemd/man/latest/systemd.path.html)
and [APT post-invoke configuration](https://manpages.debian.org/unstable/apt/apt.conf.5.en.html)
provide the event integration.

## What is verified

Next-boot checks identify Ubuntu's default `/boot/vmlinuz` target and verify the
unlock DKMS installation for that exact kernel, both expected GPU identities and
addresses, NVIDIA module availability, the generated GRUB entries, unlock module
and all declared firmware in the target initramfs, and dracut's pre-udev loader.
A custom GRUB default requires an explicit target policy; it is not guessed.

Boot checks require explicit current kernel targets, successful per-card unlock
journal records before NVIDIA initialization, both cards bound to NVIDIA and
available through `nvidia-smi`, and matching loaded/on-disk NVIDIA versions for
the running kernel. Relevant incomplete package states and kernel errors are
reported. The normal unsigned-module taint warning is not itself an unlock
failure when successful early unlock is proven; missing success still fails.

An installed update awaiting its next boot is **pending verification**, never a
post-boot success. Fresh boot evidence supersedes stale prior-boot records.
These checks establish configuration/boot persistence, not unchanged compute
performance or a measured token-rate benefit on a new software stack.

## Status and failures

```sh
gpu-unlock-health status --brief
gpu-unlock-health status
systemctl status gpu-unlock-health-boot.service gpu-unlock-health-update.service
systemctl status gpu-unlock-health.path
journalctl -u gpu-unlock-health-boot.service -u gpu-unlock-health-update.service
```

Results are root-written, readable JSON under `/var/lib/gpu-unlock-health/`:
`boot.json`, `update.json` and `latest.json`. Errors persist with versions, time,
boot ID and the failing stage. Failed checks leave a failed systemd unit. An
owned MOTD hook shows a brief result at logins that display `/etc/update-motd.d`.
A pending result is not a request or requirement to reboot immediately.

The services run with a read-only system/home view, dedicated writable state and
runtime directories, low CPU/I/O priority, resource/time bounds and no privilege
escalation. Root-owned configuration pins existing GPU targets and reviewed unlock
version. No root service executes code from a user-writable project directory.
Concurrent checks serialize on a runtime lock; service timeouts also record failure.

## Installation and recovery

Prepare a fresh reviewed bundle as the ordinary user:

```sh
python3 scripts/install_gpu_unlock_health.py prepare --output <new-private-bundle>
```

The installer consumes only hash-verified bytes at ten fixed destinations: the
checker, status wrapper, queue helper, root configuration, two services, path
unit, APT hook, kernel post-install hook and MOTD hook. It refuses unrelated files,
symlink destinations and writable/non-root-controlled system paths. Structural
installation failures roll back its own file changes. An initial health failure
keeps the monitor installed and visibly failed for diagnosis.

Administrator installation uses the exact bundle manifest hash. The local
installation command must also verify the installer hash before root execution;
never substitute a root service that runs a mutable checkout directly. Installed
hashes and any replaced managed files are retained under the state directory.
No actual kernel/driver update or reboot is needed to install the checker.

To suspend this monitoring, disable its boot service and path unit and remove only
its owned APT/kernel queue hooks after checking their markers/hashes. This does
not disable the GPU unlock itself. Its existing GRUB/dracut unlock configuration
is separate and must be preserved unless explicitly requested otherwise.

## Validation

29 focused synthetic health/installer tests passed, plus the full 103-test CPU
suite. Cases include missing/late per-card unlock, missing NVIDIA devices,
incomplete packages, missing modules/firmware/early loading, stale boot evidence,
update-pending states, changed GPU identities, and modified installation bundles.
Hook shell syntax, APT parsing and `systemd-analyze verify` passed. Ten installed file hashes/owners/modes, enabled units, active watched paths,
current-boot audit, all five firmware files and the exact hook queue command were
verified live.
A future real package update/reboot must generate its own new evidence.

The first deployed sandbox used `ProtectKernelModules=yes`, which also hides
module files and caused a false DKMS-readiness failure. It was corrected to
read-only module access with `CAP_SYS_MODULE` removed and module syscalls denied;
system writes remain blocked. The failure records and original bundle are kept
privately. Three superseded definitions are hash-verified in the private archive
batch `linux-nvidia/2026-10-27-unlock-health-module-visibility`, commit `ac7474a`.
The [systemd sandbox documentation](https://freedesktop.org/software/systemd/man/latest/systemd.exec.html)
describes this visibility distinction. No actual package update or reboot was
performed to install or test these event hooks; future events create fresh proof.
