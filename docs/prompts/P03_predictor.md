# Codex prompt: P03 — Differentiable predictor and checkpoints

Copy the text below into the coding session, or ask Codex to read this file after importing the package.

---

You are implementing Phi-JEPA in the user's repository. Read the applicable root/nested AGENTS.md, docs/implementation/README.md and PROGRESS.md, then these package documents: [docs/02_architecture.md](../docs/02_architecture.md); [docs/03_data_evaluation.md](../docs/03_data_evaluation.md); [docs/06_phases.md](../docs/06_phases.md); [docs/08_defaults_decisions.md](../docs/08_defaults_decisions.md). Read the active phase in the phase specification and the last completed phase report. File paths here assume this package was installed under docs/implementation/; preserve equivalent paths if the user placed it elsewhere.

Implement only P03 using accepted data/provider interfaces. Add the structured encoder, linear fusion, latent vector field, differentiable RK4, linear physical and semantic heads, masked terminal physical MSE and semantic reconstruction objective. Fit normalization on training data only. Train an independent text-only latent ODE for fallback/no-schema comparison; do not reuse the full checkpoint with inputs zeroed.

Provide training, validation selection, complete checkpoint saving/resuming and fresh-process inference. Begin with a tiny CPU experiment and explicit fixture embeddings for mechanics; real frozen embeddings are a separate labeled condition. Keep the initial smoke bounded to at most 200 optimizer steps per tiny model and small batches, then report rather than silently launching a full run. Do not add intermediate-target, EMA or EBM losses.

Verify intended gradients, frozen components, terminal-only supervision, nonfinite failure handling, RK4 step refinement, tiny-set fitting trend and checkpoint round trip. A numerical solver check should use an analytic vector field, independently of the learned model's accuracy. Record seeds/configuration and distinguish fitting/plumbing success from generalization.

If Torch is unavailable, diagnose/install an appropriate CPU development profile within session permissions; continue independent code and mark execution pending if the environment remains blocked. The user's workstation CUDA result is not required for CPU implementation. Write docs/reviews/P03_completion.md and update progress. Stop at the phase boundary.

For any blocker, use [BLOCKER_REPORT](BLOCKER_REPORT.md), diagnose it with bounded reversible steps, and continue independent authorized work. Do not reopen settled architecture or silently change the method. The final report must state actual commands/results, source/branch state, artifacts, deviations and pending gates per [workflow](../docs/07_workflow.md).
