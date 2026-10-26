# NVIDIA Windows-to-Linux handoff — October 25, 2026

## Objective and current evidence

The user is switching the NVIDIA workstation to **native Linux**. Maintain its
Linux source in `Biegle-W/linux-llm-nvidia`, with reviewed examples in
`Biegle-W/linux-llm-nvidia-public`. Windows stays independently recoverable in its
existing private/public repositories. The AMD Linux workstation is a different
machine; do not run its ROCm launchers or copy its validation flags here.

Preparation was performed from Windows. Inspect the actual native Linux session
before assuming an OS, driver, target SSD, GPU count or PCI address. An additional
Linux SSD was planned previously; its installation was not verified here. Do not
format or resize an unidentified disk. The user controls reboot and OS installation.

| Component | Last verified / planned state |
|---|---|
| CPU | Intel Core i5-13600KF; no integrated display GPU |
| RAM | 64 GiB, 4 x 16 GiB Corsair, configured 4200 MT/s in Windows |
| Currently installed GPU | RTX 3080 Ti 12 GB, GA102, device ID `2208` |
| Next GPU | RTX 3080 10 GB, GA102, device ID `2206`; previously tested separately |
| Later GPU | Original RTX 3060 12 GB, GA106, device ID `2503` |
| Planned topology | Ti + 3080, then PEX88096 PCIe switch and 3060 |
| Nominal VRAM | 22 GB for the pair; 34 GB with the 3060, before per-device overhead |
| PSU | 1200 W unit expected; exact installed model and wiring require inspection |
| Existing system storage | 1 TB NVMe; identify current Linux/model mounts afresh |

These cards have **separate verified Windows compute-unlock results**, not a
simultaneously validated Linux result. Historical unlocked FP16/BF16 GEMM:
Ti 126.501/130.344 TFLOPS; 3080 113.375/113.455; 3060 50.724/50.591.
Those measurements used different Windows sessions; RAM changed between some
baselines. They are not predicted Linux speed, model decode, a GPU sum or a full
system controlled comparison. Windows evidence remains in the Windows repos.

## 1. Establish a normal native Linux baseline

Clone the appropriate repository to a Linux filesystem. Use the private repo for
actual local state, or the public repo as a reference requiring local adaptation.

```bash
git clone https://github.com/Biegle-W/linux-llm-nvidia.git ~/Local-LLM-NVIDIA
cd ~/Local-LLM-NVIDIA
mkdir -p data models runtimes
uname -a
lspci -nnk -d 10de:
lsblk -o NAME,SIZE,FSTYPE,MOUNTPOINTS,MODEL
nvidia-smi
nvidia-smi topo -m
free -h
```

Confirm native Linux, not a Microsoft/WSL kernel. Save host inventory, actual
addresses, driver/kernel versions, topology, RAM and storage mappings privately.
Never publish GPU UUIDs, subsystem selectors, disk serials, user paths or addresses.

Install the distribution-supported NVIDIA driver if necessary, then validate normal
display and CUDA operation first. Use [Ubuntu's driver guidance](https://documentation.ubuntu.com/server/how-to/graphics/install-nvidia-drivers/).
The Windows driver version is not a Linux installation instruction. Native builds
and virtual environments must be isolated from both Windows binaries and AMD ROCm.

Before enabling any unlock, retain per-card stock FP32/FP16/BF16 GEMM with FP32
accumulation/reference checks, clocks/power/temperature and matched real-model
prefill/decode samples. Use the same kernel, driver, power cap, model, context,
batch, prompt/output lengths and cache state for the later comparison. Record
thermal coverage; do not import another machine's results as a baseline.

## 2. Native Linux compute unlock

The helper now allows **2208, 2206 and 2503** and requires an explicit list of
physical PCI display-device addresses found on this boot. It refuses Windows,
WSL, duplicate/missing/unknown targets, and `targets=all`. It does not flash VBIOS,
increase VRAM, install the NVIDIA driver, modify Windows or reboot.

Reviewed upstream pin: `af28cbbfd3d922a659227ecfb7369adfd924cf03`,
[Zagitta/gpu-unlock](https://github.com/Zagitta/gpu-unlock).
The Linux module runs before NVIDIA binds each selected GPU; multiple cards are
processed in the same boot. The Windows USB GOP-release procedure is not the
native Linux unlock procedure. No USB-per-card chain is required on Linux.

```bash
python3 scripts/native_linux_gpu_unlock.py check
python3 scripts/native_linux_gpu_unlock.py source
python3 scripts/native_linux_gpu_unlock.py install
```

Installation automation covers Ubuntu/Debian, GRUB and initramfs-tools. It refuses
mutations with enabled/unknown Secure Boot; signing/MOK support is not implemented.
Do not disable Secure Boot automatically. Review current upstream changes and
distribution compatibility before updating the pin; preserve the tested helper's
fail-closed behavior and rollback tests.

Then run the helper's `enable --targets` command as root with the **actual Linux
addresses**. Do not reuse Windows addresses or examples from older reports.
The helper manages its own GRUB drop-in and initramfs hook/early loader, preserving
existing arguments. Confirm image generation succeeded. Let the user perform a
full power-off/start, then inspect:

```bash
cat /proc/cmdline
sudo journalctl -k -b | grep -Ei 'gpu.unlock|NVRM|Xid'
nvidia-smi
lspci -nnk -d 10de:
```

Check every selected card, reference correctness and display health. A successful
module log alone does not prove faster compute. Do not infer doubled decode from
GEMM gains. Keep the operation once per GPU per fresh boot; do not reapply after
NVIDIA has bound a card. Recheck DKMS and initramfs after kernel updates.

Recovery: temporarily remove `gpu_unlock.targets=...` in GRUB, boot normally and
run `sudo python3 scripts/native_linux_gpu_unlock.py disable`. It removes only its
three owned files and rebuilds the boot configuration; it does not revert a running
GPU immediately. Inspect errors before another restart.

## 3. P2P and the PCIe switch are a separate experiment

First verify ordinary two-GPU inference without P2P. The compute unlock does not
enable peer access. The PEX88096 provides routing; its adapter wiring, negotiated
links, BAR allocation, ACS and the driver decide the usable path. Shared upstream
lanes remain shared for host transfers.

Community [Linux P2P kernel-module patches](https://github.com/EKI-INDRADI/open-gpu-kernel-module-ai-patch)
claim support for these RTX 30-series models. They require matching NVIDIA kernel
modules/userspace, Above 4G/ReBAR, BAR1 large enough for usable VRAM and suitable
IOMMU/ACS configuration. This exact trio and switch are **not locally verified**.
IOMMU passthrough changes device isolation; do not apply it without reviewing the
machine's actual topology and trust boundary. Do not copy a Linux module into WSL.

Retain a stock-driver fallback. Verify both directions with CUDA's
`p2pBandwidthLatencyTest` and relevant peer-access checks; for engines using NCCL,
also run numerical collective checks. A topology label or peer-access boolean is
not proof of working bandwidth/collectives. Test the pair first, then each link
in the three-card system. Confirm compute-unlock correctness still holds with the
chosen P2P driver. No P2P-driver installation is automated by this handoff.

## 4. Rebuild inference for this NVIDIA machine

Existing GGUF assets on Windows, currently under that project's `models/`:

| Model filename stem | Windows configured context | Windows cache placement |
|---|---:|---|
| Ornith-1.5-35B-A3B-IQ2_S | 131072 | Q8 KV in RAM |
| LFM2.5-24B-A2B-UD-IQ3_XXS | 131072 | Q8 KV in RAM |
| Qwen3.8-27B-UD-IQ3_XXS | 65536 | Q8 KV in RAM; dense model |
| Empero: Qwen3.8-35B-A3B-IQ2_M | 65536 | Q8 KV in RAM |

Verify exact filenames/hashes and actual mounts before copying or downloading.
Model inventories here are disabled examples, not executable Linux profiles.
The old Windows source drive D: is now a USB in that session; never assume it is
the former shared model drive. Avoid duplicate weights. Keep engine builds on
ext4 and choose static/streaming model locations from actual free space.

Start with native **llama.cpp CUDA layer splitting** across the detected Ti/3080
pair. Discover CUDA device order rather than assuming GPU0 is always the Ti.
Use actual free memory/headroom and unequal splits; neither equal splitting nor
the raw 12:10 ratio guarantees balance. Prefer GPU-resident KV where feasible,
then compare quantized KV or host offload for larger contexts. Keep one maintained
setting per model, with allocated versus tested lengths and placement documented.

Only after P2P is proven, compare supported tensor parallelism against layer split
on matching workloads. Current upstream tensor mode is experimental:
[llama.cpp multi-GPU guide](https://github.com/ggml-org/llama.cpp/blob/master/docs/multi-gpu.md).

Candidate engines, installed only in isolated native environments:

- **Strata:** Qwen Flash-Next with bounded host expert backing and per-GPU caches.
  Unequal multi-GPU layer split works without P2P; retain room for each device's
  duplicated state/buffers. [Implementation](https://github.com/Niko1221/Strata/blob/main/docs/MULTI_GPU.md).
- **FreeToken-Kai:** supported Qwen MoEs/GPT-OSS, bounded host banks and pipeline
  splitting. Treat the third-GPU path and 64 GB host budget as new validation.
  [Pipeline details](https://github.com/yuuki-net/FreeToken-Kai/blob/kai/docs/pipeline.md).
- **ExLlamaV3 / TabbyAPI:** EXL3, tensor/expert parallelism and CPU expert offload;
  use Ampere-compatible kernels. [Project](https://github.com/turboderp-org/exllamav3).
- **Project Maya:** large GLM/DeepSeek streaming experiments, not a promise that
  64 GB RAM plus 34 GB nominal VRAM fits every pack. [Project](https://github.com/mw00/project-maya).

Qwen3.8-27B Q4 and 24–35B MoEs at larger quants are sensible initial capacity
experiments. Qwen3-Coder-Next Q4, GPT-OSS-120B and Flash-Next still require host
offload/caching. Check actual quant sizes and architecture support before any
download. Ampere unlock does not add native FP8/NVFP4 hardware instructions;
format support depends on compatible dequantization kernels.

When adding the 3060, compare all-three inference with the faster pair plus an
independent 3060 workload/display role. More VRAM can reduce offload while slower
compute can increase latency. Publish measured prefill, TTFT and decode separately.

## 5. Client/router and completion criteria

The Windows router uses authenticated OpenAI-compatible port 10000 and owns one
worker at a time. Its current single-GPU hardware guard deliberately refuses a
pair. Do not run the Windows router unchanged on Linux or disable its safeguards.

Create a native authenticated router/catalog after validating engines; preserve
OpenAI-compatible model selection, chat, streaming, tools and DSH integration.
Keep one backend loaded at a time unless a deliberate multi-service configuration
is validated. Re-establish Tailscale access on this host without publishing keys,
device addresses or broad unauthenticated listeners. Host self-access is not a
remote-client connection test. No new schedules or global process cleanup are
authorized by this handoff.

Update this document and README with actual installed hardware, engine pins,
per-card unlock proof, peer-transfer results, model placement, context tests,
RAM/VRAM peaks, thermals, client checks and unresolved limitations. Keep raw data
private. Publish a reviewed example update to the public NVIDIA Linux repository.
Do not modify the AMD Linux machine, restore retired settings or present this
preparation as a completed Linux deployment.
