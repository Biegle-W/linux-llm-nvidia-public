#!/usr/bin/env python3
"""Export reviewed reference files to the matching public checkout; never push history."""
import argparse
import hashlib
import json
import struct
from pathlib import Path
import re
import subprocess

RETIRED_FILES = (
    'config/bolt-offload-runtime.json',
    'scripts/bolt_runtime.py',
    'scripts/supervise_bolt.py',
    'scripts/bolt_offload_hook/checkpoint_cache.py',
    'scripts/bolt_offload_hook/compact_pool.py',
    'scripts/bolt_offload_hook/host_trim.py',
    'scripts/bolt_offload_hook/sitecustomize.py',
    'tests/test_bolt_runtime.py',
    'tests/test_bolt_loading_cleanup.py',
    'tests/test_bolt_pool_torch.py',
    'tests/test_bolt_readonly_cache.py',
    'config/super-offload-runtime.json', 'scripts/super_runtime.py', 'scripts/supervise_super.py', 'tests/test_super_runtime.py', 'tests/test_super_bounded_policy.py', 'tests/test_super_request_state.py', 'scripts/super_offload_hook/compact_pool.py', 'scripts/super_offload_hook/repack.py', 'scripts/super_offload_hook/sitecustomize.py', 'scripts/super_offload_hook/placement.py', 'scripts/super_offload_hook/checkpoint_cache.py', 'scripts/super_offload_hook/reuse.py', 'scripts/super_offload_hook/file_backing.py', 'scripts/super_offload_hook/host_trim.py')


SAMPLE_MEDIA = (
    'assets/samples/comfy/wan-baseline-1080p.mp4', 'assets/samples/comfy/wan-baseline-1080p-poster.png',
    'assets/samples/comfy/wan-raylight-1080p.mp4', 'assets/samples/comfy/wan-raylight-1080p-poster.png',
    'assets/samples/comfy/wan-baseline-720p.mp4', 'assets/samples/comfy/wan-baseline-720p-poster.png',
    'assets/samples/comfy/ltx-mesh-720p.mp4', 'assets/samples/comfy/ltx-mesh-720p-poster.png',
    'assets/samples/comfy/ltx-mesh-1080p.mp4', 'assets/samples/comfy/ltx-mesh-1080p-poster.png',
    'assets/samples/comfy/qwen-turbo-1k.png', 'assets/samples/comfy/qwen-turbo-2k.png',
    'assets/samples/comfy/flux-klein-1k.png', 'assets/samples/comfy/flux-klein-2k.png',
    'assets/samples/comfy/wan-baseline.mp4', 'assets/samples/comfy/wan-raylight.mp4',
    'assets/samples/comfy/ltx-mesh.mp4',
    'assets/samples/comfy/wan-baseline-poster.png', 'assets/samples/comfy/wan-raylight-poster.png',
    'assets/samples/comfy/ltx-mesh-poster.png',
)

FILES = (
    'docs/POWERLOSS-RECOVERY-20261105.md', 'docs/validation-results/20261105-powerloss-recovery.json',
    'docs/IQ1S-WEIGHT-REMOVAL-20261105.md', 'docs/validation-results/20261105-iq1s-weight-removal.json',
    'scripts/flash_iq1m_strata_runtime.py', 'tests/test_flash_iq1m_strata_runtime.py',
    'config/flash-iq1m-strata-runtime.json', 'docs/FLASH-IQ1M-STRATA-20261105.md',
    'docs/validation-results/20261105-flash-iq1m-strata.json',
    'docs/ALL-MODEL-RAM-CEILINGS-20261105.md', 'docs/validation-results/20261105-all-model-ram-ceilings.json',
    'docs/STRATA-0211-QUALIFICATION-20261105.md', 'docs/validation-results/20261105-strata0211-qualification.json',
    'scripts/update_reviewed.py',
    'docs/MAYA-1154-QUALIFICATION-20261105.md', 'docs/validation-results/20261105-maya1154-qualification.json',
    'scripts/daily_update_terminal.py', 'scripts/update_short_qualification.py', 'scripts/update_native_builders.py',
    'tests/test_update_restore.py', 'docs/DAILY-UPDATER-RESTORATION-20261105.md',
    'docs/validation-results/20261105-daily-updater-restoration.json',
    'docs/ENGINE-REFRESH-AND-WEIGHT-SHARING-20261105.md', 'docs/ALL-ENTRY-BENCHMARKS-20261105.md',
    'docs/validation-results/20261105-engine-refresh.json',
    'patches/maya-ds4-file-cache-target-v1153.patch', 'scripts/patches/sglang-hetero-ct-w4a8-mtp-20261105.patch',
    'docs/COMFY-VIDEO-HD-ENTRIES-20261105.md', 'docs/validation-results/20261105-comfy-video-hd-entries.json',
    'config/comfy-workflows/wan22-5b-720p.json', 'config/comfy-workflows/wan22-5b-720p.api.json',
    'config/comfy-workflows/wan22-5b-1080p.json', 'config/comfy-workflows/wan22-5b-1080p.api.json',
    'config/comfy-workflows/ltx23-mesh-720p.json', 'config/comfy-workflows/ltx23-mesh-720p.api.json',
    'config/comfy-workflows/ltx23-mesh-1080p.json', 'config/comfy-workflows/ltx23-mesh-1080p.api.json',
    'scripts/comfy_wan_memory.py', 'tests/test_comfy_wan_memory.py',
    'docs/WAN1080-FIX-20261105.md', 'docs/benchmark-results/20261105-wan1080-fix.json',
    'docs/COMFY-VIDEO-720P1080P-20261105.md', 'docs/benchmark-results/20261105-comfy-video-720p1080p.json',
    'config/comfy-video-entries.json', 'config/comfy-workflows/wan22-5b.json',
    'config/comfy-workflows/wan22-5b.api.json', 'config/comfy-workflows/ltx23-mesh.json',
    'config/comfy-workflows/ltx23-mesh.api.json', 'scripts/comfy_video_entries.py', 'scripts/comfy_video_job.py',
    'tests/test_comfy_video_entries.py', 'docs/COMFY-VIDEO-ENTRIES-20261104.md',
    'docs/validation-results/20261104-comfy-video-entries.json',
    *SAMPLE_MEDIA,
    'assets/samples/comfy/README.md', 'assets/samples/comfy/manifest.json',
    'tests/test_public_sample_media.py',
    'docs/COMFY-VIDEO-DUAL-GPU-20261104.md', 'docs/benchmark-results/20261104-comfy-video-dual-gpu.json',
    'config/comfy-video-trial.json', 'config/comfy-video-requirements.lock',
    'scripts/comfy_mesh_gguf.py', 'scripts/comfy_video_trial.py',
    'scripts/comfy_video_nodes/__init__.py', 'scripts/comfy_video_hook/sitecustomize.py',
    'scripts/patches/raylight-native-ignored-gpu.patch', 'scripts/patches/mesh-ltx-rotary-matrix.patch',
    'tests/test_comfy_video_audit.py',
    'docs/COMFY-2K4K-20261104.md', 'docs/benchmark-results/20261105-comfy-2k4k.json',
    'config/comfy-runtime.json', 'config/comfy-requirements.lock',
    'config/comfy-workflows/qwen-image-2.1-turbo.json', 'config/comfy-workflows/qwen-image-2.1-turbo.api.json',
    'config/comfy-workflows/flux3-klein.json', 'config/comfy-workflows/flux3-klein.api.json',
    'scripts/comfy_download.py', 'scripts/comfy_run.py', 'scripts/comfy_worker.py', 'scripts/comfy_nodes/__init__.py',
    'scripts/install_comfy_shortcut.py', 'tests/test_comfy_residency.py',
    'docs/COMFY-DUAL-GPU-20261105.md', 'docs/benchmark-results/20261105-comfy-dual-gpu.json',
    'docs/UNUSED-QWEN-GGUF-REMOVAL-20261104.md', 'docs/validation-results/20261104-unused-qwen-gguf-removal.json',
    'docs/BOLT-AWQ-REMOVAL-20261104.md', 'docs/validation-results/20261104-bolt-awq-removal.json',
    'config/bolt-iq2-runtime.json', 'scripts/bolt_iq2_runtime.py', 'tests/test_bolt_iq2_runtime.py',
    'docs/BOLT-IQ2-ENTRY-20261104.md', 'docs/benchmark-results/20261104-bolt-iq2-entry.json',
    'docs/ALL-ENTRY-BENCHMARKS-PRE-IQ2-20261104.md',
    'config/bolt-iq2-trial.json', 'scripts/bolt_iq2_trial.py', 'scripts/bolt_iq2_worker.py', 'tests/test_bolt_iq2_trial.py',
    'docs/BOLT-NATIVE-IQ2-20261104.md', 'docs/benchmark-results/20261104-bolt-native-iq2.json',
    'docs/RAM96-RESTORATION-20261104.md', 'docs/benchmark-results/20261104-ram96-restoration.json', 'docs/BOLT-IQ2-AND-PROMETHEVS-20261104.md',
    'docs/RAM96-PREPARATION-20261104.md', 'docs/validation-results/20261104-ram96-preparation.json', 'tests/test_ram96_capacity.py',
    'config/flash-iq1s-runtime.json', 'scripts/flash_iq1s_runtime.py', 'tests/test_flash_iq1s_runtime.py',
    'docs/FLASH-IQ1S-ENTRY-20261104.md', 'docs/ALL-ENTRY-BENCHMARKS-20261104.md',
    'docs/benchmark-results/20261104-flash-iq1s-entry.json', 'docs/benchmark-results/20261104-all-entry-benchmarks.json',
    'docs/RAM26-28-RERUN-20261104.md', 'docs/benchmark-results/20261104-ram26-28-rerun.json',
    'config/tensorfold-runtime.json', 'scripts/tensorfold_runtime.py', 'tests/test_tensorfold_runtime.py',
    'docs/TENSORFOLD-ENTRY-AND-FLASH-IQ1S-20261104.md', 'docs/benchmark-results/20261104-tensorfold-entry-and-flash-iq1s.json',
    'docs/TENSORFOLD-AND-UNSLOTH-ASSESSMENT-20261104.md', 'docs/benchmark-results/20261104-tensorfold-and-unsloth.json',
    'docs/REQUESTED-TWO-MODEL-CHECKS-20261103.md', 'docs/benchmark-results/20261103-requested-two-model-checks.json',
    'docs/DSH-STARTUP-REPAIR-20261103.md', 'docs/validation-results/20261103-dsh-startup.json', 'tests/test_dsh_startup.py',
    'docs/PROVIDER-ABORT-BUFFERING-20261103.md', 'docs/validation-results/20261103-provider-abort-buffering.json',
    'docs/FUTURE-MODEL-TEST-PLAN.md',
    'docs/UNLOCKED-VRAM-ONLY-20261103.md', 'docs/benchmark-results/20261103-unlocked-vram-only.json', 'tests/test_model_availability.py',
    'config/hardware/61-local-igpu-primary.rules',
    'config/hardware/90-local-igpu-primary.conf',
    'config/hardware/gpu-transport.json',
    'config/hardware/local-llm-transport-verify.service',
    'docs/Z690-13900KS-MIGRATION-20261103.md', 'scripts/gpu_transport_health.py', 'tests/test_gpu_transport_health.py',
    'docs/VRAM256-OPTIMIZATION-20261103.md',
    'docs/benchmark-results/20261103-vram256-optimization.json',
    'config/maya-glm-runtime.json',
    'docs/HEADLESS-VRAM256-20261102.md',
    'docs/COMMUNITY-OPTIMIZATION-20261102.md',
    'docs/benchmark-results/20261102-community-screens.json',
    'scripts/cli_short_models.py',
    'docs/CLI-SHORT-MODEL-TESTS.md',
    'tests/test_cli_short_models.py',
    'docs/HYPERQWEN-STARTUP-REATTACH-FIX.md',
    'tests/test_worker_reattach_exit.py',
    'docs/SGLANG-56K-448MIB-20261101.md',
    'docs/validation-results/20261101-sglang-56k-448mib.json',
    'tests/test_sglang_vram_floor.py',
    'docs/QWEN-LARGER-CONTEXT-20261101.md',
    'docs/validation-results/20261101-qwen-larger-context.json',
    'docs/QWEN-48K-CONTEXT-20261101.md',
    'docs/validation-results/20261101-qwen-48k.json',
    'docs/NEMOTRON-SUPER-REMOVAL-20261101.md',
    'docs/SHORT-TOOL-BENCHMARKS-20261101.md',
    'docs/benchmark-results/20261101-short-tool.json',
    'config/maya-unsloth-runtime.json',
    'docs/API-SWITCH-CHECKS-20261101.md',
    'docs/API-SWITCH-VRAM-20261101.md',
    'docs/MAYA-UNSLOTH-20261101.md',
    'docs/SGLANG-SUPER-SHORT-FIXES-20261101.md',
    'scripts/context_capacity.py',
    'scripts/short_tool_metrics.py',
    'tests/test_context_capacity.py',
    'tests/test_metrics_stream_completion.py',
    'tests/test_pair_gpu_telemetry.py',
    'tests/test_qwen_vram_settle.py',
    'tests/test_short_tool_metrics.py',
    'tests/test_vllm_switch_wait.py',
    'docs/validation-results/20261101-permanent-pair-p2p.json',
    'docs/P2P-PERMANENT-PAIR-20261101.md',
    'scripts/boot_peer_verify.py',
    'scripts/pair_p2p_health.py',
    'scripts/verify_pair_p2p.cu',
    'tests/test_pair_p2p_health.py',
    'docs/CONTEXT-VALIDATION-POLICY-20261101.md',
    'docs/DSH-ROUTER-CLEANUP-20261101.md',
    'docs/NEMOTRON-CONTEXT-20261101.md',
    'docs/validation-results/20261101-dsh-router-cleanup.json',
    'docs/validation-results/20261101-super-context.json',
    'scripts/smoke_dsh_tools.py',
    'docs/DSH-HYPERQWEN-SEARCH-20261101.md',
    'docs/BOLT-CONTEXT-20261101.md',
    'docs/validation-results/20261101-bolt-context.json',
    'tests/test_dsh_registration.py',
    'scripts/terminal_exec.py',
    'tests/test_terminal_exec.py',
    'docs/BACKGROUND-TERMINALS-20261101.md',
    'docs/validation-results/20261101-background-terminals.json',
    'docs/BOLT-TOOL-CALLING-20261031.md',
    'docs/validation-results/20261031-bolt-tool-calling.json',
    'docs/BOLT-TWO-GPU-LOADING-20261031.md',
    'docs/validation-results/20261031-bolt-two-gpu-loading.json',
    'docs/WORKER-RAM-64GB-20261031.md', 'docs/validation-results/20261031-worker-ram-64gb.json',
    'config/deepseek-unsloth-runtime.json',
    'scripts/strata_unsloth_runtime.py',
    'tests/test_strata_unsloth_runtime.py',
    'docs/DEEPSEEK-UNSLOTH-CONTEXT-20261031.md',
    'docs/validation-results/20261031-unsloth-strata-context.json',
    'patches/llama-demand-mmap-prefault.patch',
    'docs/DEEPSEEK-DYNAMIC31-20261031.md',
    'docs/validation-results/20261031-deepseek-dynamic31.json',
    'tests/test_bolt_request_state.py',
    'docs/BOLT-MAYA-RELIABILITY-20261031.md',
    'docs/benchmark-results/20261031-bolt-maya-reliability.json',
    'docs/GPU-PAIR-AUX-OPTIMIZATION-20261031.md',
    'docs/benchmark-results/20261031-pair-main-aux.json',
    'docs/NEMOTRON-INT4-OFFLOAD-20261031.md',
    'docs/validation-results/20261031-nemotron-int4-offload.json',
    'docs/validation-results/20261031-pair-p2p.json',
    'docs/TERMINAL-ATTENTION-20261031.md',
    'docs/PEX-ACS-PAIR-20261031.md',
    'docs/P2P-DYNAMIC-UNLOCK-20261031.md',
    'scripts/dracut/91local-llm-gpu-unlock/module-setup.sh',
    'scripts/dracut/91local-llm-gpu-unlock/unlock-auto.sh',
    'tests/test_gpu_unlock_auto.py',
    'docs/P2P-POSTBOOT-20261031.md',
    'docs/P2P-DRIVER-PREPARATION-20261030.md',
    'docs/THREE-GPU-PREPARATION-20261030.md',
    'docs/UNSLOTH-COMFY-DESKTOP-20261030.md',
    'docs/validation-results/20261030-unsloth-comfy-desktop.json',
    'docs/STRATA-OFFICIAL-APP-20261030.md',
    'docs/validation-results/20261030-strata-official-app.json',
    'docs/OPENCAT-HEADLINES-20261030.md',
    'docs/validation-results/20261030-opencat-headlines.json',
    'docs/OPENCAT-SEARCH-MODEL-20261030.md',
    'docs/validation-results/20261030-opencat-search-model.json',
    'network/web_search.py', 'tests/test_web_search.py', 'config/web-search.example.json',
    'docs/RESPONSES-WEB-SEARCH-20261030.md',
    'docs/validation-results/20261030-responses-web-search.json',
    'docs/OPENCAT-RESPONSES-20261030.md',
    'docs/validation-results/20261030-opencat-responses.json',
    'docs/API-RELIABILITY-20261030.md',
    'docs/validation-results/20261030-api-reliability.json',
    'docs/HARDWARE-TUNING-QUALIFICATION-20261030.md',
    'docs/validation-results/20261030-hardware-tuning.json',
    'docs/HARDWARE-TUNING-RESEARCH-20261029.md',
    'docs/validation-results/20261029-hardware-tuning-research.json',
    'docs/TERMINAL-LIFETIME-20261029.md',
    'docs/validation-results/20261029-terminal-lifetime.json',
    'docs/BENCHMARK-PRESSURE-GUARD-64GB-20261029.md',
    'docs/benchmark-results/20261029-pressure-guard.json',
    'docs/BENCHMARK-SSD-SWAP-64GB-20261029.md',
    'docs/benchmark-results/20261029-ssd-relaxed-swap.json',
    'docs/BENCHMARK-64GB-20261029.md',
    'docs/benchmark-results/20261029-full-ram.json',
    'docs/FULL-RAM-RESTORATION-20261029.md',
    'docs/validation-results/20261029-full-ram-restoration.json',
    'scripts/daily_engine_update.py',
    'scripts/daily_update_owner.py',
    'scripts/install_daily_engine_update.py',
    'scripts/update_transaction.py',
    'scripts/update_policy.py',
    'scripts/update_builders.py',
    'scripts/update_qualification.py',
    'scripts/update_publish.py',
    'tests/test_daily_engine_update.py',
    'config/daily-update.json',
    'config/daily-update-versions.json',
    'network/systemd/nvidia-daily-engine-update.service',
    'network/systemd/nvidia-daily-engine-update.timer',
    'network/systemd/nvidia-daily-engine-update-recover.service',
    'docs/DAILY-ENGINE-UPDATES.md',
    'docs/DAILY-ENGINE-UPDATE-POLICY.md',
    'docs/QWEN-RELAXED-SWAP-20261029.md',
    'docs/validation-results/20261029-qwen-relaxed-swap.json',
    'docs/validation-results/20261029-daily-update-setup.json',

    'docs/QWEN-CURRENT-GUARDS-20261029.md', 'docs/validation-results/20261029-qwen-current-guards.json',
    'docs/MAYA-DEMAND-CACHE-20261029.md', 'docs/benchmark-results/20261029-maya-demand-cache.json', 'config/maya-cachebound-runtime.json', 'patches/maya-ds4-file-cache-target.patch', 'scripts/build_maya_file_cache_bound.py', 'scripts/maya_cachebound_runtime.py', 'tests/test_maya_cachebound_runtime.py', 'tools/maya-file-cache-bound/test_cache_bound.cpp',
    'docs/MAYA-DS4-VRAM512-FOLLOWUP-20261029.md', 'docs/benchmark-results/20261029-maya512-followup.json',
    'docs/MOE-VRAM512-20261029.md', 'docs/benchmark-results/20261029-moe-vram512.json',
    'docs/ALL-PROFILES-HOST-RESERVE2-20261029.md', 'docs/validation-results/20261029-all-profiles-host-reserve2.json',
    'docs/QWEN-HOST-RESERVE2-20261028.md', 'docs/benchmark-results/20261028-qwen-host-reserve2.json',
    'tests/test_host_ram_reserve.py',
    'docs/QWEN-STRATA-LCZ-20261028.md', 'docs/benchmark-results/20261028-qwen-strata-lcz.json',
    'docs/REDUCED-RAM-20261028.md', 'docs/benchmark-results/20261028-reduced-ram.json',
    'README.md', 'AGENTS.md', 'docs/CURRENT-STATE.md', 'docs/AMD-PARITY-HANDOFF-20261027.md', 'docs/BENCHMARK-HISTORY.md', 'docs/AMD-NVIDIA-GAP-AUDIT-20261027.md', '.gitignore', '.gitattributes', 'docs/MIGRATION-HANDOFF.md', 'docs/REPOSITORY-MAP.md', 'docs/LOCAL-SETUP.md',
    'docs/VALIDATION-20261026.md', 'docs/BENCHMARK-20261026.md',
    'scripts/build_native_llama.sh', 'scripts/check_local_api.py',
    'scripts/start_model.sh', 'scripts/native_linux_gpu_unlock.py',
    'scripts/test_native_linux_gpu_unlock.py',
    'scripts/gpu_unlock_health.py', 'scripts/install_gpu_unlock_health.py',
    'tests/test_gpu_unlock_health.py', 'docs/GPU-UNLOCK-HEALTH.md', 'docs/UNLOCK-SETUP-20261026.md',
    'docs/UNLOCK-V2-BENCHMARK-20261031.md', 'docs/benchmark-results/20261031-unlock-v2-gemm.json',
    'docs/BENCHMARK-UNLOCK-20261026.md', 'docs/ENGINE-TESTS-20261026.md',
    'scripts/run_bounded_test.sh',
    'docs/QWEN27B-GPU-ONLY-20261026.md', 'scripts/sync_public.py', 'docs/PUBLIC-SYNC.md',
    'docs/DENSE-ENGINE-OPTIMIZATION-20261027.md', 'scripts/serve_qwen27b_engines.py',
    'scripts/test_sglang_quantized_embedding.py',
    'scripts/patches/sglang-int8-embedding-sm86.patch',
    'scripts/patches/sglang-gpu-placement-audit.patch',
    'scripts/patches/vllm-dflash-meta-share.patch',
    'scripts/patches/vllm-draft-placement-audit.patch',
    'config/maintained-profiles.json', 'config/model-catalog.example.json',
    'scripts/profile_catalog.py', 'docs/MAINTAINED-PROFILES.md',
    'docs/DEEPSEEK-STRATA-CONTEXT-20261027.md',
    'network/backend_proxy.py', 'network/request_admission.py', 'tests/test_request_admission.py',
    'docs/ROUTER-IMPROVEMENTS-20261028.md', 'docs/validation-results/20261028-router-improvements.json',
    'network/api.py', 'network/hub.py', 'network/hub_transport.py', 'network/router.py', 'network/worker_manager.py', 'network/install.py', 'network/README.md',
    'scripts/serve_router_moe.py', 'scripts/router_client.py', 'scripts/open_dsh.py',
    'dsh/configure.py', 'dsh/run', 'dsh/package.json', 'dsh/package-lock.json',
    'config/terminal-runtime.json', 'scripts/install_visible_terminal_runtime.py', 'tests/test_minimized_terminals.py',
    'tests/test_backend_console.py', 'docs/ENGINE-SWITCHING-20261028.md', 'docs/validation-results/20261028-engine-switching.json',
    'tests/test_router.py', 'tests/test_api_gateway.py', 'docs/ROUTER-DEPLOYMENT-20261027.md',
    'assets/icons/README.md', 'assets/icons/strata.svg', 'assets/icons/maya.svg',
    'assets/icons/sglang.svg', 'assets/icons/dsh.svg', 'assets/icons/hyperqwen.png',
    'scripts/benchmark_models.py', 'tests/test_benchmark_metrics.py', 'scripts/visible_terminal.py',
    'docs/BENCHMARK-20261027-101219.md', 'docs/benchmark-results/20261027-101219.json',
    'docs/STORAGE-POLICY.md', 'scripts/storage_policy.py', 'tests/test_storage_policy.py',
    'docs/BENCHMARK-REPORTING.md',
    'docs/CONTEXT-EXPANSION-20261027.md', 'docs/benchmark-results/20261027-context-expansion.json',
    'docs/FORUM-OPTIMIZATION-SOURCES.md',
    'docs/SGLANG-TUNING-20261027.md', 'docs/benchmark-results/20261027-sglang-tuning.json',
    'docs/SGLANG-W4A8-20261027.md', 'docs/benchmark-results/20261027-sglang-w4a8.json',
    'scripts/patches/sglang-mlp-w4a8-sm86.patch',
    'docs/SGLANG-HETERO-MTP-20261028.md', 'docs/benchmark-results/20261028-sglang-hetero-mtp.json',
    'scripts/patches/sglang-hetero-ct-w4a8-mtp.patch',
    'docs/SGLANG-MTP3-512MIB-20261028.md', 'docs/benchmark-results/20261028-sglang-mtp3-512mib.json',
    'config/sglang-runtime.json', 'scripts/sglang_runtime.py', 'tests/test_sglang_runtime.py',
    'docs/SGLANG-DEPLOYMENT-20261028.md', 'docs/benchmark-results/20261028-sglang-deployment.json',
    'docs/SGLANG-38K-QUALIFICATION-20261028.md', 'docs/benchmark-results/20261028-sglang-38k-qualification.json',
    'docs/SGLANG-CONTEXT-20261028.md', 'docs/benchmark-results/20261028-sglang-context.json',
    'docs/INFERENCE-SWAP-POLICY.md', 'docs/UNLOCK-IMPACT-20261027.md',
    'scripts/inference_swap_guard.py', 'scripts/supervise_dense.py', 'tests/test_inference_swap_guard.py',
    'docs/UNUSED-MODEL-CLEANUP-20261027.md', 'docs/benchmark-results/20261027-dspark-screening.json',
    'docs/MOE-OPTIMIZATION-20261027.md', 'docs/benchmark-results/20261027-moe-optimized.json',
    'scripts/patches/maya-lazy-cpu-vision.patch', 'tests/test_maya_lazy_vision.py',
    'tests/test_worker_budgets.py',
    'network/idle_control.py', 'scripts/native_idle_policy.py',
    'scripts/lifecycle_telemetry.py', 'scripts/stage_engine_candidate.py',
    'config/inference-policy.json', 'scripts/inference_policy.py', 'tests/test_inference_policy.py',
    'docs/ALL-ENGINE-POLICY-20261028.md', 'docs/validation-results/20261028-all-engine-policy.json',
    'tests/test_idle_policy.py', 'tests/test_lifecycle_telemetry.py',
    'tests/test_engine_staging.py', 'tests/test_moe_supervisor.py', 'tests/test_supervisor_shutdown.py', 'docs/OPERATIONAL-LIFECYCLE.md',
)
BLOCK = re.compile(r'/(?:home|Users)/[^/\s]+|GPU-[0-9a-fA-F-]{16,}|'
                   r'gh[pousr]_[A-Za-z0-9]{20,}|github_pat_[A-Za-z0-9_]+|'
                   r'-----BEGIN (?:RSA |OPENSSH |EC )?PRIVATE KEY-----|'
                   r'[A-Za-z0-9._%+-]+@(?!example\.)[A-Za-z0-9.-]+\.[A-Za-z]{2,}')


def privacy_scan_text(relative, content):
    text = content.replace('git@github.com:', '')
    if relative == 'config/deepseek-unsloth-runtime.json':
        # Reviewed upstream Retina icon filenames are hash-map keys, not emails.
        # Limit normalization to those exact asset paths and SHA256 entries.
        icon = (r'("runtimes/strata-unsloth-029/source/apps/desktop/src-tauri/icons/'
                r'(?:128x128@2x|ios/AppIcon-[0-9.x]+@[123]x(?:-1)?)\.png"'
                r'\s*:\s*"[0-9a-f]{64}")')
        text = re.sub(icon, lambda m: m[0].replace('@', '_'), text)
    if relative.endswith('.patch'):
        # Scan the source text, without mistaking diff markers for email characters.
        text = '\n'.join(line[1:] if line[:1] in ('+', '-')
                         and not line.startswith(('+++', '---')) else line
                         for line in text.splitlines())
    return text


def strip_private_workflow(content):
    """AMD-style local Codex workflow details stay out of public exports."""
    # Split literals so exporting this source cannot strip its own implementation.
    start = '<!-- private-' + 'codex-context:start -->'
    end = '<!-- private-' + 'codex-context:end -->'
    if start not in content and end not in content:
        return content
    if content.count(start) != 1 or content.count(end) != 1:
        raise ValueError('Unbalanced private workflow markers')
    before, remainder = content.split(start)
    if end not in remainder:
        raise ValueError('Reversed private workflow markers')
    _, after = remainder.split(end)
    return (before.rstrip() + '\n\n' + after.lstrip()).rstrip() + '\n'


def validate_sample_media(relative, content, records):
    """Accept only reviewed sample bytes; never broadly bypass the privacy scan."""
    assert relative in SAMPLE_MEDIA, 'Unreviewed binary export'
    record=records[relative]
    assert len(content)==record['bytes'] and hashlib.sha256(content).hexdigest()==record['sha256'], 'Sample content changed; review media and metadata again'
    if relative.endswith('.png'):
        assert content.startswith(b'\x89PNG\r\n\x1a\n'), 'Expected PNG sample'
        pos=8;types=[]
        while pos<len(content):
            length=struct.unpack('>I',content[pos:pos+4])[0]
            kind=content[pos+4:pos+8];types.append(kind)
            assert kind in (b'IHDR',b'PLTE',b'IDAT',b'IEND',b'tRNS'), 'Unreviewed PNG metadata chunk'
            pos+=length+12
        assert pos==len(content) and types[0]==b'IHDR' and types[-1]==b'IEND'
    else:
        assert content[4:8]==b'ftyp', 'Expected reviewed MP4 sample'


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('checkout', type=Path)
    args = parser.parse_args()
    source = Path(__file__).resolve().parents[1]
    target = args.checkout.resolve()
    origin = subprocess.check_output(['git', '-C', str(target), 'remote', 'get-url', 'origin'], text=True).strip()
    if origin not in ('https://github.com/Biegle-W/linux-llm-nvidia-public.git',
                      'git@github.com:Biegle-W/linux-llm-nvidia-public.git'):
        raise SystemExit('Refusing export to an unexpected repository.')
    if subprocess.check_output(['git', '-C', str(target), 'status', '--porcelain'], text=True).strip():
        raise SystemExit('Public checkout must be clean before export.')
    exports = {}
    manifest=json.loads((source/'assets/samples/comfy/manifest.json').read_text())
    media_records={}
    for row in manifest['samples']:
        base='assets/samples/comfy/'
        media_records[base+row['file']]=dict(bytes=row['bytes'],sha256=row['sha256'])
        if row.get('poster'):
            media_records[base+row['poster']]=dict(bytes=row['poster_bytes'],sha256=row['poster_sha256'])
    assert set(media_records)==set(SAMPLE_MEDIA),'Sample manifest and reviewed allowlist differ'
    for relative in FILES:
        binary = relative == 'assets/icons/hyperqwen.png' or relative in SAMPLE_MEDIA
        content = (source / relative).read_bytes() if binary else (source / relative).read_text()
        if relative in SAMPLE_MEDIA:validate_sample_media(relative,content,media_records)
        if relative == 'assets/icons/hyperqwen.png' and not content.startswith(b'\x89PNG\r\n\x1a\n'):
            raise SystemExit('Expected official PNG artwork.')
        if relative == 'README.md':
            content = content.replace('# Linux LLM NVIDIA\n', '# Linux LLM NVIDIA — public reference\n', 1)
        if not binary:
            content = strip_private_workflow(content)
        if not binary and BLOCK.search(privacy_scan_text(relative, content)):
            raise SystemExit(f'Privacy check failed for {relative}; review locally.')
        exports[relative] = content
    for relative in RETIRED_FILES:
        retired = target / relative
        if retired.is_symlink():raise SystemExit('Refusing retired symlink: '+relative)
        retired.unlink(missing_ok=True)
    for relative, content in exports.items():
        destination = target / relative
        if destination.is_symlink() or any(parent.is_symlink() for parent in destination.parents if parent != target.parent):
            raise SystemExit(f'Refusing symlink destination: {relative}')
        destination.parent.mkdir(parents=True, exist_ok=True)
        if isinstance(content, bytes):
            destination.write_bytes(content)
        else:
            destination.write_text(content)
        destination.chmod((source / relative).stat().st_mode & 0o777)
    print(f'Exported {len(exports)} reviewed files. Review git diff before committing and pushing.')


if __name__ == '__main__':
    main()
