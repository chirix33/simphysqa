# P12 four-condition follow-up preparation — 29 September 2026

**Interface status: partially resolved, implemented_pending_validation.** Explicit
Llama CoT and the final v1.1 interface pass offline checks. Neither new cohort has
model outputs. The revised development proposal and separate fresh-validation
proposal are **disabled and unauthorized**. No expanded study or confirmation
outcomes were accessed in this task.

Branch `main`, base commit `248575fd500947edd325836e636aebe41f9f65d0`.
Existing uncommitted numerical-training work, original model lock, archived v1
requests/results/failures, enrichment, scoring rules, held-out selections and
paper are preserved. New artifacts use a separate versioned directory. The old
v2 proposal is archived there rather than discarded.

| Condition | Total output maximum | Request maximum | Temperature / top-p / top-k | New attempts / completed |
| --- | ---: | ---: | --- | --- |
| Qwen3-8B thinking-off | 1,024 | 120 s | 0.7 / 0.8 / 20 | 0 / 0; not run |
| Qwen3-8B thinking-on | 4,096 | 240 s | 0.6 / 0.95 / 20 | 0 / 0; not run |
| Llama-3.1-8B-Instruct direct | 1,024 | 120 s | 0.6 / 0.9 / 50 | 0 / 0; not run |
| Llama-3.1-8B-Instruct CoT | 4,096 | 240 s | 0.6 / 0.9 / 50 | 0 / 0; not run |

These are upper bounds, not required lengths. Reasoning and final answer share
the same token/time allowance. All conditions retain seed 11, BF16, no
quantization, SDPA, batch size one, context limit 32,768 and the pinned model and
tokenizer revisions from `configs/local_answers_p12.lock.json`. Qwen uses revision
`b968826d9c46dd6066d109eabc6255188de91218`; Llama uses
`0e9e39f249a16976918f6564b8830bc894c89659`. No native Llama thinking switch is used.

Each proposed run is one round of 32 requests: `8 × (120+240+120+240) = 5,760 s`,
or **96 minutes**. Its **shared two-hour window leaves 1,440 s / 24 minutes** for
loading, tokenizer/compiler setup, transfers, serialization and other overhead.
Constraint processing is also charged to each request. The persisted clock must
start before loading, never renew on resume, and stop remaining work when the
overhead reserve is spent or a full request allowance no longer fits. No retries
are planned; every failed/interrupted/retried attempt counts if one occurs.
GPU work must serialize after active embedding/other workers. The launcher must
supervise hard deadlines: Transformers `max_time` alone is a soft stopping limit.
The preparation tool deliberately has no generation entry point; authorization
must precede binding a supervised launcher to this frozen manifest. Do not run
the historical runner with substituted globals or reset its budget.

The development plan uses the exact original eight public validation cases.
The separate fresh check proposes eight new cases, two distinct scenario groups
per domain, with its **own separately authorized 32-request / two-hour budget**.
It is not a second round hidden inside the development window. Selection uses
seeded SHA256 ordering of identities, without accuracy, reference values or
input-length optimization. It excludes 56 known inspected/development identities
and every correlated member of those scenario groups. Only validation public
inputs and identity metadata were opened for selection; rendering/decoding then
ran under the public-only deployment guard. No references were opened.

“Fresh” means fresh for this answer-interface check and disjoint from that
exposure manifest. The validation partition was already used for numerical-model
checkpoint selection; this is not a globally unseen scientific test. The fresh
cohort, public inputs, exact requests, configuration and sources are frozen now,
before any outputs. Its check remains outstanding even if the reused eight pass.
Any configuration revision must receive a new frozen version before fresh-check
generation; an inspected cohort must never silently be called fresh again.

The shared prompt/schema/adapter remain v1.1: prominent cutoff/absolute times,
complete public facts and future controls, persistence allowed, exact target-ID
JSON, ordered schema transport, strict typed support/abstention contract and
unchanged canonical validation/scoring. Direct answers are constrained from the
first generated token. Native Qwen thinking is unmasked until `</think>`.

Llama CoT adds an explicit step-by-step reasoning instruction and the delimiter
`<<<FINAL_ANSWER>>>`. The first exact delimiter is authoritative. The decoder
never searches arbitrary reasoning for JSON. It preserves raw reasoning and
activates the same final grammar only after the delimiter. Actual Llama tokens
can span the delimiter and a newline or `{`: the decoder validates that suffix
verbatim before masking subsequent tokens. Leading JSON-envelope whitespace is
kept in raw output and ignored for grammar priming, as in the existing final-text
strip. Invalid suffixes fail without repair. Missing/duplicate boundaries and
exhausted budgets fail. The boundary token is counted with reasoning; its exact
answer suffix is recorded separately so token totals are additive and the byte
overlap remains visible.

The pinned XGrammar 0.1.19 runtime exposes string priming only through
`_debug_accept_string`; this private API is explicitly tested and pinned. A
runtime upgrade requires requalification. The boundary token itself is sampled
while reasoning is unconstrained, so its answer suffix is validated rather than
retroactively constrained. Grammar validity alone still cannot guarantee finite
numbers (e.g. an overflowing exponent); the unchanged canonical parser remains
the final boundary.

Verification: **32 focused tests passed**, including strict IDs, value types,
dimensions, nonfinite values, reasons, unchanged values, public-input preservation,
native reasoning gate, actual Llama streaming/straddling-token boundaries and
budget/settings arithmetic. **64 saved/reloaded requests** passed context and
actual-tokenizer checks; **128 supported/unsupported dummy grammar paths** passed.
These are offline synthetic checks, not forecasting measurements. The historical
budget hash remains `b7f8d43568dd3fc9e5df06bab6b1c5e2a5c369a67aa2acc7d25eb45200c48434`.

For **each of the four conditions**, strict contract validity, supported coverage,
numerical/Boolean correctness, whole-answer correctness, repetition, generated
tokens, latency and GPU memory are **not measured yet**. The frozen reporting
specification requires separate attempted/EOS/syntax/contract counts, support and
abstention denominators, numerical/Boolean eligible and evaluated denominators,
whole-answer correctness out of all eight including failures, per-quantity
MAE/RMSE, observed/hold-last repetition and hold-last scores, input/reasoning/final
tokens, latency distribution, load/setup/constraint overhead, memory, and every
boundary/truncation/runtime failure. References may be opened only by the separate
post-generation evaluator. All-unsupported output cannot establish useful
forecasting; low accuracy is not permission for prompt tuning.

Historical v1 results remain in the [original report](P12_answer_interface_completion.md):
Qwen thinking exhausted all eight 2,048-token budgets; those results do not measure
this v1.1 configuration, the proposed 4,096 allowance, or Llama CoT. Inspect new
completion and boundary failures before proposing any 8,192-token increase. No
increase or additional prompt optimization is authorized by this proposal.

Reproduce the offline checks from the repository root in WSL:

```bash
export PYTHONPATH=/home/aashraf/phi-jepa/p12-answer-interface-deps:src:tests:tools
export HF_HUB_OFFLINE=1 TRANSFORMERS_OFFLINE=1
PY=/home/aashraf/phi-jepa/.venvs/phi-core/bin/python
$PY -m unittest test_p12_explicit_reasoning test_p12_followup test_p12_answer_interface test_p12 test_p11 -q
$PY tools/p12_answer_interface_followup.py verify
# Preparation is idempotent: an existing freeze is verified, never overwritten.
$PY tools/p12_answer_interface_followup.py prepare
```

Reviewable artifacts:

- [Disabled development proposal](../../configs/p12_answer_interface_followup.proposed.json).
- [Disabled fresh-validation proposal](../../configs/p12_answer_interface_fresh_validation.proposed.json).
- [Frozen cohort and artifact/source identities](artifacts/P12_answer_interface_followup_v3/freeze.json), SHA256 `ec623b5e0f2b30e46c165f405f220c799318f9c267c47843e2112683b65cb524`.
- [Fresh public cohort](artifacts/P12_answer_interface_followup_v3/fresh-validation/public-cohort.json), semantic SHA256 `7cfe9bae8030b46771aa18e08e651e9d8211d57565d3516d0fb420d8f4a5cf68`.
- [Offline grammar evidence](artifacts/P12_answer_interface_followup_v3/offline-verification.json).
- [Llama boundary implementation](../../src/phi_jepa/providers/explicit_reasoning.py) and [shared backend](../../src/phi_jepa/providers/constrained_local.py).

**Ready to freeze for the expanded study: no.** This candidate is frozen for
qualification, not empirically qualified for the expanded study. The next
decision is authorization of the revised development proposal. The fresh check
requires its own subsequent authorization and remains outstanding. No other
scientific choice is needed to review these disabled plans.
