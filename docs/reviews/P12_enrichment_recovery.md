# P12 two-record enrichment recovery — 29 September 2026

Both missing tethered-load training records recovered successfully on their first
attempts under the user's newly approved **30-minute / six-attempt / $2** window.
Verified enrichment coverage is now **8,038/8,038 training/validation records and
500/500 confirmation records**, with zero missing notes. No confirmation request
was regenerated, and no embedding preparation or training was launched.

| Recovery measurement | Result |
|---|---:|
| Successful records / attempted requests | 2 / 2 |
| Retries / failures | 0 / 0 |
| Input / output tokens | 9,842 / 412 |
| Summed provider latency | 9.655 seconds |
| Usage-based recovery cost | **$0.057444** |
| Full workload plus recovery, charged or reserved | **$313.142965 / $475** |
| Including separately charged pilot | **$314.427644** |

The prior $0.611010 unknown-charge holds remain intact. They are not treated as
known usage or refunded. Original interrupted attempt records remain historical
failures; new successful outputs have separate provenance and caches.

Native run: `/home/aashraf/phi-jepa/p12-enrichment-recovery-01`.
Checkout: `main` at `248575fd500947edd325836e636aebe41f9f65d0`, with uncommitted
work preserved. The unchanged enrichment implementation is checked against its
approved hash; the recovery runner is separately hashed and archived with its
approved configuration. The original full-run ledger hash remains unchanged.

The recovery reused the original OpenAI model, medium reasoning, prompt/schema,
2,048 output-token cap and public-input preparation. It allowed only the two
frozen training sample IDs and checked compatible caches before dispatch. The
global $475 ceiling and original $425 training/validation scope allocation were
checked including all earlier charges and holds. The new deadline persists on
resume; the old deadline was not reset.

Current pricing was rechecked against the official
[model page](https://developers.openai.com/api/docs/models/gpt-5.6-sol) and
[pricing table](https://developers.openai.com/api/docs/pricing) before dispatch.
Standard rates remain $4 input, $0.40 cached input, $5 cache writes and $20 output
per million tokens; the existing higher conservative reservations were preserved.

Verification revalidated the recovered public requests, returned notes and cache
identities, and checked that all 8,536 previously verified cache files retained
their audited hashes. Known response usage was checked against the recovery
ledger. Eight offline tests passed, covering the two-record scope, rejection of
confirmation/substituted records, authorization, caps and usage accounting.
Completed-run resume returned `already_processed` with **zero additional requests**.

Evidence:

- [Recovery completion](artifacts/P12_enrichment_recovery/recovery-completion.json)
- [Complete enrichment coverage](artifacts/P12_enrichment_recovery/coverage-after-recovery.json)
- [Approved configuration](artifacts/P12_enrichment_recovery/approved-config.json)
- [Spending ledger](artifacts/P12_enrichment_recovery/spend-ledger.json)
- [Offline tests](artifacts/P12_enrichment_recovery/tests.log)

Executed in the existing WSL core environment:

```bash
python tools/enrichment_two_record_recovery.py prepare 2026-09-29T18:55:43+00:00
python tools/enrichment_two_record_recovery.py run
python tools/enrichment_two_record_recovery.py verify
python tools/enrichment_two_record_recovery.py run
PYTHONPATH=src:tests:tools python -m unittest test_enrichment_recovery test_p12_enrichment -v
```

The enrichment coverage gate is closed. Frozen-encoder embedding preparation
and the gated Llama runtime qualification remain before full training. The
expanded-study configuration is still disabled; no test outcomes were read,
paper changes made, or full training/evaluation launched in this recovery.
