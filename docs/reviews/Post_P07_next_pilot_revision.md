# Post-audit addendum to the proposed next pilot — not authorized or launched

25 September 2026. Preserve [the original proposal](P07_next_budget_proposal.md)
as historical evidence. No training, generation, provider call or dataset change
was performed to prepare this addendum.

The source/checkpoint audit found functioning gradient and optimizer paths but
zero valid generated custom answers after two updates. It also found that raw
primary MSE is dominated by step index and that a hold-last physical diagnostic
outperforms this primary checkpoint on the one short validation trajectory. These
findings justify better diagnostics within the proposed budget, not an objective,
architecture, tolerance, normalization or state-coordinate change.

## Training-only custom fitting diagnostic, explicitly budgeted

Use the existing training question `08930dbcfe8a3c2273ebd024c397ff39`, scenario
`6dcead753b8ad615a772be98d0c8906f`, original public/enriched input and existing
descriptive explanation/typed-label targets. Its entire scenario remains outside
validation. Use a new directory and **fresh** pinned `google/flan-t5-small`
revision `0fc9ddf78a1e988dac52e2dac162b0ede4fd74ab`, seed 11, existing eight latent
steps, fixed seeded teacher projection, and unchanged optimizer/objective settings
from `configs/custom_p06.json`. No saved two-update checkpoint is overwritten.
Teacher/student share T5 within CODI; Coconut and CODI remain separate models.

Allocate **20 optimizer updates per custom method**, microbatch one, on this one
training question. Hard training caps: 10 GPU minutes Coconut and 15 GPU minutes
CODI including teacher work, stopping at the first limit. This is an explicit
future diagnostic, not an assertion that 20 updates suffice. Preserve every loss
component, pre-clipping gradient norm, fixed-teacher-projection check, parameter
change, update number, runtime and peak memory. Save read-only learning curves
from all recorded updates. Report pre-update losses as such; do not label them
losses of the next checkpoint. Use an eval-mode teacher-forced loss pass at each
milestone to separate dropout variability from generation behavior.

At updates **0, 1, 2, 5, 10 and 20** (only reached milestones), run public-input-only
generation on that same training question using the existing greedy 2,048-new-token
limit. Generate Coconut, CODI student and CODI teacher separately: at most **18
unique calls and 36,864 new tokens** total. Count teacher work and derive the hybrid
from those outputs without extra calls. Reserve **10 of the original 45 shared GPU
minutes** for these generation/loss diagnostics. If the time cap prevents a
milestone, mark it unmeasured; do not extend limits or truncate targets. Original
EOS/round-trip/padding audits remain applicable; new selected examples need length
preflight. Preserve signs, units, decimals, vectors and Boolean types with the
existing reversible codec and parser; no generated-answer repair.

For every milestone/condition, report:

- Training-only complete-answer accuracy and correct typed targets / all four
  eligible targets; invalid cases contribute zero success, not missing rows.
- Valid typed-output rate, EOS termination, token-cap termination, generated
  length, parse-failure reason, teacher fallback attempts and recoveries.
- Coconut CE/smoothness and CODI teacher CE/student CE/alignment/smoothness curves
  separately; shared-backbone and projection/latent update diagnostics.
- Measured runtime, memory and total student/teacher inference work.

Interpretation: successful fitting supports learnability of this tiny supervised
example and correct execution, **not held-out generalization, reasoning transfer or
convergence**. Decreasing teacher-forced loss with invalid generation signals an
unresolved training/generation or optimization issue; it does not prove additional
updates will fix it. Failure to fit motivates a separately reviewed diagnosis;
there is no automatic budget extension or mandatory target-accuracy acceptance
gate. The shared teacher target can evolve through other losses even though its
alignment branch is detached.

## Accounting and unchanged broader proposal

The diagnostic **uses**, rather than adds to, the original 200-update allowance
per custom method: 20 diagnostic updates plus at most **180 broader-pilot updates
from a separate fresh initialization**, not a one-question-warmed checkpoint.
Diagnostic time is included in the original 45-minute Coconut / 90-minute CODI
caps, leaving at most 35 / 75 minutes for broader fitting. Unspent diagnostic
allowance is not silently reassigned. Broader learning curves use reached updates
50/100/180; report the final predeclared budget endpoint, with no validation-based
hyperparameter selection. Repeated one-question diagnostic training is kept
separate from the broader training population/weights.

Keep the original 32 training / eight validation scenario proposal, 640 equal
question-conditioned transitions, seed 11, six numerical methods, original loss,
full feedback, solver and provider controls. Freeze exact IDs before an authorized
run. Include the existing diagnostic training scenario among the 32 training
scenarios and select the other 31 deterministically; the eight validation
scenarios remain disjoint. No extra data generation or paid fitting diagnostic.
Aggregate caps remain **three GPU hours, one CPU hour, 20 GB new artifacts**;
provider caps remain 120 attempts, 2,000,000 input tokens, 100,000 output tokens
and USD 15, stopping at any limit. This audit grants no execution authorization.

Add coordinate-group MSE, named physical trajectory/endpoint errors and hold-last
physical diagnostics to the existing numerical evaluation budget. Use shared
supported numerical targets for public-only comparisons; report the Boolean-policy
difference separately. Before interpreting reversal controls, report perturbation
size / existing tolerance and effective/no-op status per target. Do not select new
thresholds, discard easy cases or secretly replace this control after seeing
results. The current reversed changes are below each numerical tolerance, so
unchanged binary success is weak evidence about answer reliance on forecasts.

Do not expand the pilot for chaos studies, contact mechanisms, OOD clarification,
typed-contract authoring or calibration. Eight validation scenarios still cannot
satisfy the existing minimum-20 calibration policy, and missing typed contracts
still make assessment partial. Full four-domain training, independent calibration,
multiple seeds, sealed ID/OOD evaluation and causal/clarification evidence remain
separate future work.
