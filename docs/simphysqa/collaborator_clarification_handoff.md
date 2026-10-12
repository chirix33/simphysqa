# Collaborator clarification follow-up — original-return export required

Prepared 12 October 2026 for the frozen 200-item core. This packet is public.
**No stage-2 jobs have been issued. Do not execute the draft requests.**

The received ZIP contains 600 raw first responses, exactly 200 for each of
`deepseek_r1_distill_qwen32b`, `gemma3_27b_qat_direct` and `gemma3_27b_qat_cot`.
The raw-file IDs and request/worker/condition hashes match the sealed core package.
Complete original returns and their original authority are still required.

The organizer's frozen parser and router were applied to all 120 clarification
responses. These are diagnostics of received raw files, pending authenticated import:

| Condition | Supported | Parser rejected | Schema rejected | Other unsupported |
|---|---:|---:|---:|---:|
| DeepSeek native | 1 | 37 | 2 | 0 |
| Gemma direct | 0 | 39 | 0 | 1 wrong selector |
| Gemma CoT | 1 | 37 | 1 | 1 absent clarification declaration |

The two candidate continuations are:

- DeepSeek: `spq-clarification-cc02e01f8d454b2374dd51c6`.
- Gemma CoT: `spq-clarification-f5f456979c9929dee15defae`.

All 118 unsupported cases have explicit diagnostic unexecuted-conditional receipts.
The `draft-requests/` files contain the actual first assistant response verbatim,
the recorded reply and the frozen public task updates. They contain no private
records, gold answers or verification traces. They have no issued assignment,
reservation, approved machine qualification or fresh metadata proof and cannot be
launched. `diagnostic-receipts/` is not a substitute for central ledger routing.

Gemma CoT's structured field declares `execution_condition`, while its sentence
asks for the angle unit. This wording concern is recorded separately. It does not
change the frozen structured routing decision or establish a human quality rating.
The parser, response schema, selector rules, prompts and scoring remain unchanged.

## Export the existing first-turn jobs without running them again

Preserve the original completed job folders and original execution package. Export
the complete jobs, not only `worker-output/results/`. The received files identify
12 original process IDs, three assignment hashes and three qualification hashes
that are absent from the organizer's central ledger. Their original ownership,
reservations and accounting must be reconciled from actual historical evidence;
newly authored retrospective tickets or qualifications will not close this gap.

From the directory where this packet is extracted, run these CPU-only commands in
the collaborator's Linux/WSL shell:

```bash
python3 recover_returns.py inventory \
  --search-root "$PWD" --search-root "$HOME" \
  --expected "$PWD/expected-results-index.json" \
  --output "$PWD/original-job-inventory.json" \
  --export-root "$PWD/original-first-turn-returns"

# Only when the inventory reports ready_to_export:
python3 recover_returns.py export \
  --expected "$PWD/expected-results-index.json" \
  --inventory "$PWD/original-job-inventory.json"
```

`python3` performs file discovery only. The export helper runs each original public
exporter with that job's actual pinned `bindings.json` interpreter and the original
package matched by `launch.json` package hash. The inventory prints the exact
individual export commands, including real interpreter/package/job paths. It invokes
only `public_executor.py return`, never `launch` or an answering worker. Search is
bounded, skips model/cache/environment directories and never follows directory
symlinks. If the jobs or package are outside these roots, repeat inventory with
their actual root supplied using another `--search-root` and a fresh output filename.
Export directories are exclusive; preserve a partial export if an error occurs.

The successful export produces `original-first-turn-returns.zip` and its SHA-256.
Return that ZIP and `original-job-inventory.json`. The exact pinned paths are not
available to the organizer yet; this discovery procedure reads them from existing
jobs instead of inventing them.

Each complete job must retain:

- Original assignment, ticket, qualification, bindings, resolved condition,
  execution context, launch and pre-reservation metadata proof.
- Every executed request, rendered prompt/input token sequence, raw result/output
  token sequence, stop/backend events and any original continuation history.
- Runtime and full process lifecycle receipts, timing/memory evidence and original
  Gemma server/device/offload receipts where applicable.
- The original envelope or an envelope produced by the documented original
  `return` exporter, with every listed file and exact hash.

Also supply the existing historical coordinator issuance/reservation and accounting
receipts and the actual development/task-qualification evidence or approved mapping
referenced by these jobs. Return existing records, not reconstructed approvals. If
the collaborator used a separate local ledger, identify its original path and issuer
and provide the original scoped receipts for these 12 processes; do not send private
benchmark databases or treat that ledger as a replacement central authority.
Send a missing-evidence report if any required original files no longer exist.
There is no first-turn rerun or synthetic provenance recovery path in this handoff.

## What happens after those exports arrive

The organizer validates and preserves the original returns, reconciles their
actual authority/accounting, and imports only verified returns through the existing
central workflow. A provenance mismatch blocks issuance; it is not resolved by
creating fresh first-turn assignments or inferring process timing from token counts.
Duplicate identical transports count once; differing returns remain conflicts.

The organizer then writes canonical supported/unexecuted-conditional receipts and
prepares condition-specific stage-2 jobs owned by the original collaborator. Fresh
metadata-only preflight must run on that qualified collaborator workstation and
include actual-history rendering/capacity, model/runtime/artifact/template/stop
identities, device binding and backend configuration. Gemma must use its documented
GGUF qualification path; an HF-only preflight is not a Gemma substitute. A stale
proof, missing task evidence, overflow or unresolved allocation prevents reservation.
Do not truncate history, change context limits or use accuracy as a launch gate.

The allocation is 100,800 seconds for the collaborator under the same central
226,800-second ceiling. The visible ledger currently records no collaborator charge;
this does not establish the true remaining allowance until these original processes
are accounted for. The result-import cutoff is 13 October 02:00 UTC / 12 October
21:00 America/Chicago. Batches, export, transfer and central import must fit the
remaining allocation and calendar; this packet does not extend either.

The later issued handoff will contain actual pinned launch and return commands,
jobs/tickets and validated routing. Execute only those issued jobs once, serially,
with the same models/settings and supplied dialogue unchanged. Export every full
second-turn job with the same original public `return` command and return its whole
envelope/hashed payload, including requests, renderings, raw output, routing and
runtime/process receipts. Preserve failures and partial/unknown work; no automatic
retry, initial rerun, answer repair, replacement or independent new ledger.

Resolved clarification results stay **pending** until supported continuations have
been processed. Subsequent central scoring uses authenticated first and second
turns together with unchanged scorers and fixed 200-item/40-clarification denominators.
The running remaining-200 evaluation, core results and branch are preserved. No
answering inference runs on Ashraf's workstation for these collaborator conditions.

No credentials, private records, gold values, private witness completions or
verification traces belong in the public return/handoff.
