# Inkling 2 Mini on Strata's own engine (`strata-inkling` 0.1.65): trial — November 22, 2026

**Status: added as `inkling-strata` on November 22 at the owner's request, dropped on November 23 at the owner's choice.** The owner pointed out that Strata 0.2.19 made Inkling 2 Mini much faster and asked for research and optimisation.

## Result

| | Strata engine, SQ-10, 3080 Ti alone | `inkling-llamacpp` (UD-Q4_K_M, both cards) |
|---|---:|---:|
| Generation, prose | 64-65 tok/s | 41-44 tok/s |
| Generation, code | 72 tok/s | 41-44 tok/s |
| Prompt reading, 6.2K tokens | 2,100-2,140 tok/s | about 810 tok/s |
| Largest context that stayed up | **8,192** | 32,768 |
| Thinking | hidden: the model thinks, the text is dropped | shown, always on |
| Weights | Strata's 10.5 GB pack, about 3 bits a weight | 16 GB, 4-bit |

The engine is about 1.5 times faster at writing and 2.6 times faster at reading, but on this server it only holds an 8K context, which is too small for the work the entry is used for. That is why it is not adopted.

## Why only 8K

Strata's fast path for this model uses one card and needs the whole pack in VRAM. SQ-10 takes about 10.6 GB of the 3080 Ti's 11.96 GB before any context.

| Setting | Outcome |
|---|---|
| 32K, drafter on | out of memory at start |
| 16K, drafter on | starts with 207 MiB free; out of memory while reading a 6.2K-token prompt, and the server then hung |
| 16K, drafter off | starts with 567 MiB free; runs the 6K-token tests at 65-75 tok/s; out of memory on a 14K-token prompt |
| 8K, drafter off | stable through the whole test; 347-695 MiB free |
| 32K with part of the experts in RAM (`--vram-experts-gb`) | the flags are ignored by this engine; out of memory at start |
| 32K on both cards (`--gpus 2`) | starts (5.7 GB + 4.4 GB), writes 3 tok/s, then the engine crashed (exit -11) on the third request |

The larger packs (SQ-15 13.4 GiB, SQ-20 18.0 GiB) do not fit one 12 GB card, and the two-card mode is the slow path above. The 16 GB GGUF already on the server cannot be loaded by the fast path.

## Behaviour notes

- **Hidden thinking.** Answers arrive without thinking text, but the tokens are spent: "437" cost 47 tokens, a one-line JSON 91. With a small token limit the answer comes back empty.
- **Tool calls** work, with the follow-up after the tool result.
- **Drafter:** needs greedy single requests and about 0.7 GB more VRAM; it could not be kept on at any useful context here, so no drafter speed was measured.
- Upstream publishes no figure for this card generation; its headline numbers are for cards of 24 GB and more.

## What was installed for the trial

- Engine package `strata-inkling-0.1.65-linux-x86_64-cuda-cuda13.tar.gz` (432,654,826 bytes), named in the signed 0.2.19 feed (sequence 131). Checked with upstream's own code (feed signature, size and hash, manifest hash and signature, every file's hash, test start) and unpacked to `runtimes/strata-manual/inkling-0.1.65-20261122/`. The installed Strata was not changed.
- Files from `strata-engine/Inkling-2-Mini-Strata` in `models/strata/models/inkling-2-mini/` on the NVMe, 11.1 GB: SQ-10 (10,471,526,400 bytes) and the picture file (636,526,592 bytes), both matching the hashes pinned in Strata 0.2.19, plus the tokenizer and chat template.
- Trial server: `strata serve` on port 10054 as a transient unit, router idle. Scripts and logs in `data/inkling-strata-20261122/`.
- A source review by four agents, each checked by a second one, prepared the trial. It predicted the single-card limit, the slow two-card path and the hidden thinking; its guess that 16K-32K would fit was wrong.

## Not done

- Pictures, parallel requests, the short tool-use test (the 8K limit rules the entry out first).
- The 11.1 GB of trial files and the unpacked engine are still on the NVMe. Removing them is the owner's decision.

## Router entry dropped — November 23, 2026

- Served at 6,144 tokens, the web client's own prompt (6,963 tokens with 25 tools) did not fit. At the owner's request it was set to 8,192.
- At 8,192 the router check still failed: the web client sent `max_tokens: 1`. Its library keeps a fixed 4,096-token safety margin, so output room = context − prompt estimate − 4,096. A web-client session needs about 11.5K of context; the 12 GB card holds 8K at most.
- Through the router at 6,144 it loaded in 3.2 s, passed arithmetic, a tool call with follow-up and a 5K-token recall, wrote 65-76 tok/s and read 2,219 tok/s (lowest free VRAM 465 MiB).
- Strata itself worked at 8,192 through the router: a 6,935-token prompt with a tool, streamed or not, returned a correct tool call at 65 tok/s; prompts leaving under 1,024 tokens are refused, never truncated.
- The owner chose to drop the entry rather than keep it API-only. The entry code is kept in `data/inkling-strata-20261122/dropped-entry/`; the SQ-10 and Vision weights and tokenizer (11.1 GB, NVMe) were deleted at the owner's request on November 23; the `strata-inkling` engine program stays installed.
