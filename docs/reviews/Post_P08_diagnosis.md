# Post-P08 offline forecasting and generation diagnosis

25 September 2026. P08 is closed as a **completed bounded pilot**. Learning quality,
generalization, calibrated OOD recognition and research claims remain unresolved.
This follow-up performs no training, paid calls, new generation or objective/architecture
change. Clarification integration is a separate task and report.

Source inspected: `c6922b16a254a72be58482773e3410fa6eecd0c8` on
`full-phi-jepa-from-dataset`. Historical P08 reports correctly describe their run-time
working tree as uncommitted; the user subsequently committed that work at this revision.
This follow-up is a new local change, with no commit or push performed by the agent.
Original P07/P08 reports, predictions and checkpoints are preserved. The new
[manifest](artifacts/Post_P08_diagnosis/manifest.json) hashes every consumed artifact,
checks those hashes after diagnosis, and records zero optimizer updates/provider calls.

## Physical forecasting

**Measured behavior.** The linked [per-time CSV](artifacts/Post_P08_diagnosis/physical_errors_by_time.csv)
contains all 11,200 method/scenario/time/quantity errors (seven conditions, eight
scenarios, 40 times, five physical quantities). [Window CSV](artifacts/Post_P08_diagnosis/physical_errors_by_window.csv)
retains each scenario and full horizon. Scalar errors are absolute; vector errors
are Euclidean. RMSE aggregates those errors, without mixing units. Forecast samples
start at 0.22 s: windows are (0.20,0.60] and (0.60,1.00], each 20 points; 0.20 s is
the observed initialization, not a predicted point. No tolerance or denominator changes.

Full-horizon physical RMSE (hold-last is a diagnostic, not a paper baseline):

| Method | load:position (m) | load:swing_angle (rad) | load:angular_velocity (rad/s) | support:position (m) | support:velocity (m/s) |
| --- | --- | --- | --- | --- | --- |
| phi_jepa | 0.111685 | 0.16496 | 0.213835 | 0.00402238 | 0.0123409 |
| constant_context_text_ode | 0.111525 | 0.164869 | 0.213846 | 0.00353895 | 0.0123639 |
| fixed_projection_lr | 0.0568868 | 0.0641895 | 0.569494 | 0.0273169 | 0.325955 |
| constant_context_text_rnn | 0.149695 | 0.0787053 | 0.307867 | 0.00209643 | 0.0376733 |
| no_enrichment | 0.111685 | 0.16496 | 0.213835 | 0.00402242 | 0.0123409 |
| no_text_conditioning | 0.111529 | 0.164873 | 0.213845 | 0.00358591 | 0.0123638 |
| hold_last | 0.110158 | 0.148269 | 0.218302 | 0.00264249 | 0.0108181 |

Primary early / late RMSE, by entire held-out scenario; columns retain physical units:

| Scenario | Event start/end (s) | Load position (m) | Angle (rad) | Angular velocity (rad/s) |
| --- | --- | --- | --- | --- |
| f3799e01b5cacbbbe601dd0cdf9ed7f0 | 0.446/0.646 | 0.0151738 / 0.0253226 | 0.00946232 / 0.0127348 | 0.0205055 / 0.166568 |
| c54f95a215497140b51ecbd6a59ac39e | 0.464/0.664 | 0.0168752 / 0.0408151 | 0.0359071 / 0.0875551 | 0.0311182 / 0.03091 |
| 3bf38b2bdc81ae2e946b97d6c92a3ed9 | 0.504/0.704 | 0.0355433 / 0.0591949 | 0.0450278 / 0.070974 | 0.049358 / 0.348611 |
| e8005c66efe569eae00c134f4f2cb3af | 0.540/0.740 | 0.0798788 / 0.177878 | 0.116746 / 0.263636 | 0.142187 / 0.197222 |
| f1e4d421b24f2d37e28902f12da000dd | 0.408/0.608 | 0.101866 / 0.211743 | 0.158071 / 0.335966 | 0.163508 / 0.39128 |
| 91ccb933f39fc2eeffe4d2a94a9d4ab8 | 0.402/0.602 | 0.0728583 / 0.173932 | 0.0621153 / 0.145176 | 0.118354 / 0.166044 |
| a1563cb383df538a5dbe17e2e177b670 | 0.494/0.694 | 0.00879562 / 0.0206135 | 0.0284089 / 0.06579 | 0.0217996 / 0.0268777 |
| 8e37da92e970ba6c2809a5476a61c811 | 0.586/0.786 | 0.111918 / 0.223979 | 0.181282 / 0.367684 | 0.188666 / 0.510132 |

**Measured behavior.** Pooled primary load-position RMSE rises from 0.0674973 to
0.142798 m; angle from 0.0997189 to 0.210902 rad; angular velocity from 0.112280
to 0.280792 rad/s. Primary is worse than hold-last on position/angle in both windows,
slightly better on full-horizon angular velocity. LR's late angular-velocity RMSE
is 0.802735 rad/s despite its smaller raw coordinate MSE. These are eight-scenario
measurements, not reliable method rankings.

### Scheduled controls and exposure

**Measured behavior.** The permitted controller specifies stationary support until
onset, positive acceleration for 0.1 s, negative acceleration for 0.1 s, then
stationary support; intervals use [start,end). This diagnostic reads that public
description and event times; it never executes formulas or imports oracle dynamics.
Training selects the first 20 adjacent transitions, 0.20–0.60 s, from each of 32
questions. All eight validation scenarios are excluded in full. Event onsets vary;
the recorded [regime inventory](artifacts/Post_P08_diagnosis/scheduled_regimes.json)
includes exact events, public controller and boundary-straddling intervals.

Training interval midpoint counts (boundary intervals are separately identified):

| Regime | Unique training intervals |
| --- | --- |
| pre_event | 467 |
| positive_acceleration | 126 |
| negative_acceleration | 47 |
| post_event | 0 |

Primary validation RMSE grouped by the public event regime at the forecast timestamp:

| Quantity | Regime | Points | RMSE |
| --- | --- | --- | --- |
| position | pre_event | 109 | 0.0549765 |
| swing_angle | pre_event | 109 | 0.0857874 |
| angular_velocity | pre_event | 109 | 0.114731 |
| position | positive_acceleration | 40 | 0.0998373 |
| swing_angle | positive_acceleration | 40 | 0.152129 |
| angular_velocity | positive_acceleration | 40 | 0.10499 |
| position | negative_acceleration | 40 | 0.122255 |
| swing_angle | negative_acceleration | 40 | 0.183226 |
| angular_velocity | negative_acceleration | 40 | 0.120685 |
| position | post_event | 131 | 0.142646 |
| swing_angle | post_event | 131 | 0.207438 |
| angular_velocity | post_event | 131 | 0.304845 |

**Unresolved hypothesis.** Missing post-event supervision and limited negative-phase
coverage can contribute to late errors, but time, elapsed rollout, and event phase
are confounded. Errors already exist before interventions. These tables establish
association, not event causality. Sensitive/chaotic dynamics remain possible in
principle; no perturbation growth experiment or Lyapunov analysis was performed.
Large errors and small familiarity scores do not diagnose chaos. Near-constant
learned derivatives provide a directly measured alternative failure mechanism.

### Training and gradients

**Measured behavior.** All five neural fits reached 1,000 updates. Each update used
20 chronological transitions from one question; 24 questions had 31 exposures and
eight had 32 (620/640 per-question transition presentations). Pair weights remained
one. Adam used lr=0.001, betas=(0.9,0.999), epsilon=1e-8, weight decay=0 and no
scheduler. Selection was the last configured update, with checkpoints every 100;
no validation loss was used to choose a checkpoint. LR used a single fixed-projection
least-squares fit, rcond=1e-12 and numerical rank 40 of 281 design columns.

| Method | First / last training loss | Clip >1 updates / 1000 |
| --- | --- | --- |
| phi_jepa | 0.357146 / 0.203523 | 0 |
| constant_context_text_ode | 0.71432 / 0.407154 | 0 |
| constant_context_text_rnn | 325.795 / 59.2518 | 1000 |
| no_enrichment | 0.357146 / 0.203523 | 0 |
| no_text_conditioning | 0.714289 / 0.407333 | 0 |

Loss dimensions differ: these losses are not physical performance comparisons.
[100-update means and exact exposure](artifacts/Post_P08_diagnosis/training_exposure_and_curves.json)
show decreasing losses; the original P08 curves remain unchanged. RNN clipped on
all updates; primary and all ODE variants never clipped. Primary's recorded norm
range was 0.00997575–0.0160584, so clipping does not explain its small physical updates.

**Measured behavior.** At saved updates 100 and 1000, two training and two validation
questions were inspected at pair starts 0.20, 0.40, 0.58 and 0.80 s (32 total
checkpoint/example/pairs). All four block losses are sums divided by the **same
full 2d batch denominator**, so they add to the approved objective. `autograd.grad`
used both undetached occurrences of current p; no optimizer was constructed, no
parameters changed. Late pairs from training scenarios are diagnostic references,
not previously selected training examples. Norms are pre-clip parameter gradients,
not optimizer update sizes; Adam's adaptive moments can change their influence.

Final-checkpoint ranges over the four inspected questions:

| Block | Full-loss contribution range | Parameter gradient norm range | Projection gradient norm range |
| --- | --- | --- | --- |
| physical | 1.1197e-07–4.8778e-07 | 6.3648e-06–1.0453e-05 | 7.0454e-17–2.0821e-16 |
| time_index | 0.2034–0.2034 | 0.012245–0.012245 | 3.0319e-10–3.0883e-10 |
| fixed_conditioning | 4.1012e-15–4.1298e-15 | 1.7387e-09–1.7448e-09 | 2.7444e-21–2.8479e-21 |
| contextual | 3.7905e-16–3.8277e-16 | 5.286e-10–5.3118e-10 | 5.2541e-22–5.5016e-22 |

Complete values and cosine against the summed gradient are in
[gradient_blocks.json](artifacts/Post_P08_diagnosis/gradient_blocks.json).
The time/index block dominates both loss and total gradient norm on this bounded
sample; this is stronger evidence than loss magnitude alone, but does not prove
that reweighting would fix learning (and no reweighting is authorized).

**Measured behavior.** At update 1000, the maximum physical derivative span across
four recorded states was 9.31e-10; a cached-context swap changed physical derivatives
by at most 4.66e-10. First-layer tanh activations had |activation|>0.99 for 99.80%
of inspected units; the second layer reached 100%. At update 100 the physical span
was at most 2.98e-7, with second-layer saturation already 100%.
[Derivative records](artifacts/Post_P08_diagnosis/derivative_variation.json) retain all
coordinates. This tests the primary vector field only and is not evidence that
text is intrinsically useless. Input magnitude, learned weights and activation
saturation are entangled; a causal attribution to a particular coordinate needs
controlled sensitivity measurements.

**Verified bug: none identified in the approved numerical computation.** Source
tracing confirms d=140, p=140, width=280, same current p on input/target with target
gradients, raw adjacent-pair MSE, equal weights, external physical RK4 grid and full
predicted-vector feedback (including fixed conditioning and p). Index rises by 10
per 0.02 s because the public integration interval is 0.002 s; timestamp and index
are distinct. Final primary one-step index increments are about 2.45336 instead
of 10. Timestamp predicts approximately the correct interval. No extraction,
unit or reference-offset error was found. One-step numerical MSE 0.406802 versus
autonomous 225.164 is overwhelmingly index error; named physical errors remain
poor independently. Original coordinate breakdowns and one-step physical results
are retained in P08. Saturation is a measured learning behavior, not permission
to rescale coordinates, reset feedback or change the objective.

## Custom generation

**Measured behavior / source-verified paths.** `custom_io.training_targets` creates
teacher/Coconut JSON with `explanation` and `targets`; CODI student JSON has only
`targets`. [Exact training targets](artifacts/Post_P08_diagnosis/training_target_trace.json)
are diagnostic-only training records. The same public text includes the original
input and enrichment and a generic configured-format instruction. There is no
branch-specific role token or separate teacher/student backbone. Teacher uses the
plain T5 encoder; student appends eight input-conditioned GRU-refined continuous
latent memory vectors with attended masks. Coconut uses its own pooled/gated GRU
latent construction. These latent paths are used in both training and generation.

CODI teacher and student share all T5 backbone parameters. Teacher CE updates that
backbone; student CE and alignment update the same backbone via the student path.
Only the teacher **alignment target** is detached. `teacher_proj` is fixed, excluded
from the optimizer and saved/restored; `student_proj` learns. Teacher-forced final
decoder states align at actual EOS prediction positions. Alignment is post-answer,
not verified pre-answer reasoning transfer. Checkpoint restoration is strict and
the approved gradient-checkpoint restoration fix is present. P08 recorded changes
in 190 shared backbone tensors and the respective latent/projection paths; its
EOS/serialization/padding audit remains applicable because model/codec source is
unchanged. No targets or gold explanations enter evaluation generation.

**Measured behavior.** All eight final CODI student outputs reached EOS and emitted
the teacher envelope `explanation,targets`; strict student parsing rejected every
one as `answer_envelope`. Teacher typed validity was 8/8, student 0/8; the hybrid
used teacher fallback on all eight, recovering validity, not student accuracy.
Teacher explanation is returned by composition, never fed to the student. Coconut
had 4/8 strict valid outputs; all four failures emitted five rows for four targets.

| Sample | Duplicated target | Omitted targets | Additional malformed binding |
| --- | --- | --- | --- |
| 1bbb33b715cd2013a19bb6530cf530a0 | load:position | [] | row 1: answer_type |
| c0863ac062786727c369aa55050f61a0 | load:swing_angle | [] | row 1: quantity; row 2: unit |
| a7aac3d1a98fb47e47c9e3c1758288d8 | load:swing_angle | [] | row 1: quantity; row 2: unit |
| 084bac04e8203ef56e8dec4e650d520f | load:position | [] | row 1: answer_type |

Rows are zero-based. Duplicate position rows declare number while carrying a
vector. Duplicate angle rows additionally misbind quantity/unit. Raw envelopes
remain in [generation_failure_trace.json](artifacts/Post_P08_diagnosis/generation_failure_trace.json).
This inspection neither removes duplicates nor strips explanations, and does not
rescore recognizable numbers. Official invalid/accuracy denominators are intact.

**Verified bug: none demonstrated in branch routing, target serialization or
training-versus-generation latent memory.** Teacher-style student output is a
measured mismatch with the desired student target, not evidence that generation
accidentally called the teacher branch. **Unresolved hypotheses:** the latent-only
branch distinction may be too weak, shared losses may interfere, long public inputs
may overwhelm the latent distinction, or limited fitting may be insufficient.
Neither this source audit nor decreasing teacher-forced loss isolates those causes.
More updates are not guaranteed to resolve duplicate targets or branch envelopes.

## Smallest justified next experiment (proposal; not executed)

Before another learning pilot, use frozen checkpoints and training questions only:
(1) inspect layer preactivation contributions and per-coordinate Jacobians at
16 saved states, retaining original inputs as the reference and labeling every
controlled perturbation diagnostic; (2) on four predeclared training questions,
compare CODI student latent memory versus masked latent memory and the plain teacher
path, plus Coconut, at unchanged greedy generation limits and strict parsers.
This is 16 local generation calls, at most 32,768 generated tokens. Keep gold outside
generation. Inspect branch-format probability/attention differences and validity;
failure remains informative. No training/objective/coordinate changes are proposed.

Proposed aggregate cap: **15 GPU minutes, 10 CPU minutes, 250 MB new artifacts,
zero optimizer updates, zero provider attempts and USD 0**; stop at first cap.
The purpose is to distinguish insensitive conditioning from insufficient fitting,
not guarantee a fix. If a later proposal introduces role-specific prompts or input
scaling, it must explicitly state the changed scientific condition and obtain
authorization; neither was implemented here.

## Closure and verification

`tools/diagnose_post_p08.py` completed on CPU with two threads, 32 diagnostic pairs,
zero updates/generations/provider calls, unchanged parameter hashes, scenario
separation assertions and post-read source-hash verification. Execution timing is
in the manifest (model/data work only; not agent/reporting wall time).
`tools/report_post_p08_diagnosis.py` renders these tables from the derived evidence.
No forecasting or custom-model source was modified. P08 is complete as bounded
execution, with insufficient learning, unproven generalization, unsupported
contact/support capabilities, missing typed assessment contracts and uncalibrated
OOD recognition still unresolved. The clarification correction/proposal remains
separate; the next implementation report will document its newly approved policy.
