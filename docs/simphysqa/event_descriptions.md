# Grounded shared event descriptions — export 1.1.1

Builds on bidirectional export commit 433c64186555fdc99f17261c069a2dd4b334a11e.
Export/schema: simphysqa-associations/1.1.1. Renderer:
simphysqa-event-description/1.0.1; display convention:
decimal-six-significant-half-even/1.0.0. Source annotation contract 2.0.0 and
canonical matching rules 1.0.0 remain unchanged. This is deterministic enrichment
at the public export boundary, with no new language-model calls or simulations.

## Canonical annotation and copies

Each full known_events object preserves its original generic description and
adds event_description (text), event_description_bindings (public JSON pointers),
and event_description_status. The three new fields are copied exactly to every
states[].linked_events and between_state_associations entry for that event.
The canonical annotation is rendered once per event during projection from the
original public event and its already validated controller profile. Validation
reconstructs that annotation and rejects any altered/missing text, status or
description bindings, including a consistent forgery in all copies.

linked_states remains a compact reverse index containing only the state ID,
relationship, link ID and existing matching bindings. No entire state/event or
recursive association is embedded. Existing temporal bindings and relationships
are copied unchanged. Between-state associations retain separate ordered endpoint
IDs and gap-only relationships, never an active endpoint label.

The shared description includes declared action, direct target, relevant magnitude
or maximum limit, schedule and supported phases/application details. It never uses
observed timestamps, measurements, cutoff, private references or future states.
State-specific timing belongs only in temporal_relationship; shared text does not
say 'not yet started' or 'currently active'. A declared schedule does not establish
realized physical application, causal effects, or the end of physical effects.

## Supported semantics and explicit limitations

| Public controller profile | Description |
| --- | --- |
| additive_joint_torque | +0.5 N*m additive pulse on joint_1; separate declared base control/value/frame/schedule; no total/applied torque inference |
| brake_torque_limit | car zero-velocity braking on each axle; maximum 0.25 N*m limit, distinct from realized torque |
| force_at_center_of_mass | +x force on block_1 in the declared world frame at its instantaneous center of mass; contextual block_2 is not a target |
| support_acceleration_phases | support x-acceleration, positive then negative 0.1 s phases with individual intervals; declared stationary support afterward does not establish ended load effects |

Exact public equation recognition and typed consistency checks are inherited from
events.controller_profile. Equations are never executed. Event/frame declarations
are quoted separately from controller parameters. Arm event magnitudes have source
frame world while base torque has joint_local: retain both and mark their frame
relationship unresolved; do not convert frames or sum a total torque.

event_description_status is supported_declared_semantics or
limited_unresolved_semantics. It describes automatic semantic coverage, not human
quality or verification of realized application. Unrecognized scheduled laws get
a limited schedule/target/parameter description with explicit unresolved action,
direction, application and phases; controller equations are bound as evidence for
the unresolved law. Unknown event types retain source start/end fields without
interpreting them as an active interval or inferring intervention targets. Known
point events retain existing point-registry onset/completion semantics and readout
entities; no intervention target is assigned. Unknown declared frames remain
literal and explicitly unresolved. Never infer a vector axis from a magnitude.

## Evidence and numbers

event_description_bindings is separate from the existing temporal bindings field.
Bindings cover public event IDs/type/times/parameters and relevant controller
equations, parameters and controls. They resolve into the original public input;
no /states/ or private pointer is allowed. Known point semantics are derived from
their public type with the pinned point registry. Registry/matching version and
hashes accompany renderer provenance. Shared schedule facts naturally use some of
the same event-time pointers as matching, but their evidence arrays are distinct.

For display, scalar times and quantities use Decimal(str(source value)), rounded
to six significant digits with ROUND_HALF_EVEN, independently of ambient decimal
rounding. Drop insignificant trailing zeros, normalize signed zero and scientific
exponents. For example 0.5639000000000001 becomes 0.5639, 1.018955973527567 becomes
1.01896; 1.234565 becomes 1.23456. Unsupported nonscalar parameter values are
retained as literal JSON without interpreting them as direction or application.
Displayed numbers are rounded summaries, not matching/verification inputs.
Exact source numbers and canonical decimal phase boundaries remain untouched.
A state can be before an onset even if the displayed times round identically.

## Source recovery, validation and cache identity

strip_associations removes linked_events, linked_states, between_state_associations
and all three derived known-event description fields. Canonical JSON comparison
must recover the entire original public input, distinguishing Boolean and numeric
types. Original generic description, event definitions, source QA IDs/references,
measurement values, units/frames, observation cutoffs and inherited annotations
are unchanged. Canonical organizer QA JSONL is copied byte-for-byte.

Strict schema and deterministic semantic validation check description equality,
public evidence, canonical event identity, nonrecursive shapes, both-direction
integrity/uniqueness/agreement and exact source recovery. associated_view receives
only public data. Audit packets add private verification separately; baseline
requests contain only the public enriched view and tools=[]. Generator identity
remains in organizer-private provenance.

association_provenance/cache identity includes export version, schema and projection
hashes, renderer version/hash, display convention, public-input/link digests and
controller/point registry/matching versions/hashes. Stale versions/hashes fail.
Text source hashes normalize line endings; artifact hashes cover actual bytes.
Historical exports are retained; validating them uses their pinned historical
commit/schema. Source schema and inherited annotation_version are not relabeled.

## Execution and coverage

Use python -m simphysqa.export_associations --source <original SPQ01a root>
--output <new external root>. This CLI opts into VERSION; the original default
export APIs are unchanged. Same command validates/resumes exclusive-created
outputs without overwriting completed work. Incomplete packaging fails explicitly
and is preserved. Versioned packet IDs change; QA sample identities do not.

The 16 physical development trajectories contribute 16 descriptions: 12 with
supported declared semantics and four arm descriptions with explicit unresolved
frame relationships. Across 32 QA, 352 state-side copies retain future-only
relationships; 176 after trajectory deduplication. Existing .2 s cutoffs give no
real active or between-state coverage; labeled synthetic software fixtures test
those cases and point events. 32 packets, separate blank reviewer forms and 288
public requests are prepared; no answering evaluation or human ratings exist.
See the completion report for exact commands, saved verification and four-domain
examples. Independent human assessment and subsequent QA families remain pending.
