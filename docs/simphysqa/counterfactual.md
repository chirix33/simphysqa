# Matched omission counterfactual QA 1.0.0

This is a bounded engineering-development milestone. Record schema 0.3.0 adds
counterfactual QA while retaining 0.1.0/0.2.0 loading and accepted association
export/schema 1.1.1 unchanged. Counterfactual truth requires verified matched
simulation; a renamed predictive question or copied original answer is insufficient.

## Selection and executions

The frozen external plan selects eight of the existing sixteen SPQ01 admitted
development trajectories with Python Random(20261004). Fixed domain order;
candidates sorted by trajectory ID; two without replacement; object domain one
choice from each sorted subfamily (pre_stacked and pushing). It is an engineering
sample, not unbiased quality estimation. The selected groups remain in the existing
twenty-group fresh-formal exclusion list. No failed case is replaced.

Original qualification visits one case per domain first, then the second cases.
Each eligible pair requires original coarse/fine and omission coarse/fine: at most
32 real simulations. Every execution is reserved before process creation, serialized,
and retained, including timeout/failure. An isolated subprocess enforces 180 s per
execution and the remaining 1800 s wall budget. Resume counts prior executions and
wall time, reuses verified completed results, and never retries failed or orphaned
reservations. Failures in one domain do not stop independent qualified cases.
Exact simulator/package versions, physical scenario/configuration, source snapshots,
implementation hashes and all verification receipts are organizer-private artifacts.
`generator_commit` identifies the accepted committed base; snapshots identify the
executed modified simulator sources until the final source commit is available.

Only `omit_scheduled_intervention` changes between each matched coarse pair and
each matched fine pair. Arm omits the additional pulse; driving disables scheduled
braking; object domain omits the external push; tether removes the entire scheduled
support-motion program. Initial conditions, other controls, parameters, seeds,
assets, numerical settings, state grids and two-second horizons remain fixed.
Fine dt is one half of the stored integration dt, using the existing admission rule.

## Three distinct verification layers

1. Original replay: the repository has no explicit original-to-stored-reference
   criterion. User-confirmed `canonical-exact-replay/1.0.0` requires exact canonical saved
   states (including IDs/timestamps/steps/relations/values), full private event
   records, public prior/controller/event definitions and structured labels, with
   zero numeric tolerance. Numeric/channel differences are diagnostics, not QA
   acceptance tolerances. A separate resolved criterion file records the scientific
   decision without changing the frozen selection plan's initial proposal. The user
   confirmed this criterion before any trajectory simulation. Mismatches report first
   fields, numeric differences by quantity/unit/time, Boolean/event differences and
   configuration/environment comparison. Non-scientific runtime, creation time and
   output paths are excluded; physical fields are never excluded or changed to pass.
2. Existing coarse/fine admission: `pipeline.comparison` uses endpoint Euclidean
   errors, orientation sign-invariant quaternion angle, exact Booleans, .01 for
   m/s or rad/s and .005 for other numeric channels. Event type/order/count agree;
   onset differences <=.01+1e-10 s and terminal diagnostic Booleans agree. Full
   trajectory maximum errors are reported; passing is based on prescribed target
   endpoints/events. Driving min velocity >=-.02 m/s; tether tension >0 and length
   error <1e-6 m. Generic arm/object acceptance uses the existing semantic/finite
   source validation; it is not a newly invented physics residual.
3. Answer scoring: retain the selected source target's absolute/relative tolerance,
   frame and unit. Boolean exactness, scalar error, vector Euclidean error and
   quaternion-angle scoring remain in `simphysqa.scoring`. Software self-checks
   of scoring are not model benchmark results.

## Public projection, evidence and audit

Each qualified pair gets a new stable QA ID, a private alternative-run namespace,
and original parent/group links. One source target/time after intervention onset is
selected. Public input retains exact observed prefix/.2 s cutoff, physical prior,
controller and original known schedule; the question explicitly disables the named
event. `input.counterfactual` distinguishes the original scheduled world from the
requested omission. Accepted 1.1.1 indexes/descriptions describe that original world.
No alternative outcome, private source event, future state or verification receipt
is inserted into public language. Existing measurement language is reused, public
event language is rendered deterministically for the new task cache identity.

The private record retains the original source unchanged and the separately admitted
alternative. Question evidence binds target, terminal state, unit/frame/time and
alternative run ID; raw state IDs may coincide across worlds, so run identity is
mandatory. Validation requires passed replay, original/alternative refinement and
physics receipts, four real execution artifacts, unchanged remaining physical
inputs/settings, exact alternative reference, explicit omission, stable identity,
and the final grounded public language view. Packet export supplies auditors with
paired original/alternative references, intervention differences and verification.
Organizer annotation-provider provenance remains separate; three reviewer forms
remain blank, independent and explicitly development material. Nine-condition
public requests are prepared, never executed. Original 32 packets/288 inputs and
all prior outputs are preserved.

## Arm interpretation and coverage

MuJoCo `data.qfrc_applied[:] = joint_torque_Nm` supplies base generalized forces.
The pulse adds .5 only to coordinate zero. The declared XML maps joint_1 hinge DOF
to zero, with local axis [0,1,0]. Both controls therefore use the same scalar
generalized hinge torque coordinate. The event parameter's raw `world` frame is
the generic `quantity(..., frame="world")` default in source construction; no
Cartesian world-vector torque conversion is implemented. Preserve raw provenance
and accepted 1.1.1 descriptions. The interpretation is recorded separately rather
than rewriting source frames. Local installed `mjdata.h` confirms qfrc_applied is
generalized force, distinct from xfrc_applied Cartesian force/torque; see the
[MuJoCo 3.14 API](https://mujoco.readthedocs.io/en/3.14.0/APIreference/APItypes.html).

Scan actual admitted public release shards, not the four-record smoke frame or
private future events. Coverage counts distinguish QA records from trajectory
groups. Active, ended and gap events are absent under existing cutoffs. Separately
identified later-view proposals remain unexported; existing identities/cutoffs do
not change. Human quality, agreement, model results, explanation and clarification
QA remain pending. Counterfactual exports are generated only from qualified pairs.
