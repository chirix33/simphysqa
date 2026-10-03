# P12 enrichment completion audit — 29 September 2026

Superseding follow-up: both missing records were recovered under a newly
approved bounded window. [Recovery completion](P12_enrichment_recovery.md)
confirms 8,038/8,038 train/validation and 500/500 confirmation notes. This report
preserves the original full worker's results and spending before that recovery.

The worker finished at **15:31:26 UTC (10:31 a.m. America/Chicago)**. It processed
all selected records and stopped normally. Coverage is not yet complete:
**two tethered-load training records remain unresolved after workstation restarts**.
No new provider calls were made during this completion audit.

Checkout remains `main` at `248575fd500947edd325836e636aebe41f9f65d0`, with the
existing uncommitted P12 work preserved. The executed enrichment implementation
still matches the approved source hash. Historical results, pilot records,
restart archives, raw responses and all prior charges remain intact.

## Verified results and spending

| Scope | New successful outputs | Unresolved restart records | Known usage cost | Unknown charge reserved | Charged or reserved |
|---|---:|---:|---:|---:|---:|
| Training/validation | 7,773 | 2 | $293.193396 | $0.611010 | $293.804406 |
| Confirmation | 500 | 0 | $19.281115 | $0 | $19.281115 |
| Total | **8,273** | **2** | **$312.474511** | **$0.611010** | **$313.085521** |

The full-run ceiling was $475; **$161.914479 remains unspent/unreserved**.
The separately charged pilot cost $1.284679, so pilot plus full-run accounting
is at most $314.370200 under the recorded rates. Unknown reservations are
conservative holds, not fabricated actual usage or invoice reconciliation.

Known responses used 55,207,822 input tokens and 1,823,011 output tokens;
475,404 reasoning tokens are included in the output total. Cached-read tokens
were zero; 55,183,003 input tokens were reported as cache writes. There were
8,273 known successful responses and two conservatively counted possible
attempts with unknown dispatch/completion state. No provider failure is hidden
by these figures. The two unknown attempts have no measured tokens or latency.

Measured provider latency sums to 30,246.785 seconds for training/validation and
2,242.940 seconds for confirmation: about 9.025 hours total. Elapsed time from
authorization to completion, including initialization and workstation downtime,
was 17.946 hours. The final spending and request counts stayed below all approved
global and scope limits. This is context preparation, not a physics benchmark.

## Exact cache coverage

The audit read all 8,538 public selections and verified compatible request,
provider, prompt/schema and output identities. It checked every known response
against its usage ledger and every successful new note against its verified
cache. The deployment reference-access guard remained active; no private
references, test outcomes, future states or credentials were opened.

| Domain | Training notes | Validation notes | Confirmation notes |
|---|---:|---:|---:|
| robotic_arm | 1,962 / 1,962 | 388 / 388 | 140 / 140 |
| driving | 740 / 740 | 148 / 148 | 80 / 80 |
| object_pushing_stacking | 2,000 / 2,000 | 400 / 400 | 140 / 140 |
| tethered_load | **1,998 / 2,000** | 400 / 400 | 140 / 140 |
| Total | **6,700 / 6,702** | **1,336 / 1,336** | **500 / 500** |

Thus training/validation has **8,036 / 8,038** compatible records, including
the 263 pre-existing/pilot records. Confirmation has **500 / 500**. These are
enrichment-cache counts, not embedding-cache or trained-model qualification.
No scenario is dropped to work around incomplete coverage.

The exact missing question records are:

- `b06de105f9948d5fb26f82e9194d2239`, scenario `10a627d60ff489089f4bfbe2ff512d86`.
- `757d9982860c372fb1ac7fed9ddb8ffb`, scenario `43f5a2d0efefaf8d1820f9838af39c9e`.

Both are in the original `tethered_load/train` partition. Neither has a saved
compatible output. Their prior unknown attempts remain charged at full reserved
amounts and were not automatically replayed.

Evidence: [audit](artifacts/P12_enrichment_full/completion-audit.json),
[full coverage manifest](artifacts/P12_enrichment_full/completion-cache-coverage.json),
[worker completion](artifacts/P12_enrichment_full/completion.json), and
[spending ledger](artifacts/P12_enrichment_full/spend-ledger.json).
The native root is `/home/aashraf/phi-jepa/p12-enrichment-full-01`.

Command run in the existing WSL core environment:

```bash
python tools/enrichment_completion_audit.py
```

## Proposed two-record recovery and next gate

The original 20-hour execution window expired at **17:35:44 UTC (12:35 p.m.
America/Chicago)**, before this completion audit. Its deadline is not reset.
The [disabled recovery proposal](artifacts/P12_enrichment_full/proposed-recovery.json)
freezes only the two missing public records and proposes:

- A new **30-minute execution window**.
- **$2 maximum**, drawn from the unused portion of the original $475 cap.
- At most **six provider attempts**, including retries, under the unchanged
  model/prompt/schema/reasoning settings and original per-request limits.
- A separate directory `/home/aashraf/phi-jepa/p12-enrichment-recovery-01`;
  preserved old failures and reservations; cache reuse before any dispatch.
- Fresh pricing verification, public-input-only preparation and no confirmation
  requests. Maximum original full-run plus recovery accounting: $315.085521.

This proposal remains disabled pending approval of the new execution window.
No automatic retry or extension has been launched. After recovering both notes,
re-audit coverage, prepare identity-matching frozen-encoder embeddings, and close
the gated Llama qualification before enabling the separate expanded study.
Neither full numerical training nor test-outcome evaluation has started.
