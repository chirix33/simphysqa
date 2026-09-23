# Codex prompt: P02 — Frozen interfaces and schema semantics

Copy the text below into the coding session, or ask Codex to read this file after importing the package.

---

You are implementing Phi-JEPA in the user's repository. Read the applicable root/nested AGENTS.md, docs/implementation/README.md and PROGRESS.md, then these package documents: [docs/02_architecture.md](../docs/02_architecture.md); [docs/04_assessment_fallback.md](../docs/04_assessment_fallback.md); [docs/06_phases.md](../docs/06_phases.md); [docs/08_defaults_decisions.md](../docs/08_defaults_decisions.md). Read the active phase in the phase specification and the last completed phase report. File paths here assume this package was installed under docs/implementation/; preserve equivalent paths if the user placed it elsewhere.

Implement only P02. Import the exact adopted assets/prompts.json and three response schemas as versioned immutable resources; verify their hashes. Preserve the archived repair prompt but make it unreachable from inference. Implement frozen text-embedding/provider interfaces, explicit fixture replay, a configurable live structured-output adapter, response/refusal/error types, bounded transport retries, content-based caches and call accounting.

Create generic JSON graph/features preserving names, units, values, operators, event text and topology. Build compact named answer payloads from [B,T,D] predictions with explicit batch selection, physical units and metadata. Preserve external answer schema and original numeric predictions. Unknown extracted numbers go in unknowns; do not mutate the supplied numeric schema to accept null without a versioned change.

Check equal-number/different-meaning schemas yield distinct features, masks and tree edges are correct, payload vectors have D rather than T*D entries, and changed inputs/prompts/models invalidate cache. Test malformed/refused/incomplete output, numeric answer mismatch and no secret logging. Use fixtures to validate behavior; mark live SDK/model checks pending if credentials or approved model/budget are absent. Do not ask for GPU access to finish offline work.

Write docs/reviews/P02_completion.md, including exact asset hashes and live-test status. Stop after the phase.

For any blocker, use [BLOCKER_REPORT](BLOCKER_REPORT.md), diagnose it with bounded reversible steps, and continue independent authorized work. Do not reopen settled architecture or silently change the method. The final report must state actual commands/results, source/branch state, artifacts, deviations and pending gates per [workflow](../docs/07_workflow.md).
