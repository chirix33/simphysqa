# User-facing inference runner

Larger-count follow-up: the user's 20-question/domain command exposed the
prepared-inventory ceiling. Main-cohort `auto` selection may now expand within
the original requested release partition, preferring prepared cases for cache
reuse. It never uses outcomes to choose cases or borrows training records for
test requests. Public enrichment and frozen embedding preparation are inference
dependencies, charged to the existing per-run limits. No training or increased
API allowance is implicit. Matched appendix selection remains frozen; explicit
`p11` inventory remains available for reproducing the prepared subset.

Gold export follow-up: user requests gold answers as part of each run's output.
Export only the requested typed evaluator labels after inference; display them
alongside unchanged model predictions. Keep units, frames, query semantics and
tolerances. Store raw gold under `evaluation/private/`, which the deployment
I/O guard rejects. No gold values enter generation, and no reference trajectory
is copied to a public input file. Separate `evaluate` can add these comparisons
to existing manual runs without additional inference or API calls.

Latest user decisions supersede the lower-level replay interface:

- Existing checkpoints by default; explicit train-and-run mode. No automatic
  training for missing domain checkpoints; report unavailable.
- Existing dataset cases, by sample ID or count; default three per domain.
- Main user workflow: Phi-JEPA versus the configured vanilla LLM on exactly the
  same public question, with final answers and all supporting run files saved.
- Vanilla answers use fresh real API calls by default (user follow-up).
- USD 5 per run is the explicitly approved default aggregate provider cap,
  including uncached Phi-JEPA final answers. Each run has its own ledger.
- Phi-JEPA always recomputes numerical inference; an exact request-bound final
  answer cache may be reused. Either answer policy has an explicit CLI override.

Engineering choices: outcome-blind lexicographic IDs, default original test_id
partition, one request attempt, original strict prompts/parsers/limits, separate
evaluation process, source snapshots, exclusive output directory and run lock.
Resume retains failed attempts as well as successes. Fresh custom student typed
outputs are rendered transparently for display, without changing their targets
or inventing an explanatory LLM pass. Human clarification remains separate.

No architecture, training objective, Boolean policy, scientific threshold or
checkpoint is changed. The initial inventory is the existing P11 prepared
cohort, not a claim of cache coverage for the entire dataset release. Explicit
train-and-run uses the existing budgeted numerical training stages and a new
manual training configuration. No new training or paid calls were launched as
part of implementation verification.
