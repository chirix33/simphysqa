# SPQ06 AWQ supplemental qualification — 10 October 2026

The three authorized AWQ combinations completed 15 initials and 3 actual supported
clarification continuations, with 18 accepted immutable outputs,18 parsed objects,
15 fixed condition/item diagnostic rows and six worker launches. All three have
initial task execution and live stage 2 evidence. No startup/import failure, CPU
fallback, timeout, length limit, conflict or scientific retry occurred. This is
execution qualification, not main accuracy, human acceptability or explanation
prose-quality evidence. The original 40-row diagnostic and 15 reserved AWQ failures
remain unchanged; the supplemental15 rows do not replace them.

Branch simphysqa-spq06; starting commit b23d375f58f2cc8205ea455c3bde3d244a6c5e4c.
No subsequent commits or pre-existing uncommitted work were present. The final local
commit receipt is linked below; no reset, merge, rebase, push or main launch.

| Combination | Initials | Actual continuations | Total stages (s) | Adapter lifecycle (s) | Sampled stage peak (MiB) |
|---|---:|---:|---:|---:|---:|
| qwen3_32b_awq_off / enriched | 5 completed | 1 completed | 87.902 | 174.552 | 31869 |
| qwen3_32b_awq_on / enriched | 5 completed | 1 completed | 254.909 | 346.012 | 31922 |
| qwen3_32b_awq_on / structured_only | 5 completed | 1 completed | 211.896 | 299.547 | 31901 |

All 18 backend finish reasons are actual vLLM `stop`; raw stop_reason:null is
preserved, not fabricated as an EOS ID. Exact tokenizer/template render, input IDs,
output decode, and real history assembly passed. vLLM may omit stop tokens from
returned IDs. Code/config/stop metadata are pinned; no inaccessible reasoning is
inferred. Parsed validity does not imply correctness or prose quality.

## Frozen supplemental selection

| Family | Domain | QA ID | Trajectory group |
|---|---|---|---|
| direct | driving | `spq-direct-12773c2ff79f31a23df5f707` | `75d5bf58ef3677542fb0eeedc7ef467c` |
| predictive | driving | `1d6b0392477db4ca7e6bf4d4dbf7287e` | `cafaa3974103ef3a588ca4310bf40402` |
| counterfactual | object_pushing_stacking | `spq-counterfactual-0b0f5aedf50bf91faf923f65` | `201bd588247c0ba999f1955a18d6d3f5` |
| explanation | robotic_arm | `spq-explanation-4718f82e29aa5d63e889fe56` | `8c6023bf3a70e990db8eb51fb1ff9106` |
| clarification | tethered_load | `spq-clarification-56252ff337726a65e727b51d` | `fe9fbb418a17d5412a16024d7a76ea64` |

All are existing accepted train records. Before loading their private source bodies,
selection took the first feasible lexicographic tuple of manifest-order candidates
in direct/predictive/counterfactual/explanation/clarification order, excluding the
original five QA AND groups, requiring five distinct groups and all four domains.
No text quality, correctness or intervention magnitude informed selection. Each
combination used these same tasks through unchanged public_request/request_from
main projection. No held-out QA, annotation generation, simulations or new records.

[Selection freeze](C:/Users/aashraf/.codex/visualizations/2026/10/06/01a1131b-eac2-7a31-afb4-f219a8dd6471/spq06/2026-10-09/awq-supplement-1.0.0/selection-freeze.json),
[Execution/config/budget freeze](C:/Users/aashraf/.codex/visualizations/2026/10/06/01a1131b-eac2-7a31-afb4-f219a8dd6471/spq06/2026-10-09/awq-supplement-1.0.0/execution-freeze.json),
[Pre-inference offline receipt](C:/Users/aashraf/.codex/visualizations/2026/10/06/01a1131b-eac2-7a31-afb4-f219a8dd6471/spq06/2026-10-09/awq-supplement-1.0.0/offline-verification.json).

## Accounting and measurements

The adapter ledger charges 820.110343 s once across
six ended process lifecycles, including coordinator preparation, runtime metadata,
GPU/ModelConfig preflight, full artifact verification, loading, stages and teardown.
The separately preserved outer dispatcher observations add
2.187657 s; full supplemental accounting is
822.298000/8640 s. Original accounting remains
1894.0963235319355 s, including 1200 s unknown abandoned metadata reservations.
Combined accounting is 2716.394324/20400 s,
with 17683.605676 s remaining. Supplemental calls18/18 and
worker launches6/6 are exhausted; time headroom does not authorize additional work.
The explicit six-process extension is separate from the original 16 bound and its
15 conservative process reservations. No orphan reservation was freed.

[Full accounting and boundaries](C:/Users/aashraf/.codex/visualizations/2026/10/06/01a1131b-eac2-7a31-afb4-f219a8dd6471/spq06/2026-10-09/awq-supplement-1.0.0/delivery-1.0.0/accounting-reconciliation.json),
[Actual status/loading/timing/memory detail](C:/Users/aashraf/.codex/visualizations/2026/10/06/01a1131b-eac2-7a31-afb4-f219a8dd6471/spq06/2026-10-09/awq-supplement-1.0.0/delivery-1.0.0/actual-results.json),
[Private central parsed/scored15-row analysis](C:/Users/aashraf/.codex/visualizations/2026/10/06/01a1131b-eac2-7a31-afb4-f219a8dd6471/spq06/2026-10-09/awq-supplement-1.0.0/analysis/development-analysis.json).

Each actual stage preserves exact request, rendered prompt/IDs, output/IDs,
backend termination, generation latency, total stage time and qualification references.
Device-wide nvidia-smi monitoring samples every0.5 s with UUID, sample counts,
errors and sampled high-water marks. Peaks may be missed and include other device
work. Torch allocation concerns the parent process and may exclude vLLM children;
it must not be interpreted as total model/device memory. Loading is separately
recorded and charged once/process. No measured TTFT/prefill/decode split, semantic
refusal classifier, explanation prose rating or human judgment is claimed.
Unchanged vLLM teardown NCCL warnings remain in logs; all processes exited0.

## Corrected main transfer and evidence mapping

Use execution-public-1.1.1. Its 2200 initial request bytes,200 selected identities,
400 inventory, condition specifications, workers, support, templates, generation
settings, timeouts and scoring contracts are identical to execution-public-1.0.3.
All 2640 possible keys remain uniquely covered with unassigned main ownership.
Public explanation comparisons remain; private gold/rollouts/credentials are absent.

Numeric CUDA visibility is checked against nvidia-smi index/UUID AND Torch UUID;
the exact vLLM ModelConfig must pass before science reservations. HF symlink targets
must remain inside the explicit cache and match every pinned digest. A600 s overhead
allocation precedes metadata and is augmented with stage allowances after preflight,
so process work is charged once. Persistent central queue blocks stop related model
representations after shared startup failure. No automatic retries/unblocking.

Supplemental inference used development-awq-public-1.0.0, referencing main 1.1.0;
these roots and receipts remain sealed. Final main 1.1.1 adds the central queue and
corrects the unexercised GGUF metadata branch: Torch UUID is null/not applicable
without a Torch measurement. Its AWQ metadata branch and all generation bytes stay
unchanged. This overlay is explicitly mapped, not silently substituted.

Five existing 8B combinations/29 outputs map to the corrected main worker/support,
scientific/resolved condition, artifact/tokenizer digests, precision and unchanged
UUID binding/hardware/runtime. They were not rerun. Three AWQ combinations map
their new evidence through exact numeric bindings and the1.1.0→1.1.1 metadata overlay.
Main-scope orchestration itself remains inference-unexercised; its gates are offline
verified. Llama CoT's original actual requested_information:null stays unroutable;
no live stage 2 evidence is invented. Its unchanged240 s continuation allowance is
retained in planning. Collaborator hardware and Gemma/DeepSeek task paths are not
qualified by Ashraf's evidence.

[Portable instructions](C:/Users/aashraf/.codex/visualizations/2026/10/06/01a1131b-eac2-7a31-afb4-f219a8dd6471/spq06/2026-10-09/execution-public-1.1.1/README.md),
[Main package hashes](C:/Users/aashraf/.codex/visualizations/2026/10/06/01a1131b-eac2-7a31-afb4-f219a8dd6471/spq06/2026-10-09/execution-public-1.1.1/package-manifest.json),
[Main transfer ZIP](C:/Users/aashraf/.codex/visualizations/2026/10/06/01a1131b-eac2-7a31-afb4-f219a8dd6471/spq06/2026-10-09/execution-public-1.1.1.zip)
— ZIP SHA256 `eb37bc827d4dc6795e9a504eab58a9f856c99aa6d08dc4dc4c4368b93cba3903`;
manifest SHA256 `722276ecb67b851ef9c8de0563ee074c83c2b1493727e3a25fc0f95bb3981094`.

[Executed supplemental package hashes](C:/Users/aashraf/.codex/visualizations/2026/10/06/01a1131b-eac2-7a31-afb4-f219a8dd6471/spq06/2026-10-09/development-awq-public-1.0.0/package-manifest.json),
[Eight-combination evidence/change-impact mapping](C:/Users/aashraf/.codex/visualizations/2026/10/06/01a1131b-eac2-7a31-afb4-f219a8dd6471/spq06/2026-10-09/awq-supplement-1.0.0/delivery-1.0.0/qualification-evidence-mapping.json),
[Metadata overlay byte-identity proof](C:/Users/aashraf/.codex/visualizations/2026/10/06/01a1131b-eac2-7a31-afb4-f219a8dd6471/spq06/2026-10-09/awq-supplement-1.0.0/main-1.1.0-to-1.1.1-compatibility.json),
[collaborator handoff](../simphysqa/awq_supplement_handoff.md).

## Forecast and later main plan

Ashraf's six enriched conditions plus two ablations evaluate the same 200 frozen
QA:1600 initials and at most320 continuations,1920 calls. The revised forecast is
17.041 h, separating measured family stages, Llama CoT's
unmeasured continuation timeout fallback, loading/other overhead and25% reserve.
It extrapolates one development task/family and does not establish runtime coverage
for all domains/lengths or a two-machine schedule. Five batches/combination are
planned: four ≤50-item initial processes plus one ≤40 supported-continuation batch.
Keep actual history/context rejection and fixed denominators; no truncation/retry.

[Revised Ashraf-only forecast](C:/Users/aashraf/.codex/visualizations/2026/10/06/01a1131b-eac2-7a31-afb4-f219a8dd6471/spq06/2026-10-09/awq-supplement-1.0.0/delivery-1.0.0/ashraf-main-forecast-2.0.1.json);
historical43.136 h size decision and82.282 h AWQ-timeout envelope are preserved.
Main spending remains0; the full172800 s aggregate budget remains available,
not a fresh48 h allowance/machine. Before main authorization/issuance, adopt reviewed
package-mapped task receipts, record missing Llama CoT continuation coverage, refresh
hardware/artifact/ModelConfig preflight, coordinate disjoint central assignments
and aggregate reservations, and include collaborator measurements in a joint plan.
Reserve analysis/writing time before October12,2026,23:59AoE. No size change.

[Exact executed/future commands](../simphysqa/awq_supplement_commands.md).
No main/collaborator inference, new annotation, simulations, altered scoring,
human ratings, merge, rebase or push occurred in this supplemental milestone.

## Verification and provenance

96 offline checks passed before weights;102 final checks passed after the additive
queue/GGUF metadata fixes. All 18 actual render/token/output/history/memory/timing/
backend-stop checks passed. Immutable import accepted18, with no invalid returns or
conflicts. Central analysis contains 15 fixed rows and18 actual parsed objects,
joined to raw-result hashes; scored diagnostic values remain private and are not
main estimates. Existing explanation/numerical/Boolean/quaternion/clarification
scorers and uncertainty procedures are unchanged.

[102-test log](C:/Users/aashraf/.codex/visualizations/2026/10/06/01a1131b-eac2-7a31-afb4-f219a8dd6471/spq06/2026-10-09/awq-supplement-1.0.0/offline-tests-final.log),
[Actual18-stage verification](C:/Users/aashraf/.codex/visualizations/2026/10/06/01a1131b-eac2-7a31-afb4-f219a8dd6471/spq06/2026-10-09/awq-supplement-1.0.0/actual-token-output-verification.json),
[23603 historical file preservation hashes](C:/Users/aashraf/.codex/visualizations/2026/10/06/01a1131b-eac2-7a31-afb4-f219a8dd6471/spq06/2026-10-09/awq-supplement-1.0.0/delivery-1.0.0/preservation-after.json),
[Code/package/receipt provenance](C:/Users/aashraf/.codex/visualizations/2026/10/06/01a1131b-eac2-7a31-afb4-f219a8dd6471/spq06/2026-10-09/awq-supplement-1.0.0/delivery-1.0.0/artifact-index.json),
[Immutable import receipts](C:/Users/aashraf/.codex/visualizations/2026/10/06/01a1131b-eac2-7a31-afb4-f219a8dd6471/spq06/2026-10-09/awq-supplement-1.0.0/import-receipts),
[Actual immutable raw returns](C:/Users/aashraf/.codex/visualizations/2026/10/06/01a1131b-eac2-7a31-afb4-f219a8dd6471/spq06/2026-10-09/awq-supplement-1.0.0/immutable-imports),
[Final local commit receipt](C:/Users/aashraf/.codex/visualizations/2026/10/06/01a1131b-eac2-7a31-afb4-f219a8dd6471/spq06/2026-10-09/awq-supplement-1.0.0/delivery-1.0.0/final-commit-receipt.json).
