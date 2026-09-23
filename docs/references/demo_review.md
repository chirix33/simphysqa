> Reference-copy note: notebook links below point to a source-identical copy with outputs/metadata removed. The quoted notebook SHA-256 identifies the original supplied file; see the source manifest for both hashes.

# Phi JEPA: September 22 decisions, demo results, and source audit

Updated after the user supplied the generating notebook and Professor Kaushik’s explicit instruction: **“We should stick with the decisions we did in the morning.”**

## Current status

Both previously requested inputs are resolved. The inference policy is settled, and the generating source has been reviewed. There is enough information to draft the complete modular implementation plan without another broad clarification round.

The demo is a useful source of prompts, typed response contracts, basic components, and recorded development results. Its algorithm and evaluation cannot be adopted wholesale: the source contains known deviations from the agreed method and several concrete defects. These are implementation tasks, not reasons to reopen settled scientific decisions.

No notebook/repository source was modified, no model API calls were made, and no full experiment was rerun. Selected pure functions were exercised locally against the saved results to verify the shape, schema-encoding, and metric findings below.

## Authoritative decisions

| Topic | Current decision |
| --- | --- |
| Test-time energy | Fixed scoring for assessment, OOD diagnosis, and the agreed fallback policy. No separate EBM training. |
| Test-time optimization | Exclude latent gradient descent, Langevin updates, anchor/radius optimization, and K1 adaptation loops. |
| Test-time schema repair | Exclude K2 topology repair and prediction-driven rewriting of constraints. Preserve scenario-supported input facts and bounds. |
| Physical prediction | Frozen question embedding plus a modular structured-schema encoder, trainable hybrid projection, latent ODE, and physical-state readout. |
| Training loss | Terminal physical-state MSE plus the agreed question-alignment regularizer. Exact semantic distance/weight are explicit plan defaults to validate. |
| JSON generation | Frozen prompted LLM generates the final explanation/structured answer from question, extracted structure, and named physical predictions. No separately trained arbitrary-JSON decoder is required for the initial implementation. |
| Structured encoding | Preserve names, values, units, relations, events, and topology. Compare interchangeable tree/graph or other explicitly defined encoders. |
| Prompt/schema choice | Adopt the supplied prompt strings and response schemas as the baseline. Correct tensor handling and provide field metadata in the payload. |
| Bregman | Deferred. |
| OOD contribution | Detect and provide evidence-supported possible causes; do not equate this with autonomous trajectory correction. |

The afternoon meeting’s later decoder decision supersedes its preliminary discussion of training a separate JSON probe. The latest explicit confirmation resolves the demo’s optimization/repair conflict in favor of the morning decisions. The old manuscript is not an implementation authority.

## Sources

- [Generating notebook](sources/professor_demo_source.ipynb), all 71 source/markdown cells reviewed. SHA-256: `a66b96b69c304268218d058235d4a1f5669164cd5cb0535323c6e6cce44668d6`.
- [Demo results archive](sources/phi_jepa_results.zip), all 14 files reviewed previously and used for targeted source checks.
- [September 22 part 2](sources/september_22_part_2.docx), particularly 18:35–19:53 for final decoding and 22:38–24:00 for the regularizer ablation.
- [September 22 part 1](sources/september_22_part_1.docx), plus the user’s latest explicit confirmation of its inference decisions.
- [Current manuscript](sources/active_paper.pdf), subject to those meeting corrections.

Notebook references below use function names and section headings so they remain understandable if cell numbering changes.

## What source inspection resolves

### 1. Training does not implement the agreed objective

`train_phi` rolls out the complete time grid and computes:

- `MSE(predictor(Z), target_state(Y))` over all times;
- `MSE(state_decoder(Z), Y)` over all times.

This is full-trajectory supervision plus an additional target-embedding objective. It is not terminal-only physical MSE plus question-semantic reconstruction. The `lambda_anchor_l2` and `lambda_anchor_cos` terms belong to test-time embedding updates, not to training-time semantic regularization.

The `online_state` encoder is never used in a differentiable training loss, so it receives no training gradient. Its `target_state` copy is updated from it by EMA; that machinery therefore does not create the intended learned target encoder. Do not carry it into the agreed implementation merely because it appears in the demo.

The physical decoder is a two-layer MLP, whereas earlier explanations describe a linear readout. Make the agreed linear readout explicit in the initial configuration; additional decoder capacities can be isolated comparisons. Validation records are generated but never used for checkpoint selection. Training history and state-normalization statistics are not packaged in a self-contained checkpoint.

### 2. The schema encoder discards textual values

`SchemaEncoder.forward` embeds JSON leaf paths and numerical features. It does not embed the string values stored at those paths. Therefore observation names, units, relation operators, event descriptions, evidence text, and relationship strings can change without changing the encoder inputs, provided the paths and numbers remain the same.

A local check constructed one schema for speed=5 m/s with a maximum relation and another for mass=5 kg with a minimum relation. Their encoded inputs were identical. The question embedding still supplies question text, so this does not mean the whole model receives no semantics; it means the explicit schema branch loses precisely the distinctions it is intended to contribute.

The encoder uses a Transformer over path/numeric features, not an explicit tree/graph network. A replacement must preserve textual values and define structural relationships, masking, and pooling. Unknownness and absent fields also need deliberate representations.

### 3. Answer generation contains a batch-axis bug

Inference produces `Yhat` with shape `[1,126,8]`. `decode_answer_openai` expects `[time,state]`, but receives that batch-shaped array directly. Consequently:

- `y[0]` is the entire trajectory, not the initial state;
- `y[-1]` is the same entire trajectory, not the terminal state;
- `y.min(0)` and `y.max(0)` also return that same trajectory for a batch of one.

A local replay of the payload construction confirmed four identical `[126,8]` arrays. The intended compact four-vector payload contains **32 numbers**; the current payload contains **4,032 numbers**. This explains much of the unexpectedly large answer-request payload. It does not establish an exact proportional speedup, which must be measured after correction.

Define and validate the batch/time/state contract, select the intended sample explicitly, and attach observable names, units, times, coordinate frames, and normalization status. Selected rollout samples for OOD diagnosis should be deliberate additions rather than accidental copies.

### 4. Reported PCVR is a text-provenance score

`schema_pcvr(X,S)` has no predicted trajectory argument. It checks whether evidence occurs in the scenario and whether each observation’s number appears textually in its evidence. It does not check trajectories, physical laws, numerical bounds against predictions, or functional correctness.

The arm penalty is now explained exactly: the schema stores the number of joints as `2`, while its valid supporting text says `two-joint robot arm`. The numeric substring check fails. Five observations produce ten checks plus one event check, giving 1/11 ≈ 0.0909. An empty schema returns zero automatically, explaining the standard baseline’s zero score.

Replaying this function reproduces every saved PCVR value exactly. Retain an appropriately named provenance/coverage metric if useful, but implement physical evaluation independently and consistently across methods. Treat absent evidence/check coverage separately from compliance. Do not adopt the current PCVR labels for manuscript reporting.

### 5. The actual energy differs from the paper’s reference-cosine energy

`differentiable_bound_energy` uses trained query-conditioned value heads to reconstruct numeric observations from the input schema. It compares their predictions to those extracted input values, treating every observation as an equality. It does not interpret maximum/minimum operators or compare physical rollout outputs with their applicable limits. This is learned input-value reconstruction, not the described latent-reference cosine energy.

`total_energy` combines that reconstruction error with an optional semantic judge score. It has no retrieved-reference latent cosine term, and `lambda_json` is configured but unused in the calculation.

`evaluate_model` explicitly sets `use_judge=False` for the full method; the ablations and sweep also disable it. Thus the stored full-model evaluation does not demonstrate the intended hybrid LLM-judged energy. The repair calls are not semantic-judge calls.

The final plan must implement the agreed fixed score explicitly, with train-only references, a validation calibration rule, component diagnostics, and an OOD explanation interface. Remove the adaptation-specific value probes unless a separate justified role is agreed; they are not required by the approved answer-generation approach.

### 6. The existing baselines are not independent method comparisons

The driver trains one `full` model per seed, then evaluates all four labels using that same checkpoint. The “Standard Neural ODE” zeros the schema input of this fully trained model; it is a schema-removal evaluation ablation, not a separately trained numerical baseline. The `variant="node"` training path exists but is not used by the driver.

The “without EBM” function still computes energy and triggers energy-based fallback. In this run, all eight full/no-EBM cases exceed the energy threshold, so fallback gives the same zero-schema rollout as the so-called standard baseline. This explains the exact trajectory equality already observed.

`static_pin_penalty` is not used in training or evaluation. It is a generic adjacent-slice squared-difference expression rather than an implemented system-specific physics residual. The exported PIN-ODE DEO row therefore does not show that a PIN-ODE experiment ran.

Train actual baseline models under their stated inputs/objectives; distinguish inference ablations from independently trained baselines; define the no-energy comparison so energy-triggered actions are genuinely disabled.

### 7. Oracle behavior and state definitions are now available

| Domain | Eight observed coordinates, in source order |
| --- | --- |
| Driving | x position, y position, x velocity, y velocity, yaw, yaw rate, friction coefficient, applied x force divided by 1000 |
| Arm | first joint angle, second joint angle, first angular velocity, second angular velocity, first angular acceleration, second angular acceleration, gravity magnitude, payload-body mass |
| Slosh proxy | tank x position, slosh angle, tank x velocity, slosh angular velocity, tank x acceleration, slosh angular acceleration, damping coefficient, applied tank force |

These names must accompany model outputs. Different domains reuse coordinate indices for different physical quantities; report per-observable errors and declare any aggregate scaling. The current train-derived normalization pools these mixed columns across domains.

`sim_drive` applies `-mu*9.81*1000` as an x force at every step, even after forward velocity reaches zero. It consequently reverses motion. This is an imposed signed-force toy model, not passive friction stopping dynamics. Correct or relabel the oracle before using it as a physical benchmark.

The slosh system is explicitly a pendulum-like mechanical proxy in the notebook’s final notes, not a continuum-fluid solver. Its “braking shock” is implemented as a positive applied-force pulse. The force profile, initial conditions, physical interpretation, and text description must agree. Samples are recorded after simulator steps while the learning time grid begins at zero; align the recorded timestamps and initial-state convention.

Parameter-OOD ranges are explicitly separated in the code (friction, gravity, damping). The “topology” cases are timed parameter/forcing changes; they do not change the simulator’s joint/graph topology. Keep these as event/regime shifts unless a true structural-change benchmark is added.

### 8. Reliability and measurement need routine corrections

- The leakage guard checks an artificially constructed `{text,id}` dictionary, while inference still receives the complete record. The inspected inference path does not directly read test `Y`, but that guard does not enforce the broader API boundary it claims to enforce. Pass a label-free inference record; keep evaluation labels in the evaluator.
- `total_nfe` misses the ODE solves inside the phase-1 optimization loop. The exact interpretation of the old NFE column is therefore incomplete. Removing the loop simplifies the new method, but counters still need to cover every executed solve.
- Both default full configuration and smoke mode use the same `...smoke20` output directory despite comments claiming separate directories. Schema cache keys use case ID alone, so regenerated cases or changed prompts/models can reuse stale schemas. Use separate run IDs and content/config hashes.
- The DEO rows are hard-coded numbers followed by an assertion of those same numbers; they are a declaration, not an independent audit. Record a reproducible counting policy and separate model-specific physics from benchmark/evaluation engineering.
- The notebook does not implement a controlled OOD cause-diagnosis metric, no-regularizer experiment, or alternate structured-encoder experiment. These remain required work.
- The prompt/schema definitions match the archive exactly. Model identity remains configured as `gpt-5`; preserve actual provider metadata in future runs.

## Reuse and implementation sequence

**Reuse with ordinary modularization:** approved prompt strings and JSON response schemas; provider adapter structure; frozen text-embedding interface; latent ODE integration scaffold; train-only scaling concept; basic split/result export patterns; explicit source state definitions.

**Replace or correct:** whole-trajectory/EMA training objective; text-discarding schema features; batched decoder payload; provenance-as-PCVR; value-reconstruction energy; baseline driver; invalid/poorly labeled oracle behavior; cache identity; evaluation boundaries and measurement accounting.

**Exclude from the active method:** `phase1_adapt`, test-time anchor/radius settings, `phase2_repair_openai` and its K2 loop, K1/K2 sweeps, and claims of trajectory correction through energy descent. The supplied repair prompt can remain archived without being called during inference.

Implementation planning can now proceed in this order:

1. Freeze the current decision table and typed data/observable contracts.
2. Preserve prompts/schemas and create provider-independent adapters with complete run attribution.
3. Validate one physical generator, its time grid, and independently defined evaluation checks; establish ID/OOD splits.
4. Implement a semantics-preserving structured encoder, hybrid projection, ODE, and physical readout.
5. Implement terminal MSE plus question-alignment regularization, validation selection, and complete checkpoints.
6. Implement fixed reference/structural scoring and evidence-supported OOD diagnosis without optimization or schema rewriting.
7. Connect compact, named physical predictions to the prompted answer generator and bounded fallback.
8. Train genuine baselines and run the regularizer, encoder, energy-assessment, and fallback ablations.
9. Record physical/semantic/structural metrics separately, profile latency/calls/tokens, expand domains, and populate paper tables only from these experiments.

Reference retrieval, semantic-distance choices, and threshold calibration are explicit implementation-plan defaults to test; they do not require treating the notebook as the scientific authority or reopening the professor’s settled decisions.

## Retained audit of the supplied demo artifacts

The following preserves the prompt baseline and verified artifact-level results. Where the original ZIP lacked source, the source findings above now supply the explanation.

## Adopted prompt and schema baseline

The four strings in `prompts.json` are the prompt baseline. Their individual SHA-256 hashes agree with `all_results.json`. The extraction prompt requires literal, scenario-supported facts with evidence; the repair prompt disallows relaxing bounds merely to fit a rollout; the judge evaluates scenario/schema semantics; the decoder generates explanation and structured output without claiming ground-truth access.

All 20 cached extractions share these root keys:

| Key | Observed contents |
| --- | --- |
| `observations` | Records with free-form `name`, numeric `value`, optional `unit`, `relation`, and exact `evidence`. |
| `events` | Records with `description`, optional `time`, and exact `evidence`. |
| `relations` | List of strings. |
| `symmetries_or_invariances` | List of strings. |
| `unknowns` | List of strings. |

All 32 structured answers share:

| Key | Observed contents |
| --- | --- |
| `final_state` | Predicted terminal physical-state array; eight numbers in this demo. |
| `trajectory_summary` | Text summarizing the predicted rollout. |
| `structural_interpretation` | Text interpreting the scenario and structure. |
| `fallback_used` | Boolean. |

These are two related contracts, not one JSON document whose original fields are all overwritten. Preserve the initial extracted schema, final schema, predicted state, and generated explanation as separate recorded objects. Initialize output slots as missing when needed; do not encode unknown predictions as physical zeros.

Adopt the archive's actual envelope rather than adding the earlier brainstormed `domain`, `objects`, or `formulas` fields as mandatory requirements. The newly supplied notebook provides `EXTRACT_SCHEMA`, `JUDGE_SCHEMA`, and `ANSWER_SCHEMA`, together with the exact provider request wrapper. These definitions are now available as the baseline contracts. `ANSWER_SCHEMA` wraps `plain_text_answer` and `structured_answer` in one response.

The repair prompt is retained as a supplied artifact. Test-time schema repair is explicitly excluded by the professor’s confirmation. Any bounded extraction repair during training/data preparation must have a separately defined scope; it is not permission to alter a test schema after inspecting predictions.

### Exact supplied prompts

**EXTRACTION_PROMPT**

```text
You are a domain-agnostic structural extractor for continuous physical reasoning.
Read the scenario literally. Use no domain-specific template. Extract only scenario-supported information.
Return observations (free-form name, numeric value, optional unit, relation/operator, exact evidence substring),
events/structural changes (description, optional explicit time, exact evidence), relations,
symmetries_or_invariances, and unknowns. Never invent a number and never relax a bound.
```

**REPAIR_PROMPT**

```text
Repair the current structural JSON interpretation using ONLY the original scenario.
Make the smallest topology/structure correction that explains the listed contradictions.
Every changed factual/numerical field must quote an exact evidence substring from the original scenario.
Never relax a numerical bound merely to make a model rollout valid. If unsupported, use unknown.
```

**JUDGE_PROMPT**

```text
Score semantic consistency between the scenario and schema from 0 (fully consistent)
to 1 (strong contradiction). Judge structure/meaning only, not trajectory accuracy.
```

**DECODE_PROMPT**

```text
Given a scenario, predicted terminal state, final schema, and fallback flag,
write a concise physical explanation and a structured answer. Never claim access to ground truth.
```

## What the demo actually contains

The archive has configuration, prompt strings, schema cache, checkpoint, scenario/split hashes, predictions and ground truth, explanations, metrics, refinement/repair logs, and summary CSVs. The ZIP itself has no Python source or notebook. The generating notebook has now been supplied separately and reviewed; the simulator definitions and training/evaluation code are available.

The manifest has **20 distinct cases**: 9 training (3 per domain), 3 validation (1 per domain), and 8 evaluation cases. Evaluation covers 3 IID, 2 parameter-OOD, and 3 topology-OOD cases. Fluid parameter OOD is absent.

There are **32 evaluation records**: the same 8 cases under Standard Neural ODE, Phi-JEPA without EBM, Phi-JEPA without fallback, and full Phi-JEPA. One seed, 11, is represented; configuration specifies two epochs. The larger per-domain counts in `config.json` do not describe the 20-case manifest actually supplied. This is consistent with its `smoke20` output-directory name.

The configuration records `openai_model: "gpt-5"`. It does not establish the user's reported GPT-5.5-Instant identity. That may describe the chat model used to help build the demo rather than the API model used in it. Preserve the configured name and obtain actual response/model metadata before assigning a different experimental model label.

### Verified positive findings

- Prompt hashes match the supplied prompt strings.
- JSON and CSV exports contain 32 records; the embedded Q&A copy matches the separate JSON file.
- Every evaluated initial observation/event evidence substring occurs literally in its scenario text. This checks evidence location, not completeness or correctness of interpretation.
- All 32 structured `final_state` arrays agree with the saved predicted terminal states to within 1e-6; no larger discrepancy was found. Fallback booleans also agree.
- Reported RMSE reconstructs as RMSE across all 126 time samples and all 8 state coordinates, with maximum discrepancy below 1e-6.
- Reported NCS reconstructs as cosine similarity of flattened trajectories, with discrepancy below 2e-7.

These checks support internal artifact consistency. They do not validate the simulator, training objective, physics verifier, or semantic explanations.

### Main experimental findings

| Variant | Cases | Fallback | Median logged latency | Median answer-generation latency |
| --- | ---: | ---: | ---: | ---: |
| Standard Neural ODE | 8 | 0/8 | 25.173 s | 25.097 s |
| Phi-JEPA without EBM | 8 | 8/8 | 25.612 s | 25.393 s |
| Phi-JEPA without fallback | 8 | 0/8 | 59.530 s | 24.999 s |
| Full Phi-JEPA | 8 | 8/8 | 54.395 s | 21.493 s |

For every evaluated case, the full model's saved trajectory is exactly equal to both the no-EBM trajectory and the Standard Neural ODE trajectory. Thus the archive demonstrates no final trajectory improvement from the full method in this run. All full-model cases used fallback, including IID cases.

The full records' final energy values are all above the configured 0.05 threshold. Source now confirms that this energy threshold triggers fallback; probe disagreement is not the final fallback trigger. It is not evidence that the method can never work: this is a tiny, briefly trained development run.

Each method/domain/split summary cell has n=1. Blank standard deviations and confidence bounds identical to the mean do not establish uncertainty. No conventional LLM-only or PIN-ODE results, no semantic-regularizer ablation, and no encoder comparison are supplied.

### Latency implication

For the Standard Neural ODE rows, subtracting recorded answer-generation time from total latency leaves approximately 0.074–0.077 seconds. This residual is not a separately instrumented solver benchmark, but it strongly suggests that LLM output generation dominates those recorded end-to-end rows.

The K1/K2 sweep likewise reports approximately 0.3–0.9 seconds with no logged LLM calls and approximately 29–66 seconds in the configurations with one call. These runs are not a complete uncached application timing: extraction is recorded separately and cached data are available. Do not combine them as if every row includes identical work. Prioritize stage-level measurements, payload sizes, and call policy before assuming multi-GPU ODE inference is needed.

