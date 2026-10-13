# SPQ06 — Ashraf development rehearsal, 10 October 2026

Implemented and executed with an honest qualification shortfall. 25 initials and 4 actual continuations returned;15 AWQ initials were reserved but startup failed before answering. No scientific retry, replacement, prompt change or main inference occurred. The original 40 condition/item rows remain the diagnostic denominator. This is execution qualification, not a benchmark quality estimate.

Branch `simphysqa-spq06`; clean starting parent `a1dd726b32fe4dc958dffb49b9bcc8ea0c21e765`. No later commits or user edits were present at start. Final local commit/state: [post-commit receipt](C:/Users/aashraf/.codex/visualizations/2026/10/06/01a1131b-eac2-7a31-afb4-f219a8dd6471/spq06/2026-10-09/development-rehearsal-1.0.3/delivery-1.0.2/final-commit-receipt.json). No merge/rebase/push.

The five accepted train items are the unchanged selection in rehearsal-proposal-1.0.0. Every assigned representation used exactly those items through the exact main projection.40 source request files were independently reconstructed only for offline comparison against the saved bytes; the saved bytes were used for execution. The main 200-item core and enclosing 400-item pool, all nine enriched conditions, both ablation conditions, exclusions, cutoffs, schemas, scorers and original requests remain unchanged.

| Family | Domain | QA ID | Original trajectory group |
|---|---|---|---|
| direct | robotic_arm | `spq-direct-06749fe8a9f9c2ac6524d3bf` | `e5b3e572a3a3ae69523f12a8aeb6f616` |
| predictive | driving | `e52c5e8391589681cf355d960fb8f185` | `09fae68d427585369e6be2bee1ce4441` |
| counterfactual | object_pushing_stacking | `spq-counterfactual-68a75d394cefe37a0d48a30c` | `de7550b6e98df7e249dc3c44f1874120` |
| explanation | tethered_load | `spq-explanation-183d115cb9d68114d96538c4` | `3c44b44c4f41c3e7b89ffb6ab352a9a3` |
| clarification | robotic_arm | `spq-clarification-ce09635e16f3584d4a6228d0` | `a9563dc9343a2c57b624ae5048f3216a` |

The 40 request instances represent five unique development QA/groups, not 40 independent QA items. Collaborator Gemma/DeepSeek conditions were not run, loaded or assigned here.

## Actual execution and qualification

| Condition | Representation | Completed initials /5 | Reserved startup failures | Actual completed continuation /1 | Generation s | Task-stage total s | Lifecycle s | Sampled peak MiB |
|---|---|---:|---:|---:|---:|---:|---:|---:|
| `llama31_8b_cot` | enriched | 5 | 0 | 0 | 59.723 | 59.875 | 77.749 | 22562 |
| `llama31_8b_direct` | enriched | 5 | 0 | 1 | 41.977 | 42.166 | 81.373 | 22476 |
| `qwen3_32b_awq_off` | enriched | 0 | 5 | 0 | unavailable | unavailable | 31.096 | unavailable |
| `qwen3_32b_awq_on` | enriched | 0 | 5 | 0 | unavailable | unavailable | 19.485 | unavailable |
| `qwen3_32b_awq_on` | structured_only | 0 | 5 | 0 | unavailable | unavailable | 20.210 | unavailable |
| `qwen3_8b_direct` | enriched | 5 | 0 | 1 | 50.036 | 50.263 | 96.823 | 23786 |
| `qwen3_8b_direct` | structured_only | 5 | 0 | 1 | 46.698 | 46.897 | 75.824 | 23466 |
| `qwen3_8b_thinking` | enriched | 5 | 0 | 1 | 209.125 | 209.347 | 238.975 | 23774 |

The four actual continuations are Qwen8 direct enriched/structured-only, Qwen8 thinking enriched and Llama direct enriched. Their original first responses were retained verbatim. Llama CoT emitted a relevant question but `requested_information:null`; the unchanged router marked it unroutable. Its authored reference question was never inserted. Three AWQ condition/representation stages had no actual first response, so explicit unexecuted-conditional receipts contain `actual_raw:null`. No stage2 qualification is claimed for these four combinations.

All 29 returned stages have `completed` termination;22 have an accepted final JSON suffix and 7 retain `missing_or_ambiguous_final_JSON_object` parser failures. These are model/interface outcomes, not orchestration repairs or a quality acceptance gate. Correctness and target-level details are organizer-only in the central analysis. Automatic explanation fact checks do not judge prose. No refusal/internal-reasoning/prose metric was invented.

The three AWQ batches failed in vLLM 0.11 ModelConfig before loading/answering because its device utility parses CUDA visibility as an integer. The initial adapter supplied a UUID. The queue continued through all three before this was diagnosed; all15 initial stage reservations remain immutable and cannot resume. The original traceback/logs, invalid returns and import reasons are preserved. The failure is execution infrastructure, not15 scored model answers.

A separately reserved startup-only probe with verified `index0 → GPU-33a65a33-cb7a-f2f9-5697-93b058670d4b` passed. It loaded the same pinned AWQ model using the identical LLM constructor, explicit `quantization=awq`, FP16,32768 context, eager mode and .89 GPU fraction. Backend initialization/profiling/warmup occurred; no generate/add_request/step task call occurred. Constructor/loading took17.646s, full lifecycle52.562s, sampled device peak30586MiB with52 successful .5s samples. This demonstrates load compatibility only; AWQ task/decode/stop/dialogue qualification remains blocked.

## Budget and logging

Measured13 actual worker lifecycles total694.096s, including successful per-shard metadata preflight charged once. Two abandoned pre-weight metadata-only preflights lacked fully saved outer lifecycle timing; each retains a conservative600s unknown overhead charge. The central ledger therefore accounts **1894.096 /20400s**, leaving **18505.904s**. Conservative process reservations are15/16:13 actual worker launches plus those2 overhead charges.40 initials and 4 continuations were reserved;25+4 actual answering calls returned. The 8 conditional opportunities have4 executed and 4 explicit unexecuted receipts. Unused time does not authorize retrying reserved stages.

Generation latency keeps the historical boundary. Total-stage timing begins before seed/render/tokenization and ends at result construction, excluding final file write. Lifecycle includes preparation, executor verification, imports, model loading, all stages and process teardown once; transfer/queue wait is excluded. Loading is separately recorded and must not be added again to lifecycle. Device memory is nvidia-smi device-wide memory.used at .5s, with samples/errors/count/source/UUID; it is a sampled high-water mark that may miss peaks. Torch allocated/reserved peaks remain separate and exclude vLLM children. AWQ failed-task timing/memory/token fields are null/unavailable, never measured zero. TTFT, prefill/decode separation and semantic refusal are unavailable.

## Versions, immutable evidence and checks

Actual answering used coordinator `SPQ06-development/1.0.1` in [sealed executed package](C:/Users/aashraf/.codex/visualizations/2026/10/06/01a1131b-eac2-7a31-afb4-f219a8dd6471/spq06/2026-10-09/development-public-1.0.2/package-manifest.json) and exact instrumented workers/support `SPQ06-execution/1.0.0` from readiness. Final additive repaired coordinator is `SPQ06-development/1.0.4` in [repaired package manifest](C:/Users/aashraf/.codex/visualizations/2026/10/06/01a1131b-eac2-7a31-afb4-f219a8dd6471/spq06/2026-10-09/development-public-1.0.5/package-manifest.json). Worker generation/rendering code and scientific condition files did not change. The revised binding preflight has fresh configuration/load evidence, not fresh AWQ answering evidence. Older packages and failed preflights remain intact.

The new development issuer/launcher uses `--authorize-development`, runtime-qualified bootstrap receipts, one central SQLite ledger and explicit assignment filters. Main issuers/importers retain their main-only gates and reject development returns. No `--authorize-main` workaround was used. HF cache symlinks resolve only inside the explicit cache and still require exact digests. vLLM now requires numeric visibility with both nvidia-smi index/UUID and Torch selected UUID proof, plus pre-weight ModelConfig construction. Hardware/revisions/precision are checked, not substituted. Unknown/interrupted work retains full reservation/overrun; never-reserved-only resume remains enforced.

Actual returns were copied into exclusive immutable source roots and every file hash was validated.29 canonical actual records;15 invalid startup returns; no duplicate/conflicting real records. Central accepted parser/scorer outputs include original parsed objects, diagnostics/failures and source-version hashes. Final analysis has the exact same40 rows and 29 parsed objects as the prior sealed analysis, while adding complete conditional/accounting receipts.

62 offline behavioral tests passed before answering weights were loaded. Final68 tests passed, including scope rejection, assignment overlap, aggregate/orphan accounting, qualified binding proof, failed/partial preservation, immutable duplicates/conflicts, actual-history stage2 import, null memory and scoring compatibility. Earlier fixture/preflight failures are retained. Tokenizer-only verification reproduced all29 actual prompts/token IDs and decoded raw outputs, verified memory samples and timing, and checked actual continuation history. No weight/inference was used by that verifier. All 13291 relevant preexisting hash entries remain unchanged.

- [actual counts, configuration/worker hashes and measurements](C:/Users/aashraf/.codex/visualizations/2026/10/06/01a1131b-eac2-7a31-afb4-f219a8dd6471/spq06/2026-10-09/development-rehearsal-1.0.3/delivery-1.0.2/actual-results.json)
- [organizer-only parsed/scored40-row analysis](C:/Users/aashraf/.codex/visualizations/2026/10/06/01a1131b-eac2-7a31-afb4-f219a8dd6471/spq06/2026-10-09/development-rehearsal-1.0.3/analysis-1.0.1/development-analysis.json)
- [immutable answering-return source roots](C:/Users/aashraf/.codex/visualizations/2026/10/06/01a1131b-eac2-7a31-afb4-f219a8dd6471/spq06/2026-10-09/development-rehearsal-1.0.3/immutable-imports)
- [immutable startup-only import receipt](C:/Users/aashraf/.codex/visualizations/2026/10/06/01a1131b-eac2-7a31-afb4-f219a8dd6471/spq06/2026-10-09/development-rehearsal-1.0.3/startup-import-receipt-1.0.0.json)
- [29 actual tokenizer/output/memory checks](C:/Users/aashraf/.codex/visualizations/2026/10/06/01a1131b-eac2-7a31-afb4-f219a8dd6471/spq06/2026-10-09/development-rehearsal-1.0.3/actual-token-output-verification-1.0.0.json)
- [unchanged scoring/parsing compatibility](C:/Users/aashraf/.codex/visualizations/2026/10/06/01a1131b-eac2-7a31-afb4-f219a8dd6471/spq06/2026-10-09/development-rehearsal-1.0.3/analysis-compatibility-1.0.0.json)
- [68 passing offline checks](C:/Users/aashraf/.codex/visualizations/2026/10/06/01a1131b-eac2-7a31-afb4-f219a8dd6471/spq06/2026-10-09/development-offline-tests-final-1.0.3.log)
- [before hashes](C:/Users/aashraf/.codex/visualizations/2026/10/06/01a1131b-eac2-7a31-afb4-f219a8dd6471/spq06/2026-10-09/development-rehearsal-1.0.3/preservation-before.json) / [after hashes](C:/Users/aashraf/.codex/visualizations/2026/10/06/01a1131b-eac2-7a31-afb4-f219a8dd6471/spq06/2026-10-09/development-rehearsal-1.0.3/preservation-after.json)
- [exact actual executor commands](C:/Users/aashraf/.codex/visualizations/2026/10/06/01a1131b-eac2-7a31-afb4-f219a8dd6471/spq06/2026-10-09/development-rehearsal-1.0.3/delivery-1.0.2/commands.json)
- [pre-inference selection/code/settings/limits freeze](C:/Users/aashraf/.codex/visualizations/2026/10/06/01a1131b-eac2-7a31-afb4-f219a8dd6471/spq06/2026-10-09/development-rehearsal-1.0.3/execution-freeze.json)
- [retained unknown metadata overhead](C:/Users/aashraf/.codex/visualizations/2026/10/06/01a1131b-eac2-7a31-afb4-f219a8dd6471/spq06/2026-10-09/development-rehearsal-1.0.3/abandoned-preflight-accounting-1.0.0.json)

## Main plan: preparation only, not launched

Ashraf's five 8B condition/representation combinations extrapolate to **9.146h** including all40 potential clarifications, measured process/loading overhead and25% reserve. This includes a full 240s fallback for Llama CoT's unmeasured continuation. The full eight-combination conservative envelope is **82.282h** because AWQ task timings are unmeasured and use unchanged120/360s stage allowances. This is not a measured82h prediction or evidence that the48h target is impossible; it means an updated feasible full forecast cannot yet be confirmed. No two-machine schedule is claimed.

Main core remains200, pool400, historical size-decision forecast43.136h unchanged. Ashraf planned share is1600 initials +320 possible continuations =1920 calls across the six enriched and two existing ablation combinations, all 200 items per combination. Four50-item initial batches and one up-to40 actual supported clarification batch per combination give40 planned worker processes. Future work must use one central aggregate ledger with the collaborator, not48h per executor. Main spending/accounting remains0; all172800s remain unreserved, shared across both executors.

Before main issuance: obtain separately authorized fresh AWQ task/decode/actual-history evidence without erasing these failed attempts; document Llama CoT’s unexercised stage2 path; backport the cache/index validation fixes into a separately versioned MAIN adapter/package and obtain receipts pinned to that main package; verify task-qualified hardware/runtime on each executor; combine measured collaborator timings with the refreshed Ashraf forecast; budget loading/continuations/reserve and preserve writing time before12 October2026 23:59AoE. No main stage/owner/budget ticket was issued here.

After those prerequisites and main authorization, issue exactly the eight Ashraf condition/representation shards, prepare batches of never-reserved keys, reserve before launch, import immutable actual returns, centrally route supported actual clarifications, then issue only never-reserved supported stage2 keys. Run GPU jobs serially. Stop on exhausted aggregate reservations or execution incompatibility; do not replace/retry failures. Use the existing fixed200-item endpoints and paired whole-group stratified uncertainty procedure unchanged. Commands below are future procedure templates, not executed main commands.

- [separate per-condition/per-family forecast](C:/Users/aashraf/.codex/visualizations/2026/10/06/01a1131b-eac2-7a31-afb4-f219a8dd6471/spq06/2026-10-09/development-rehearsal-1.0.3/delivery-1.0.2/ashraf-main-forecast.json)
- [Development commands and main prerequisites](../simphysqa/development_rehearsal_commands.md)
- [Collaborator compatibility handoff](../simphysqa/development_rehearsal_handoff.md)
- [AWQ task qualification blocker](SPQ06_rehearsal_blocker.md)

No main inference, simulations, annotation calls, collaborator inference, answering API, main reservations, merge or push. Human acceptability, explanation prose quality, OOD and main performance remain unclaimed.
