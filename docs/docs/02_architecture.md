# Architecture and contracts

[Start](../README.md) · [Defaults](08_defaults_decisions.md) · [Assessment](04_assessment_fallback.md)

This is the concrete development specification. Values explicitly called defaults are adjustable experiments, not quotations from the professor. Module names are proposed; preserve equivalent existing interfaces when their behavior is correct.

## Package boundaries

Use a `src/phi_jepa/` package with `contracts`, `config`, `data`, `providers`, `encoding`, `models`, `solvers`, `training`, `assessment`, `inference`, `evaluation`, `baselines`, and `artifacts`. Keep physical generators and evaluator oracles in a clearly separated benchmark namespace. Third-party baseline source belongs under a pinned external checkout or dependency path, not copied into the core neural module. Start with CLI commands, not a web UI.

Use Python 3.12, typed Pydantic or dataclass boundaries, NumPy for data and PyTorch for learning. Keep network, model-download and accelerator dependencies optional for offline contract/evaluator tests. Choose packaging/CLI details in P00 and lock verified environments; do not combine the distinct CoConuT/CODI dependency trees.

## Typed objects

| Object | Required responsibilities |
| --- | --- |
| `ScenarioInput` | Stable ID/family ID; scenario text; explicitly observed initial facts; observable specification; physical query horizon and permitted event/control information; no target/OOD labels |
| `ObservableSpec` | Stable quantity ID/name, unit, frame, target position/index, output mask and tolerance policy; no unitless interpretation of a naked array |
| `TrainingExample` | Label-free input plus separate target record and training-only solution annotations |
| `EvaluationTruth` | Physical trajectory/time grid, terminal target, OOD type/cause and reviewed audit constraints; never accepted by inference API |
| `ExtractedSchema` | Exact adopted response envelope; preserved original payload and content hash |
| `SchemaFeatures` | Nodes/edges, numeric features, frozen string embeddings, masks and source bindings; no invented facts |
| `PhysicalPrediction` | Terminal values, ordered observable IDs, units, physical time, optional sampled trajectory, validity mask and producing checkpoint |
| `Assessment` | Component scores, availability/coverage, references, threshold/calibration ID, decision and evidence; no false zeros for unavailable terms |
| `AnswerRecord` | Exact adopted answer payload plus internal numeric comparison and provenance sidecar |
| `RunManifest` | Dataset/split/code/model/config/prompt/schema/checkpoint hashes; environment; seed; mode; budgets; cache policy; actual calls/tokens/errors; artifact paths |

Use immutable input objects. Conversion from a raw benchmark record to `ScenarioInput` explicitly selects allowed fields. Adding an OOD label, terminal target or gold future trajectory to inference must fail a boundary test. Debug fixtures are visibly named and cannot silently replace real extraction or evaluation inputs.

## Forward computation

For batch B, text width E, structural width C, hidden width H, target width D:

1. `q = frozen_text_encoder(question)` has `[B,E]`. The encoder is eval-mode, gradient-disabled, model/revision pinned. Use the same encoder for meaningful schema strings initially. The proposed downloadable development encoder is `sentence-transformers/all-MiniLM-L6-v2`; use a deterministic fixture only for plumbing tests and label its results. Long-text truncation is measured and recorded.
2. Convert the adopted JSON to a generic tree/graph. Make nodes for containers, keys and typed values; parent/child and sequence-position edges preserve structure. Numeric features retain signed values, bounded sign-log encoding, presence masks, and type indicators; text features preserve **actual string values**, not just paths. Do not use an LLM-generated domain string to select hidden authored physics.
3. `s = schema_encoder(features)` is `[B,C]`. Initial candidate: two message-passing rounds over the generic JSON graph with masked pooling; implement in plain PyTorch if this avoids a heavy graph dependency. A pooled structured-token encoder is a comparison, not silently the claimed graph encoder. Use variable-length masks, not one fixed eight-field schema.
4. `z0 = W_h [q || s] + b_h` is `[B,H]`. The projection is trainable and linear. Do not replace it with a learned numerical simulator whose state is hand-engineered per question.
5. Integrate `dz/dτ = f_theta(z, τ)` with a differentiable solver on normalized physical time `τ=t/T`. T and requested horizon are supplied in the label-free question/context. Store both physical and normalized grids. A latent ODE trajectory is an internal prediction, not proof of correct intermediate physics.
6. `y_hat_norm(T) = W_y z(T) + b_y` is `[B,D]`; inverse train-fitted normalization supplies physical units. Readout is linear initially. `q_hat = W_q z(T) + b_q` is `[B,E]`.

The first domain has a fixed registered observable layout. For multiple domains, use per-layout linear heads and normalization keyed by declared observable metadata, with a shared core as an explicit experiment. A previously unseen output layout is unsupported until trained/evaluated; a language decoder cannot create a validated physical readout for arbitrary new variables. Report this boundary and any metadata engineering. Do not silently pool “column 0” across unrelated physical units.

Physical time is the active implementation convention. The older paper's artificial reasoning-time interpretation is superseded here. Do not conflate solver substeps with observation samples, or train on intermediate labels merely because the dataset contains them.

## Objective

Compute the physical loss only from valid terminal coordinates:

`L_phys = mean_over_samples(mean_over_valid_targets((y_hat_norm(T) - y_gt_norm(T))**2))`.

Reject training records with zero valid supervised targets; do not create a zero loss. Fit per-observable normalization only on training labels and persist it. Constant coordinates use a documented epsilon/unit scale and are reported separately.

Development semantic choice:

`L_sem = mean(1 - cosine(q_hat, stop_gradient(q)))`;
`L = L_phys + beta * L_sem`, initial `beta=0.1`.

This cosine term is **semantic regularization**, not the rejected cosine physical guidance. `beta=0` is required as a separately trained ablation. Log both raw terms and gradient magnitudes; validate a small declared beta grid before the main study. Zero-norm q or q_hat is an invalid/degenerate embedding condition with explicit handling, not fabricated perfect similarity.

No intermediate-state MSE, pretrained-target EMA, EBM loss, derivative-supervision loss or latent energy loss in the primary objective. Extra objectives are separate changes requiring documented scientific review.

## Solver and training defaults

Use differentiable fixed-step RK4 first, ordinary autograd, FP32; no adjoint implementation requirement initially. Start with 32 internal steps over the query horizon. Use a step-refinement check against 64 on held-out development inputs; monitor numerical agreement independently of predictive error. Set a finite step/compute budget and detect nonfinite states. Do not clamp physical predictions to make violations disappear. A later adaptive solver fits the same interface and is separately validated.

Represent emitted states as `[B,T,H]`; physical samples as `[B,T,D]`. A tensor of requested output times is separate from solver-internal steps. A batch-one test must prove initial and terminal vectors have D entries, not T×D entries.

Use train-only caches for frozen features; batches keep differentiable schema-encoder outputs uncached across optimizer updates. Start AdamW at LR 1e-3, weight decay 1e-5, batch 16, gradient clip 1, seed 11, and a small development training cap. These are prototype defaults, not a final search budget. Select checkpoints by normalized terminal physical validation error; always report semantic term separately. No test-set selection.

Train a **separate text-only latent ODE** using the same question encoder, comparable widths, readout and terminal objective, without a schema branch. It supplies both a transparent no-schema baseline and the numerical fallback path. This avoids deploying a full model under an unseen all-zero schema. Its parameters/training cost must be included when the full deployed system carries this fallback checkpoint. This default is a concrete implementation of the normal unguided ODE fallback, not inference adaptation.

## Frozen language providers and exact assets

The versioned originals are in [assets](../assets/prompts.json), [extraction schema](../assets/extract_schema.json), [judge schema](../assets/judge_schema.json), and [answer schema](../assets/answer_schema.json). Prompts and schemas are constants with hashes. `REPAIR_PROMPT` is archived, **not reachable in the inference execution graph**.

An offline provider replays explicit fixture responses with provenance; a live adapter uses configured model IDs and structured output supported by that SDK. Validate refusal, incomplete generation, malformed JSON, unsupported schema, timeouts and rate limits as distinct outcomes. Bounded transport retries do not authorize semantic repair. Initial inference extraction policy is one successful response attempt, with up to two transport retries only; invalid content triggers the declared fallback. Any preparation-only repair experiment requires its own mode/record and never observes test predictions.

Do not select a current paid model ID from the notebook's conversational label. Live execution requires a user-provided valid model ID and bounded run budget; missing credentials do not block offline implementation. Never log credentials, request headers or environment dumps. Hash cache keys over exact input text, prompt/schema version, provider/model revision, decoding settings and relevant context, not just case ID.

The adopted extraction schema permits numeric observations but not null numeric values. Represent unavailable numbers in `unknowns`; internal output slots start null with a validity mask. The answer schema's `final_state` array is accompanied by internal named metadata. Preserve external contracts; do not silently change arrays to a new object format.

## Final answer payload and validation

Send the original question/schema, named initial observations, named decoded terminal predictions, physical horizon, selected compact rollout summaries, and fallback status. Normalization must already be inverted. Select one sample explicitly before slicing time. Do not send evaluation labels, entire batch tensors or accidental repeated trajectories. Set configurable sample/token limits and log payload sizes.

The numerical `PhysicalPrediction` is authoritative for numerical metrics. Check the LLM's `final_state` length and agreement with that prediction at declared tolerances. On disagreement preserve both and flag `answer_numeric_mismatch`; never overwrite the original prediction to improve a score. A deterministic formatter can expose known numeric output if generation fails, clearly labeled as a software fallback with unavailable narrative. If no numeric prediction exists, return a terminal failure object; the fixed numeric answer schema cannot honestly encode arbitrary missing outputs.

## Checkpoints and tests

Checkpoint includes all learned states, optimizer/scheduler/RNG where needed to resume, architecture/config, frozen-model/tokenizer revisions, feature schema, target layouts, scaling, split hashes, prompts, training history and selected validation epoch. Store weights and typed metadata without secrets. Inference must recreate a prediction within tolerance in a fresh process without reaching into the training dataset.

Required tests: input-label separation; zero/negative/scientific values; schema semantic distinctions; gradients reach intended parameters while frozen encoder remains unchanged; terminal-only loss independent of unconsumed intermediate truth; RK4/refinement on an analytic test vector field; tiny-set overfit trend; checkpoint round trip; batch/time axis regression; numeric answer mismatch; solver failure propagation. Fixtures verify mechanics, not research performance.
