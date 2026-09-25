> **Active supersession — 2026-09-24:** Model work follows [training contract 2.0.0-candidate.1](../../MODEL_TRAINING_CONTRACT.md) and the user's revision-3 Stage 1/P02a request. Adjacent recorded-state training uses frozen E(Q,C), trainable P of width d, the same undetached p on both sides, and full predicted 2d-vector feedback. Conflicting terminal-only, tree/readout/semantic-head, E(Q,C,A), upstream-baseline substitution and truth-forbidden-in-training instructions below are historical. Custom Coconut-inspired/CODI-inspired variants are intentional. Future phases require separate authorization. Frozen dataset/export contracts remain unchanged.

# Codex prompt: P05 — Independent conventional baselines

Copy the text below into the coding session, or ask Codex to read this file after importing the package.

---

You are implementing Phi-JEPA in the user's repository. Read the applicable root/nested AGENTS.md, docs/README.md and docs/PROGRESS.md, then these package documents: [docs/03_data_evaluation.md](../docs/03_data_evaluation.md); [docs/05_baselines.md](../docs/05_baselines.md); [docs/06_phases.md](../docs/06_phases.md); [docs/08_defaults_decisions.md](../docs/08_defaults_decisions.md). Read the active phase in the phase specification and the last completed phase report. File paths here assume this package was installed under docs/; preserve equivalent paths if the user placed it elsewhere.

Implement only P05. Add independently trained numerical NODE and legitimate physics-informed NODE for the first domain; expose the separately trained TEXT-NODE and PHI through the same runner/evaluator. The PIN method must use reviewed physical residuals, not a generic smoothness penalty. Keep its formulas outside the primary predictor. Document extra supervision and machine-readable input advantages.

Add direct-LLM and explicit CoT interfaces, and a real bounded action/tool loop for any ReAct condition supported. Missing live credentials/model budget means live results pending, not fabricated fixture wins. Implement an ablation registry distinguishing retrained variants from inference switches, with separate checkpoint identities where required.

Verify the no-energy condition does not execute scorers or energy-triggered fallback; no-fallback exposes failures; every method faces the same physical audit. Run a tiny CPU comparison with complete manifests and failures included. Preserve numerator/denominator and coverage semantics. Do not perform a broad model sweep.

Write docs/reviews/P05_completion.md with the exact independent training runs/checkpoints and runnable comparison command. Stop after this slice.

For any blocker, use [BLOCKER_REPORT](BLOCKER_REPORT.md), diagnose it with bounded reversible steps, and continue independent authorized work. Do not reopen settled architecture or silently change the method. The final report must state actual commands/results, source/branch state, artifacts, deviations and pending gates per [workflow](../docs/07_workflow.md).
