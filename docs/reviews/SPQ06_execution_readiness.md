# SPQ06 execution readiness — 10 October 2026

Implemented on the existing unmerged `simphysqa-spq06`, starting from clean
`96140fbd55af9d4c86ff98d08ad288b3d1dc139d`. No later commits or uncommitted user
changes were present. Local implementation/verification only: no owners assigned,
real main reservations, answering/qualification inference, paid annotation,
simulations, main launch, merge, rebase or push. The dataset-paper scope is retained;
no learned Phi-JEPA method is introduced. Final commit/clean branch state is in
[the post-commit delivery receipt](C:/Users/aashraf/.codex/visualizations/2026/10/06/01a1131b-eac2-7a31-afb4-f219a8dd6471/spq06/2026-10-09/execution-readiness-1.0.1/delivery-receipt.json).

## Review and transfer entry points

- [Portable public ZIP (17,259,567 bytes)](C:/Users/aashraf/.codex/visualizations/2026/10/06/01a1131b-eac2-7a31-afb4-f219a8dd6471/spq06/2026-10-09/execution-public-1.0.3.zip).
- [Transfer instructions, exact commands and logging/rehearsal contract](C:/Users/aashraf/.codex/visualizations/2026/10/06/01a1131b-eac2-7a31-afb4-f219a8dd6471/spq06/2026-10-09/execution-public-1.0.3/README.md).
- [Public package manifest](C:/Users/aashraf/.codex/visualizations/2026/10/06/01a1131b-eac2-7a31-afb4-f219a8dd6471/spq06/2026-10-09/execution-public-1.0.3/package-manifest.json) and [transfer receipt](C:/Users/aashraf/.codex/visualizations/2026/10/06/01a1131b-eac2-7a31-afb4-f219a8dd6471/spq06/2026-10-09/execution-readiness-1.0.1/transfer-receipt.json).
- [All 2,200 exact initial request mappings and condition specifications](C:/Users/aashraf/.codex/visualizations/2026/10/06/01a1131b-eac2-7a31-afb4-f219a8dd6471/spq06/2026-10-09/execution-public-1.0.3/execution-spec.json).
- [Selected 200-item identity/group/domain/family/split manifest](C:/Users/aashraf/.codex/visualizations/2026/10/06/01a1131b-eac2-7a31-afb4-f219a8dd6471/spq06/2026-10-09/execution-public-1.0.3/selected-items.json) and [non-executable 400-item inventory](C:/Users/aashraf/.codex/visualizations/2026/10/06/01a1131b-eac2-7a31-afb4-f219a8dd6471/spq06/2026-10-09/execution-public-1.0.3/inventory-400.json).
- [Unassigned exhaustive ownership template](C:/Users/aashraf/.codex/visualizations/2026/10/06/01a1131b-eac2-7a31-afb4-f219a8dd6471/spq06/2026-10-09/execution-public-1.0.3/ownership-template.json) and [unqualified receipt template](C:/Users/aashraf/.codex/visualizations/2026/10/06/01a1131b-eac2-7a31-afb4-f219a8dd6471/spq06/2026-10-09/execution-public-1.0.3/qualification-template.json).
- [Worker source and asserted transformation provenance](C:/Users/aashraf/.codex/visualizations/2026/10/06/01a1131b-eac2-7a31-afb4-f219a8dd6471/spq06/2026-10-09/execution-public-1.0.3/workers/transformations.json).
- [Central reservation/import/analysis implementation](C:/Users/aashraf/.codex/worktrees/simphysqa/phi-jepa/src/simphysqa/execution_readiness.py), [standalone public executor](C:/Users/aashraf/.codex/visualizations/2026/10/06/01a1131b-eac2-7a31-afb4-f219a8dd6471/spq06/2026-10-09/execution-public-1.0.3/procedures/public_executor.py) and [common instrumentation](C:/Users/aashraf/.codex/visualizations/2026/10/06/01a1131b-eac2-7a31-afb4-f219a8dd6471/spq06/2026-10-09/execution-public-1.0.3/workers/execution_support.py).
- [Return envelope schema](C:/Users/aashraf/.codex/worktrees/simphysqa/phi-jepa/src/simphysqa/return-envelope.schema.json) and [per-file prompt/procedure mappings](C:/Users/aashraf/.codex/visualizations/2026/10/06/01a1131b-eac2-7a31-afb4-f219a8dd6471/spq06/2026-10-09/execution-public-1.0.3/file-generation-index.json).
- [Independent verification receipt](C:/Users/aashraf/.codex/visualizations/2026/10/06/01a1131b-eac2-7a31-afb4-f219a8dd6471/spq06/2026-10-09/execution-readiness-1.0.1/verification.json) and [actual 45-test log](C:/Users/aashraf/.codex/visualizations/2026/10/06/01a1131b-eac2-7a31-afb4-f219a8dd6471/spq06/2026-10-09/readiness-offline-tests-final-1.0.4.log).
- [Preservation baseline](C:/Users/aashraf/.codex/visualizations/2026/10/06/01a1131b-eac2-7a31-afb4-f219a8dd6471/spq06/2026-10-09/execution-readiness-1.0.1/preservation-before.json) and [after-work hashes](C:/Users/aashraf/.codex/visualizations/2026/10/06/01a1131b-eac2-7a31-afb4-f219a8dd6471/spq06/2026-10-09/execution-readiness-1.0.1/preservation-after.json).
- [Proposed development rehearsal, actual IDs and per-condition bounds](C:/Users/aashraf/.codex/visualizations/2026/10/06/01a1131b-eac2-7a31-afb4-f219a8dd6471/spq06/2026-10-09/rehearsal-proposal-1.0.0/proposal.json) and [55 unexecuted request/projection mappings](C:/Users/aashraf/.codex/visualizations/2026/10/06/01a1131b-eac2-7a31-afb4-f219a8dd6471/spq06/2026-10-09/rehearsal-proposal-1.0.0/file-generation-index.json).

## Frozen science and public packaging

The core remains 200 unique QA/200 groups, ten per domain/family cell, within the
400-item pool. The original test_id splits, exclusions, cutoffs and group identities
are verified. Nine enriched conditions plus the two existing Qwen structured-only
ablations evaluate those same 200 items. All 2,200 request bytes match the saved
preparation files; all nine scientific configurations match after moving **only**
local interpreter/cache/library paths to explicit bindings. No prompt, template,
model/quantization, decoding, stop/context/output/time allowance, parser, scorer,
unit/frame/tolerance, quaternion rule or selection decision is changed. The existing
48-hour aggregate ceiling and 43.14-hour historical size-decision forecast remain
unchanged. That forecast does not measure new instrumentation/another workstation.

The manifest projection retains every identity and original hash field but omits
organizer filesystem/evidence pointers. The original nested manifest hashes remain
authority. Internal package paths are relative. The ZIP contains 2,958 hashed files
plus its manifest; 110 complete development/held-out inspection examples are separate
from the full main requests. Historical workers are copied for provenance and never
used as the instrumented entry point. Old sealed workers and receipts are preserved.
No checkpoints, credentials, private gold/prose/rollouts/scoring records or organizer
reply database enter the transfer. Supplied explanation comparisons stay public.
Historical pilot response streams, launch-path receipts and pilot-render receipts
remain in the original archive, outside the final transfer. Copied stop metadata
retains provenance pointers to that untransferred historical evidence.

ZIP SHA256: `0fe1b8f9367b0217f8e39b5100bf56b234f8403691a66247f962caaea9c5134b`.
Package manifest SHA256: `e080dea1143d563b8c303231c5aa9d44a5522cee91e936f345a1b7768383834e`.

## Portable adapter and qualification

Each later executor supplies an interpreter, explicit environment/cache/model paths,
GPU UUID visibility, nvidia-smi path and (GGUF) pinned server/library/device bindings.
Scientific overrides are rejected. The coordinator approves a **fresh** qualification
receipt pinning package/worker/support/config/bindings, all model/tokenizer digests,
precision/quantization, GPU/VRAM, OS/WSL, driver/CUDA/backend versions and rendering,
stop and development-task evidence. The worker rechecks GPU name/UUID, VRAM/driver/OS,
backend versions, CUDA runtime for Torch, template and artifact identities. The
executor rehashes pinned cache files before model loading. GGUF keeps strict CUDA,
all-layer offload, fit-off, fixed KV/threads and no-context-shift options. The pinned
Linux server is not silently replaced by a Windows build. Incompatibility is a
blocker, not permission to shrink context/change model or quantization.

Main execution requires task_qualified scope. A separately authorized development
coordinator may later issue bounded runtime_qualified rehearsal contexts restricted
to the prespecified development IDs; this avoids a circular prerequisite while
collecting fresh task evidence. Main importer rejects rehearsal scope. No such
receipt/context/owner is issued here. GPU jobs must execute serially per device;
this version does not qualify concurrent capacity or malicious executor behavior.

## Logging contract and remaining unavailable measurements

| Artifact/field | Implemented definition and handling |
|---|---|
| result IDs/provenance | stage_key = sample_id \| condition_id \| representation \| stage; qualification/assignment/hardware-runtime/worker/scientific-config hashes, process/stage reservations and scope retained for every returned result |
| executed-requests / tokenized-prompts | exact canonical prepared request; full rendered prompt/token IDs; no repaired response or reconstructed assistant turn |
| raw_output / output_token_ids / raw_stream_events | old outputs kept; GGUF stream events and available vLLM partial IDs saved; Transformers cannot recover inaccessible partial tokens when generate raises before returning |
| input_tokens / output_tokens | rendered input ID count and **retained emitted ID count**, including saved stop IDs; not an inaccessible internal-reasoning count or guaranteed total generated tokens after a crash |
| termination | normalized complete/failed/length_limited/timed_out/interrupted/unknown; actual vLLM finish_reason/stop_reason and GGUF stop_type retained; Torch terminal-token/EOS/deadline evidence explicitly derived, not invented backend fields |
| latency_seconds | existing worker latency boundary retained, including existing decode/synchronization where present |
| total_stage_seconds | starts before seeding/render/tokenization, ends at result construction; result write excluded and captured in process accounting |
| runtime.json / process-receipt.json | model loading separately measured; full coordinator preparation + executor preflight/hash/process/loading/stages/I/O/teardown charged once, not repeated per item; transfer/queue wait excluded |
| device_memory | nvidia-smi device-wide samples: UUID/name, 0.5 s interval, successful count, sampled peak, errors, nullable unavailable windows; sampled high-water mark may miss peaks |
| peak_allocated_bytes / peak_reserved_bytes | original Torch process allocation counters, distinct from device-wide memory and potentially excluding child processes |
| central-parsed-records.json | parsed objects, exact parser diagnostics/failures, parser/scorer/analysis source hashes, reservation/process states, conditional receipts, invalid returns and conflicts; remains organizer-only |
| main-analysis.json | unchanged family endpoints and paired whole-group stratified 10,000-replicate percentile bootstrap, seed20261009; fixed selected-item denominators and visible missing/failure coverage |
| unavailable | separate prefill/decode/TTFT, semantic refusal classification, inaccessible reasoning and human explanation prose adequacy are not claimed measured |

Monitoring adds CPU and timing overhead and may alter the number of tokens obtained
at a wall deadline; unchanged generation calls do not prove identical samples on
another hardware/runtime. All nine model-load/generate/SamplingParams/LLM call ASTs
match the frozen workers. Revised inference behavior is **pending task qualification**.
Render/loading crashes can leave logs and unknown stages rather than returned output;
their bytes and reservations survive. Parseable failures remain unsuccessful in
primary endpoints. Automatic explanation facts/nonempty prose do not grade quality.

## Assignment, reservation, returns and central analysis

One central transactional SQLite ledger issues whole condition/representation shards
(200 initials and 40 possible conditionals), with no default all-conditions executor.
The template covers 2,640 unique possible keys:2,200 initial/440 conditional. Ownership
is null. Explicit stage filters make <=50-stage process batches. Unique keys reject
overlapping assignments/reservations across executors/roots before inference. Resume
returns never-reserved eligible keys only; no failed/reserved stage is released.

Process allocations reserve 600 seconds overhead plus unchanged stage timeouts under
172,800 aggregate seconds. Known ended lifecycle receipts charge measured work once;
unknown/orphan work retains its full bound and observed overruns. Conflicting lifecycle
receipts restore conservative unknown accounting. No automatic orphan release or
replacement attempt. Separate executors do not each receive48hours.

The coordinator parses/routs actual first turns using the accepted private source
scope. A supported continuation retains the original messages and exact raw assistant,
then the recorded query reply and exact main public update. Unsupported/absent/premature/
invalid responses produce unexecuted_conditional receipts. Stage2 receives no authored
assistant replacement, future observation or expanded/truncated history. Routing
evidence is returned and checked; a first-turn conflict blocks its continuation.

Return directories hash every file and contain tickets, assignment/qualification,
exact requests/render/token IDs/raw results, routing/history, process/runtime receipts
and measurements. Import preserves bytes in exclusive immutable source roots **before**
validation. Identical transport is recorded/counts once. Differing per-key artifacts
preserve both and block canonicalization, even if one appears successful. Other items
in the same transport are not automatically conflicted by an unrelated changed result.
Invalid/incomplete returns remain preserved with reasons and consumed reservations.
No latest/success/high-score preference, no pilot-to-main import. The organizer bridge
passes accepted canonical records to unchanged main_analysis, preserving missing and
failing items in all-item denominators. Source rehashing detects later import tampering.
This is a trusted coordinator/executor protocol; deliberately copying an already
launched ticket to evade a local exclusive marker is not cryptographically prevented.

## Actual offline verification and retained engineering failures

45 targeted tests pass:26 new behavioral tests and19 existing SPQ06 tests. New checks
cover exact bytes/relative paths/privacy, assignments/cross-root collisions, aggregate
budget/orphans, duplicate versus conflict handling, invalid hashes/CPU fallback,
actual-history assembly and returned continuation evidence, never-reserved resume,
memory unavailability/termination/timing, rehearsal scope rejection, central parsed
objects and unchanged analysis endpoints/paired denominators. One mocked Transformers
worker ran inside a temporary FIXTURE namespace with fake torch/model/tokenizer and
explicit MOCK_BACKEND_FIXTURE outputs. No answering weights or real main stages were
loaded/reserved; no mock result is empirical evidence.

Independent checks verify all2,200 source bytes,200 unique groups,20cells×10,
exclusions/original splits/nesting, exact nine configs, unchanged generation-call
ASTs,2958package hashes,110inspection requests and every ZIP entry byte. All
**10,190** original files in the sealed baseline plus
confirmation package remain hash-identical. CPU wheel creation and standalone public
package validation pass; required packaged schemas/worker resources are checked.

The first independent verifier failed on a broad '*pilot*' filename assertion.
Inspection found public render receipts and historical stop-event streams; final
export1.0.3 excludes them using an explicit whitelist while retaining the original
archives. Earlier public exports1.0.0–1.0.2 and partial verification1.0.0 remain as
intermediate offline artifacts; transfer only1.0.3. A Windows inline Python quoting
error and an apply_patch context mismatch affected only offline setup/documentation;
their diagnostics are retained. No scientific failure was replaced or rerun. The
final verification/ZIP checks pass; optional GPU execution is not exercised here.

## Proposed rehearsal and exact offline commands

The rehearsal proposal freezes five **existing accepted development** tasks through
the exact main projection, one per family spanning all four domains, shared by all
nine enriched/twoablation conditions.55initial+at most11supportedcontinuations,
66calls maximum. Proposed aggregate reserve28,320seconds (7h52m) includes15,120stage
seconds and22loading/process allowances×600seconds. Each later executor's reservation
is the sum of its agreed shards under that separate aggregate budget. Owners are
unassigned. No correctness/quality acceptance threshold. Unsupported first turns
stay unexecuted conditionals; stage2 coverage is explicitly reported. This is a
proposal, not authorization or a claim that a live rehearsal issuer has run.

Run from `C:/Users/aashraf/.codex/visualizations/2026/10/06/01a1131b-eac2-7a31-afb4-f219a8dd6471/spq06/2026-10-09`, using the CPU Python with
PYTHONPATH pointing to this checkout/src and PYTHONDONTWRITEBYTECODE=1/PYTHONUTF8=1.
New exports/ZIPs use exclusive output roots and do not overwrite sealed outputs.

```text
python -m unittest test_execution_readiness test_spq06 test_spq06_execution test_spq06_main test_spq06_analysis -v
python -m simphysqa.execution_readiness prepare-package --preparation main-preparation-1.0.0 --confirmation confirmation-1.0.2 --output <new-versioned-public-root>
python -m simphysqa.execution_readiness validate-package --package execution-public-1.0.3
python -m simphysqa.execution_readiness export --package execution-public-1.0.3 --output <new-exclusive.zip>
python execution-public-1.0.3/procedures/public_executor.py validate --package execution-public-1.0.3
python -m simphysqa.rehearsal_preparation --pilot pilot-1.0.0 --package execution-public-1.0.3 --output <new-exclusive-proposal>
```

Exact issue/prepare-job/launch/return/import/route/analyse commands are in the linked
README. Only prepare/validate/export and offline tests were executed here. The
independent verifier produced the delivered ZIP and verified every entry. No live
ledger/assignment/qualification/main job was created. Rehearsal/main launch requires
later explicit authorization and fresh compatible-runtime evidence.
