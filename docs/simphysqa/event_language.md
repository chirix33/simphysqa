# Public event-language contract 2.0.0 — SPQ01a

Use `python -m simphysqa.spq01a --help`,
`configs/simphysqa/annotation_spq01a.json`, `events.py`, `event_language.py`
and `event_language.schema.json`. This extends the SPQ01 public annotations;
the physical source schema, predictive/direct wrappers and QA contracts stay exact.
Every annotation remains generated_unreviewed. This is annotation enrichment,
not explanation or counterfactual QA, and adds no human approval software gate.

## Public boundary and matching

`derive(input)` and `generator_input(input)` receive only public input. They read
observed states, all measurements/relations, entity declarations, known_events
and declared controller information. They never receive private reference events,
future states, solutions, answers or verification metadata. The full-state scan
is independent of the focal measurement selected for language. Whole public
controller/entity definitions and derived links are available to the deterministic
annotation generator and versioned future generator projection.

All state links explicitly carry state_id, event_id, direct target_entity_ids,
contextual_entity_ids, temporal_relationship, phase ID when applicable, match
pointers and supporting source bindings. Pointers resolve into original public
input; derived links do not pretend to be original measured data. Context entities
are scene declarations, never additional intervention targets or affected-entity
claims. Point-event readout entities have event_entity_ids but no intervention
target assignment.

For `scheduled_intervention`, compare the exact decimal representation of the
supplied numbers: timestamp < onset is scheduled_future; onset <= timestamp < end
is scheduled_active; timestamp >= end is scheduled_interval_ended. No epsilon,
rounding, nearest-state assignment or interpolated state. Empty intervals are
explicitly empty and never active. Every overlapping event gets its own link.

Between each consecutive pair of saved states, report nonempty scheduled interval
overlap and strictly interior onset/end/phase boundaries separately. Boundaries
coincident with saved states are not labeled unsampled. An interval wholly inside
the gap can exist with neither endpoint active. No new state IDs are generated.
Derived phase bounds retain decimal strings as well as numerical display values;
phase matching uses the strings to avoid rounding across a boundary.

The versioned point registry retains existing simulator semantics: joint_limit_contact
is an onset (rearmed below 2.795 rad); boundary_crossing is a positive-x crossing
with .005 m hysteresis; support_contact is onset above .01 N aggregate force;
stopped is the earliest *end* of a qualifying continuous .2 s stopped interval.
These have start=end and use declared_point_future/at_timestamp/past, never active
intervals. The registry traces to retained simulation/engines.py and bullet.py;
only publicly supplied events are processed. Unknown types remain explicitly
temporal_semantics_unresolved. Do not infer a duration or apply the interval rule
to an unknown type. Other event/controller definitions need explicit versioned
semantics before broader language support.

## Controller and language claims

Controller recognition uses exact known public equation strings plus typed event/
parameter checks. Strings are never executed. Unrecognized laws have unresolved
application semantics; timing links remain usable but no direction or phases are
guessed from magnitude. Inconsistencies in recognized laws fail explicitly.

| Domain | Declared semantics retained |
| --- | --- |
| Arm | +.5 N*m additive pulse on joint_1; base control and its interval/frame are separate; no total/applied-torque claim |
| Driving | Zero-velocity brake on each axle with .25 N*m maximum torque limit; limit is not realized applied torque |
| Pushing/stacking | +x force at block_1 instantaneous center of mass; block_2 readout is contextual, not the pushed target |
| Tethered load | Support acceleration +a for declared .1 s, then -a for .1 s; derive boundary as onset+.1, verify event duration; support stationary afterward is a declaration, not proof of load effects ending |

Arm source event magnitude has frame world while base control has joint_local;
retain and identify both source declarations. Do not silently normalize frames,
equate those quantities, or synthesize a realized total torque.

Reuse original meaningful measurement text verbatim. Each sentence now has explicit
claims: measurement, event_schedule, controller_definition, controller_phase or
between_saved_states. Each claim has its own text, bindings, stable claim ID and
link IDs where relevant; sentence text concatenates claims and bindings are their
union. Controller law statements bind equations/parameters, schedule statements
bind event times/targets and observed timestamps, measurement statements retain
their original evidence. Derived phases bind both the .1 s law and event/parameter
fields, with an explicit derivation.

The trajectory summary describes declared future interventions once; final observed
timestamps briefly say they have not yet started. Earlier future-only timestamps
retain measurement language without repeating the schedule. At a scheduled-active
state, measurement and relevant declared intervention/phase are described together
but bound separately. Intervening links are separate claims. The first ended state
notes only that the interval ended, explicitly leaving physical effects unresolved.
No timing statement establishes application or causation.

## Validation, identity and provenance

Strict revised annotation schema plus deterministic reconstruction validates the
final exported view. The original measurement component still passes the SPQ01
numeric/unit/frame/timestamp/unsupported-claim checks. Reconstruct all added claims,
links and text from public input and require exact equality, rejecting altered
claims, unsupported pointers, changed links, stale versions, missing timestamps and
future outcomes. This is automatic software validation, not human acceptability.

Cache identity includes contract/prompt/rule versions, their content hashes,
controller/point registries, renderer/schema hashes, the entire public generator
projection and original annotation digest. Old outputs cannot satisfy the revised
contract by retaining an old cache key. Text source hashes normalize line endings
for cross-platform source checkouts; artifact manifests hash actual file bytes.
Keep pinned code/schema revisions when validating a historical annotation version.

Original provider model/settings/attempt provenance is retained verbatim in private
storage. Separate event_enrichment provenance records deterministic method, versions,
source record/annotation hash and zero new requests/attempts/spend. Reviewer packets
and baseline views have no organizer model identity. All source QA records and
private numerical/Boolean references remain unchanged.

`spq01a` prints resolved non-secret configuration, 16 physical inputs/input sizes,
32 QA count, zero request/budget estimate and cumulative accounting before writing
items. Durable exclusive-created items and exports verify exact content on resume;
completed work is never overwritten. Tampering/version changes fail explicitly.
Incomplete packet packaging is detected by the missing ready manifest and preserved
for recovery; no automatic deletion or fallback. No credentials/network are needed.
The original shared budget remains 16 initial /32 attempts /USD5; prior estimated
spend $.522767, new spend $0, remaining $4.477233. It is a token estimate, not a
confirmed invoice. New live generation is disabled by this milestone configuration.

## Real coverage and pending research

The 16 original engineering trajectories have 176 saved states, 16 declared events
and 176 future-only state/event links after physical-pair deduplication. Each domain
has four trajectories /44 states /four future events. There are zero real active,
ended or between-state links in these .2 s observation windows. Tethered controllers
contribute eight declared phases; none overlaps saved observations. All 32 QA
packets carry revised language; nine conditions receive 288 prepared requests and
zero executed answering-model calls.

Boundary/active/ended/overlap/phase/point behavior is tested with clearly labeled
synthetic software fixtures, not empirical physical examples. Broader real observed
event overlap remains a development coverage gap; do not change these cutoffs to
manufacture coverage. Future milestones may select other existing admitted views.

Independent reviewer judgments remain absent. Calibration/rubric revision, the
alternative-source model/protocol, counterfactual matched-intervention truth,
causal explanation support and genuine clarification gaps remain subsequent work.
No formal sample or additional QA family is exported here.
