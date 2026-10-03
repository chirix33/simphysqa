# P12 regenerated training plan — 29 September 2026

Authority: the user's instruction to prepare the training run and regenerate
the expanded-study plan from completed embedding manifests. This is preparation
authorization; numerical training remains unstarted.

1. Preserve the old incomplete-coverage proposal unchanged. Create a separate
   `p12-complete-context-training-v2` proposal under
   `/home/aashraf/phi-jepa/p12-training-plan-01`, exported to
   `docs/reviews/artifacts/P12_training_plan/`.
2. Bind explicit paths/checksums for completed training/validation and confirmation
   contexts, their enrichment origins, the encoder identity, original scenario
   selections, layouts and numerical source/runtime. Recount all admitted
   training pairs; never add validation/test questions to training.
3. Preserve the accepted objective and ten-pass seed-11 proposal: equal-pair
   batches of 256, 17,742 total optimizer updates and 4,541,952 pair presentations.
   Use all validation questions each pass and the unchanged selection metric.
   Preserve old checkpoints; no diagnostic weights initialize this study.
4. Separate numerical-training approval from study/evaluation approval. The new
   plan is disabled. A later approved copy must bind the exact prepared checksum
   and leave global `enabled` and `evaluation_enabled` false. Local-answer
   diagnostics are independent; no evolving interface is silently selected.
5. Lock only source dependencies relevant to numerical preparation/training and
   validation. Preserve and do not edit the user's new answer-interface files.
   Numerical training need not wait for an unrelated answer-prompt decision.
6. Close identified resume gaps: persist domain deadlines so restarts do not
   reset the budget; lock workers; record update attempts; reject uncheckpointed
   or unresolved work; and refuse to skip interrupted pass validation. Recovery
   is conservative and may require explicit reconciliation, not silent replay.
7. Verify readiness without executing the study. A disabled CLI launch must fail
   before creating study artifacts. Record both `data_ready: true` and
   `can_train: false` while training authorization is absent.

Evidence and commands: [training preparation completion](../reviews/P12_training_preparation.md).
