# Official Strata desktop app and existing Q3 model — October 30, 2026

The official **Strata 0.2.8 Linux x86-64 desktop app** is installed, with a
**Strata Official** shortcut on the Desktop and in the applications menu. The
existing managed **Strata** engine-selector shortcut is preserved.

The app is linked to the existing Qwen3.8-Flash-Next **IQ3_XXS** GGUF library and
prepared packs. Its model inventory recognizes `iq3_xxs`, with **32,768 context**
and no missing model or engine files. No model weights were downloaded, moved
or copied. The two existing GGUF shards are reused in place.

## Open it

Double-click **Strata Official** on the Desktop, then choose the installed
**Qwen3.8-Flash-Next IQ3_XXS** entry. The matching desktop engine is already
installed. The model has been registered but is not automatically started by
this setup; the app's persisted `current` and `loaded` fields are unset.

The official app manages its own engine. The existing router and its qualified
worker remain separate; starting this app's local model is a separate inference
run. This installation did not qualify the new desktop engine's speed or change
the production router's selected runtime, guards, model profile or context.

## Installed layout

- AppImage and extracted official payload: `runtimes/strata-official/0.2.8/`.
- Desktop launcher: `runtimes/strata-official/open-strata-official`.
- App state and components: `data/strata-official-app/`.
- Existing library: `models/strata/models/IQ3_XXS/`.
- Existing prepared packs: `models/strata/packs/iq3_xxs/`.
- App-local profile: `data/strata-official-app/install/strata-iq3_xxs.json`.

The app's model-directory setting and its library link point to the same
existing files. App runtime, profiles, state, session file and component paths
are separate from the guarded installation. Its app-local profile is a copy
of the selected Q3 launch settings with the router credential removed, a
loopback-only separate port, its own log path and a concrete app-local engine
path. The canonical launch profile and existing global Strata settings are
preserved. The concrete path avoids a desktop inventory warning produced by
the older `component:strata-engine` placeholder.

The new app has its own official **0.1.54 CUDA 13 engine**, installed through its
bundled Strata Control. This does not update the original router's component
pointer or runtime pin. The existing GGUFs, MTP/vision files and packs remain
shared; copying a small JSON profile does not duplicate the model.

## Download integrity and checks

Both downloads came from the official `Niko1221/Strata` v0.2.8 release and matched
the GitHub release asset size and SHA-256 metadata:

| Asset | Bytes | SHA-256 |
| --- | ---: | --- |
| `Strata-0.2.8-linux-x86_64.AppImage` | 291,514,872 | `a042f05dd7a740e0cd8c43cad6d8958152595b16fc3a566c029280a836ad3b6e` |
| `strata-engine-0.1.54-linux-x86_64-cuda-cuda13.tar.gz` | 645,985,849 | `a183c298e26145a11b87baaeda5fe2ec32b305c600e6886206fd225bf3070726` |

The packaged app starts in help mode, and its real desktop host reports the
linked model ready with no missing files. The host verification uses the
official bundled Node and Control, with real-engine mode enabled; it does not
simulate an installed model. No GPU model load, generation or benchmark was
performed. The owned verification host is stopped afterward.

The first inventory test used the CLI inventory's field names against the
desktop host's different schema; that check was corrected. The app itself
reported the Q3 entry, and the final check uses its native `model`, `ready`,
`missing` and `context` fields. The app-local symbolic-engine warning was fixed
without editing upstream app code or the original profile.

Sources: [official release](https://github.com/Niko1221/Strata/releases/tag/v0.2.8),
[official installation instructions](https://github.com/Niko1221/Strata/blob/v0.2.8/docs/INSTALL.md).
See [installation verification](validation-results/20261030-strata-official-app.json).
