# Local evaluation direction

Workstation-only, tool-free answering models; tools are permitted for annotation
generation and private simulator verification. configs/simphysqa/evaluation.json
carries five models and nine conditions: Qwen3-8B off/on, Llama-3.1-8B-Instruct
direct/prompted CoT, Qwen3-32B-AWQ off/on, Gemma-3-27B-IT QAT direct/prompted CoT,
and DeepSeek-R1-Distill-Qwen-32B native reasoning using a pinned locally qualified
quantized artifact. Additional artifact revisions, quantization/runtime settings
and hardware qualification are pending. Null fields mean unresolved, not default
permissions to download or run. No model calls occur in bootstrap.

Historical Qwen/Llama artifact identities and runtime settings are carried forward
from P12 files. Prior qualification is historical and does not qualify the new
annotation/task inputs. The actual Qwen thinking completion allowance is 8192 tokens
and 360 seconds; historical direct/Llama conditions retain their recorded budgets.
These are preparation settings, not a newly authorized experiment.

baseline-requests exports actual public structured inputs AND public language
annotations to every condition. Requests have tools=[] and contain no references,
future states, verification metadata, organizer/source paths or generator identity.
The importer/exporter tracks annotation version and condition. SPQ01 has generated human-unreviewed public language on the development subset.
Release-wide language and answering-model evaluation remain pending. These requests
provide transport, not empirical answering-model performance.

Later result tables must cross model/condition, domain and question type with
actual example/trajectory counts and failure denominators. For typed readouts:
exact Boolean accuracy, per-channel/unit/frame MAE/RMSE, declared tolerance accuracy,
coverage/invalid/abstention and whole-question correctness. Preserve original
numerical predictions separately from generated prose. For direct/predictive/
counterfactual QA use verified family-specific references. Explanation needs
claim/evidence and unsupported-causality scoring; clarification needs gap/request
validity, not predictive numerical relabeling. Metric/rubric operationalization for
new families remains pending.

Compare conditions on matched examples. Uncertainty resamples physical trajectories
and keeps all model/question variants together; nominal confidence/replicates and
multiplicity treatment must be frozen separately from human-audit power assumptions.
Export raw outputs, artifact/runtime/template identities, attempts/tokens/time/cost,
per-item scores and aggregation manifests. No trained Phi-JEPA/SCLD/EBM/CODI/Coconut
baselines belong in this paper. Aggregation/scoring adapters for new families and
qualified inference runners remain pending; no benchmark result is produced here.

## Supplied-prediction scoring interface

The private score command implements typed readout scoring for current predictive
records, with model/condition/domain/question-type tables and per-channel counts,
Boolean/tolerance accuracy and valid-only numeric MAE/RMSE accompanied by coverage.
Every configured example remains in the denominator, including missing, invalid,
failed and abstained output. Quaternion error is sign-invariant rotation angle in
radians; other vectors use Euclidean distance. It never calls a model/simulator.

Predictions JSON is a list of objects containing condition_id, sample_id,
annotation_version, status (completed/failed/invalid/abstained), and targets (each
target_id/value/unit/frame). Model prose can be stored separately and cannot replace
these values silently. The caller explicitly selects one or more configured
conditions. Unknown/duplicate identities or wrong annotation versions fail.
New-family adapters and uncertainty computation are pending; score artifacts
explicitly mark uncertainty unavailable until its analysis settings are frozen.
Only synthetic test inputs were scored in bootstrap; these are not experiments.
