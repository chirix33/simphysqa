# Codex workflow and escalation

[Start](../README.md) · [Phases](06_phases.md) · [Review prompt](../prompts/REVIEW_PHASE.md) · [Blocker template](../prompts/BLOCKER_REPORT.md)

The user sends one phase prompt to the coding agent. Codex reads the listed documents, implements the slice, performs meaningful targeted checks, updates progress/decisions, and returns a concise completion report. The user returns that report to the planning assistant for review, then sends the next prompt. Do not use an initial prompt as blanket authorization for all experiments.

## Import and repository discipline

Place this complete package under `docs/implementation/`. Merge its AGENTS policy into the repository-root file without discarding existing applicable instructions. If existing rules conflict with the latest user decisions, explain the exact conflict. Inspect dirty state; preserve unrelated work. Prefer a dedicated phase branch or worktree when needed. Never reset/clean the checkout, remove historical artifacts, or overwrite a working implementation merely to match this proposed tree.

Phase commits are useful review units. Follow the user's current coding-session instructions for local commits. Do not push, merge, publish or message collaborators solely because a phase completed. This handoff does not grant unspecified paid API/training budgets. Local code edits, reversible fixes and bounded CPU tests are within an implementation phase; live/long runs need a supplied cap and credentials.

Keep the actual dependency lock and source revision with every report. The project-private repository has been identified, but Phase 0 is responsible for the current checkout inventory. Nested instruction files still apply.

## Blocking versus nonblocking choices

Codex may choose routine names, serialization, small helper libraries, numerical epsilon and test organization consistent with this specification, recording material choices. It may implement the explicit development defaults in [decisions](08_defaults_decisions.md) without asking the professor again.

Escalate scientific contradictions, unavailable required source assets, a missing output-label mapping, an unsupported dataset/physics claim, unavoidable changes to the algorithm, or a live run without a defined model/budget. An environment error is a problem to diagnose first: collect versions, exact command, traceback and minimal reproducer; try bounded reversible remedies that preserve constraints. Do not downgrade the CUDA stack to an incompatible wheel or change the method to fit a dependency.

The blocker report must state: phase/substep; exact expected versus observed behavior; reproducible command and sanitized trace; environment and commit; attempts/results; whether independent work can continue; two viable options and tradeoffs when known; recommended choice; smallest precise question the user must answer. Never just say “environment issue” or “clarify architecture.” Never include secrets.

## Completion report contract

1. Phase and status, branch/commit (or explicit uncommitted state).
2. What executable behavior now exists and where to find it.
3. Exact validation commands and short outcomes; distinguish tests actually run from suggested commands.
4. Artifacts: manifest/checkpoint/metrics/phase-report paths and hashes where relevant.
5. Algorithm/config changes and authority: settled requirement, explicit plan default or proposed deviation.
6. Remaining blocked/pending items, impact and a filled blocker report if needed.
7. Smallest next authorized step; stop at the phase boundary.

Write the durable report at `docs/reviews/PXX_completion.md`, update `docs/implementation/PROGRESS.md`, and record consequential decisions in `docs/decisions/` with date, alternatives, evidence and superseded decision IDs. Do not overwrite the supplied source transcripts or silently revise historical audit findings.

## Reviewer behavior

The planning assistant reviews evidence and code/diffs supplied by the user; a Codex assertion alone is not proof that a gate passed. Use [REVIEW_PHASE](../prompts/REVIEW_PHASE.md) for a separate review session if helpful. Findings should distinguish must-fix scientific/data errors from minor implementation preference. The next phase prompt may include precise fixes; avoid restarting accepted work.

## Efficient verification

Run the tests needed to cover the changed behavior and required gates. Examples: analytic oracle comparison, leakage boundary, gradient flow, checkpoint round trip, one real model smoke, profile. Do not inflate test counts with assertions mirroring constants or repeat full training to prove a doc-only change. Once evidence resolves the remaining risk, stop optional tests and report.

All generated figures/tables derive from raw saved records. A scheduler config, fixture result or expected range is not a measured experiment. The user's hardware report is evidence of WSL/NVIDIA visibility only; CUDA FP32/BF16 validation remains pending until returned.
