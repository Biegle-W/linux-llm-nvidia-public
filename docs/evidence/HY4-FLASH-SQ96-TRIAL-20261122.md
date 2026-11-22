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

## Not done

- 64K and 128K context (Strata's default is 128K; its plan says both fit in the card).
- The second GPU, the drafter's effect on long outputs, a sustained run.
- The short test with prompt reuse on (not rerun, under the rule that nothing is rerun), and any knowledge, maths or coding score.
- The idle-timeout unload and a picture request through the router.
- Memory headroom is thin: about 8 GiB of RAM is left with the model loaded, so nothing else large can run beside it.
