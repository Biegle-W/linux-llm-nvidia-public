#!/usr/bin/env python3
"""Export reviewed reference files to the matching public checkout; never push history."""
import argparse
from pathlib import Path
import re
import subprocess

FILES = (
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
    'network/router.py', 'network/worker_manager.py', 'network/install.py', 'network/README.md',
    'scripts/serve_router_moe.py', 'scripts/router_client.py', 'scripts/open_dsh.py',
    'dsh/configure.py', 'dsh/run', 'dsh/package.json', 'dsh/package-lock.json',
    'config/terminal-runtime.json', 'scripts/install_visible_terminal_runtime.py', 'tests/test_minimized_terminals.py',
    'tests/test_backend_console.py', 'docs/ENGINE-SWITCHING-20261028.md', 'docs/validation-results/20261028-engine-switching.json',
    'tests/test_router.py', 'docs/ROUTER-DEPLOYMENT-20261027.md',
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
    for relative in FILES:
        binary = relative == 'assets/icons/hyperqwen.png'
        content = (source / relative).read_bytes() if binary else (source / relative).read_text()
        if binary and not content.startswith(b'\x89PNG\r\n\x1a\n'):
            raise SystemExit('Expected official PNG artwork.')
        if relative == 'README.md':
            content = content.replace('# Linux LLM NVIDIA\n', '# Linux LLM NVIDIA — public reference\n', 1)
        if not binary:
            content = strip_private_workflow(content)
        if not binary and BLOCK.search(privacy_scan_text(relative, content)):
            raise SystemExit(f'Privacy check failed for {relative}; review locally.')
        exports[relative] = content
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
