# SPQ06 authorized remaining-200 execution

Branch `simphysqa-spq06`; execution implementation commit `bcf5ee7`, base `239cda5`. This report is committed locally with the final documentation commit; its exact identity is recorded in the external post-commit receipt. The branch remains unmerged and unpushed.

The user explicitly authorized the eight frozen Ashraf combinations and prospectively revised cumulative Ashraf/shared ceilings to 126,000/226,800 seconds. Collaborator allocation remains 100,800 seconds. The same central ledger retains all prior charges, decisions and the historical 6,600-second unknown process charge. The result-import cutoff was explicitly revised to 2026-10-13 02:00 UTC (October 12, 21:00 Chicago), leaving 9h59 before the official submission deadline.

The complement is exactly 200 frozen QA and distinct original trajectory groups, ten per domain–family cell and forty per family. Core and complement are disjoint from each other and the frozen development/audit/prompt-use exclusions. No score-based selection, substitution, retry, new data, annotation, simulation or collaborator inference occurred. Expansion was authorized after core results were available.

## Actual coverage

All eight combination coverage/accounting checks complete: **True**. Canonical failures remain assigned outcomes. Unsupported clarification routes are explicitly unexecuted, rather than authored continuations.

| Condition | Representation | Initials | Supported continuations / imported | Unexecuted conditional | Coverage complete |
|---|---|---:|---:|---:|---|
| qwen3_8b_direct | enriched | 200/200 | 39 / 39 | 1 | True |
| qwen3_8b_thinking | enriched | 200/200 | 37 / 37 | 3 | True |
| llama31_8b_direct | enriched | 200/200 | 39 / 39 | 1 | True |
| llama31_8b_cot | enriched | 200/200 | 19 / 19 | 21 | True |
| qwen3_32b_awq_off | enriched | 200/200 | 40 / 40 | 0 | True |
| qwen3_32b_awq_on | enriched | 200/200 | 40 / 40 | 0 | True |
| qwen3_8b_direct | structured_only | 200/200 | 40 / 40 | 0 | True |
| qwen3_32b_awq_on | structured_only | 200/200 | 39 / 39 | 1 | True |

| Condition | Input | Existing latency_seconds total (s) | Total stage timing (s) | Sampled device peak (MiB) | Successful stage samples |
|---|---|---:|---:|---:|---:|
| qwen3_8b_direct | enriched | 2097.584 | 2104.664 | 31482 | 3942 |
| qwen3_8b_thinking | enriched | 7642.452 | 7649.657 | 31639 | 14317 |
| llama31_8b_direct | enriched | 1844.398 | 1850.795 | 28085 | 3460 |
| llama31_8b_cot | enriched | 1991.562 | 1997.574 | 27857 | 3721 |
| qwen3_32b_awq_off | enriched | 3385.746 | 3394.567 | 32009 | 6148 |
| qwen3_32b_awq_on | enriched | 10028.494 | 10037.283 | 32103 | 15973 |
| qwen3_8b_direct | structured_only | 1967.393 | 1974.304 | 29319 | 3453 |
| qwen3_32b_awq_on | structured_only | 11285.025 | 11293.429 | 32020 | 8329 |

| Executor | Cumulative accounted (s) | Ceiling (s) | Remaining (s) |
|---|---:|---:|---:|
| Ashraf | 110569.238 | 126000.000 | 15430.762 |
| Collaborator | 0.000 | 100800.000 | 100800.000 |

Shared accounted 110569.238 / 226800.000 seconds; remaining 116230.762. This snapshot follows analysis settlement; any final documentation/verification control has a separately saved subsequent accounting receipt.

42 complement process reservations; 42 measured lifecycle receipts totaling 50704.247 seconds. Worker model-construction/load_seconds is available in 42 runtime receipts, totaling 334.055 seconds. These loading and stage timings are nested within lifecycle work and are not added to cumulative accounting again.

The existing latency_seconds field covers generation, output decoding and CUDA synchronization in these unchanged workers. It is not a separate decode or prefill measurement. Total-stage timing additionally covers rendering/tokenization and response processing according to the frozen instrumentation boundaries.

## Forecast and calendar reconciliation

Analysis-settled cumulative increment over the last verified core/recovery accounting point (58172.897 seconds) is 52396.341 accounted seconds. This includes central work and the retained unknown routing-control reservation; it is not pure GPU kernel time. The original component forecast was 51,995.106 seconds plus 25% reserve (64,993.882 seconds). The separately preserved historical-repeat estimate was 51,572.897 seconds plus 25% reserve (64,466.121 seconds). Forecasts were estimates, never enlarged hard ceilings.

[Original live forecast](<C:/Users/aashraf/.codex/visualizations/2026/10/06/01a1131b-eac2-7a31-afb4-f219a8dd6471/spq06/2026-10-09/complement-execution-1.0.0/forecast-before.json>) is the core-only historical basis. In the preserved forecast-after-budget artifact, its historical-repeat field includes the prospectively held 3,600-second final-analysis reservation; that field is not a clean core-only repeat prediction. Its separately computed component forecast and the original pre-revision historical estimate remain the interpretable estimates. The artifact is preserved rather than rewritten.

The controller reduced final initial batches to 48, 41 and 11 and conditional batches to 35 plus four according to budget/calendar capacity, retaining frozen order. [Analysis completion timestamp](<C:/Users/aashraf/.codex/visualizations/2026/10/06/01a1131b-eac2-7a31-afb4-f219a8dd6471/spq06/2026-10-09/complement-analysis-1.0.1/manifest.json>) records actual return/import/analysis completion before the approved 02:00 UTC cutoff. No further Ashraf main work remains in this authorized complement. No two-machine completion forecast is asserted without collaborator measurements.


## Evidence and scientific results

[Paper tables and paired ablations](<C:/Users/aashraf/.codex/visualizations/2026/10/06/01a1131b-eac2-7a31-afb4-f219a8dd6471/spq06/2026-10-09/complement-analysis-1.0.1/paper-results.md>). [Core 200](<C:/Users/aashraf/.codex/visualizations/2026/10/06/01a1131b-eac2-7a31-afb4-f219a8dd6471/spq06/2026-10-09/complement-analysis-1.0.1/core-analysis.json>), [complement 200](<C:/Users/aashraf/.codex/visualizations/2026/10/06/01a1131b-eac2-7a31-afb4-f219a8dd6471/spq06/2026-10-09/complement-analysis-1.0.1/complement-analysis.json>), [combined 400](<C:/Users/aashraf/.codex/visualizations/2026/10/06/01a1131b-eac2-7a31-afb4-f219a8dd6471/spq06/2026-10-09/complement-analysis-1.0.1/combined-analysis.json>). All assigned items remain in primary denominators. Combined intervals are recomputed from union records with twenty whole groups per domain–family stratum, 10,000 paired replicates and unchanged seed 20261009; CI endpoints are never averaged. Unexpanded conditions require common-core comparisons.

[Central parsed records and scoring joins](<C:/Users/aashraf/.codex/visualizations/2026/10/06/01a1131b-eac2-7a31-afb4-f219a8dd6471/spq06/2026-10-09/complement-analysis-1.0.1/central-parsed-records.json>), [complement diagnostics](<C:/Users/aashraf/.codex/visualizations/2026/10/06/01a1131b-eac2-7a31-afb4-f219a8dd6471/spq06/2026-10-09/complement-analysis-1.0.1/complement-diagnostics.json>), [core diagnostics](<C:/Users/aashraf/.codex/visualizations/2026/10/06/01a1131b-eac2-7a31-afb4-f219a8dd6471/spq06/2026-10-09/complement-analysis-1.0.1/core-diagnostics.json>). Diagnostics distinguish generation noncompletion, JSON parsing, schema/type/unit/frame invalidity and valid-but-incorrect answers separately from primary scoring. Clarification first-turn and continuation validity remain separate. Human explanation prose adequacy is uncollected; automatic factual checks are not prose quality. Explicit query gaps establish no OOD claim.

## Integrity, timing and operational limitations

[Actual coverage, timing/tokens and sampled memory](<C:/Users/aashraf/.codex/visualizations/2026/10/06/01a1131b-eac2-7a31-afb4-f219a8dd6471/spq06/2026-10-09/complement-analysis-1.0.1/coverage.json>), [final accounting](<C:/Users/aashraf/.codex/visualizations/2026/10/06/01a1131b-eac2-7a31-afb4-f219a8dd6471/spq06/2026-10-09/complement-analysis-1.0.1/final-accounting.json>), [original ledger-row preservation](<C:/Users/aashraf/.codex/visualizations/2026/10/06/01a1131b-eac2-7a31-afb4-f219a8dd6471/spq06/2026-10-09/complement-analysis-1.0.1/original-ledger-preservation.json>). Process lifecycle and dispatcher overhead are charged once; nested stage/loading timings are not added again. Unknown charges retain full bounds. Device memory is a sampled device-wide high-water mark and can miss peaks; missing measurements are unavailable, not zero. Separate prefill/decode/TTFT and semantic refusal are not asserted as measured.

[Latest delivery settlement](<C:/Users/aashraf/.codex/visualizations/2026/10/06/01a1131b-eac2-7a31-afb4-f219a8dd6471/spq06/2026-10-09/complement-execution-1.0.0/final-delivery-1.0.0.json>) adds the separately reserved final preservation/documentation verification controls to the preceding analysis accounting snapshot.

The first normal fifty-item Qwen3-8B enriched batch passed actual return/import, token rendering, raw-output, measurement and central scoring-join checks. Routing then exposed a missing coordinator configuration in the first source snapshot. Exact existing configuration files were added in a separate coordinator snapshot; saved first responses were checked and routed without repeating any scientific stage. The original failure/pause record and full 600-second unknown central charge remain. Scientific worker/rendering/scoring behavior was unchanged.

The outer monitoring shell ended with a Get-Content error caused by its log-tail path using 2026/10/09 instead of 2026-10-09. The actual serial controller log, execution-completion receipt and every immutable import establish successful controller completion. This log-tail error caused no model rerun or stage reservation.

[First batch integrity receipt](<C:/Users/aashraf/.codex/visualizations/2026/10/06/01a1131b-eac2-7a31-afb4-f219a8dd6471/spq06/2026-10-09/complement-execution-1.0.0/first-main-batch-integrity.json>), [dependency-only repair disposition](<C:/Users/aashraf/.codex/visualizations/2026/10/06/01a1131b-eac2-7a31-afb4-f219a8dd6471/spq06/2026-10-09/complement-execution-1.0.0/coordinator-repair-disposition-1.0.1.json>), [analysis source/core equivalence](<C:/Users/aashraf/.codex/visualizations/2026/10/06/01a1131b-eac2-7a31-afb4-f219a8dd6471/spq06/2026-10-09/complement-execution-1.0.0/analysis-source-equivalence-1.0.1.json>). Actual immutable imports and all fresh metadata/artifact/template/ModelConfig proofs remain in [execution root](<C:/Users/aashraf/.codex/visualizations/2026/10/06/01a1131b-eac2-7a31-afb4-f219a8dd6471/spq06/2026-10-09/complement-execution-1.0.0>).

[Final historical hash preservation check](<C:/Users/aashraf/.codex/visualizations/2026/10/06/01a1131b-eac2-7a31-afb4-f219a8dd6471/spq06/2026-10-09/complement-execution-1.0.0/final-preservation-1.0.1.json>) compares the preserved pre-recovery artifact inventory, execution freeze and original source/manifests. Mutable central ledger files are excluded from file hashing and checked by immutable original-row preservation instead. The first helper incorrectly addressed the identities map as hashes and failed before checking files; its log and full 300-second unknown reservation remain. The separately versioned corrected helper used the actual saved key.

## Delivery and verification

[Private audit bundle](<C:/Users/aashraf/.codex/visualizations/2026/10/06/01a1131b-eac2-7a31-afb4-f219a8dd6471/spq06/2026-10-09/complement-analysis-1.0.1/audit-bundle-1.0.0.zip>), [analysis manifest and file hashes](<C:/Users/aashraf/.codex/visualizations/2026/10/06/01a1131b-eac2-7a31-afb4-f219a8dd6471/spq06/2026-10-09/complement-analysis-1.0.1/manifest.json>). Exact request/raw examples are in [examples](<C:/Users/aashraf/.codex/visualizations/2026/10/06/01a1131b-eac2-7a31-afb4-f219a8dd6471/spq06/2026-10-09/complement-analysis-1.0.1/exact-examples>). The public sealed base and complement overlay stay external; private evidence is not committed.

Fifty relevant offline implementation tests, sixteen focused post-repair checks and five analysis fixtures passed. The 1,600 core item-condition rows were independently recomputed and their endpoints, completion, parsing and validity matched the original recovered analysis exactly. Original fixture/failure logs remain preserved; mock outputs are not inference evidence. See [offline logs](<C:/Users/aashraf/.codex/visualizations/2026/10/06/01a1131b-eac2-7a31-afb4-f219a8dd6471/spq06/2026-10-09/complement-live-offline-1.1.1.log>), [post-repair tests](<C:/Users/aashraf/.codex/visualizations/2026/10/06/01a1131b-eac2-7a31-afb4-f219a8dd6471/spq06/2026-10-09/complement-postrepair-offline-1.0.0.log>), [analysis fixtures](<C:/Users/aashraf/.codex/visualizations/2026/10/06/01a1131b-eac2-7a31-afb4-f219a8dd6471/spq06/2026-10-09/complement-analysis-fixtures-1.0.1.log>).

The paper text describes the scientific protocol, actual balanced coverage and post-core expansion timing. Operational interruption/recovery/accounting history remains in execution records. No collaborator conditions or human ratings are inferred. No further answering is launched by this completion report.

## Final reporting and recovery-preservation addendum

The [reporting diagnostics](<C:/Users/aashraf/.codex/visualizations/2026/10/06/01a1131b-eac2-7a31-afb4-f219a8dd6471/spq06/2026-10-09/complement-closure-1.0.1/paper-diagnostics.md>) accompany the scientific tables, without operational interruption history. They separately enumerate first-stage generation/JSON/schema failures, valid-but-incorrect answers and clarification continuation categories. Eight noncomplete generations across core plus complement retain their primary denominators (six occur in the complement). Five complement stage memory monitors report unavailable status; none was converted to measured zero.

The paired 400-item contrasts are structured-only minus enriched. For Qwen3-8B direct, direct correctness falls 15.0 pp (paired 95% interval [-22.5, -7.5]) and resolved clarification falls 7.5 pp ([-13.7, -2.5]); predictive correctness is unchanged. For Qwen3-32B thinking, the direct contrast is +5.0 pp ([-1.2, 11.3]), and the resolved-clarification contrast is 0.0 pp ([-5.0, 5.0]). All family comparisons remain available in the tables; these mixed results support no blanket enrichment benefit. The intervals are descriptive, marginal and not multiplicity-adjusted. Automatic explanation factual scores do not grade prose quality.

[Recovery preservation proof](<C:/Users/aashraf/.codex/visualizations/2026/10/06/01a1131b-eac2-7a31-afb4-f219a8dd6471/spq06/2026-10-09/complement-closure-1.0.1/recovered-core-preservation.json>) verifies all 4,607 files in the recovery post-commit index and both raw-result hash fields for each of Ashraf's 1,600 core item-condition rows. There are no mismatches. These checks complement the 40,037 pre-recovery/source-freeze file checks and original-ledger-row preservation; overlapping inventories are not summed as unique scientific records.

The first closure helper also failed: it attempted to compare unexecuted collaborator placeholders in the historical all-condition analysis with the Ashraf-only analysis. The corrected /1.0.1 helper explicitly filters the frozen eight authorized combinations. The /1.0.0 source/log and full 300-second unknown reservation remain. This was a reporting helper correction, not a changed scorer, skipped Ashraf result or scientific retry.

[Accounting/audit addendum](<C:/Users/aashraf/.codex/visualizations/2026/10/06/01a1131b-eac2-7a31-afb4-f219a8dd6471/spq06/2026-10-09/complement-closure-1.0.1/audit-addendum.zip>), [closure manifest](<C:/Users/aashraf/.codex/visualizations/2026/10/06/01a1131b-eac2-7a31-afb4-f219a8dd6471/spq06/2026-10-09/complement-closure-1.0.1/manifest.json>) and [settled closure accounting](<C:/Users/aashraf/.codex/visualizations/2026/10/06/01a1131b-eac2-7a31-afb4-f219a8dd6471/spq06/2026-10-09/complement-closure-1.0.1/accounting.json>) are separately exported, preserving the sealed main audit ZIP. Final local review/commit accounting and exact commit identity are in the post-commit receipt. No models, datasets, prompts, scoring tolerances, observers or split identities changed.

Subsequent commits 49adc36 and 205a04f were inspected and preserved before this
completion commit. Supplied collaborator native metadata is audited separately;
its noncentral reservation/approval blockers are unchanged. Zero centrally adopted
collaborator accounting is not a claim that no native work happened elsewhere.
