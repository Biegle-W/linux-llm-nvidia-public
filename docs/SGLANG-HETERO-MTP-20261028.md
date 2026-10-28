# Isolated SGLang heterogeneous TP2 and MTP — October 28, 2026

The user accepted the earlier MLP-only W4A8 prefill tradeoff and requested heterogeneous TP2/MTP testing for generation speed. This study started late October 27 and uses the temporarily reduced RAM configuration (45.55 GiB usable). HyperQwen remains the normal default; no candidate is promoted by this report.

Best completed MTP result: 84.63 decode tok/s at 16K, +32.51% over its matched TP2 control. It passed JSON, arithmetic and 14,686-input retrieval. MTP1 at 32K failed the headroom guard during retrieval, despite completing short timings. Corrected MTP3 at 32K failed its post-load headroom check (904/1,039 MiB free). These capacity failures prevent calling either a qualified 32K MTP replacement.

[Numeric settings, all attempts, samples and quality/resource evidence](benchmark-results/20261028-sglang-hetero-mtp.json). [Reproducible candidate patch](../scripts/patches/sglang-hetero-ct-w4a8-mtp.patch).

## VRAM-only models

| Model / quant / engine / measured trial | Prefill (tok/s) | First token (s) | Decode (tok/s) | Context limit (tokens) | Storage size (GB) | Storage location |
| --- | ---: | ---: | ---: | ---: | ---: | --- |
| Qwen3.8-27B / AutoRound INT4 + INT8 embedding / PP2 SGLang W4A8 reference (October 27) | 3,233.72 | 0.6877 | 45.69 | 32,768 | 15.79 | Samsung SSD 870 QVO SATA: `models/engine-tests/qwen38-27b-hyperqwen-fast` |
| Qwen3.8-27B / AutoRound INT4 + INT8 embedding / isolated SGLang / `hetero-tp2-no-mtp-tp-metrics-v8` | 1,653.52 | 1.3433 | 63.73 | 32,768 | 15.79 | Samsung SSD 870 QVO SATA: `models/engine-tests/qwen38-27b-hyperqwen-fast` |
| Qwen3.8-27B / AutoRound INT4 + INT8 embedding / isolated SGLang / `hetero-tp2-no-mtp-bf16-slot1-v11` | 1,716.45 | 1.2947 | 64.18 | 32,768 | 15.79 | Samsung SSD 870 QVO SATA: `models/engine-tests/qwen38-27b-hyperqwen-fast` |
| Qwen3.8-27B / AutoRound INT4 + INT8 embedding / isolated SGLang / `hetero-tp2-no-mtp-chunk128-v12` | 1,458.22 | 1.5292 | 64.20 | 32,768 | 15.79 | Samsung SSD 870 QVO SATA: `models/engine-tests/qwen38-27b-hyperqwen-fast` |
| Qwen3.8-27B / AutoRound INT4 + INT8 embedding / isolated SGLang / `hetero-tp2-no-mtp-16k-v13` | 1,712.66 | 1.3001 | 63.87 | 16,384 | 15.79 | Samsung SSD 870 QVO SATA: `models/engine-tests/qwen38-27b-hyperqwen-fast` |
| Qwen3.8-27B / AutoRound INT4 + INT8 embedding / isolated SGLang / `hetero-tp2-mtp1-16k-packedfc-v14` | 1,662.17 | 1.3454 | 70.25 | 16,384 | 15.79 | Samsung SSD 870 QVO SATA: `models/engine-tests/qwen38-27b-hyperqwen-fast` |
| Qwen3.8-27B / AutoRound INT4 + INT8 embedding / isolated SGLang / `hetero-tp2-mtp3-16k-packedfc-v14` | 1,662.79 | 1.3475 | 84.63 | 16,384 | 15.79 | Samsung SSD 870 QVO SATA: `models/engine-tests/qwen38-27b-hyperqwen-fast` |

## MoE models with CPU RAM offload

None tested in this study. Reduced-RAM MoE capacity is unqualified.

## MoE models with SSD streaming

None tested in this study. Existing profiles are unchanged.

## Attempt outcomes

- `hetero-tp2-no-mtp`: incomplete; No completed quality qualification; KV pools []; 0 audited W4A8 rank/projection entries. Error: Owned dense worker exited during loading..
  TypeError: ServerArgs.__init__() got an unexpected keyword argument 'default_chat_template_kwargs'
- `hetero-tp2-no-mtp-api-v2`: incomplete; No completed quality qualification; KV pools []; 0 audited W4A8 rank/projection entries. Error: Owned dense worker exited during loading..
  ValueError: Loaded weights leave no GPU memory for the KV cache under --rank-gpu-memory-mib on rank 0: the rank already uses 8.87 GiB (~9083 MiB) for weights and runtime state, which exhausts the per-rank budget. Raise --rank-gpu-memory-mib above that, or place fewer ranks on this GPU. If using speculative decoding, draft weights are now counted.
  ValueError: Loaded weights leave no GPU memory for the KV cache under --rank-gpu-memory-mib on rank 1: the rank already uses 7.41 GiB (~7588 MiB) for weights and runtime state, which exhausts the per-rank budget. Raise --rank-gpu-memory-mib above that, or place fewer ranks on this GPU. If using speculative decoding, draft weights are now counted.
- `hetero-tp2-no-mtp-textonly-v3`: incomplete; No completed quality qualification; KV pools [31817, 31817]; 0 audited W4A8 rank/projection entries. Error: Owned dense worker exited during loading..
- `hetero-tp2-no-mtp-packed-v4`: incomplete; No completed quality qualification; KV pools []; 0 audited W4A8 rank/projection entries. Error: Owned dense worker exited during loading..
  AttributeError: 'ModelRunner' object has no attribute 'quant_config'. Did you mean: 'load_config'?
- `hetero-tp2-no-mtp-packed-v5`: incomplete; No completed quality qualification; KV pools [32768, 32768]; 0 audited W4A8 rank/projection entries. Error: SGLang internal warm-up did not settle..
- `hetero-tp2-no-mtp-metrics-v6`: incomplete; No completed quality qualification; KV pools [32768, 32768]; 256 audited W4A8 rank/projection entries. Error: invalid literal for int() with base 10: 'cuda:0'.
- `hetero-tp2-no-mtp-audit-v7`: incomplete; No completed quality qualification; KV pools [32768, 32768]; 256 audited W4A8 rank/projection entries. Error: Invalid native prefill interval/count 2.0870097980000537/2.0; inspect qwen27b-sglang-warmup metric snapshots..
- `hetero-tp2-no-mtp-tp-metrics-v8`: complete; json passed, arithmetic passed, retrieval passed (29,434 input tokens); KV pools [32768, 32768]; 256 audited W4A8 rank/projection entries.
- `hetero-tp2-mtp1-tp-metrics-v8`: incomplete; No completed quality qualification; KV pools []; 0 audited W4A8 rank/projection entries. Error: Owned dense worker exited during loading..
  ValueError: sum(partitions)=64 does not match num_hidden_layers=1.
- `hetero-tp2-mtp3-tp-metrics-v8`: incomplete; No completed quality qualification; KV pools []; 0 audited W4A8 rank/projection entries. Error: Owned dense worker exited during loading..
  ValueError: sum(partitions)=64 does not match num_hidden_layers=1.
- `hetero-tp2-mtp1-draft-layout-v9`: incomplete; No completed quality qualification; KV pools [9388, 9388, 9388, 9388]; 0 audited W4A8 rank/projection entries. Error: [Errno 104] Connection reset by peer.
  RuntimeError: The expanded size of the tensor (65536) must match the existing size (65540) at non-singleton dimension 0.  Target sizes: [65536].  Tensor sizes: [65540]
- `hetero-tp2-mtp3-draft-layout-v9`: incomplete; No completed quality qualification; KV pools [4982, 4982, 4982, 4982]; 0 audited W4A8 rank/projection entries. Error: [Errno 104] Connection reset by peer.
  RuntimeError: The expanded size of the tensor (131072) must match the existing size (131088) at non-singleton dimension 0.  Target sizes: [131072].  Tensor sizes: [131088]
- `hetero-tp2-mtp1-mask-gc-v10`: incomplete; No completed quality qualification; KV pools [32768, 32768, 32768, 32768]; 0 audited W4A8 rank/projection entries. Error: Less than 1 GiB post-load GPU headroom; larger allocation rejected..
- `hetero-tp2-mtp3-mask-gc-v10`: incomplete; No completed quality qualification; KV pools [32768, 32768, 32768, 32768]; 0 audited W4A8 rank/projection entries. Error: Less than 1 GiB post-load GPU headroom; larger allocation rejected..
- `hetero-tp2-no-mtp-bf16-slot1-v11`: complete; json passed, arithmetic passed, retrieval passed (29,434 input tokens); KV pools [32768, 32768]; 256 audited W4A8 rank/projection entries.
- `hetero-tp2-mtp1-bf16-slot1-v11`: incomplete; No completed quality qualification; KV pools [32768, 32768, 32768, 32768]; 0 audited W4A8 rank/projection entries. Error: Less than 1 GiB post-load GPU headroom; larger allocation rejected..
- `hetero-tp2-mtp3-bf16-slot1-v11`: incomplete; No completed quality qualification; KV pools [32768, 32768, 32768, 32768]; 0 audited W4A8 rank/projection entries. Error: Less than 1 GiB post-load GPU headroom; larger allocation rejected..
- `hetero-tp2-no-mtp-chunk128-v12`: complete; json passed, arithmetic passed, retrieval passed (29,434 input tokens); KV pools [32768, 32768]; 256 audited W4A8 rank/projection entries.
- `hetero-tp2-mtp1-chunk128-v12`: incomplete; No completed quality qualification; KV pools [32768, 32768, 32768, 32768]; 0 audited W4A8 rank/projection entries. Error: Less than 1 GiB post-load GPU headroom; larger allocation rejected..
- `hetero-tp2-mtp3-chunk128-v12`: incomplete; No completed quality qualification; KV pools [32768, 32768, 32768, 32768]; 0 audited W4A8 rank/projection entries. Error: Less than 1 GiB post-load GPU headroom; larger allocation rejected..
- `hetero-tp2-no-mtp-16k-v13`: complete; json passed, arithmetic passed, retrieval passed (14,686 input tokens); KV pools [16384, 16384]; 256 audited W4A8 rank/projection entries.
- `hetero-tp2-mtp1-16k-v13`: invalid-draft-loader; json passed, arithmetic passed, retrieval passed (14,686 input tokens); KV pools [16384, 16384, 16384, 16384]; 256 audited W4A8 rank/projection entries.
  Diagnostic/partial timing only; not a qualified candidate: {'profile': 'qwen27b-sglang', 'context': 16384, 'variant': 'hetero-tp2-mtp1-16k-v13', 'repetitions': 3, 'prefill_tps': 1664.7476887254181, 'ttft_s': 1.342342971999642, 'client_decode_tps': 38.68534770206996, 'memory_high_gib': 30, 'memory_max_gib': 36}
- `hetero-tp2-mtp3-16k-v13`: interrupted-invalid-draft-loader; No completed quality qualification; KV pools [16384, 16384, 16384, 16384]; 0 audited W4A8 rank/projection entries.
- `hetero-tp2-mtp1-32k-packedfc-v14`: incomplete; json passed, arithmetic passed; KV pools [32768, 32768, 32768, 32768]; 256 audited W4A8 rank/projection entries. Error: Remote end closed connection without response.
  Diagnostic/partial timing only; not a qualified candidate: {'profile': 'qwen27b-sglang', 'context': 32768, 'variant': 'hetero-tp2-mtp1-32k-packedfc-v14', 'repetitions': 3, 'prefill_tps': 1662.5887356094133, 'ttft_s': 1.3452350180000394, 'client_decode_tps': 69.59142108435796, 'memory_high_gib': 30, 'memory_max_gib': 36}
- `hetero-tp2-mtp1-16k-packedfc-v14`: complete; json passed, arithmetic passed, retrieval passed (14,686 input tokens); KV pools [16384, 16384, 16384, 16384]; 256 audited W4A8 rank/projection entries.
- `hetero-tp2-mtp3-16k-packedfc-v14`: complete; json passed, arithmetic passed, retrieval passed (14,686 input tokens); KV pools [16384, 16384, 16384, 16384]; 256 audited W4A8 rank/projection entries.
- `hetero-tp2-mtp3-32k-packedfc-v15`: incomplete; No completed quality qualification; KV pools [32768, 32768, 32768, 32768]; 0 audited W4A8 rank/projection entries. Error: Less than 1 GiB post-load GPU headroom; larger allocation rejected..

## Source compatibility and isolation

The common profile uses TP2/PP1, physical ranks 0=RTX 3080 Ti and 1=RTX 3080, base ratio 9:8 and aligned MLP ratio 10:7 (10,240/7,168 intermediate channels). Admission budgets are 11,008/8,960 MiB, checked independently against actual NVML headroom. BF16 KV, chunk384, decode graphs at batch1, no prefix cache, one running request and zero CPU weight offload are retained; BF16 recurrent state/one Mamba slot applies to the matched MTP controls. The FP32/two-slot and chunk128 controls are separate recorded variants. MTP1 proposes one draft (two verify tokens); MTP3 proposes three (four verify tokens).

The pinned [htsglang fork](https://github.com/efschu/htsglang/tree/62271fd7c8aa8fe9edebf04e00a414b7fbf64388) documents uneven TP and MTP on different hardware/model formats. Its source is staged immutably; the local candidate is a separate copy. A separate Torch2.11/cu130 + sglang-kernel0.4.4 runtime was required because the maintained Torch2.13/native kernel ABI is incompatible. General Python packages are read-only fallback dependencies. The maintained runtime is untouched.

The candidate ports the tested W4A8 kernel to the older JIT API and preserves compressed-tensors group alignment, packed INT8 embeddings, INT4 output heads, GPU-only execution and module-level target/draft vocab sharing. Text-only behavior was backported: the unadapted fork allocates an unused vision tower and otherwise skips this checkpoint's packed embedding tensors. Those invalid startups were rejected before benchmarking. Per-process GPU masking requires TP-rank-based audits; both rank names and physical card identities are checked.

Initial server-argument, ABI, namespace, loader and audit failures remain in the numeric/private records. No failed startup is a throughput result. No CPU weight offload, new model download, driver/P2P/unlock change, clock change or global VM change was used. The uniform-memory ratio check remains enabled for ordinary TP; this fork uses per-rank budget admission in heterogeneous mode, alongside unchanged external resource guards.

Final source hashes, 18 standalone GPU kernel cases and 8 bit-exact packed-weight/scale reconstruction checks are preserved in the numeric record. Each actually launched plan retains its exact context, rank budgets, shard ratios, state/KV precision and draft settings. Long-context retrieval and configured KV capacity are reported separately; a shorter token pool is not qualified as a maintained 32K setting.

Raw plans, logs, requests, native metrics, source snapshots, runtime versions and telemetry remain private under `data/sglang-hetero-mtp-20261027/`. Earlier W4A8 results are preserved unchanged; the user's acceptance of that tradeoff supersedes its earlier no-speed-loss rejection for future selection.

## Local compatibility repairs and metric validation

The draft fusion projection was also incompatible: fork nn.Linear skipped packed INT4 mtp.fc weights, leaving it uninitialized. The first 16K MTP1 timing had zero acceptance and is retained only as invalid diagnostic evidence; the next MTP3 attempt was interrupted. The corrected candidate uses a quant-aware replicated fc, unpacks its forward tuple and refuses to start if any required non-vocab draft parameter is missing. Both ranks must pass this audit before benchmarking. MTP verification masks now reserve space for both the prefix and draft-to-draft block; the original allocation overflowed by four entries for MTP1 and sixteen for MTP3 at startup. Module sharing now collects discarded packed vocabulary modules before cache profiling: bound weight-loader references formed cycles, retaining 974,333,440 bytes per rank. Actual sharing identities and GPU placement were checked. These are isolated source repairs, covered by three focused regression tests.

The benchmark metric reader now selects one canonical TP replica after the final PP stage. Summing duplicated per-rank counters incorrectly counted a single request twice and doubled native prefill time; the strict request-count check caught this before accepting results. Seven CPU metric tests pass, including combined PP/TP labels. Historical numeric results are unchanged.

Initial FP32 MTP configurations backed all 32K tokens after the source repairs but failed the unchanged 1 GiB GPU-free requirement. BF16 recurrent state and one Mamba slot were tested with a matching single-request control; any smaller-workspace variants have their own fresh controls. Failed post-load guards are capacity failures, never accepted throughput. Three-request medians and a small quality suite do not establish sustained-load reliability.

## Interpretation

- `hetero-tp2-mtp1-16k-packedfc-v14`: decode +10.00% against the matching 16,384-token no-MTP control. Last-window draft acceptance 80.0%; accepted length including the bonus token 1.80. These are last reporting-window gauges, not a whole-suite acceptance average.
- `hetero-tp2-mtp3-16k-packedfc-v14`: decode +32.51% against the matching 16,384-token no-MTP control. Last-window draft acceptance 51.7%; accepted length including the bonus token 2.55. These are last reporting-window gauges, not a whole-suite acceptance average.
- The 32K BF16/one-slot heterogeneous control gives 64.18 decode tok/s, +40.46% versus the accepted PP2 W4A8 reference; prefill changes -46.92% and TTFT +88.27%. This comparison changes fork/runtime, TP layout and state precision together. The FP32/two-slot control is reported separately.

The fork uses the full shared vocabulary head for MTP; it does not use HyperQwen’s existing compact 40,960-token draft head. The historical HyperQwen measurement (89.10 decode tok/s at 56,320 context) was not rerun here. Keep HyperQwen as default. The 16K MTP3 candidate is the strongest tested SGLang generation option, with lower prefill performance and reduced context; it remains isolated. None of these tests changes the selected production profile. A context reduction cannot be claimed as a maintained 32K qualification.
