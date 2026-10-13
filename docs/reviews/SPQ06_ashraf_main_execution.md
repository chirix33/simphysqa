# SPQ06 actual Ashraf main execution

Ashraf's eight frozen combinations produced 1565 initial and 280 conditional records on the same 200 held-out QA/groups. Accounted main work is 57116.632 seconds (15.866 hours) of 72,000. Collaborator inference remains unexecuted; this is Ashraf's share, not completion of all nine enriched conditions.

The source base is 8c901ee on simphysqa-spq06. The final local commit/branch state is recorded in [post-commit receipt](<C:/Users/aashraf/.codex/visualizations/2026/10/06/01a1131b-eac2-7a31-afb4-f219a8dd6471/spq06/2026-10-09/main-ashraf-1.0.0/delivery-1.0.0/git-completion.json>). No merge, rebase or push is authorized or performed.

## Execution, coverage and reservations

| Condition | Representation | Initial status counts | Conditional status counts | Unexecuted conditional | Process lifecycle s | Loading s | Sampled device peak MiB |
| --- | --- | --- | --- | ---: | ---: | ---: | ---: |
| qwen3_8b_direct | enriched | {'completed': 199, 'length_limited': 1} | {'completed': 40} | 0 | 3353.180 | 13.118 | 31236 |
| qwen3_8b_thinking | enriched | {'completed': 200} | {'completed': 38} | 2 | 8903.735 | 12.172 | 31515 |
| llama31_8b_direct | enriched | {'completed': 199, 'length_limited': 1} | {'completed': 38} | 2 | 2934.729 | 12.855 | 27914 |
| llama31_8b_cot | enriched | {'completed': 200} | {'completed': 21} | 19 | 3281.603 | 12.709 | 27983 |
| qwen3_32b_awq_off | enriched | {'completed': 200} | {'completed': 40} | 0 | 4812.393 | 80.871 | 31999 |
| qwen3_32b_awq_on | enriched | {'completed': 200} | {'completed': 39} | 1 | 11710.200 | 79.756 | 31991 |
| qwen3_8b_direct | structured_only | {'completed': 165} | {'completed': 25} | 15 | 2564.525 | 13.185 | 29105 |
| qwen3_32b_awq_on | structured_only | {'completed': 200} | {'completed': 39} | 1 | 11976.800 | 80.994 | 31980 |

There are 1600 initial and 280 conditional reservations. Canonical conflicts: 0; invalid returned entries: 35; unknown process reservations: 1. Every combination retains 200 primary items, including failures. Clarification has 40 possible continuations per combination; absent/unsupported actual first turns receive immutable unexecuted-conditional receipts. No authored assistant question, truncated history, repaired answer, replacement item or scientific retry is used.

Llama CoT's missing development live stage 2 remains historical. Actual main stage 2 coverage is shown above; a combination with no completed continuation has no demonstrated completed main stage 2. Its conservative continuation allowance stays unchanged.

An abrupt PC restart interrupted the first Qwen3-8B direct structured-only batch. Its 15 saved actual outputs were imported unchanged; 35 reserved initials have no saved response and remain interrupted. The full 6,600 s unknown process bound is retained. No failed key was reopened, moved, replaced or rerun. Missing initial clarification responses have explicit unexecuted-conditional receipts with null actual response. The primary denominator remains 200 for this combination.

## Fixed-denominator family results

Each family has 40 independent QA/groups, ten per domain. Values are balanced domain means with the unchanged paired whole-trajectory percentile bootstrap: 10,000 replicates, seed 20261009, nominal marginal 95% intervals. Main conditions share identical stratified group draws. No adequately powered cell-level or natural-release-frequency claim follows. Degenerate observed bootstrap support is flagged in the machine results and does not establish zero population uncertainty.

| Condition | Representation | Family | Endpoint | Rate | 95% interval |
| --- | --- | --- | --- | ---: | --- |
| llama31_8b_cot | enriched | clarification | resolved_answer_correct | 0.000 | [0.000, 0.000] |
| llama31_8b_direct | enriched | clarification | resolved_answer_correct | 0.000 | [0.000, 0.000] |
| qwen3_32b_awq_off | enriched | clarification | resolved_answer_correct | 0.325 | [0.250, 0.400] |
| qwen3_32b_awq_on | enriched | clarification | resolved_answer_correct | 0.300 | [0.225, 0.400] |
| qwen3_32b_awq_on | structured_only | clarification | resolved_answer_correct | 0.325 | [0.225, 0.425] |
| qwen3_8b_direct | enriched | clarification | resolved_answer_correct | 0.100 | [0.025, 0.200] |
| qwen3_8b_direct | structured_only | clarification | resolved_answer_correct | 0.000 | [0.000, 0.000] |
| qwen3_8b_thinking | enriched | clarification | resolved_answer_correct | 0.250 | [0.150, 0.350] |
| llama31_8b_cot | enriched | counterfactual | typed_correct | 0.000 | [0.000, 0.000] |
| llama31_8b_direct | enriched | counterfactual | typed_correct | 0.175 | [0.100, 0.250] |
| qwen3_32b_awq_off | enriched | counterfactual | typed_correct | 0.075 | [0.000, 0.150] |
| qwen3_32b_awq_on | enriched | counterfactual | typed_correct | 0.175 | [0.099, 0.275] |
| qwen3_32b_awq_on | structured_only | counterfactual | typed_correct | 0.150 | [0.075, 0.225] |
| qwen3_8b_direct | enriched | counterfactual | typed_correct | 0.350 | [0.275, 0.450] |
| qwen3_8b_direct | structured_only | counterfactual | typed_correct | 0.275 | [0.250, 0.325] |
| qwen3_8b_thinking | enriched | counterfactual | typed_correct | 0.125 | [0.050, 0.225] |
| llama31_8b_cot | enriched | direct | typed_correct | 0.000 | [0.000, 0.000] |
| llama31_8b_direct | enriched | direct | typed_correct | 0.000 | [0.000, 0.000] |
| qwen3_32b_awq_off | enriched | direct | typed_correct | 0.725 | [0.675, 0.750] |
| qwen3_32b_awq_on | enriched | direct | typed_correct | 0.925 | [0.850, 1.000] |
| qwen3_32b_awq_on | structured_only | direct | typed_correct | 0.975 | [0.925, 1.000] |
| qwen3_8b_direct | enriched | direct | typed_correct | 0.200 | [0.100, 0.300] |
| qwen3_8b_direct | structured_only | direct | typed_correct | 0.000 | [0.000, 0.000] |
| qwen3_8b_thinking | enriched | direct | typed_correct | 0.525 | [0.400, 0.650] |
| llama31_8b_cot | enriched | explanation | structured_facts_all_correct | 0.300 | [0.175, 0.425] |
| llama31_8b_direct | enriched | explanation | structured_facts_all_correct | 0.150 | [0.050, 0.250] |
| qwen3_32b_awq_off | enriched | explanation | structured_facts_all_correct | 0.650 | [0.575, 0.725] |
| qwen3_32b_awq_on | enriched | explanation | structured_facts_all_correct | 0.525 | [0.375, 0.650] |
| qwen3_32b_awq_on | structured_only | explanation | structured_facts_all_correct | 0.625 | [0.500, 0.725] |
| qwen3_8b_direct | enriched | explanation | structured_facts_all_correct | 0.625 | [0.525, 0.700] |
| qwen3_8b_direct | structured_only | explanation | structured_facts_all_correct | 0.400 | [0.325, 0.475] |
| qwen3_8b_thinking | enriched | explanation | structured_facts_all_correct | 0.800 | [0.700, 0.900] |
| llama31_8b_cot | enriched | predictive | typed_correct | 0.000 | [0.000, 0.000] |
| llama31_8b_direct | enriched | predictive | typed_correct | 0.000 | [0.000, 0.000] |
| qwen3_32b_awq_off | enriched | predictive | typed_correct | 0.075 | [0.000, 0.150] |
| qwen3_32b_awq_on | enriched | predictive | typed_correct | 0.000 | [0.000, 0.000] |
| qwen3_32b_awq_on | structured_only | predictive | typed_correct | 0.025 | [0.000, 0.075] |
| qwen3_8b_direct | enriched | predictive | typed_correct | 0.125 | [0.050, 0.225] |
| qwen3_8b_direct | structured_only | predictive | typed_correct | 0.125 | [0.050, 0.225] |
| qwen3_8b_thinking | enriched | predictive | typed_correct | 0.000 | [0.000, 0.000] |

Typed endpoints require correct values with unchanged units/frames/tolerances, strict Boolean types and sign-invariant quaternion angular distance. Exact per-target validity, correctness and numerical errors are retained in the private item rows; unavailable/invalid errors are null, never zero. No cross-unit error pooling or answer repair is performed. Parsing and typed validity are separate from correctness. Explanation reports six structured facts (intervention, fixed conditions, two supplied readouts, exact equality and existing-scorer distinguishability); this does not establish semantic/prose adequacy. All clarification gap-recognition, slot-match, premature-answer, routing and resolved-answer endpoints are available in the machine results. Scientific failures and execution/interface failures remain separately visible.

## Matched representation ablations

Differences are structured-only minus enriched on the same selected QA/groups and pinned condition. Negative values favor enriched on that endpoint. No extra independent items are created by conditions or turns. The Qwen3-8B direct structured-only primary difference includes 35 power-loss missing responses as unsuccessful. That execution shortfall confounds interpretation as a pure language-enrichment effect; do not attribute its entire difference to input representation. The fixed denominator and paired uncertainty are preserved, with coverage and failure causes reported separately.

| Condition | Family | Endpoint | Difference | Paired 95% interval |
| --- | --- | --- | ---: | --- |
| qwen3_8b_direct | clarification | resolved_answer_correct | -0.100 | [-0.200, -0.025] |
| qwen3_32b_awq_on | clarification | resolved_answer_correct | +0.025 | [-0.050, +0.125] |
| qwen3_8b_direct | counterfactual | typed_correct | -0.075 | [-0.150, +0.000] |
| qwen3_32b_awq_on | counterfactual | typed_correct | -0.025 | [-0.150, +0.100] |
| qwen3_8b_direct | direct | typed_correct | -0.200 | [-0.300, -0.100] |
| qwen3_32b_awq_on | direct | typed_correct | +0.050 | [-0.025, +0.125] |
| qwen3_8b_direct | explanation | structured_facts_all_correct | -0.225 | [-0.250, -0.175] |
| qwen3_32b_awq_on | explanation | structured_facts_all_correct | +0.100 | [-0.075, +0.275] |
| qwen3_8b_direct | predictive | typed_correct | +0.000 | [+0.000, +0.000] |
| qwen3_32b_awq_on | predictive | typed_correct | +0.025 | [+0.000, +0.075] |

## Accounting, provenance and limits

Ashraf remaining allocation: 14883.368s. Collaborator allocation: 100800.000/100800s. Shared remaining: 115683.368/172800s. Unused Ashraf time is not automatically reassigned. Development ledgers and their historical failures remain separate. No second-machine completion schedule is measured or inferred.

Lifecycle accounting includes main preparation/preflight, package/artifact checks, loading, stages, teardown, measured dispatcher gaps and central work once. Generation and total-stage timings are nested process measurements, not additional charges. Unknown work retains its bound; observed overruns remain recorded. Final accounting/index receipt serialization follows the declared central timing boundary. Queue/transfer wait and software implementation are excluded. These are accounted work seconds, not measured GPU busy time. The prior 17.041h Ashraf estimate and original200-versus400 forecast remain preserved; this separately versioned report provides actual elapsed components.

Device-wide nvidia-smi memory is sampled at a requested0.5s interval and may miss peaks. Sample counts, timestamps, UUID, peak, errors and null/unavailable reasons are preserved. Torch process allocation is separate and can omit backend children. HF stop reasons are identified as derived token/EOS/deadline evidence; vLLM retains exposed backend reasons. No measured TTFT/prefill/decode split, inaccessible internal reasoning, GPU utilization integral or semantic refusal classifier is claimed.

Preservation checks cover 24340 existing frozen/historical files; all preserved: True. The core/pool, all 2,200 initial package requests, worker/settings, templates, model/tokenizer revisions, quantization, precision, cutoffs, source evidence, scorers and uncertainty plan remain unchanged. Fresh GPU/artifact/template/runtime and exact ModelConfig checks precede scientific reservation; reviewed qualification mappings are adopted only for their exact supported identities.

Condition comparisons concern the pinned artifacts and complete execution specifications. Model size, quantization/precision, backend, reasoning controls, decoding and output allowances differ across configured conditions; these results do not isolate a causal effect of scale or reasoning alone. Matched input ablations preserve the same condition settings and task facts, with the Qwen3-8B restart coverage limitation stated above. Unexecuted collaborator conditions remain unavailable.

Central allocation guards, immutable hash-once transaction indexing and the conservative conflicting-lifecycle import fix are separately versioned outside the sealed public package. 115 offline behavioral tests passed; the offline wheel build and byte-equality check passed. Sixteen restart/import/allocation regression checks (including three new recovery tests) passed after reboot. Earlier failed fixture expectations remain archived; no actual scientific attempt was retried. The earlier failing allocation test and corrected unexecuted analysis-draft syntax check remain archived. Actual main batch token/render/raw-output/memory/history/scoring-join verification receipts are separate empirical execution evidence.

## Prospective prose assessment and remaining work

The frozen eight-task enriched prose subset provides 48 available actual responses and 24 missing planned responses. P1/P2 forms are blank and uncollected. Private condition mappings stay separate. Review packets preserve returned words and parsed final objects; metadata blinding cannot prevent response wording from revealing reasoning mode. No human explanation-quality or annotation-acceptability result is claimed. The 140-item annotation audit remains a different study with pending feedback; explicit query-gap clarification supports no OOD claim.

The next execution work is collaborator qualification and separately authorized Gemma/DeepSeek issuance through the same ledger. Ashraf's reserved stages cannot be retried or replaced. No collaborator inference, paid annotation, simulation, new dataset generation or hosted answering occurs in this milestone.

## Inspectable evidence and commands

- [Execution freeze](<C:/Users/aashraf/.codex/visualizations/2026/10/06/01a1131b-eac2-7a31-afb4-f219a8dd6471/spq06/2026-10-09/main-ashraf-1.0.0/execution-freeze.json>)
- [First normal main-batch integrity gate](<C:/Users/aashraf/.codex/visualizations/2026/10/06/01a1131b-eac2-7a31-afb4-f219a8dd6471/spq06/2026-10-09/main-ashraf-1.0.0/first-main-batch-integrity.json>)
- [Central orchestration compatibility overlay](<C:/Users/aashraf/.codex/visualizations/2026/10/06/01a1131b-eac2-7a31-afb4-f219a8dd6471/spq06/2026-10-09/main-ashraf-1.0.0/orchestration-overlay-1.0.1.json>)
- [Actual status, timing, memory and runtime records](<C:/Users/aashraf/.codex/visualizations/2026/10/06/01a1131b-eac2-7a31-afb4-f219a8dd6471/spq06/2026-10-09/main-ashraf-1.0.0/delivery-1.0.0/actual-execution-results.json>)
- [Fixed-denominator items and paired uncertainty](<C:/Users/aashraf/.codex/visualizations/2026/10/06/01a1131b-eac2-7a31-afb4-f219a8dd6471/spq06/2026-10-09/main-ashraf-1.0.0/delivery-1.0.0/ashraf-fixed-denominator-analysis.json>)
- [Accounting and remaining shared-work forecast](<C:/Users/aashraf/.codex/visualizations/2026/10/06/01a1131b-eac2-7a31-afb4-f219a8dd6471/spq06/2026-10-09/main-ashraf-1.0.0/delivery-1.0.0/resource-accounting.json>)
- [Final offline actual-evidence checks](<C:/Users/aashraf/.codex/visualizations/2026/10/06/01a1131b-eac2-7a31-afb4-f219a8dd6471/spq06/2026-10-09/main-ashraf-1.0.0/delivery-1.0.0/final-offline-verification.json>)
- [Power-loss recovery and preserved interrupted evidence](<C:/Users/aashraf/.codex/visualizations/2026/10/06/01a1131b-eac2-7a31-afb4-f219a8dd6471/spq06/2026-10-09/main-ashraf-1.0.0/restart-recovery-1.0.0/recovery-receipt.json>)
- [Frozen-artifact preservation](<C:/Users/aashraf/.codex/visualizations/2026/10/06/01a1131b-eac2-7a31-afb4-f219a8dd6471/spq06/2026-10-09/main-ashraf-1.0.0/delivery-1.0.0/preservation-after.json>)
- [Per-file executed/reused/deterministic mapping](<C:/Users/aashraf/.codex/visualizations/2026/10/06/01a1131b-eac2-7a31-afb4-f219a8dd6471/spq06/2026-10-09/main-ashraf-1.0.0/delivery-1.0.0/per-file-procedure-index.json>)
- [File hashes](<C:/Users/aashraf/.codex/visualizations/2026/10/06/01a1131b-eac2-7a31-afb4-f219a8dd6471/spq06/2026-10-09/main-ashraf-1.0.0/delivery-1.0.0/file-index.json>)
- [Central parsed actual responses](<C:/Users/aashraf/.codex/visualizations/2026/10/06/01a1131b-eac2-7a31-afb4-f219a8dd6471/spq06/2026-10-09/main-ashraf-1.0.0/central-analysis-1.0.0/central-parsed-records.json>)
- [Prospective model-answer prose entry point](<C:/Users/aashraf/.codex/visualizations/2026/10/06/01a1131b-eac2-7a31-afb4-f219a8dd6471/spq06/2026-10-09/main-ashraf-1.0.0/model-prose-packets-1.0.0/README.md>)
- [Commands](<C:/Users/aashraf/.codex/worktrees/simphysqa/phi-jepa/docs/simphysqa/ashraf_main_commands.md>)
- [Collaborator handoff](<C:/Users/aashraf/.codex/worktrees/simphysqa/phi-jepa/docs/simphysqa/ashraf_main_handoff.md>)

Examples below use the first saved Qwen3-8B-direct enriched batch. They are inspection links, not an additional sample or selected by accuracy.

- predictive: 0534cc26662521d389782143e08923fd — [exact executed request](<C:/Users/aashraf/.codex/visualizations/2026/10/06/01a1131b-eac2-7a31-afb4-f219a8dd6471/spq06/2026-10-09/main-ashraf-1.0.0/jobs/001--qwen3_8b_direct--enriched--stage1/worker-output/executed-requests/0534cc26662521d389782143e08923fd-stage1.json>), [raw actual response](<C:/Users/aashraf/.codex/visualizations/2026/10/06/01a1131b-eac2-7a31-afb4-f219a8dd6471/spq06/2026-10-09/main-ashraf-1.0.0/jobs/001--qwen3_8b_direct--enriched--stage1/worker-output/results/0534cc26662521d389782143e08923fd-stage1.json>)
- clarification: spq-clarification-03f99fd543cae50855906c0e — [exact executed request](<C:/Users/aashraf/.codex/visualizations/2026/10/06/01a1131b-eac2-7a31-afb4-f219a8dd6471/spq06/2026-10-09/main-ashraf-1.0.0/jobs/001--qwen3_8b_direct--enriched--stage1/worker-output/executed-requests/spq-clarification-03f99fd543cae50855906c0e-stage1.json>), [raw actual response](<C:/Users/aashraf/.codex/visualizations/2026/10/06/01a1131b-eac2-7a31-afb4-f219a8dd6471/spq06/2026-10-09/main-ashraf-1.0.0/jobs/001--qwen3_8b_direct--enriched--stage1/worker-output/results/spq-clarification-03f99fd543cae50855906c0e-stage1.json>)
- counterfactual: spq-counterfactual-2fd07975772b169be50f92f0 — [exact executed request](<C:/Users/aashraf/.codex/visualizations/2026/10/06/01a1131b-eac2-7a31-afb4-f219a8dd6471/spq06/2026-10-09/main-ashraf-1.0.0/jobs/001--qwen3_8b_direct--enriched--stage1/worker-output/executed-requests/spq-counterfactual-2fd07975772b169be50f92f0-stage1.json>), [raw actual response](<C:/Users/aashraf/.codex/visualizations/2026/10/06/01a1131b-eac2-7a31-afb4-f219a8dd6471/spq06/2026-10-09/main-ashraf-1.0.0/jobs/001--qwen3_8b_direct--enriched--stage1/worker-output/results/spq-counterfactual-2fd07975772b169be50f92f0-stage1.json>)
- direct: spq-direct-206c7f87e84d5dbae22cf223 — [exact executed request](<C:/Users/aashraf/.codex/visualizations/2026/10/06/01a1131b-eac2-7a31-afb4-f219a8dd6471/spq06/2026-10-09/main-ashraf-1.0.0/jobs/001--qwen3_8b_direct--enriched--stage1/worker-output/executed-requests/spq-direct-206c7f87e84d5dbae22cf223-stage1.json>), [raw actual response](<C:/Users/aashraf/.codex/visualizations/2026/10/06/01a1131b-eac2-7a31-afb4-f219a8dd6471/spq06/2026-10-09/main-ashraf-1.0.0/jobs/001--qwen3_8b_direct--enriched--stage1/worker-output/results/spq-direct-206c7f87e84d5dbae22cf223-stage1.json>)
- explanation: spq-explanation-215ad23dd08aaf8dd42e5bc8 — [exact executed request](<C:/Users/aashraf/.codex/visualizations/2026/10/06/01a1131b-eac2-7a31-afb4-f219a8dd6471/spq06/2026-10-09/main-ashraf-1.0.0/jobs/001--qwen3_8b_direct--enriched--stage1/worker-output/executed-requests/spq-explanation-215ad23dd08aaf8dd42e5bc8-stage1.json>), [raw actual response](<C:/Users/aashraf/.codex/visualizations/2026/10/06/01a1131b-eac2-7a31-afb4-f219a8dd6471/spq06/2026-10-09/main-ashraf-1.0.0/jobs/001--qwen3_8b_direct--enriched--stage1/worker-output/results/spq-explanation-215ad23dd08aaf8dd42e5bc8-stage1.json>)

Package manifest SHA256: `722276ecb67b851ef9c8de0563ee074c83c2b1493727e3a25fc0f95bb3981094`.

## Output-interface reporting caveat

The unchanged analysis uses the legacy label `parsing: not_completed` both for
noncompleted generations and completed generations whose final JSON cannot be
parsed. Use completion status and parser diagnostics together. This label must not
be interpreted as a measured generation failure by itself. The frozen parser accepts
a unique JSON suffix and wholly fenced JSON, but rejects prose followed by a final
fenced JSON block with trailing backticks. A manifest-first Llama direct inspection
shows this format. Rejected text remains unscored numerically; no fence removal,
answer repair, parser change or rescoring is performed. The reported endpoints are
end-to-end outcomes under this frozen output/parser contract.

| Condition | Representation | Parsed JSON first turns | Completed first turns rejected by parser | Family-specific answer_valid flags |
| --- | --- | ---: | ---: | ---: |
| qwen3_8b_direct | enriched | 199 | 0 | 193 |
| qwen3_8b_thinking | enriched | 200 | 0 | 129 |
| llama31_8b_direct | enriched | 78 | 121 | 35 |
| llama31_8b_cot | enriched | 78 | 122 | 23 |
| qwen3_32b_awq_off | enriched | 200 | 0 | 169 |
| qwen3_32b_awq_on | enriched | 200 | 0 | 126 |
| qwen3_8b_direct | structured_only | 165 | 0 | 155 |
| qwen3_32b_awq_on | structured_only | 200 | 0 | 135 |

All columns retain 200 selected first-turn items. The answer_valid flag has the
existing family-specific definition; clarification first-turn contract validity is
separate from resolved-answer validity and correctness. Explanation schema/factual
flags do not measure prose adequacy. Typed numerical error summaries use only
available valid targets, with primary coverage and failures retained alongside.

The immutable central parsed records retain response objects, diagnostic messages,
parser/scorer identities and source-record hashes. The readable table above clarifies
the legacy label; it changes no stored field, endpoint or uncertainty estimate.

## Offline verification receipts

- [115 behavioral checks](<C:/Users/aashraf/.codex/visualizations/2026/10/06/01a1131b-eac2-7a31-afb4-f219a8dd6471/spq06/2026-10-09/main-offline-1.0.3.log>)
- [16 restart/import/allocation checks](<C:/Users/aashraf/.codex/visualizations/2026/10/06/01a1131b-eac2-7a31-afb4-f219a8dd6471/spq06/2026-10-09/main-restart-offline-1.0.3.log>)
- [Temporary prose-form compatibility fixture](<C:/Users/aashraf/.codex/visualizations/2026/10/06/01a1131b-eac2-7a31-afb4-f219a8dd6471/spq06/2026-10-09/main-prose-offline-1.0.2.log>)
- [Original five-helper wheel byte check](<C:/Users/aashraf/.codex/visualizations/2026/10/06/01a1131b-eac2-7a31-afb4-f219a8dd6471/spq06/2026-10-09/main-wheel-verification-1.0.0.json>)
- [Executed central analysis command and lifecycle](<C:/Users/aashraf/.codex/visualizations/2026/10/06/01a1131b-eac2-7a31-afb4-f219a8dd6471/spq06/2026-10-09/main-analysis-execution-1.0.0.log.command.json>)

The original wheel check predates the recovery module; recovery is committed as
additional central editable source and has separate behavioral checks. Normal-exit
NCCL cleanup warnings remain in raw logs; their returns passed import/integrity
verification. No warning caused a scientific retry.

The default whitespace check flags one trailing space in the exact archived
executed finish_main.py source. Its bytes/hash are preserved. The maintained-source
and documentation diff check passes with archived procedure snapshots excluded;
this exception changes no scientific behavior.
