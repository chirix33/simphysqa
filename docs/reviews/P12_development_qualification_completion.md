# P12 development qualification completed — 30 September 2026

**Interface status: partially resolved. Output failures remain under the authorized
limits.** All 32 requests ran once. Thirty produced EOS-terminated, syntax-valid,
strict contract-valid answers. Qwen thinking-on exhausted its 4,096-token allowance
twice. There were no runtime failures, timeouts, retries, repairs, or complete
final answers rejected by the canonical parser. Llama CoT's boundary worked in
all eight cases, but three responses omitted reasoning before it.

The run took **1,096.99 seconds / 18.28 minutes**, including loading and setup,
within the shared two-hour window. This completes only the authorized reused-eight
development qualification. Fresh validation remains unexecuted and disabled;
expanded-study readiness is not established.

Branch `main`, base commit `248575fd500947edd325836e636aebe41f9f65d0`.
The executed proposal SHA256 is
`68ab8086e08b40c1695a8fe23b8b3a7166601f4a1c9dbc5a2a3d5ff314419720`.
Scientific source identity is unchanged from preparation:
`4e7da84dd47b8ba4a858307a31a8d3896685e3211c6f258bb5e26125f684a4ee`.
The original disabled proposal/freeze and all historical v1 failures are retained.
An authorized copy and separately hashed supervisor/evaluator live in the new run.
Existing uncommitted training work, enrichment, scoring rules, held-out selections
and paper are unchanged. No paid calls, confirmation outcomes, expanded study,
push or merge occurred.

## Completion and forecasting

“Completed” below means EOS-terminated. All eight calls per condition returned and
were recorded, including Qwen's two truncated outputs. Syntax/contract counts are
out of eight; accuracy includes failed and abstained targets in eligible denominators.
Numerical counts are targets, including vectors, rather than vector components.

| Condition | Attempted / returned / EOS completed | Syntax / strict contract | Supported targets | Abstained targets | Whole-answer correct |
| --- | --- | --- | --- | --- | --- |
| Qwen thinking-off | 8 / 8 / 8 | 8 / 8 | 40/40 (100%) | 0/40 (0%) | 1/8 |
| Qwen thinking-on | 8 / 8 / 6 | 6 / 6 | 28/40 (70%) | 6/40 (15%) | 1/8 |
| Llama direct | 8 / 8 / 8 | 8 / 8 | 28/40 (70%) | 12/40 (30%) | 0/8 |
| Llama prompted CoT | 8 / 8 / 8 | 8 / 8 | 32/40 (80%) | 8/40 (20%) | 0/8 |
| Hold-last control | No model requests | Deterministic typed control | 40/40 | 0/40 | 1/8 |

The remaining six Qwen-thinking targets (15%) belong to failed requests; they are
not abstentions. No condition was all-unsupported. Llama direct abstained on **all
12 Boolean targets**. Some abstention reasons describe an event as absent; those
reasons were not converted into Boolean predictions.

| Condition | Numerical correct / eligible | Numerical evaluated | Boolean correct / eligible | Boolean evaluated |
| --- | --- | --- | --- | --- |
| Qwen thinking-off | 10/28 (35.7%) | 28 | 7/12 (58.3%) | 12 |
| Qwen thinking-on | 13/28 (46.4%) | 19 | 6/12 (50.0%) | 9 |
| Llama direct | 10/28 (35.7%) | 28 | 0/12 (0%) | 0 |
| Llama prompted CoT | 9/28 (32.1%) | 28 | 1/12 (8.3%) | 4 |
| Hold-last | 13/28 (46.4%) | 28 | 7/12 (58.3%) | 12 |

For Qwen thinking-on, valid-only numerical correctness is 13/19 and Boolean
correctness is 6/9; these conditional rates do not replace eligible-denominator
results. Llama direct's valid-only Boolean accuracy is undefined (zero evaluated),
not zero percent. Llama CoT's valid-only Boolean accuracy is 1/4.
Per-domain/quantity native-unit MAE and RMSE, with evaluated counts, are in each
condition's linked evaluation artifact. Existing tolerances, vector distances and
quaternion treatment were used unchanged.

No condition exceeded hold-last on whole-answer correctness. The eight cases are
reused development cases (two per domain, all ID), so this is a debugging result,
not an independent generalization or OOD result. Low forecasting accuracy does
not justify retuning this completed run.

## Repetition

Exact equality is checked against matching public measurement channels. The
denominator is supported/evaluated targets of the relevant type; failures and
abstentions have no numeric value to compare. Persistence was allowed by design.

| Condition | Numeric equals any observed | Numeric equals hold-last | Boolean equals any observed / hold-last |
| --- | --- | --- | --- |
| Qwen thinking-off | 15/28 | 8/28 | 12/12 / 12/12 |
| Qwen thinking-on | 9/19 | 3/19 | 9/9 / 9/9 |
| Llama direct | 18/28 | 15/28 | 0/0 / 0/0 (not applicable) |
| Llama prompted CoT | 10/28 | 9/28 | 3/4 / 3/4 |
| Hold-last | 28/28 | 28/28 | 12/12 / 12/12 |

Repetition counts alone do not establish an error: persistence can be a correct
forecast. The independent gold comparison above determines correctness.

## Remaining output and reasoning failures

Both output failures were Qwen thinking-on driving questions:

- `c17eb5d6194d9ac370e960ed103edac9`: 4,080 reasoning tokens, then 16 final tokens.
  The native `</think>` boundary was found and the answer grammar activated, but
  the 4,096-token cap cut off the JSON before completion.
- `f79317340aceb5423ab4d7f1da33acd3`: 4,096 reasoning tokens, zero final tokens;
  the native closing boundary was absent when the token allowance ended.

Thus there were **two token-cap failures, one missing boundary, zero time-cap
failures and zero runtime failures**. These categories overlap: the missing
boundary is one of the two truncations. No JSON was recovered from reasoning and
no missing predictions were synthesized. The six successful Qwen-thinking outputs
used 1,691–3,546 total tokens; the maximum was not forced.

Llama CoT produced the exact explicit delimiter and valid final answer in 8/8
cases, with no missing/duplicate boundary or invalid boundary-token suffix.
Five responses contained prose before the delimiter. Three emitted only the
delimiter before their answer: object cases `f59ef3672785aaff7e14547781c43e4d` and
`92bd4c8c45c02bd49e083101c3999999`, and arm case
`b9302dd565e2bcf04a5984808d930603`. Each has six tokens counted in the reasoning
segment because that segment includes the delimiter. They are **valid answers
but noncompliant with the requested reasoning step**. This is a prompted-CoT
condition with observed reasoning compliance 5/8, not evidence of substantive
CoT in every request. No native Llama thinking flag or forced reasoning length was
introduced. No prompt was changed after inspecting outputs.

## Tokens, time and memory

| Condition | Input tokens | Output tokens | Reasoning / final tokens | Backend request time sum | Load/setup | Peak allocated / reserved GiB |
| --- | ---: | ---: | ---: | ---: | ---: | --- |
| Qwen thinking-off | 81,025 | 1,604 | 0 / 1,604 | 63.13 s | 12.49 s | 18.484 / 19.172 |
| Qwen thinking-on | 80,993 | 24,627 | 23,257 / 1,370 | 853.60 s | 6.17 s | 18.484 / 19.172 |
| Llama direct | 64,302 | 1,367 | 0 / 1,367 | 40.87 s | 10.79 s | 17.359 / 17.895 |
| Llama prompted CoT | 65,086 | 3,588 | 2,240 / 1,348 | 93.83 s | 10.06 s | 17.386 / 17.906 |

Token totals include truncations, delimiters and generated EOS tokens. An explicit
boundary token is counted with reasoning; any answer suffix in that token is
recorded separately. Raw reasoning, final text, token IDs and boundary offsets are
preserved. Memory figures are measured CUDA allocation/reservation peaks;
per-process driver memory was not continuously sampled and is not claimed.

| Condition | Latency min / median / p95 / max | Grammar compilation | Processor wall time |
| --- | --- | ---: | ---: |
| Qwen thinking-off | 3.39 / 6.44 / 15.11 / 15.44 s | 1.25 s | 25.72 s |
| Qwen thinking-on | 52.21 / 105.67 / 157.46 / 157.88 s | 1.25 s | 360.69 s |
| Llama direct | 3.22 / 4.32 / 8.58 / 8.70 s | 1.12 s | 18.28 s |
| Llama prompted CoT | 4.52 / 10.43 / 17.74 / 18.97 s | 1.12 s | 37.05 s |

Compilation and processor times are **included in request latency**, not added on
top. Processor wall time includes reasoning-boundary checks, synchronization and
CPU mask transfers, so it is not an isolated estimate of grammar arithmetic cost.
The observational token streamer also runs inside the measured request interval.

The supervisor recorded 1,052.93 seconds in request intervals and 44.06 seconds in
loading/setup/other overhead, totaling 1,096.99 seconds. Backend latency sums to
1,051.43 seconds within those intervals; the approximately 1.50-second difference
includes request orchestration and saving. Setup/other overhead was well below
its 1,440-second reserve. All request times were below their 120/240-second limits.
Evaluation ran only after generation closed and took 2.92 seconds (excluding
artifact export). There were no retries, repairs or paid calls.

## Configuration, evidence and next gate

All four conditions used final v1.1 ordered schema transport, the compact exact
target-ID contract, public-only metadata adapter, unchanged canonical parser and
the pinned XGrammar 0.1.19 CPU mask. Qwen thinking was unconstrained until native
`</think>`; Llama CoT was unconstrained until `<<<FINAL_ANSWER>>>`. Full public
inputs, observation cutoff, absolute prediction times and scheduled interventions
were preserved. No enrichment, Phi forecasts, tools or private future inputs were
available to the generator. The pinned private string-priming API and its tested
boundary-token behavior are unchanged from the preparation report.

Direct limits were 1,024 tokens/120 seconds; reasoning limits were 4,096 total
tokens/240 seconds. Seed 11, sampling, model/tokenizer revisions, BF16, SDPA and
context limits were unchanged. The larger reasoning allowance is not compute
matched to direct generation.

**36 pre-run offline tests passed**, including hard supervisor timeout, immutable
attempt counting, token-stream preservation and the frozen interface tests.
Post-run replay checked all **32 raw token streams** against the returned IDs and
all **30 valid answers** against the adapter. Predictions were identical. Running
the completed wrapper again made zero new attempts and retained the closed
ledger. The frozen preparation still verifies; historical budgets were not reset.

- [Authorized plan and source identities](artifacts/P12_answer_interface_qualification_02/authorization.json).
- [Closed attempt budget](artifacts/P12_answer_interface_qualification_02/budget.json).
- [Four-condition summary and hold-last](artifacts/P12_answer_interface_qualification_02/evaluation/summary.json).
- Per-target scores, per-quantity MAE/RMSE, costs and repetition: [Qwen off](artifacts/P12_answer_interface_qualification_02/evaluation/qwen3_8b_direct.json), [Qwen on](artifacts/P12_answer_interface_qualification_02/evaluation/qwen3_8b_thinking.json), [Llama direct](artifacts/P12_answer_interface_qualification_02/evaluation/llama31_8b_direct.json), [Llama CoT](artifacts/P12_answer_interface_qualification_02/evaluation/llama31_8b_cot.json).
- [Raw-token/adapter audit](artifacts/P12_answer_interface_qualification_02/evaluation/audit.json) and [full artifact index](artifacts/P12_answer_interface_qualification_02/artifact-index.json).
- [Historical v1 report](P12_answer_interface_completion.md) and [frozen follow-up preparation](P12_answer_interface_followup_completion.md).

Native artifacts are at `/home/aashraf/phi-jepa/p12-answer-interface-qualification-02`.
The export includes exact requests/messages, input tokens, generated tokens,
reasoning, parsed outputs, worker logs, configurations and content-addressed source
snapshots. Only the eight selected development reference values were parsed by
the separate evaluator. Fresh-cohort outputs do not exist; its check is outstanding.

Commands actually run from the repository root in WSL:

```bash
export PYTHONPATH=/home/aashraf/phi-jepa/p12-answer-interface-deps:src:tests:tools
export HF_HUB_OFFLINE=1 TRANSFORMERS_OFFLINE=1
PY=/home/aashraf/phi-jepa/.venvs/phi-core/bin/python
$PY -m unittest test_p12_qualification_run test_p12_explicit_reasoning test_p12_followup test_p12_answer_interface test_p12 test_p11 -q
$PY tools/p12_interface_qualification_run.py run
$PY tools/p12_interface_qualification_report.py
$PY tools/p12_interface_qualification_run.py run  # verified closed-run no-op
```

**Ready to freeze for the expanded study: no.** Complete final answers are
reliably serialized in this small reused cohort, but Qwen thinking still loses
2/8 requests to its total output budget, and Llama prompted CoT does not reliably
produce reasoning prose. No 8,192-token run was proposed or launched on these
results. The unresolved decision is whether to separately qualify a larger Qwen
thinking allowance and whether 5/8 observed reasoning compliance is sufficient
for the intended Llama CoT baseline. Any revision must be versioned and frozen
before the separate fresh-validation check; no forecasting-score optimization is
authorized. Fresh validation and expanded-study launch require their separate
decisions.
