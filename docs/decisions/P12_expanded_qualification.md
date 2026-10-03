# P12 expanded-population qualification decisions — 28 September 2026

Authority: the user's expanded experimentation request and root `AGENTS.md`.
This supersedes the earlier phase-only scope for this task. Paper rewriting is
deferred. No prior experiment budget is renewed. The original handoff remains
in `docs/` and historical runs remain unchanged. These are the initial
qualification decisions; the subsequent explicitly authorized $5 / 32-attempt
pilot is recorded in [the enrichment decision addendum](P12_enrichment_pilot.md).

1. Freeze all admitted original training scenarios: 3,721 simulations, 6,702
   question records and 454,130 question-conditioned adjacent pairs. Preserve
   scenario-group partitions, including all question variants and horizons.
   Each pair has weight one. Validation and test data never become training data.
2. Preserve the accepted frozen Qwen3-Embedding-0.6B encoder, trainable projection,
   augmented width `2d`, target-side projection gradients, raw augmented MSE,
   full-vector recurrent feedback, deterministic readout, train-only scaling,
   and training-mean derivative initialization. No scientific model code changed.
3. Use fresh seed-11 models for the proposed study. Initial exposure is ten
   complete shuffled pair cycles, carried tails, batch 256. Select each domain's
   checkpoint using all original validation questions after each completed pass,
   with the existing tolerance-normalized numerical error and earliest tie.
   No convergence claim or desired-accuracy gate. Retain old models as controls.
4. Keep OpenAI `gpt-5.6-sol` enrichment and its adopted asset. Exact request,
   public input, tokenization, encoder settings, provenance and file identities
   determine cache eligibility. Missing coverage blocks full training; there is
   no smaller-population fallback. Initial qualification authorized no API spend;
   the subsequent pilot and disabled remaining-work proposal are separate.
5. Freeze three answer conditions: Qwen3-8B with its native thinking switch false
   and true, and Llama-3.1-8B-Instruct direct answer without a thinking-switch claim.
   Use official templates, BF16 without quantization, SDPA, immutable model and
   tokenizer revisions, seed 11 and explicit decoding/output limits. Run them
   sequentially on the RTX 5090. Pins are in
   [the local model lock](../../configs/local_answers_p12.lock.json).
6. All direct baselines receive identical original public facts and requested
   target schema. No enrichment, Phi forecasts, references, tools or retrieval.
   Store raw completions and token IDs. Qwen reasoning is separated at the native
   closing token; only the final part reaches the strict existing answer parser.
   EOS, cap terminations, invalid output and runtime failure remain explicit.
   No schema repair or automatic retry.
7. Diagnostics use two long validation simulations per domain, selected by public
   input byte length, one question per simulation. Numerical training probes use
   only two cached training questions per domain; their weights are discarded.
   These probes are not the expanded training study or benchmark evidence.
8. Conservatively mark selected/cached historical test cases and every question
   from their simulations as inspected. Freeze 20 unused simulations per domain
   and test distribution, including all their questions: 320 simulations / 500
   questions. Hash ordering uses seed 11 and identities only. No test reference
   outcomes were opened to select the cohort. Do not pool the historical Sol
   results or the 40-question comparison with this cohort.
9. The common target mask is frozen from existing public readout capabilities,
   excluding `stable_stack` and `support_lost`: 2,340 of 2,620 confirmation targets.
   Report this alongside all-target complete-answer accuracy, including every
   unsupported target and failure. Retain per-target errors, Boolean denominators,
   domain/distribution breakdowns and all costs. Phi numerical/readout accuracy
   stays separate from optional generated prose. Existing OpenAI enrichment and
   answer-generation dependencies prevent calling the whole method fully local.
10. Full execution requires a new explicit bounded configuration after the
    documented access/context gates close. The generated proposal is disabled.
    Llama and full-population training are `implemented_pending_validation`.

See [completion evidence](../reviews/P12_completion.md),
[the full-run proposal](../reviews/P12_full_run_plan.md), and
[commands](../P12_pipeline.md).
