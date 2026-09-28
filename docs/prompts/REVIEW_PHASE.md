# Prompt for reviewing a completed phase

Review the submitted Phi-JEPA phase report, current diff/commit, actual run artifacts and acceptance criteria in docs/docs/06_phases.md. Read root AGENTS.md and the relevant architecture/data/assessment specifications. Do not rely on the report's assertions alone where source or logs are available.

Check scientific invariants, input/target separation, terminal supervision, physical oracle/evaluator validity, baseline independence, frozen references/thresholds, exact prompt scope, cost/failure accounting and reproducibility. Verify only the concrete risks relevant to this phase. Do not require unrelated future phases or full experiments to accept a foundational slice.

Return: accepted / accepted with nonblocking follow-ups / changes required; evidence inspected; prioritized findings with paths; exact minimal fixes; which checks must be rerun; and whether the next phase may begin. Distinguish implementation defects, missing environment evidence and unresolved scientific decisions. Never mark a live/GPU test passed from fixture evidence.

Do not implement the next phase, rewrite settled decisions, push/merge or launch paid runs as part of the review unless the user separately requests it.
