# P12 Qwen completion-budget qualification — 1 October 2026

**Qwen completion status: resolved on these eight development cases.** All eight
original cases ran once with 8,192 total output tokens and a supervised 360-second
request maximum. All eight completed with EOS, valid syntax and strict canonical
answers. There were **zero token-cap, time-cap, missing-boundary or runtime
failures**, and zero retries, repairs or forced reasoning termination.

The run used **894.76 seconds / 14.91 minutes** of its one-hour shared window,
including setup. The two previous truncations completed by extending their exact
saved token sequences. Forecasting remains weak: whole-answer correctness is
still **1/8**, equal to hold-last. Fresh validation remains unexecuted and disabled;
this reused-case result is not evidence that the expanded study is ready.

Branch `main`, base commit `248575fd500947edd325836e636aebe41f9f65d0`.
Native run: `/home/aashraf/phi-jepa/p12-qwen-thinking-budget-8192-01`.
Approved plan SHA256:
`37ce5f6d75c14bb9728f81bbf8e6a71e7ffdcd9349443677fbe8e83b2ed95b85`.
Scientific source identity remains
`4e7da84dd47b8ba4a858307a31a8d3896685e3211c6f258bb5e26125f684a4ee`.
Historical runs, other baselines, existing uncommitted training work, enrichment,
scientific scoring rules, held-out selections and paper were preserved. No paid
calls, fine-tuning, confirmation requests/outcomes, expanded study, push or merge.

## Completion, coverage and forecasting

All eight calls returned normally. Completion counts below mean EOS termination.
Numerical counts are targets, including vectors, rather than individual components.
All eligible targets remain in the primary correctness denominators.

| Measure | Prior Qwen thinking-on: 4,096 / 240 s | New Qwen thinking-on: 8,192 / 360 s |
| --- | ---: | ---: |
| Attempts | 8 | 8 |
| EOS completion / syntax valid / strict valid | 6 / 6 / 6 | 8 / 8 / 8 |
| Token-cap failures | 2 | 0 |
| Missing native final boundary | 1 | 0 |
| Time-cap / runtime failures | 0 / 0 | 0 / 0 |
| Supported-target coverage | 28/40 (70%) | 34/40 (85%) |
| Abstentions / all eligible targets | 6/40 (15%) | 6/40 (15%) |
| Numerical correct / eligible | 13/28 (46.4%) | 14/28 (50.0%) |
| Numerical evaluated | 19 | 23 |
| Boolean correct / eligible | 6/12 (50.0%) | 7/12 (58.3%) |
| Boolean evaluated | 9 | 11 |
| Whole-answer correct, failures included | 1/8 (12.5%) | 1/8 (12.5%) |

New valid-only numerical correctness is **14/23 (60.9%)** and Boolean correctness
is **7/11 (63.6%)**. These conditional rates do not replace eligible-denominator
results. Five numerical targets and one Boolean target were explicitly unsupported;
there were no targets lost to output failure. Abstention reasons remain raw model
outputs; none were converted into Boolean outcomes or numerical predictions.

Hold-last remains 13/28 numerical, 7/12 Boolean and 1/8 whole-answer correct, with
40/40 supported targets. Thus the revised Qwen output has one additional correct
numerical target over hold-last, but no whole-answer improvement. Per-domain and
quantity MAE/RMSE in native units, with evaluated counts, are recorded in the
[Qwen evaluation](artifacts/P12_qwen_thinking_budget_8192_01/evaluation/qwen3_8b_thinking.json).
The evaluator, tolerances and vector/quaternion treatment are unchanged.

## Trace evidence and repetition

| Former failure | Prior stop | New natural completion |
| --- | --- | --- |
| `c17eb5d6194d9ac370e960ed103edac9` | 4,080 reasoning + 16 partial final tokens | 4,080 reasoning + 91 final tokens = **4,171**, in 160.04 s |
| `f79317340aceb5423ab4d7f1da33acd3` | 4,096 reasoning tokens, no closing boundary | 4,852 reasoning + 88 final tokens = **4,940**, in 189.06 s |

The first case needed 75 tokens beyond the old cap; the second needed 844.
All eight prior token sequences are exact prefixes of their new sequences. The
six already-complete sequences are identical in full. No reasoning was interrupted,
no boundary was inserted, and no answer was recovered by searching reasoning.
Actual output lengths ranged from **1,691 to 4,940**, so neither allowance was
forced. There is no remaining incomplete trace requiring further escalation.

Exact repetition among the new supported targets:

- Numerical: **11/23** equal some matching historical observation; **5/23** equal
  the last observation. Prior counts were 9/19 and 3/19.
- Boolean: **11/11** equal a matching historical observation and hold-last.
- Hold-last itself repeats all 28 numerical and 12 Boolean observations.

Persistence remains allowed. Equality to an observation is reported separately
from correctness; it is not automatically classified as an error.

## Other conditions retained unchanged

These are the **prior 30 September results**, not new generations. No responses
were filtered or selectively regenerated.

| Retained condition | New attempts here | Prior strict-valid | Prior supported targets | Prior numerical correct / evaluated / eligible | Prior Boolean correct / evaluated / eligible | Prior whole-answer correct |
| --- | ---: | ---: | ---: | --- | --- | ---: |
| Qwen thinking-off | 0 | 8/8 | 40/40 | 10 / 28 / 28 | 7 / 12 / 12 | 1/8 |
| Llama direct | 0 | 8/8 | 28/40 | 10 / 28 / 28 | 0 / 0 / 12 | 0/8 |
| Llama **prompted CoT** | 0 | 8/8 | 32/40 | 9 / 28 / 28 | 1 / 4 / 12 | 0/8 |

Llama prompted CoT has **5/8 nonempty reasoning compliance**, separately from
**8/8 final-answer validity**. Nonempty means non-whitespace text before the exact
delimiter; the delimiter itself is excluded. Three prior responses emitted the
delimiter immediately. All eight remain included in scores, cost and validity.
Nonempty prose does not establish correctness or quality of the reasoning. The
[retained-baseline audit](artifacts/P12_qwen_thinking_budget_8192_01/evaluation/completion-and-compliance-audit.json)
records this per case, with source hashes and no new baseline calls.

## Resource use and verification

| Resource | New Qwen qualification |
| --- | ---: |
| Input tokens | 80,993 |
| Total output tokens | 25,546 |
| Reasoning / final segment tokens | 24,013 / 1,533 |
| Backend request-time sum | 881.15 s |
| Request latency min / median / p95 / max | 51.11 / 104.23 / 178.90 / 189.06 s |
| Model/tokenizer/backend loading and setup | 12.45 s |
| Supervisor setup/other overhead | 13.23 s |
| Shared model-run wall time | 894.76 s (14.91 min) |
| Grammar compilation / processor wall time | 1.26 / 374.00 s |
| Peak CUDA allocated / reserved | 18.484 / 19.172 GiB |
| Retries / repairs / paid calls | 0 / 0 / 0 |

Compilation, processor work and observational token logging are included in
request time. Processor wall time includes synchronization and CPU mask transfers;
it must not be added again to request time or interpreted as isolated grammar
arithmetic. Supervisor request intervals total 881.53 seconds, including about
0.38 seconds of orchestration/saving beyond backend timers. Setup/other overhead
was below the 720-second reserve. Per-process driver memory was not continuously
sampled; CUDA allocation/reservation peaks are the reported memory measurements.
Scoring occurred only after generation closed and took 2.50 seconds before export.

**38 offline tests passed** before generation. All eight public requests passed
the actual pinned tokenizer/grammar checks, including 16 dummy supported and
unsupported paths. The largest complete input plus 8,192-token output reserve was
**21,743 / 32,768**. Request comparison allowed changes only to `max_new_tokens`
and `max_seconds`; messages, rendered template, input IDs, schema and all other
settings matched exactly. Post-run replay verified all eight raw token archives
and all eight adapted answers. Re-invoking the completed supervisor was a no-op
with zero additional attempts; its original deadline and ledger were retained.

The final v1.1 prompt, ordered schema, deterministic public-metadata adapter,
strict parser, Qwen model/tokenizer, sampling settings and scientific evaluator
were unchanged. Qwen revision is `b968826d9c46dd6066d109eabc6255188de91218`; seed 11,
temperature 0.6, top-p 0.95, top-k 20, BF16, SDPA, no quantization and context
32,768 remain fixed. Native reasoning stayed unconstrained until `</think>`;
only the final answer used the existing XGrammar 0.1.19 CPU mask. Generation had
public inputs only and the deployment I/O guard. Only the eight development
reference records were parsed by the separate post-generation evaluator.

## Disabled fresh-validation proposal

The predeclared completion criterion passed: all eight EOS-completed and strictly
valid without repair. **8,192 / 360 s is selected for the revised proposal based
only on completion**, not forecasting score. The new version is frozen before any
fresh generation. The original proposal and cohort remain preserved.

| Condition | Output-token maximum | Request-time maximum |
| --- | ---: | ---: |
| Qwen thinking-off | 1,024 | 120 s |
| Qwen thinking-on | 8,192 | 360 s |
| Llama direct | 1,024 | 120 s |
| Llama prompted CoT | 4,096 | 240 s |

The existing eight scenario-disjoint validation cases are reused **without
reselection**, two per domain. The 24 requests for unchanged conditions are
byte-identical to the prior fresh preparation; only Qwen-thinking allowance fields
changed in its eight requests. Maximum complete context reserve across all 32
requests is **21,715 / 32,768**. Cohort semantic SHA256 remains
`7cfe9bae8030b46771aa18e08e651e9d8211d57565d3516d0fb420d8f4a5cf68`.

Budget: **32 attempts, one round**, with
`8 × (120 + 360 + 120 + 240) = 6,720 seconds = 112 minutes` worst-case request
time. Proposed shared window: **9,000 seconds / 150 minutes**, leaving
**2,280 seconds / 38 minutes** for loading/setup/other overhead. A persisted clock
must start before loading, enforce hard request/shared deadlines and never renew
on resume. No retries, repairs, selective regeneration or automatic escalation.
GPU work must serialize with active preparation. Prompted-CoT nonempty reasoning
and final-answer validity will be reported independently, retaining all responses.

**Execution remains disabled pending review.** There were zero fresh generations
and no fresh outputs were inspected. This cohort is fresh for the answer-interface
check and scenario-disjoint from development/known exposure, but its validation
partition was used for numerical-model checkpoint selection; it is not a globally
unseen scientific test. Reused-eight completion does not finish this check.

- [Disabled fresh-validation v2 proposal](../../configs/p12_answer_interface_fresh_validation_v2.proposed.json).
- [Fresh v2 freeze](artifacts/P12_fresh_validation_v2_8192/freeze.json), SHA256 `0e6ace8690b37aaee5f1b6318554e6d6060836e691af64e6545e06f4b0c8fc94`.
- [New qualification summary](artifacts/P12_qwen_thinking_budget_8192_01/evaluation/summary.json), [closed budget](artifacts/P12_qwen_thinking_budget_8192_01/budget.json), [authorization/source identity](artifacts/P12_qwen_thinking_budget_8192_01/authorization.json), and [full artifact index](artifacts/P12_qwen_thinking_budget_8192_01/artifact-index.json).
- [Trace and prompted-CoT audit](artifacts/P12_qwen_thinking_budget_8192_01/evaluation/completion-and-compliance-audit.json).
- [Previous four-condition qualification](P12_development_qualification_completion.md), retained unchanged.

Commands actually run from the repository root in WSL:

```bash
export PYTHONPATH=/home/aashraf/phi-jepa/p12-answer-interface-deps:src:tests:tools
export HF_HUB_OFFLINE=1 TRANSFORMERS_OFFLINE=1
PY=/home/aashraf/phi-jepa/.venvs/phi-core/bin/python
$PY -m unittest test_p12_qwen_completion test_p12_qualification_run test_p12_explicit_reasoning test_p12_followup test_p12_answer_interface test_p12 test_p11 -q
$PY tools/p12_qwen_completion_prepare.py prepare
$PY tools/p12_qwen_completion_run.py run
$PY tools/p12_qwen_completion_report.py
$PY tools/p12_qwen_completion_audit.py
$PY tools/p12_qwen_completion_prepare.py fresh
$PY tools/p12_qwen_completion_run.py run  # verified completed-run no-op
```

**Next decision:** review the disabled 150-minute fresh-validation proposal.
No further Qwen budget increase is proposed or needed for these observed cases.
Expanded-study readiness remains pending fresh validation. Llama's 5/8 nonempty
reasoning compliance remains an explicit limitation of the unchanged prompted-CoT
baseline, not a reason to filter or regenerate its historical responses.
