"""Deterministic declared event links. The only data argument is public input.

No equation evaluation, simulator calls, interpolation, or private-event lookups.
Exact decimal representations of supplied times implement half-open intervals.
"""
from copy import deepcopy
from decimal import Decimal
from hashlib import sha256
from pathlib import Path
from .dataset import pointer
from .io import canonical, digest

RULE_VERSION = "simphysqa-event-links/1.0.0"
# These are declared laws, not executable formulas. Unknown laws stay unresolved.
LAWS = {
    "additive_joint_torque": "tau_1=tau_2=joint_torque_Nm; add +0.5 N*m to joint_1 during the scheduled pulse; viscous damping=0.05 N*m*s/rad.",
    "brake_torque_limit": "After onset, each axle uses a zero-velocity brake with maximum torque 0.25 N*m; PyBullet VELOCITY_CONTROL targetVelocity=0 opposes wheel motion. Braking remains engaged through T.",
    "force_at_center_of_mass": "Apply +x force to block_1 at its instantaneous center of mass for 0.1 s; no force outside event.",
    "support_acceleration_phases": "support x=0,v=0 until event onset; +a for 0.1s then -a for 0.1s, then stationary; continuous analytic position and velocity.",
}
# Simulator-defined instantaneous events, including completion-time semantics.
# A point event is never an active interval, even at its declared timestamp.
POINTS = {
    "joint_limit_contact": "joint-limit contact onset (rearmed below 2.795 rad)",
    "boundary_crossing": "positive-x boundary crossing (0.005 m hysteresis)",
    "stopped": "earliest end of a qualifying continuous 0.2 s stopped interval",
    "support_contact": "support contact onset above 0.01 N (aggregate contact points)",
}

def dec(value):
    if type(value) not in (int, float):
        raise ValueError("event time must be a finite number")
    result = Decimal(str(value))
    if not result.is_finite():
        raise ValueError("nonfinite event time")
    return result

def signatures():
    return {"matching_rules_version": RULE_VERSION,
            "matching_rules_sha256": sha256(Path(__file__).read_text(encoding="utf-8").encode()).hexdigest(),
            "controller_registry_sha256": digest(LAWS), "point_registry_sha256": digest(POINTS)}

def controller_profile(inp, event, event_index):
    controller = inp["controller"]
    equations = controller["equations"]
    base = f"/known_events/{event_index}"
    ep = event["parameters"]
    profile = {"kind": "unresolved_declared_law", "claims": [], "phases": [],
               "bindings": ["/controller/mode", "/controller/description"]}
    # Never infer direction/application/phase from a generic magnitude alone.
    if event["type"] != "scheduled_intervention" or len(ep) != 1:
        return profile
    mag = ep[0]
    params = controller["parameters"]
    def param(entity, name, unit):
        hits = [(i, p) for i, p in enumerate(params)
                if (p["entity_id"], p["name"], p["unit"]) == (entity, name, unit)]
        if len(hits) != 1:
            raise ValueError("recognized controller needs one declared parameter")
        i, p = hits[0]
        return p, f"/controller/parameters/{i}"
    def match(kind, entity, unit):
        return LAWS[kind] in equations and mag["entity_id"] == entity and mag["unit"] == unit
    def law(kind):
        profile["kind"] = kind
        eq = f"/controller/equations/{equations.index(LAWS[kind])}"
        profile["bindings"].extend([eq, base + "/parameters/0"])
        return eq
    def claim(text, bindings):
        profile["claims"].append({"text": text, "bindings": sorted(set(bindings))})
    if match("additive_joint_torque", "joint_1", "N*m"):
        if mag["value"] != 0.5:
            raise ValueError("joint pulse magnitude contradicts declared law")
        eq = law("additive_joint_torque")
        claim("The declared pulse adds +0.5 N*m to joint_1; this is additive control, not total or verified applied torque.", [eq, base + "/parameters/0"])
        for i, control in enumerate(controller["controls"]):
            if control["entity_id"] == "joint_1" and control["channel"] == "applied_torque":
                path = f"/controller/controls/{i}"
                profile["bindings"].append(path)
                claim(f'Declared base torque for joint_1 is {control["value"]} {control["unit"]} in {control["frame"]}, scheduled [{control["start_time"]}, {control["end_time"]}) s; event magnitude retains its source frame {mag["frame"]}.', [eq, path, base + "/parameters/0"])
    elif match("brake_torque_limit", "car", "N*m"):
        p, path = param("car", "brake_torque_limit", "N*m")
        if p["value"] != 0.25 or mag["value"] != p["value"]:
            raise ValueError("brake limit contradicts declared law/event")
        eq = law("brake_torque_limit")
        profile["bindings"].append(path)
        claim(f'The declared controller schedules a zero-velocity brake on each axle with maximum torque limit {p["value"]} {p["unit"]} (parameter frame {p["frame"]}); realized applied torque is not specified by this limit.', [eq, path, base + "/parameters/0"])
    elif match("force_at_center_of_mass", "block_1", "N"):
        p, path = param("block_1", "force", "N")
        if p["value"] != mag["value"] or p["frame"] != "world":
            raise ValueError("push parameter contradicts declared event/frame")
        if abs(dec(event["end_time"]) - dec(event["start_time"]) - Decimal("0.1")) > Decimal("1e-12"):
            raise ValueError("push event duration contradicts declared 0.1 s law")
        eq = law("force_at_center_of_mass")
        profile["bindings"].append(path)
        claim(f'The declared controller schedules +x force {p["value"]} {p["unit"]} in {p["frame"]} at block_1\'s instantaneous center of mass; block_1 is the intervention target.', [eq, path, base + "/parameters/0"])
    elif match("support_acceleration_phases", "support", "m/s^2"):
        p, path = param("support", "acceleration", "m/s^2")
        if p["value"] != mag["value"] or type(p["value"]) not in (int, float) or p["value"] <= 0:
            raise ValueError("support acceleration contradicts declared event")
        start, end = dec(event["start_time"]), dec(event["end_time"])
        # Duration tolerance only verifies the law; it is NEVER used for active matching.
        if abs(end - start - Decimal("0.2")) > Decimal("1e-12"):
            raise ValueError("support event duration contradicts declared two 0.1 s phases")
        eq = law("support_acceleration_phases")
        profile["bindings"].append(path)
        bounds = [base + "/start_time", base + "/end_time", eq, path, base + "/parameters/0"]
        for index, sign in enumerate((1, -1)):
            profile["phases"].append({"phase_id": event["event_id"] + f"/phase-{index + 1}",
                "start_time": event["start_time"] if index == 0 else float(start + Decimal("0.1")),
                "end_time": float(start + Decimal("0.1")) if index == 0 else event["end_time"],
                "start_time_decimal": str(start if index == 0 else start + Decimal("0.1")),
                "end_time_decimal": str(start + Decimal("0.1") if index == 0 else end),
                "target_entity_ids": ["support"], "quantity": "acceleration", "value": sign * p["value"],
                "unit": p["unit"], "frame": p["frame"],
                "derivation": "declared +a for 0.1 s then -a for 0.1 s; second onset = event onset + 0.1 s",
                "bindings": sorted(set(bounds))})
        phases = profile["phases"]
        claim(f'The declared support acceleration has positive phase +{p["value"]} {p["unit"]} on [{phases[0]["start_time_decimal"]}, {phases[0]["end_time_decimal"]}) s, then negative phase {-p["value"]} {p["unit"]} on [{phases[1]["start_time_decimal"]}, {phases[1]["end_time_decimal"]}) s (frame {p["frame"]}); the declared support is then stationary, without implying that load motion has ended.', bounds)
    profile["bindings"] = sorted(set(profile["bindings"]))
    return profile

def derive(inp):
    """Link every public known event against the WHOLE saved public state."""
    states = inp["states"]
    entities = inp["entities"]
    ids = [e["entity_id"] for e in entities]
    if len(ids) != len(set(ids)) or len({s["state_id"] for s in states}) != len(states):
        raise ValueError("duplicate entity/state identity")
    if not states or any(dec(s["timestamp"]) > dec(inp["observation_cutoff"]) for s in states):
        raise ValueError("states outside public cutoff")
    if any(dec(a["timestamp"]) >= dec(b["timestamp"]) for a, b in zip(states, states[1:])):
        raise ValueError("saved times must be strictly increasing")
    events = inp["known_events"]
    if len({e["event_id"] for e in events}) != len(events):
        raise ValueError("duplicate event identity")
    descriptors, links, between = [], [], []
    for j, event in enumerate(events):
        start, end = dec(event["start_time"]), dec(event["end_time"])
        if end < start:
            raise ValueError("event ends before onset")
        base = f"/known_events/{j}"
        scoped = sorted({p["entity_id"] for p in event["parameters"]})
        if not set(scoped) <= set(ids):
            raise ValueError("event entity missing from public declarations")
        semantics = ("half_open_interval" if event["type"] == "scheduled_intervention" else
                     "declared_point" if event["type"] in POINTS and start == end else "unresolved")
        if event["type"] in POINTS and start != end:
            raise ValueError("point event has nonzero duration")
        targets = scoped if semantics == "half_open_interval" else []
        profile = controller_profile(inp, event, j)
        event_bindings = [base + "/" + key for key in ("event_id", "start_time", "end_time", "type", "description")]
        event_bindings += [base + f"/parameters/{k}" for k in range(len(event["parameters"]))]
        # Context entities are declarations/readouts, NEVER additional intervention targets.
        contextual = sorted(set(ids) - set(targets))
        descriptor = {"event_id": event["event_id"], "type": event["type"], "start_time": event["start_time"],
            "end_time": event["end_time"], "temporal_semantics": semantics,
            "point_definition": POINTS.get(event["type"]), "target_entity_ids": targets,
            "event_entity_ids": scoped, "contextual_entity_ids": contextual,
            "context_note": "declared scene entities, not claims of intervention application or effects",
            "bindings": sorted(event_bindings), "controller": profile}
        descriptors.append(descriptor)
        for i, state in enumerate(states):
            time = dec(state["timestamp"])
            if semantics == "half_open_interval":
                relationship = "scheduled_future" if time < start else "scheduled_active" if time < end else "scheduled_interval_ended"
                if start == end:
                    relationship = "scheduled_future" if time < start else "scheduled_empty_interval"
            elif semantics == "declared_point":
                relationship = "declared_point_future" if time < start else "declared_point_at_timestamp" if time == start else "declared_point_past"
            else:
                relationship = "temporal_semantics_unresolved"
            bindings = event_bindings + [f"/states/{i}/state_id", f"/states/{i}/timestamp"]
            entity_matches, measurement_matches, relation_matches, controller_matches = [], [], [], []
            # Scan all measurements/relations, independent of the language focal quantity.
            for k, entity in enumerate(entities):
                if entity["entity_id"] in scoped:
                    entity_matches.append(f"/entities/{k}")
            for k, measurement in enumerate(state["measurements"]):
                if measurement["entity_id"] in scoped:
                    measurement_matches.append(f"/states/{i}/measurements/{k}")
            for k, relation in enumerate(state["relations"]):
                if relation["subject_id"] in scoped or relation["object_id"] in scoped:
                    relation_matches.append(f"/states/{i}/relations/{k}")
            for group in ("parameters", "controls", "initial_internal_state"):
                for k, value in enumerate(inp["controller"][group]):
                    if value["entity_id"] in scoped:
                        controller_matches.append(f"/controller/{group}/{k}")
            phase = next((p["phase_id"] for p in profile["phases"] if
                          Decimal(p["start_time_decimal"]) <= time < Decimal(p["end_time_decimal"])), None) if relationship == "scheduled_active" else None
            link = {"link_id": f'{state["state_id"]}/{event["event_id"]}', "state_id": state["state_id"],
                "timestamp": state["timestamp"], "event_id": event["event_id"],
                "target_entity_ids": targets, "contextual_entity_ids": contextual,
                "temporal_relationship": relationship, "scheduled_phase_id": phase,
                "entity_matches": entity_matches, "measurement_matches": measurement_matches,
                "relation_matches": relation_matches, "controller_matches": controller_matches,
                "bindings": sorted(set(bindings + entity_matches + measurement_matches + relation_matches + controller_matches + profile["bindings"]))}
            links.append(link)
            if i == 0 or semantics == "unresolved":
                continue
            previous = states[i - 1]
            left = dec(previous["timestamp"])
            boundaries = []
            candidates = [("onset", start)] if semantics == "declared_point" else [("onset", start), ("end", end)]
            candidates += [("phase_boundary", Decimal(p["start_time_decimal"])) for p in profile["phases"][1:]]
            for kind, at in candidates:
                if left < at < time:
                    boundaries.append({"kind": kind, "timestamp": float(at), "timestamp_decimal": str(at),
                                       "sampled_state": False})
            interval_overlap = semantics == "half_open_interval" and start < end and max(left, start) < min(time, end)
            if boundaries or interval_overlap:
                between.append({"link_id": previous["state_id"] + "/" + link["link_id"],
                    "previous_state_id": previous["state_id"], "state_id": state["state_id"],
                    "event_id": event["event_id"], "target_entity_ids": targets,
                    "temporal_relationship": "interval_between_saved_states" if interval_overlap else "point_between_saved_states",
                    "entire_interval_between": semantics == "half_open_interval" and left < start and end < time,
                    "scheduled_overlap": [float(max(left, start)), float(min(time, end))] if interval_overlap else None,
                    "boundaries": boundaries,
                    "endpoint_relationship": relationship,
                    "bindings": sorted(set(link["bindings"] + [f"/states/{i - 1}/state_id", f"/states/{i - 1}/timestamp"]))})
    result = {**signatures(), "observation_cutoff": inp["observation_cutoff"],
              "events": descriptors, "state_links": links, "between_state_links": between}
    for value in descriptors + links + between:
        for binding in value["bindings"]:
            pointer(inp, binding)
    return result
