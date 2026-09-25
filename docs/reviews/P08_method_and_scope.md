# P08 execution method and limits

The user authorized the revised learning pilot on 25 September 2026. This method
record accompanies the measured completion report; it does not authorize another
run. The historical proposals and P07/audit evidence remain unchanged.

## Frozen population and weighting

The selection file was written before enrichment or training. Its SHA256 is
`3d621fafc275c20ae96a020f0eaef34ad4fec1753a8db9318bdbd0ff5c5170d6`.
It names all 32 training and eight validation scenarios and their question IDs.
The original diagnostic question is included in training. The other scenarios use
seed-11 content-hash order within the existing split; question choice uses earliest
horizon then sample ID. All selected questions have T=1 s. This is a short-horizon,
single-domain selection, not a representative four-domain or OOD evaluation.

Each numerical training question contributes the first 20 recorded post-cutoff
adjacent transitions, from 0.20 through 0.60 s at 0.02-s intervals: 640 distinct
question-conditioned pairs. Each pair has weight one. A numerical update processes
all 20 chronological transitions from one question, with questions visited in
seeded shuffled cycles. The 1,000-update ceiling contains 31 complete cycles plus
eight questions in the next cycle. These exposure counts are recorded; there is
no inverse-multiplicity or equal-sequence reweighting. LR fits all 640 pairs once.
RNN hidden state persists inside a trajectory and resets between trajectories.
At autonomous inference it starts from the last permitted public observation with
zero hidden state and no earlier-history warmup, then consumes predictions and
retains hidden state. This is the existing comparator initialization policy.

The eight whole validation scenarios are excluded from training. Validation
rollouts start at the permitted 0.20-s observation and predict 40 future samples
through 1.00 s. No validation checkpoint selection or hyperparameter search is
performed. The predeclared final budget endpoint supplies each reported model.

## Unchanged forecasting and readout contract

Primary Phi-JEPA freezes Qwen, jointly trains P and the ODE, maps the 1024-wide
embedding to p of width d=140, and trains a 280-wide augmented state. The same
current p appears in input and adjacent-state target with gradients through both
copies. The complete predicted vector, including contextual and fixed-conditioning
coordinates, feeds back during autonomous rollout. RK4 uses one substep and the
external physical grid. No coordinate resetting, target detachment, altered loss,
new normalization, classification head or hidden simulator state is introduced.

The six numerical methods are primary, constant-context text-conditioned ODE,
fixed-projection least-squares LR, constant-context text-conditioned RNN,
independently retrained no_enrichment, and independently retrained numerical-only
no_text_conditioning. Their state dimensions/objectives and parameter counts are
reported separately; no exact capacity matching is claimed. No_enrichment uses
original public Q/C only for its frozen embedding. No_text_conditioning has no E,
P, p or contextual target, while retaining complete numerical conditioning.
PIN-ODE remains excluded. Original public Q/C remains available to the common
downstream answer LLM.

Named numerical predictions are kept separately from LLM answers and are the
inputs to numerical metrics. Qualified public rules supply Boolean/event readout;
unsupported results remain explicit. Public-only QA uses the same answer model
and original public information but has no forecast and deliberately unsupported
Boolean readout. Its 24 numerical components are compared separately from the
full eight-question/32-component denominator. Reversed forecasts reverse physical
measurement order while preserving the external timestamps. Perturbation sizes
are compared to the original tolerances; none are retuned. Removing an inactive
fallback is an output no-op. Removing the current partial assessment removes
metadata but does not change forecasts or answers.

## Custom T5 fitting and generation

Coconut and CODI each receive two separate fresh, seed-11 initializations of
`google/flan-t5-small` at revision
`0fc9ddf78a1e988dac52e2dac162b0ede4fd74ab`: 20 updates on the one training-only
diagnostic question, and 180 updates across the 32 training questions. Broader
training never loads the diagnostic checkpoint. Its 180 updates contain five
complete shuffled cycles plus 20 questions from the next cycle, microbatch one.

Eight latent steps, AdamW (learning rate 0.0001, weight decay zero), gradient clip
1.0, BF16 autocast with FP32 parameters, query-block attention and gradient
checkpointing are unchanged. Coconut uses explanation/typed-label CE plus 0.001
times latent smoothness. CODI uses teacher CE + student CE + 0.5 times alignment
plus 0.001 times smoothness. Raw component curves retain those distinctions.
The inherited `custom_p06.json` retains its historical two-update correctness
profile as provenance; `learning_pilot_p08.json` explicitly supplies this run's
approved 20/180 caps and 32/eight selection. The executed histories and checkpoint
update fields record the actual counts.

CODI teacher and student share one T5 backbone; their projections are separate.
The teacher projection stays at its seeded initialization, has no gradients or
optimizer membership, and is checkpointed. The teacher alignment target is
detached, but teacher CE still updates the shared backbone. Other losses can
therefore change subsequent teacher states. Alignment is teacher-forced,
post-answer, final-decoder-layer EOS-position alignment, not demonstrated transfer
of pre-answer reasoning. These are custom notebook-inspired implementations, not
official Coconut/CODI reproductions. Explanations are descriptive supervision.

Diagnostic generation occurs at updates 0/1/2/5/10/20, with separate Coconut,
CODI student and CODI teacher calls. Eval-mode teacher-forced loss is also measured
there. Broader checkpoints and training-example loss checks occur at 50/100/180;
only the final checkpoint generates on validation. The training curves label
pre-update train-mode losses separately from checkpoint eval-mode losses.

Generation is greedy with the unchanged 2,048-new-token limit. No answer repair,
target truncation or parser change is allowed. Training targets retain exact
round-trip serialization, complete EOS and padding/ignored-label rules. The new
population has its own input/target-length preflight; prior gradient/EOS/padding
tests remain applicable. Fresh validation-generation processes consume only
public preparation and checkpoints, not gold labels/explanations. Student-only
CODI is the primary condition. The separately named hybrid returns the teacher
explanation without feeding it to the student; it uses generated teacher labels
only after an observable student generation/parsing failure. Every failure remains
in the relevant denominator and both branches' costs count.

## Budgets, provenance and limits on interpretation

The shared caps are 10,800 GPU seconds, 3,600 CPU seconds, 20 billion new-artifact
bytes, 120 provider attempts, two million input tokens, 100,000 output tokens and
USD 15. Local numerical caps are 1,000 updates/600 CPU seconds per neural method,
and one fit/300 CPU seconds for LR. Custom fitting caps remain 45 GPU minutes for
Coconut and 90 for CODI; diagnostic work consumes their approved 20/180 allocation
and component caps. Shared GPU preparation/generation has 45 minutes, with ten
minutes allocated to the diagnostic generation/loss checks.

The persistent ledger reserves provider usage before dispatch and retains full
reservations when usage is unknown. An external supervisor checks compute
deadlines and artifact size. Resource accounting uses worker elapsed time for
GPU/CPU stages, including startup/checkpoint overhead, and process CPU time for
provider transport; provider waiting time is recorded separately. Historical
preparation-launch overhead is reconciled once without modifying original launch
reports. Model environments are unchanged; any plotting dependencies use a new
isolated reporting environment and count against CPU/storage allowances.
The preserved preflight test log supplies 18.012 measured seconds. Its startup
receives a separate 15-second conservative charge, and uninstrumented
selection/provenance/status bookkeeping receives a 60-second conservative charge.
Those 75 seconds are accounting reserves, not claimed runtime measurements.

The implementation base is `ba5d31d9251b58bf17c19a2f4dd9050d3109d4b6`, which already
contains the audit fixes. Each stage stores exact working-tree source/configuration
hashes and the selection identity. Provider returned model IDs are recorded; an
alias is not an immutable model revision. Usage-priced spend uses the accepted
adapter's recorded price basis, not an independently audited invoice. New pilot
code/evidence is local until separately committed or pushed; no push is part of
this task. Native checkpoints live in `/home/aashraf/phi-jepa/p08-learning-01`;
the review bundle carries content identities and pointers.

Lower training loss, valid output syntax or short-horizon success does not establish
convergence, reasoning transfer, comparative rankings or generalization. Physical
rollout errors could involve learned-dynamics error and sensitivity, but neither
large error nor a familiarity score diagnoses chaos. No perturbation experiment
is added here. Fixed reference-bank assessment remains partial/uncalibrated;
eight scenarios do not meet the minimum-20 calibration policy and missing typed
contracts are unresolved. Contact-dependent outputs, full-study claims and
production OOD clarification remain pending. The
[clarification correction and proposal](P08_clarification_correction_and_proposal.md)
preserves the prototype's actual two-call interactive demonstration.
