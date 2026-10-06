"""SPQ04: genuine query ambiguity, saved witnesses, no simulation/provider calls."""
from copy import deepcopy
from hashlib import sha256
from pathlib import Path
import math
from jsonschema import Draft202012Validator
from .io import ROOT, canonical, digest, read
from .dataset import restore, pointer
from .answer_annotations import roots as parent_roots, binding, readout, display, control_text
from .associations import VERSION as ASSOCIATIONS, associated_view, strip_associations
from .scoring import distance

VERSION = "saved-witness-clarification/1.0.0"
PARTIAL = "simphysqa-partial-input/1.0.0"
RECORD = "simphysqa-clarification/1.0.0"
SLOTS = ("execution_condition", "entity_id", "readout_time")
SCENARIO_KEYS = ("domain", "entities", "global_context", "coordinate_convention", "controller", "known_events", "states", "observation_cutoff")


def versions():
    return {"procedure": VERSION, "partial_input": PARTIAL, "associations": ASSOCIATIONS,
        "implementation_sha256": sha256(Path(__file__).read_text(encoding="utf-8").encode()).hexdigest(),
        "evaluation_sha256": sha256(Path(__file__).with_name("clarification_evaluation.py").read_text(encoding="utf-8").encode()).hexdigest(),
        "schema_sha256": digest(read(Path(__file__).with_name("clarification.schema.json"))),
        "rubric_sha256": digest(read(ROOT/"configs/simphysqa/clarification_rubric.json"))}


def response_schema():
    # Same schema across gaps; no selected completion, reference question or gold value.
    return {"type": "object", "additionalProperties": False,
        "required": ["response_kind", "requested_information", "clarification_question"],
        "properties": {"response_kind": {"const": "clarify"},
            "requested_information": {"enum": list(SLOTS)},
            "clarification_question": {"type": "string", "minLength": 1}}}


def disjoint(a, b, t1, t2):
    """Scorer acceptance regions, not merely mutual rejection of point answers."""
    for key in ("answer_type", "quantity", "unit", "frame", "absolute_tolerance", "relative_tolerance"):
        if canonical(t1[key]) != canonical(t2[key]):
            raise ValueError("witness scoring semantics differ")
    error, _, unit = distance(a, b, t2)
    if t1["answer_type"] == "boolean":
        return {"qualified": type(a) is bool and type(b) is bool and a != b,
            "metric": "Boolean inequality", "separation": None, "radii": [0, 0], "metric_unit": "1"}
    if t1["answer_type"] not in ("number", "integer", "vector"):
        raise ValueError("unsupported acceptance geometry; no guessed threshold")
    orientation = t1["quantity"] == "orientation" and t1["answer_type"] == "vector"
    def radius(value, target):
        magnitude = 1. if orientation else math.sqrt(sum(v*v for v in value)) if isinstance(value, list) else abs(value)
        return target["absolute_tolerance"] + target["relative_tolerance"]*magnitude
    radii = [radius(a,t1), radius(b,t2)]
    # Quaternion scorer is the SO(3) geodesic metric modulo sign and norm; triangle
    # inequality gives the same sufficient disjoint-ball certificate in radians.
    return {"qualified": error > sum(radii), "metric": "sign_invariant_rotation_angle" if orientation else "Euclidean" if isinstance(a,list) else "absolute",
        "separation": error, "radii": radii, "required_strictly_greater_than": sum(radii), "metric_unit": unit}


def roots(record):
    e = record["private"]["clarification_evidence"]; p = e["parent_record"]
    root = parent_roots(p, p["private"]["answer_annotation"]["evidence_context"])
    root.update(initial=record["public"]["input"], resolved=record["private"]["resolved_view"]["input"], gap=e["selection"])
    for key, value in e["saved_fine_results"].items():
        root[key] = value
    return root


def select(parent):
    """Frozen groups, original target first, then sorted source targets; no replacement."""
    root = parent_roots(parent,parent["private"]["answer_annotation"]["evidence_context"])
    source = root["factual"]; targets = source["input"]["answer_spec"]
    selected = parent["public"]["input"]["answer_spec"][0]
    ordered = [selected] + [t for t in sorted(targets,key=lambda t:t["target_id"]) if t != selected]
    attempts = []
    def candidate(slot, ts, ns, values):
        outcomes = [readout(root,n,t,root["pair"]["original_run_id"] if n=="factual" else root["pair"]["alternative_run_id"])[0]["value"] for t,n in zip(ts,ns)]
        check = disjoint(*outcomes,*ts)
        attempts.append({"ambiguity_type":slot,"targets":deepcopy(ts),"namespaces":ns,"completion_values":values,"certificate":check})
        return {"ambiguity_type":slot,"targets":deepcopy(ts),"namespaces":ns,"completion_values":values,"certificate":check,"candidates":deepcopy(attempts)} if check["qualified"] else None
    for t in ordered:
        result = candidate("execution_condition",[t,t],["factual","alternative"],["scheduled","omitted"])
        if result:return result
    # Existing pre-stacked source has two admitted same-unit position targets.
    if source["input"]["domain"] == "object_pushing_stacking":
        positions = sorted((t for t in targets if t["quantity"]=="position"),key=lambda t:t["entity_id"])
        if len(positions)==2:
            result = candidate("entity_id",positions,["factual","factual"],[t["entity_id"] for t in positions])
            if result:return result
    # New query times, not new physics: saved 0.4/1.0 readouts. Both future to .2 s.
    # Readout validity at the additional endpoint is checked against saved fine
    # results and the EXISTING admission thresholds during construction below.
    if source["input"]["domain"] == "tethered_load":
        t = next(t for t in targets if t["quantity"]=="position")
        early = deepcopy(t);early.update(start_time=.4,end_time=.4)
        result = candidate("readout_time",[early,t],["factual","factual"],[.4,t["end_time"]])
        if result:return result
    return {"status":"failed","reason":"No supported disjoint witness found under declared bounded candidate rules", "candidates":attempts}


def fine_evidence(parent, selection, runs):
    """Read saved executions only; no engine import or solve. Extra-time qualification."""
    if selection["ambiguity_type"] != "readout_time":return {}, []
    root = parent_roots(parent,parent["private"]["answer_annotation"]["evidence_context"])
    run_id = root["pair"]["pair_id"]+"-original-fine"
    path = Path(runs)/"executions"/run_id/"result.json"
    raw = path.read_bytes(); fine = read(path)
    if sha256(raw).hexdigest() != root["context"]["runs"]["original-fine"]["result_file_sha256"] or fine["status"] != "completed":
        raise ValueError("saved fine result integrity failure")
    checks=[]
    for t in selection["targets"]:
        a,_,_=readout(root,"factual",t,root["pair"]["original_run_id"])
        states=fine["rollout"]["states"];i,s=next((i,s) for i,s in enumerate(states) if s["timestamp"]==t["end_time"])
        j,m=next((j,m) for j,m in enumerate(s["measurements"]) if (m["entity_id"],m["name"])==(t["entity_id"],t["quantity"]))
        if (m["unit"],m["frame"])!=(t["unit"],t["frame"]):raise ValueError("fine metadata differs")
        tol=0. if type(a["value"]) is bool else .01 if t["unit"] in ("m/s","rad/s") else .005
        check_target={**t,"absolute_tolerance":tol,"relative_tolerance":0.}
        error,passed,unit=distance(a["value"],m["value"],check_target)
        if not passed:raise ValueError("additional saved endpoint fails existing refinement threshold")
        checks.append({"target":deepcopy(t),"error":error,"tolerance":tol,"unit":unit,"passed":passed,
            "fine_run_id":run_id,"result_file_sha256":sha256(raw).hexdigest(),
            "fine_state_pointer":f"/rollout/states/{i}/measurements/{j}","state_id":s["state_id"],
            "method":"offline_saved_readout_check; thresholds from accepted pipeline.comparison, not answer scoring"})
    return {"factual_fine":fine},checks


def initial(parent, selection, sample_id):
    p=deepcopy(parent["public"]["input"])
    p={k:p[k] for k in SCENARIO_KEYS}  # Discard old question, answer_spec, counterfactual IDs/text.
    t=deepcopy(selection["targets"][0]);t["target_id"]="clarified-target"
    query={k:deepcopy(v) for k,v in t.items() if k not in ("start_time","end_time")}
    slot=selection["ambiguity_type"]
    if slot=="entity_id":query.pop("entity_id")
    if slot!="readout_time":query["timestamp"]=t["end_time"]
    if slot!="execution_condition":query["execution_condition"]="scheduled"
    entity=t["entity_id"] if slot!="entity_id" else "the intended block"
    when=f'at {display(t["end_time"])} s' if slot!="readout_time" else "at the intended future readout time"
    suffix={"execution_condition":"The requested condition has not been specified: the declared scheduled intervention may be retained or omitted; all other scenario and execution settings stay fixed.",
        "entity_id":"The requested block has not been specified: block_1 or block_2.",
        "readout_time":"The requested future readout time has not been specified."}[slot]
    p.update(task_type="clarification_state_readout",question=f'What is {entity} {t["quantity"]} {when} ({t["unit"]}, frame {t["frame"]})? '+suffix,
        query=query,partial_input_contract=PARTIAL,
        scenario_role="Base scheduled scenario; declared controls and schedule do not select an unspecified query condition. Observed prefix is common to both matched conditions.",
        interaction={"stage":1,"behavior":"Request one focused clarification before supplying a unique answer.","response_schema":response_schema()})
    view={"schema_version":RECORD,"sample_id":sample_id,"question_type":"clarification", "annotation_version":parent["annotation_version"],
        "input":p,"annotations":deepcopy(parent["public"]["annotations"])}
    return associated_view(view)


def erase_resolution(view, slot):
    """Remove all stage-2 query resolution and derived text to recover initial view."""
    out=deepcopy(view);inp=out["input"]
    inp.pop("answer_spec",None);inp.pop("recorded_reply",None)
    key={"execution_condition":"execution_condition","entity_id":"entity_id","readout_time":"timestamp"}[slot]
    inp["query"].pop(key,None)
    # These two values are deterministic derived wording, not additional evidence.
    inp.pop("resolved_question",None);inp["interaction"]= {"stage":1,"behavior":"Request one focused clarification before supplying a unique answer.","response_schema":response_schema()}
    out["association_provenance"]["source_public_input_sha256"]=digest(strip_associations(inp))
    return out


def completed_view(initial_view, selection, index):
    out=deepcopy(initial_view);inp=out["input"];slot=selection["ambiguity_type"]
    value=selection["completion_values"][index];target=deepcopy(selection["targets"][index]);target["target_id"]="clarified-target"
    key={"execution_condition":"execution_condition","entity_id":"entity_id","readout_time":"timestamp"}[slot]
    reply_text={"execution_condition": "Use the condition with the scheduled intervention "+("retained." if value=="scheduled" else "omitted; retain all other controls and conditions."),
        "entity_id":f'Use {value}.',"readout_time":f'Use the readout at {display(value) if type(value) in (int,float) else value} s.'}[slot]
    inp["query"][key]=value;inp["answer_spec"]=[target]
    inp["recorded_reply"]={"requested_information":slot,"value":value,"text":reply_text,"origin":"recorded_task_author_reply_not_model_response"}
    condition=inp["query"]["execution_condition"]
    inp["resolved_question"]=(f'In the {condition} condition, what is {target["entity_id"]} {target["quantity"]} at {display(target["end_time"])} s ({target["unit"]}, frame {target["frame"]})?')
    inp["interaction"]={"stage":2,"behavior":"Answer the resolved question with typed value and concise evidence-supported explanation; no private outcomes are supplied.",
        "response_schema":{"type":"object","additionalProperties":False,"required":["targets","explanation"],"properties":{
            "targets":{"type":"array","minItems":1,"maxItems":1,"items":{"type":"object","additionalProperties":False,"required":["target_id","value","unit","frame"],"properties":{
                "target_id":{"const":"clarified-target"},"value":{"type":"boolean"} if target["answer_type"]=="boolean" else {"type":"array","minItems":4 if target["quantity"]=="orientation" else 3,"maxItems":4 if target["quantity"]=="orientation" else 3,"items":{"type":"number"}} if target["answer_type"]=="vector" else {"type":"number"},"unit":{"const":target["unit"]},"frame":{"const":target["frame"]}}}},"explanation":{"type":"string","minLength":1}}}}
    out["association_provenance"]["source_public_input_sha256"]=digest(strip_associations(inp))
    return out


def reference(record):
    root=roots(record);sel=root["gap"];slot=sel["ambiguity_type"]
    witnesses=[]
    for i,(ns,t) in enumerate(zip(sel["namespaces"],sel["targets"])):
        run=root["pair"]["original_run_id"] if ns=="factual" else root["pair"]["alternative_run_id"]
        m,b,sid=readout(root,ns,t,run)
        witnesses.append({"completion_value":sel["completion_values"][i],"namespace":ns,"run_id":run,"target":deepcopy(t),"answer":m,"state_id":sid,"bindings":b})
    target=record["private"]["resolved_view"]["input"]["answer_spec"][0];w=witnesses[1]
    cert=sel["certificate"];claims=[]
    def claim(kind,text,bs):
        c={"kind":kind,"text":text,"bindings":bs};c["claim_id"]="CLC-"+digest(c)[:16];claims.append(c)
    gap_b=[binding(root,"initial","/query"),binding(root,"gap","/completion_values")]
    both=witnesses[0]["bindings"]+witnesses[1]["bindings"]+[binding(root,"gap","/certificate")]
    claim("information_gap",f'The initial question does not determine {slot}; both private completions agree with the complete initial scenario, language and query.',gap_b)
    difference=("The Boolean answers differ." if target["answer_type"]=="boolean" else f'The witness separation is {display(cert["separation"])} {cert["metric_unit"]}, strictly greater than the sum of acceptance radii {display(sum(cert["radii"]))}. Their answer regions are disjoint under the unchanged scorer.')
    claim("underdetermination",difference,both)
    claim("reply_resolution",f'The recorded reply supplies only {slot}: {sel["completion_values"][1]}. This selects one requested readout without disclosing its answer.',[binding(root,"resolved","/recorded_reply"),binding(root,"resolved","/answer_spec/0")])
    inp=root["factual"]["input"];omission=w["namespace"]=="alternative"
    # Detailed implementation, including raw arm metadata distinction, remains in trace.
    text=control_text(inp,omission).split(" Implementation applies",1)[0]
    if not omission:text += " The requested entity/time is now fixed by the query and reply."
    controls=[binding(root,"factual","/input/controller"),binding(root,"factual","/input/known_events"),binding(root,"pair","/intervention_change")]
    claim("effective_conditions",text,controls+[binding(root,"resolved","/query")])
    claim("resolved_answer",f'{target["entity_id"]} {target["quantity"]} at {display(target["end_time"])} s is {display(w["answer"]["value"])} {target["unit"]} ({target["frame"]}), read from the selected saved {w["namespace"]} run.',w["bindings"]+[binding(root,"resolved","/answer_spec/0")])
    if target["answer_type"]=="boolean":
        claim("predicate_rule",target["rule_definition"]+" Use the saved flag and event history; an endpoint measurement alone cannot establish a duration predicate.",w["bindings"]+[binding(root,w["namespace"],"/reference/events",run_id=w["run_id"]),binding(root,"resolved","/answer_spec/0")])
    claim("interpretation_limit","The reply resolves the requested condition, entity or time; it does not discover a missing physical mechanism. These verified simulator readouts do not establish real-world causality or human explanation quality.",[binding(root,"context","/verification")]+both)
    questions={"execution_condition":"Should the scheduled intervention be retained or omitted for this question?", "entity_id":"Which block should I report, block_1 or block_2?", "readout_time":"At what time should I report the load position?"}
    steps=[]
    for c in claims:
        steps.append({"step":len(steps)+1,"kind":c["kind"],"text":c["text"],"supports_claim_ids":[c["claim_id"]],"bindings":deepcopy(c["bindings"])})
    method=[binding(root,"context","/method"),binding(root,"context","/runs"),binding(root,"context","/implementation")]
    if inp["domain"]=="robotic_arm":method.append(binding(root,"context","/arm_interpretation"))
    steps.insert(4,{"step":0,"kind":"saved_numerical_procedure","text":"Use the saved execution configuration, simulator method and implementation; no new solve or analytical derivation was performed. Raw source controller/frame metadata stays unchanged; arm generalized-hinge interpretation is separate saved implementation evidence.","supports_claim_ids":[],"bindings":method})
    checks=record["private"]["clarification_evidence"]["additional_readout_checks"]
    verification=[binding(root,"pair","/verification"),binding(root,"context","/verification")]
    if checks:
        verification.append(binding(root,"gap","/additional_readout_checks"))
        for check in checks:verification.append(binding(root,"factual_fine",check["fine_state_pointer"],run_id=check["fine_run_id"],state_id=check["state_id"]))
    for i,s in enumerate(steps,1):s["step"]=i
    trace={"version":VERSION,"status":"evidence_checked_human_unreviewed","steps":steps,
        "verification_record":{"status":"saved_exact_replay_and_separate_admissions_passed", "bindings":verification,
            "additional_readout_checks":checks,"new_simulations":0,"human_explanation_assessment":"uncollected"}}
    return {"label":"Resolved answer: "+display(w["answer"]["value"])+" "+target["unit"],
        "structured_label":[{"target_id":"clarified-target", "entity_id":target["entity_id"],"quantity":target["quantity"],"value":deepcopy(w["answer"]["value"]),"unit":target["unit"],"frame":target["frame"],"timestamp":target["end_time"]}],
        "reference_clarification_question":questions[slot], "reference_question_origin":"authored_reference_not_executed_model_response",
        "acceptable_equivalents":"Any single focused question that requests the missing slot; exact wording is not required. Compound or answer-leaking questions require human review.",
        "witnesses":witnesses,"claims":claims,"explanation":" ".join(c["text"] for c in claims if c["kind"] in ("reply_resolution","effective_conditions","resolved_answer","predicate_rule","interpretation_limit")),
        "explanation_kind":"resolved_saved_witness_readout","solution_trace":trace,"verification_record":trace["verification_record"]}


def construct(parent, selection, fine):
    sel=deepcopy(selection);saved,checks=fine
    sel["additional_readout_checks"]=checks
    sample_id="spq-clarification-"+digest({"version":VERSION,"group":parent["trajectory_id"],"gap":sel["ambiguity_type"]})[:24]
    view=initial(parent,sel,sample_id);resolved=completed_view(view,sel,1)
    record={"schema_version":RECORD,"source_schema_version":parent["source_schema_version"],"sample_id":sample_id,"trajectory_id":parent["trajectory_id"],
        "question_type":"clarification","annotation_version":parent["annotation_version"],"source":deepcopy(parent["source"]),
        "public":{"input":view["input"],"annotations":view["annotations"]},
        "private":{"source_record":restore(parent),"metadata":deepcopy(parent["private"]["metadata"]),"annotation_provenance":deepcopy(parent["private"]["annotation_provenance"]),
            "evidence_bindings":deepcopy(parent["private"]["evidence_bindings"]),"initial_view":view,"resolved_view":resolved,
            "clarification_evidence":{"parent_sample_id":parent["sample_id"],"parent_record_sha256":digest(parent),"parent_record":deepcopy(parent),"selection":sel,"saved_fine_results":saved,"additional_readout_checks":checks},
            "clarification_annotation":{"version":VERSION,"versions":versions(),"cache_identity":digest({"parent":parent,"selection":sel,"fine":saved,"versions":versions()}),"generation":"deterministic_no_model_request","status":"evidence_checked_human_unreviewed"}},
        "completion":{**deepcopy(parent["completion"]),"clarification_qa":"constructed_disjoint_witness_human_unreviewed"}}
    record["private"]["reference"]=reference(record)
    return record


def build(parent, runs):
    from .dataset import validate
    validate(parent)
    if parent["question_type"]!="counterfactual" or parent["private"]["answer_annotation"]["version"]!="simphysqa-answer-annotation/1.0.3":raise ValueError("requires accepted paired parent")
    sel=select(parent)
    if sel.get("status")=="failed":return None,sel
    out=construct(parent,sel,fine_evidence(parent,sel,runs));validate_clarification(out)
    return out,sel


def validate_clarification(record):
    from .dataset import validate
    canonical(record)
    Draft202012Validator(read(Path(__file__).with_name("clarification.schema.json"))).validate(record)
    e=record["private"]["clarification_evidence"];p=e["parent_record"];validate(p)
    expected_sel=select(p)
    if expected_sel.get("status")=="failed":raise ValueError("unqualified witnesses")
    s=deepcopy(e["selection"]);s.pop("additional_readout_checks")
    if canonical(s)!=canonical(expected_sel):raise ValueError("candidate selection or scorer certificate changed")
    if canonical(record)!=canonical(construct(p,s,(e["saved_fine_results"],e["additional_readout_checks"]))):raise ValueError("clarification content differs from deterministic construction")
    root=roots(record);cutoff=root["initial"]["observation_cutoff"]
    for ns in ("factual","alternative"):
        prefix=root[ns]["input"]["states"]
        # Input/reference differ only in generic context strings; scientific prefix must agree.
        for a,b in zip(root["initial"]["states"],prefix):
            for field in ("state_id","timestamp","step_index","measurements","relations"):
                if canonical(a[field])!=canonical(b[field]):raise ValueError("prefix not common to witnesses")
        if len(prefix)!=len(root["initial"]["states"]):raise ValueError("prefix length differs")
    view=record["private"]["initial_view"];slot=s["ambiguity_type"]
    missing={"execution_condition":"execution_condition","entity_id":"entity_id","readout_time":"timestamp"}[slot]
    if missing in view["input"]["query"] or "answer_spec" in view["input"] or "recorded_reply" in view["input"]:raise ValueError("partial query contains completion")
    for i in (0,1):
        if canonical(erase_resolution(completed_view(view,s,i),slot))!=canonical(view):raise ValueError("entire visible input differs between witnesses")
    # Recheck fine saved evidence, independent from organizer-supplied check summary.
    for check in e["additional_readout_checks"]:
        t=check["target"];coarse=readout(root,"factual",t,root["pair"]["original_run_id"])[0]
        m=pointer(root["factual_fine"],check["fine_state_pointer"])
        if t not in s["targets"] or check["result_file_sha256"]!=root["context"]["runs"]["original-fine"]["result_file_sha256"]:
            raise ValueError("fine readout is not tied to saved qualified run/target")
        state_path=check["fine_state_pointer"].split("/measurements/")[0]
        state=pointer(root["factual_fine"],state_path)
        if state["timestamp"]!=t["end_time"] or state["state_id"]!=check["state_id"] or (m["entity_id"],m["name"],m["unit"],m["frame"])!=(t["entity_id"],t["quantity"],t["unit"],t["frame"]):
            raise ValueError("fine readout target/time metadata differ")
        if digest(root["factual_fine"])!=digest(e["saved_fine_results"]["factual_fine"]):raise ValueError("fine namespace differs")
        if sha256(canonical(root["factual_fine"])).hexdigest()!=check["result_file_sha256"]:raise ValueError("fine raw result integrity differs")
        err,ok,_=distance(coarse["value"],m["value"],{**t,"absolute_tolerance":check["tolerance"],"relative_tolerance":0.})
        if not ok or err!=check["error"] or check["tolerance"]!=(.01 if t["unit"] in ("m/s","rad/s") else .005):raise ValueError("invalid extra-time saved refinement check")
    if s["ambiguity_type"]=="readout_time" and [c["target"] for c in e["additional_readout_checks"]]!=s["targets"]:
        raise ValueError("extra-time qualification is incomplete")
    ref=record["private"]["reference"]
    for c in ref["claims"]+ref["solution_trace"]["steps"]+[ref["verification_record"]]:
        if not c["bindings"]:raise ValueError("claim/step lacks evidence")
        for b in c["bindings"]:
            if digest(pointer(root[b["namespace"]],b["pointer"]))!=b["value_sha256"]:raise ValueError("unresolved clarification evidence")
    ex=read(ROOT/"configs/simphysqa/development_exclusions.json")["excluded_groups"]
    if record["trajectory_id"] not in ex or record["private"]["metadata"]["split_group_id"] not in ex:raise ValueError("development exclusion missing")
    return True


def rubric_text():
    r=read(ROOT/"configs/simphysqa/clarification_rubric.json")
    return r["version"]+"\n"+"\n".join(c["criterion"]+": "+c["requirement"] for c in r["criteria"])+"\n"+r["limitations"]
