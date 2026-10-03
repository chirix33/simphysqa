# P12 Llama qualification decisions — 29 September 2026

Authority: the user's explicit approval of HF access and WSL login, followed by
the instruction to proceed with Llama qualification. Root `AGENTS.md` and the
accepted model-training contract remain unchanged.

1. Acquire the already pinned Llama revision using the user's existing HF login.
   Run only the frozen eight-question validation diagnostic under a new bounded
   qualification configuration: eight requests, 1,200 generation seconds,
   1,500 seconds persisted generation wall window, 20 GB download allowance and
   2,700 seconds acquisition limit. No paid enrichment or full study is launched.
2. Preserve the original gated result and all Qwen results. Store the follow-up
   under `/home/aashraf/phi-jepa/p12-llama-qualification-01`, exported directly
   under `docs/reviews/artifacts/P12_llama/`. Preserve exact generation source
   separately from subsequent integration changes.
3. Keep the official Llama template, BF16 runtime, direct-answer prompt and
   strict common parser. There is no native thinking switch. All eight outputs
   failed JSON parsing, while all eight runtime requests completed at EOS.
   Record both facts: `complete_with_recorded_failures` is not valid-answer or
   scientific-performance qualification. Do not repair or rerun outputs.
4. Update only Llama's entry in the local model registry; archive its predecessor
   and verify Qwen entries are identical. Full-study execution resolves the
   new qualification root using manifest hashes and requires the approved plan
   to pin the entire model lock. It still requires fresh fits, selected checkpoint
   sealing, complete compatible contexts and new full-study authorization.
5. Keep the 0/8 diagnostic accuracy and malformed outputs in all denominators;
   do not invent a desired-accuracy acceptance gate. If a different prompt is
   requested later, preserve this condition and qualify the new version using
   training/validation data only. Confirmation outcomes remain unopened.
6. Use measured Llama runtime only as a rough planning estimate. Short malformed
   outputs cannot support a valid-answer throughput claim. The expanded plan's
   shared caps stay in force. Enrichment is complete; frozen-encoder preparation
   and re-audit remain. Paper rewriting remains deferred.

Evidence: [completion report](../reviews/P12_llama_qualification.md).
