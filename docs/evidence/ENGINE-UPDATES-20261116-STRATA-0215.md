# Strata 0.2.15 installed by hand — November 16, 2026

Daily update at the owner's request. The upstream check found one update; everything else was current.

| Engine | From | To | Result |
|---|---|---|---|
| Strata (`flash-next-strata`) | `09b603886925` (0.2.14; control 0.1.60.1, engine 0.1.60) | `c77572806996` (0.2.15; control 0.1.61, engine 0.1.60) | **promoted** |
| Strata (`deepseek-unsloth-strata`) | 0.2.13, DSV4.1 engine 0.1.59 | unchanged | frozen at 0.2.13 (upstream no longer runs DeepSeek) |

HyperQwen, SGLang, Maya (1.1.65) and llama.cpp (1.0.0) had no new commits; ComfyUI, Raylight, the mesh and GGUF nodes are pinned and current. ComfyUI has tags 0.45.1 to 0.45.4 upstream that are not published as releases; the checker follows releases and reports 0.45.0 as current.

## Review before the install

Sources: the release notes, the signed feed (sequence 127) and a file-by-file comparison of the new control package with the installed one (52 upstream commits).

- **Only the control package changes.** The feed still names engine 0.1.60 (the 0.2.14 file, same digest as the installed one) and the frozen DSV4.1 0.1.59. No speed change is claimed upstream and none was expected here.
- The release notes are about the desktop app and the Terminal: no llama-server fallback, drafter choices kept across restarts, first-run install of Qwen3.6, clearer update errors. None of that is used on this server, which starts the engine from its own preset.
- **Two fixes in the server code this machine runs are not in the release notes:**
  - a tool argument declared as boolean that the model writes as `True` or `False` is now returned as a real boolean, not a string (upstream issue 5979, listed as an open risk in yesterday's review);
  - a request that arrives while the engine is closing is now refused with 503 `server_draining` instead of being accepted and cut off with no output (issue 6055).
- No setting, launch flag or file name this server uses changed. The known problems listed are for AMD, Mac and peer mode.

## Install

Control 0.1.61 was taken from the signed feed; feed signature and package digest were verified with upstream's `strata_control` code. It went to `runtimes/strata-terminal/terminal/0.1.61` with the idle adapter applied to `serve/server.py`, `current` was repointed and the Flash-Next preset's working folder moved to it. The engine path in the preset is unchanged. The preset was saved to `data/strata-update-20261116/preimages/` and `rollback.sh` written first. Nothing under `runtimes/strata-unsloth-029` was touched.

## Short DSH check

Load, one short answer through the app path, tool call, unload; GPUs unlocked and idle (1 MiB each) before and after; server otherwise idle (load 0.6).

| Profile | Version | Result | Prompt reading (tok/s) | Time to first token (s) | Generation (tok/s) |
|---|---|---|---:|---:|---:|
| `flash-next-strata` | 0.2.14 (run 1) | pass | 1046.1 | 5.47 | 82.2 |
| `flash-next-strata` | 0.2.14 (run 2) | pass | 1061.5 | 5.39 | 85.3 |
| `flash-next-strata` | 0.2.15 (run 1) | pass | 1058.0 | 5.40 | 83.7 |
| `flash-next-strata` | 0.2.15 (run 2) | pass | 1063.4 | 5.38 | 80.2 |
| `flash-next-strata` | 0.2.15 (run 3) | pass | 1056.3 | 5.41 | 80.8 |
| `deepseek-unsloth-strata` | 0.2.13 (untouched) | pass | 28.3 | 6.07 | 12.4 |

Same speed before and after, as expected with an unchanged engine. These idle-server runs also answer yesterday's open question about Flash-Next generation on the 0.1.60 engine: five runs give 80.2 to 85.3 tok/s, against a single 87.1 on 0.2.13 yesterday and 77.1 and 77.5 on November 9. That is inside the day-to-day spread of this check; no slowdown is shown.

The boolean-argument and shutdown fixes were read in the source, not exercised here. No long-context or sustained run was made.

Rollback: `data/strata-update-20261116/rollback.sh` restores control 0.1.60.1.
