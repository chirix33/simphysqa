"""Two-stage preparation/routing and factual scoring; no models or prose judge."""
from copy import deepcopy
from jsonschema import Draft202012Validator
from jsonschema.exceptions import ValidationError
from .io import canonical, read, ROOT
from .clarification import response_schema, VERSION, SLOTS
from .scoring import distance

VERSION_RESPONSE="clarification-interaction/1.0.0"


def initial_request(record, condition):
    from .dataset import validate
    validate(record)
    view=record["private"]["initial_view"]
    text=("The question is deliberately incomplete. Use every visible surface and request one focused clarification if a unique requested answer is not determined. "
        "Return JSON following input.interaction.response_schema. Do not guess missing information or give a unique answer before clarification. Tools are unavailable.")
    if condition["reasoning"]=="prompted_cot":text+=" Express the focused information request in clarification_question; keep it concise."
    return {"sample_id":record["sample_id"],"condition_id":condition["condition_id"],"tools":[],"messages":[{"role":"user","content":text+"\n"+canonical(view).decode()}]}


def inspect_stage1(record, response):
    """Structured declared-slot checks only; text relevance/adequacy require humans."""
    canonical(response)
    premature = any(k in response for k in ("answer","answers","targets","value","resolved_answer")) or response.get("response_kind")=="answer"
    # A prose answer disguised as a question cannot be decided by a keyword heuristic.
    try:
        Draft202012Validator(response_schema()).validate(response);valid=True
    except ValidationError:valid=False
    slot=record["private"]["clarification_evidence"]["selection"]["ambiguity_type"]
    matches=valid and response["requested_information"]==slot
    return {"version":VERSION_RESPONSE,"gap_recognition_declaration":response.get("response_kind")=="clarify",
        "structured_slot_matches_gap":matches,"structured_slot_sufficient":matches,"response_contract_valid":valid,
        "premature_structured_answer":premature,"premature_answer_in_prose":"human_review_required",
        "clarification_wording_relevance":"human_judgment_uncollected","clarification_wording_sufficiency":"human_judgment_uncollected",
        "automatic_coverage":"Declared behavior/slot and explicit structured answer fields only; no exact-text or keyword semantic grading"}


def route_reply(record, response):
    result=inspect_stage1(record,response)
    if not result["structured_slot_matches_gap"] or result["premature_structured_answer"]:
        return {"status":"unroutable","reply":None,"resolved_view":None,"checks":result}
    return {"status":"recorded_reply_routed","reply":deepcopy(record["private"]["resolved_view"]["input"]["recorded_reply"]),
        "resolved_view":deepcopy(record["private"]["resolved_view"]),"checks":result,
        "policy":"Structured slot routes reproducibly; wording/compound demands remain separately reviewed. Never exact reference wording."}


def continuation(record, condition, actual_response):
    """Only actual supplied responses can become assistant turns; never gold questions."""
    routed=route_reply(record,actual_response)
    if routed["status"]!="recorded_reply_routed":return routed
    first=initial_request(record,condition)
    first["messages"].extend([{"role":"assistant","content":canonical(actual_response).decode()},
        {"role":"user","content":"Recorded clarification reply and resolved task (no gold answer):\n"+canonical(routed["resolved_view"]).decode()}])
    return first


def continuation_template(record, condition):
    # Reference clarification question is PRIVATE and never a prepared assistant message.
    return {"sample_id":record["sample_id"],"condition_id":condition["condition_id"],"tools":[],
        "status":"template_not_executed_interaction","version":VERSION_RESPONSE,
        "initial_request":initial_request(record,condition),
        "conditional_continuation":{"assistant_message":"Insert actual recorded model stage-1 response only; no authored reference response.",
            "routing":"clarification_evaluation.route_reply; structured single-slot match required",
            "user_message":{"role":"user","content":"Recorded clarification reply and resolved task (no gold answer):\n"+canonical(record["private"]["resolved_view"]).decode()}},
        "on_unroutable":"Record invalid/irrelevant/premature response separately; do not silently supply reply or count a completed interaction"}


def check_stage2(record,response):
    schema=record["private"]["resolved_view"]["input"]["interaction"]["response_schema"]
    canonical(response);Draft202012Validator(schema).validate(response)
    target=record["private"]["resolved_view"]["input"]["answer_spec"][0]
    truth=record["private"]["reference"]["structured_label"][0];v=response["targets"][0]
    error,accepted,unit=distance(v["value"],truth["value"],target)
    return {"answer_correct_under_existing_typed_scorer":accepted,"error":error,"metric_unit":unit,
        "exact_value":canonical(v["value"])==canonical(truth["value"]),
        "answer_explanation_adequacy":"human_judgment_uncollected","prose_premature_answer_assessment":"separate_human_review"}


def score_interactions(records, supplied, condition_ids):
    """Retain missing/invalid/failed stages. Does not prepare or execute a conversation."""
    from .dataset import validate
    if not condition_ids or len(set(condition_ids))!=len(condition_ids):raise ValueError("distinct conditions required")
    byid={r["sample_id"]:r for r in records}
    if len(byid)!=len(records):raise ValueError("duplicate clarification record")
    for r in records:
        validate(r)
        if r["question_type"]!="clarification":raise ValueError("clarification-only interaction scorer")
    predictions={}
    for p in supplied:
        key=(p["condition_id"],p["sample_id"])
        if key in predictions or key[0] not in condition_ids or key[1] not in byid:raise ValueError("unknown/duplicate supplied interaction")
        if p["task_version"]!=VERSION or p["annotation_version"]!=byid[key[1]]["annotation_version"]:raise ValueError("stale interaction")
        predictions[key]=p
    results=[]
    for c in condition_ids:
        for sid,r in byid.items():
            p=predictions.get((c,sid));s1=s2=None;status="missing" if p is None else p["status"]
            if status not in ("completed","failed","invalid","abstained","missing"):raise ValueError("invalid status")
            if status=="completed":
                try:
                    s1=inspect_stage1(r,p["stage1_response"])
                    routed=route_reply(r,p["stage1_response"])
                    if routed["status"]!="recorded_reply_routed":status="invalid"
                    elif p.get("reply")!=routed["reply"]:status="invalid"
                    else:s2=check_stage2(r,p["stage2_response"])
                except (KeyError,TypeError,ValueError,ValidationError):status="invalid"
            results.append({"condition_id":c,"sample_id":sid,"domain":r["public"]["input"]["domain"],"question_type":"clarification","status":status,"stage1":s1,"stage2":s2})
    tables=[]
    for c in condition_ids:
        for d in sorted({r["public"]["input"]["domain"] for r in records}):
            rows=[v for v in results if v["condition_id"]==c and v["domain"]==d]
            tables.append({"condition_id":c,"domain":d,"question_type":"clarification","examples":len(rows),
                "gap_recognition_declarations":sum(bool(v["stage1"] and v["stage1"]["gap_recognition_declaration"]) for v in rows),
                "matching_structured_requests":sum(bool(v["stage1"] and v["stage1"]["structured_slot_matches_gap"]) for v in rows),
                "premature_structured_answers":sum(bool(v["stage1"] and v["stage1"]["premature_structured_answer"]) for v in rows),
                "correct_post_reply_answers":sum(bool(v["stage2"] and v["stage2"]["answer_correct_under_existing_typed_scorer"]) for v in rows),
                "status_counts":{s:sum(v["status"]==s for v in rows) for s in ("missing","failed","invalid","abstained","completed")}})
    return {"version":VERSION_RESPONSE,"items":results,"tables":tables,"model_calls":0,"human_wording_and_explanation_judgments":"uncollected","uncertainty":"pending_experiment_and_analysis_freeze"}
