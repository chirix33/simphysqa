"""Versioned bidirectional projection of canonical SPQ01a public links.

Original organizer records stay lossless. Only exported public inputs acquire
compact association indexes; no semantic matching rule or language is changed.
"""
from copy import deepcopy
from hashlib import sha256
from pathlib import Path
from jsonschema import Draft202012Validator
from .events import derive
from .event_descriptions import FIELDS, render, versions as description_versions
from .io import canonical, digest, read

VERSION = "simphysqa-associations/1.1.1"

def versions():
    return {**description_versions(), "export_version": VERSION,
        "association_schema_sha256": sha256(Path(__file__).with_name("association.schema.json").read_text(encoding="utf-8").encode()).hexdigest(),
        "association_implementation_sha256": sha256(Path(__file__).read_text(encoding="utf-8").encode()).hexdigest()}

def strip_associations(inp):
    original = deepcopy(inp)
    original.pop("between_state_associations")
    for state in original["states"]:
        state.pop("linked_events")
    for event in original["known_events"]:
        event.pop("linked_states")
        for field in FIELDS:
            event.pop(field)
    return original

def _project(inp, canonical_links):
    if any(field in e for e in inp["known_events"] for field in FIELDS) or "between_state_associations" in inp or any("linked_events" in s for s in inp["states"]) or any("linked_states" in e for e in inp["known_events"]):
        raise ValueError("association projection needs original unindexed public input")
    result = deepcopy(inp)
    states = {s["state_id"]: s for s in result["states"]}
    events = {e["event_id"]: e for e in result["known_events"]}
    for state in states.values():
        state["linked_events"] = []
    descriptions = {}
    for j, event in enumerate(result["known_events"]):
        event["linked_states"] = []
        descriptions[event["event_id"]] = render(inp, canonical_links["events"][j], j)
        event.update(deepcopy(descriptions[event["event_id"]]))
    # Both indexes come from the SAME canonical link, never separate matching.
    for link in canonical_links["state_links"]:
        state = states[link["state_id"]]
        event = events[link["event_id"]]
        common = {"temporal_relationship": link["temporal_relationship"],
                  "link_id": link["link_id"], "bindings": deepcopy(link["bindings"])}
        state["linked_events"].append({"event_id": event["event_id"], "event_type": event["type"],
            "target_entity_ids": deepcopy(link["target_entity_ids"]), **deepcopy(common), **deepcopy(descriptions[event["event_id"]])})
        event["linked_states"].append({"state_id": state["state_id"], **deepcopy(common)})
    # These associations are intervals/points in a GAP, never endpoint-active.
    result["between_state_associations"] = []
    for link in canonical_links["between_state_links"]:
        result["between_state_associations"].append({
            "endpoint_state_ids": [link["previous_state_id"], link["state_id"]],
            "event_id": link["event_id"], "event_type": events[link["event_id"]]["type"],
            **deepcopy(descriptions[link["event_id"]]),
            **{k: deepcopy(link[k]) for k in ("link_id", "temporal_relationship", "target_entity_ids",
                "bindings", "entire_interval_between", "scheduled_overlap", "boundaries")}})
    return result

def validate_input(inp, canonical_links, exported):
    """Check integrity/uniqueness/mirrors AND exact agreement with canonical links."""
    if canonical(canonical_links) != canonical(derive(inp)):
        raise ValueError("canonical SPQ01a links do not match their original public input")
    Draft202012Validator(read(Path(__file__).with_name("association.schema.json"))).validate(exported)
    if canonical(strip_associations(exported)) != canonical(inp):
        raise ValueError("association export changed source physical input")
    states = {s["state_id"]: s for s in exported["states"]}
    events = {e["event_id"]: e for e in exported["known_events"]}
    for j, event in enumerate(exported["known_events"]):
        expected = render(inp, canonical_links["events"][j], j)
        if canonical({field: event[field] for field in FIELDS}) != canonical(expected):
            raise ValueError("noncanonical event description or description bindings")
    for entry in [entry for state in exported["states"] for entry in state["linked_events"]] + exported["between_state_associations"]:
        if entry["event_id"] in events and canonical({field: entry[field] for field in FIELDS}) != canonical({field: events[entry["event_id"]][field] for field in FIELDS}):
            raise ValueError("event description copy/bindings disagreement")
    forward, reverse, link_ids = {}, {}, set()
    for state in exported["states"]:
        for entry in state["linked_events"]:
            key = (state["state_id"], entry["event_id"])
            if entry["event_id"] not in events:
                raise ValueError("dangling event association")
            if key in forward or entry["link_id"] in link_ids:
                raise ValueError("duplicate state-event association/link identity")
            if entry["event_type"] != events[entry["event_id"]]["type"]:
                raise ValueError("association event type mismatch")
            forward[key] = {k: entry[k] for k in ("link_id", "temporal_relationship", "bindings")}
            link_ids.add(entry["link_id"])
    for event in exported["known_events"]:
        for entry in event["linked_states"]:
            key = (entry["state_id"], event["event_id"])
            if entry["state_id"] not in states:
                raise ValueError("dangling state association")
            if key in reverse:
                raise ValueError("duplicate event-state association")
            reverse[key] = {k: entry[k] for k in ("link_id", "temporal_relationship", "bindings")}
    if forward != reverse:
        raise ValueError("bidirectional association disagreement")
    positions = {s["state_id"]: i for i, s in enumerate(exported["states"])}
    for entry in exported["between_state_associations"]:
        left, right = entry["endpoint_state_ids"]
        if left not in states or right not in states or positions[right] != positions[left] + 1:
            raise ValueError("between-state association needs consecutive endpoint IDs")
        if entry["event_id"] not in events:
            raise ValueError("dangling between-state event")
        if entry["link_id"] in link_ids:
            raise ValueError("duplicate between-state link identity")
        link_ids.add(entry["link_id"])
    if canonical(exported) != canonical(_project(inp, canonical_links)):
        raise ValueError("associations differ from canonical SPQ01a links")

def associated_view(original):
    if "export_version" in original or "association_provenance" in original:
        raise ValueError("already indexed public view; use original records to resume")
    if "event_context" not in original["annotations"]:
        raise ValueError("bidirectional export requires validated SPQ01a canonical links")
    links = original["annotations"]["event_context"]["links"]
    result = deepcopy(original)
    result["input"] = _project(original["input"], links)
    result["export_version"] = VERSION
    result["association_provenance"] = {**versions(), "source_public_input_sha256": digest(original["input"]),
                                       "canonical_links_sha256": digest(links)}
    validate_view(original, result)
    return result

def validate_view(original, exported):
    if set(exported) != set(original) | {"export_version", "association_provenance"}:
        raise ValueError("unexpected derived public view fields")
    links = original["annotations"]["event_context"]["links"]
    expected_meta = {**versions(), "source_public_input_sha256": digest(original["input"]), "canonical_links_sha256": digest(links)}
    if exported["export_version"] != VERSION or exported["association_provenance"] != expected_meta:
        raise ValueError("derived export version/hash/provenance mismatch")
    for key in set(original) - {"input"}:
        if canonical(exported[key]) != canonical(original[key]):
            raise ValueError("derived export changed public QA or language: " + key)
    validate_input(original["input"], links, exported["input"])
