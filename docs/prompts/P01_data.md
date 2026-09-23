# Codex prompt: P01 — Verified data and evaluator

Copy the text below into the coding session, or ask Codex to read this file after importing the package.

---

You are implementing Phi-JEPA in the user's repository. Read the applicable root/nested AGENTS.md, docs/implementation/README.md and PROGRESS.md, then these package documents: [docs/01_context.md](../docs/01_context.md); [docs/02_architecture.md](../docs/02_architecture.md); [docs/03_data_evaluation.md](../docs/03_data_evaluation.md); [docs/06_phases.md](../docs/06_phases.md); [docs/08_defaults_decisions.md](../docs/08_defaults_decisions.md). Read the active phase in the phase specification and the last completed phase report. File paths here assume this package was installed under docs/implementation/; preserve equivalent paths if the user placed it elsewhere.

Implement only P01 using the accepted P00 interfaces. Build the proposed passive-stopping benchmark with named x/v targets, correct sample timestamps, analytic and independent numerical oracle checks, text generation, train-only normalization, family-level partitions, parameter/combination/event-OOD manifests and a strict label-free inference conversion.

Implement a prediction-file evaluator with per-observable endpoint errors, explicit failure/coverage handling, independent physical predicates and separate provenance metrics. Export a tiny fixture dataset plus source registry. Do not use the broken demo car-force behavior or describe an event as a topology change. Keep all authored formulas outside the Phi-JEPA predictor namespace.

Check zero initial speed, mu=0, stop before/at/after horizon, scheduled changes, negative positions, units/time origin, paired-family leakage and unavailable PCVR. Deliberately wrong predictions must fail checks. Verify no test-label information reaches ScenarioInput. Record which benchmark defaults were used and which strata remain unsupported. This phase needs no GPU or paid LLM calls.

Write docs/reviews/P01_completion.md and update progress. Stop after this data-to-evaluation slice; do not train models or claim oracle-fixture accuracy as model performance.

For any blocker, use [BLOCKER_REPORT](BLOCKER_REPORT.md), diagnose it with bounded reversible steps, and continue independent authorized work. Do not reopen settled architecture or silently change the method. The final report must state actual commands/results, source/branch state, artifacts, deviations and pending gates per [workflow](../docs/07_workflow.md).
