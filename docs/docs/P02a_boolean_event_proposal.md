# Separate Boolean/event mechanism — proposal for later review

24 September 2026. The user selected a separate Boolean/event mechanism before
full-answer evaluation. This is a proposal, not an approved extra loss/head or an
implemented autonomous Boolean predictor. Booleans remain outside numerical MSE.

Proposed interface: `assess_outcomes(public_problem, physical_rollout,
rule_manifest) -> typed_outcomes | stage_failure`. Inputs are public answer_spec,
known controls/events, and named predicted numerical states at physical times.
No reference state, reference event, metadata label, simulator physics module or
gold answer is available. Each outcome carries target_id, Boolean or explicit
unsupported status, evidence time interval, rule/version hash and sampling limits.
Keep these results separate from numerical predictions and later LLM prose.

First review deterministic, disclosed public-rule bindings for outcomes expressible
from available predicted coordinates: left_table from predicted object position
and public footprint; boundary crossing from predicted load position and public
hysteresis; joint-limit occurrence from predicted joint angle history and public
thresholds. Stopped-by-time needs the exact public speed/dwell rule. These are
candidate discrete-time approximations, not a claim to reconstruct events between
saved timestamps. A 20ms prediction grid can miss a brief event; qualification
must compare against evaluator truth and report temporal resolution failures.

Stable_stack and support_lost additionally depend on contact force/contact history
and dwell-time bookkeeping not fully present in the selected numerical state.
Do not invent those variables or substitute proximity for supporting force.
Return `unsupported_missing_contact_history` until a later reviewed mechanism
addresses it. Categorical observed relations may initialize public history only;
private future relations cannot be fed into autonomous inference.

Later experimental options, requiring an explicit decision before implementation:

1. A separate learned temporal outcome predictor using recorded event/Boolean
   supervision, with its own objective and ablation outside the accepted numerical
   ODE loss. This needs model/head, supervision and calibration choices.
2. A frozen public-only answer model consuming named predicted trajectories and
   public rules, with typed output and independent evaluator checks. This avoids
   a new trained head but does not establish reliable event inference or recover
   unobserved contact state; refusals/unsupported outcomes remain explicit.

Recommend starting the next proposal with the deterministic supported subset and
an explicit unsupported inventory, then choosing and budgeting a separate method
for the remaining targets. Do not label partial Boolean coverage as full-answer
qualification. No method is added, trained, downloaded or called in P02a.
