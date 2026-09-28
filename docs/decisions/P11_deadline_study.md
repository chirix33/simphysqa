# P11 frozen deadline execution

Authority: latest user deadline instruction and explicit approval of an
additional USD 25, 350 provider attempts, four million input tokens and 150,000
output tokens. Starting implementation commit:
`d2e9fe3daba63cc0b5295fa108177628c4319098`, branch
`full-phi-jepa-from-dataset`. P10 is committed at this starting point; its older
reports' uncommitted statements describe their historical run time.

The new native run is `/home/aashraf/phi-jepa/p11-tonight-01`. Its paid caps are
the unused P10 balance plus this approval: USD 35.931835, 421 attempts,
5,272,987 input tokens, 228,345 output tokens. Prior usage is not erased.
Local execution is bounded by the deadline; new artifacts are conservatively
capped at 8 GB. One GPU worker runs at a time. Remote requests have one ledger
writer; local operation records are separate and combined in the report.

An outcome-blind timing probe used four existing training examples, two
discarded updates per method/domain. It took 399.13 seconds, below the
15-minute allowance. Mean update seconds (Coconut/CODI): driving 30.51/60.21,
object pushing/stacking 18.62/36.37, arm 9.57/19.05, tether 6.39/12.80.
Long inputs were included (up to 23,627 T5 tokens). Three uncached training
enrichment requests took 4.13–4.87 seconds; the fourth reused a cache.

The frozen main cohort has 60 trajectories/domain: 48 original training,
12 original test_id, plus eight separate original validation scenarios for
checkpoint selection. The appendix has 20/domain: 16 training and four test,
both nested in the main cohort. Question selection uses the earliest available
forecast horizon then sample ID; scenarios are SHA256 ordered, preserving the
existing P10 tethered training/selection scenarios first. No outcome-based
selection is used. Exact IDs and public target coverage are persisted before
held-out reference access. All questions from a scenario retain its original
release partition. This one-question rule emphasizes a particular available
question/horizon mix; it is not claimed to sample every task type uniformly.
The selected driving questions end at 2.0 seconds; the other domains end at
1.0 second. All adjacent intervals from cutoff to the selected question's
horizon are retained; other questions' longer horizons are not added to this
one-question cohort. Physical reporting
includes driving's additional 1.0–2.0-second window rather than mislabeling it
as the 0.6–1.0-second interval.

Each appendix custom model is one fresh, four-domain T5 model trained on the
same 64 trajectory questions for two complete shuffled passes (128 updates).
The final second-pass checkpoint is predefined; the held-out 20% never selects
it. One fixed training generation after each pass is a fitting diagnostic.
Phi-JEPA requires separate models for the four accepted layouts. Its appendix
fits use only the 16 training trajectories/domain, independently of the main
fits. This is data matching, not parameter-count matching.

Main Phi-JEPA selection chooses among 5k/10k/20k updates using only the eight
separate validation questions/domain, numeric tolerance-normalized endpoint
error, earliest on ties. Appendix Phi-JEPA uses the fixed final 20k checkpoint.
All retain the existing P10 numerical input conditioning and supervised
training-mean output-bias initialization, raw full-2d MSE, both p gradient paths,
equal pair weighting, full temporal coverage, physical RK4 grid and full-vector
feedback. No new scientific parameterization is introduced here.

The new direct-LLM condition is explicitly identified in its cache and prompt.
It may predict Boolean values from the same public problem without satisfying
the forecast method's deterministic readout policy. Strict binding, type,
duplicate, missing-target and complete-answer checks remain. The existing
readout-restricted default parser behavior and P10 results are preserved.
Only the actually configured gpt-5.6-sol service is used; no immutable service
revision is exposed, so returned model identifiers and response IDs are saved.

Custom training is estimated at 6,193 seconds from domain-specific timing.
The frozen schedule estimates expensive completion at 23:15 Chicago, subject
to long-input/provider variation, with a hard 23:39 stop and 20-minute reporting
reserve. Further ablation retraining, hybrid/teacher evaluation, clarification
evaluation and calibrated OOD claims are deferred. Complete failed/capped
conditions remain reportable; no silent shortened-pass claim is permitted.
