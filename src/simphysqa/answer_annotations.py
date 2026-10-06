"""Private, deterministic evidence-bound answer annotations; no physics/provider calls."""
from copy import deepcopy
from hashlib import sha256
from pathlib import Path
from jsonschema import Draft202012Validator
from .dataset import pointer, restore
from .io import canonical, digest, read
from .scoring import distance

VERSION = "simphysqa-answer-annotation/1.0.3"
RENDERER = "grounded-saved-solution/1.0.3"
DISPLAY = "eight-significant-digits/1.0.0"

def versions():
    return {"contract": VERSION, "renderer": RENDERER, "display": DISPLAY,
            "implementation_sha256": sha256(Path(__file__).read_text(encoding="utf-8").encode()).hexdigest(),
            "schema_sha256": digest(read(Path(__file__).with_name("answer_annotation.schema.json")))}

def display(value):
    if type(value) is bool:
        return "true" if value else "false"
    if isinstance(value, list):
        return "[" + ", ".join(display(v) for v in value) + "]"
    return format(value, ".8g")

def roots(record, context):
    result = {"public": record["public"]["input"], "factual": restore(record), "context": context}
    if record["question_type"] == "counterfactual":
        result["alternative"] = record["private"]["counterfactual_evidence"]["alternative_record"]
        result["pair"] = record["private"]["counterfactual_evidence"]
    return result

def binding(root, namespace, path, **identity):
    return {"namespace": namespace, "pointer": path, "value_sha256": digest(pointer(root[namespace], path)), **identity}

def readout(root, namespace, target, run_id):
    source = root[namespace]
    states = source["states"] if namespace == "public" else source["reference"]["states"]
    i, state = next((i, s) for i, s in enumerate(states) if s["timestamp"] == target["end_time"])
    j, m = next((j, m) for j, m in enumerate(state["measurements"])
                if (m["entity_id"], m["name"]) == (target["entity_id"], target["quantity"]))
    if (m["unit"], m["frame"]) != (target["unit"], target["frame"]):
        raise ValueError("target unit/frame differ from saved channel")
    prefix = "" if namespace == "public" else "/reference"
    identities = {"state_id": state["state_id"], "run_id": run_id}
    b = [binding(root, namespace, f"{prefix}/states/{i}/timestamp", **identities),
         binding(root, namespace, f"{prefix}/states/{i}/measurements/{j}", **identities)]
    return deepcopy(m), b, state["state_id"]

def comparison(factual, alternative, target):
    error, accepted, error_unit = distance(factual, alternative, target)
    orientation = target["quantity"] == "orientation" and target["answer_type"] == "vector"
    delta = None if type(factual) is bool or orientation else ([b-a for a,b in zip(factual, alternative)]
            if isinstance(factual, list) else alternative-factual)
    return {"factual_value": deepcopy(factual), "alternative_value": deepcopy(alternative),
            "exact_canonical_equality": canonical(factual) == canonical(alternative),
            "alternative_minus_factual": delta,
            "difference_kind": "sign_invariant_rotation_angle" if orientation else "boolean_equality" if type(factual) is bool else "signed_numeric_difference",
            "rotation_angle_rad": error if orientation else None, "scorer_error": error, "scorer_error_unit": error_unit,
            "factual_answer_passes_alternative_scorer": accepted,
            "absolute_tolerance": target["absolute_tolerance"], "relative_tolerance": target["relative_tolerance"],
            "interpretation_limit": "Equal Booleans or a difference within answer tolerance do not establish absence of a physical effect."}

def control_text(inp, omission):
    d = inp["domain"]; e = inp["known_events"][0]
    schedule = f'[{display(e["start_time"])}, {display(e["end_time"])}) s'
    p = {v["name"]: v["value"] for v in inp["controller"]["parameters"]}
    if d == "robotic_arm":
        base = "; ".join(f'{v["entity_id"]} base torque {display(v["value"])} {v["unit"]}' for v in inp["controller"]["controls"])
        action = f'additional +0.5 N*m joint_1 pulse scheduled over {schedule}'
        tail = f'{base}; gravity, model inertia, joint constraints and viscous damping are retained. '
        tail += 'Implementation applies base and pulse as scalar generalized hinge torques in qfrc_applied; inherited event world and base joint_local declarations are preserved, not converted.'
    elif d == "driving":
        action = f'zero-velocity axle brake command scheduled over {schedule}, with maximum torque limit {display(p["brake_torque_limit"])} N*m'
        tail = f'wheel/ground contact and declared friction coefficient {display(p["friction"])} remain. The command limit is not a measured realized torque.'
    elif d == "object_pushing_stacking":
        action = f'+x external force {display(p["force"])} N on block_1 at its instantaneous center of mass over {schedule}'
        tail = 'gravity, contacts, friction and the complete table/block model remain; block_2 is contextual, not the directly pushed target.'
    elif d == "tethered_load":
        action = f'complete support-motion program starting at {display(e["start_time"])} s: +{display(p["acceleration"])} then -{display(p["acceleration"])} m/s^2 for 0.1 s each, including subsequent prescribed displacement'
        tail = f'load mass {display(p["mass"])} kg, cable length {display(p["length"])} m, gravity and constrained pendulum dynamics remain.'
        if omission:
            tail += ' Support translation and velocity stay zero; only its world z position remains 2 m.'
    else:
        raise ValueError("unsupported domain; no guessed control semantics")
    return ("Omit only the " if omission else "Retain the ") + action + ". " + tail

def render(record, context):
    """Target-specific deterministic claims/steps. Raw source references are never edited."""
    typ = record["question_type"]
    if typ not in ("direct", "predictive", "counterfactual"):
        raise ValueError("explanation/clarification families require their own supported-claim/gap construction")
    root = roots(record, context); inp = root["public"]
    if typ != "direct":
        verified = context["verification"]
        if canonical(verified["stored_source_admission"]) != canonical(restore(record)["metadata"]["validation"]):
            raise ValueError("admission context differs from source metadata")
        if context.get("runs"):
            replay = verified["additional_exact_replay"]
            if not replay["passed"] or not all(replay[k] for k in ("all_saved_states_exact", "all_private_events_equal", "all_public_definitions_exact", "all_structured_labels_exact")):
                raise ValueError("exact-replay claim lacks passed evidence")
            for key in ("original_admission", "alternative_admission"):
                if not verified[key]["domain_physics"] or not verified[key]["refinement"]["passed"]:
                    raise ValueError("admission claim lacks passed evidence")
        if typ == "counterfactual":
            proof = root["pair"]
            for key, ctx_key in (("replay", "additional_exact_replay"), ("original_admission", "original_admission"), ("alternative_admission", "alternative_admission")):
                if canonical(proof["verification"][key]) != canonical(verified[ctx_key]):
                    raise ValueError("paired verification context differs")
            for role, receipt in proof["simulation_artifacts"].items():
                run = context["runs"][role]
                if run["run_id"] != receipt["run_id"] or run["result_file_sha256"] != receipt["result_sha256"] or run["reservation_file_sha256"] != receipt["reservation_sha256"]:
                    raise ValueError("paired execution namespace/hash differs")
    labels = {v["target_id"]: v for v in record["private"]["reference"]["structured_label"]}
    namespace = "public" if typ == "direct" else "alternative" if typ == "counterfactual" else "factual"
    run_id = (context["runs"]["alternative-coarse"]["run_id"] if typ == "counterfactual" else
              context.get("runs", {}).get("original-coarse", {}).get("run_id", "stored-source:"+restore(record)["sample_id"]))
    if typ == "direct":
        run_id = "public-observed:" + record["sample_id"]
    targets = []; shared_claims = []
    for index, target in enumerate(inp["answer_spec"]):
        tb = [binding(root, "public", f"/answer_spec/{index}")]
        measured, rb, state_id = readout(root, namespace, target, run_id)
        label = labels[target["target_id"]]
        if canonical(label["value"]) != canonical(measured["value"]):
            raise ValueError("label not exact requested saved readout")
        requested = f'{target["entity_id"]} {target["quantity"]} at {display(target["end_time"])} s, unit {target["unit"]}, frame {target["frame"]}'
        answer = f'The saved {namespace} state {state_id} gives {display(label["value"])} {target["unit"]} for {requested}.'
        claims = []; steps = []
        def claim(kind, text, bindings):
            item = {"kind": kind, "text": text, "bindings": deepcopy(bindings)}
            claims.append(item); return item
        def step(operation, text, bindings):
            steps.append({"step": len(steps)+1, "operation": operation, "text": text, "bindings": deepcopy(bindings)})
        claim("target", f'Requested readout: {requested}.', tb)
        identify = f'Identify {requested} using target {target["target_id"]}.'
        identify_bindings = tb
        if typ == "counterfactual":
            event = inp["known_events"][0]
            identify += f' Evaluate the alternative omitting scheduled event {event["event_id"]}, leaving the remaining scenario fixed.'
            identify_bindings = tb + [binding(root, "pair", "/intervention_change")]
        step("identify_target", identify, identify_bindings)
        comp = None
        if typ == "direct":
            claim("observed_readout", answer + ' This channel is already present in the observed input; no interpolation or future solve is required.', rb+tb)
            step("locate_observed_measurement", f'Locate public state {state_id} and its {target["entity_id"]}/{target["quantity"]} measurement at the exact requested timestamp.', rb)
            step("extract_exact_value", f'Copy the typed value {display(label["value"])} with its source unit/frame; perform no additional computation.', rb+tb)
            verification = {"status": "observed_readout_exactly_checked", "readout_equals_gold": True,
                            "simulation_required": False, "bindings": rb+tb, "human_assessment": "unreviewed"}
        else:
            cf = typ == "counterfactual"
            # Controllers/effective models are evidence, not equations evaluated by this module.
            cb = [binding(root, "public", "/controller"), binding(root, "public", "/known_events/0", event_id=inp["known_events"][0]["event_id"]),
                  binding(root, "public", "/global_context"), binding(root, "context", "/implementation/"+("engines" if inp["domain"] in ("robotic_arm","tethered_load") else "bullet"))]
            if inp["domain"] == "tethered_load":
                cb.append(binding(root,"context","/implementation/scenes"))
            if inp["domain"] == "robotic_arm":
                cb.append(binding(root, "context", "/arm_interpretation"))
            if cf:
                cb += [binding(root, "pair", "/intervention_change")]
            ct = control_text(inp, cf)
            claim("effective_control", ct, cb)
            if not shared_claims:
                # Share only physical context; technical execution detail stays in traces.
                concise_control = ct.split(" Implementation applies", 1)[0]
                shared_claims.append({"kind": "shared_physical_conditions", "text": concise_control,
                                      "bindings": deepcopy(cb)})
            initial = inp["states"][0]
            ib = [binding(root, "public", "/states/0", state_id=initial["state_id"])]
            step("effective_conditions", ct + f' Start from observed initial state {initial["state_id"]}; retain initial conditions and all other declared parameters.', cb+ib)
            settings = root[namespace]["metadata"]["simulation"]
            sb = [binding(root, namespace, "/metadata/simulation", run_id=run_id), binding(root, "context", "/method")]
            if context.get("runs"):
                role = "alternative-coarse" if cf else "original-coarse"
                sb.append(binding(root, "context", "/runs/"+role, run_id=run_id))
            method = f'{context["method"]} Saved engine {settings["engine"]} {settings["engine_version"]}; integration dt {display(settings["integration_timestep_s"])} s, saved interval {display(settings["saved_state_interval_s"])} s, seed {settings["seed"]}, configured horizon {display(settings["duration_s"])} s. Run {run_id}. Solver/model configuration is bound without inventing intermediate states.'
            claim("numerical_method", method, sb)
            step("saved_numerical_procedure", method, sb)
            rule_bindings = tb + rb
            if target["answer_type"] == "boolean":
                # Rule/event history and implementation are indispensable for cumulative/duration predicates.
                rule_bindings += [binding(root, namespace, "/reference/events", run_id=run_id), binding(root, "context", "/implementation/"+("engines" if inp["domain"] in ("robotic_arm","tethered_load") else "bullet"))]
                rule = target["rule_definition"]
                text = f'Saved Boolean {display(label["value"])} uses rule: {rule} The simulator evaluates the declared predicate on integration steps. Historical/duration flags use the recorded event history and saved accumulator/duration flag, not a terminal instantaneous speed, angle or contact. Saved observations do not expose every integration substep; this procedure cites the simulator flag and admission rather than inventing a substep reconstruction.'
                claim("boolean_rule", text, rule_bindings)
            else:
                text = f'Locate exact saved timestamp {display(target["end_time"])} s and channel {target["entity_id"]}/{target["quantity"]}; use its declared measurement frame, without resampling.'
            step("locate_saved_state_or_rule", text, rule_bindings)
            claim("readout", answer, rb+tb)
            step("extract_exact_answer", answer + ' Structured readout retains full source precision; display rounding is only for prose.', rb+tb)
            if cf:
                factual, fb, _ = readout(root, "factual", target, context["runs"]["original-coarse"]["run_id"])
                comp = comparison(factual["value"], measured["value"], target)
                ctext = f'Matched factual value {display(factual["value"])} {target["unit"]}; omission value {display(measured["value"])} {target["unit"]}. Exact canonical equality: {comp["exact_canonical_equality"]}. '
                if comp["rotation_angle_rad"] is not None:
                    ctext += f'Sign-invariant orientation difference: {display(comp["rotation_angle_rad"])} rad. '
                if comp["alternative_minus_factual"] is not None:
                    ctext += f'Alternative minus factual: {display(comp["alternative_minus_factual"])} {target["unit"]}; scorer error {display(comp["scorer_error"])} {comp["scorer_error_unit"]}. '
                ctext += f'Factual answer passes the alternative scorer: {comp["factual_answer_passes_alternative_scorer"]}. {comp["interpretation_limit"]} This comparison concerns the matched omission in the stated simulator; it does not identify an additional physical mechanism.'
                short = f'Matched factual: {display(factual["value"])} {target["unit"]}. '
                if comp["rotation_angle_rad"] is not None:
                    short += f'Sign-invariant orientation difference: {display(comp["rotation_angle_rad"])} rad. '
                elif comp["alternative_minus_factual"] is not None:
                    short += f'Alternative minus factual: {display(comp["alternative_minus_factual"])} {target["unit"]}. '
                else:
                    short += 'The saved Boolean is unchanged. ' if comp["exact_canonical_equality"] else 'The saved Boolean differs. '
                short += comp["interpretation_limit"]
                claim("matched_comparison", short, rb+fb+tb)
            else:
                # Case-specific change, without claiming its cause from timing.
                matches = [(j,m) for j,m in enumerate(initial["measurements"]) if (m["entity_id"],m["name"])==(target["entity_id"],target["quantity"])]
                if matches and target["answer_type"] != "boolean":
                    j, before = matches[0]
                    if (before["unit"], before["frame"]) != (measured["unit"],measured["frame"]):
                        raise ValueError("initial/readout frame mismatch")
                    change = comparison(before["value"], measured["value"], target)
                    delta = change["alternative_minus_factual"]
                    db = [binding(root, "public", f"/states/0/measurements/{j}", state_id=initial["state_id"]), binding(root,"public","/states/0/timestamp",state_id=initial["state_id"])]
                    if change["rotation_angle_rad"] is not None:
                        change_text = f'From the observed orientation at {display(initial["timestamp"])} s, the sign-invariant rotation-angle change is {display(change["rotation_angle_rad"])} rad.'
                    else:
                        change_text = f'Initial observed value at {display(initial["timestamp"])} s: {display(before["value"])} {target["unit"]}; saved change: {display(delta)} {target["unit"]}.'
                    claim("observed_to_saved_change", change_text + ' This simulated change does not establish causation from timing alone.', db+rb)
            vb = [binding(root, "context", "/verification")]
            if cf:
                vb.append(binding(root, "pair", "/verification"))
            summary = ('Original canonical exact replay and independent original/alternative coarse-fine admission passed.' if cf else
                       'Stored source admission passed; '+('the matched SPQ02 factual replay and coarse-fine checks also passed.' if context.get("runs") else 'no additional exact factual replay was performed for this development trajectory.'))
            claim("verification_limit", summary + ' Numerical checks do not assess human explanation quality.', vb)
            step("verification_and_comparison", summary + (' '+ctext if cf else ' Use the saved numerical result under the declared model; do not replace it with generated prose.'), vb + (rb+fb+tb if cf else rb))
            verification = {"status": "saved_numerical_evidence_checked", "readout_equals_gold": True,
                            "exact_factual_replay": bool(context.get("runs")), "bindings": vb+rb,
                            "admission_source": "saved_receipts_and_source_metadata", "human_assessment": "unreviewed"}
        # Concise prose is assembled only from these explicitly bound claims.
        result_text = f'{target["entity_id"]} {target["quantity"]} at {display(target["end_time"])} s: {display(label["value"])} {target["unit"]} ({target["frame"]}).'
        claim("concise_readout", result_text, rb+tb)
        prose_kinds = ["concise_readout"]
        if typ == "direct":
            claim("direct_interpretation", 'This observed channel determines the answer directly; no interpolation or future simulation is required.', rb+tb)
            prose_kinds.append("direct_interpretation")
        elif target["answer_type"] == "boolean":
            claim("concise_boolean_rule", f'Saved flag follows the rule: {target["rule_definition"]} Historical/duration predicates use recorded history, not just an instantaneous endpoint.', rule_bindings)
            prose_kinds.append("concise_boolean_rule")
        if comp is not None:
            prose_kinds.append("matched_comparison")
        elif any(c["kind"] == "observed_to_saved_change" for c in claims):
            prose_kinds.append("observed_to_saved_change")
        concise = " ".join(next(c["text"] for c in claims if c["kind"] == k) for k in prose_kinds)
        targets.append({"target_id": target["target_id"], "target": deepcopy(target), "state_id": state_id,
                        "run_id": run_id, "value": deepcopy(label["value"]), "claims": claims,
                        "comparison": comp, "explanation": concise, "explanation_claim_kinds": prose_kinds,
                        "solution_trace": {"status": "evidence_checked_human_unreviewed", "steps": steps,
                                           "verification_record": verification}})
    raw = deepcopy(record); raw["private"].pop("answer_annotation", None)
    return {"version": VERSION, "versions": versions(), "kind": {"direct":"observed_evidence_readout", "predictive":"saved_numerical_prediction", "counterfactual":"matched_omission_numerical_comparison"}[typ],
            "status": "automatically_checked_human_unreviewed", "parent_record_sha256": digest(raw),
            "cache_identity": digest({"record": raw, "context": context, "versions": versions()}),
            "evidence_context": deepcopy(context), "shared_claims": shared_claims, "targets": targets,
            "future_family_contracts": {"explanation": "supported claims, their evidence and steps connecting evidence to the answer",
                "clarification": "genuine information gap; demonstrate underdetermination and why requested information resolves it; no unique numerical answer before supply"}}

def validate_answer_annotation(record):
    annotation = record["private"]["answer_annotation"]
    Draft202012Validator(read(Path(__file__).with_name("answer_annotation.schema.json"))).validate(annotation)
    context = annotation["evidence_context"]
    for entry in context.get("implementation", {}).values():
        if sha256(entry["text"].encode()).hexdigest() != entry["sha256"]:
            raise ValueError("implementation evidence hash differs")
    root = roots(record, context)
    for part in annotation["shared_claims"]:
        if not part["bindings"] or not part["text"].strip():
            raise ValueError("unsupported shared explanation statement")
        for b in part["bindings"]:
            if b["value_sha256"] != digest(pointer(root[b["namespace"]], b["pointer"])):
                raise ValueError("unresolved shared answer evidence")
    for target in annotation["targets"]:
        for part in target["claims"] + target["solution_trace"]["steps"]:
            if not part["bindings"] or not part["text"].strip():
                raise ValueError("unsupported explanation/trace statement")
            for b in part["bindings"]:
                if b["value_sha256"] != digest(pointer(root[b["namespace"]], b["pointer"])):
                    raise ValueError("unresolved or changed answer evidence")
    if canonical(annotation) != canonical(render(record, context)):
        raise ValueError("answer explanation/trace/cache differs from grounded deterministic procedure")

def enrich(record, context):
    out = deepcopy(record)
    out["private"]["answer_annotation"] = render(record, context)
    validate_answer_annotation(out)
    return out

def enriched_reference(record):
    result = deepcopy(record["private"]["reference"])
    annotation = record["private"].get("answer_annotation")
    if annotation:
        validate_answer_annotation(record)
        result["explanation_kind"] = annotation["kind"]
        result["explanation"] = "\n\n".join([c["text"] for c in annotation["shared_claims"]] + [t["explanation"] for t in annotation["targets"]])
        result["solution_trace"] = {"status": "evidence_checked_human_unreviewed", "version": VERSION,
            "targets": [{"target_id": t["target_id"], **t["solution_trace"]} for t in annotation["targets"]],
            "verification_record": {"status": "per_target_evidence_checked", "target_verification": [t["solution_trace"]["verification_record"] for t in annotation["targets"]], "human_assessment": "unreviewed"}}
    return result
