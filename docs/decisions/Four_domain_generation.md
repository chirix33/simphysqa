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

## Completion and storage-only relocation

Generation revision `a8920b23dfbdb089b95cee5c00a47758b942d4ce` completed the exact
6,800-attempt plan: 6,340 admitted, 460 quarantined, 11,105 admitted questions.
No quota filling, threshold changes, source changes, or scientific configuration
changes were made. All final release and independent data audits passed.

Growing Windows/WSL filesystem scanning overhead justified a byte-verified native
WSL working copy at `/var/tmp/phi-jepa-release-a8920b2`. After a completed receipt,
the original process was interrupted during its next disk-budget scan. All 711
completed attempts and 3,085 files were verified before exact resume. The original
outputs are preserved as `dataset-runs/release-four-domain-v1-pre-native/`; the
validated complete export was checksum-copied to the configured project path.
This was an execution-storage choice within authorized local generation; no new
license grant, public publication approval, or scientific setting was inferred.

The enabled configuration remains committed for reproducibility and exact resume.
This task performed no model training, remote push, or public publication. See the
[completion report](../reviews/PDS_generation_completion.md) and compact evidence.
