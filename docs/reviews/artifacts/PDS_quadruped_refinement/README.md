# Measured quadruped follow-up evidence

These are measured development artifacts, not model performance or a qualified
release. Read `qualification-status.json` before the original study summary:
the initial nominal pair passed, then repeated and finer checks failed the same
endpoint tolerances. The smoke set admitted five scenarios at that time; its
nine exported records are historical per-case results. Calibration simulated
zero scenarios. No failed configuration or realization was discarded.

`study-summary.json`, `study-plan.json` and `study-source/` preserve the original
24-run one-factor study and its actual source fingerprints. `worker-replay-*`
and `worker-label-audit.json` preserve the subsequent four real repetitions;
strict state equality was an additional diagnostic, while the independent label
audit uses the original tolerances and also fails. The current worker verifier
separates those two concepts. Its original executed version is archived.

`finer-*` preserve the two serial 0.125 ms runs and comparisons to every retained
0.25 ms run. `initial-state-audit.json` records the actual WSL initializer,
including identical zero solver warmstarts. `clock-audit.json` records applied
forces from the real MJX step inputs; `independent-trace-audit.json` and
`finer-trace-audit.json` check controller algebra and geometric contact timing.

`smoke-manifest.json` contains checksums for all local smoke artifacts, including
quarantined cases. `smoke-rejections.jsonl` preserves every rejected scenario.
The manifest and nominal gate describe the run before the later qualification
revocation; they are not rewritten to hide that history. `handoff-*` distinguish
the original concurrency plan from the actual stop before calibration.

Large full trajectories remain in the gitignored local `dataset-runs/` folders
named by the report. Source snapshots and summary paths refer to this workstation;
checksums identify their content. `CHECKSUMS.json` covers this compact evidence
bundle. Unit-test fixtures are never represented as empirical simulator results.
