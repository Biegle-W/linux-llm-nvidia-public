# Bolt automatic tool calling — October 31

Bolt now launches with `--enable-auto-tool-choice --tool-call-parser qwen3_coder`, matching the existing checkpoint model card's tool-format recipe. These flags resolve the backend rejection of `tool_choice: "auto"`. The existing parser entrypoints, Qwen parser/adapter source and unchanged chat template are included in the runtime integrity manifest. No runtime package or model weight was changed.

## Live verification

One fresh normal-router load took 222.48s on the RTX 3080 Ti/3080 pair. An authenticated Chat Completions request with a function schema and `tool_choice: "auto"` returned a parsed `get_inventory` call with valid JSON arguments for `keyboard` and finish reason `tool_calls`. A local fixture returned a count of 12 under the matching call ID; the next response consumed that result and returned the count without another call. A separate streamed auto request returned a parsed call for `monitor`, with valid assembled JSON arguments, finish reason `tool_calls` and a complete SSE end marker. No external function, network lookup or side effect was executed by the verification.

The requests explicitly used `chat_template_kwargs: {"enable_thinking": false}`. This screen qualifies that Chat tool-calling path; it does not establish every schema, client, reasoning mode or multi-step agent workflow. The model requests calls; the client remains responsible for validating and executing approved tools.

## Preserved loading policy and resources

The 8,192-token context, `experts`/`out_proj`/`in_proj` prefetch offload, 1GiB KV cache per GPU, 56/58GiB worker budget and all independent resource guards remain active. 185 swap/pressure guard samples recorded zero violations; worker swap peaked at 0 bytes. Peak worker memory was 49.72GiB. All 325 CPU regression tests passed. The owned test worker unloaded cleanly; router and DSH services were preserved. Earlier loading and benchmark evidence remains historical.

[Numeric evidence](validation-results/20261031-bolt-tool-calling.json). [Two-GPU loading fix](BOLT-TWO-GPU-LOADING-20261031.md).
