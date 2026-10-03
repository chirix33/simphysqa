# P12 frozen embedding preparation — 29 September 2026

Authority: the user explicitly instructed embedding preparation to proceed
alongside their Llama diagnostics. This authorizes local context preparation;
expanded numerical training and confirmation outcome evaluation remain disabled.

1. Prepare all 8,038 frozen training/validation questions and all 500 frozen
   confirmation questions, without changing scenario-group splits. The latter
   use only public inputs and already frozen enrichment. No confirmation
   references or evaluator outcomes are opened.
2. Preserve the accepted Qwen3-Embedding-0.6B encoder revision
   `97b0c614be4d77ee51c0cef4e5f07c00f9eb65b3`, BF16, SDPA, last nonpadding-token
   pooling and float32 L2 normalization to width 1,024. Use the existing single
   unpadded-record adapter, without truncation or a changed input instruction.
   Encoder weights, tokenizer files, runtime, serialization and relevant source
   hashes are frozen in the run configuration.
3. Independently verify each existing enrichment output against its exact public
   request, approved provider policy, prompt/schema and recorded returned model.
   Reuse embeddings only when encoder settings, full context, token identity,
   width, finiteness and normalization match. Keep all prior files unchanged.
   No provider, credential, download or paid API operation is permitted.
4. Store this run at `/home/aashraf/phi-jepa/p12-embedding-preparation-01`, with
   reports exported to `docs/reviews/artifacts/P12_embeddings/`. Historical P12
   audits and model results are preserved. Llama code/settings are independent
   of this run's frozen source list and are not edited by preparation.
5. Bound preparation preflight to 1,200 wall seconds. Encoding has at most one
   call per missing vector, no automatic retries, 3,600 summed encoding seconds,
   a conservative 120-second reservation per call, 5,400 persisted execution
   wall seconds and 2 GB run artifacts. Previously reserved/interrupted calls
   remain explicit and prevent silent retries. These caps do not renew on resume.
6. Save each successful vector and attempt record atomically. Acquire an exclusive
   worker lock; check competing GPU processes before loading and every 25 calls,
   pausing under the same wall deadline when another compute process is visible.
   This permits independent Llama diagnostics without scheduling a second answer
   model. Each measured encoding latency is reported as preparation cost.
7. After generation, recompute every public context/token identity using the
   tokenizer, recheck enrichment provenance and all reused vector hashes, and
   export separate training/validation and confirmation coverage/origin audits.
   A missing or mismatched record fails the completion audit. No partial cohort
   is silently declared complete.

Run commands and results: [embedding completion](../reviews/P12_embedding_preparation.md).
