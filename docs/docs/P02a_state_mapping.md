# P02a candidate recorded-state mapping

24 September 2026; active contract 2.0.0-candidate.1. No layout is silently chosen.
Machine manifests include every column, collision-free tagged key, reference type,
and matching units/frames in the structure signature. They are fit from a training
public cutoff state and checked against the release; held-out truth never fits a
layout. Canonical tuple sorting determines actual column order.

| Domain | Numerical measurements per state | Plus time/index: d | p width | ODE width |
|---|---|---:|---:|---:|
| Arm | joint_1/2 angle and angular_velocity; tip position xyz: 7 | 9 | 9 | 18 |
| Driving | car position xyz, orientation xyzw, velocity xyz, angular_velocity xyz; forward_position, forward_velocity; wheel_0..3 angle/angular_velocity: 23 | 25 | 25 | 50 |
| Objects | block_1/2 position xyz, orientation xyzw, velocity xyz, angular_velocity xyz: 26 | 28 | 28 | 56 |
| Tether | load position xyz, swing_angle, angular_velocity; support position xyz and velocity xyz: 11 | 13 | 13 | 26 |

Position/velocity use m and m/s; angular quantities rad and rad/s; quaternion
orientation uses unit 1 and preserved xyzw components. World frame applies except
arm joints and driving wheels (joint_local). Timestamp is seconds; step_index is
the recorded integration index (integer reference, continuous prediction). Actual
stored intervals are audited rather than reconstructed from a guessed index rate.
state_id and context remain strings. All Boolean measurements remain validated
categorical fields outside numeric loss. Contact relations can vary in count and
are validated as subject_id/predicate/object_id string triples, not numerical slots.

State-plus-fixed-conditioning appends every numeric leaf from public input except
the complete `states` history. This includes entities/model properties, controller,
known_events, observation_cutoff and answer_spec (query times/tolerances). Ordinary
numeric arrays preserve indices; entities and measurements use semantic IDs.
Strings containing embedded XML/URDF numbers are still strings, not parsed numbers.

| Domain | State d | Appended fixed numeric fields | Combined d / p width | ODE width |
|---|---:|---:|---:|---:|
| Arm | 9 | 168 | 177 | 354 |
| Driving | 25 | 81 | 106 | 212 |
| Objects | 28 | 58 | 86 | 172 |
| Tether | 13 | 127 | 140 | 280 |

The old whole-input registry widths are export artifacts, not state dimensions.
Neither candidate drops public Q/C: both retain full model parameters, controls,
scheduled future interventions and observed history in the frozen embedding input.
In the combined candidate the fixed numeric coordinates repeat on each reference
side; autonomous inference still carries their predicted values, without clamping.

## Observability and nonnumeric outcomes

Arm has joint position/velocity and known torque/model parameters. Tether records
its reduced angle/angular velocity plus support motion; do not add an unrecorded
load linear velocity. Driving records car and wheel positions/velocities but not
all engine contact/solver state. Objects record both rigid-body poses and velocities
but not contact force history or all stability dwell-time state. Thus recorded
states are useful supervised observations, not proven exact Markov states of the
numerical engines. Public history provides context; no simulator-internal variable
is silently added. Predictive adequacy is a later empirical diagnostic.

Boolean targets: arm joint_limit_by_T; driving stopped_by_T; objects stable_stack,
support_lost, left_table; tether boundary_crossed. Some describe event history or
dwell time and cannot safely be inferred from a terminal numerical state alone.
Reference events are evaluator-only; known scheduled public events remain context.
Options presented for review: explicit unsupported Boolean answers in a numeric
first predictor, or a separately specified event/Boolean mechanism in a later
phase. No Boolean-to-number casting or new head is approved here.

## Source selection and ambiguity

P02a uses admitted recorded simulator JSON from the frozen local release. The
original extracted-JSON schema/prompts and export adapters remain intact; no live
extraction or assumed equivalence to this per-state layout is claimed. Future
extraction must explicitly bind quantities, times and observed history to an
accepted layout and fail on absent data. Never complete it from private future.

Earlier training pairs would require re-rendering context to end at each pair's
start; they are not enabled. Forecast-window pairs use history only through 0.2s,
then recorded adjacent futures. Overlapping 1s/2s question windows preserve Q and
answer_spec differences; physical duplicate counts and proposed inverse-frequency
weights are audited separately from question-conditioned pair counts.

## User scope decision — 24 September 2026

The user selected **state plus fixed conditioning**. Active d and p widths are
arm 177, driving 106, objects 86, tether 140; ODE widths are 354/212/172/280.

The state-only mapping remains a documented comparison candidate, not an active
choice. Public-only LLM enrichment, separately recorded, is also user-approved.
The user selected a separate Boolean/event mechanism proposal for a later phase.

## Enrichment implementation boundary

The selected later E input includes Q/C plus separately recorded public-only LLM
notes. Original public facts remain immutable; answers and private explanations
are forbidden. `context_mode=enriched` fails on missing enrichment. P02a audit
uses the explicitly named `public_base_for_offline_audit` mode and makes no live
call; its context character lengths are base-context measurements, not enriched
lengths or tokenizer counts. Provider/model/prompt/cache budgets and actual output
validation belong to the next separately authorized interface phase.

Boolean/event update (24 September 2026): the user selected a separate mechanism
proposal for later review. No Boolean casting, new head or objective is implemented
here. See `docs/docs/P02a_boolean_event_proposal.md` from the repository root.
