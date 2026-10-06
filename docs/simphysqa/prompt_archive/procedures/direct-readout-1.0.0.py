"""Deterministic observed-state QA construction, with original source lineage intact."""
from copy import deepcopy
from .annotation import FOCAL
from .dataset import restore, validate
from .io import digest

def build_direct(predictive):
    validate(predictive)
    source=restore(predictive)
    inp=source["input"]
    state=inp["states"][-1]
    entity,quantity=FOCAL[inp["domain"]]
    measurement=next(m for m in state["measurements"] if (m["entity_id"],m["name"])==(entity,quantity))
    target_id=entity+":"+quantity
    target={"target_id":target_id,"entity_id":entity,"quantity":quantity,
        "answer_type":"vector" if isinstance(measurement["value"],list) else "boolean" if type(measurement["value"])is bool else "number",
        "unit":measurement["unit"],"frame":measurement["frame"],"query_kind":"at_time",
        "start_time":state["timestamp"],"end_time":state["timestamp"],"rule_id":"observed_readout_v1",
        "rule_definition":"Read the named measurement in the observed public source state at the specified timestamp.",
        "absolute_tolerance":0.,"relative_tolerance":0.}
    identity={"version":"direct-readout/1.0.0","source_sample_id":source["sample_id"],"state_id":state["state_id"],"target_id":target_id}
    result=deepcopy(predictive)
    result["sample_id"]="spq-direct-"+digest(identity)[:24]
    result["schema_version"]="simphysqa/0.2.0"
    result["question_type"]="direct"
    result["public"]["input"]["task_type"]="observed_state_readout"
    result["public"]["input"]["question"]=f'At observed timestamp {state["timestamp"]:.6g} s, what is {entity} {quantity} in {measurement["unit"]} (frame {measurement["frame"]})?'
    result["public"]["input"]["answer_spec"]=[target]
    label={"target_id":target_id,"value":deepcopy(measurement["value"]),"unit":measurement["unit"],"frame":measurement["frame"]}
    evidence_id="spq-observed-"+digest(identity)[:24]
    result["private"]["reference"]={"states":[deepcopy(state)],"events":[],"structured_label":[label],
        "label":f'{target_id} at {state["timestamp"]:.6g} s = {measurement["value"]} {measurement["unit"]}; frame {measurement["frame"]}.',
        "explanation":"The answer is copied deterministically from the named observed measurement; no causal claim.",
        "explanation_kind":"descriptive","evidence":[{"evidence_id":evidence_id,"state_ids":[state["state_id"]],"event_ids":[],
            "description":"Observed public measurement readout."}],"solution_trace":{"status":"unavailable","steps":[],"verification_record":None}}
    result["private"]["evidence_bindings"]=[{"target_id":target_id,"kind":"observed_readout","state_ids":[state["state_id"]],
        "event_ids":[],"evidence_ids":[evidence_id]}]
    result["private"]["source_record"]=deepcopy(source)
    result["private"]["derivation"]=identity
    result["completion"]["direct_qa"]="deterministically_verified_observed_readout"
    result["completion"]["predictive_qa"]="not_applicable_this_item_source_predictive_preserved"
    validate(result)
    return result

def validate_direct(record,source):
    inp=record["public"]["input"]
    expected=deepcopy(source["input"])
    for key in ("task_type","question","answer_spec"):
        expected[key]=inp[key]
    if expected!=inp or inp["task_type"]!="observed_state_readout":
        raise ValueError("direct_QA_changed_source_facts")
    identity=record["private"].get("derivation")
    if identity is None or identity["source_sample_id"]!=source["sample_id"] or record["sample_id"]!="spq-direct-"+digest(identity)[:24]:
        raise ValueError("direct_QA_lineage_identity_mismatch")
    targets=inp["answer_spec"]
    if record["schema_version"] != "simphysqa/0.2.0" or identity["version"] != "direct-readout/1.0.0":
        raise ValueError("direct_schema_or_adapter_version_mismatch")
    if len(targets)!=1:
        raise ValueError("one_direct_readout_required")
    target=targets[0]
    if target["rule_id"] != "observed_readout_v1" or target["query_kind"] != "at_time" or target["absolute_tolerance"] != 0 or target["relative_tolerance"] != 0:
        raise ValueError("direct_readout_contract_mismatch")
    state=next((s for s in source["input"]["states"] if s["state_id"]==identity["state_id"]),None)
    if state is None or state["timestamp"]!=target["end_time"] or target["start_time"]!=state["timestamp"] or state["timestamp"]>inp["observation_cutoff"]:
        raise ValueError("direct_target_not_observed")
    measured=next(m for m in state["measurements"] if (m["entity_id"],m["name"])==(target["entity_id"],target["quantity"]))
    label=record["private"]["reference"]["structured_label"]
    if label!=[{"target_id":target["target_id"],"value":measured["value"],"unit":measured["unit"],"frame":measured["frame"]}]:
        raise ValueError("direct_reference_not_exact_source_measurement")
    if (target["unit"],target["frame"])!=(measured["unit"],measured["frame"]) or identity["target_id"]!=target["target_id"]:
        raise ValueError("direct_unit_frame_target_mismatch")
    ref=record["private"]["reference"]
    expected_label=f'{target["target_id"]} at {state["timestamp"]:.6g} s = {measured["value"]} {measured["unit"]}; frame {measured["frame"]}.'
    if ref["states"]!=[state] or ref["events"] or ref["label"]!=expected_label:
        raise ValueError("direct_reference_evidence_or_text_changed")
    if record["private"]["metadata"]!=source["metadata"]:
        raise ValueError("direct_simulation_provenance_changed")
