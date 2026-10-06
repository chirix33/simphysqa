# Evaluation direction — five-family foundation/1.0.0

Answering is workstation-only and tool-free; annotations/public structured inputs
under evaluation are actually included. Private gold/traces/rollouts/receipts stay
out. configs/simphysqa/evaluation.json retains exact artifact/runtime fields and
disabled execution budget. Five models/nine conditions: Qwen3-8B thinking off/on;
Llama3.1-8B-Instruct direct/promptedCoT; Qwen3-32B-AWQ off/on; Gemma3-27B-ITQAT
direct/promptedCoT; DeepSeek-R1-Distill-Qwen32B native reasoning with a pending pinned
locally-qualified quantized artifact. Historical qualification is not SimPhysQA
task qualification. No answering experiment has run;504 requests are preparation,
with72 additional conditional clarification templates.

Direct/predictive/counterfactual use typed private targets: scalar absolute error,
Euclidean-vector error, sign-invariant quaternion rotation angle and exact Boolean
values with declared tolerances. Typed units/frame/time/target bindings are required.
Simulator admission and exact replay are separate from answer correctness.

Explanation QA intentionally supplies selected matched outcomes in a separate
public comparison. explanation_evaluation.score_facts checks structured factual
components only. It cannot establish prose quality, explanatory adequacy or human
acceptability by keywords/exact text/MSE. Numeric score() rejects that family.

Clarification uses a dedicated initial partial view and conditional reply routing.
clarification_evaluation.score_interactions separates declared gap/slot, explicit
premature structured answering and post-reply typed correctness. Equivalent relevant
questions are acceptable; exact reference wording is not required. Semantic wording,
compound questions, disguised prose answers and explanation adequacy need independent
human assessment. Reference questions/replies are authored, not executed model turns.
Unresolved records have no unique numerical truth; ordinary score() rejects them.

The implemented preparation/scoring adapters retain missing/invalid/failed/abstained
cases. Empirical aggregation, human assessment and uncertainty analysis still need
a frozen protocol and locally qualified runner before benchmarks. Eventual tables
must report model/domain/family, counts, task-appropriate metrics and uncertainty.
Use group-aware dependence handling;56 engineering items do not power all subgroup
claims or establish release-wide/OOD performance. [Foundation](foundation.md),
[family rubrics/contracts](explanation_qa.md), [clarification contract](clarification_qa.md).
