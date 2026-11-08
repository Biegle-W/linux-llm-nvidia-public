# SGLang tool default and bounded Super swap policy — November 1, 2026

SGLang's earlier API switch test loaded and unloaded normally but claimed an existing file was missing without calling a tool. The router now defaults this profile to temperature0 and top_p1 while retaining enable_thinking:false; explicit client settings remain respected. One actual DSH read call plus matching file result passed in5.04seconds, followed by unload. This is a successful short regression, not proof of general hallucination elimination.

Super remains at64K with384MiB KV per GPU. Its model-specific30-second swap limits changed from64MiB/s writes and96MiB/s combined to80MiB/s writes and128MiB/s combined. The earlier failure at56.12MiB/s writes and107.58MiB/s combined remains recorded as failed under its old policy. The independent2GiB host,512MiB GPU,82C temperature,10% active-pressure, telemetry and worker-budget guards remain enabled. The old settings were saved for restoration.

One actual DSH read call and matching result passed under the new policy in334.43seconds. This is slow functional qualification, not a performance improvement claim. Across125 recorded inference rate windows the new check's peak combined swap was4.54MiB/s and peak writes0; it did not reproduce the earlier high-churn window. Four policy regressions separately verify the recorded107.58MiB/s case is allowed, excess write/combined rates still fail, pressure remains independently guarded, and dense limits are unchanged. Thirteen existing swap checks and52router regressions passed; explicit client sampling overrides are covered.

No full-context, sustained-generation, repeated-reload or timed-idle tests were run. Each successful tool check requests owned unload.
