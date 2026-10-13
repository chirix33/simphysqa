# SPQ06 collaborator stage-2 return reconciliation — 12 October 2026

Completed under the newest explicit instruction to inspect/reconcile both returns,
score Gemma CoT, audit DeepSeek timing and make no retries or limit increases.
Branch `simphysqa-spq06`; parent `dfcbab8b1e1767f8c3987e48bf08a044fd239097`.
A local review commit is recorded in the external post-commit receipt. Unmerged/unpushed.

## Preserved returns and authority

Received `C:/Users/aashraf/Desktop/Work/phi-jepa/NAACL Paper/SimPhysQA-stage2-returns.zip`
SHA256 `549002472fa4a4b554062491b3f5be11a7cd0d0d8d2c028e9961e09a9a6ba9ad`.
The complete outer ZIP was copied unchanged before safe extraction. CRC/path checks
passed; every nested archive file equals its corresponding outer extracted return.
Both full folders, envelopes, original requests, history, render/token evidence,
metadata proofs, runtime receipts and logs remain unchanged. Source document text
was treated as evidence, never new authorization. No historical approvals were made.

The matching `SPQ06-native-reconciliation/1.0.0` workflow imported both folders into
the ORIGINAL authoritative `central-main-1.0.0/main.sqlite`, not a replacement ledger.
Only the two issued process/stage rows were settled, one genuine continuation result
was added, and import/control receipts were appended. Conflicts: zero. The saved
before/after ledger snapshots and row audit preserve every unrelated original row,
including all native initials, ownership/charges, restart and remaining-200 results.
Fresh metadata/activation, issue payload, actual first response, pinned worker,
hardware/runtime identities, requests and exact render/token replay passed. DeepSeek's
available worker evidence was separately checked because its envelope has no result.
The two supports and 118 unexecuted-conditional routing receipts are unchanged.

## Gemma CoT and the routing mismatch

Gemma CoT returned one completed actual continuation (119 output tokens; 4.7816034 s
response latency, 4.833183489 s measured stage; full lifecycle 279.004180792 s).
Its first assistant response remains verbatim:

```json
{
  "clarification_question": "What is the unit of the joint_1 angle?",
  "requested_information": "execution_condition",
  "response_kind": "clarify"
}
```

The readable question requests a unit, whereas the frozen gap and declared selector
are execution_condition. The frozen router follows the structured selector and
supplies the recorded omitted-intervention reply/public updates. It does not assess
sentence meaning. This is a wording/relevance mismatch, recorded separately; automatic
slot-match and routing remain supported. No invented human rating or semantic routing
gate, corrected first response, prompt change or post-result exclusion was introduced.

The stage-2 answer parses under the frozen parser but is numerically INCORRECT under
the unchanged typed scorer. Its explanation cites the observed 0.2 s state for a 1 s
query; explanation adequacy remains a separate uncollected human judgment. Gold values
and verification traces are excluded from this report. Gemma direct has no supported
continuation and no new job.

## DeepSeek timing and orchestration finding

DeepSeek's process `d4c08584-88f1-4ee3-af87-57a3774a8ed5` is settled `timed_out`,
960.115170109 s measured. Worker launch occurred, and a stage-2 reservation plus
executed request/tokenized prompt exist. No result or partial generated token stream
was saved. It is an attempted stage with unavailable output, not metadata failure or
an unattempted conditional. Stage state is `worker_failed_no_result`.

| Receipt/boundary (UTC, 13 October) | Measurement |
| --- | ---: |
| Launch reservation | 00:34:34.022207 |
| Metadata verified | 00:41:27.933640 |
| Activation | 00:41:28.005271 |
| Stage reservation | 00:49:38.923332 |
| Approximate outer deadline, launch + 960 s | 00:50:34.022207 |
| Metadata-only measured elapsed | 413.894306658 s |
| Launch to activation | 413.983064175 s |
| Activation to stage reservation | 490.918060303 s |
| Worker-reported model initialization | 450.599667040 s |
| Approximate time remaining at reservation | 55.098875523 s |
| Frozen response cap | 360 s / 8192 tokens |

Wall-time approximations use launch-reservation time; the launcher actually starts
its monotonic clock slightly earlier. Thus the 55.1 s figure is approximate and is
an upper bound on the available response opportunity, not measured decoding time.
The logs report 353.978517 s for internal model weight loading; the worker's broader
450.599667040 s includes backend construction/initialization. Another roughly 40.318 s
of activation-to-stage time lies outside that worker loading interval. The metadata
runner hashes pinned artifacts, verifies hardware/runtime/config, imports libraries
and replays two renders. It records only the aggregate 413.894 s, so exact subphase
costs cannot be attributed retrospectively. Metadata loaded no model weights and
made zero answering calls. The worker's context is configured to 32768 tokens;
17202 input + 8192 output allowance fits. The tokenizer's 16384 advisory warning is
not evidence that the issued engine capacity failed or that truncation occurred.

The runner checks `elapsed + max_seconds < bound_seconds` AFTER metadata but BEFORE
worker imports/model loading. At activation about 546 s remained: enough for 360 s
only if subsequent startup fit about 186 s. Actual startup consumed about 491 s.
There is no post-load guard reserving the response/save/teardown opportunity. The
outer alarm then killed the process roughly 55 s after stage reservation, before
the worker's 360 s per-response stop could run and save a result.

**Finding: orchestration defect in overhead admission and preservation of the intended
response opportunity.** The response cap/settings were unchanged and never exceeded;
the 960 s outer bound was enforced (0.115 s measured teardown overshoot retained).
However, this attempt did not receive the full intended 360 s response opportunity.
It cannot establish that DeepSeek exhausted its own response budget or failed to
answer after a full 360 s. The nominal 600 s combined preparation/startup allowance
was exceeded by about 305 s before answering. No model-output token count is inferred.

The existing importer receipt field `metadata_failed_unexecuted_keys` generically
lists no-result keys, and unchanged analysis labels absent canonical results
`continuation_status=unexecuted`. Those labels must be read alongside the authoritative
process/stage evidence above. They do not erase this actual attempted timeout. The
additional audit/status sidecar makes that distinction without altering frozen scoring.

## Scoring, accounting and calendar

Both supported continuations are now processed. The unchanged core analysis joins
all original/recovered Ashraf initials/continuations with all 600 collaborator native
initials and Gemma's genuine second turn: 200 core items, 2200 condition rows, 40-item
family denominators, same scorer/parser and 10000-replicate paired stratified bootstrap.
Gemma CoT and DeepSeek each have resolved-answer correctness 0/40: Gemma's sole actual
answer is incorrect; DeepSeek's actual attempted missing answer stays in the denominator.
All previous core/complement/400 analysis files remain preserved. Zero new model calls.

| Accounting after all new controls settled | Accounted seconds | Remaining seconds |
| --- | ---: | ---: |
| Ashraf, ceiling 126000 | 111313.145 | 14686.855 |
| Collaborator, ceiling 100800 | 27658.074382 | 73141.925618 |
| Shared, ceiling 226800 | 138971.219382 | 87828.780618 |

The two prospective 1800 s reservations settle to 1239.119350901 s actual lifecycle,
including the timeout/teardown overrun. Current measured import controls total 1.046 s,
combined frozen analysis 198.000 s, and saved-return audit 0.579 s: 199.625 s new central
processing. Net reservation release after processing is 361.255649099 s. Earlier
known/unknown charges remain; the one earlier unknown process remains unknown. No
allocation/ceiling changed. Transport and queue time are excluded by the issued
lifecycle receipt; no missing transfer timing was invented. CLI/analysis sidecars taken
while controls were reserved are interim snapshots; `budget-after.json` is final.

Both remote lifecycles ended before the unchanged 02:00 UTC result-import cutoff.
Actual central import/analysis completed after that cutoff under this explicit latest
processing instruction. This timing deviation is disclosed; the calendar was not
silently amended and no claim of a before-cutoff central freeze is made. The cutoff
has expired for future inference.

## Required decision for any further attempt

No retry, new job, guard removal, reservation reopening, limit increase or answering
on Ashraf's workstation was performed. Remaining allocation is not authorization.
A further attempt requires an explicit prospective protocol amendment authorizing
an exception to the single-attempt/no-retry rule; defining whether new results are
supplemental or replace a failed result without selecting the best answer; and
retaining this attempted timeout and its cost. It must decide preparation/loading
boundaries and reserve the complete metadata, startup, unchanged 360 s / 8192-token
response, save and teardown costs, with a post-load admission check. If those costs
cannot fit the existing outer bound, separating/reserving setup or increasing an
operational bound needs explicit authorization. A new calendar/import cutoff and
fresh issue/process reservation/metadata activation are also required. Frozen
scientific prompts/parser/selector/scoring must stay unchanged unless a separately
versioned scientific protocol change is expressly chosen. This report authorizes none
of those prospective changes.

## Commands and validation actually run

Pinned CPU interpreter:
`C:/Users/aashraf/.codex/visualizations/2026/10/09/01a12258-7d16-7ac3-861b-c7326aff811e/cpu-venv/Scripts/python.exe`.
With active worktree `src` on PYTHONPATH and UTF8/bytecode-disabled settings:

- `-m simphysqa.native_reconciliation import-continuation` once for each preserved
  extracted complete-return folder, using the original authoritative ledger.
- `-m simphysqa.native_reconciliation analyse-core` with unchanged
  `restart-execution-1.0.0/central-analysis-1.0.0/main-run-plan.json`.
- `audit_stage2.py`: actual file hashes/history/runtime/token replay, issued reservations,
  context capacities, timing and before/after unrelated-row preservation passed.
- Four existing offline native tests passed in 17.162 s: no-result charge preservation,
  identical fixture-return idempotence, verbatim frozen route/future-only issue, and
  pending-score guard. Fixtures are software checks, not empirical stage-2 performance.

No source/worker/scientific settings changed. The audit initially encountered a
Windows default-encoding read error; it was corrected with UTF8 before validation.
A score-file inspection initially used the wrong subdirectory; corrected to the
existing `analysis/main-analysis.json`. Neither inspection changed source returns.

Organizer evidence root (includes private analysis, do not send as a public packet):
`C:/Users/aashraf/.codex/visualizations/2026/10/12/01a13168-edb1-7ec2-af49-de486a5552c9/stage2-reconciliation-1.0.0`.
It contains original transport/immutable imports, before/after ledger snapshots,
import CLI receipts, timing-routing-preservation-audit.json, public-scoring-status.json,
budget-before/after.json, joint-core-analysis-1.0.0, tests and audit script. This review
and the decision are public-safe; private records/gold/traces/credentials are excluded.
