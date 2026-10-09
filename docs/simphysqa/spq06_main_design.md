# SPQ06 main experiment and analysis, prespecified before main outputs

The population is the original admitted `test_id` release after the authoritative
development manifest, actual SPQ05 formal audit groups and recorded historical
inspection/prompt-use groups are excluded. Original split assignments, cutoffs,
targets, units, frames, tolerances and private evidence remain unchanged. Disjoint
randomized family pools ensure one selected QA per trajectory group. The first ten
qualified candidates per cell form the nested core; the next ten form the extension.
Failures and clarification eligibility attrition remain in the candidate ledger.
Neither intervention size nor description quality is a sampling/admission filter.

## Inputs and matched ablation

All nine conditions receive the same chosen enriched items. Qwen3-8B direct and
Qwen3-32B-AWQ thinking-on receive an additional matched structured-only condition.
This choice contrasts size/quantization/reasoning within one architecture family
and was made before any main scores. It is a combined input ablation, not a causal
isolation of those model attributes.

`main_public.project` retains the complete original structured physical input:
all public states, source state context, measurements, relations, coordinate
conventions, entities, controllers, event schedules, question/answer specification,
supplied comparison and initial/resolved query information. Annotation binding
lists, hashes and cache identities are evidence metadata, omitted from model tasks.
Derived event text is represented once per declared event. Every state keeps its
actual event ID/temporal relationship. Declared status and typed event/controller
semantics remain in both conditions. Enriched inputs retain exact generated
trajectory and timestamp texts and declared-event descriptions. Structured-only
removes those derived texts. Original global/physical context and original control
equations/descriptions remain because they contain unique task facts.

Initial clarification views are projected only after the accepted full-view scrub.
The projection adds no hidden selector. Replies supply recorded missing query
information, never private outcomes. Actual assistant turns are retained verbatim.
Initial-to-resolved public updates must reconstruct the projected resolved view
exactly. Explanation comparison readouts remain explicitly supplied evidence,
separate from observed prefix states. No new OOD claim is made.

The pilot used the full accepted public export; the main uses this separately
versioned projection. The pilot is not rerun or silently repaired. Context failures
are retained; main tokenization/capacity checks and projection fidelity are separate
preparation checks. Forecasts conservatively use frozen timeout bounds where the
pilot supplied no actual inference timing for an entire condition/family.

## Runtime decision and execution

The timing-only forecast reads raw latency, completion status and loading receipts;
it never reads parsed answers or correctness. For each condition/family, use the
largest measured inference time across pilot domains for every domain in the main
forecast, separately for initials and continuations. Context rejection latency is
never counted as fast inference; it remains a qualification failure. Where an
entire condition/family has no measured inference, use its frozen timeout bound.
Extrapolation to unmeasured domains is explicitly an inference, not a guaranteed
worst-case bound. Preserve the raw cell measurements and timeout alternatives.
This estimator is fixed before any main output or size decision. It budgets every
possible clarification continuation, actual
loading overhead for bounded 50-item shards, and a 25% reserve. Choose400 only with
20 qualified items/cell and a measured/conservative main-plus-ablation forecast
within48GPUhours, with at least12hours reserved for analysis/writing before
2026-10-13 11:59UTC (October12 23:59AoE). Otherwise use a qualified, feasible200core;
if prerequisites fail, report the constraint rather than claim a ready experiment.

Workloads are400:3600main initials+720main continuations+960ablation calls=5280;
200:1800+360+480=2640. There are400or200 independent QA items, not5280or2640.
The main runner is disabled during SPQ06 preparation. A later explicit launch uses
only the local RTX5090 and pinned standalone workers. Conditions execute serially.
Single attempt per item/stage; no answer repair, automatic failed-answer retry,
hidden substitution, simulator/tool access or hosted answering. Raw output and
partial/unknown failures remain immutable. Resume schedules only never-reserved
item/stages, using new exclusive shard roots. Unknown work retains full reservations.

## Scoring and uncertainty

Keep response completion, JSON parsing, typed validity, factual correctness and
reasoning-format diagnostics separate. Direct/predictive/counterfactual use the
accepted typed scorer: unchanged scalar tolerance, Euclidean vectors, sign-invariant
quaternion angle and exact Booleans with units/frames. Explanation scores structured
intervention/fixed-condition/readout/contrast facts only. Nonempty prose is a format
requirement, not adequacy. Clarification reports declared gap recognition, requested
slot match, premature structured answering, routing/completion and resolved-answer
correctness separately. Semantics of disguised prose answers and question wording
remain outside automatic checks.

All selected items remain in task denominators. Missing/invalid/failed/abstained
answers are unsuccessful; valid-only numerical errors require coverage alongside.
Never pool numerical errors across different units or physical quantities. Report
each family endpoint separately, with balanced domain averages. Balanced evaluation
claims concern this qualified balanced design, not natural release frequencies.
Seven-item audit cells and pilot singletons do not support powered subgroup claims.

For main intervals and paired condition differences use95% percentile intervals
from10000paired whole-trajectory bootstrap replicates, seed20261009, resampling
groups within domain/family strata. Apply the same sampled groups to every model
and matched ablation. The prespecified preference for one QA/group is achieved by
the disjoint pools; if implementation detects duplicated/cross-stratum groups it
halts rather than independently resampling correlated records. Report item/group
counts and failed/missing coverage. Model conditions/dialogue turns do not increase
the number of independent items. Pilot timing extrapolation is a feasibility
estimate, not an achieved power or accuracy claim.

## Separate human model-answer prose assessment

If prose quality is reported, assess the first two explanation items in each domain
of the nested core: eight unique tasks, all nine model conditions,72responses.
This deterministic subset is fixed before main outputs, not selected by scores.
Two independent blinded assessors review each response against its original public
task, comparison and source evidence before discussion. No reviewer identity mapping
is assumed. Use separate P1/P2 blank forms and private condition-code mapping.

Primary judgment: adequate or material_error within the supplied evidence. Record
claim-level findings for intervention identity/fixed conditions, comparison fidelity,
supported interpretation and causal restraint, limitations/uncertainty, and clarity.
An explicit warranted limitation is acceptable; acknowledging unresolved semantics
does not license a fabricated mechanism. Equality or within-tolerance contrast does
not establish unchanged physical behavior. Source-supported numerical facts and
readable prose must both be considered; automatic fact checks do not decide this
judgment. Record categories, source locations, exact claim excerpts and comments.

Blank forms are uncollected. Preserve submitted CSV bytes immutably with hashes;
keep discussion, adjudication, rubric revisions and corrections separate. Do not
alter frozen model outputs. Report both independent assessments and missingness;
agreement is descriptive with eight task clusters, without a power claim. Any prose
adequacy claim is limited to this eight-task subset and conditions. This is a model
answer study, distinct from the140-item annotation audit and its three reviewers.
