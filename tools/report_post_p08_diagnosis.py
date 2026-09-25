"""Render measured tables from the separate offline diagnosis, no model calls."""
import csv
import json
import math
from collections import Counter, defaultdict
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]
D=ROOT/'docs/reviews/artifacts/Post_P08_diagnosis'
load=lambda n:json.loads((D/n).read_text())
rows=list(csv.DictReader((D/'physical_errors_by_window.csv').read_text().splitlines()))
errors=list(csv.DictReader((D/'physical_errors_by_time.csv').read_text().splitlines()))

def md(headers, rows):
    return '\n'.join(['| '+' | '.join(headers)+' |','| '+' | '.join(['---']*len(headers))+' |']+['| '+' | '.join(map(str,r))+' |' for r in rows])

methods=list(dict.fromkeys(r['method'] for r in rows))
quantities=[('load','position','m'),('load','swing_angle','rad'),('load','angular_velocity','rad/s'),('support','position','m'),('support','velocity','m/s')]
def metric(method,scenario,entity,quantity,window):
    return float(next(r['rmse'] for r in rows if (r['method'],r['scenario_id'],r['entity_id'],r['quantity'],r['window'])==(method,scenario,entity,quantity,window)))

reg=load('scheduled_regimes.json'); counts=Counter()
for r in reg: counts.update(r['training_regime_counts'])
val=[r for r in reg if r['split']=='validation']
grad=load('gradient_blocks.json'); final=[g for g in grad if g['checkpoint_update']==1000]
report='''# Post-P08 offline forecasting and generation diagnosis

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

'''
report+=md(['Method']+[e+':'+q+' ('+u+')' for e,q,u in quantities],[[m]+[f'{metric(m,"ALL",e,q,"full_horizon"):.6g}' for e,q,u in quantities] for m in methods])
report+='\n\nPrimary early / late RMSE, by entire held-out scenario; columns retain physical units:\n\n'
report+=md(['Scenario','Event start/end (s)','Load position (m)','Angle (rad)','Angular velocity (rad/s)'],[[r['scenario_id'],f"{r['event']['start_time']:.3f}/{r['event']['end_time']:.3f}"]+[f'{metric("phi_jepa",r["scenario_id"],e,q,"(0.20,0.60]"):.6g} / {metric("phi_jepa",r["scenario_id"],e,q,"(0.60,1.00]"):.6g}' for e,q,u in quantities[:3]] for r in val])
report+='''

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

'''+md(['Regime','Unique training intervals'],[[k,counts[k]] for k in ('pre_event','positive_acceleration','negative_acceleration','post_event')])
phasegroups=defaultdict(list)
for e in errors:
    if e['method']=='phi_jepa' and e['entity_id']=='load': phasegroups[(e['quantity'],e['regime'])].append(float(e['error']))
report+='\n\nPrimary validation RMSE grouped by the public event regime at the forecast timestamp:\n\n'
report+=md(['Quantity','Regime','Points','RMSE'],[[q,p,len(v),f'{math.sqrt(sum(x*x for x in v)/len(v)):.6g}'] for (q,p),v in phasegroups.items()])
report+='''

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

'''
curves=load('training_exposure_and_curves.json')
report+=md(['Method','First / last training loss','Clip >1 updates / 1000'],[[r['method'],f"{r['loss_first']:.6g} / {r['loss_last']:.6g}",r['clip_exceeded_updates']] for r in curves if 'updates' in r])
report+='''

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

'''
report+=md(['Block','Full-loss contribution range','Parameter gradient norm range','Projection gradient norm range'],[[b]+[f'{min(g[k] for g in final if g["block"]==b):.5g}–{max(g[k] for g in final if g["block"]==b):.5g}' for k in ('full_loss_contribution','gradient_norm','projection_gradient_norm')] for b in ('physical','time_index','fixed_conditioning','contextual')])
report+='''

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

'''
fail=[x for x in load('generation_failure_trace.json') if x['method'].startswith('coconut') and x['strict_reason']]
report+=md(['Sample','Duplicated target','Omitted targets','Additional malformed binding'],[[x['sample_id'],', '.join(x['duplicated_ids']),str(x['omitted_ids']),'; '.join('row '+str(y['row'])+': '+','.join(y['fields']) for y in x['binding_errors'])] for x in fail])
report+='''

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
'''
(ROOT/'docs/reviews/Post_P08_diagnosis.md').write_text(report)
print('Rendered Post_P08_diagnosis.md')
