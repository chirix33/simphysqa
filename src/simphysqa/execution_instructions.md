# SPQ06 portable public execution package /1.0.0

This is the frozen **200-item** experiment: nine enriched conditions and two
prespecified structured-only ablations, 2,200 exact initial requests and at most
440 conditional continuations. The ownership template is **unassigned**. Preparing
or transferring this package authorizes no inference. The 400-item inventory is
preserved preparation inventory and has no executable request mapping here.

`selected-items.json` is a lossless identity/mapping projection of the original
frozen core manifest; only organizer filesystem/evidence pointers are omitted.
Original manifest hashes are retained. Requests are exact copies, not reserialized.
The full 110 inspected examples are under `inspection/`; those are unexecuted
inspection material, not a replacement for the complete 2,200 collection. Template
and inherited stop evidence is under `templates/` and `runtime-stop-evidence/`.
Historical pilot response streams, render receipts and server launch paths remain
in the original confirmation archive; they are excluded from this public transfer.
The copied stop contract retains their original provenance pointers, not local
execution inputs. GGUF vocabulary/properties and pinned HF stop procedure source
are present. The original archive is the authority for untransferred historical
observations; none is interpreted as a main response.

Private gold/prose/traces/witnesses/rollouts/scoring records and credentials are
absent. Supplied explanation comparisons remain intentional public task evidence.
Never give a model the coordinator database, scoring checkout or routing records.
Workers read only issued public request lists, model/configuration metadata and
their execution context. They import no dataset/scoring/simulator modules.

## Transfer and paths

Transfer the entire ZIP, verify its separately supplied SHA256, extract into a new
root, then run `python procedures/public_executor.py validate --package <root>`.
The package manifest hashes every payload/source/configuration file. Never change
prepared request bytes. Internal file references are relative. Model/cache and
interpreter bindings are explicit local configuration, not guessed workstation
paths. `conditions/` contains unchanged scientific settings and model file digests;
old local path fields are omitted and bound separately. `historical-workers/`
preserves old source for provenance, but is never the execution entry point.

The coordinator installs the committed SimPhysQA source and CPU requirements.
The public executor needs Python 3.11+ stdlib for the adapter, and the **exact**
backend dependencies in its assigned condition. No network access or automatic
model download. Transformers/vLLM snapshots must retain pinned revision-directory
names and every `weight_files` hash. GGUF requires the pinned GGUF and server binary
digests and library bindings. A Windows-native server with another digest does not
silently substitute for the pinned Linux server: qualify compatible WSL/runtime or
report incompatibility. Hardware differences are recorded, not concealed.

## Qualification gate

Before a later authorized job, each condition/representation requires a newly
approved **task_qualified** receipt covering the instrumented worker/support/package,
scientific and resolved configuration, portable bindings, model files, tokenizer
template, precision/quantization, GPU UUID/name/VRAM, exact `platform.platform()` OS,
WSL status, driver, CUDA/runtime and backend versions, and hashed passed rendering,
stop and actual development-task rehearsal evidence. Old worker/pilot receipts do
not qualify this version. Offline metadata/render success alone is insufficient.
Do not load weights during this infrastructure milestone. Native reasoning/decoding/
context/stop settings remain exactly as saved; no substitutions for insufficient VRAM.
Bindings require `CUDA_VISIBLE_DEVICES` equal to the qualified GPU UUID; the worker
uses logical CUDA0 inside that visibility. GGUF's explicit `llama_device` must match
the qualified filtered CUDA device. Workers reject CPU fallback. Missing required
device/driver monitoring preflight rejects execution rather than assuming a GPU.

## Organizer commands (later, not executed during readiness)

Use one central SQLite database on a local organizer filesystem, never cloned or
independently re-created per executor. Transactions and unique stage primary keys
prevent overlap across job roots. Avoid SQLite on unqualified network filesystems.
Back up the organizer ledger without using a backup to grant replacement attempts.

```text
python -m simphysqa.execution_readiness init-ledger --package <package> --ledger <central.sqlite>
python -m simphysqa.execution_readiness issue --ledger <central.sqlite> --executor <agreed-id> --shard <condition--representation> --output <new-assignment.json>
python -m simphysqa.execution_readiness approve-qualification --ledger <central.sqlite> --receipt <fresh-qualification.json>
python -m simphysqa.execution_readiness pending --ledger <central.sqlite> --assignment <id> --executor <agreed-id>
python -m simphysqa.execution_readiness prepare-job --ledger <central.sqlite> --assignment <id> --executor <agreed-id> --qualification <approved-hash> --keys <explicit-never-reserved-keys.json> --bindings <qualified-bindings.json> --output <exclusive-job>
```

No default all-conditions executor. Each issued condition/representation shard
contains all 200 items and its 40 clarification conditionals. Stage filters permit
bounded batches, but initial/conditional ownership stays together. The coordinator
keeps batches at the frozen maximum of 50 stages per process. It
reserves stages and the process allocation **before** issuing the job directory.
Transfer the public job directory plus package; executor launch recomputes actual
package/worker/support/request/config/model digests at the local paths. Already
reserved stages are never scheduled again, even if no result exists. A lost ticket
or interrupted process is unknown work, not permission for another attempt.

```text
python procedures/public_executor.py launch --package <local-package> --job <issued-public-job> --authorize-main
python procedures/public_executor.py return --job <issued-public-job> --output <exclusive-return>
python -m simphysqa.execution_readiness import --ledger <central.sqlite> --source <return-directory> --output <immutable-import-root>
```

The aggregate ceiling is 172,800 seconds across executors, not per machine. Each
process reserves 600 seconds overhead plus unchanged stage timeouts. Unknown work
retains the entire allocation. A validated ended process receipt charges the full
measured lifecycle once; known completed work can release unused **time**, never a
stage attempt. Overruns remain actual charges and block further reservations.
Work includes coordinator job preparation, executor hash/preflight, loading,
render/tokenization, response processing and teardown; transfer/queue wait is
excluded. OS timeout/kill overhead can overshoot; preserve the overrun. Executors
must never launch the same issued ticket twice: exclusive launch markers enforce
this within the original job root; central return/reservation validation detects
transported copies. Deliberately copying a launched job to evade a marker is outside
the trusted executor protocol; no offline ticket can prevent malicious duplication.

## Clarification, coordinator only

Import and validate actual first-turn output, then invoke:

```text
python -m simphysqa.execution_readiness route --ledger <central.sqlite> --key <sample|condition|representation|1> --preparation <original-private-preparation> --output <exclusive-route.json>
```

This uses accepted `parse_answer`, `route_reply` and `main_public.continuation`.
Supported actual turns receive only the recorded missing query information and
exact public update. Their raw assistant text is retained verbatim, with all initial
messages. No authored gold question replaces the first turn. Unsupported, absent,
premature, failed or unparsable requests get explicit `unexecuted_conditional`
receipts, no stage-2 model attempt. Supported stage 2 is issued to the same owner;
no context expansion or history truncation. A late first-turn conflict blocks its
continuation and canonical analysis. Central scoring uses separate private records.

## Returns and analysis

Returns contain issued assignment/qualification/bindings/ticket/context, exact
executed requests, rendered prompts/token IDs, raw output/token IDs/backend events,
timing/memory/provenance, process receipt/log and an envelope hashing every file.
Incomplete returns preserve bytes and unknown/missing execution reasons. Import
creates exclusive source directories; no overwrite or latest-success choice.
Identical transport hashes count once with a duplicate receipt. Differing artifacts
for the same key (including invalid evidence) preserve both, mark conflict and block
that key pending explicit disposition. No automatic conflict-disposition command.

```text
python -m simphysqa.execution_readiness analyse --ledger <central.sqlite> --plan <original-main-run-plan.json> --output <exclusive-central-analysis>
```

The bridge saves parsed objects/diagnostics and parser/scorer/source versions beside
unchanged `main_analysis.assess`/`paired_intervals`. Primary denominators retain every
selected item and condition; missing/failing/conflicted returns remain unsuccessful.
Valid-only numerical errors and routing-conditional summaries require coverage.
No pilot responses are main results. Explanation factual validity is separate from
uncollected human prose adequacy. No inference or benchmark claims arise from mocks.

## Essential measurements and limitations

Old latency, raw output and token fields are retained. Total-stage timing begins
before seeding/render/tokenization and ends at result construction (excludes result
file write); process lifecycle captures that I/O plus loading/teardown once.
Transformers records derived terminal-token/EOS/deadline evidence; vLLM saves its
actual `finish_reason` and `stop_reason`; GGUF preserves streaming events/stop_type.
Normalized states distinguish complete/failed/length_limited/timed_out/interrupted/
unknown. Partial vLLM/stream outputs are retained where available. Transformers may
not expose partial tokens if its generate call raises before returning; do not
claim that inaccessible output was recovered. Render/loading crashes may leave only
a process log and unknown reserved stage, which importer reports as incomplete.

Device-wide nvidia-smi memory samples use 0.5-second intervals and identify UUID,
sample count/peak/errors and nullable unavailable windows. Sampling may miss peaks.
Torch allocated/reserved peaks remain different process-allocator fields and can
exclude backend children. Qualification uses actual preflight device metadata;
sample failure during a stage yields null/unavailable rather than zero. Monitoring
adds CPU/process and timing overhead; the revised worker requires task qualification.
Generation call arguments, seeds, rendering and acceptance behavior are unchanged.
No separate prefill/decode/TTFT or automatic semantic refusal classification is
implemented. Reasoning diagnostics inspect emitted text only. Exact token counts
include rendered prompt and emitted token IDs, not unexposed internal reasoning.

## Proposed later development rehearsal (NOT authorized/executed here)

Use five accepted development examples through exact main projection, one per
family, distributed over all four domains without claiming a balanced quality
sample. Each of the nine enriched and two ablation representations sees the same
five tasks: **55 initial requests, at most 11 actual supported continuations**.
Retain all failures and never substitute an authored first turn. Proposed hard
aggregate reserve is **28,320 seconds (7h52m)**: 15,120 seconds stage allowances
plus at most 22 separately loaded processes ×600 seconds. This is independent of
main's 48h ledger. Each executor's bounds equal the sum of only its later agreed
shards, under this aggregate ceiling; no owner is assigned now. Qualification must
include all five families, exact chat rendering/stop checks and actual conditional
turns where supported; unsupported continuations are explicit and cannot establish
stage-2 task qualification. Request separate rehearsal authorization later. Freeze
actual development IDs and receipts before that run; this plan does not infer
permission from the previously executed 20-item pilot.
The proposal's development IDs and 55 initial payloads are frozen in the separate
rehearsal proposal export. A future authorized development coordinator must issue
its own bounded reservations and fresh `runtime_qualified` contexts, restricted
to those IDs (at most six stages per condition/representation), with an explicit
`development_rehearsal` scope and manifest hash. This bootstrap permits recording
task evidence after metadata/hardware/runtime/render/stop qualification; it does
not falsely require that task rehearsal to have already run. The main issuer and
importer accept only `task_qualified` main-scope evidence. This milestone prepares
the proposal, not a live development issuer or any qualification receipt. Interface
qualification has no correctness or prose-quality acceptance threshold.
