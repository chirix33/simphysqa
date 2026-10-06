# Bidirectional public associations 1.0.1

This is a derived export/schema extension to SPQ01a event-language 2.0.0. It changes
neither source records nor canonical temporal matching or language annotations.
Use `python -m simphysqa.export_associations --help`. The new public-view envelope
has export_version=simphysqa-associations/1.0.1 and association_provenance containing
schema/implementation hashes, original public-input digest and canonical-link digest.
The source wrapper schema and annotation_version retain their original values.

## Representation

Every exported input.states object adds linked_events, including an empty array
when there are no known events. Each entry contains only event_id, event_type,
temporal_relationship, target_entity_ids, the existing canonical link_id and
existing public evidence bindings. Every input.known_events object retains all
original definition fields and adds linked_states: compact state_id,
temporal_relationship, link_id and matching bindings. No whole state is embedded
in an event, and no full event (or event containing linked_states) is embedded in
a state. Compact entries have strict schemas rejecting recursive/extra fields.

Both arrays come from the same annotations.event_context.links.state_links entry. The source event's type becomes
event_type in the compact state-side entry. Relationships are copied verbatim,
including half-open interval active/future/ended/empty, point future/at/past, and
unresolved semantics. Target IDs remain canonical direct intervention targets;
point readout/context entities are never promoted to intervention targets.

Between-state entries live only in input.between_state_associations, derived from
the existing between_state_links. Each has ordered endpoint_state_ids=[previous,
current], event_id/type, canonical link_id, target IDs, existing bindings, interval
overlap, unsampled boundaries and entire-interval-between flag. Relationships are
strictly interval_between_saved_states or point_between_saved_states. Such an
entry is not an additional endpoint-active link and omits the canonical auxiliary
endpoint_relationship field. Endpoint state links independently retain their actual
canonical timestamp relationship. No saved state is invented at a boundary.

Original canonical links remain available in annotations, including supported
controller phase IDs/definitions. This projection does not recompute phases,
nearest-state matches, controller application or causation.

## Validation and source boundary

association.schema.json validates compact entry shapes and between-state labels.
The source loader validates original QA/physical/annotation contracts first.
Semantic validation checks all endpoint/event/state IDs resolve; each pair and
canonical link ID is unique; both directions agree on relationship, link ID and
bindings; between-state endpoint IDs are consecutive and ordered; all indexes
exactly reproduce canonical SPQ01a links. Even two consistently forged directions
are rejected when they disagree with canonical links. Canonical links themselves
are checked against the unchanged public-only SPQ01a derivation.

Removing only linked_events, linked_states and between_state_associations must
recover the complete original public input exactly, including JSON Boolean/number
types (false and 0 must not compare equal). Annotation text/evidence,
sample IDs, question type/specification, units, frames, measurements and cutoffs
are unchanged. Projection receives a public view only; no private evidence is
used to construct it. Auditors retain private QA verification in their packets;
baseline requests contain only the derived public view and tools=[].

## Entry points and compatibility

Use public_record(record, association_version=VERSION), where VERSION is imported
from simphysqa.associations, for the new projection. audit.export_packets and
evaluation.request/export_requests accept the same keyword. Omitting the keyword
preserves historical export behavior so old jobs and their saved outputs can still
validate/resume. The dedicated new CLI consistently enables VERSION for every
public item, audit packet and baseline request.

Version/hash metadata accompanies public views, packets and manifests. Packet IDs
include the export version, preventing old/new reviewer forms from sharing packet
identities; original QA sample IDs do not change. Source organizer records remain
canonical and are copied byte-for-byte into the new external export. New files are
exclusive-created; resume verifies exact content and manifest hashes without
overwriting completed outputs. Incomplete packet packaging is preserved and fails
explicitly, consistent with the original SPQ01a policy.

## Coverage

The existing 32 development QA views contain 352 forward and 352 reverse entries
(176 physical pairs after deduplication); all are scheduled_future. Each source
window still ends at .2 s. Real active/ended/intervening coverage remains absent.
Synthetic software fixtures exercise active boundaries, gaps, point completion,
overlap, phases, empty events and unknown semantics. These are not new simulated
physical data, model outcomes or human annotation-quality judgments. No simulations
or model calls are performed; human ratings remain pending.

## Grounded description extension (supersedes the export version above)
[Export 1.1.1](event_descriptions.md) retains these canonical relationships and
adds shared event_description, event_description_bindings and semantic status
fields. Historical 1.0.1 exports remain pinned to their commit/schema.
