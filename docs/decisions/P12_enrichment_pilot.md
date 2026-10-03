# P12 enrichment pilot decisions — 28 September 2026

Recovery follow-up: the user approved the new 30-minute / six-attempt / $2
window. Two unchanged public enrichment requests succeeded for $0.057444.
Keep original interrupted attempts and their unknown-charge holds intact; the
new outputs live in a separate recovery cache. All enrichment coverage is now
verified complete. See [recovery report](../reviews/P12_enrichment_recovery.md).

Completion follow-up (29 September): full enrichment ended with 8,273 successes
and two explicit unknown restart failures. Keep their $0.611010 conservative
holds and historical records. The original execution deadline is expired;
propose a separately approved 30-minute recovery window for only those two
training records, at most six attempts and $2 within the original unused cap.
See [completion evidence](../reviews/P12_enrichment_completion.md).

Follow-up: the user approved "$475 maximum for both scopes". The additional
full-enrichment budget is now authorized with unchanged $425/$50 scope limits.
See [the separate execution record](../reviews/P12_enrichment_full.md). The
original pilot/proposal decisions below are preserved as historical evidence.

The user's explicit follow-up superseded the earlier no-paid-calls restriction
only for an initial $5 / 32-attempt enrichment profiling pilot. No old budget
was reused. This record supplements [initial P12 decisions](P12_expanded_qualification.md).

1. Reuse exact compatible caches first; the initial 231 records were preserved.
   Freeze 32 missing training/validation requests across four domains and four
   public-input-length strata per split. Confirmation is excluded from pilot
   selection and generation. No reference outcomes are used.
2. Preserve the accepted OpenAI model, medium reasoning, prompt/schema,
   2,048-token output cap and public context preparation. Local direct-answer
   baselines receive no OpenAI enrichment. No scientific training objective changes.
3. Keep the original provider adapter and historical cost records unchanged.
   A separate durable transport ledger accounts for current cache-write billing,
   all attempts/retries, unknown usage and conservative pre-dispatch reservations.
   Single-worker locking and atomic cache persistence support safe resume.
4. Keep the original executed source snapshot. Later guard hardening and the
   proposed full runner have separate identities and offline tests. An exhausted
   pilot resumes without credentials, model calls or overwriting its execution record.
5. The 32 successful requests cost $1.284679 under verified current prices.
   No request beyond the 32-attempt limit is authorized, despite remaining dollars.
6. Propose an additional $475 maximum ($425 train/validation, $50 confirmation),
   with independently enforced scope limits and one shared ledger. The proposed
   configuration stays disabled pending explicit approval. Training/validation-only
   approval should instead freeze a $425 configuration and exclude confirmation.
7. Unresolved in-flight reservations stop rather than risk duplicate billed calls.
   Terminal failed records remain visible and are not silently retried on resume.
   Fresh pricing proof is required within 24 hours of every future dispatch.

Evidence, uncertainties, remaining counts and exact commands are in
[the pilot completion report](../reviews/P12_enrichment_pilot.md) and
[the pipeline guide](../P12_enrichment_pipeline.md).
