# P12 approved full enrichment — 28 September 2026

Latest status: [two-record recovery completed](P12_enrichment_recovery.md).
Enrichment coverage is now complete; the original restart failures and charges
below are preserved as historical evidence.

Final update: the worker finished on 29 September. The
[completion audit](P12_enrichment_completion.md) verifies 8,273 new successes,
two unresolved restart records, and $313.085521 charged/reserved. All confirmation
notes are present. The original deadline has expired; the status and recovery
history below do not authorize starting another run.

Second restart recovery, 2026-09-29 12:39 UTC: worker absent again. Verified
5,988 successes, $241.081671 actual usage charges, and the first interruption's
$0.30531 retained reserve. A second orphan attempt has no response; reserved
$0.30570 and retained another unresolved failure without replay. Total charges
and reserves before resume: **$241.692681**. Prior evidence is preserved in
`recovery-20260929-1238/`; the source, configuration, $475 cap and original
20-hour deadline are unchanged. See [second reconciliation](artifacts/P12_enrichment_full/recovery-20260929-1238-reconciliation.json).

Windows System events show repeated Kernel-Power 41 / EventLog 6008 unexpected
shutdowns; they do not identify a specific hardware or software cause. A separate
earlier User32 1074 event recorded a planned OS upgrade restart. No power/update
settings were changed. No matching recent BugCheck/WHEA/volmgr events were
returned by the bounded follow-up query.

For a status check that detects a dead process or stale PID after restart, run:

```bash
python tools/enrichment_live_status.py
```

This checks both the actual process command and held worker locks, preserves the
saved status timestamp and writes `live-status.json`. The pinned supervisor is
unchanged. Two offline tests cover stale PID/lock cases and genuine live status.
An exported JSON file is still a snapshot; rerun this command for a live check.

Second resume verified at 12:42:11 UTC: successful count advanced from 5,988 to
5,989, with the next request in flight. Two prior unknown requests remain
separately accounted. The original deadline is 2026-09-29 17:35:44 UTC
(12:35:44 p.m. America/Chicago); it was not extended for downtime.

Restart recovery, 2026-09-29 05:23 UTC: no worker survived the workstation
restart. The saved `running` label was stale. Audited 5,568 successful outputs,
their cache checksums, raw responses and reconciled usage charges ($228.820201).
One additional provider attempt record had no saved response or spending row;
its dispatch status cannot be established after power loss. Conservatively
reserved its entire $0.30531 maximum, counted it against the request allowance,
and retained it as a failed/unresolved record without replaying it. No specimen
or failure is silently dropped; complete coverage remains false until resolved.

Preserved pre-recovery ledger/status/deadline in native
`recovery-20260929/`. Resumed with the exact same approved configuration, source,
spending limits and original deadline; no budget was reset. See
[reconciliation evidence](artifacts/P12_enrichment_full/restart-reconciliation.json)
and [read-only audit](artifacts/P12_enrichment_full/restart-audit.json).
On a future abrupt restart, a saved status label alone does not prove the process
is alive; check the worker and locks before using the resume command.

Resume confirmed at 05:25:14 UTC: successful count advanced from 5,568 to 5,569,
with another new request in flight. Supervisor PID 595 / worker PID 596 are the
resumed processes. Initialization took about two minutes to traverse previously
processed public records before dispatching new work.

Launch verified at 2026-09-28 21:36:57 UTC: supervisor PID 367 and scope worker
PID 368 were running; eight training/validation requests had succeeded, with
$0.420976 reconciled usage charges and a ninth request in flight. This is a launch
check, not a completion result. Use the live status below for subsequent progress.

The user approved the additional **$475 maximum for both scopes**, following the
[pilot and concrete proposal](P12_enrichment_pilot.md). This authorizes enrichment
of the remaining 7,775 training/validation records and 500 frozen confirmation
public inputs. The earlier $1.284679 pilot charge remains separate. No training,
test scoring, answer-model generation or paper edits are started by this run.

Checkout: `main`, base `248575fd500947edd325836e636aebe41f9f65d0`, with preserved
uncommitted P12 work. The reviewed enrichment implementation remains
`0864994441bd3cd67767cf8af6954c785d600c62f57e03bc3a4f7676d2f14180`.
The added supervisor has its own content hash in the approved configuration;
it orchestrates the existing runner without changing requests, parsing or budget
accounting. Native artifacts are isolated in
`/home/aashraf/phi-jepa/p12-enrichment-full-01`.

| Scope | Missing unique requests | Hard spending cap | Attempt cap including retries |
|---|---:|---:|---:|
| Training/validation | 7,775 | $425 | 8,942 |
| Confirmation | 500 | $50 | 575 |
| Shared total | 8,275 | **$475** | **9,517** |

The supervisor runs scopes sequentially, training/validation first. It imposes
a 20-hour elapsed deadline that persists on resume, in addition to the existing
20-hour cumulative provider-call allowance and 2 GB artifact cap. Every request
uses a durable conservative reservation, including retries. Unknown charges
remain reserved. Scope limits cannot borrow from one another; a scope cap stops
the shared run. Successful requests and terminal failed records are not repeated
automatically. An unresolved in-flight reservation requires reconciliation.

Official [model pricing](https://developers.openai.com/api/docs/models/gpt-5.6-sol)
and [pricing tables](https://developers.openai.com/api/docs/pricing) were fetched
again in the approval session and still support the standard short-context rates:
$4 input, $0.40 cached read, $5 cache write, $20 output per million tokens. Existing
higher reservations are retained. The full run has its own dated verification
file; the original pilot proof is preserved. Pricing proof must be less than
24 hours old at every dispatch.

The preflight rechecks all 8,538 public request identities and compatible caches,
retaining 263 existing notes. The OpenAI enrichment model, medium reasoning,
prompt, schema and public observation boundaries remain frozen. Confirmation
inputs stay outside training/checkpoint selection and prompt development. Local
Qwen and Llama direct-answer inputs do not receive enrichment.

Eight targeted offline tests passed, including supervisor failure/in-flight
reporting, no launch without scope authorization, durable global/scope caps and
usage accounting. The preceding broader qualification suite passed 54 tests.

## Live status and resume

The supervisor writes [status.json](artifacts/P12_enrichment_full/status.json)
approximately every 30 seconds and at scope completion. It writes
`completion.json` automatically when it finishes or stops; `all_records_successful`
distinguishes full coverage from a stopped or partly failed run. Raw responses,
per-request results, caches and the authoritative spending ledger stay in the
native run directory. Compact status/configuration are exported to
`docs/reviews/artifacts/P12_enrichment_full/`; the final ledger is also exported.

The [approved configuration](artifacts/P12_enrichment_full/approved-config.json)
is distinct from the unchanged disabled proposal. Credentials are read only by
the worker at its explicit provider boundary and are never put in these artifacts.

In the existing WSL core environment:

```bash
cd /mnt/c/Users/aashraf/Desktop/Work/phi-jepa/phi-jepa
source /home/aashraf/phi-jepa/.venvs/phi-core/bin/activate
python tools/enrichment_run_control.py status
# Resume only after checking stopped/in-flight status; preserves all caps:
python tools/enrichment_run_control.py start
```

An active worker makes `start` fail rather than creating another spender. Never
delete the ledger, reset the persisted deadline or edit the approved configuration
to resume. The two original scope commands remain usable as documented in
[the enrichment pipeline](../P12_enrichment_pipeline.md), but the supervisor is
preferred because it handles both scopes and writes completion status.

The machine must remain awake with WSL running. An interruption preserves completed
outputs and reservations; it is not evidence that remaining requests completed.
After completion, audit coverage before preparing embeddings or enabling the
separate expanded training study. Llama qualification still needs authorized
access to its pinned gated checkpoint.
