# Codex prompt: P01 — Verified data and evaluator

Updated after planner review of the supplied P00 completion report. Copy the text after the separator into the coding session. This authorizes P01 only.

---

Implement Phase P01 of Phi-JEPA: a verified passive-stopping dataset and a prediction-file evaluator. The planner accepted P00 for progression on the evidence in its completion report; this was a report review, not an independent source-diff audit.

## Read the current project

The handoff is installed directly under `docs/`, not `docs/implementation/`. Read applicable root/nested `AGENTS.md`, `docs/README.md`, `docs/PROGRESS.md`, `docs/reviews/P00_completion.md`, `docs/reviews/P00_repo_audit.md`, `docs/decisions/P00_bootstrap.md`, and specifications `docs/docs/01_context.md`, `02_architecture.md`, `03_data_evaluation.md`, `06_phases.md`, and `08_defaults_decisions.md`. Follow existing equivalent paths if the checkout changed. Do not create a duplicate handoff.

Inspect git status and the actual P00 package, tests and configuration. The reported branch is `codex/p00-bootstrap`, with base HEAD `8e1cd56feb8f9fb0ec8aee92b0d0365b32722066` and uncommitted P00 changes. Preserve that work. Record the actual starting state and isolate your P01 additions in the report. Continue from this working tree; do not reset, discard, silently stash, or start from a clean checkout that omits P00. A clean tree or a P00 commit is not a prerequisite. No push/merge is requested.

Reuse P00's strict input contracts, configuration, artifact writer, `phi-jepa` CLI and lightweight CPU setup. Inspect them where P01 depends on them and fix concrete integration defects if found; do not repeat the entire repository audit or redesign working interfaces. The user-reported RTX 5090 FP32/BF16 GPU check has passed. Codex's Windows CPU checks are separate evidence, and P01 does not need GPU access.

## Deliver one executable data-to-evaluation slice

1. **Benchmark oracle.** Implement the proposed one-dimensional passive-stopping benchmark with named position `x` and forward speed `v` in SI units. Inputs include `x0`, nonnegative `v0`, nonnegative friction coefficient, positive gravity, query horizon and explicitly stated scheduled friction changes. Reject nonfinite or ambiguous inputs. Friction cannot make a stopped object reverse or restart. Support zero horizon as a boundary case, or reject it explicitly and document that policy consistently.

   Implement the constant-friction closed-form oracle and piecewise analytic event handling. Validate them against a genuinely separate time-stepping numerical implementation and step refinement; merely calling the analytic function twice is not independent validation. Define event ordering and exact sample-time semantics. Emit the true initial sample at time zero; include the requested terminal time. Place all authored dynamics in a disclosed benchmark namespace. Primary predictor/inference modules must not import benchmark dynamics or evaluation truth.

2. **Dataset and contracts.** Produce label-free `ScenarioInput` records and separate terminal/trajectory truth records, carrying observable IDs, units and times. Generate deterministic, physically complete scenario text using templates; no LLM is needed. Keep solution annotations, gold outputs, split/OOD labels and hidden simulator metadata out of inference inputs. IDs must be opaque and must not embed a split/OOD label or target. Keep the P00 fixture command's round-trip-only meaning unchanged.

3. **Partitioning and OOD.** Split base families before paraphrases and correlated time-query variants. Support training, model-selection validation, calibration validation, ID test and distinct parameter-, combination- and event-OOD test manifests. Specify the candidate ID ranges from the data specification. Parameter-OOD covers low/high friction outside the ID interval; combination-OOD reserves an explicit joint region while its individual parameter ranges remain represented in training; event-OOD introduces a stated friction change. Reserve that joint region from every ID partition. Do not label event/parameter changes as topology changes.

   Export a small wiring fixture, not a main-study dataset. A suitable explicit allocation is 32 base families: 16 training, 4 selection, 4 calibration, 4 ID test and 4 OOD (one low-friction, one high-friction, one held-out-combination and one event case). This replaces the earlier illustrative 24/4/4 allocation for this fixture so calibration is separate. Record the choice in `docs/decisions/P01_data.md`. Ensure the fixture exercises moving and stopped outcomes and demonstrates the claimed marginal support for combination-OOD. These tiny counts support wiring checks only, not statistical OOD conclusions. Keep counts/ranges configurable for later runs; do not generate a large study now.

4. **Train-only normalization.** Fit per-observable scales exclusively from training terminal targets; persist training-family provenance and handle constant coordinates explicitly. Selection, calibration and test records cannot fit scalers. Changing only held-out targets must leave fitted normalization unchanged. Preserve physical-unit targets and predictions for reporting.

5. **Prediction-file evaluator.** Extend the existing CLI with clearly documented generate, validate and evaluate operations (equivalent syntax is acceptable). Evaluation must accept external numerical predictions without running a model. Validate sample identity, observable order/names, units, dimensions, finiteness and duplicates. Reject unknown/duplicate prediction IDs rather than silently matching by row order. Missing or invalid predictions count as failures with explicit denominators. Report per-observable endpoint errors and train-normalized aggregate error together with valid-prediction coverage; all-missing predictions produce unavailable errors, never zero error.

   Implement independent physical predicates applicable to this benchmark. Report PCVR, its numerator/denominator, eligible/evaluated/unsupported checks, coverage and failure counts. No checks means unavailable. Keep exact answer error distinct from physical-invariant compliance; a wrong answer can satisfy a weak physical bound. Keep provenance/schema checks distinct from PCVR. Test physically impossible predictions such as reversal, speed gain or displacement outside the reachable interval. Only evaluate trajectory metrics when actual compatible trajectories are supplied; never invent intermediate states from terminal predictions.

6. **Reproducible artifacts.** Preserve deterministic generation and P00 artifact integrity. Record generator/configuration/source hashes, seed, family partitions, observable layouts, time grids and scaler provenance. Add a compact dataset-source registry identifying the local analytic benchmark as implemented and external candidate datasets as not yet adopted. Do not invent a license or verified download status. Keep executable source assets and the professor's demo untouched as historical references.

## Required evidence and bounded verification

Use the existing CPU environment if it works; new dependencies must be necessary and recorded. No paid calls, model downloads, neural training or full experimental runs.

Targeted tests must cover:

- zero initial speed, zero friction, stop before/at/after the horizon, negative initial position, and input units/finiteness;
- events before/at/after a stop, friction changes to/from zero, and event-boundary sampling without reverse motion;
- analytic/numerical agreement within documented tolerances and numerical step refinement;
- deterministic family disjointness, correlated-variant containment, explicit OOD support, and label-free conversion;
- train-only scaling and invariance to changes in held-out truth;
- deliberate numerical errors, physical violations, missing/nonfinite/misaligned/duplicate predictions, partial coverage, and entirely unavailable metrics;
- generation-to-validation-to-evaluation through the CLI, plus the relevant P00 regression suite and offline network isolation.

A perfect oracle prediction file is permitted solely as `oracle_fixture` evaluator verification. Include a deliberately corrupted prediction file so the checks visibly detect errors. Neither output is Phi-JEPA performance. Validate oracle edge cases independently of test-split outcomes; do not inspect or tune on a later sealed study test set.

Write `docs/reviews/P01_completion.md`, record consequential choices in `docs/decisions/P01_data.md`, and update `docs/PROGRESS.md`. Include exact commands/results, branch/base and dirty-state provenance, modified interfaces, artifact paths/hashes, chosen ranges/split counts, oracle comparison tolerances/results, metrics denominators, and remaining gates. Report actual failures and deviations.

If blocked, follow `docs/prompts/BLOCKER_REPORT.md`, perform bounded reversible diagnosis, and continue independent authorized work. Do not reopen settled scientific decisions or invent target-latent/judge specifications. Stop after P01; do not begin P02 or train a predictor.
