# Codex prompt: P07 — Workstation validation and pilot

Copy the text below into the coding session, or ask Codex to read this file after importing the package.

---

You are implementing Phi-JEPA in the user's repository. Read the applicable root/nested AGENTS.md, docs/implementation/README.md and PROGRESS.md, then these package documents: [docs/03_data_evaluation.md](../docs/03_data_evaluation.md); [docs/04_assessment_fallback.md](../docs/04_assessment_fallback.md); [docs/05_baselines.md](../docs/05_baselines.md); [docs/06_phases.md](../docs/06_phases.md); [docs/08_defaults_decisions.md](../docs/08_defaults_decisions.md); [docs/10_environment.md](../docs/10_environment.md). Read the active phase in the phase specification and the last completed phase report. File paths here assume this package was installed under docs/implementation/; preserve equivalent paths if the user placed it elsewhere.

Implement and execute only the authorized P07 slice. Read prior phase reports and the user's actual CUDA-check result. Reconcile environment versions, perform actual model/checkpoint smoke tests and bounded 20–50 optimizer-step memory/time profiles, completing pending P06 gates. Use the real workstation only if this coding session has access; never imply a sandbox is that workstation.

Before long or paid runs, write a concrete pilot manifest specifying model IDs/revisions, dataset/splits, seed, score profile, fallback policy, exact commands and compute/API caps. Consume a budget already authorized in the current session; if absent, complete offline preparation/profile work that is authorized and return the exact proposed cap for the user. Do not make up credentials or a budget.

Review Q1/Q2 decisions with the planner/user before any full-paper-faithfulness claim. A development_r1_v1 pilot may run only under that honest label. Run the approved one-domain pilot, preserve unsuccessful/missing baselines and export reproducible raw/aggregate artifacts. Report original/fallback errors, coverage, physical violations, OOD and cost metrics. Do not choose a winner by dropping failed cases.

Finish with docs/reviews/P07_completion.md, an evidence-backed main-study proposal and updated pending gates. Stop before the main multidomain experiment.

For any blocker, use [BLOCKER_REPORT](BLOCKER_REPORT.md), diagnose it with bounded reversible steps, and continue independent authorized work. Do not reopen settled architecture or silently change the method. The final report must state actual commands/results, source/branch state, artifacts, deviations and pending gates per [workflow](../docs/07_workflow.md).
