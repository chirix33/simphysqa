# SPQ05 frozen processing protocol /1.0.0

Authority: [SPQ05 instruction](../prompts/SPQ05_formal_audit.md). This supersedes
the historical calibration/formal plan and foundation-review execution restrictions
only within SPQ05. No calibration set is constructed. Three unidentified slots
R1/R2/R3 each review the identical 140 frozen QA items independently (420 ratings).

This is a focused internal audit of physical/global context, observed-window
trajectory language, question wording and canonical family, generated timestamp
language, and state–event descriptions. Gold answers, private explanations, traces
and simulator outcomes supply optional corroboration outside the primary scope.
This is not a comprehensive answer/explanation/benchmark audit or an OOD study.

## Source frame and random selection

Use the original admitted dataset1.0.0 four-domain release: 11,105 predictive QA,
6,340 groups. Reuse its SPQ01 inventory; verify its manifest, every source shard
hash and release-manifest hash. Preserve source IDs, metadata, split, entities,
measurements, relations, references, scoring tolerances and observation boundaries.
Freeze the authoritative development_exclusions.json bytes/hash and exclude its
20 groups by group or trajectory ID. All56 accepted enriched development QA are
ineligible. They may be used only for explicitly labeled software integration.

All original partitions are in the source frame; splits are not reassigned or
interpreted as new OOD evidence. Sampling unit is one distinct group, checking that
each group has one domain/split/trajectory identity. No repeated group across QA
families, primary candidates, reserves or final items.

Algorithm: Python Random(20261006), existing DOMAINS order robotic_arm, driving,
object_pushing_stacking, tethered_load; family order direct, predictive,
counterfactual, explanation, clarification. Within each domain sort group IDs,
shuffle uniformly, assign groups round-robin to five disjoint family pools. For
each shuffled group select one original predictive source QA uniformly from its
sample-ID-sorted records. In each cell take the first7 groups as primary, next7
as reserves; freeze all280 source candidates and ranks before any new annotation,
private readout qualification or simulation. Do not reassign family pools after
seeing outcomes. Candidate source IDs are not final family QA or packet IDs.

Candidate processing: visit ranks1–7 within each cell, then rank8–14 only when
fewer than7 have qualified. Cell order is domain/family order above. First7
qualified items form that cell's final sample. Stop processing a filled cell.
Never borrow another cell's reserves or select on prose appeal/effect size.
Unused reserves remain unused, not failures. Exhausted cells cause an explicit
shortfall, not reallocation or a relaxed threshold. This targets the resulting
balanced, qualification-conditioned audit design; it is not uniform record
sampling or the natural QA-record-weighted quality of the original release.
All source candidates, exclusions, qualified items, exclusions after qualification,
failures, unused reserves and replacements retain their counts and reasons.

## Eligibility and deterministic family procedures

Every source must pass existing admitted-source validation and lossless migration.
No formulas execute as code. All public surfaces retain the original cutoff and
observed states. Required generated trajectory/timestamp prose must be nonempty
and pass the established binding, numeric, timestamp and privacy validators.

Direct: existing build_direct, last observed state, existing focal entity/quantity,
exact observed value and its deterministic evidence. Predictive: original source
question/answer_spec/reference, unchanged. Language is generated once per selected
physical prefix, then enriched by event language2.0.0 and association1.1.1; do not
cosmetically regenerate cached outputs. Versioned new derived identities preserve
original source IDs. Answer annotations use1.0.3 with actual saved evidence.

Counterfactual/explanation: established omission of the existing scheduled
intervention only. Verify the intervention starts after the unchanged observation
cutoff and omit only its established program. Select the first supported target
in source target-ID order, without consulting outcome size. Same source group,
seed/model/assets/configuration/controller and numerical settings. Require exact
canonical factual replay against all saved source states, private events, public
definitions and structured labels, separately from coarse/fine admission of both
factual and omission outcomes. Four executions/pair if matching verified saved
evidence is unavailable. Pin original WSL/runtime/assets and executed implementation.
Use established pipeline.comparison, domain_physics and source admission thresholds,
not answer tolerances as replay/admission thresholds. No simulation retry or
different tolerance after a failure; record failed/interrupted reservations.
Unchanged Booleans and within-tolerance numerical differences are valid. Explanation
uses the selected comparison in supplied_comparison, explicitly supplied simulation
outcomes outside the observed prefix, with the established bounded interpretation.
Never infer a detailed mechanism from temporal association.

Clarification: existing saved-witness explicit query-gap procedures. Try selected
target first, then source targets sorted by ID for scheduled/omitted query-condition
gaps. Then try the existing two-block position entity gap in objects, then the
existing tether .4-second/factual-target-time position gap, only if both times
are future to the preserved cutoff, distinct, and present in saved evidence.
No invented masses, defaults, alternative readouts or interventions. Attempted
slots, targets, values and rejection certificates are organizer-private ledger
entries. Boolean witness values must differ; scalar/vector/quaternion acceptance
regions must be strictly disjoint under actual scoring (separation > r1+r2), using
unchanged tolerances and sign-invariant rotation. Both completions must erase to
the entire identical initial view, including wording, associations and metadata.
Additional saved endpoints require existing fine/coarse admission evidence at
those times before qualification. Unavailable endpoint evidence is a failure,
not assumed verification. No qualifying gap means eligibility rejection; consume
only a same-cell reserve. Report clarification rejection/qualification attrition
separately from annotation failures and simulation failures. A recorded reply
resolves only missing query information; authored turns are not executed dialogue.

## Budgets, failures and resumes

Historical limits are ceilings, not reusable allowances: SPQ01 initial16, total32,
two attempts/item, USD5, 4,200 seconds, 1,000,000 input/65,536 output tokens;
SPQ02 simulations32, total1,800/per-execution180 seconds. Saved prior usage has
16 initial annotation calls and32 simulations, leaving zero initial calls or
simulations under those allowances. A new directory does not renew a budget.
Budget status is unresolved; no new live execution is enabled by preparation.

Prepare exact observed-only annotation payloads and byte-based token reservations
using historical gpt-5.6-sol/medium/2,048 output tokens/120-second timeout,
omitted temperature/seed, default tier, store=false, tools=[], established
prompt/schema1.0.0. Record returned model identities if later authorized; an alias
is not an immutable snapshot. Historical pricing is labeled, not today's quote;
refresh official rates/context support and credential access before any live run.
Never log credentials. Annotation retries: one controlled repair at most per
candidate, including feedback in its actual recomputed reservation. No hidden
transport retry, redirect or fixture fallback. Access/provider/pricing failures
halt globally, not a reason to replace selected groups. Invalid outputs after
one permitted repair are logged failures and may consume same-cell reserves.
Every annotation attempt/repair, reservation/raw response, solve, interrupted
operation and replacement is preserved. Unknown usage retains full reservation.
All resource axes must admit each operation including prior/new charges. The
frozen280 candidate cap bounds attrition; no promise that it fills all20 cells.

The actual preflight lists first140 and all280 candidate requests/reservations.
First140 require56 CF/explanation matched pairs (224 executions); up to28
clarification pairs add112, totaling336. All280 candidates need at most672.
Verified matching saved evidence may reduce execution; development pairs cannot
be reused as formal items. Prepared requests are not executed annotations.
Live runner adaptation/qualification remains pending explicit new budget; existing
SPQ01/SPQ02 executors retain their hard caps unchanged.

Export outside the worktree to a new versioned root. Every deterministic file
uses exclusive creation or exact-byte resume; mismatches fail. Protocol identity
pins producer commit, source frame, source files, exclusions, candidate ordering,
config, procedures/schemas, rubric and analysis. Source manifest/shards are verified
before prepare; actual saved-output resume must preserve all output hashes.
Never revise frozen packets due to ratings. New versions, corrections, rubric
revisions and adjudications are separate. No answering-model benchmark, full-release
enrichment, collected/invented judgments, merge or push.

## Final freeze and review entry

Only after7 qualified complete QA per cell: validate140 sample IDs,140 distinct
trajectory/split groups, exclusion disjointness,20 cells of7, all source and
evidence hashes, actual public/privacy projections, full required extraction and
420 blank assignments. Freeze final packet/sample identities and public/private
hash manifests; release a readable focused primary index with separate auditor-only
gold links and organizer-only generator/accounting identity key. Extraction uses
actual exported keys, joins timestamps by state_id and preserves every state,
repeated event text, original schedule/controller and typed values. Missing required
fields are explicit findings and block complete-packet qualification.

Three separate blank R1/R2/R3 forms have the identical140 assignments; no identity
mapping is assumed. Preparation header-only templates and development test forms
must not be presented as those formal forms. [Guide](formal_reviewer_guide.md) and
[analysis](formal_analysis.md) are frozen before human review. Report a shortfall
and blocker if final readiness fails. No per-item human generation approval gate.
