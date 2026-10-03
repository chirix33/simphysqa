# P12 separately budgeted enrichment commands

Approval follow-up: the user authorized the additional $475 for both scopes.
Use [the full-run supervisor/status guide](reviews/P12_enrichment_full.md).
The pilot commands and original approval procedure below are historical; the
disabled proposal is preserved alongside a distinct approved configuration.

Use Ubuntu 24.04 WSL and the existing core environment:

```bash
cd /mnt/c/Users/aashraf/Desktop/Work/phi-jepa/phi-jepa
source /home/aashraf/phi-jepa/.venvs/phi-core/bin/activate
```

Commands executed for the authorized pilot:

```bash
python tools/p12_enrichment.py prepare
python tools/p12_enrichment.py run
python tools/p12_enrichment_report.py
PYTHONPATH=src:tests:tools python -m unittest test_p12_enrichment test_p12 test_p03 test_p10 test_p11 test_p02b_live_boundaries -v
python tools/p12_enrichment.py run
```

The last command is a completed-pilot resume check: it returns `pilot_closed`
with 32 attempts and zero additional requests, before reading credentials.
Do not reset/delete the ledger or edit the pilot cap to obtain more calls.
`prepare` preserves the frozen selection. `p12_enrichment_report.py` performs
read-only provider-cache inspection and writes reports/proposals; it makes no API
calls. It refreshes the proposal identity, so do not run it during a subsequently
approved full workload with a locked inventory.

Native pilot records: `/home/aashraf/phi-jepa/p12-enrichment-pilot-01`.
Repository export: `docs/reviews/artifacts/P12_enrichment/`. See
[measured costs and the proposed cap](reviews/P12_enrichment_pilot.md).

The following was the pre-approval procedure, now executed after explicit approval: copy
`proposed-full-enrichment.json` to a distinct `approved-full-enrichment.json`,
record the approval and approved scopes, set `enabled: true`, and verify the
current source, provider, asset, inventory and prices. The proposal contains no
credential. An approval for training/validation only requires a $425 overall cap,
8,942-attempt cap and only `train_validation` in `authorized_scopes`. Freeze the
approved configuration before its first dispatch; resume rejects any alteration.
Verify the pinned pricing from official sources and refresh the dated price proof
only when its rates still match. Do not fabricate a new verification timestamp.

Approved scope commands (the supervisor invokes them sequentially):

```bash
python tools/p12_enrichment_full.py --config /home/aashraf/phi-jepa/p12-enrichment-pilot-01/approved-full-enrichment.json --scope train_validation
# Only if this separate scope was approved:
python tools/p12_enrichment_full.py --config /home/aashraf/phi-jepa/p12-enrichment-pilot-01/approved-full-enrichment.json --scope confirmation
```

Use exactly the same command to resume an interruption. A shared worker lock,
budget ledger and per-request result paths prevent concurrent spending and
repetition of completed requests. Unknown in-flight state requires reconciliation;
do not delete its reservation. Terminal failures remain failures until separately
reviewed. Every provider retry counts toward global and scope limits. A scope
limit conservatively stops the shared run; it cannot borrow another scope's budget.

Successful notes go into a new `p12-enrichment-full-01` cache, preserving the
pilot and historical outputs. Then independently prepare embeddings with the
approved frozen encoder, re-audit all identities, close Llama's access/runtime
gate and refresh the disabled expanded-training plan. No enrichment command
starts training, answer generation, test scoring or paper rewriting.
