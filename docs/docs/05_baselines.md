> **Active supersession — 2026-09-24:** Model work follows [training contract 2.0.0-candidate.1](../../MODEL_TRAINING_CONTRACT.md) and the user's revision-3 Stage 1/P02a request. Adjacent recorded-state training uses frozen E(Q,C), trainable P of width d, the same undetached p on both sides, and full predicted 2d-vector feedback. Conflicting terminal-only, tree/readout/semantic-head, E(Q,C,A), upstream-baseline substitution and truth-forbidden-in-training instructions below are historical. Custom Coconut-inspired/CODI-inspired variants are intentional. Future phases require separate authorization. Frozen dataset/export contracts remain unchanged.

# Baselines, ablations and experiment design

[Start](../README.md) · [Detailed official baseline runbook](../references/baseline_runbook.md) · [Evaluation](03_data_evaluation.md)

## Comparison registry

| ID | Method | Training/inference distinction |
| --- | --- | --- |
| PHI | Full structured latent ODE | Agreed terminal physical + semantic objective; fixed assessment profile and recorded fallback policy |
| TEXT-NODE | Independently trained text-only latent ODE | Same frozen question encoder, comparable latent capacity/readout; also deployable fallback |
| NUM-NODE | Standard numerical neural ODE | Learned physical-state vector field, permitted numeric initial conditions/context; independent checkpoint |
| PIN-NODE | Physics-informed numerical ODE | NUM-NODE plus reviewed domain residual/constraint loss; authored physics and compute disclosed |
| LLM-DIRECT | Representative direct LLMs | Same observable question, no hidden labels; model/reasoning settings logged |
| LLM-COT | Explicit worked-answer prompt condition | Prompt/decoding budget logged; do not assume hidden reasoning tokens are observable |
| LLM-REACT | Optional tool-using condition | Explicit action loop and shared allowed tool budget; plain CoT relabeling is invalid |
| COCONUT | Official continuous-thought method | CoT training followed by staged latent curriculum, physics adapters |
| CODI | Official self-distillation method | Verified solution traces and fixed latent steps, physics adapters |

Primary architecture comparison is PHI against TEXT-NODE and language-based methods using the same question information. NUM-NODE/PIN-NODE use the same disclosed numerical facts that are serialized in questions, but receive them in machine-readable form; label this input-format advantage. No hidden future controls, OOD event labels or simulator-only parameters. Supply event schedules only when they are stated in the question for every method. Keep such schedules out of “unobserved event” cases.

Ablation definitions must distinguish **retraining** (schema encoder removed/replaced, beta=0, capacity changes) from **runtime switches** (assessment/fallback disabled on the same selected full checkpoint). Both are useful, but their interpretation differs. TEXT-NODE is independently trained; zeroing one full-model input is an additional intervention, not that baseline.

## Required ablations

- No semantic regularizer: retrain with beta=0, comparable training/tuning budget.
- Structural encoder comparison: generic tree/graph versus declared pooled/flat encoder, same available content; retain names/units/relations in both.
- No schema: independently trained text-only model, not schema erasure only at test time.
- No energy assessment: no reference/judge energy computation and no score-triggered fallback; label technical fallback policy separately.
- No fallback: expose appropriate failures and original predictions, with no silent retry through another model.
- Latent-only versus JSON-only versus hybrid score: only after each component/profile and calibration is defined. Component-unavailable cases are not silently omitted.

No exhaustive solver-order or provider × domain × prompting × encoder × seed product is required. Prioritize correctness and the small declared comparison matrix; expand only for a concrete scientific question.

## CoConuT and CODI integration

Use official commits recorded in the runbook and preserve licenses. Initial matched backbone GPT-2, six final latent steps. CoConuT uses full tuning; CODI uses its author LoRA settings. Equal latent count does not imply equal parameter count, compute or optimization. Report training work including CoConuT's CoT precursor.

Do not treat closed API models as drop-in latent backbones. Released CODI arithmetic checkpoints provide native verification and optional labeled transfer results, not trained physics performance. Native benchmark checks and physics-adapted experiments have separate manifests.

Adapters consume the same dataset contract, then serialize verified solution steps and canonical target components. Replace arithmetic parsers and any digit-first filtering that loses negative answers; preserve signs, exponent notation and multiple values. Token lengths, sequence filters and dropped-example counts must be visible. Do not invent a local-data CLI flag before implementing it.

Pinned CoConuT configuration has `resume=3,num_epochs=25`, yielding 22 latent loop iterations; preserve or deliberately document the schedule instead of copying a misleading “25 latent epochs” label. CODI's known attention-mask flag and any correction are separately configured/reported. Add validation selection for physics runs without silently changing the upstream-reference profile.

## Numerical baselines

For the stopping pilot, NUM-NODE learns a vector field over physical x/v and allowed context, with terminal-only supervised rollout loss as the matched default. If derivative-supervised or trajectory-supervised variants are run, label their extra supervision. PIN-NODE adds an explicitly reviewed stopping-dynamics residual at valid collocation points; handle event discontinuities and stopped states correctly. Register constraint functions only in the PIN/evaluator namespace. It is not sufficient to penalize adjacent-state differences and call it physics-informed.

All learnable baselines get train/validation selection and independent checkpoints. Their optimization budgets may differ appropriately but are declared. Count input preparation and structured parsing advantages in the result description. Distinguish a cheap analytic oracle for correctness from a learned comparison model.

## Experiment progression

P07 pilot: one domain, ID + parameter-OOD + event/regime-OOD, PHI/TEXT-NODE/NUM-NODE/PIN-NODE/direct LLM plus available latent baselines, one development seed. Purpose: validate behavior, cost, failure reporting and manageable runtime. No paper superiority claim from a tiny pilot.

P08 main: freeze model IDs, prompting/tool budgets, data/splits, assessment profile, target/metric definitions, tuned settings and seeds before sealed tests. Use one representative high-, moderate- and non-reasoning model (categorization must be documented for the exact model/configuration). Open/proprietary status is a reported property, not necessarily another factorial dimension. Proposed three training seeds 11/22/33; justify larger/smaller count with the budget and uncertainty goals.

Price/cost tables require actual recorded calls and a dated pricing source, or report raw tokens/GPU time without invented currency conversions. Include cold versus cached extraction separately. Published speedups must use matched hardware, output tasks and measured timing, not the demo's malformed answer payload.

## What waits for the workstation

Dataset adapters, serialization, CLI/configuration, parser tests, result import and tiny mock runner contracts can be implemented now. Actual CUDA model execution, training-memory profiles and completed CoConuT/CODI experiment claims wait for GPU runtime validation. A runnable launcher that has never loaded a real checkpoint is `implemented_pending_validation`.
