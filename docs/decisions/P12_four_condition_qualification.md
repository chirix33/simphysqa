# Four-condition interface qualification proposal — 29 September 2026

The user's latest instruction supersedes the disabled 8,192-token proposal.
Propose Qwen thinking-off, Qwen thinking-on, Llama direct and explicit Llama CoT
using final v1.1. Direct limits are 1,024 tokens/120 seconds; both reasoning limits
are 4,096 total output tokens/240 seconds. One fixed 32-request development round
uses 96 minutes of worst-case request time plus 24 minutes loading/setup/overhead
within a persisted two-hour window. No generation is authorized yet.

Explicit Llama CoT uses `<<<FINAL_ANSWER>>>`, without a native thinking flag.
The actual pinned tokenizer can merge delimiter and answer bytes; retain raw
reasoning, validate the exact overlapping suffix, then activate the same JSON
grammar. Never search reasoning for JSON or repair outputs. Missing boundaries,
invalid suffixes, invalid canonical answers and exhausted budgets fail.

Freeze eight additional scenario-disjoint validation cases (two per domain) and
a separate disabled 32-request/two-hour budget now. This is fresh to the interface
check, not globally unseen data after numerical checkpoint selection. Do not
read outcomes until configuration is frozen; reused-eight success cannot satisfy
this check. Inspect completion/boundary failures before proposing 8,192 tokens;
do not tune toward a forecasting score.

The [completion report](../reviews/P12_answer_interface_followup_completion.md)
records implementation, evidence, exact manifests, remaining gates and commands.
Historical v1 failures, scoring rules, enrichment, held-out selections and paper
remain unchanged. Expanded-study launch remains a separate decision.
