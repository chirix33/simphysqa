# Matched-intervention explanation QA — SPQ03 /1.0.0

This implements [the full user instruction](../prompts/SPQ03_explanation_qa.md)
from accepted 10ace28. New question family: explain the controlled intervention
comparison, not merely supply a counterfactual numerical answer or read an answer's
accompanying explanation. Eight engineering-development items reuse every frozen
SPQ02 pair and its existing single selected target: two per domain, no replacements.
Three unchanged Booleans and two nonzero within-tolerance contrasts are retained.
Groups, splits and the twenty-group formal exclusion configuration stay exact.
This is not an unbiased release-wide quality sample.

## Public evidence and task boundary

Wrapper simphysqa/0.4.0 adds explanation_evidence/explanation_annotation privately;
original v1 source restoration remains exact. Existing wrapper families and accepted
40-item export/answer contract 1.0.3 are unchanged. The task changes question/type
and adds explanation_task, supplied_comparison and explanation_response_contract.
The selected target descriptor/rule/tolerances in answer_spec are unchanged; its
role is described explicitly, because the response is now an explanation.

Public supplied_comparison version supplied-selected-outcomes/1.0.0 contains only
the selected factual_scheduled/omission readouts, target/entity/quantity/time,
unit/frame and an explicit disclosure. It is intentionally supplied simulation
evidence, not an observation in the original .2-second prefix. No saved observation
is added, moved or rewritten. The original controller, entities, physical context,
known schedule and observed language remain exact. Accepted bidirectional/event
description projection 1.1.1 still describes the factual scheduled world.

No gold explanation/trace, private rollout/events, receipt, implementation snapshot,
operator path or generator identity enters answering requests. All nine conditions
have tools=[] and an explanation-specific user prompt and JSON response schema.
The additional answering models/artifacts remain planned until locally qualified.
Prepared answering requests are not executed annotation requests or benchmarks.

## References and trace evidence

Each concise reference separates declared control, implemented omission, fixed
conditions, measured selected outcome, supported interpretation and uncertainty.
Boolean references additionally quote the actual threshold/history/duration rule
and bind both event histories; sparse terminal measurements never replace that
predicate. Numeric comparisons separate canonical equality, numeric difference
and acceptance under the unchanged answer scorer. Scalar absolute error, vector
Euclidean error and sign-invariant quaternion angle retain accepted conventions.
Equal flags/sub-tolerance contrasts do not establish absence of physical effects.

Arm removes only the additive pulse and retains both base torques; private saved
implementation/arm interpretation corroborates actual generalized hinge controls,
while raw historical world/joint_local metadata remains untouched. Driving removes
the zero-velocity brake command, preserving friction/contact; torque limit is not
realized torque. Objects remove the external force on block_1, with block_2
contextual. Tether removes the complete support program, both acceleration phases
and subsequent displacement. Remaining model dynamics and execution settings stay
fixed, verified against the saved matched configurations/reservations.

Claim and step bindings use explicit public/factual/alternative/pair/context roots,
JSON pointers, value hashes, and state/event/run IDs where applicable. Every claim
has a stable ID and a supporting procedural trace step. Actual saved method/settings
and non-null replay/admission verification live in the trace and private evidence.
Status evidence_checked_human_unreviewed means saved evidence/consistency checked,
not new simulation, proven detailed mechanism, real-world causality or human quality.
The selected outcomes alone do not determine all other physical behavior.

Validator rerenders from the accepted parent, checks its original-source/pair
validation and accepted annotation 1.0.3, matches all four saved execution
reservations at each precision modulo role/omission flag, resolves every claim,
checks target/value/frame/time/cutoff/group and exact public projection. No physical
model, provider or simulation worker executes. Cache identity pins parent content,
procedure, response implementation, rubric and schema. Exclusive writes and manifests
reject stale/changed content rather than overwrite it. Human corrections require
separate versioned records; no human generation approval gate is introduced.

## Evaluation coverage and human rubric

[Rubric JSON](../../configs/simphysqa/explanation_rubric.json), version
matched-explanation-rubric/1.0.0, gives six required supported-claim/quality criteria,
acceptable paraphrases, contradictions/unsupported claims and mapping to existing
independent form criteria. Human primary judgment remains acceptable/material_error;
original ratings, adjudication and corrections stay separate. Three forms contain
eight shared development packets each; all are blank and uncollected.

Response explanation-response/1.0.0 contains readable explanation, supported
interpretation and uncertainty, plus structured intervention identity, fixed-
condition declarations, selected readouts and equality/scorer facts. All conditions
use the same contract; prompted-CoT wording fits the explanation field rather than
conflicting with the final JSON. No exact reference text, keyword list or MSE grades
an explanation. Nonempty prose is only a formatting requirement.

explanation_evaluation.check_facts and score_facts (factual-components/1.0.0) check
six structured components. Reported readouts use unchanged source tolerances and
typed metadata; exact-value diagnostics are separate. These checks do not inspect
semantic entailment, unsupported prose, completeness, readability or explanatory
adequacy. overall_explanation_correctness is null and human judgment uncollected,
even when all facts pass. Missing/failed/invalid/abstained items stay in denominators.
Numerical readout score() rejects this family rather than silently treating it as
an ordinary numerical answer. Example API for future supplied predictions:

```python
from simphysqa.explanation_evaluation import score_facts
result = score_facts(records, supplied_predictions, selected_condition_ids)
```

That API runs no models. Before empirical evaluation, locally qualify exact model
artifacts/runtimes and freeze human explanation assessment, uncertainty/aggregation
and comparison analysis separately. No performance or agreement estimate exists now.

## Archive and remaining scope

[Stable archive entry](prompt_archive/README.md), [catalogue](prompt_archive/catalogue.md)
and [per-file index](prompt_archive/file-generation-index.json). Archive 1.0.6 labels
questions/references/traces deterministic and language reuse linked to the original
executed request. New deterministic fields resolve to the accepted matched
counterfactual parent; embedded accepted parent copies are separately inventoried.
All sixteen actual model payloads are exact/unchanged, zero reconstructed/unavailable.
Two preliminary association/event-description source revisions remain explicitly
unrecoverable, with their executed/output hashes retained. Authoring instruction,
deterministic procedure and prepared answering prompt are distinct.

Clarification QA needs genuine underdetermination and justified requested missing
information; no new clarification items are created. Human review/rubric calibration,
paired alternative annotation-source protocol, locally qualified answering models,
later observed-event views, full release enrichment and final formal sampling remain
subsequent work. This eight-item engineering sample does not change the settled
calibration/formal allocation or power every subgroup.
