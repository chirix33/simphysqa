> **Active supersession — 2026-09-24:** Model work follows [training contract 2.0.0-candidate.1](../../MODEL_TRAINING_CONTRACT.md) and the user's revision-3 Stage 1/P02a request. Adjacent recorded-state training uses frozen E(Q,C), trainable P of width d, the same undetached p on both sides, and full predicted 2d-vector feedback. Conflicting terminal-only, tree/readout/semantic-head, E(Q,C,A), upstream-baseline substitution and truth-forbidden-in-training instructions below are historical. Custom Coconut-inspired/CODI-inspired variants are intentional. Future phases require separate authorization. Frozen dataset/export contracts remain unchanged.

# Phases and acceptance gates

[Start](../README.md) · [Progress tracker](../PROGRESS.md) · [Workflow](07_workflow.md)

Each phase delivers an executable slice with a bounded proof of behavior. Proposed CLI verbs below are acceptance interfaces to implement, not claims that commands already exist. P00 chooses the exact CLI syntax and updates later prompts/specs if an equivalent is used. No interface redesign solely to match a preferred filename.

## P00 — repository reconciliation and runnable skeleton

Read current root/nested AGENTS instructions, git status, branch and relevant source. Preserve uncommitted changes and legacy assets. Import this package, inspect differences against current repository state, and produce `docs/reviews/P00_repo_audit.md` with exact head, reusable modules, legacy isolation and a conflict table. Audit the professor notebook's actual presence/path without assuming the old audit's commit is head.

Deliver a package/CLI, validated configuration, explicit offline/live modes and a run directory with manifest. One deterministic fixture input must pass through typed loading and produce a visibly fixture-only result JSON. Include target-free inference type and artifact writer from the start. Define light CPU development dependencies and optional extras rather than installing every baseline to run a schema test.

**Gate:** clean import/CLI help; configuration rejects unknown/invalid values; fixture run persists deterministic provenance; no network calls in offline mode; relevant prior tests preserved or migration documented. Report actual commands and output. No model training or paid calls. [Prompt](../prompts/P00_bootstrap.md).

## P01 — data-to-evaluation slice

Implement the passive-stopping generator and independent numerical/analytic validation, observable metadata, family-level splits, input/label separation, canonical targets and evaluator. A prediction-file input should generate metrics without running a model. Deliberately wrong outputs must trigger violations/errors; perfect oracle fixtures establish evaluator correctness only.

**Gate:** zero-speed/no-friction/stop/event/time-origin cases; correct physical units; disjoint family/derivative splits; no hidden fields in inference; PCVR with coverage and correct unavailable state; invalid outputs counted; deterministic manifests and normalization train-only. Export tiny fixture dataset and dataset-source registry. [Prompt](../prompts/P01_data.md).

## P02 — extraction-to-features-to-answer-payload slice

Version exact supplied prompts/schemas; implement frozen embedding and structured-output provider interfaces, offline replay, error typing, budgets/caches, generic schema graph and named compact answer payload. Live adapter code can be implemented from the installed SDK contract while its integration test is marked unavailable without credentials. Add a small supervised extraction audit fixture with evidence and unknown fields.

**Gate:** schema validation, negative/unknown data, content-sensitive cache, no secret logging, graph features distinguish names/units/operators at equal numbers, `[B,T,D]` regression, final-state output binding, archived repair prompt unreachable. Real prompt validity is not established by fixture playback. [Prompt](../prompts/P02_interfaces.md).

## P03 — train-to-checkpoint-to-prediction slice

Implement hybrid projection, generic structured encoder, differentiable RK4, linear physical readout, semantic head, terminal-only objective, independent text-only fallback model, validation selection and full checkpoints. Run a tiny CPU experiment using fixed deterministic embeddings for mechanics; separately support/download a real frozen encoder when feasible, with its revision recorded. Label all fixture-encoder results as such.

**Gate:** intended gradient flow and frozen parameters; no dependence of loss on intermediate target rows; solver convergence check; tiny-set fitting without NaNs; fresh-process checkpoint prediction; preserved shapes/units/scalers; separate full/fallback checkpoint identity. Compare beta=0 plumbing, not claim statistical benefit. [Prompt](../prompts/P03_predictor.md).

## P04 — prediction-to-assessment-to-answer slice

Implement R1 development reference bank, V1 intrinsic semantic judge integration, generic contract score, separate calibration partition, missing-component semantics, output generation, technical fallbacks and a disabled-by-default high-score substitution policy. Add typed retrieved-schema judge/diagnosis interfaces and fixtures, preserving their prompt-review status. End-to-end offline run must preserve original/final predictions and complete costs.

**Gate:** reference leakage/cross-checkpoint invalidation; calibration isolation; missing coverage not zero; immutable scenario/schema; no inference optimizer/repair; fallback caps; answer disagreement detection; lossless provenance. Include a report explicitly stating R1/V1 scope and which full-paper claims remain unvalidated. Prompt approval/live evidence gates may remain pending while this development slice is complete. [Prompt](../prompts/P04_assessment.md).

## P05 — conventional comparison slice

Train independent NUM-NODE and valid PIN-NODE on the first domain; expose the separately trained TEXT-NODE; add direct/CoT/ReAct adapter interfaces with actual method distinctions. Implement ablation registry so runtime switches and retrained methods cannot be confused. Run a tiny offline comparison through the common evaluator.

**Gate:** independent checkpoints and supervision records; PIN residual correctness; no physical-law imports in PHI; equal evaluation predicates; no-energy skips its scorers; no-fallback exposes failures; summaries include failed/missing methods. Credentials are needed only for live LLM results. [Prompt](../prompts/P05_baselines.md).

## P06 — continuous-reasoning baseline slice

Create pinned external-source manifests, patch ledger, isolated environment recipes, local physics loaders, solution-step adapters, general numeric serialization/parsers, checkpoint loaders and launch/evaluation wrappers for CoConuT and CODI. Retain native-reference versus physics-adapted profiles. Implement bounded model smoke/profile commands; no unbounded native dataset evaluation by accident.

**CPU gate:** format/negative/exponent/multi-output examples; identical family splits; token-length/filter accounting; config schedules; result import and missing-checkpoint failure behavior. **GPU gate:** real checkpoint loading/key audit, finite forward/backward, CoConuT stage transition and save/reload, CODI BF16 execution, representative longest-stage memory profile. If GPU pending, report `implemented_pending_validation`; P00–P05 need not stop. [Prompt](../prompts/P06_latent_baselines.md).

## P07 — workstation and one-domain pilot

Consume the user's runtime result rather than assuming it passed. Install/reconcile environments on the actual workstation under the coding session's access, perform bounded real-model smoke checks and 20–50-step profiles, choose safe batches, and execute a predeclared one-domain pilot only within a stated compute/API budget. Finish any P06 GPU gates. Before live claims, resolve R1 target-reference interpretation and judge/diagnosis prompt scope with the planner/user. A pilot may remain development-labeled if those are unresolved.

**Gate:** exact environment/model/data revisions; budgets and seeds; runnable selected checkpoints; representative ID/OOD cases; meaningful physical/semantic/fallback metrics; all costs; reproducible aggregate from raw records; actual unsuccessful methods retained. Store a pilot report with discrepancies and recommended frozen main matrix. Success means trustworthy evidence, not a desired accuracy value. [Prompt](../prompts/P07_pilot.md).

## P08 — multidomain study and report

Validate each new oracle and observable head independently, implement genuinely justified OOD strata, and run only the approved matrix. Preserve the mechanical-proxy label if used. Include all mandatory baselines or state concrete missing evidence. Export tables/figures from immutable raw outputs, with method/profile/run IDs, uncertainty and compute/DEO accounting.

**Gate:** all main claims trace to measured runs; no surrogate results for missing systems; shared evaluator, family splits and cost policy; seeded repetitions; ablation completeness; no hidden repaired constraints or trajectory-loss additions; reproducer and limitations written. Main-study completion requires actual experiments, not just a scheduler. [Prompt](../prompts/P08_study.md).

## Concurrent work without premature completion

While a GPU gate is pending, Codex may finish authorized CPU substeps and tests, prepare manifests and reduce genuine environment uncertainty. It should report blocked evidence precisely. A later prompt may authorize an independent phase without marking the blocked phase complete. Avoid two coding agents editing the same modules concurrently unless the user explicitly coordinates branches and integration.

## Completion labels

`not_started`, `in_progress`, `implemented_pending_validation`, `blocked`, `complete`. `complete` requires the phase's declared applicable gates and honest exceptions. A known missing scientific decision can limit claims even if its software interface is complete. Phase reports must distinguish code correctness, environment compatibility and scientific validation.
