# Post-P07 audit decisions — 25 September 2026

Authority: the user's focused source-audit request and RQ clarification in this
task. No settled model or evaluation contract is reopened.

- Audit source baseline: `5810d1899007ae602c3db1ca486d43a1b7865ba4`, branch
  `full-phi-jepa-from-dataset`. Checkout was clean; local origin tracking matched.
  No remote refresh, commit or push is performed by this audit. Older reports'
  uncommitted statements retain their historical run-time meaning.
- Apply routine fixes: active equal-pair default, standalone custom training
  checkpoint restoration of configured gradient checkpointing, and rejection of
  mislabeled custom generation branches. Earlier recorded runs already used
  explicit correct weighting/resume settings/branch names; no checkpoint rerun.
- Keep raw mixed-unit training loss, step-index/timestamp coordinates, full-2d
  feedback, frozen E and undetached trainable P unchanged. Expose coordinate
  decomposition and hold-last physical diagnostics separately.
- Keep stable_stack/support_lost and unqualified initial boundary crossings
  explicitly unsupported. No hidden contact state, new head or guessed Boolean.
- RQ1 is forecasting/QA with reduced extensive domain engineering and richer
  outputs. RQ2 separates OOD recognition and clarification. Both remain research
  questions. “Clarification” has no approved operational meaning; existing
  diagnostics must not be relabeled as cause identification or recovery.
- The next-pilot fitting diagnostic is prepared only and carved out of the
  previous proposed budget. It was not executed during this audit.

Evidence, remaining issues and decisions requiring user input are in
[the focused review](../reviews/Post_P07_focused_audit.md),
[coverage matrix](../reviews/Post_P07_coverage_matrix.md), and
[budget addendum](../reviews/Post_P07_next_pilot_revision.md).
