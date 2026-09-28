# Executable Phi-JEPA qualification workflow

This workflow implements the user's post-P09 learning instruction. The frozen
training contract remains authoritative. Results and limitations are in
[the benchmark report](reviews/P10_benchmark_report.md); source/config/checkpoint
identities and completion status are in [P10 completion](reviews/P10_completion.md).
Historical P07/P08/P09 reports and runs are preserved.

## Environment and one-command execution

Run from the repository root inside `Ubuntu-24.04` WSL, with the existing pinned
`phi-core`, `phi-coconut-custom` and `phi-codi-custom` environments under
`/home/aashraf/phi-jepa/.venvs/`. The supervisor selects the appropriate interpreter.
Models must already be present at their pinned revisions in `model-cache`;
model download/network fallback is disabled. The configuration names the
run directory, dataset selection policy, solver, update/milestone limits,
generation limits and aggregate budget. It becomes immutable on first use.

`setup_report` installs the separate `RUN_ROOT/report-env` from
`configs/report-p10.lock.txt`. This reporting-only dependency step may download
pinned Python wheels; it does not change the core or custom model environments.
The environment and any initial package-cache bytes count toward artifact limits.

```bash
cd /mnt/c/Users/aashraf/Desktop/Work/phi-jepa/phi-jepa
/home/aashraf/phi-jepa/.venvs/phi-core/bin/python tools/run_pipeline.py --config configs/qualification_p10.json all
/home/aashraf/phi-jepa/.venvs/phi-core/bin/python tools/run_pipeline.py --config configs/qualification_p10.json status
```

`all` resumes completed stages and recomputes final evaluation/report/export from
saved results. It does not resume a stopped aggregate budget. Use the same command
after resolving a genuine execution failure; never edit frozen config, delete
failure evidence, or reset a budget to obtain more work. A changed configuration
requires a new run identity and appropriate execution authorization.

One worker runs at a time. `.pipeline.lock` prevents concurrent workers. A stale
lock or interrupted attempt requires operator inspection; do not clear it while a
worker remains alive. GPU/CPU worker wall time, provider usage/reservations and
artifact size are enforced by the supervisor. Per-job limits bound recovery work.
Stage JSON and logs distinguish failure, cap, complete and complete-bounded work;
`fit.json` records actual updates even when a usable checkpoint exists before a cap.
An absent checkpoint becomes explicit forecast failures in evaluation.

The qualification uses **three GPU hours, one CPU hour, 20 GB, 120 provider
attempts, two million input tokens, 100,000 output tokens and USD 15**. Cache hits
do not charge their historical calls again. Unknown usage retains its entire
reservation. Standard-tier GPT-5.6 Sol pricing was checked against
[official documentation](https://developers.openai.com/api/docs/models/gpt-5.6-sol)
on 25 September 2026. New provider accounting conservatively charges input at
the cache-write upper rate, without discounts. It is not a billing invoice.

## Resumable stages

The prefix below is abbreviated as `python`; use the core interpreter above.

| Command | Inputs and resulting artifact | Truth access |
| --- | --- | --- |
| `python tools/run_pipeline.py prepare` | Pinned release, frozen train/selection scenarios, layout validation, checked existing cache copies | Training/selection references copied only into `private/` |
| `python tools/run_pipeline.py validate_release` | All public train/validation questions across the four domains checked against accepted layouts | Public-only preflight |
| `python tools/run_pipeline.py prepare_evaluation` | Four-domain calibration and sealed ID/OOD public cohorts from frozen scenario inventories | Public inputs and identity metadata only; no outcomes |
| `python tools/run_pipeline.py verify --refresh` | Offline behavioral tests and exact command/results | Fixtures only |
| `python tools/run_pipeline.py setup_report` | Pinned isolated Matplotlib environment; included in `all` | No dataset/model inputs |
| `python tools/run_pipeline.py enrich` | Immutable public Q/C to content-addressed enrichment | Public only; budgeted provider boundary |
| `python tools/run_pipeline.py encode` | Public/enriched contexts to frozen pinned Qwen embeddings | Public only; model cache only |
| `python tools/run_pipeline.py numerical small_fit` | Fresh two-scenario fitting diagnostic, fixed milestones | Training supervision only |
| `python tools/run_pipeline.py controls` | Independent raw/conditioned × early/full temporal comparison | Train supervision; separate validation selection |
| `python tools/run_pipeline.py bias_controls` | Same comparison plus fitting diagnostic with disclosed supervised output-bias initialization | Same separation |
| `python tools/run_pipeline.py baselines` | Independent constant-context ODE, fixed-projection LR, RNN, no-enrichment and numerical-only ablations | Same separation |
| `python tools/run_pipeline.py custom_prepare` | Branch instruction tokens and separately stored teacher/student targets, no truncation | Gold target serialization only in `private/` |
| `python tools/run_pipeline.py custom coconut_small` | Fresh single-example fitting run | Training only |
| `python tools/run_pipeline.py custom codi_small` | Fresh single-example fitting run | Training only |
| `python tools/run_pipeline.py custom coconut_broad` | Fresh broader run, validation loss checkpoint selection | Train targets; validation labels for selection only |
| `python tools/run_pipeline.py custom codi_broad` | Fresh shared-backbone teacher/student run | Same separation |
| `python tools/run_pipeline.py forecast` | Selected checkpoints, public inputs/caches to raw trajectories, named readout and statuses | **No reference files** |
| `python tools/run_pipeline.py custom_forecast coconut` | Selected custom checkpoint to saved strict generations | **No target/reference files** |
| `python tools/run_pipeline.py custom_forecast codi` | Student and teacher generation; separately composed hybrid | **No target/reference files** |
| `python tools/run_pipeline.py prepare_continuation` | Fork each completed 4,000-update numerical checkpoint into a separate evidence directory | Existing checkpoints/history only |
| `python tools/run_pipeline.py numerical continued_biasinit_conditioned_full` | Continue the primary to at most 20,000 total updates; analogous `continued_` jobs cover the four iterative comparators/ablations | Same training pairs and frozen transform, validation selection |
| `python tools/run_pipeline.py select_continued_methods` | Select continued conditions plus the unchanged independent LR fit | Checkpoint metadata only |
| `python tools/run_pipeline.py evaluate --refresh` | Training/validation one-step/autonomous errors and answer denominators | Separate evaluator interface opens references |
| `python tools/run_pipeline.py diagnose` | Bounded selected-checkpoint gradients, saturation and sensitivity; no optimizer updates | Explicit evaluator diagnostics |
| `python tools/run_pipeline.py assessment` | Train-predicted bank, full-2d familiarity, unchanged V1, supported checks | Public/predicted data; no gold assessment labels |
| `python tools/run_pipeline.py calibrate --refresh` | Complete, identity-matched disjoint validation assessment records only | No test tuning; returns explicit uncalibrated if ineligible |
| `python tools/run_pipeline.py answers` | Local qualification prerequisite, frozen answer LLM, all readout statuses | Public inputs and predictions only |
| `python tools/run_pipeline.py report --refresh` | Curves, metrics, capability matrix and resource snapshot | Evaluator artifacts |
| `python tools/run_pipeline.py export --refresh` | Review artifacts, hashes and native checkpoint pointers | Excludes private files, credentials and model weights |
| `python tools/run_pipeline.py aggregate aggregation` | Future approved multi-run manifest to matched question/seed summaries; refuses incomplete cohorts | Saved evaluator results only |

Run `evaluate --refresh` after answer/custom generation, then `report --refresh`
and `export --refresh`. `customs` is a convenience group for preprocessing, all
four custom fits and both selected-checkpoint generation stages.

Numerical checkpoints contain their frozen affine buffers, projection and vector
field. `load_selected` verifies pointer/hash/layout/context identity. No numerical
coordinate is replaced, reset, clipped or rescaled on output. Raw augmented loss
and full predicted-vector feedback remain unchanged. External physical time
comes from the public horizon and 0.02-second grid. Conditioning affects only n
at the network input; evolving p and its target gradient remain live.

The qualification's baseline selection uses the full-coverage conditioned primary
with separately disclosed training-derived initialization. The better early-only
validation score is still reported; full coverage is not claimed to be better.
No-enrichment has its own projection/ODE and public-only embeddings; numerical-only
has its own numerical ODE and no E/P/p. LR uses a fixed independent projection.
RNN preserves chronological hidden state and predicts autonomously after cutoff.

The separate `configs/qualification_p10_continuation.json` freezes the single
higher-exposure condition after small-set fitting succeeded. It uses the same
aggregate ledger, model/optimizer states and sampler prefix, with new checkpoint
directories and no refitting of affine statistics. The four-domain `study` command
instead starts its declared 20,000-update models independently; it does not repeat
the qualification continuation. Numerical diagnostic caches require matching
checkpoint, public inputs, evaluator references and source identities.

Checkpoint selection uses the evaluator's unchanged tolerance
`absolute_tolerance + relative_tolerance * reference_magnitude`; reference magnitude
is absolute scalar value or vector Euclidean norm. The frozen qualification
config's shorter phrase "absolute tolerance" is an imprecise description, not an
override of that executable calculation. No tolerance was changed. An interrupted
milestone diagnostic is recovered from its saved checkpoint before final selection,
without optimizer updates; the original failed attempt remains recorded.

## Independent deployment and evaluation

The deployment modules are `tools/p10_inference.py` and the public-only selected
custom generation path. Selected deployment checkpoints require no evaluator
references or training target files. The runtime workflow's root may contain
private evaluator artifacts, but these are neither read nor passed into inference.
The evaluator is a separate executable stage. Original predictions are preserved
when the answer LLM produces prose/JSON or fails.

Each requested target has supported/unsupported/failure status. Contact-dependent
`stable_stack` and `support_lost` stay unsupported. Supported public-rule outputs
still check units, frame, initial conditions, threshold/hysteresis, duration and
time coverage. Sampling is 0.02 seconds; no exact continuous-time event recovery
is claimed. Failed/unsupported targets remain in full-answer denominators.

Public-only and forecast-based answers share public facts, frozen model, parser
and reference tolerances. Public-only lacks forecast Boolean evidence; its
Boolean policy differs and must be reported. Compare common numerical targets
separately. Removing inactive assessment/fallback is a no-op, not independent
ablation evidence. PIN-ODE remains excluded.

## Separately enabled clarification

Autonomous `all` never requests a human reply. P09's one-question/one-reply
human-reviewed service is exposed through `clarify REQUEST_ID`, outside `all`.
No clarification calls were needed to run this qualification.

For an explicitly enabled live human condition, place a JSON request at
`RUN_ROOT/clarification_requests/start1.json`:

```json
{"enable_human_condition":true,"action":"start","attempt_id":"human1","sample_id":"EXACT_PUBLIC_SAMPLE_ID"}
```

```bash
python tools/run_pipeline.py clarify start1
python tools/clarification_reply.py show --root RUN_ROOT/clarification --attempt human1
python tools/clarification_reply.py reply --root RUN_ROOT/clarification --attempt human1 --actor ACTUAL_USER_ID --message-id ACTUAL_MESSAGE_ID --reply-file ACTUAL_REPLY.txt
```

A human reviewer then writes a separate request with action `review_and_refine`,
the same attempt ID, `enable_human_condition:true`, and `human_review` containing
the `ReplyReview` fields: category, reason, reviewer_id, reviewed_at, exact
reply_quote, preserves_task, preserves_physical_assumptions, no_conflict,
no_supplied_outcome, resolves_requested_gap. Run `clarify REVIEW_REQUEST_ID`.
Only a usable reply preserving task/assumptions dispatches one refinement call.
Changed physical conditions require reforecasting; changed tasks cannot improve
the original-task score. No automatic reforecasting, repair, retrieval, EBM or
unsupported contact-value invention occurs. Authenticating user/reviewer IDs is
the host operator's responsibility. Actual, scripted and autonomous conditions
must be evaluated separately with the existing clarification evaluator.

## Calibration and sealed evaluation

`prepare_evaluation` materializes public-only cohorts for all four domains and
keeps outcomes sealed. Checkpoint-selection scenarios are excluded from the
calibration set. A future separately authorized config may set
`evaluation_authorized:true`. Then the following stages are executable:

```bash
python tools/run_pipeline.py --config AUTHORIZED_STUDY.json public_cohort calibration--enrich
python tools/run_pipeline.py --config AUTHORIZED_STUDY.json public_cohort calibration--encode
python tools/run_pipeline.py --config AUTHORIZED_STUDY.json public_cohort calibration--forecast
python tools/run_pipeline.py --config AUTHORIZED_STUDY.json assessment_cohort calibration
python tools/run_pipeline.py --config AUTHORIZED_STUDY.json calibrate
python tools/run_pipeline.py --config AUTHORIZED_STUDY.json public_cohort test_id--enrich
python tools/run_pipeline.py --config AUTHORIZED_STUDY.json public_cohort test_id--encode
python tools/run_pipeline.py --config AUTHORIZED_STUDY.json public_cohort test_id--forecast
python tools/run_pipeline.py --config AUTHORIZED_STUDY.json public_cohort test_id--answers
python tools/run_pipeline.py --config AUTHORIZED_STUDY.json custom_cohort test_id--coconut
python tools/run_pipeline.py --config AUTHORIZED_STUDY.json custom_cohort test_id--codi
python tools/run_pipeline.py --config AUTHORIZED_STUDY.json assessment_cohort test_id
python tools/run_pipeline.py --config AUTHORIZED_STUDY.json benchmark_cohort test_id
```

Repeat the last public/evaluator sequence for each named OOD partition. Calibration
only runs after complete assessment records exist. Empty typed contracts, missing
V1 or compatible references keep it partial/uncalibrated. Cohort assessment/custom
paths are implemented but are not empirically exercised by this qualification;
public-cohort preparation is not a detector-performance result.

The current qualification uses one selected question per scenario and equal-length
chronological chunks. A future configuration can select all questions and enable
`mixed_horizon_equal_pair_sampling`: numerical ODEs use fixed-size shuffled
question-pair cycles with tails carried into the next cycle; RNN samples complete
chronological trajectories with probability proportional to their length. With
the unchanged mean transition loss, every pair has equal expected gradient weight.
Actual exposure is recorded; no loss weighting or inverse-multiplicity weighting
is introduced. Software tests qualify this sampler; larger empirical training is
still pending. Layout/overlength incompatibilities fail explicitly.
