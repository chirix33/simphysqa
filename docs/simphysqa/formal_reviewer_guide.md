# Focused reviewer guide /1.0.0

Review independently using your assigned R1, R2 or R3 slot. All three reviewers
inspect the same140 items; slots do not specify personal identities. No separate
calibration set. Copy your frozen CSV form before editing. Submit original ratings
before discussion. Blank judgments are uncollected, never acceptable ratings.

Primary judgment: acceptable or material_error **within the focused scope**:
physical/global context, trajectory language, question wording/type, generated
timestamp language and state–event descriptions. A material error could change
the physical interpretation, target/entity/time/unit/frame or intended question,
or asserts an unsupported fact/effect. Optional gold answers, explanations, traces
and extra private verification corroborate this scope; they are not automatically
part of a comprehensive answer-quality audit. Do not rate answering-model performance.

Supply each criterion as acceptable/material_error/not_applicable:
global_context; trajectory_language; question_type_wording; timestamp_language;
state_event_descriptions. Use not_applicable only for a criterion that has no
applicable content (e.g. no declared events); missing required content is an error.
Global context describes physical setup; trajectory text describes the observed
window. They need not be duplicate paraphrases. Timestamp text is generated
language joined by state_id, distinct from the generic original state.context.

Error categories: factual_contradiction, unsupported_claim, wrong_entity,
wrong_time, wrong_unit, wrong_frame, misleading_event_semantics,
question_type_mismatch, readability, missing_required_field, other. Minor awkward
wording may be recorded in comments while the item remains acceptable. Use the
readability error category for material ambiguity/illegibility. For material_error
record at least one material criterion, category, source location (JSON pointer,
state/event/link ID or question field) and an explanatory comment. Separate
multiple categories/locations with semicolons. Criterion CSV syntax:
`global_context=acceptable;trajectory_language=acceptable;question_type_wording=acceptable;timestamp_language=acceptable;state_event_descriptions=not_applicable`.

Assess statements against original measurements/relations, entities and declarations,
with their units/frames and exact temporal relationships. Scheduled future events
are declarations, not evidence they were applied or caused an effect. Ended timing
does not mean effects ended; torque/force limits do not establish realized values.
Shared event text repeats per state with that state's actual relationship.
Explicitly labeled unresolved semantics or limitations are acceptable if the prose
faithfully conveys what is established and uncertain. Asserted resolution without
evidence, concealed uncertainty that changes interpretation, or contradicted source
is material_error. Never convert a declared limitation into an invented fact.

Direct asks an observed readout. Predictive asks future outcomes. Counterfactual
asks the verified omission world; a Boolean can remain unchanged and a numerical
contrast can be within tolerance. Explanation intentionally supplies its selected
comparison outcomes in a separate task field, not in observed states; assess
question/family framing and public descriptions, not automatically every private
gold claim. Clarification is an explicit absent query selector with two compatible
incompatible-answer completions. Inspect labeled initial question/view, authored
clarification, recorded author reply and resolved question/view. They are reference
turns, not an executed model conversation. The reply supplies information, not gold.

Freeze original submissions immutably. Discussion, adjudication, proposed annotation
corrections and any later rubric revision live separately and do not change the
packets or original independent ratings. Do not begin formal review from the
development extraction-check index or header-only preparation templates.
