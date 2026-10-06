# SPQ04 clarification QA — 6 October 2026

Read docs/prompts/SPQ04_clarification_qa.md and docs/simphysqa/clarification_qa.md.
Eight frozen verified development groups; genuine absent query slot with two
private completions agreeing with EVERY initial visible surface. Boolean values
must differ; numerical scorer acceptance regions must be disjoint. No invented
default completion or unique initial gold answer. Recorded reply resolves only
missing query information; gold/traces/witnesses/receipts stay private.
Preserve accepted48 QA, answer annotation1.0.3, association1.1.1 and main.
No simulations/provider/model calls, benchmarks, full release, OOD claim or formal
sample. Human judgments remain uncollected; software slot/scorer checks do not
establish prose adequacy. Read docs/reviews/SPQ04_completion.md.
Historical instructions follow unchanged.

# SPQ03 matched-intervention explanation QA — 6 October 2026

Read docs/prompts/SPQ03_explanation_qa.md and docs/simphysqa/explanation_qa.md.
Eight new explanation QA are explicitly authorized from the eight frozen SPQ02
pairs and selected targets. Supplied comparison readouts are intentionally public
only in this task-specific field; prefix/cutoff, source data, accepted 40 items,
answer annotation 1.0.3 and association 1.1.1 remain unchanged. No new simulations,
model calls, answering benchmarks or definitive formal sample. Claims/traces are
evidence-bound and human-unreviewed. Structured fact checks cannot grade prose.
Read docs/reviews/SPQ03_completion.md; older constraints remain historical below.

# Current bounded refinement — 6 October 2026

Read docs/prompts/SPQ02b_answer_refinements.md and the latest answer contract.
Concise bound explanations, shared conditions once, sign-invariant quaternion
changes; preserve values/cutoffs/privacy/prior outputs. Zero simulation/model calls.

# Active milestone: SPQ02b answer enrichment and prompt provenance

Current user instruction from accepted 1ae35749421283e63344504dc6a5d24ce18f32e7
overrides earlier eight-only scope: enrich all 40 existing QA and eight supporting
alternatives. Read docs/prompts/SPQ02b_answer_enrichment.md and
docs/simphysqa/answer_annotations.md. Keep source/public data, association 1.1.1,
answers/tolerances/cutoffs and prior outputs exact. No simulations/provider calls.
Gold explanations/traces are private and human-unreviewed. Archive actual
annotation requests separately from deterministic procedures and prepared
answering prompts. Durable report: docs/reviews/SPQ02b_completion.md.
Older instructions and findings remain below.

# Active milestone: SPQ02 — 5 October 2026

Read docs/prompts/SPQ02_counterfactual_qa.md, docs/simphysqa/counterfactual.md and
docs/reviews/SPQ02_completion.md first. The explicit SPQ02 chat specification and
confirmed exact factual-replay criterion supersede phase-only SPQ01a prohibitions
on simulations/new QA within this eight-pair milestone. Preserve accepted association
export 1.1.1 and all prior outputs; do not reopen its renderer for cosmetic changes.
Work on simphysqa-naacl from e379013b7e80fe28172682cd39e42f4066fde841. Select
eight existing development groups once; no silent replacement, reference changes
or implicit replay tolerances. Count coarse/fine factual and omission executions.
Only verified alternatives support new counterfactual QA. Keep outcomes/evidence
private; original QA identities, physical values and .2 s cutoffs remain immutable.
No model benchmark, full-release regeneration, broad cleanup or formal sample.
Update SPQ02 completion/progress/decisions. Older instructions below remain evidence.

# SimPhysQA coding-agent instructions

## Active direction and authority
The explicit 4 October 2026 project pivot supersedes Phi-JEPA phase prompts,
MODEL_TRAINING_CONTRACT, training/ODE/EBM/CODI/Coconut requirements and legacy
human-reply approval rules. SimPhysQA targets NAACL Resources, Benchmarks, and
Evaluation: (A) simulator-grounded structured and language-enriched trajectories,
QA, evidence and reproducible annotation; (B) evaluation across models, domains
and question types. Learned dynamics and latent-baseline training are outside scope.

Read docs/README.md, docs/PROGRESS.md, docs/prompts/SPQ01a_event_language.md and relevant
docs/simphysqa specifications. Historical docs/assets/references remain original
evidence, not implementation authority. Do not duplicate the handoff. Inspect
nested instructions and git status. Work on simphysqa-naacl in the simphysqa
worktree; preserve main, unrelated work, source assets and generated datasets.

## Data and annotation contract
Current domains: robotic_arm, driving, object_pushing_stacking, tethered_load.
Start from actual current schema/data. Preserve source/sample/trajectory IDs,
all numerical/Boolean references, units, frames, controls, event definitions and
simulation provenance. Unknown is not zero. Never execute extracted formulas.
Schema development is iterative creation, enrichment and human revision;
do not call it few-shot schema generation. Human review is a research activity,
not a mandatory generation-software approval gate.

Track meaningful trajectory and timestamp descriptions, direct, predictive,
counterfactual, explanation and clarification QA, and question-specific evidence.
Generic timestamp context is incomplete. Do not create QA families by relabeling.
Counterfactual truth needs matched interventions or verified re-simulation.
Causal explanation needs evidence beyond temporal association. Clarification
needs a genuine information gap and justified requested information.
Predictive public language uses observed states and declared controls and must
not reveal realized future outcomes. Auditors can see private evidence;
answering models cannot. Keep references separate from generated prose.

Annotation model is configurable; exact model identity, prompt/schema versions,
settings, failures, every attempt, retry and repair are required provenance.
Keep an alternative-source matched/blinded comparison protocol separate from the
main audit. Document its model/subset/instructions; pending choices stay pending.

## Human audit
Three independent reviewers review the same 20 calibration plus same 140 fresh
formal records: 160 each; 60 calibration and 420 formal ratings. Keep phases and
physical groups disjoint; prefer one record per trajectory. Keep originals,
adjudication and corrections separate. Primary acceptable/material_error judgment
has criterion findings and error categories. Preserve planning assumptions:
80% nominal confidence, two-sided alpha .20, 80% power, .90 expected acceptable
prevalence, kappa .60 versus .80. These are neither results nor passing thresholds.
The supplied audit_power_analysis.py is preserved under docs/references/spq01_audit.
Reconcile its fixed-prevalence one-degree-of-freedom score approximation with
finite-sample simulation; descriptive Fleiss kappa alone is not the powered test.
Formal sampling machinery may preview; do not freeze/export the definitive formal
sample before annotation version, release population and rubric are ready.
No claim that the pooled sample powers domain-by-question-type subgroups.

## Evaluation and engineering
Workstation-only tool-free answering-model experiments. Annotation and private
simulation may use tools. Preserve the five-model/nine-condition plan in
configs/simphysqa/evaluation.json. Planned artifacts remain planned until locally
qualified; pin revisions, tokenizer/runtime/quantization settings before runs.
Public annotations must be included in baseline requests. Report counts and
task-appropriate metrics/uncertainty by model/domain/question type, with missing
or invalid answers retained as failures. No invented empirical results.

New data/weights/cache/run outputs must use configurable external roots and
versioned content-hashed manifests. Existing historical tracked artifacts are
preserved; do not move large archives or delete generated data.
Keep provider/network calls explicit, no credentials in code/logs/manifests,
no network in offline tests and no automatic fixture fallback after live failure.
Live/long runs require a configured budget and authorized credentials.
Do not push/merge/publish/message others unless requested.
Bounded CPU verification and reversible local choices may proceed autonomously.

## Durable handoff
Update docs/PROGRESS.md, docs/reviews/SPQ01a_completion.md and docs/decisions/
with base/branch/source hashes, changed behavior, actual commands/results,
artifacts, deviations, pending validation and next step. For blockers use
docs/prompts/BLOCKER_REPORT.md. SPQ01 authorizes 16 initial requests, 32 total attempts including repairs, and
$5 total estimated/recorded annotation spend. No full-release jobs, definitive
formal export, answering-model evaluation or further broad cleanup.

## SPQ01a event annotation enrichment
Build on accepted SPQ01 6d420b779e0204868fec4c45e26bb1cdcd2b98c7.
Read docs/simphysqa/event_language.md. Link public known events deterministically
with half-open interval and declared point semantics; never nearest-state active
assignment or invented boundary states. Match the whole structured state and
entity/controller declarations. Keep targets/context, additive/total control,
limits/applied values and supported controller phases distinct. Scheduled active
does not verify application/causation; ended timing does not imply effects ended.
Keep .2 s development cutoffs, source facts/QA IDs/references exact. No private
reference events/future states in public construction. Version/hash rules, schemas,
prompt/renderer and cache; preserve SPQ01 outputs in a new versioned external root.
Use deterministic schedule wording with retained measurement prose; this config
allows zero new requests and shares the original SPQ01 budget/prior spend.
Synthetic boundary fixtures are software tests only; report real overlap coverage
gaps. Re-export all 32 development packets and nine-condition public inputs.
Counterfactual/explanation/clarification QA and human results remain pending.

## Bidirectional association export follow-up
Read docs/simphysqa/associations.md. Version derived public association indexes
separately from source/annotation schemas. Both directions must come from canonical
SPQ01a links and agree on relationship/link ID/evidence. Keep full event definitions
and compact nonrecursive indexes; put gap associations in a separate endpoint-ID
array. Do not mutate canonical source QA or prior outputs. The new offline exporter
updates all 32 packets and nine-condition public views consistently with no calls.
Record follow-up results in docs/reviews/SPQ01a_associations_completion.md.

## Grounded shared event-description follow-up
Read docs/simphysqa/event_descriptions.md. Preserve inherited event descriptions;
add canonical public-only shared text, independent evidence bindings and explicit
unresolved status. Copy exactly into state/gap associations. Version renderer,
schema, display convention and cache; never round matching/source values. Preserve
prior outputs and source recovery. No simulations/model calls or new QA families.
Report results in docs/reviews/SPQ01a_event_descriptions_completion.md.
