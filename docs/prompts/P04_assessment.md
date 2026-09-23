# Codex prompt: P04 — Fixed assessment and bounded inference

Copy the text below into the coding session, or ask Codex to read this file after importing the package.

---

You are implementing Phi-JEPA in the user's repository. Read the applicable root/nested AGENTS.md, docs/README.md and docs/PROGRESS.md, then these package documents: [docs/02_architecture.md](../docs/02_architecture.md); [docs/04_assessment_fallback.md](../docs/04_assessment_fallback.md); [docs/06_phases.md](../docs/06_phases.md); [docs/08_defaults_decisions.md](../docs/08_defaults_decisions.md). Read the active phase in the phase specification and the last completed phase report. File paths here assume this package was installed under docs/; preserve equivalent paths if the user placed it elsewhere.

Implement only P04's explicitly labeled development_r1_v1 path: immutable training-reference bank, k=1 retrieval, normalized-cosine latent score, generic supported contract severity, exact V1 scenario/schema judge interface, separate ID calibration, missing-component handling and the bounded fallback/output policy.

Connect the independent text-only fallback checkpoint for technical failures. Keep high-score numerical substitution disabled by default pending validation evidence. Preserve original and returned predictions, all reason codes, reference IDs, score/profile/calibration provenance and call/solve costs. No trained energy model, inference optimizer, Langevin update, schema topology repair or hidden target encoder.

Implement typed retrieved-schema judge and cause-diagnosis interfaces plus fixtures; prepare separately versioned draft prompts/examples for planner review. Do not activate these new tasks for live experiments or present V1 as already doing them. State the R1 target-latent ambiguity and V1 scope in the report; bounded development implementation can proceed while owner decisions are pending.

Check no label leakage, bank/checkpoint invalidation, partial score semantics, zero coverage, calibration isolation, no inference gradients/updates, fallback caps and numeric answer consistency. Show one offline end-to-end run including a deliberate failure. Record which live semantic/diagnosis validations remain pending. Write docs/reviews/P04_completion.md and stop.

For any blocker, use [BLOCKER_REPORT](BLOCKER_REPORT.md), diagnose it with bounded reversible steps, and continue independent authorized work. Do not reopen settled architecture or silently change the method. The final report must state actual commands/results, source/branch state, artifacts, deviations and pending gates per [workflow](../docs/07_workflow.md).
