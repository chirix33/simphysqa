# Focused post-P07 source and artifact audit

25 September 2026 — `full-phi-jepa-from-dataset`.

The approved primary computation is present and its saved autonomous trajectory
replays exactly. Three routine implementation fixes are applied below. The large
raw numerical error is overwhelmingly a poorly predicted **simulator step-index
coordinate**, not evidence of enormous physical position error or chaos. The
custom models have working optimizer/gradient paths and changed weights, but
their two-update checkpoints still produce no valid typed answers. Four-domain
output coverage is incomplete; fixed assessment is partial and uncalibrated;
OOD recognition performance and OOD clarification are not demonstrated.

This audit used source, preserved checkpoint tensors, cached encoder outputs,
saved trajectories/references and offline tests. It made **zero optimizer updates,
new encoder forwards, custom generations, paid/provider calls or dataset changes**.
Small synthetic gradient/optimizer tests are verification, not expanded empirical
training. No full pilot was launched. Original reports and checkpoints are intact.

Companion deliverables:

- [Every-coordinate error breakdown](Post_P07_coordinate_errors.md), with names,
  units, ranges and raw-MSE contributions; [machine data](artifacts/Post_P07/coordinate-errors.json).
- [Four-domain output/assessment matrix](Post_P07_coverage_matrix.md), including
  contact events, initial-state qualification, required contracts and calibration.
- [Next-pilot budget addendum and training-only fitting protocol](Post_P07_next_pilot_revision.md),
  prepared only; [decision record](../decisions/Post_P07_focused_audit.md).
- New derived evidence in `docs/reviews/artifacts/Post_P07/`; native numerical
  diagnostics in `/home/aashraf/phi-jepa/post-p07-audit-02`, custom/ablation
  checkpoint checks in `post-p07-audit-01`. The first diagnostic pass is retained;
  its inherited unit annotations were corrected in pass 02 (time is seconds,
  relative tolerance dimensionless). No scientific values changed between passes.

## 1. Source and provenance reconciliation

The initially clean implementation checkout is commit
**`5810d1899007ae602c3db1ca486d43a1b7865ba4`**, parent
`7f2553ca6591301de588bd3362e72838354169a0`. The local
`origin/full-phi-jepa-from-dataset` reference matches that commit with no local
tracking divergence. This verifies present committed/local-tracking status;
no network refresh was performed, so current server-side state is not newly
verified. This audit makes no commit or push. Its fixes/reports are working-tree
changes on top of that implementation commit.

Earlier reports' statements that implementation was uncommitted describe their
run time and are preserved. Their per-run source-file hashes/checkpoint identities
remain authoritative for those runs; do not substitute the current Git hash as
their training-source identity. The unchanged P07 evidence export is
`/home/aashraf/phi-jepa/p07-pilot/79675fd7676e26a051c23fd521a7d136a48b875fa5d590ff50007beec3263d1c`.

Key preserved deployment/final checkpoint identities:

| Method | SHA-256 |
| --- | --- |
| Primary Phi-JEPA | `f639763501219c6d32e714b3a25daf36a5b4954137b7ae4c74c632f1a4befe8e` |
| no_enrichment | `b135b2393b1fa6735b207853e8dff38dfeb857c88b25f920f326bea707714b14` |
| no_text_conditioning | `d0dcc118c7763072fb1062c0c62e112014eda39285164a782e9e85521e6e8815` |
| Custom Coconut, update 2 | `aad86b157cd7eb1e822e24e4bbb9581b5106e791be210fe93ce05263754b5277` |
| Custom CODI, update 2 | `c8ff78fead53c3f7105e348e4c924ba6074092397b0b160363933ab6d955545f` |

## 2. Primary computation: one real example and autonomous replay

The real training question is `08930dbcfe8a3c2273ebd024c397ff39`, scenario
`6dcead753b8ad615a772be98d0c8906f`. First pair
`5e0191fdbf2d10eb3565a3d982109e307dd93d17abd319457ca06f2c9126690a` links
state `22d35b8453463cfa97dcfa682f1cdd58` at 0.20 s to
`98447b92fcdbe6883ec30e650a6739f5` at 0.22 s. The first 20 reconstructed pair
identities match the actual training provenance exactly. Evaluation uses question
`494b17e6fb6b7a9dc42c0727f92e0b17`, scenario
`ba28c67a348a7459ddeca5b3de93b385`, absent from the training scenario. The preserved
[P07 whole-scenario audit](artifacts/P07/output-and-split-audit.json) checked all
6,702 training metadata records and found no overlapping training questions.

| Step | Source and observed behavior |
| --- | --- |
| Public inputs | `integration/contracts.py`, `integration/readers.py`: full original Q/C, observed history through cutoff, public parameters/controls, scheduled intervention and answer specification. No future reference handle on `PublicInputReader`. Scheduled future controls are permitted, unlike future outcome observations. |
| Enrichment | `providers/openai_enrichment.py`, `providers/context.py`: saved gpt-5.6-sol notes; original public leaves are reconstructed and immutable. Training/audit read only the existing enrichment envelope. Structural validation cannot prove arbitrary prose is scientifically true; enrichment factual quality remains a separate limitation. |
| Frozen E | `providers/qwen.py`: `Qwen/Qwen3-Embedding-0.6B`, revision `97b0c614be4d77ee51c0cef4e5f07c00f9eb65b3`; eval/no-grad frozen module, last nonpadding token, BF16 forward and FP32 L2 normalization, width 1024, no truncation. This audit verifies exact-content cache hits, 5,678/5,690 tokens for train/validation; the backend was explicitly forbidden from running a new encoding. |
| Numerical layout | `integration/layout.py`: d=140 = 127 fixed-conditioning coordinates + 11 physical measurement coordinates + timestamp + simulator step index. Semantic paths bind exact quantity/unit/frame. Booleans, text and categorical relations are not numerical loss coordinates; missing/extra/null/nonfinite values fail. |
| P and targets | `models/context_projection.py`: current trainable linear P is computed once, width 140. Input `[n_k,p]` and target `[n_(k+1),p]` are both width 280 with the same undetached p. No projected cache, teacher/EMA or gold-answer encoder. |
| Gradient evidence | Real-pair projection-weight gradient norms: input branch `9.9499102e-9`, target branch `2.0421627e-9`; full gradient minus their sum has norm `3.8453210e-16`. Both paths exist; tiny norms are reported, not a claim of sufficient text learning. |
| Pair weights/loss | `training/pairs.py`: optimizer includes P and ODE; rejects weights other than 1; raw equal-coordinate/equal-pair MSE over 2d. Actual runs explicitly selected equal weights. Audit tests multiplicity 3 and all weights remain 1. Historical inverse-multiplicity factory default is corrected below. |
| Solver | `solvers/rk4.py`: external start/end tensors from recorded physical times; one RK4 substep per 0.02 s in this profile. Timestamp/index predictions never schedule the solver. Numerical one-step diagnostics use consecutive recorded inputs and are labeled separately from autonomous inference. |
| Autonomous feedback | `inference/rollout.py`: public last n + initial P(E) only, then every complete predicted 280-vector is the next input. Instrumented k1 states equal the preceding saved prediction exactly, including fixed-conditioning and contextual coordinates. Nothing is reset, rounded or teacher-forced. All 40 saved predictions replay bit-for-bit at external 0.22 through 1.00 s. |
| Answer readout | `inference/readout.py`: semantic measurement columns become named physical channels; authoritative external times are attached. P and numerical clock/index coordinates are not exposed as physical measurements. Public rules provide supported Booleans or unsupported reasons. `providers/openai_answer.py` supplies public input, forecasts and explicit readout statuses to frozen gpt-5.6-sol; original numerical predictions remain independent of generated prose. |

Evidence: [primary-trace.json](artifacts/Post_P07/primary-trace.json). One audit pass
counted 42 solver calls, 81 sample intervals, 168 vector-field calls / 324
sample-weighted evaluations, zero failures and zero optimizer steps. This comprises
one training-pair gradient trace, one batched 40-pair diagnostic and 40 autonomous
steps; it is not a new training run.

Deployment modules accept typed public problems and predictions, not evaluator
truth. `reject_private`, immutable enrichment binding, train-only readers and
the inference signatures enforce that separation; existing tests mutate/delete
private references without changing public reads and reject private enrichment.
Reference states/gold are opened only in training supervision and the evaluator
portion of these audit tools. No benchmark oracle, simulator dynamics or PIN
residual is imported into the learned forecasting path. This is an audited
application boundary, not a claim that an arbitrary malicious replacement provider
or caller cannot put false prose in a public field.

## 3. Numerical-error discrepancy

One-step here means **40 recorded-input adjacent predictions** on the held-out
trajectory. Autonomous means 40 predictions from the cutoff with full-vector
feedback. Both compare the same 140 numerical coordinates at the same reference
times. Decomposition uses saved FP32 model predictions and targets converted to
the training FP32 representation, accumulating squared errors in double precision.
Named physical errors below compare against original reference measurements.

For coordinate j, contribution to raw numerical MSE is
`mean_t((prediction[t,j]-target[t,j])²)/140`. Thus the following contributions
sum to the reported raw loss; within-group MSE has a different denominator and is
also preserved in the JSON. Raw mixed-unit MSE is not a physical accuracy unit.

| Coordinate group | Width | One-step contribution | Autonomous contribution |
| --- | ---: | ---: | ---: |
| Fixed conditioning | 127 | 3.41150e-15 | 1.88823e-12 |
| Physical measurements | 11 | 1.10288e-7 | 1.26604e-6 |
| Timestamp + simulator step index | 2 | 0.641094200340 | 354.845639888025 |
| **All numerical coordinates** | **140** | **0.641094310628** | **354.845641154069** |

The step index alone accounts for **99.9999828%** of one-step and
**99.999999643%** of autonomous raw MSE. One-step predicted index range is
100.526184–490.526184 versus targets 110–500; autonomous range is
100.526184–121.047363 versus the same targets. Its coordinate MSE is
89.753188 and 49,678.389584, respectively. The largest physical contributor is
load angular velocity: coordinate MSE `1.0526491e-5 (rad/s)^2` one-step and
`1.1289263e-4 (rad/s)^2` autonomous.

This is **not a row-number extraction error**. `simulation/engines.py:state`
stores integration-step counts and `timestamp=step*dt`; frozen tether integration
dt is 0.002 s and saved spacing is 0.02 s, so adjacent saved indices differ by 10.
The public cutoff is index 100; references are 110,120,...,500. Pair IDs,
adjacency, exact layout columns, horizon and timestamps all match. The model adds
about 0.526184 per interval, a deficient learned index increment consistent with
the bounded fit. The timestamp itself is accurate: its one-step prediction range
is 0.219999641–0.999999642 s, autonomous 0.219999641–0.999985695 s; coordinate MSE
is only `1.27898e-13` / `7.07914e-11 s²`. It does not drive solver time.

The original training loss around 0.32072 also includes another 140 contextual
coordinates, whose small error roughly halves a numeric-only MSE near 0.641.
That denominator distinction and index drift explain the apparently conflicting
numbers. No coordinate was removed, rescaled, reset or excluded from training.

### Named physical errors and hold-last diagnostic

The diagnostic repeats only the final observed physical measurements at requested
external times. It changes no model coordinate/loss and is **not a new paper
baseline**. Errors use the existing evaluator's native units and vector norms.

| Physical channel | Unit | Primary trajectory RMSE | Hold-last RMSE | Primary endpoint error | Hold-last endpoint error |
| --- | --- | ---: | ---: | ---: | ---: |
| Load position | m | 0.000668809 | 0.000549400 | 0.001775776 | 0.001554614 |
| Load swing angle | rad | 0.003119891 | 0.001301060 | 0.005894898 | 0.001033510 |
| Load angular velocity | rad/s | 0.010625094 | 0.009734709 | 0.018610896 | 0.009719795 |
| Support position | m | 0.001949771 | 0.001380953 | — | — |
| Support velocity | m/s | 0.007097230 | 0.006616216 | — | — |

All 40 timepoints per channel remain in these denominators. The primary checkpoint
does not beat this simple diagnostic here. This is one short, small-motion
validation example, not a method ranking or proof that learned forecasts cannot
improve. Full per-time errors are in
[hold-last-physical.json](artifacts/Post_P07/hold-last-physical.json).

Sensitive dynamics could contribute to physical rollout errors on some systems.
This audit measured neither perturbation amplification nor Lyapunov behavior.
Large mixed-unit loss, accumulated index bias and a familiarity score cannot
diagnose chaos. Here the index discrepancy is already directly explained, while
physical error reflects some combination of insufficient fitting, model/solver
approximation and possible sensitivity; their relative contributions are not
identified. A future sensitivity study would require controlled initial-state
perturbations under identical forcing and solver-resolution checks, with a
separate budget. No such study or architectural change is implied here.

## 4. Custom Coconut/CODI learning audit

Source: `baselines/custom_t5.py`, `custom_checkpoint.py`, `custom_io.py`,
`t5_memory.py`, and `tools/run_p06_custom.py`. Both use the pinned
`google/flan-t5-small` revision recorded in the budget addendum and independent
model instances/checkpoints. These are **custom notebook-inspired baselines**,
not official reproductions.

Within Coconut, one T5 backbone produces public encoder states; masked pooling,
learned queries, gated GRU refinement and output projections append eight latent
vectors to encoder memory. Both training and generation attend to that enhanced
memory. Training predicts the descriptive explanation plus typed labels using
cross-entropy plus `0.001*smoothness`. The latent vectors are functional inputs,
not unused diagnostic tensors.

Within CODI, **teacher and student share the same T5 parameters**, including the
tied token embedding and encoder/decoder. They are different forward paths, not
separate teacher/student backbone objects. Teacher CE uses ordinary public-input
encoding and the explanation+label target. Student CE uses its GRU-enhanced memory
and label target. Loss is teacher CE + student CE + `0.5*alignment` +
`0.001*smoothness`. Separate teacher/student projection modules align the final
decoder states at the actual EOS prediction positions after the full answer.
Teacher projection is fixed at seed 11, excluded from the optimizer and saved;
student projection trains.

`teacher_proj(teacher_final).detach()` stops **alignment** gradients through that
teacher computation. Teacher CE still updates shared T5; student CE and alignment
also update shared T5 through the student path. Consequently teacher representations
can change after an optimizer step even though teacher projection and the teacher
alignment branch are frozen. This is teacher-forced, post-answer alignment, not
evidence of pre-answer reasoning transfer or a stationary independent teacher.

Read-only comparison of actual update-1 and update-2 checkpoint tensors verifies:

| Group | Coconut change L2 | CODI change L2 | Finding |
| --- | ---: | ---: | --- |
| Unique T5 parameters | 0.460815 | 0.489914 | All 190 named parameter tensors changed in each model |
| Learned latent queries / continuous thoughts | 0.00431872 | 0.00444962 | Changed in both |
| GRU cell / thought refiner | 0.0850034 | 0.0850913 | Changed in both; pooling/gates/output modules also changed |
| Student projection | N/A | 0.0380005 | All four tensors changed |
| Fixed teacher projection | N/A | **0** | All four tensors unchanged; requires_grad false and excluded from optimizer |

Both optimizers contain exactly the trainable parameter objects, have finite
states and step counters 2, and restore model values exactly. Parameter counts
deduplicate tied tensors: Coconut 79,858,560 trainable; CODI 79,859,584 total /
79,595,904 trainable. Full groups and original loss histories are in
[custom-checkpoints.json](artifacts/Post_P07/custom-checkpoints.json).

The saved two pre-update Coconut losses are 8.863120 / 9.448321; CODI total losses
12.259123 / 4.365937, with teacher CE 2.063279 / 2.017634, student CE
9.864379 / 2.034575 and alignment 0.662920 / 0.627447. These two observations do not
establish a learning curve, convergence or output quality. Tests isolate alignment
student gradients, zero teacher-branch alignment gradients and positive teacher-CE
backbone gradients. Checkpoint updates can include AdamW effects as well as loss
gradients; update differences alone are not causal gradient attribution.

Training is teacher-forced with dropout and use_cache false; generation is
autoregressive in eval mode. Student-only generation accepts public input without
gold/teacher output. The hybrid generates teacher and student independently:
**teacher explanation is returned in the response, not fed into the student**.
Teacher-label fallback uses only generated teacher labels after observable
student parsing/generation failure, never correctness against gold. Training
descriptions are descriptive supervision, not verified reasoning.

The P07 serialization/EOS/padding/stopping audit remains applicable: these fixes
change neither targets, labels, masking nor valid-branch generation. Its evidence
is reused, and associated offline tests pass again. Tether teacher/student targets
contain 554/523 tokens including EOS at indices 553/522; longest selected target
is 1,025, below 2,048. Correctly shifted EOS positions and `-100` padding exclusion
were verified. The reversible `ZXQ` codec handles unsupported punctuation without
changing signs, decimals, units or Boolean types; no target truncation/answer repair.

Output failures remain unchanged: Coconut emits EOS at 173/156 tokens on
train/validation but both outputs fail typed parsing. CODI student and teacher
each reach 2,048 tokens without EOS on both questions (four failed calls).
Hybrid attempts fallback twice and recovers neither. Student-only and hybrid each
retain 0/1 complete-answer success per split; failed examples remain denominators.
The prepared [20-update training-only fitting diagnostic](Post_P07_next_pilot_revision.md)
will measure losses, valid typed output rate, EOS and accuracy if separately
authorized. More updates are not guaranteed to resolve the failures.

## 5. Controls, ablations and fair evaluation

Actual preserved [ablation checkpoints](artifacts/Post_P07/ablation-checkpoints.json)
have distinct hashes, changed parameters relative to their own seeded initializers,
and the same 20 physical transition IDs as the primary. Their source constructs
fresh models; no primary trained weights are loaded.

| Variant | Path removed / retained | Width, parameters and original compute |
| --- | --- | --- |
| no_enrichment | Frozen Qwen encodes original public Q/C only; base context rejects enrichment arguments. P, full target gradients and full feedback retained. Downstream answer provider receives original public information and separate forecast. | 280 state width; 232,228 parameters; 200 updates, 2.578 CPU s; full augmented MSE |
| no_text_conditioning | No E, P, p or contextual target in forecasting; no zero placeholders. Complete accepted n including fixed conditioning retained. Answer LLM still gets original public Q/C and named numerical predictions. | 140 state width; 52,748 parameters; 200 updates, 2.105 CPU s; numerical MSE |

Both use the same split, physical intervals, equal transition weights, RK4 and
final predeclared checkpoint policy. The shared ablation preparation runner reads
cached base embeddings for the no_enrichment branch, but the numerical-only model,
training call and inference call consume no embedding. It is not exact capacity
matching; raw losses with different coordinate counts are not comparative quality
metrics. Existing fresh-process replay evidence is retained, not rerun as new
independent evidence. Undefined no-schema and PIN-ODE remain excluded.

The three shared supported numerical targets provide a fairer public-only
comparison than complete-answer success: **all three numerical targets pass the
unchanged tolerances for primary, public-only and reversal**. Public-only absolute
errors are 0.000005326 m, 0.000003226 rad and 0.000001262 rad/s, smaller than the
forecast answer errors on this question. It receives the same original public
question/control information and frozen answer provider, with forecast payload
removed. These one-call results do not establish an advantage or causal mechanism.

Public-only deliberately has no forecast-based Boolean readout and returns
`unsupported` for boundary_crossed. Forecast-based conditions use the qualified
public rule and report false correctly here. Consequently complete success is
0/1 public-only versus 1/1 primary, but that difference **cannot be attributed
solely to better numerical QA**. Keep both complete denominators and report
Boolean-policy differences alongside the common numerical subset.

Reversal reassigns the existing physical measurements in reverse chronological
order while retaining external timestamps. Actual queried-value changes are:

| Target | Absolute change | Existing tolerance | Change / tolerance |
| --- | ---: | ---: | ---: |
| Load position (vector norm), m | 0.000216339 | 0.01 | 0.0216339 |
| Swing angle, rad | 0.006755199 | 0.01 | 0.675520 |
| Angular velocity, rad/s | 0.008668823 | 0.02 | 0.433441 |
| Boundary-crossed Boolean | 0 | exact | unchanged false |

Thus reversal changes numerical values but less than each tolerance; Boolean
output is a no-op. Unchanged pass/fail answers are weak evidence about sensitivity
to forecast information. [Controls data](artifacts/Post_P07/controls-common-targets.json)
retains actual predictions and answer errors. No tolerance is changed.

`without_fallback` is a true no-op on this successful technical path; no fallback
was active. `without_fixed_assessment` removes an actual assessment payload, so its
runtime `no_op=false` is correct for metadata, but the partial assessment was not
controlling the forecast/answer: it is an **answer/trajectory no-op** here. Cached
answers reused for these controls are zero new independent observations. These
are runtime controls, distinct from the independently retrained ablations.

## 6. Coverage, assessment and the two research questions

The [coverage matrix](Post_P07_coverage_matrix.md) lists every answer binding and
exact missing evidence. The all-public scan finds 2,400 unsupported stable_stack
and 2,400 unsupported support_lost components, plus 152 boundary-crossed components
with unqualified initial latch state. Contact-dependent results cannot be recovered
from current predicted coordinates without sufficient additional evidence. All
8,038 public contexts have **zero typed controller constraints**; empty required
contract coverage is unavailable, not zero severity. Calibration remains absent.

### RQ1: dynamical-system QA, domain engineering and richer outputs

| Part | Implemented mechanism / available evidence | Remaining evidence or limitation |
| --- | --- | --- |
| Forecasting and QA | Full2d model, public-rule readout and frozen answer interface; exact replay/gradient/leakage tests; one tether validation answer 1/1 complete | No convergence, multi-scenario generalization, four-domain forecast qualification or ranking; hold-last and public-only diagnostics caution against inferring learned physical skill |
| Avoiding extensive domain engineering | Learned vector field, P and solver are generic; no force-law residual/oracle in prediction | Domain knowledge is authored in simulator/public model descriptions, state/layout/unit/frame registrations, target/rule mappings, four Boolean readouts, three families of physical checks, prompts/schema and explicit unsupported policies. The 20 target bindings and exact public rules are enumerated, not “zero engineering.” No comparative labor/generalization measurement establishes reduced engineering yet |
| Richer outputs | Numerical trajectories by physical time, typed answers/units, explicit unsupported reasons, physical-check coverage/violations, separate familiarity/V1/contract status and block diagnostics; original predictions preserved | Only one trajectory measured; accurate provenance/status does not make the forecast/explanation physically correct. Contact outputs absent; generated explanations are not verified causal accounts |

Locations of authored knowledge: `simulation/engines.py`, `bullet.py`, domain
configs/assets (data generation/public descriptions); `integration/layout.py`
and P02a layout manifests (representation); `simulation/records.py` and
`inference/readout.py` (20 output bindings, exact event thresholds/history);
`assessment/checks.py` and assessment config (quaternion/tether/redundant-channel
checks); preserved extraction/answer/judge assets (language/schema instructions).
These boundaries are disclosed. Adding support checks later would add domain
engineering and must be reported as such.

### RQ2: recognizing and clarifying OOD scenarios

**Recognition mechanism.** `assessment/reference.py` filters training-only
predicted references by domain/layout and physical grid/horizon, retrieves k=1 by
frozen public-context embedding, and scores terminal `1-cosine` of the complete
augmented prediction. Same model/P/E identities are required; changes invalidate
the bank. Entire query scenario is excluded for train queries; missing-compatible,
nonfinite and zero-norm cases are explicit. This is fixed development familiarity,
not ground-truth distance, calibrated uncertainty or a learned EBM.

The actual query familiarity is `1.30849248e-5`. Query/reference norms are
121.074861/121.074042 for dynamic numerical coordinates (including index/time),
6.232738/6.074381 for fixed conditioning, and 1.613803/1.616199 for contextual
coordinates. Their additive familiarity contributions are `2.17313e-7`,
`1.28352e-5` and `3.24366e-8`. A small score can reflect similarity of two
underfit **predictions**; it does not contradict error against true trajectories.
No normalization or weights were changed.

The unchanged V1 judge receives original scenario/schema and returns a bounded
score plus a reason about their consistency. Its saved score is 0; the reason
describes matching entities, units, controls and requested channels. Required
typed contract checks are absent, so combination is **partial, score null,
threshold decision null**. The implemented calibration policy requires complete
assessments from at least 20 separate validation-ID calibration scenarios, apart
from selection, using per-scenario maxima and a 0.95 higher quantile. No calibrated
alarm or ID/OOD detection metrics have been measured. One ID query cannot establish
AUROC, detection sensitivity, false-alarm rate or OOD localization.

**What “clarification” currently does.** There is no separately implemented,
qualified OOD clarification task. Existing outputs provide (a) reference identity,
compatibility/missing-component reasons and block diagnostics from predictions,
(b) supported physical/typed-contract checks from permitted channels and public
metadata, and (c) V1's public scenario/schema consistency reason. Tests and saved
artifacts verify those diagnostics are emitted; they do **not** verify an OOD
explanation. The answer LLM receives public information and readout/forecast
payloads, not a newly defined OOD-cause explanation task. No system path asks the
user to resolve an OOD cause, repairs a schema, corrects a trajectory or identifies
an unobserved cause. Technical fallback is separately labeled and high-score
numerical replacement stays disabled.

Operational clarification remains a scientific decision. Recommended initial
definition: an evidence-bounded account of which public conditions/compatible
references/checks are available or missing and why recognition is partial or
flagged, with uncertainty and supported scope explicit. This would not assert a
physical cause from latent similarity. Its content and correctness criteria need
approval before implementation or any clarification-performance claim.

## 7. Fixes and verification

| Fix / affected file | Demonstrated problem and correction | Effect on saved runs |
| --- | --- | --- |
| `src/phi_jepa/integration/readers.py` | `make_pairs` default still selected historical inverse multiplicity; now defaults to approved equal question pairs. Explicit legacy option remains for reproducibility; active trainer rejects non-unit weights | None: original empirical runners explicitly used equal weights |
| `src/phi_jepa/baselines/custom_checkpoint.py` | Standalone training restore omitted configured gradient checkpointing; loader now restores non-reentrant checkpointing from checkpoint identity | None: original runner already re-enabled it after restore |
| `src/phi_jepa/baselines/custom_t5.py` | Coconut could accept the label “student,” or CODI “coconut,” while running the same enhanced path; now mismatched condition names fail | None: actual saved calls used the correct branch names |
| `src/phi_jepa/coordinate_diagnostics.py`; `tools/audit_post_p07*.py` | New evaluator-only decomposition, source trace, support inventory and checkpoint diagnostics. Time/tolerance unit overrides prevent parent-target units from incorrectly labeling metadata fields | New derived artifacts only; no model/loss change |
| `tests/test_p02a.py`, `tests/test_post_p07_audit.py` | Active default assertion plus multiplicity/legacy-policy, MSE conservation, unit-label, standalone-resume and generation-label regressions | Offline synthetic verification only |
| New reviews/decision + `docs/PROGRESS.md` | Reconcile historical provenance with present checkout; document limits and future protocol | Original completion reports, decisions and checkpoints preserved |

Commands actually run in WSL Ubuntu-24.04, repository cwd, core Python
`/home/aashraf/phi-jepa/.venvs/phi-core/bin/python`, `CUDA_VISIBLE_DEVICES=`:

```text
timeout 300 .../python tools/audit_post_p07.py --native-root /home/aashraf/phi-jepa --output /home/aashraf/phi-jepa/post-p07-audit-01
timeout 300 .../python tools/audit_post_p07.py --native-root /home/aashraf/phi-jepa --output /home/aashraf/phi-jepa/post-p07-audit-02
timeout 180 .../python tools/audit_post_p07_checkpoints.py --native-root /home/aashraf/phi-jepa --output /home/aashraf/phi-jepa/post-p07-audit-01/custom-checkpoints.json
timeout 60 .../python tools/audit_post_p07_ablations.py --native-root /home/aashraf/phi-jepa --output /home/aashraf/phi-jepa/post-p07-audit-01/ablation-checkpoints.json
PYTHONPATH=src timeout 180 .../python -m unittest discover -s tests -p "test_p*.py"
```

All diagnostic commands exited 0. First regression pass: 123 tests; final after
unit-annotation regression: **124 tests passed in 17.111 s**
([log](artifacts/Post_P07/tests-final.log)). Coverage includes both P-gradient
paths, adjacent alignment, full feedback, leakage, finite failures, checkpoints,
typed parsing, event support, assessment/calibration and custom alignment/memory
equivalence. Existing EOS/padding audit is reused, not recast as a new generation
experiment. GPU/provider tests were not rerun. No simulator dependency installation
or all-project test expansion was needed for these scoped changes.

Original measured resource evidence remains in P06/P07: two-update fits took
16.237 s Coconut / 25.031 s CODI; peak allocated GPU memory 2.415 / 2.959 GB.
Longest selected-input qualification peaked at 2.857 / 3.889 GB. Six unique saved
generation calls used 60,648 input and 8,521 output tokens; all-condition generation
time was 6.22 s Coconut / 51.95 s CODI. Validation student-only took about 12.29 s,
hybrid 24.44 s including teacher. Historical shared provider preparation/answers
cost USD 0.831996 across 17 calls; this audit's new provider cost is **zero**.
These are existing measurements, not audit-time performance remeasurements.

## 8. Remaining issues and anticipated reviewer questions

| Issue | Classification | Resolution / remaining work |
| --- | --- | --- |
| Historical default weights, standalone resume option, branch label acceptance | Implementation bugs | Fixed and regression-tested; no historical model retraining needed |
| Primary index underprediction and no hold-last advantage on this trace | Insufficient training evidence | Bounded checkpoint is demonstrably inaccurate on index; root causes beyond verified data path are not isolated. Preserve objective and measure learning/physical errors in an authorized next pilot |
| Zero valid custom answers after two updates | Insufficient training evidence / unresolved output quality | Optimizer/gradient paths verified; no convergence conclusion or guarantee. Proposed training-only fitting diagnostic |
| Stable stack, support lost; 152 ambiguous initial crossings | Unsupported capability | Keep explicit reasons and complete-answer denominators; sufficient future evidence/initial-state conventions require separately reviewed work |
| Empty required typed contracts | Unsupported capability + scientific decision | Operator code exists; a reviewed public-evidence contract policy is absent. Keep assessment partial |
| Calibration/detection performance | Unsupported empirical capability | Complete components plus separate validation calibration and sealed ID/OOD evaluation needed |
| Meaning/evaluation of OOD clarification | Scientific decision | Define and qualify evidence-bounded outputs before implementing claims |
| Four-domain learning, multiple seeds, sensitivity and comparative engineering reduction | Missing broader research evidence | Separately budgeted future evaluation; not part of this audit |

Anticipated reviewer questions:

| Question | Evidence available now | Missing evidence / honest answer |
| --- | --- | --- |
| Does the implementation actually follow full2d learning with target gradients? | Source, real-pair gradients, exact replay, contract tests | Training effectiveness across data/scales remains unmeasured |
| Why is raw MSE huge while position looks accurate? | Full coordinate decomposition and verified index/time alignment | Mixed-unit objective is unchanged; high index error cannot be marketed as physical trajectory error |
| Is the method better than doing nothing? | Hold-last diagnostic beats this checkpoint on all five reported trajectory channels | Meaningfully trained multi-scenario comparison |
| Does text/enrichment help? | Independent ablations and common numerical targets; no-enrichment pathway removal checked | Statistical benefit across scenarios/seeds; current one-question evidence cannot show it |
| Does reversal prove the answer LLM uses forecasts? | Actual changed values and unchanged tolerances; numeric answers reflect those readouts | Perturbations below tolerance give weak binary evidence; no causal reliance claim |
| Were custom baselines broken by masking/optimizer errors? | EOS/serialization/padding audit, unique optimizer membership, checkpoint deltas, isolated gradient tests | Training-only fit and held-out valid-generation curves; more updates may still fail |
| Is the CODI teacher frozen/independent? | Teacher projection frozen; shared T5 explicitly documented | No independent frozen teacher or official CODI reproduction is claimed |
| What authored physics remains? | Enumerated source boundaries, 20 output bindings, four Boolean rules and limited check families | Comparative engineering effort/generalization measurement |
| Can all output types be answered? | Exhaustive four-domain target matrix and 8,038-public-context inventory | Contact-dependent support and ambiguous initial latch cases remain unsupported |
| Does a low score mean physical correctness or ID membership? | Raw score/block norms, train-only bank, partial-status policy | Calibrated detection and ID/OOD performance; no such interpretation licensed |
| What exactly does OOD clarification explain? | Current technical diagnostics and V1 consistency reason are identified | Operational definition, implementation and explanation correctness benchmark |
| Are there leaked future truths or reused scenarios? | Public/evaluator separation, content-bound caches, whole-scenario exclusion, train-only reference bank | Broader run-specific contamination/split audits must accompany future selections |
| Are failures and teacher costs hidden? | All parsing/EOS/fallback failures retained, teacher-plus-student timing/counts | Broader cost/quality tradeoffs after meaningful training |
| Could chaos explain rollout failures? | Index error has a direct coordinate explanation; physical errors measured separately | No perturbation/sensitivity/chaos analysis was performed |
| Is this a completed study? | Bounded implementation pilot plus this source audit are complete within scope | Full training, four-domain/ID/OOD evaluation, calibration, clarification and performance claims remain pending |

## 9. Decisions genuinely requiring user input

1. **Operational meaning of OOD clarification.** Evidence: no distinct
   implementation/evaluation exists; current outputs are component/status reasons
   and V1 scenario/schema consistency. Recommended: approve an evidence-bounded
   diagnostic explanation as the first clarification target, with explicit
   abstention on causes and a separate evaluation specification. Consequence:
   supports a reviewable limited RQ2 task; causal clarification would need different
   evidence and a separate scientific scope. No implementation is presumed approved.
2. **Whether to authorize the revised next pilot.** Evidence: source paths work,
   two-update typed generation fails, and current forecast/control comparisons are
   weak. Recommended: use the existing proposed caps with the documented
   20-update fitting diagnostic carved out, leaving 180 broader custom updates
   from fresh initialization. Consequence: makes failure interpretation more
   informative without increasing aggregate caps, but allocates fewer broader
   training updates. It remains unlaunched until explicitly authorized.

Contact mechanisms, additional public contracts and calibration remain listed
future work, not reopened approvals or blockers for completing this audit. The
accepted architecture, equal-pair weighting, model selections, Boolean subset,
fixed reference score and custom baseline definitions remain unchanged.
