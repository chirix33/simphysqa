# Larger dataset selections in answer_pipeline

Branch `full-phi-jepa-from-dataset`, base HEAD
`d2e9fe3daba63cc0b5295fa108177628c4319098`; local uncommitted changes. No push,
training, checkpoint replacement, dataset generation or paid calls occurred.

## Cause and fix

The runner always read P11's `selected-public.json`, which has only 12 original
test questions per domain. A 20-question request therefore failed before opening
the output directory. This was a prepared-subset limitation, not a shortage in
the full dataset or a checkpoint-training failure.

Main-cohort `--inventory auto` now expands to the original release partition
when the prepared pool is too small or an explicitly selected sample is absent.
Prepared cases retain priority for cache reuse; additional cases use sample-ID
ordering. Selection reads admitted public inputs and partition/scenario metadata,
not gold labels or future reference states. Partition/checksum and known scenario
overlap checks remain explicit. Matched appendix cases stay frozen. `list` shows
the original partition; `--inventory p11` preserves the old subset restriction.
Out-of-range requests now receive argparse errors instead of a traceback.

New run-local context preparation reuses valid enrichment/embeddings or generates
missing public notes under the same USD/token/attempt caps and computes missing
embeddings with the unchanged frozen Qwen model. Historical caches are read-only.
Numerical and custom workers read these local caches. The separate evaluator can
join original release references for new cases and export gold comparisons.
No optimizer, projection, solver, loss, readout or parser policy changes.

USD 5 and 120 attempts remain the defaults. An 80-question comparison may exceed
these allowances once fresh vanilla answers, enrichment and Phi final answers
are counted. The implementation does not increase caps or shrink the evaluation
population; unavailable contexts/answers and failed generations remain explicit.

## Verification

All 15 targeted offline tests pass: 11 existing answer/gold/cache tests plus four
tests for release-only selection, prepared-case ordering, no reference access
during selection, missing-enrichment handling at zero budget, frozen encoding of
uncached public inputs and context-free method routing. Encoder/provider mocks
are software evidence only, not model-performance measurements.

Actual WSL preflight:

```bash
python tools/answer_pipeline.py run --domains all --questions-per-domain 20 --dry-run
```

Selected exactly 20 questions/domain, including 48 prepared P11 questions total
and 32 additional release questions. Available original `test_id` question counts:
driving 138, object_pushing_stacking 400, robotic_arm 394, tethered_load 400.
This preflight performs no writes, model execution or provider calls. These are
question counts, not a claim of that many distinct trajectories.

Two separate zero-spend execution checks:

1. `expanded-inventory-cached-check`: one question/domain; four fresh Phi forecasts
   succeeded with reused run-local embeddings and exact cached final answers.
   Two vanilla cache hits and two cache misses were retained; gold export passed.
2. `expanded-inventory-new-embedding-check`: additional held-out sample
   `0041b933f487283f91295c6270beb1eb`, existing `no_enrichment` checkpoint. A new
   frozen public-only Qwen embedding and autonomous forecast succeeded. Its
   uncached final LLM answer remained a cache miss under the explicit zero budget;
   the separate full-release evaluator still exported the gold answer.

Native evidence is under `/home/aashraf/phi-jepa/manual-outputs/` in those two
directories. Configuration, budget, source and summary copies are under
`docs/reviews/artifacts/Answer_inventory/`. No new scientific performance claim
is made. The newly enabled enrichment transport is covered offline and reuses
the existing previously live-tested public-only provider adapter; no new paid
enrichment or 80-question paid benchmark was launched for this fix.

Changed files: `tools/answer_pipeline.py`, new `tools/answer_inventory.py` and
`tools/answer_context.py`, `tests/test_answer_inventory.py`, WSL instructions,
progress/decision records and this completion report. Larger-count commands are
ready for user execution within explicitly supplied caps.
