# Strata 0.2.11 qualification — November 5, 2026

**Strata0.2.11 / engines0.1.57 is selected for both existing Strata entries.** Flash-Next passed the strict paired gate. DeepSeek passed its actual DSH tool/result/exact follow-up, owned unload and resource checks, but generated59 tokens versus60 on production. The automatic gate rejected that mismatch and restored0.2.10; both restored-production checks passed. The human then explicitly accepted that one-token difference. A separate durable activation reverified the tested packages and observations and selected0.2.11 without repeating inference. The original rejection is preserved, not rewritten as an automatic pass.

## Observed performance

Same downloaded checkpoints, contexts, operational settings, hardware and per-profile tool fixture across each pair. Zero reported prompt-cache reuse; OS file caches were not dropped. These first-tool-generation measurements exclude loading and follow-up. Different DeepSeek output lengths limit exact latency comparison. A single short pair cannot establish a sustained speed improvement or regression.

| Profile / engine | Context | Prefill tok/s | TTFT s | Decode tok/s | Prompt/output tokens |
| --- | ---: | ---: | ---: | ---: | ---: |
| Flash-Next IQ3_XXS /0.2.10 |131,072|941.5|6.413|68.7|5594/40|
| Flash-Next IQ3_XXS /0.2.11 |131,072|934.2|6.460|68.4|5594/40|
| DeepSeek Unsloth IQ1_S /0.2.10 |32,768|85.1|67.084|11.6|5704/60|
| DeepSeek Unsloth IQ1_S /0.2.11 |32,768|83.4|68.423|11.8|5704/59|

Flash-Next prefill/decode changed−0.78%/−0.44%, TTFT+0.73%. DeepSeek prefill/decode changed−2.00%/+1.72%, TTFT+1.99%, with the output-length caveat. These short observations show no material speed gain on this server and remain inside the retained5% throughput and TTFT performance bounds after the accepted token-count exception. They do not reproduce the release screenshot's large gains on other configurations. Existing Flash-Next IQ3_XXS weights were used; this does not test the newly released, different Unsloth quantizations. No model download or weight conversion occurred.

## Effective resource guards

Configured limits, not measured peak usage. Both cards remain selected; no P2P or topology change. Existing MoE host expert caching remains selected.

| Profile | Worker RAM high/max GiB | Host available floor | GPU policy | Swap write/combined MiB/s over30s | Active/loading full PSI |
| --- | ---: | ---: | --- | ---: | --- |
| Flash-Next /Strata |87.76985/89.76985|2GiB|1024MiB native reserve/card|128/160|15% / no separate loading limit|
| DeepSeek Unsloth /Strata |87.76985/89.76985|2GiB|256MiB free/card after ready;1024MiB native reserve/card|128/160|15%/15%|

Unlimited swap occupancy;100C stops; existing three-bad2-second-sample hysteresis, fail-closed telemetry, swappiness60, concurrency1 and idle600s are unchanged. Short calls may not fill the30-second averaging window. All four original arms passed resource checks and unload; no guard was waived.

## Verification and selected state

Official signed feed, signed engine packages, archive digests, source/control payloads and recorded runtime hashes were verified again before reviewed activation. Derived Python bytecode was removed so verified sources recompile. Hardware/settings fingerprints and passing restored-production receipts were required. The transaction retained preimages and exact-owner reservation handling.500 CPU regressions passed, including tests that the manual one-token acceptance cannot bypass profile, prompt, cache, fixture, resource or speed gates. The default scheduled comparison still requires identical output tokens; this explicit command is bound to one completed run, not a future waiver.

Selected source: `c3b3f5035506f3e966f1b4b7b188aeaabae92f1d`. Current API/DSH entries and desktop routing retain their existing IDs. Workers are unloaded, no updater transaction/publication or GPU reservation remains, and the03:00America/Toronto daily timer remains enabled. Maya1.1.54 remains rejected independently; no other engine was replaced. No full-context, sustained or new-quant quality claim is made.

[Sanitized observations and original strict gate results](validation-results/20261105-strata0211-qualification.json). [Manual acceptance policy](DAILY-ENGINE-UPDATE-POLICY.md#explicit-reviewed-acceptance).
