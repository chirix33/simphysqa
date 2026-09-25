> **Active supersession — 2026-09-24:** Model work follows [training contract 2.0.0-candidate.1](../../MODEL_TRAINING_CONTRACT.md) and the user's revision-3 Stage 1/P02a request. Adjacent recorded-state training uses frozen E(Q,C), trainable P of width d, the same undetached p on both sides, and full predicted 2d-vector feedback. Conflicting terminal-only, tree/readout/semantic-head, E(Q,C,A), upstream-baseline substitution and truth-forbidden-in-training instructions below are historical. Custom Coconut-inspired/CODI-inspired variants are intentional. Future phases require separate authorization. Frozen dataset/export contracts remain unchanged.

# Codex prompt: P06 — CoConuT and CODI integration

Copy the text below into the coding session, or ask Codex to read this file after importing the package.

---

You are implementing Phi-JEPA in the user's repository. Read the applicable root/nested AGENTS.md, docs/README.md and docs/PROGRESS.md, then these package documents: [docs/03_data_evaluation.md](../docs/03_data_evaluation.md); [docs/05_baselines.md](../docs/05_baselines.md); [docs/06_phases.md](../docs/06_phases.md); [docs/10_environment.md](../docs/10_environment.md). Read the active phase in the phase specification and the last completed phase report. File paths here assume this package was installed under docs/; preserve equivalent paths if the user placed it elsewhere.

Implement only P06; also read references/baseline_runbook.md. Pin official source commits and preserve licenses. Keep isolated environments and a patch ledger. Implement shared-physics-to-native data adapters, verified solution-step conversion, local loaders, canonical multi-component targets, signed/scientific numeric parsing, token/filter audits, checkpoint loading, bounded smoke/profile commands and result import.

Preserve native-reference and physics-adapted configurations separately. Handle CoConuT's CoT precursor/curriculum/resume behavior and CODI's author paths, CUDA/BF16 behavior, strict=False key audit and attention-mask flag deliberately. Do not silently install CUDA 12.6 pins over the RTX 5090's cu128 profile. Do not invent flags that upstream code does not implement.

CPU format/adapter tests can finish while the workstation GPU check is pending. Actual GPU forward/backward, checkpoint/stage transition and memory-profile gates must remain pending until executed. No released arithmetic checkpoint result is a physics-trained benchmark. Do not launch a full training run or unbounded native evaluation without a supplied cap/budget.

Write docs/reviews/P06_completion.md with upstream hashes, patches, exact launch commands, actual versus pending validations and resource estimates only where measured. Use implemented_pending_validation if GPU gates remain. Stop at the phase boundary.

For any blocker, use [BLOCKER_REPORT](BLOCKER_REPORT.md), diagnose it with bounded reversible steps, and continue independent authorized work. Do not reopen settled architecture or silently change the method. The final report must state actual commands/results, source/branch state, artifacts, deviations and pending gates per [workflow](../docs/07_workflow.md).
