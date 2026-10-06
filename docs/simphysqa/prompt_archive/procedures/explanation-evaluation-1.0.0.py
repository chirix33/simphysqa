"""Structured factual checks only; never an automatic explanation-quality score."""
from copy import deepcopy
from jsonschema import Draft202012Validator
from jsonschema.exceptions import ValidationError
from .io import canonical, digest
from .explanation import FIXED
from .scoring import distance

VERSION="explanation-response/1.0.0"
EVALUATOR="explanation-factual-components/1.0.0"

def response_schema(target):
    value={"type":"boolean"} if target["answer_type"]=="boolean" else {"type":"array","minItems":4 if target["quantity"]=="orientation" else 3,"maxItems":4 if target["quantity"]=="orientation" else 3,"items":{"type":"number"}} if target["answer_type"]=="vector" else {"type":"number"}
    measurement={"type":"object","additionalProperties":False,
        "required":["value","entity_id","quantity","timestamp","unit","frame"],"properties":{
            "value":value,"entity_id":{"const":target["entity_id"]},"quantity":{"const":target["quantity"]},
            "timestamp":{"const":target["end_time"]},"unit":{"const":target["unit"]},"frame":{"const":target["frame"]}}}
    return {"$schema":"https://json-schema.org/draft/2020-12/schema","type":"object","additionalProperties":False,
        "required":["response_version","target_id","intervention","fixed_conditions","outcomes","contrast","explanation","supported_interpretation","remaining_uncertainty"],
        "properties":{"response_version":{"const":VERSION},"target_id":{"const":target["target_id"]},
            "intervention":{"type":"object","additionalProperties":False,"required":["operation","omitted_event_id"],
                "properties":{"operation":{"const":"omit_scheduled_intervention"},"omitted_event_id":{"type":"string"}}},
            "fixed_conditions":{"type":"array","uniqueItems":True,"items":{"enum":FIXED}},
            "outcomes":{"type":"object","additionalProperties":False,"required":["factual_scheduled","omission"],
                "properties":{"factual_scheduled":measurement,"omission":measurement}},
            "contrast":{"type":"object","additionalProperties":False,"required":["exact_target_equality","factual_passes_omission_scorer"],
                "properties":{"exact_target_equality":{"type":"boolean"},"factual_passes_omission_scorer":{"type":"boolean"}}},
            "explanation":{"type":"string","minLength":1},"supported_interpretation":{"type":"string","minLength":1},
            "remaining_uncertainty":{"type":"string","minLength":1}}}

def expected_facts(record):
    inp=record["public"]["input"];s=inp["supplied_comparison"]
    comparison=record["private"]["reference"]["comparison"]
    return {"response_version":VERSION,"target_id":s["target_id"],
        "intervention":{"operation":"omit_scheduled_intervention","omitted_event_id":inp["explanation_task"]["omitted_event_id"]},
        "fixed_conditions":FIXED,
        "outcomes":{r["condition"]:{"value":deepcopy(r["value"]),**{k:deepcopy(s[k]) for k in ("entity_id","quantity","timestamp","unit","frame")}} for r in s["readouts"]},
        "contrast":{"exact_target_equality":comparison["exact_canonical_equality"],"factual_passes_omission_scorer":comparison["factual_answer_passes_alternative_scorer"]}}

def prompt(condition):
    text=("This is explanation QA. The separately identified supplied_comparison contains intentionally supplied simulation target outcomes, not observed prefix states. "
        "Explain the actual intervention change, fixed conditions, selected outcome comparison, supported interpretation and remaining uncertainty within the specified simulator. "
        "Use the original public scenario, language annotations, declared controls and supplied target readouts. Do not invent private rollouts, forces/contact histories or real-world causality. "
        "Return one JSON object following input.explanation_response_contract.schema; include readable explanation, supported_interpretation and remaining_uncertainty, alongside structured factual components. "
        "Equality of a Boolean or a sub-tolerance numerical contrast does not establish unchanged physical behavior. Respect historical/duration predicate rules.")
    if condition["reasoning"]=="prompted_cot":
        text+=" Present your evidence-based explanation in the explanation field before the final structured factual interpretation."
    return text

def check_facts(record,response):
    """Content/schema checks do not grade the meaning of any prose field."""
    target=record["public"]["input"]["answer_spec"][0]
    canonical(response)  # Reject nonfinite JSON and preserve Boolean/numeric type distinction.
    Draft202012Validator(response_schema(target)).validate(response)
    expected=expected_facts(record)
    checks={"intervention_identity":response["intervention"]==expected["intervention"],
        "fixed_condition_declarations":set(response["fixed_conditions"])==set(FIXED),
        "exact_target_equality_fact":response["contrast"]["exact_target_equality"]==expected["contrast"]["exact_target_equality"],
        "existing_scorer_distinguishability_fact":response["contrast"]["factual_passes_omission_scorer"]==expected["contrast"]["factual_passes_omission_scorer"]}
    diagnostics={}
    for role in ("factual_scheduled","omission"):
        v=response["outcomes"][role]["value"];truth=expected["outcomes"][role]["value"]
        error,accepted,unit=distance(v,truth,target)
        checks[role+"_reported_value_under_existing_tolerance"]=accepted
        diagnostics[role]={"exact_canonical_value":canonical(v)==canonical(truth),"readout_error":error,"error_unit":unit}
    return {"version":EVALUATOR,"factual_component_checks":checks,"factual_components_correct":sum(checks.values()),
        "factual_components_total":len(checks),"factual_components_all_correct":all(checks.values()),"diagnostics":diagnostics,
        "automatic_coverage":"Structured intervention ID, fixed-condition declarations, selected readouts and equality/scorer facts only. Nonempty prose is a format requirement, never proof of explanatory adequacy.",
        "prose_quality":"not_automatically_assessed","explanatory_adequacy":"human_judgment_uncollected",
        "unsupported_or_contradictory_prose":"requires_claim_level_review_no_keyword_score","overall_explanation_correctness":None}

def score_facts(records,predictions,condition_ids):
    """All items remain in denominators; no models, text matching or prose grading."""
    from .dataset import validate
    if not condition_ids or len(set(condition_ids))!=len(condition_ids):raise ValueError("distinct conditions required")
    by_id={r["sample_id"]:r for r in records}
    if len(by_id)!=len(records):raise ValueError("duplicate record")
    for r in records:
        validate(r)
        if r["question_type"]!="explanation":raise ValueError("explanation-only factual evaluator")
    supplied={}
    for p in predictions:
        key=(p["condition_id"],p["sample_id"])
        if key in supplied or key[0] not in condition_ids or key[1] not in by_id:raise ValueError("unknown/duplicate prediction")
        if p["annotation_version"]!=by_id[key[1]]["annotation_version"] or p["task_version"]!=by_id[key[1]]["public"]["input"]["explanation_task"]["version"]:
            raise ValueError("prediction version differs")
        supplied[key]=p
    items=[]
    for condition in condition_ids:
        for sid,r in by_id.items():
            p=supplied.get((condition,sid));status=p["status"] if p else "missing";facts=None;error=None
            if status not in ("completed","failed","invalid","abstained","missing"):raise ValueError("invalid result status")
            if status=="completed":
                try:facts=check_facts(r,p["response"])
                except (ValueError,KeyError,TypeError,ValidationError) as exc:
                    status="invalid";error=type(exc).__name__
            items.append({"condition_id":condition,"sample_id":sid,"domain":r["public"]["input"]["domain"],"question_type":"explanation",
                "trajectory_id":r["trajectory_id"],"status":status,"factual_content":facts,"validation_error":error})
    tables=[]
    for condition in condition_ids:
        for domain in sorted({r["public"]["input"]["domain"] for r in records}):
            selected=[i for i in items if i["condition_id"]==condition and i["domain"]==domain]
            tables.append({"condition_id":condition,"domain":domain,"question_type":"explanation","examples":len(selected),
                "factual_components_all_correct":sum(bool(i["factual_content"] and i["factual_content"]["factual_components_all_correct"]) for i in selected),
                "expected_factual_components":6*len(selected),"correct_factual_components":sum(i["factual_content"]["factual_components_correct"] if i["factual_content"] else 0 for i in selected),
                "status_counts":{s:sum(i["status"]==s for i in selected) for s in ("completed","missing","failed","invalid","abstained")},
                "overall_explanation_correctness":None,"human_judgments":"uncollected"})
    return {"version":EVALUATOR,"items":items,"tables":tables,"new_model_calls":0,
        "coverage":"factual structured components only; no keyword, exact-text or MSE explanation-quality score",
        "prose_quality_and_explanatory_adequacy":"pending_independent_human_review","uncertainty":"pending_experiment_and_analysis_freeze"}
