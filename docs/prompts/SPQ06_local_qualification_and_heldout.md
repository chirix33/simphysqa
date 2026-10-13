# SPQ06 — local baseline qualification and held-out preparation

Active user instruction, 9 October 2026. The earlier draft SPQ06 prompt was never
sent. No SPQ06 branch, implementation, qualification or evaluation export may be
assumed from that draft. Read the cleanup handoff, current main, actual paths,
configurations, active AGENTS and scientific contracts. Reconcile retained context.
Create ordinary branch `simphysqa-spq06` from updated main in the existing SimPhysQA
checkout. Do not create another worktree by default.

## Authorized milestone

Run the baseline qualification pilot while preparing the frozen held-out set where
resources permit. Target four domains × five families (direct, predictive,
counterfactual, explanatory/canonical explanation, clarification) ×20items =400unique
evaluation QA. Prefer one evaluated QA per distinct held-out trajectory group.
Prespecify the nested200core, ten/cell; decide200versus400from measured runtime and
preparation feasibility, never main accuracy. The20-item model pilot is separate
from the human audit. No20-item human calibration was requested. The formal audit
uses the same140unique items independently reviewed by three reviewers, with feedback
processing. Inspect actual SPQ05 records/status rather than infer completion.

## Track A

Select20existing accepted development items, one/domain/family; record identities
and groups. Qualify all nine authoritative conditions: Qwen3-8B thinking off/on;
Llama-3.1-8B-Instruct direct/promptedCoT; Qwen3-32B-AWQ off/on; Gemma3-27B QAT
direct/promptedCoT; DeepSeek-R1-Distill-Qwen-32B native reasoning. Verify actual
artifacts, revisions, quantization, licenses and runtimes; no silent substitution or
assumption that larger models are qualified. Inspect current workstation GPU/runtime
(previously RTX5090/32607MiB). Answer locally, without hosted APIs or remote GPUs;
conditions run sequentially unless measured capacity supports otherwise.

Use intended public inputs, tools=[], no private answers, traces, rollouts or
simulator access. Execute clarification first turns actually; route only supported
requests through recorded replies; execute conditional answer turns. Record absent,
unsupported or ineffective clarification separately. Never replace actual first
turns with authored gold clarification. Freeze limits/failure handling before runs;
retain raw outputs, no silent repair/retry/hard-item exclusion. Save exact requests,
model/runtime revisions, tokens, latency, peak memory, completion, parsing/scoring.
Reasoning compliance is separate from answer validity/correctness. Pilot180initials,
at most36continuations, for execution qualification/timing, not empirical quality.

## Track B

Inventory eligible original held-out population excluding development and prompt
tuning; preserve original splits. Existing11105QA are a source inventory, not a
prepared five-family evaluation. Freeze release/code/schema/annotation versions,
population/exclusions, seed/allocation, family admission/evidence, candidate ordering,
failure/replacement rules, annotation provenance/settings, scoring and privacy before
generation. First ten qualified in each randomized cell order form core; next ten
extension. Never weaken criteria to fill quotas.

Counterfactuals need verified matched conditions/outcomes. Explanations must be
answerable from deliberately supplied public evidence. Clarifications need genuine
fully scrubbed information gaps and scorer-disjoint witnesses; explicit query-gap
clarification is separate from OOD. Preserve numerical tolerances and sign-invariant
quaternions. If a cell is insufficient, report the constraint and concrete remedy
before changing population/allocation. Reuse admitted records/outcomes when suitable;
freeze/qualify sources before new solves. Archive executed payloads and deterministic
procedures with per-file mappings. Calculate concrete bounded resource estimates
before paid/new-budget generation. SPQ05 audit budgets are not SPQ06 authorization;
continue independent work while genuinely missing spending decisions are resolved.

## Main design

Prepare enriched inputs for all nine on the same final set. Prepare matched
structured-only ablation for two representative conditions chosen before main scores,
with rationale. Preserve underlying facts, supplied comparisons, ambiguity and
answerability; remove derived language without removing unique facts or restoring
hidden clarification information. Workload400:3600initial main+720continuations+
960ablation=5280calls. Workload200:1800+360+480=2640. Forecast by condition/family
from pilot measurements, including continuations, loading and explicit reserve.
Target main plus essential ablation within approximately48GPUhours. Choose400only
if measured forecast/preparation supports it, otherwise core200; freeze decision
before any main output. DeadlineOctober12 2026 23:59AoE; reserve analysis/writing.
DecemberNAACL commitment does not extend initial submission.

Accepted scorers: typed numerical/Boolean with unchanged tolerances; separate
structured factual checks and explanation prose adequacy; separate clarification
behavior and resolved correctness. Automatic factual validation does not establish
prose quality. Prespecify a separate human model-answer subset/protocol if reporting
prose quality; the annotation audit is not human model-answer evaluation. Compare
conditions on same items with group/sampling-aware uncertainty. Extra conditions
and dialogue turns do not add independent QA. Balanced benchmark claims do not
describe natural release frequencies. Keep model outputs separate from independent
annotation-audit feedback.

## Delivery and execution boundaries

Allow GPU answering alongside CPU preparation. Pin each job's source/configuration;
do not switch branches or mutate running dependencies. Execute20-item pilot and
prepare validated ready-to-run main, forecast and commands. Do not automatically
launch the larger benchmark. Deliver branch/commit; every-condition qualification
including blockers; actual pilot IDs; frozen200/400manifests and runtime-based size;
validated counts, exclusions/failures; measured forecast/spending; public requests,
private scoring/provenance; exact resume commands; actual tests/limitations.
No human-acceptability, explanation-quality, OOD or main-answering claims without
evidence. Commit implementation for review; do not merge automatically.

## Explicit subsequent user authorization

“Access granted.” — existing HF account's official Gemma artifact terms/access.

“Authorize these SPQ06 ceilings and annotation payloads” —676initial annotation
requests,1352total attempts, two/candidate, USD320,18million reserved input tokens,
2768896output tokens, four cumulative hours annotation attempt work;1612simulator
executions,180seconds each, four cumulative hours workers/static compilations.
Approves exact observed-prefix payloads in external heldout-preparation-1.0.0 to
https://api.openai.com/v1/responses via existing credential reference. No gold/private
future states, no automatic increases, no main answering authorization.
