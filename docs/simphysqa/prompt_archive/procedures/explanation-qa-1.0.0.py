"""Bounded matched-intervention explanation QA from saved, qualified pairs only."""
from copy import deepcopy
from hashlib import sha256
from pathlib import Path
from .io import ROOT, canonical, digest, read
from .dataset import restore, pointer
from .answer_annotations import binding, comparison, control_text, display, readout, roots as parent_roots

VERSION = "matched-intervention-explanation/1.0.0"
DISCLOSURE = "supplied-selected-outcomes/1.0.0"
FIXED = ["initial_conditions", "physical_parameters", "other_controls", "execution_settings"]

def versions():
    return {"procedure": VERSION,
        "implementation_sha256": sha256(Path(__file__).read_text(encoding="utf-8").encode()).hexdigest(),
        "rubric_sha256": digest(read(ROOT/"configs/simphysqa/explanation_rubric.json")),
        "record_schema_sha256": digest(read(Path(__file__).with_name("record.schema.json"))),
        "response_implementation_sha256": sha256(Path(__file__).with_name("explanation_evaluation.py").read_text(encoding="utf-8").encode()).hexdigest()}

def action(inp):
    p={v["name"]:v["value"] for v in inp["controller"]["parameters"]}
    if inp["domain"]=="robotic_arm":return "the additive +0.5 N*m pulse on joint_1"
    if inp["domain"]=="driving":return f'the scheduled zero-velocity axle brake command (maximum torque limit {display(p["brake_torque_limit"])} N*m)'
    if inp["domain"]=="object_pushing_stacking":return f'the scheduled +x external force on block_1 ({display(p["force"])} N)'
    if inp["domain"]=="tethered_load":return "the complete support-motion program, including both acceleration phases and subsequent prescribed displacement"
    raise ValueError("unsupported domain; no guessed semantics")

def evidence_roots(record):
    parent=record["private"]["explanation_evidence"]["parent_record"]
    root=parent_roots(parent,parent["private"]["answer_annotation"]["evidence_context"])
    root["public"]=record["public"]["input"]
    return root

def supplied(parent):
    target=parent["public"]["input"]["answer_spec"][0]
    t=parent["private"]["answer_annotation"]["targets"][0]
    c=t["comparison"]
    return {"version":DISCLOSURE,
        "disclosure":"Intentionally supplied simulation outcomes for an explanation task; these readouts are not observations in the saved prefix.",
        **{k:deepcopy(target[k]) for k in ("target_id","entity_id","quantity","unit","frame")},
        "timestamp":target["end_time"],
        "readouts":[{"condition":"factual_scheduled","value":deepcopy(c["factual_value"])},
                    {"condition":"omission","value":deepcopy(c["alternative_value"])}]}

def public_input(parent):
    from .explanation_evaluation import response_schema
    inp=deepcopy(parent["public"]["input"])
    target=inp["answer_spec"][0]
    c=parent["private"]["answer_annotation"]["targets"][0]["comparison"]
    event=inp["known_events"][0]
    inp.pop("counterfactual")
    inp["task_type"]="matched_intervention_explanation"
    focus=("Explain the unchanged predicate outcome without implying that all physical behavior is unchanged."
           if target["answer_type"]=="boolean" and c["exact_canonical_equality"] else
           "Explain the predicate-outcome difference using its declared threshold/history/duration rule."
           if target["answer_type"]=="boolean" else
           "Distinguish numerical difference from distinguishability under the existing answer tolerance.")
    inp["question"]=(f'Explain the matched comparison of {target["entity_id"]} {target["quantity"]} at '
        f'{display(target["end_time"])} s ({target["unit"]}, frame {target["frame"]}). '
        f'The factual condition retains {action(inp)}; the omission condition removes only that intervention. '
        'Initial conditions, physical parameters, other controls and execution settings remain fixed. '
        'Using the separately supplied target outcomes, explain what changed in the intervention, what stayed fixed, '
        'what the outcomes show, and which interpretation is supported or remains undetermined. '+focus)
    inp["explanation_task"]={"version":VERSION,"pair_id":parent["private"]["counterfactual_evidence"]["pair_id"],
        "operation":"omit_scheduled_intervention","omitted_event_id":event["event_id"],
        "fixed_conditions":FIXED,
        "worlds":"Known events and public scenario describe the factual condition; only the named intervention is omitted in the comparison condition.",
        "answer_spec_role":"Descriptor, predicate rule and existing tolerance for the single supplied target; this task requests an explanation, not a new future-state prediction."}
    inp["supplied_comparison"]=supplied(parent)
    inp["explanation_response_contract"]={"version":"explanation-response/1.0.0","schema":response_schema(target)}
    return inp

def reference(record):
    root=evidence_roots(record); inp=root["public"]; target=inp["answer_spec"][0]
    proof=root["pair"];context=root["context"]
    original_id=proof["original_run_id"];alternative_id=proof["alternative_run_id"]
    factual,fb,_=readout(root,"factual",target,original_id)
    alternative,ab,_=readout(root,"alternative",target,alternative_id)
    comp=comparison(factual["value"],alternative["value"],target)
    tb=[binding(root,"public","/answer_spec/0")]
    public_bindings=[binding(root,"public","/controller"),binding(root,"public","/known_events/0",event_id=inp["known_events"][0]["event_id"])]
    changed=[binding(root,"pair","/intervention_change")]
    for role in ("original-coarse","alternative-coarse"):
        changed.append(binding(root,"context","/runs/"+role+"/reservation",run_id=context["runs"][role]["run_id"]))
    impl=[binding(root,"context","/implementation/"+("engines" if inp["domain"] in ("robotic_arm","tethered_load") else "bullet"))]
    if inp["domain"]=="robotic_arm":impl.append(binding(root,"context","/arm_interpretation"))
    if inp["domain"]=="tethered_load":impl.append(binding(root,"context","/implementation/scenes"))
    fixed=[binding(root,"pair","/intervention_change/original_scenario"),binding(root,"pair","/intervention_change/original_config")]
    for ns in ("factual","alternative"):
        fixed.extend([binding(root,ns,"/input/states"),binding(root,ns,"/input/controller"),binding(root,ns,"/metadata/simulation")])
    claims=[]
    def claim(kind,text,bindings):
        item={"kind":kind,"text":text,"bindings":deepcopy(bindings)}
        item["claim_id"]="EXC-"+digest(item)[:16];claims.append(item)
    event=inp["known_events"][0]
    claim("declared_control",f'The factual schedule declares {action(inp)}, starting at {display(event["start_time"])} s.',public_bindings)
    ct=control_text(inp,True).split(" Implementation applies",1)[0]
    claim("implemented_change",ct,public_bindings+changed+impl)
    claim("fixed_conditions","The matched runs retain initial states, physical parameters, other controls, seed, solver settings, saved time grid and horizon; only the scheduled intervention is disabled.",fixed+changed)
    text=(f'{target["entity_id"]} {target["quantity"]} at {display(target["end_time"])} s: factual '
        f'{display(factual["value"])} versus omission {display(alternative["value"])} {target["unit"]} ({target["frame"]}).')
    disclosure=[binding(root,"public","/supplied_comparison")]
    claim("matched_outcome",text,fb+ab+tb+disclosure)
    if target["answer_type"]=="boolean":
        history=[binding(root,ns,"/reference/events",run_id=rid) for ns,rid in (("factual",original_id),("alternative",alternative_id))]
        claim("predicate_rule",f'This flag follows the declared rule: {target["rule_definition"]} History/duration predicates cannot be inferred from one terminal measurement.',tb+fb+ab+history+impl)
        interpretation=("Both runs return the same predicate outcome; that does not establish identical trajectories or absence of physical effects."
            if comp["exact_canonical_equality"] else "The predicate outcome differs in the matched simulator comparison; the saved flags follow the declared history/duration rule, rather than terminal speed alone.")
    else:
        error=display(comp["scorer_error"]);unit=comp["scorer_error_unit"]
        distinguish="within" if comp["factual_answer_passes_alternative_scorer"] else "outside"
        metric="sign-invariant rotation-angle" if target["quantity"]=="orientation" else "Euclidean" if target["answer_type"]=="vector" else "absolute"
        interpretation=(f'The {metric} readout difference is {error} {unit}, {distinguish} the existing answer tolerance '
            f'(absolute {display(target["absolute_tolerance"])} plus relative {display(target["relative_tolerance"])} times the reference magnitude). '
            'A nonzero difference within tolerance is still a numerical difference, not proof of no physical effect.' if comp["factual_answer_passes_alternative_scorer"] else
            f'The {metric} readout difference is {error} {unit}, outside the existing answer tolerance '
            f'(absolute {display(target["absolute_tolerance"])} plus relative {display(target["relative_tolerance"])} times the reference magnitude). '
            'The selected target is distinguishable by this scorer in the matched simulator comparison.')
    claim("supported_interpretation",interpretation,fb+ab+tb)
    vb=[binding(root,"pair","/verification"),binding(root,"context","/verification")]
    claim("remaining_uncertainty","This controlled comparison isolates the intervention within the specified simulator; it does not establish a detailed force/contact pathway or real-world causality. The selected readout alone does not determine all other physical behavior.",changed+fixed+fb+ab+vb)
    procedure={
        "declared_control":"Read the factual public schedule and controller parameters to identify the declared action, direct target and onset; do not treat a magnitude limit as a realized measurement.",
        "implemented_change":"Compare the saved factual/alternative reservations: omit_scheduled_intervention is false/true. Use the saved implementation/intervention record to identify precisely which control program is skipped and which controls remain.",
        "fixed_conditions":"Check equality of the paired initial states, scenario/configuration hashes, remaining controller parameters and numerical settings. Role and the omission flag distinguish conditions; all other scientific execution settings agree at each matched precision.",
        "matched_outcome":f'Locate {target["entity_id"]}/{target["quantity"]} at exactly {display(target["end_time"])} s in the factual and alternative saved states. Retain typed values, unit and frame and check that the separate supplied readouts reproduce them exactly.',
        "predicate_rule":"Read the declared threshold/history/duration rule and saved simulator flags/event histories. Sparse saved measurements do not reconstruct every integration substep; do not substitute an instantaneous endpoint for a historical or continuous-duration predicate.",
        "supported_interpretation":"Compare the selected typed readouts: canonical equality is distinct from numeric difference and from the unchanged answer scorer's tolerance acceptance. Use scalar absolute error, vector Euclidean error or sign-invariant quaternion angle as applicable; a common Boolean or accepted numeric contrast does not imply all behavior is unchanged.",
        "remaining_uncertainty":"Connect the one verified controlled change and fixed scenario to the selected simulator contrast. Restrict the inference to this matched simulator; selected readouts and numerical receipts do not verify a detailed force/contact mechanism or real-world causality."
    }
    trace=[]
    for c in claims:
        trace.append({"step":len(trace)+1,"operation":c["kind"],"supports_claim_ids":[c["claim_id"]],"text":procedure[c["kind"]],"bindings":deepcopy(c["bindings"])})
    parent_target=record["private"]["explanation_evidence"]["parent_record"]["private"]["answer_annotation"]["targets"][0]
    numerical=next(s for s in parent_target["solution_trace"]["steps"] if s["operation"]=="saved_numerical_procedure")
    trace.append({"step":len(trace)+1,"operation":"saved_numerical_procedure","supports_claim_ids":[],"text":numerical["text"],"bindings":deepcopy(numerical["bindings"])})
    trace.append({"step":len(trace)+1,"operation":"verification","supports_claim_ids":[c["claim_id"] for c in claims if c["kind"] in ("implemented_change","fixed_conditions","remaining_uncertainty")],
        "text":"Saved canonical exact factual replay and separate factual/alternative admission passed; these receipts verify numerical provenance, not human explanatory quality.","bindings":vb})
    verification={"status":"saved_evidence_checked","target_readouts_equal_saved_values":True,
        "exact_factual_replay":True,"separate_factual_and_alternative_admission":True,"bindings":vb+fb+ab,
        "human_explanation_assessment":"uncollected","new_simulations":0}
    prose=" ".join(c["text"] for c in claims)
    return {"label":prose,"explanation":prose,"explanation_kind":"supported_matched_intervention_claims",
        "claims":claims,"comparison":comp,"solution_trace":{"version":VERSION,"status":"evidence_checked_human_unreviewed","steps":trace,"verification_record":verification},
        "verification_record":verification,"rubric_version":"matched-explanation-rubric/1.0.0"}

def construct(parent):
    inp=public_input(parent); proof=parent["private"]["counterfactual_evidence"]
    target=inp["answer_spec"][0]
    record={"schema_version":"simphysqa/0.4.0","source_schema_version":parent["source_schema_version"],
        "sample_id":"spq-explanation-"+digest({"version":VERSION,"pair_id":proof["pair_id"],"target":target})[:24],
        "trajectory_id":parent["trajectory_id"],"question_type":"explanation","annotation_version":parent["annotation_version"],
        "source":deepcopy(parent["source"]),"public":{"input":inp,"annotations":deepcopy(parent["public"]["annotations"])},
        "private":{"source_record":restore(parent),"metadata":deepcopy(parent["private"]["metadata"]),
            "annotation_provenance":deepcopy(parent["private"]["annotation_provenance"]),
            "evidence_bindings":deepcopy(parent["private"]["evidence_bindings"]),
            "explanation_evidence":{"parent_sample_id":parent["sample_id"],"parent_record_sha256":digest(parent),"pair_id":proof["pair_id"],"parent_record":deepcopy(parent)},
            "reference":{}},"completion":deepcopy(parent["completion"])}
    record["private"]["reference"]=reference(record)
    v=versions()
    record["private"]["explanation_annotation"]={"version":VERSION,"versions":v,
        "cache_identity":digest({"parent":parent,"versions":v}),"generation":"deterministic_no_model_request",
        "annotation_language_origin":"reuse_of_SPQ01_measurement_language_and_SPQ01a_deterministic_event_enrichment",
        "status":"evidence_checked_human_unreviewed","new_model_calls":0,"new_simulations":0,"new_spend_usd":0}
    record["completion"]["explanation_qa"]="constructed_matched_intervention_human_unreviewed"
    return record

def build(parent):
    from .dataset import validate
    validate(parent)
    if parent["question_type"]!="counterfactual" or parent["private"]["answer_annotation"]["version"]!="simphysqa-answer-annotation/1.0.3":
        raise ValueError("explanation requires accepted verified matched parent and answer annotation 1.0.3")
    result=construct(parent);validate_explanation(result);return result

def validate_explanation(record):
    from .dataset import validate
    from .event_language import validate_view
    parent=record["private"]["explanation_evidence"]["parent_record"]
    validate(parent)
    if parent["question_type"]!="counterfactual" or parent["private"]["answer_annotation"]["version"]!="simphysqa-answer-annotation/1.0.3":
        raise ValueError("unqualified explanation parent")
    # Four saved reservations isolate the actual change, rather than a label alone.
    runs=parent["private"]["answer_annotation"]["evidence_context"]["runs"]
    for precision in ("coarse","fine"):
        a=deepcopy(runs["original-"+precision]["reservation"]);b=deepcopy(runs["alternative-"+precision]["reservation"])
        if a.pop("omit_scheduled_intervention") is not False or b.pop("omit_scheduled_intervention") is not True:
            raise ValueError("saved execution does not implement matched omission")
        a.pop("role");b.pop("role")
        if canonical(a)!=canonical(b):raise ValueError("remaining saved execution settings differ")
    if canonical(record)!=canonical(construct(parent)):
        raise ValueError("explanation question, disclosure, reference, evidence or provenance differs from pinned construction")
    inp=record["public"]["input"]
    validate_view(inp,record["public"]["annotations"],record["annotation_version"])
    root=evidence_roots(record);ref=record["private"]["reference"]
    ids={c["claim_id"] for c in ref["claims"]}
    if len(ids)!=len(ref["claims"]):raise ValueError("duplicate explanation claim")
    for item in ref["claims"]+ref["solution_trace"]["steps"]:
        if not item["bindings"] or not item["text"].strip():raise ValueError("unsupported explanation statement")
        if not set(item.get("supports_claim_ids",[]))<=ids:raise ValueError("unresolved trace claim")
        for b in item["bindings"]:
            if digest(pointer(root[b["namespace"]],b["pointer"]))!=b["value_sha256"]:raise ValueError("unresolved explanation evidence")
    exclusions=read(ROOT/"configs/simphysqa/development_exclusions.json")["excluded_groups"]
    if record["trajectory_id"] not in exclusions or record["private"]["metadata"]["split_group_id"] not in exclusions:
        raise ValueError("explanation development group missing formal exclusion")
    return True

def rubric_text():
    rubric=read(ROOT/"configs/simphysqa/explanation_rubric.json")
    return rubric["version"]+"\n"+rubric["instructions"]+"\n\n"+"\n\n".join(
        c["criterion"]+": "+c["required_supported_claim"]+"\nAcceptable paraphrases: "+"; ".join(c["acceptable_paraphrases"])+
        "\nMaterial contradictions: "+"; ".join(c["material_contradictions"]) for c in rubric["criteria"])+"\n\n"+rubric["limitations"]+"\n"
