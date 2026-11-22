# Hy4-Flash 220B (SQ-96) on Strata: trial — November 22, 2026

**Status: router entry `hy4-flash-strata` since November 22 (section "Router entry" below).** The owner pointed out that Strata 0.2.18 runs Tencent Hy4-Flash and asked for the SQ-96 build to be set up.

## The model and the files

Tencent Hy4-Flash, 220B parameters with 12B active per token, in Strata's own quantization (`.strata` v1.0). Strata ships three builds named for the memory they target; SQ-96 is the middle one and the one Strata's fit rule recommends for a 12 GB card with 91.8 GiB of RAM.

| File | Size | Role |
|---|---:|---|
| `Hy4-Flash-SQ-96.strata` | 89.58 GB | the model; loaded into RAM |
| `Hy4-Flash-Engram-Q8.strata` | 67.58 GB | shared shard, read from the SSD while answering |
| `Hy4-Flash-Vision.strata` | 0.93 GB | picture input, loaded on the first picture |

Downloaded from the source Strata 0.2.18 names (`strata-engine/Hy4-Flash-Strata` on Hugging Face) to `models/strata/models/hy4-flash/` on the NVMe. All three match the sizes and SHA-256 values pinned in Strata's source. The system disk went from 68% to 85% used (144 GB free).

## The engine

Hy4-Flash runs on a separate program, `strata-hy4` 0.1.64 (cuda13 package, 447 MB), named in the same signed release feed as the rest of Strata 0.2.18. It was fetched by hand into `runtimes/strata-manual/hy4-0.1.64-20261122/` and checked with Strata's own code: feed signature, package size and hash, manifest hash and signature, every file's hash, and a test start. Nothing in the installed Strata was changed. A first fetch script of mine unpacked the package but failed its manifest check (wrong lookup); it was discarded and redone with the correct procedure.

A source review by two agents, each checked by a second one, prepared the setup. Its main findings, all confirmed on the server unless marked:

- The engine uses **one card** (the 12 GB one). A two-card mode exists (`--gpus 0,1`) but Strata never uses it and it was not tried; the 10 GB card stays empty.
- Almost the whole model sits in RAM as ordinary (anonymous) memory and is computed by 16 CPU threads; the card holds the dense trunk, the context state and a cache of the most-used experts.
- The engine does not see the router's memory limit (it reads the limit at the top of the cgroup tree) and plans against the whole machine.
- No one-time calibration; the CPU kernel is chosen at each start (here: AVX2 with VNNI).
- Review error caught by the checker: setting `"drafting": "off"` in the launch file does not turn the drafter off; only the engine argument `--draft off` does.

## Measurements (trial server on port 10052, router idle)

Started through the installed `strata serve` with the router's worker memory limits (87.77 GiB soft, 89.77 GiB hard), card 0 only, Engram reads set to bypass the page cache (`HY4_ENGRAM_ODIRECT=1`).

| | 8K context, text only, drafter off | 32K context, pictures and drafter on |
|---|---:|---:|
| Load to ready | 58 s (first, cold files) | 28-38 s |
| Experts in RAM | 82.93 GB, none left on the SSD | same |
| Worker memory | 79.4 GiB | 79.8-80.0 GiB |
| Host RAM still available | 9 GiB | 8 GiB |
| VRAM, 12 GB card | 11.35 GB | 11.36 GB, 11.71 GB after the context grew past 16K |
| Generation | 18-20 tok/s | 18-22 tok/s (30 on a ten-token answer) |
| Prompt reading, short prompts | 52-59 tok/s | 55-61 tok/s |
| Prompt reading, 16.8K tokens | — | 270 tok/s (62 s) |

- **Answers:** arithmetic and JSON correct with thinking off and on; the code hidden at the end of a 16.8K-token prompt was returned; a picture's colour was named.
- **Thinking** is on by default and can be turned off per request (`reasoning_effort: "none"`).
- **Tool calls** work, with the follow-up after the tool result. One test prompt worded "use the tool to read /tmp/marker.txt" was declined twice; the same request worded as a task, a weather tool, and `tool_choice: required` all produced correct calls.
- **Context growth** from 16K to 32K inside the card took 26 ms and left about 580 MiB free, above the router's 256 MiB guard.
- **Drafter:** it runs (the engine logs accepted drafts), but generation speed with it on is the same within run-to-run spread. Not measured separately on long code.
- **Prompt reuse between turns** is off by default: every request reads its whole prompt again. With `--session-reuse 1` a second turn in an 8.2K-token conversation read 16 new tokens in 0.4 s; without it the first turn's 8.2K tokens took 29 s. Third turn the same.

For scale on this server: DeepSeek generates 8-12 tok/s, GLM 14, Bolt (74B) 67, Qwen 27B 60-110.

## Short tool-use test

New weights, so the short test ran once, as a larger model (one hour). Thinking was on (the test sends no thinking switch) and prompt reuse was off. It was cut by the limit.

| Part | Result |
|---|---|
| Single turn | 33 of 40 correct (parallel 14/15, no-tool 13/15, plain call 6/10) |
| Multi-turn episodes | 5 of 15 reached: 1 passed, 2 failed, 2 hit the 8-minute episode limit (counted wrong); 1 cut by the deadline, 9 not run |
| Coverage | 45 of 55 items scored |
| Time | 0.5 s to first answer (already loaded), 3,361 s of items |

The printed score of 51.2 rests on five episodes and is not comparable with entries that completed all of them. Single turn (33 of 40) is level with the other entries (28 to 36 of 40). Episodes were slow because each step re-read the whole growing conversation; with prompt reuse on they should be much faster, which was not re-measured. Run id `fast-hy4-20261122`.

## Router entry (November 22)

- **Entry:** `hy4-flash-strata`, 32,768 context, text and pictures, card 0 only, drafter on, prompt reuse between turns on (`--session-reuse 1`), Engram reads bypassing the page cache. Thinking is off as served, like the other entries; a request can turn it on. Launch name `hy4`.
- **Engine:** `runtimes/strata-hy4/0.1.64-linux-x86_64-cuda-cuda13/`, pinned by hash together with the three weight files and the tokenizer in `config/hy4-flash-strata-runtime.json`. The private launch preset is `~/.local/state/strata/launch/hy4-flash-sq-96.json`; the launcher refuses to start if it differs from the selected settings in any key or argument.
- **Updates:** on a Strata update the `strata-hy4` package of the same release has to be fetched, verified and installed with it. The old automatic builder now refuses Strata for that reason; Strata updates are done by hand in any case.
- **Code:** written by Codex (GPT-6.2 Astra) from a specification and reviewed by three reviewers, each finding checked by a second agent. No defect was confirmed. One gap is left open: the free-VRAM stop rule for this entry has no unit test (it is the same rule the other entries use). 571 tests pass.

| Check through the router | Result |
|---|---|
| Load | ready in 26 s |
| Chat request | correct, no thinking |
| Tool call and follow-up | correct call; the follow-up reused 210 of 227 prompt tokens |
| Short DSH check (tool call, result, follow-up) | pass; 211 tok/s prompt reading, 26.6 s to first token, 27.4 tok/s generation |
| VRAM loaded | 11.4 GB of 12 GB; second card 1 MiB |
| Owned unload | pass; both cards back to 1 MiB, RAM released |

The guards were checked against the measured figures: worker memory 79.4-80.0 GiB under the 87.77 GiB soft limit, about 8 GiB of host RAM available against the 2 GiB floor, about 580 MiB free on card 0 at the lowest against the 256 MiB floor. No shared threshold was changed.

## Further tests (November 22, afternoon)

Run at the owner's request after the entry was added. Strata had meanwhile been updated to 0.2.19; the Hy4 engine is still 0.1.64.

**Through the router (`hy4-flash-strata`, 32K, thinking off):**

| Test | Result |
|---|---|
| Load | 39-40 s (three loads) |
| Picture (red and blue halves, yellow circle) | described correctly; a follow-up placed the circle on the right side. 6-7 s each |
| Long outputs, three of 1,800-2,000 tokens | 18.6, 19.0 and 22.0 tok/s (the last is code); no slowdown |
| 12-turn conversation on an 8.1K-token prompt | first turn 29 s (279 tok/s); each later turn 1.2-3.0 s with the earlier tokens reused; every answer correct |
| Memory during all of this | card 0 at 10.4-11.4 GB, card 1 unused, 8.5-9.1 GiB of RAM available |
| Idle unload | unloaded by the router after the 600 s idle time; both cards back to 1 MiB |

**Short tool-use test through the router** (larger-model limits, run id `fast-hy4-router-20261122`). This is the entry as served, so it is the comparable result; the earlier run on the trial server had thinking on and prompt reuse off and was cut by the limit.

| Part | Result |
|---|---|
| Single turn | 33 of 40 (parallel 11/15, no-tool 14/15, plain call 8/10) |
| Multi-turn episodes | 4 of 15 (3 of the 9 core episodes) |
| Coverage and time | all 55 items, no timeouts, 2,493 s (42 minutes) |
| Score | 57.9 on the scale shared with the other entries (54.6 with all 15 episodes) |

On the shared scale the stored results of the other entries are 66.0 (Qwen on HyperQwen), 64.7, 63.5, 61.7, 60.4, 53.6 (Bolt), 52.4 (Inkling), 47.4 and 40.6. Hy4-Flash is in the lower middle: single-turn calls are good, multi-turn episodes are weak (4 of 15).

**Larger context (trial server outside the router, same memory limits, same files):**

| Context setting | Prompt | Read speed | Time | Both hidden codes | Follow-up |
|---|---:|---:|---:|---|---|
| 64K | 29,867 tokens | 282 tok/s | 106 s | returned | 0.7 s |
| 64K | 62,067 tokens | 279 tok/s | 223 s | returned | 0.8 s |
| 128K | 94,267 tokens | 280 tok/s | 337 s | returned | 0.7 s |
| 128K | 127,867 tokens | 274 tok/s | 467 s | returned | 0.8 s |

Loads took 38-40 s at either setting. Worker memory stayed at 79.5-79.8 GiB and available RAM at 8.7-9.1 GiB. The card showed 11.3-11.8 GB used between requests. **Correction:** an earlier version of this line gave the lowest free memory as about 480 MiB; that figure did not subtract the roughly 324 MiB the driver reserves. True free memory at these lengths falls to about 230 MiB, below the 256 MiB guard (see the next section). Reading speed does not fall with length, and one code sat at the very start and one at the very end of each prompt. The router entry still serves 32K; raising it is a serving change for the owner to decide.

## 128K through the router: not adopted (November 22, evening)

The owner asked for 128K to be tested through the router and adopted if it passed. It did not pass cleanly, and the entry was put back to 32K. Nothing was committed to the entry.

| Setting tried | Long prompt (127,867 tokens) | Pictures | Lowest free VRAM, card 0 |
|---|---|---|---:|
| 128K, engine default (context memory grows while reading) | **stopped by the router's free-VRAM guard** after about 56 s, at the first growth step | not reached | under 256 MiB for three samples |
| 128K, context memory reserved at start (`HY4_KV_INIT_SLOTS=131072`) | pass: read at 272 tok/s (471 s), both codes returned, follow-up 0.9 s, tool call and follow-up, 2,000-token outputs at the usual speed, owned unload | 256-pixel picture pass; **1024 and 2048-pixel pictures refused** ("out of device memory for the vision workspace"), model stays up | 523 MiB (text), 49 MiB for a moment on the refused pictures |
| 128K, half reserved (65,536), trial server | not run | 1024 pass, 2048 refused once in two tries | 267 MiB |
| 32K as served (re-checked through the router) | not applicable | 256, 1024 and 2048-pixel pictures all pass (9 s and 23 s) | 7 MiB for a moment, guard not triggered |

- **Cause:** the 12 GB card cannot hold the full 128K context memory (2.72 GB), the picture workspace and the 256 MiB guard margin at once. The engine's own rule keeps only 128 MiB free while it grows the context, which is under the router's floor.
- **Speed with the reservation:** unchanged within spread (prompt reading 271-275 tok/s, generation 16-21 tok/s), although fewer experts stay cached on the card.
- **Choices left to the owner:** 128K with only small pictures; 32K with all pictures (current); or a trial of Project Maya's Hy4-Flash engine, which can use both cards.
- The router's picture dip to 7 MiB at 32K lasts under the guard's three-sample window; a slower picture could trigger it. Not observed.

## Not done

- The second GPU, the drafter's effect on long outputs, a sustained run.
- Any knowledge, maths or coding score.
- 64K or 128K through the router, and long episodes of tool use at those lengths.
- Memory headroom is thin: about 8 GiB of RAM is left with the model loaded, so nothing else large can run beside it.
