# SimPhysQA coding-agent instructions

Read [the documentation index](docs/README.md), [current progress](docs/PROGRESS.md),
[foundation contract](docs/simphysqa/foundation.md), relevant family contracts and
nested AGENTS.md files. Inspect actual Git status and worktrees before edits.
The newest explicit user instruction governs authorized scope. SPQ06 has not been
sent or started; plans and prepared requests never authorize experiments.

## Scientific boundaries

SimPhysQA contributes simulator-grounded structured/language trajectories, five QA
families, reproducible annotation/auditing and evaluation across models/domains/
question types. Learned Phi-JEPA/SCLD/JEPA/EBM/ODE and CODI/Coconut training are
historical and outside active scope. Root source-generation specifications retain
historical downstream model sections; those sections are not current authority.

Preserve accepted source records, IDs, groups/splits, answers, tolerances, units,
frames, cutoffs, controls, event semantics and provenance. Unknown is not zero.
Never execute extracted formulae. Do not create families by relabeling records.
Counterfactual truth needs matched, verified interventions; timing overlap alone
is not causation. Clarification requires a real query gap and two scorer-disjoint
private completions consistent with every initial visible surface. Replies supply
missing query information, never the answer. Explanation QA discloses only its
explicit selected supplied comparison. Keep gold, traces, witnesses and verification
private and separate from public answering inputs and generated prose.

Retain association 1.1.1, answer annotation 1.0.3 and their exact saved outputs.
New derived exports require version/hash identities and exclusive-write or exact-byte
resume. Preserve exact executed prompts, deterministic procedures and per-file
lineage. Schema development is iterative creation, enrichment and human revision.
Automatic fact/scorer checks do not establish human language quality or agreement.

The 56-item engineering set spans 16 train groups; all 20 inspected/development
groups remain excluded from fresh formal sampling. SPQ05's current protocol is
[formal_protocol.md](docs/simphysqa/formal_protocol.md): same 140 items for three
independent reviewers, no calibration set, 420 initially blank assignments.
Earlier 20/140 calibration planning is historical. Planning power/prevalence/kappa
assumptions are not measurements or acceptance thresholds. Preserve failures,
missingness, rejections and unused reserves. Human review is research, not a
mandatory software-generation approval gate.

## Engineering and workflow

Use ordinary branches from current main, validate, review the complete diff, then
commit and merge through the configured repository workflow. Do not create another
worktree merely for routine changes, switch dirty checkouts, reset/clean unrelated
work, remove existing worktrees or rewrite/force-push history. Publish or message
others only when the user authorizes it. This cleanup session explicitly authorizes
its validated commit/merge/push; it authorizes no experiments.

Supported setup is an editable checkout with separate CPU, simulator, numerical
audit and answering-model environments; optional numpy pins conflict. See the
foundation setup. Keep `phi_jepa` as simulator compatibility namespace. Do not
rename it for appearance. Frozen generation snapshots need a new source freeze
and optional-runtime qualification before another full release.

Use configurable external roots for data, models, environments, caches and outputs.
Do not physically delete ignored/untracked artifacts. Read source releases and
accepted exports without alteration. Provider/network access must stay explicit;
offline tests use no network. Live/long runs require a configured budget and
authorized credentials. No secret logging, synthetic fallback after live failure,
silent repair, changed thresholds or invented empirical results. Record exact
identities/settings and every call, solve, retry, failure and cost. Answering is local
and tool-free; annotation/private verification have separate boundaries.

Run relevant existing behavioral tests, import/CLI and packaging/resource checks.
Report actual commands and untested optional runtimes. Update docs/PROGRESS.md,
docs/reviews/ and docs/decisions/ with base/branch, behavior, evidence, deviations,
pending gates and next step. Use [the blocker template](docs/prompts/BLOCKER_REPORT.md)
for unresolved prerequisites; continue independent authorized work.

Historical recovery and remaining legacy paths: [docs/history.md](docs/history.md).
