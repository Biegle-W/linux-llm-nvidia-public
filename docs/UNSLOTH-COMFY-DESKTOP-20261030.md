# Unsloth and Comfy Desktop installation — October 30, 2026

The current official Linux desktop releases were installed per-user, with
Desktop and application-menu shortcuts named **Unsloth** and **ComfyUI**.

| App | Installed version | State |
| --- | --- | --- |
| Unsloth Desktop | 0.1.913-beta | App, isolated CUDA backend and shortcuts installed |
| Comfy Desktop / ComfyUI | 1.1.8 stable | App and shortcuts installed; normal Electron launch blocked by Ubuntu sandbox policy |

Comfy's newer 1.1.9 release-candidate was not selected; 1.1.8 is the current
official stable download. The Unsloth release itself carries the beta suffix.

## Installation and integrity

AppImage files are installed under `~/.local/opt/unsloth-desktop/0.1.913-beta/`
and `~/.local/opt/comfy-desktop/1.1.8/`. Each has a launcher beside its version
folder. Desktop/menu entries use official icons and were validated; Desktop
launchers were marked trusted. AppImage extraction mode avoids requiring FUSE.
The extracted payloads are retained for inspection and the prepared Comfy
application-specific sandbox option.

Unsloth came from the official `unslothai/unsloth` release. Its 179,005,944-byte
AppImage matched the published GitHub SHA-256:

`94be4a21a10ef80a7dc2fcfb569a0a13cee1f453d08cc5912e7b4abd0ae5ec6e`

Comfy came from the official download service linked in Comfy's Linux docs.
Its 220,534,474-byte AppImage identifies itself internally as version 1.1.8;
the downloaded content matched the service's MD5 ETag. Its locally computed
SHA-256 is:

`3f3d4b710ecd7f6c0d3a4bb45a1d0cd8a5f5aa8f4d053975580a3de1ebb750a7`

No separate upstream SHA-256 was available for that Comfy download. The local
SHA-256 is a recorded fingerprint, not a claim of comparison with a publisher's
SHA-256. Both AppImage runtime checks and native-library resolution checks
passed. Official download URLs are used in this report; temporary signed asset
redirect URLs are excluded.

## Unsloth backend

The official installer bundled with the desktop app completed all 17 setup
stages, using the application's separate environment under `~/.unsloth/studio/`.
Automatic startup was disabled. The installation includes an isolated Python
3.13 environment, PyTorch CUDA 13 support, the Unsloth backend, isolated Node,
and validated prebuilt llama.cpp, whisper.cpp and audio.cpp components.

The installer detected the NVIDIA driver and selected its CUDA backend. It
removed an incompatible xFormers build inside this new environment and uses
PyTorch SDPA; existing environments were not altered. A separate import/CUDA
check records the final Python, backend and Torch versions and GPU detection.
No generation model was selected and no training or generation job was started.

## Comfy launch blocker

The real headless Electron bootstrap failed with **No usable sandbox** under
the current Ubuntu AppArmor/user-namespace restrictions. Native libraries and
the AppImage runtime are present; the failure is specifically Electron startup.
The current installed launcher does **not** contain `--no-sandbox`.

The sandbox-preserving option is an application-specific AppArmor profile based
on the profile shipped by Comfy itself. It permits user namespaces for the
installed Comfy executable while retaining Electron's user-namespace sandbox.
The prepared profile passed parser validation without being loaded into the
kernel. Applying it requires administrator authentication. A corresponding
launcher would use the fixed extracted payload with `--disable-setuid-sandbox`
to select the user-namespace sandbox rather than the unavailable SUID helper.

Comfy's official Linux docs also document `--no-sandbox` when normal sandboxed
launches fail; that option disables Electron sandboxing for Comfy processes.
It has not been applied. The system-wide namespace/sandbox policy was not
changed. The launch option remains pending a user choice and, for the
sandbox-preserving option, administrator authentication.

Comfy's first-run Local/Cloud and installation screens remain pending. No local
ComfyUI instance or image model was created. Training, generation and native GUI
interaction were not tested. The existing guarded LLM setup, model files,
profiles and selected runtimes were preserved.

Sources: [Unsloth release](https://github.com/unslothai/unsloth/releases/tag/v0.1.913-beta),
[Comfy stable release](https://github.com/Comfy-Org/Comfy-Desktop/releases/tag/v1.1.8),
[official Comfy Linux installation and sandbox guidance](https://docs.comfy.org/installation/desktop/linux).
See [verification metadata](validation-results/20261030-unsloth-comfy-desktop.json).
