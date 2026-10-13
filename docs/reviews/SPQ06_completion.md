# SPQ06 completion — 200-item main set frozen

Branch `simphysqa-spq06`, updated-main base `5e1355d63b6829395b266a18edec198603e10932`. Implementation commit before this documentation: `1e337f41c52ed24f06bf06228f83f261ea3c8371`. The external final delivery receipt records the final documentation commit; no merge/push occurred.

Prepared400 unique QA/400 distinct original held-out groups; target400 complete:True. Nested200 core has10 per cell. The timing/preparation-only final decision selects **200**. Main-plus-essential-ablation forecast including25%reserve: **43.136GPUhours**. No main output, model-answer human judgment or audit-feedback import was executed.

## Actual pilot qualification

The20 development QA come from16 train groups. Same20 items were reserved for each of nine conditions:180 initials,16 supported conditional continuations,196 stage reservations,195 returned raw results and one interrupted/unknown stage.122 initials reached valid GPU inference;55 were context-capacity rejections, two were invalid CPU-runtime returns and one unknown. All16 continuations were actual GPU model turns, not authored reference questions. Requests, raw text/token IDs, parsing/factual scoring and separate reasoning diagnostics are saved privately.

| Condition | Initial completion/status counts (all20 retained) | Actual local GPU runtime |
|---|---|---|
| llama31_8b_cot | completed:18, length_limited:2 | available, with retained failures |
| llama31_8b_direct | completed:18, length_limited:2 | available, with retained failures |
| qwen3_8b_direct | completed:15, failed:5 | available, with retained failures |
| qwen3_8b_thinking | completed:10, failed:10 | available, with retained failures |
| qwen3_32b_awq_off | completed:15, failed:5 | available, with retained failures |
| qwen3_32b_awq_on | completed:10, failed:10 | available, with retained failures |
| gemma3_27b_qat_direct | completed:11, failed:5, interrupted_unknown_reserved:1, invalid_runtime_cpu:2, length_limited:1 | available, with retained failures |
| gemma3_27b_qat_cot | completed:10, failed:10 | available, with retained failures |
| deepseek_r1_distill_qwen32b | completed:10, failed:10 | available, with retained failures |

Runtime availability is qualification of execution, not all-item successful execution or an empirical quality threshold. No current artifact/access blocker remains. Original long full public pilot views were not replaced or rerun. The separately versioned main projection is fact-validated and tokenized, but has not been rerun through models.

| Model artifact | Exact revision | Quantization and license |
|---|---|---|
| Qwen/Qwen3-8B | b968826d9c46dd6066d109eabc6255188de91218 | BF16, no weight quantization; Apache2 |
| meta-llama/Llama-3.1-8B-Instruct | 0e9e39f249a16976918f6564b8830bc894c89659 | BF16; Llama3.1 |
| Qwen/Qwen3-32B-AWQ | 0499c3ac83fdef8810b907a23894ba91e95eddd8 | OfficialAWQ, FP16 activation; Apache2 |
| google/gemma-3-27b-it-qat-q4_0-gguf | 17cf0f6ad611f1a57a1640daa57eb427d6e67ed6 | OfficialQAT Q4_0 GGUF/f16KV; [Gemma terms](https://ai.google.dev/gemma/terms), [official model card](https://huggingface.co/google/gemma-3-27b-it-qat-q4_0-gguf) |
| deepseek-ai/DeepSeek-R1-Distill-Qwen-32B | 711ad2ea6aa40cfca18895e8aca02ab92df1a746 | Official original BF16 weights, runtime-derived pinned bitsandbytesNF4 double quantization/BF16 activation/cache; MIT with upstream Qwen notices |

Small runtime: torch2.7.1+cu128, transformers4.51.3, tokenizers0.21.1, safetensors0.5.3. Large runtime: vLLM0.11.0, torch2.8.0 CUDA12.8 build, transformers4.57.1, tokenizers0.22.1, bitsandbytes0.48.1. Gemma: official llama.cpp b11538/79e2e74eb CUDA12.8 binary. Model/license/tokenizer files and Gemma server/GGUF were independently hashed offline:134,571,692,740 unique bytes, all nine conditions passed. See [integrity receipt](C:/Users/aashraf/.codex/visualizations/2026/10/06/01a1131b-eac2-7a31-afb4-f219a8dd6471/spq06/2026-10-09/model-integrity-1.0.0.json).

The workstation was RTX5090,32607MiB. AWQ required immutable startup revisions to FP16/.89VRAM; DeepSeek required .93VRAM after a zero-item insufficient-KV-cache startup. Exact artifacts,32768context and generation limits stayed fixed. DeepSeek device-wide sampled peak was approximately31993MiB; thin memory headroom is a limitation. Torch allocation does not cover vLLM child engines. One-second nvidia-smi sampling may miss peaks; absent early samples remain unavailable, never zero.

Gemma initially fell back to CPU because a bundled CUDA library directory was absent. Three direct item reservations remain: two invalid-runtime timeouts and one interrupted unknown. The second CPU timeout lasted144.509s and exceeded the intended120s deadline; this is a retained deviation. The revised worker uses strictCUDA0 discovery/all-layer offload and an absolute HTTP deadline. Only never-reserved stages were scheduled after startup repairs. No scientific item/stage was retried. See [the user CUDA notes and actual repair](../simphysqa/gguf_cuda_setup.md).

The CPU tokenizer emitted a generic DeepSeek length warning because its default metadata is16384. The pinned model configuration supports131072 positions; the qualified runtime remains at the frozen32768 total-context limit. An actual pilot inference used23509 input tokens. No context or generation allowance was increased. See [offline context-bound evidence](C:/Users/aashraf/.codex/visualizations/2026/10/06/01a1131b-eac2-7a31-afb4-f219a8dd6471/spq06/2026-10-09/context-bounds-evidence-1.0.0.json).

Pilot accounted work: 15505.671s (4.307h) under64800s. This includes measured processes4105.671s, unknown full reservation5400s and6000s conservative retrospective bounds for the first two manually scheduled processes. These bounds are not invented timings. Returned-stage token counts:5,008,920 inputs (including tokenized capacity rejections, not all prefilled),64,729 outputs. Hosted answering/API spendUSD0.

### Actual selected pilot identities

| Domain | Canonical family | QA ID | Trajectory group |
|---|---|---|---|
| robotic_arm | clarification | spq-clarification-ce09635e16f3584d4a6228d0 | a9563dc9343a2c57b624ae5048f3216a |
| robotic_arm | explanation | spq-explanation-4718f82e29aa5d63e889fe56 | 8c6023bf3a70e990db8eb51fb1ff9106 |
| robotic_arm | counterfactual | spq-counterfactual-880173bd9c70a2ba3e5efa4d | a9563dc9343a2c57b624ae5048f3216a |
| robotic_arm | direct | spq-direct-06749fe8a9f9c2ac6524d3bf | e5b3e572a3a3ae69523f12a8aeb6f616 |
| robotic_arm | predictive | 2a6a0b83dcf873b3699bba4e35023eff | c919f9c23f01e781978c330477762d44 |
| driving | clarification | spq-clarification-18fa6951f1d3e7ded51067bf | 75d5bf58ef3677542fb0eeedc7ef467c |
| driving | explanation | spq-explanation-4a1bc0bb5da442b28767e5c4 | 8527f5b0a2fef1d647c2fb239b52e473 |
| driving | counterfactual | spq-counterfactual-e3457ad6b03d422ebc6191a3 | 8527f5b0a2fef1d647c2fb239b52e473 |
| driving | direct | spq-direct-c0d54e45966d9cce493e478f | cafaa3974103ef3a588ca4310bf40402 |
| driving | predictive | e52c5e8391589681cf355d960fb8f185 | 09fae68d427585369e6be2bee1ce4441 |
| object_pushing_stacking | clarification | spq-clarification-38b4461a6db9b1e8affc8356 | de7550b6e98df7e249dc3c44f1874120 |
| object_pushing_stacking | explanation | spq-explanation-d94b4671c2ae80c4045a358b | 201bd588247c0ba999f1955a18d6d3f5 |
| object_pushing_stacking | counterfactual | spq-counterfactual-68a75d394cefe37a0d48a30c | de7550b6e98df7e249dc3c44f1874120 |
| object_pushing_stacking | direct | spq-direct-9bfb1b0ecd5c620e6b3731bf | c666e35a062a41d352b2a241f0969530 |
| object_pushing_stacking | predictive | 9ca52411dc610e46e81bafdb308f500b | 61c8d7ee2f1dedf7ee01b63f262a9e3e |
| tethered_load | clarification | spq-clarification-56252ff337726a65e727b51d | fe9fbb418a17d5412a16024d7a76ea64 |
| tethered_load | explanation | spq-explanation-183d115cb9d68114d96538c4 | 3c44b44c4f41c3e7b89ffb6ab352a9a3 |
| tethered_load | counterfactual | spq-counterfactual-9af7db590c14b3b198ac2c1b | fe9fbb418a17d5412a16024d7a76ea64 |
| tethered_load | direct | spq-direct-797fd7d31ec5cdec4fa949cc | 0b6c45a66fe8fb6fb7e2a82dd0255286 |
| tethered_load | predictive | 222d4fd6c0e00e05726c1c1c94fa2d37 | e28bd6316c55e1bebd3c402261edcaf8 |

## Held-out preparation and accounting

Original inventory11,105 QA/6,340 groups. Original `test_id` frame735 groups;676 eligible after the frozen exclusions.208 distinct groups are excluded globally: authoritative development/inspection, all140 SPQ05 groups and actual historical prompt-use groups. No split was changed or other split borrowed. Seed20261009: sorted per-domain groups shuffled, disjoint round-robin family pools, random original QA/group. First20 qualified/cell and first10/core identities are frozen independently of model scores.

Qualified400; core200; rejected15; unused261 of676 candidates. Clarification eligibility attrition remains separate from annotation failures and replay/admission failures. Same-cell replacements retain original reasons and use the frozen candidate order. Counterfactual/explanation contrasts may be unchanged or within tolerance.

| Cell / rank | Retained rejection |
|---|---|
| robotic_arm/clarification / 3 | ValueError: no_scorer_disjoint_query_gap |
| robotic_arm/clarification / 12 | ValueError: no_scorer_disjoint_query_gap |
| driving/clarification / 15 | ValueError: saved_replay_or_admission_rejection |
| tethered_load/clarification / 5 | ValueError: no_scorer_disjoint_query_gap |
| tethered_load/clarification / 10 | ValueError: no_scorer_disjoint_query_gap |
| tethered_load/clarification / 11 | ValueError: no_scorer_disjoint_query_gap |
| tethered_load/clarification / 13 | ValueError: no_scorer_disjoint_query_gap |
| tethered_load/clarification / 15 | ValueError: no_scorer_disjoint_query_gap |
| tethered_load/clarification / 18 | ValueError: no_scorer_disjoint_query_gap |
| tethered_load/clarification / 21 | ValueError: no_scorer_disjoint_query_gap |
| tethered_load/clarification / 23 | ValueError: no_scorer_disjoint_query_gap |
| tethered_load/clarification / 28 | ValueError: no_scorer_disjoint_query_gap |
| tethered_load/clarification / 29 | ValueError: no_scorer_disjoint_query_gap |
| tethered_load/clarification / 30 | ValueError: no_scorer_disjoint_query_gap |
| tethered_load/clarification / 31 | ValueError: no_scorer_disjoint_query_gap |

Annotation: 414 initial requests, 420 actual attempts, 6 recorded repairs; chargedUSD13.631765; 4982708 reserved input tokens and860160 reserved output tokens; 3840.159s attempt work. Matched simulations:1020; simulator/static worker work2444.298s. All separate approved SPQ06 ceilings were respected. SPQ05 budgets were not reused. Exact requests, repair feedback, raw responses, outcomes and receipts remain saved.

Provider: gpt-5.6-sol, medium reasoning,2048max-output,120s,store=false,tools=[],default tier. Official pricing refreshed before live calls; reserve rates10/40USD per million versus resolved input4/cache.4/cache-write5/output20. The configured provider alias has no immutable model snapshot; this limitation remains disclosed. Actual charges are token-based estimates, not a provider invoice.

Independent verification: 4400 saved public states with original cutoffs;23200 private evidence bindings resolved;240 qualified matched-pair manifests;6600 exact public requests across both nested sizes verified. Full/enriched/structured inputs agree on physical facts, comparisons, ambiguity and answerability. No gold/reference/private verification enters model inputs. All pairs retain exact factual replay plus separate original/alternative admission.

Actual saved-output resume with annotation/simulation/derivation boundaries disabled preserved11841 run files and7212 export files; zero new calls/solves/compilations, only a new immutable summary. Original6340 source files,62 prior manifests/5002 indexed files and96 SPQ05 manifests remained unchanged. SPQ05 stored R1/R2/R3 blanks each retain140 rows; external independent feedback is processing per user and was not imported or inferred.

Actual annotation usage (known receipts only):{"known_cache_write_tokens": 819953, "known_cached_input_tokens": 0, "known_input_tokens": 821213, "known_output_tokens": 476348, "known_usage_attempts": 420, "unknown_usage_attempts": 0}. Zero-step static compilations:62; their work is included in the simulator/static ceiling. Of208 globally excluded groups,59 overlap the original735-group held-out frame.

## Timing-only size decision

Use the largest measured initial/continuation GPU inference latency per condition/family, applied across domains. An entirely unmeasured family retains its frozen timeout. Zero-time context rejection is never a fast inference measurement. Include every possible continuation, measured loading/process overhead for50-item shards and25%reserve. Smaller main projection was not rerun on models: extrapolation is a feasibility estimate, not a guaranteed bound.

| Condition | Initial D/P/CF/E/Clar seconds; Clar continuation |400h with reserve |200h with reserve |
|---|---|---|---|
| llama31_8b_cot | 18.939/18.456/153.816/22.384/152.620; 157.935 | 14.584 | 7.292 |
| llama31_8b_direct | 16.997/23.898/46.795/24.392/10.759; 9.272 | 3.725 | 1.863 |
| qwen3_8b_direct | 6.873/21.229/6.719/38.123/6.466; 13.679 | 2.615 | 1.307 |
| qwen3_8b_thinking | 20.910/19.756/45.294/67.503/21.987; 61.034 | 6.620 | 3.310 |
| qwen3_32b_awq_off | 31.554/28.871/29.358/53.693/53.874; 30.201 | 6.448 | 3.224 |
| qwen3_32b_awq_on | 54.659/40.689/98.531/85.208/42.726; 123.940 | 12.464 | 6.232 |
| gemma3_27b_qat_direct | 11.374/20.169/11.521/26.425/20.747; 120.000 | 5.891 | 2.946 |
| gemma3_27b_qat_cot | 8.472/13.821/9.067/32.475/10.877; 240.000 | 8.781 | 4.390 |
| deepseek_r1_distill_qwen32b | 45.632/55.014/61.832/92.344/70.236; 32.728 | 10.066 | 5.033 |

Total main+two ablations:400=86.273h/5280maxcalls;200=43.136h/2640maxcalls. Final choice200, frozen at2026-10-10T00:18:32.053388+00:00, before any main output. Deadline2026-10-13 11:59UTC (October12,23:59AoE), minimum12h writing reserve. December commitment does not extend it.

Capacity: {"200": {"checked_initial_requests": 2200, "complete": true, "conservative_continuation_capacity_failures": 30, "expected_initial_requests": 2200, "initial_capacity_failures": 0}, "400": {"checked_initial_requests": 4400, "complete": true, "conservative_continuation_capacity_failures": 60, "expected_initial_requests": 4400, "initial_capacity_failures": 0}}. Conservative continuation bounds reserve both full output allowances and64boundary tokens; an actual short first turn may fit when that bound does not. Actual continuations must pass the unchanged context check. Every frozen item stays in the denominator; known capacity failures are retained unsuccessful stages, never substitutions.

Prespecified matched ablations: Qwen3-8B direct and Qwen3-32B-AWQ thinking-on. They contrast model scale/quantization/reasoning within one architecture family, not a causal isolation of those attributes. All selected items receive both input conditions. Structured-only removes derived language without removing unique physical declarations/comparison evidence or restoring a clarification selector.

## Main readiness, analysis and human boundaries

The local serial runner is prepared but disabled in this milestone. Single reserved attempt/stage, immutable raw outputs, never-reserved-only resume,48GPUhour cumulative cap. Private scoring uses accepted typed scalar/vector/Boolean/sign-invariant quaternion checks and unchanged tolerance; explanation fact components and prose adequacy are separate; clarification behavior/routing/resolved correctness are separate. Missing/invalid/failed/abstained rows remain in item denominators. No pooling numerical errors across units/quantities.

Main intervals and paired differences:10000 paired whole-trajectory bootstrap draws within domain/family strata,seed20261009,95%percentile intervals. Same group draws apply to every condition and ablation; duplicate/cross-stratum groups halt. Balanced claims concern this qualified design, not natural release frequencies. No achieved power, human acceptability, explanation adequacy, OOD or main accuracy claim.

Prospective model-answer prose study: first two core explanation items/domain,eight tasks×nine conditions=72responses; separate blinded P1/P2 forms,144blank assignments. Both blank imports collected0; originals immutable, discussion/adjudication separate. This is not SPQ05 annotation feedback. Actual answer packets cannot be exported until model responses exist; metadata is blinded, raw self-identification is retained and reported if it unblinds.

## Validation actually executed

19 targeted SPQ06 behavioral tests passed (`python -m unittest test_spq06 test_spq06_execution test_spq06_main test_spq06_analysis -v`), actual log `final-targeted-tests-1.0.1.log`. Earlier broad offline invocation executed113passing methods but failed a counterfactual setUpClass due to an incorrect artifact path; the four affected tests passed after pointing to the actual counterfactual QA. Preserve the original nonzero run receipt. Tests are software verification, not empirical model quality. CPU and large answering-environment `pip check` passed. CLI help/imports, full branch diff and whitespace review passed.

Actual saved export, source/evidence/privacy/allocation/exclusion/nesting, tokenization, blank-form imports and disabled-boundary resume receipts are linked below. No main response assessment or human submission was invented. The Windows GGUF/MSVC build was not executed; the actual runtime is pinned WSL CUDA. Different GPUs require their own qualification.

## Inspectable delivery and exact commands

External root: `C:/Users/aashraf/.codex/visualizations/2026/10/06/01a1131b-eac2-7a31-afb4-f219a8dd6471/spq06/2026-10-09`. [Main readable item index](C:/Users/aashraf/.codex/visualizations/2026/10/06/01a1131b-eac2-7a31-afb4-f219a8dd6471/spq06/2026-10-09/main-preparation-1.0.0/INDEX.md); [timing decision](C:/Users/aashraf/.codex/visualizations/2026/10/06/01a1131b-eac2-7a31-afb4-f219a8dd6471/spq06/2026-10-09/runtime-decision-1.0.0/runtime-forecast-and-size-decision.json); [future run plan](C:/Users/aashraf/.codex/visualizations/2026/10/06/01a1131b-eac2-7a31-afb4-f219a8dd6471/spq06/2026-10-09/main-run-preflight-1.0.0/main-run-plan.json).

[Exact commands/environment variables](../simphysqa/spq06_commands.md), [main design](../simphysqa/spq06_main_design.md), [execution/procedure archive supplement](../simphysqa/prompt_archive/SPQ06/README.md). Preparation commands were executed; main `run`, main analysis and actual prose packet commands are future commands requiring later authorization/evidence.

| Artifact | SHA256 |
|---|---|
| [heldout-preparation-1.0.0/protocol.json](C:/Users/aashraf/.codex/visualizations/2026/10/06/01a1131b-eac2-7a31-afb4-f219a8dd6471/spq06/2026-10-09/heldout-preparation-1.0.0/protocol.json) | 072a689720efce5bc5405b250ecfd38e5ed9baaaed6644336d39f09daa0d2307 |
| [heldout-preparation-1.0.0/candidate-order.json](C:/Users/aashraf/.codex/visualizations/2026/10/06/01a1131b-eac2-7a31-afb4-f219a8dd6471/spq06/2026-10-09/heldout-preparation-1.0.0/candidate-order.json) | 92205ba993e9c9d7ad8ca53d5c74a2e4474d367ec5496af4836fee8ff6282e35 |
| [heldout-execution-1.0.0/execution-plan.json](C:/Users/aashraf/.codex/visualizations/2026/10/06/01a1131b-eac2-7a31-afb4-f219a8dd6471/spq06/2026-10-09/heldout-execution-1.0.0/execution-plan.json) | 74a665130502858c9b0410e6ad2159219b4ae6b9c1305f45a2e45ce61bc18f24 |
| [main-preparation-1.0.0/nested-200-manifest.json](C:/Users/aashraf/.codex/visualizations/2026/10/06/01a1131b-eac2-7a31-afb4-f219a8dd6471/spq06/2026-10-09/main-preparation-1.0.0/nested-200-manifest.json) | 15cffeba8fbad9a32095ebf08e6860903bb82a05666cf6b22ebf7347dd49dbfc |
| [main-preparation-1.0.0/nested-400-manifest.json](C:/Users/aashraf/.codex/visualizations/2026/10/06/01a1131b-eac2-7a31-afb4-f219a8dd6471/spq06/2026-10-09/main-preparation-1.0.0/nested-400-manifest.json) | f8322849a0df4d9f3a7683d664193f0d1fcd4dd7113a7a79346892672a3311d3 |
| [main-preparation-1.0.0/manifest.json](C:/Users/aashraf/.codex/visualizations/2026/10/06/01a1131b-eac2-7a31-afb4-f219a8dd6471/spq06/2026-10-09/main-preparation-1.0.0/manifest.json) | d58dfb712f23bb2985c8310054dee3ab0f55b4775b64446ae0c1dd1905d9362b |
| [pilot-analysis-1.0.0/pilot-analysis.json](C:/Users/aashraf/.codex/visualizations/2026/10/06/01a1131b-eac2-7a31-afb4-f219a8dd6471/spq06/2026-10-09/pilot-analysis-1.0.0/pilot-analysis.json) | 9e281330d518484ed9b175a8851a30b79bcb56e559fa1a001035f330055533c4 |
| [pilot-accounting-1.0.0/pilot-resource-accounting.json](C:/Users/aashraf/.codex/visualizations/2026/10/06/01a1131b-eac2-7a31-afb4-f219a8dd6471/spq06/2026-10-09/pilot-accounting-1.0.0/pilot-resource-accounting.json) | f698edc05faf292b4b409e659cbe31b0189b4196963750bd18b105e04fbb88ba |
| [main-tokenization-1.0.0/capacity-checks.json](C:/Users/aashraf/.codex/visualizations/2026/10/06/01a1131b-eac2-7a31-afb4-f219a8dd6471/spq06/2026-10-09/main-tokenization-1.0.0/capacity-checks.json) | 7adc1ee5ea7f474a123cd35fcff64b80ab9e14cc10238a5e2e49f02245c6447d |
| [runtime-decision-1.0.0/runtime-forecast-and-size-decision.json](C:/Users/aashraf/.codex/visualizations/2026/10/06/01a1131b-eac2-7a31-afb4-f219a8dd6471/spq06/2026-10-09/runtime-decision-1.0.0/runtime-forecast-and-size-decision.json) | ce6f5232cf4f71aaec8fe37b92883b5de8afff0ce359460129d4d7bb5f509e21 |
| [main-run-preflight-1.0.0/main-run-plan.json](C:/Users/aashraf/.codex/visualizations/2026/10/06/01a1131b-eac2-7a31-afb4-f219a8dd6471/spq06/2026-10-09/main-run-preflight-1.0.0/main-run-plan.json) | c509c701fd232468db0c39dc7d9289a9f0ddc0c13659399b040c1a7bded7f37a |
| [preparation-verification-1.0.0/preparation-verification.json](C:/Users/aashraf/.codex/visualizations/2026/10/06/01a1131b-eac2-7a31-afb4-f219a8dd6471/spq06/2026-10-09/preparation-verification-1.0.0/preparation-verification.json) | adb2858fcc6415017fb233fa4013b22efcbbf981ea50ab1fe7764d4ee9f2982f |
| [saved-resume-verification-1.0.0/saved-resume-verification.json](C:/Users/aashraf/.codex/visualizations/2026/10/06/01a1131b-eac2-7a31-afb4-f219a8dd6471/spq06/2026-10-09/saved-resume-verification-1.0.0/saved-resume-verification.json) | 9e391690d356e1d214b48aeadc9013545d8e95da01e1d793b71efae8593c4a50 |
| [execution-provenance-1.0.0/execution-per-file-index.json](C:/Users/aashraf/.codex/visualizations/2026/10/06/01a1131b-eac2-7a31-afb4-f219a8dd6471/spq06/2026-10-09/execution-provenance-1.0.0/execution-per-file-index.json) | 3c74d6f9fcb855f98878503a11083301f9c4b9092b60c5d9daa22ff90c145ce9 |
| [preservation-verification-1.0.1/source-preservation.json](C:/Users/aashraf/.codex/visualizations/2026/10/06/01a1131b-eac2-7a31-afb4-f219a8dd6471/spq06/2026-10-09/preservation-verification-1.0.1/source-preservation.json) | 715cc710e9e45204d09795b35e71312933c8e57c451c86991c3b89b8c5724380 |

Inspect one frozen example per family; private record links disclose organizer evidence only, separate from model inputs:

- direct: [public enriched](C:/Users/aashraf/.codex/visualizations/2026/10/06/01a1131b-eac2-7a31-afb4-f219a8dd6471/spq06/2026-10-09/main-preparation-1.0.0/public/400/enriched/qwen3_8b_direct/spq-direct-a3e6bc7ca3ad2eeb947418ca.json) / [matched structured-only](C:/Users/aashraf/.codex/visualizations/2026/10/06/01a1131b-eac2-7a31-afb4-f219a8dd6471/spq06/2026-10-09/main-preparation-1.0.0/public/400/structured_only/qwen3_8b_direct/spq-direct-a3e6bc7ca3ad2eeb947418ca.json) / [private source and scoring record](C:/Users/aashraf/.codex/visualizations/2026/10/06/01a1131b-eac2-7a31-afb4-f219a8dd6471/spq06/2026-10-09/main-preparation-1.0.0/private/records/spq-direct-a3e6bc7ca3ad2eeb947418ca.json).

- predictive: [public enriched](C:/Users/aashraf/.codex/visualizations/2026/10/06/01a1131b-eac2-7a31-afb4-f219a8dd6471/spq06/2026-10-09/main-preparation-1.0.0/public/400/enriched/qwen3_8b_direct/680ac990725bf74030910bbbdd5e489f.json) / [matched structured-only](C:/Users/aashraf/.codex/visualizations/2026/10/06/01a1131b-eac2-7a31-afb4-f219a8dd6471/spq06/2026-10-09/main-preparation-1.0.0/public/400/structured_only/qwen3_8b_direct/680ac990725bf74030910bbbdd5e489f.json) / [private source and scoring record](C:/Users/aashraf/.codex/visualizations/2026/10/06/01a1131b-eac2-7a31-afb4-f219a8dd6471/spq06/2026-10-09/main-preparation-1.0.0/private/records/680ac990725bf74030910bbbdd5e489f.json).

- counterfactual: [public enriched](C:/Users/aashraf/.codex/visualizations/2026/10/06/01a1131b-eac2-7a31-afb4-f219a8dd6471/spq06/2026-10-09/main-preparation-1.0.0/public/400/enriched/qwen3_8b_direct/spq-counterfactual-a01477462539da3d274b7cb6.json) / [matched structured-only](C:/Users/aashraf/.codex/visualizations/2026/10/06/01a1131b-eac2-7a31-afb4-f219a8dd6471/spq06/2026-10-09/main-preparation-1.0.0/public/400/structured_only/qwen3_8b_direct/spq-counterfactual-a01477462539da3d274b7cb6.json) / [private source and scoring record](C:/Users/aashraf/.codex/visualizations/2026/10/06/01a1131b-eac2-7a31-afb4-f219a8dd6471/spq06/2026-10-09/main-preparation-1.0.0/private/records/spq-counterfactual-a01477462539da3d274b7cb6.json).

- explanation: [public enriched](C:/Users/aashraf/.codex/visualizations/2026/10/06/01a1131b-eac2-7a31-afb4-f219a8dd6471/spq06/2026-10-09/main-preparation-1.0.0/public/400/enriched/qwen3_8b_direct/spq-explanation-3aeccb89ddfe93711e8fbda9.json) / [matched structured-only](C:/Users/aashraf/.codex/visualizations/2026/10/06/01a1131b-eac2-7a31-afb4-f219a8dd6471/spq06/2026-10-09/main-preparation-1.0.0/public/400/structured_only/qwen3_8b_direct/spq-explanation-3aeccb89ddfe93711e8fbda9.json) / [private source and scoring record](C:/Users/aashraf/.codex/visualizations/2026/10/06/01a1131b-eac2-7a31-afb4-f219a8dd6471/spq06/2026-10-09/main-preparation-1.0.0/private/records/spq-explanation-3aeccb89ddfe93711e8fbda9.json).

- clarification: [public enriched](C:/Users/aashraf/.codex/visualizations/2026/10/06/01a1131b-eac2-7a31-afb4-f219a8dd6471/spq06/2026-10-09/main-preparation-1.0.0/public/400/enriched/qwen3_8b_direct/spq-clarification-1fd81f740be58bd6541815af.json) / [matched structured-only](C:/Users/aashraf/.codex/visualizations/2026/10/06/01a1131b-eac2-7a31-afb4-f219a8dd6471/spq06/2026-10-09/main-preparation-1.0.0/public/400/structured_only/qwen3_8b_direct/spq-clarification-1fd81f740be58bd6541815af.json) / [private source and scoring record](C:/Users/aashraf/.codex/visualizations/2026/10/06/01a1131b-eac2-7a31-afb4-f219a8dd6471/spq06/2026-10-09/main-preparation-1.0.0/private/records/spq-clarification-1fd81f740be58bd6541815af.json).

Next step: review this branch and separately authorize the frozen main run while preserving independent SPQ05 feedback. Do not merge automatically.
