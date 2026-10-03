"""Schema, semantic, endpoint and production admission checks."""
import math
from functools import lru_cache
from .common import ROOT, read, grid_index
from phi_jepa.artifacts import canonical

@lru_cache
def validator(kind="record"):
    from jsonschema import Draft202012Validator
    schema=read(ROOT/"dataset.schema.json")
    schema["$ref"]="#/$defs/"+kind
    Draft202012Validator.check_schema(schema)
    return Draft202012Validator(schema)

def unique(values, what):
    if len(values)!=len(set(values)): raise ValueError("duplicate "+what)

def validate(record, admission=False):
    canonical(record) # rejects NaN/Infinity anywhere, including metadata
    validator().validate(record)
    inp, ref, meta=record["input"],record["reference"],record["metadata"]
    if meta["distribution"]=="structural": raise ValueError("structural OOD unsupported")
    entities=[e["entity_id"] for e in inp["entities"]]; unique(entities,"entity")
    states=inp["states"]+ref["states"]
    unique([s["state_id"] for s in states],"state ID")
    dt=meta["simulation"]["integration_timestep_s"]
    if inp["states"][0]["timestamp"]!=0 or inp["states"][0]["step_index"]!=0: raise ValueError("missing initialized time zero")
    if inp["states"][-1]["timestamp"]!=inp["observation_cutoff"]: raise ValueError("cutoff mismatch")
    last=-1
    layout=None
    for s in states:
        if s["timestamp"]<=last or grid_index(s["timestamp"],dt)!=s["step_index"]: raise ValueError("time/step inconsistency")
        last=s["timestamp"]
        keys=[(v["entity_id"],v["name"]) for v in s["measurements"]]; unique(keys,"quantity identity")
        current=sorted((v["entity_id"],v["name"],v["unit"],v["frame"],len(v["value"]) if isinstance(v["value"],list) else 1) for v in s["measurements"])
        if layout is not None and current!=layout: raise ValueError("channel/unit/frame inconsistency")
        layout=current
        for v in s["measurements"]:
            if v["entity_id"] not in entities or v["value"] is None: raise ValueError("invalid measurement")
        for rel in s["relations"]:
            if rel["subject_id"] not in entities or rel["object_id"] not in entities: raise ValueError("relation entity")
    if ref["states"][0]["timestamp"]<=inp["observation_cutoff"]: raise ValueError("future boundary")
    for e in inp["entities"]:
        unique([(p["entity_id"],p["name"]) for p in e["properties"]],"property")
        if any(p["entity_id"]!=e["entity_id"] for p in e["properties"]): raise ValueError("property owner mismatch")
    controller=inp["controller"]
    grid_index(controller["update_interval_s"],dt)
    if controller["mode"]=="explicit_schedule" and not controller["controls"]: raise ValueError("empty explicit schedule")
    if controller["mode"]=="fully_specified_feedback" and not controller["equations"]: raise ValueError("missing feedback law")
    for c in controller["controls"]:
        if c["entity_id"] not in entities or c["start_time"]>c["end_time"] or c["value"] is None: raise ValueError("invalid control")
        grid_index(c["start_time"],dt); grid_index(c["end_time"],dt)
    for p in controller["parameters"]+controller["initial_internal_state"]:
        if p["entity_id"] not in entities: raise ValueError("controller entity")
    for event in inp["known_events"]+ref["events"]:
        if event["end_time"]<event["start_time"]: raise ValueError("event interval")
        grid_index(event["start_time"],dt); grid_index(event["end_time"],dt)
        for p in event["parameters"]:
            if p["entity_id"] not in entities: raise ValueError("event entity")
    targets=inp["answer_spec"]; labels=ref["structured_label"]
    unique([t["target_id"] for t in targets],"target")
    unique([l["target_id"] for l in labels],"label")
    if {t["target_id"] for t in targets}!={l["target_id"] for l in labels}: raise ValueError("label coverage")
    for target in targets:
        if target["entity_id"] not in entities: raise ValueError("target entity")
        end=target["end_time"]; start=target["start_time"]
        if end<=inp["observation_cutoff"] or start>end: raise ValueError("target time")
        if target["query_kind"]=="at_time" and start!=end: raise ValueError("point target interval")
        if target["query_kind"]=="over_interval" and start<inp["observation_cutoff"]: raise ValueError("event target cutoff")
        label=next(l for l in labels if l["target_id"]==target["target_id"])
        if (label["unit"],label["frame"])!=(target["unit"],target["frame"]): raise ValueError("label units/frame")
        value=label["value"]; kind=target["answer_type"]
        valid={"number":type(value) in (int,float),"integer":type(value) is int,"boolean":type(value) is bool,"vector":isinstance(value,list),"category":isinstance(value,str)}[kind]
        if not valid: raise ValueError("label type")
        if target["query_kind"]=="at_time":
            terminal=next((s for s in ref["states"] if s["timestamp"]==end),None)
            if terminal is None: raise ValueError("missing target state")
            measured=next((v for v in terminal["measurements"] if (v["entity_id"],v["name"])==(target["entity_id"],target["quantity"])),None)
            if measured is None or measured["value"]!=value: raise ValueError("endpoint/label mismatch")
    from .records import answer_text
    ordered_labels=[next(l for l in labels if l["target_id"]==t["target_id"]) for t in targets]
    if ref["label"]!=answer_text(targets,ordered_labels): raise ValueError("readable answer differs from verified structured labels")
    state_ids={s["state_id"] for s in states}; event_ids={e["event_id"] for e in ref["events"]}
    for evidence in ref["evidence"]:
        if not set(evidence["state_ids"])<=state_ids or not set(evidence["event_ids"])<=event_ids: raise ValueError("invalid evidence")
    if ref["solution_trace"]["status"]=="unavailable" and (ref["solution_trace"]["steps"] or ref["solution_trace"]["verification_record"] is not None): raise ValueError("unavailable trace contains claims")
    if admission:
        sim=meta["simulation"]; checks=meta["validation"]["checks"]
        if meta["record_origin"]!="simulation" or meta["validation"]["status"]!="accepted": raise ValueError("record not admitted")
        if not checks or any(c["status"]!="pass" for c in checks): raise ValueError("unpassed admission checks")
        if not {"semantic", "refined_timestep", "domain_physics"}<={c["name"] for c in checks}: raise ValueError("missing mandatory checks")
        if any(not sim[k] for k in ("engine_version","generator_commit","config_sha256","assets","solver_settings","runtime_environment")): raise ValueError("incomplete provenance")
        for event in inp["known_events"]:
            if event["start_time"]<=ref["states"][-1]["timestamp"]:
                applied=next((e for e in ref["events"] if e["event_id"]==event["event_id"]),None)
                if applied is None or (applied["start_time"],applied["end_time"],applied["parameters"])!=(event["start_time"],event["end_time"],event["parameters"]): raise ValueError("known/applied event timing mismatch")
    return True

def validate_groups(records):
    import copy
    from phi_jepa.artifacts import digest
    ids=set(); groups={}; fingerprints={}
    for r in records:
        if r["sample_id"] in ids: raise ValueError("duplicate sample")
        ids.add(r["sample_id"])
        m=r["metadata"]; g=m["split_group_id"]
        if g in groups and groups[g]!=m["split"]: raise ValueError("cross-split group leakage")
        groups[g]=m["split"]
        facts=copy.deepcopy(r["input"])
        facts.pop("question"); facts.pop("answer_spec")
        for state in facts["states"]: state.pop("state_id")
        for event in facts["known_events"]: event.pop("event_id")
        fingerprint=digest(facts)
        if fingerprint in fingerprints and fingerprints[fingerprint]!=g: raise ValueError("duplicate physical scenario assigned to different groups")
        fingerprints[fingerprint]=g
        validate(r)
    return dict(records=len(ids),groups=len(groups))
