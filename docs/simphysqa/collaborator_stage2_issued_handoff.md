# Issued collaborator clarification jobs — run exactly once

This is the one runnable public handoff for two central prospective stage-2 jobs.
It contains frozen public workers, 120 canonical routing receipts and the exact two
supported conversations. Original 600 first turns were reconciled as independent
local execution; their approvals/local process identities were not rewritten.
The two NEW jobs are assigned to Collaborator and reserved centrally. They are
issued_pending_remote_metadata until actual on-machine verification permits a
single answer call. No first turns, other conditions or further continuations.

Extract this ZIP once into the new, exact directory below. Do not overwrite an old
folder, edit files, copy jobs to another attempt, reset run folders/host attempt
guards, rerun a completed/failed command or change model/settings/history.

```bash
mkdir /mnt/c/Users/mmujawar/VisualStudioCode/SimPhys/handoff/clarification-stage2-1.0.0
# Extract the received ZIP's contents into that directory; keep its manifest.
```

The pinned original model/artifact/runtime paths are in each jobs/*/job.json.
No model downloads or runtime upgrades are part of this handoff. Both jobs are
serial on the original GPU0/UUID. Fixed host locks/attempt guards survive copied
handoffs; failure retains the attempt and its complete return must be exported.
Do not remove guards or retry metadata/answering with the same issue.

Run DeepSeek once, then export its entire return even if the run reports failure:

```bash
/mnt/c/Users/mmujawar/VisualStudioCode/SimPhys/runtimes/deepseek/bin/python -B /mnt/c/Users/mmujawar/VisualStudioCode/SimPhys/handoff/clarification-stage2-1.0.0/native_remote.py run --handoff /mnt/c/Users/mmujawar/VisualStudioCode/SimPhys/handoff/clarification-stage2-1.0.0 --job deepseek --authorize-stage2
/mnt/c/Users/mmujawar/VisualStudioCode/SimPhys/runtimes/deepseek/bin/python -B /mnt/c/Users/mmujawar/VisualStudioCode/SimPhys/handoff/clarification-stage2-1.0.0/native_remote.py export --handoff /mnt/c/Users/mmujawar/VisualStudioCode/SimPhys/handoff/clarification-stage2-1.0.0 --job deepseek --output /mnt/c/Users/mmujawar/VisualStudioCode/SimPhys/handoff/clarification-stage2-1.0.0/deepseek-stage2-complete-return.zip
```

Run Gemma CoT once, then export its entire return even if it reports failure:

```bash
/mnt/c/Users/mmujawar/VisualStudioCode/SimPhys/runtimes/control/bin/python -B /mnt/c/Users/mmujawar/VisualStudioCode/SimPhys/handoff/clarification-stage2-1.0.0/native_remote.py run --handoff /mnt/c/Users/mmujawar/VisualStudioCode/SimPhys/handoff/clarification-stage2-1.0.0 --job gemma-cot --authorize-stage2
/mnt/c/Users/mmujawar/VisualStudioCode/SimPhys/runtimes/control/bin/python -B /mnt/c/Users/mmujawar/VisualStudioCode/SimPhys/handoff/clarification-stage2-1.0.0/native_remote.py export --handoff /mnt/c/Users/mmujawar/VisualStudioCode/SimPhys/handoff/clarification-stage2-1.0.0 --job gemma-cot --output /mnt/c/Users/mmujawar/VisualStudioCode/SimPhys/handoff/clarification-stage2-1.0.0/gemma-cot-stage2-complete-return.zip
```

The run command performs a fresh METADATA-ONLY phase before the answering worker:
hash pinned artifacts/template/worker/support; verify original hardware/OS/driver,
CUDA numeric-index/UUID and exact backend versions/configuration; reproduce an
actual original saved prompt/token sequence; render the FULL actual conversation
and check input+output capacity. DeepSeek uses frozen 0.93 vLLM ModelConfig without
creating an LLM instance. Gemma uses pinned CUDA device listing and CPU GGUF
vocabulary tokenization, with the frozen template and no server/model load in the
metadata phase. Pinned pure-Python Jinja2 3.1.6 / MarkupSafe 3.0.4 and their licenses are bundled for metadata rendering; no installation or model-environment changes are needed.
DeepSeek's pinned environment needs its existing Transformers/vLLM dependencies.
Changed artifacts/hardware or other missing original runtime dependencies stop and are exported as failure;
do not install substitutions or alter the evaluated model to force completion.

Only a passed fresh proof (within 300 s) activates the issued worker. The metadata,
loading, one actual stage and teardown share the process bound: 960 s DeepSeek,
840 s Gemma CoT (600 s overhead plus frozen 360 s / 240 s answering limits). SIGALRM and
worker deadlines bound the lifecycle; no automatic retry or context truncation.
No changed parser, schema, prompts, selector rules, sampling, precision or scoring.

The actual first assistant response is verbatim, including reasoning. The supplied
user message contains the recorded missing selector and exact public updates;
it contains no answer. Keep those messages unchanged. Gemma CoT's unit-question
wording concern is separately recorded; its declared execution_condition routes
under the unchanged rule. There is no new semantic routing gate or human grade.

If a run exits nonzero but created a runs/<job>/process-receipt.json, export that
failure with the command above and send it. If no run folder/receipt exists (for
example a prior-attempt guard, invalid bundle or expired cutoff refused startup),
send the exact sanitized error and preserve all files; do not manufacture receipts.
If an item has incomplete request/render evidence, preserve the full run folder
and report that export failure rather than rerunning or inventing missing records.

Return BOTH complete-return ZIPs and their printed SHA256s. Each export includes
the issued job/routing, fresh metadata/qualification/activation, exact executed
request/rendered prompt/input IDs/raw output/output IDs/stop events, runtime,
memory/timing and process lifecycle logs/receipt plus the immutable return envelope
and every listed hash. Do not send only the two result JSONs. No credentials or
organizer-private records/gold/verification traces belong in this transfer.

The original budgets remain unchanged: collaborator 100,800 s, Ashraf 126,000 s,
shared 226,800 s. Original native measurements plus explicitly unknown outer bounds
were recorded centrally once; they are not presented as new historical tickets.
The unchanged result-import cutoff is October 12, 21:00 America/Chicago / October 13
02:00 UTC. Each job must fit its bound PLUS600 s export/central-import reserve before
that cutoff. Transfer promptly; the runner refuses a late start. No ceiling or
calendar extension is granted by this handoff.

Resolved clarification scoring is pending until both supported jobs' returns are
processed centrally. The organizer imports and scores genuine first/second turns
together with unchanged core 200 denominators/scorers/bootstrap. No independent
ledger or grading/private-data access is needed on your machine.
