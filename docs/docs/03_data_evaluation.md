# Data, physical oracles and evaluation

[Start](../README.md) · [Architecture](02_architecture.md) · [Baselines](05_baselines.md)

## First vertical slice: one-dimensional passive stopping

Use a simple, independently checkable benchmark before trusting the demo's three generators. This is a proposed engineering starting domain, not a claim that the complete study is a one-dimensional problem.

Scenario states initial forward speed, position, friction coefficient, gravity, query horizon, and any explicitly observable scheduled change. Predict terminal position and speed in SI units. Benchmark-only oracle for constant friction: `a=mu*g`, `t_stop=v0/a`; velocity is `max(v0-a*t,0)` and position is `x0+v0*t-0.5*a*t*t` before stopping, then `x0+v0*v0/(2*a)` afterward. Handle mu=0 separately and reject negative passive-friction parameters. For changes, integrate piecewise with the same stopping convention. These formulas belong only to the generator, independent evaluator and disclosed physics-informed baseline.

Validate an independent numerical implementation against closed-form cases and time-step refinement, including zero initial speed, no friction, stop before/at/after T, and events around stopping. A positive braking-force sign, reversed velocity after a passive stop, or a post-step sample labeled t=0 fails acceptance. Record the true initial sample and exact sample times. Avoid a dataset where every target speed is zero: vary horizons and retain stopped/moving strata.

Text generation serializes physically complete observed facts. Paraphrases must preserve every quantity, unit, event and question target. Do not claim hidden changes are identifiable from an identical initial question alone. Case IDs and family IDs must not encode target/OOD information available to the model.

## Candidate sources and expansion

| Candidate | Role and limits | First use |
| --- | --- | --- |
| Reviewed analytic stopping generator | Small, auditable oracle; authored benchmark physics is disclosed | P01 core correctness and pipeline development |
| [MuJoCo](https://mujoco.readthedocs.io/en/stable/overview.html) | Engine for articulated/contact systems; requires an actual model, parameters and generated dataset | P08 vehicle/arm cases after physical validation |
| [DeepMind Control Suite](https://github.com/google-deepmind/dm_control) | MuJoCo-based environments; not an existing question/solution corpus | Candidate for robotic dynamics and state trajectories |
| [PDEBench](https://github.com/pdebench/PDEBench) | Scientific PDE datasets; field/conditioning interfaces differ from a small vector head | Optional genuine fluid/PDE extension, not a relabeled pendulum |
| Professor's three-domain demo | Prompt/format examples and debugging artifacts; too small and flawed for final benchmark | Read-only reference, not training/evaluation authority |

The cited official projects were inspected for scope. Dataset/model licenses, versions, exact usable variables, download sizes and physical coverage must be recorded before adopting a subset. No claim is made that any source already supplies our natural-language questions, structured schemas or verified solution traces. Codex must create a compact dataset-source registry including suitability, required conversion, license and rejection reason where applicable.

Proposed expansion: corrected vehicle dynamics, articulated arm, and a clearly labeled mechanical slosh proxy. A fluid claim requires an actual fluid oracle. A graph-topology claim requires an actual body/joint/constraint-graph change and compatible observable layout; a friction change is not topology OOD. Three well-supported domains are preferable to a larger list of mislabeled tasks.

## Splits, quantities and scaling

Create deterministic family-level train, model-selection validation, calibration validation, and sealed tests before text paraphrasing or transformations. Every correlated derivative/paraphrase/time-query view of one base scenario stays together. Distinct random seeds are not a substitute for a leakage audit. Record content hashes and duplicate/near-duplicate families.

Suggested sizes: 32-case wiring fixture (24/4/4 train/validation/test; no statistical claims). First development dataset: 512 training families, 128 selection, 128 calibration, 256 ID test, and 256 for each implemented OOD stratum. These are proposed feasible starting counts, not a power analysis or promised final dataset size. Confirm stable validation learning before increasing counts; main-study counts and seeds are frozen in P07.

For stopping development, initial candidate ID ranges: v0 in [5,20] m/s, mu in [0.3,0.7], x0 in [-10,10] m, T in [0.5,5] s, g=9.81 m/s². Preserve those explicit ranges in configuration. Candidate parameter-OOD: mu in [0.05,0.15] or [0.85,1.0], with other quantities matched. Candidate combination-OOD: reserve high-speed/low-friction combinations while both marginal ranges remain in training. Candidate event-OOD: a specified friction change within the horizon; this is a regime shift. Tune generator ranges using training/development diagnostics only, then freeze before testing.

OOD sets must not merely use paraphrased wording; ID lexical changes are a separate robustness condition. Include controls for magnitude, horizon and answer distribution where possible. If a held-out quantity is absent from all available observations, label the case underdetermined and score appropriate uncertainty/failure rather than asserting a uniquely recoverable answer.

Normalization fits only training targets and is keyed by observable ID/unit/frame. Selection and calibration sets do not fit scalers. Keep raw-unit values for all reported per-variable errors. Heterogeneous domains must not share normalization just because their output arrays have the same width.

## CoT annotations for latent baselines

CoConuT and CODI need question, verified worked solution and terminal answer. Store solution steps separately from model-visible test inputs. Use concise explicit explanations, analytic/simulator-supported values and a canonical final serialization. For the stopping pilot, a disclosed annotation generator may use the benchmark formulas; keep it out of inference and charge its domain-specific authoring to annotation infrastructure. This is not autonomous training-data discovery.

For complex domains, generated explanations must be checked against simulator labels and audited for incorrect causal claims. Physics trajectories alone do not make a textual rationale valid. Preserve provenance and rejected annotations. Use the same training questions/labels and available verified explanations for both latent baselines; record any format conversion or dropped samples. No request for hidden proprietary chain-of-thought is necessary.

## Metrics: definitions and denominators

- **Primary:** per-observable terminal RMSE in physical units, and a declared macro-average of train-normalized terminal MSE/RMSE across variables. Include mean absolute error if useful. Missing/invalid predictions are failures, not zero error or silently dropped rows; report coverage and valid-only error together.
- **Trajectory:** error over a common declared physical time grid, only for methods that actually produce that grid. Terminal supervision alone does not guarantee accurate intermediate trajectories. Extra calls made to generate time slices are counted.
- **NCS:** `cos(y_hat_norm, y_gt_norm)` with a documented normalization and zero-vector policy. If reporting a [0,1] mapping, explicitly name it `(1+cos)/2`; do not silently mix formulas. Treat it as secondary to physical errors.
- **PCVR:** sum of violated applicable physical checks divided by number of evaluated applicable checks, with family-level macro aggregation additionally reported. Include check coverage, unknown/uncheckable count and severity. No checks means unavailable, not 0% violations. Use the same independent predicate set for every method.
- **Provenance/schema:** schema parse rate, supported facts, evidence spans, extraction completeness on audited samples, output completeness and numeric answer consistency. Do not equate provenance with PCVR.
- **Assessment:** AUROC/AUPRC where both classes exist; ID false-positive rate and per-OOD-type recall at a validation-calibrated threshold; explicitly state positive label. Compare against latent-only, structural-only and confidence-free baselines as available.
- **Diagnosis:** cause-label agreement plus evidence validity and unsupported-claim rate; permit abstention. For non-identifiable causes, score appropriate uncertainty. Judge agreement is a proxy; use blinded/manual adjudication of a defined sample before stronger claims.
- **Fallback:** trigger/reason counts, original-versus-final error and violations, correction/harm rate on paired cases, output coverage and terminal failures. Report additional inference work.
- **Cost:** wall time with CUDA synchronization for GPU sections, p50/p95, batch-one latency versus throughput, all model calls/tokens/retries, extraction versus solve versus assessment versus decode, cache policy, NFE, peak memory, training GPU-hours and parameter counts. API queue/network time remains part of end-to-end latency.
- **DEO:** inventory of hand-authored domain physics, residuals, bindings, benchmark and annotation work. Separate inference method from data/evaluation infrastructure; publish counting rules rather than asserting “0 lines” without inspection.

An LLM semantic comparison may supplement text-only cases but must not be labeled numerically equivalent to programmatic PCVR. The final answer LLM cannot correct a latent prediction and thereby replace the numeric score unnoticed.

## Statistical and artifact policy

Development uses seed 11; proposed main seeds 11/22/33 after budgets are established. Report training-seed variability and paired confidence intervals resampled by scenario family, not every correlated paraphrase as independent. Three seeds are a practical minimum proposal, not a guarantee of statistical power. Never pool structurally different OOD cases into one favorable mean without per-type results.

Keep test truth sealed from tuning commands. Once inspected for failure analysis, results are exploratory unless a fresh sealed set remains. Export raw predictions, provenance, manifests and deterministic aggregation code. Paper tables must link to actual run IDs and status. Unexecuted baselines get “not run,” not synthetic estimates or copied paper numbers.
