# Codex prompt: P00 — Bootstrap and reconcile

Copy the text below into the coding session, or ask Codex to read this file after importing the package.

---

You are implementing Phi-JEPA in the user's repository. Read the applicable root/nested AGENTS.md, docs/README.md and docs/PROGRESS.md, then these package documents: [docs/01_context.md](../docs/01_context.md); [docs/02_architecture.md](../docs/02_architecture.md); [docs/06_phases.md](../docs/06_phases.md); [docs/07_workflow.md](../docs/07_workflow.md); [docs/10_environment.md](../docs/10_environment.md). Read the active phase in the phase specification and the last completed phase report. File paths here assume this package was installed under docs/; preserve equivalent paths if the user placed it elsewhere.

Inspect the current checkout, root/nested AGENTS.md, git status and branch/head. The private repository is chirix33/phi-jepa; do not assume the older audited commit is current. The package is already installed directly in docs/ and AGENTS.md is at repository root. Preserve existing applicable rules and user changes; do not duplicate the handoff.

Implement only P00: current repository/source inventory and conflict table; a small installable typed package; validated offline/live configuration; CLI help; label-free inference input type; immutable run manifest/artifact writer; and a deterministic fixture command producing a clearly fixture-only result. Adopt existing correct modules where appropriate and isolate legacy/domain-authored behavior. Do not begin neural training or silently turn the old numerical pipeline into the claimed new architecture.

Define the concrete CLI names that later phases will use. Keep dependencies light enough that contracts/fixture tests run without CUDA, model weights or API keys. Verify import/help, invalid configuration rejection, deterministic artifact provenance, input-label separation and no offline network calls. Preserve or explain changes to relevant existing tests. Record the notebook/source assets found and any difference from the supplied audit.

The user has now supplied a PASSED WSL GPU check: PyTorch 2.7.1+cu128, CUDA runtime 12.8, NVIDIA GeForce RTX 5090, capability (12, 0), BF16 supported, and FP32/BF16 forward/backward both PASS. This supersedes pending-GPU-check statements in the imported handoff. Update the environment/progress documentation accordingly, attributing the result to the user; do not claim you ran it or that model-specific baseline validation has passed. P00 remains CPU-capable and must not depend on workstation access.

The subsequent author rewrite does not change implementation authority: retain terminal projected physical MSE plus question alignment, fixed untrained energy assessment, and no inference-time latent optimization or schema repair. The draft's proposed reference-bank/judge details have not become new professor-approved decisions.

No paid calls or long jobs. Finish with docs/reviews/P00_completion.md and an updated progress tracker. Stop at the P00 boundary.

For any blocker, use [BLOCKER_REPORT](BLOCKER_REPORT.md), diagnose it with bounded reversible steps, and continue independent authorized work. Do not reopen settled architecture or silently change the method. The final report must state actual commands/results, source/branch state, artifacts, deviations and pending gates per [workflow](../docs/07_workflow.md).
