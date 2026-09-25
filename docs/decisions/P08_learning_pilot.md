# Approved P08 learning pilot — 25 September 2026

The user approved execution of `Post_P07_next_pilot_revision.md`, with unchanged
aggregate limits: three GPU hours, one CPU hour, 20 GB new artifacts, 120 provider
attempts, two million input tokens, 100,000 output tokens and USD 15. Component
caps also apply; stop the applicable work at its first cap. No automatic increase,
silent objective/parser/target change or convergence guarantee is permitted.

Scenario IDs are frozen before calls/training. Include the original diagnostic
training scenario and choose the other 31 training/eight validation scenarios by
seed-11 content-hash order; choose earliest horizon then sample ID within a
scenario, preserving the original diagnostic question. Entire validation scenarios
are absent from all training metadata. Numerical batches contain a complete
20-transition question trajectory, selected by deterministic shuffled cycles;
every transition has unit weight. RNN hidden state resets between independent
trajectories and remains chronological within each. Truncated final cycles have
recorded sample exposure counts, not changed loss weights.

Each custom method uses its own fresh pinned T5 initialization for its 20-update
training-only diagnostic and a separate fresh initialization for the 180-update
broader run. The latter does not load the diagnostic checkpoint. CODI teacher and
student share T5 within one model, with fixed seeded teacher projection and trained
student projection. All original target-gradient/feedback and numerical contracts
remain unchanged. Predeclared final budget checkpoints are evaluated without
validation-based selection. Every failed/unattempted eligible output remains in
the denominator. No new clarification interaction is executed.

The single-worker ledger reserves provider attempts/input/output/spend before
dispatch; unknown usage retains a conservative reservation. The established
adapter's usage-price basis ($4 input / $0.4 cached input / $20 output per million)
is recorded, not presented as an independently audited billing invoice. An external
supervisor enforces active compute deadlines and the artifact limit. GPU buckets
include model calls/loading/checkpoint operations and teacher work; provider wait
is reported separately from local CPU processing. Stage sources are content hashed,
including the audit fixes at base commit `ba5d31d`; no automatic commit/push.

Prototype clarification status and remaining trigger/reply/refinement/evaluation
decisions are in [the correction](../reviews/P08_clarification_correction_and_proposal.md).
The original notebook and historical audit artifacts remain unchanged.
