# Authorized four-domain generation — 24 September 2026

The user explicitly authorized the frozen 6,800-attempt release plan and local
export on `dataset-prep`, following finalized licensing in `3d99eeb`. Preflight
verified the grant to Kaushik Roy, frozen source/artifact hashes, installed WSL
runtime and disk headroom (1,728.81 GiB available). Its measured record is retained
at `dataset-runs/release-execution/preflight.json`.

Enable only `final_generation_enabled` in the committed release configuration.
This switch is deliberately outside the frozen scientific contract. Do not change
the freeze, sampling, split plans, seeds, numerical thresholds, question policy,
numeric registries or model-data contract. The licensing decision's historical
disabled-state field records the earlier licensing action, not this new generation
authorization; the executable release configuration is the current control.

Use the existing serial CPU WSL environment, six-hour invocation/two-hour partition
budgets, 100 GiB release disk cap and 200 GiB free-space floor. Preserve attempts,
failed receipts and quarantined records. Resume uses the exact config/source
identity; no rejected draw may be replaced or retried to fill a quota.

The launch record will record the resulting enablement commit before generation.
Logs and outputs remain under `dataset-runs/`, outside Git. Only compact evidence
and the completion report belong in Git. Development and quadruped data remain
excluded. No training, remote push or publication is authorized.
