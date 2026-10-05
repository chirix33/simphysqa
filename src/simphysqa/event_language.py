"""Versioned deterministic schedule enrichment of validated SPQ01 language.

The generator and validator accept public input/annotations only. Model-generated
measurement claims are preserved verbatim and validated by the original contract.
Schedule and controller claims must equal a deterministic public reconstruction.
"""
from copy import deepcopy
from hashlib import sha256
from pathlib import Path
from jsonschema import Draft202012Validator
from .annotation import validate_generated
from .dataset import pointer
from .events import derive, signatures
from .io import digest, read

CONTRACT = "simphysqa-event-language/2.0.0"
PROMPT_VERSION = "simphysqa-event-context-prompt/2.0.0"
PROMPT = """Describe only observed states and declared events/controllers. Use derived half-open schedule links, not nearest timestamps. Keep direct targets separate from contextual entities. Scheduled active is not verified applied. Preserve additive versus total control, limits versus realized values, and supported controller phases. Bind measurement, schedule and controller claims separately. Describe declared future interventions once in the summary and briefly at the last observed timestamp; never describe realized future outcomes or infer causation from timing. No private reference inputs, invented boundary states, or executed equations."""

def versions():
    return {"annotation_contract_version": CONTRACT, "prompt_version": PROMPT_VERSION,
            "prompt_sha256": digest(PROMPT),
            "annotation_schema_sha256": sha256(Path(__file__).with_name("event_language.schema.json").read_text(encoding="utf-8").encode()).hexdigest(),
            "renderer_sha256": sha256(Path(__file__).read_text(encoding="utf-8").encode()).hexdigest(), **signatures()}

def generator_input(inp):
    # Whole state/entity/controller information; no question answers/private fields.
    return {"versions": versions(), "instructions": PROMPT,
            "public_input": {k: deepcopy(inp[k]) for k in ("domain", "entities", "states", "known_events", "controller", "coordinate_convention", "observation_cutoff")},
            "derived_event_context": derive(inp)}

def identity(inp, base):
    return digest({"versions": versions(), "generator_input": generator_input(inp),
                   "measurement_annotations_sha256": digest(base)})

def claim(kind, text, bindings, link_ids=()):
    value = {"kind": kind, "text": text, "bindings": list(bindings) if kind == "measurement" else sorted(set(bindings)), "link_ids": list(link_ids)}
    return {"claim_id": kind + "-" + digest(value)[:20], **value}

def compose(base, extra):
    result = deepcopy(base)
    measured = claim("measurement", base["text"], base["bindings"])
    result["claims"] = [measured] + extra
    result["text"] = " ".join(c["text"] for c in result["claims"])
    result["bindings"] = sorted({b for c in result["claims"] for b in c["bindings"]})
    return result

def render(inp, base):
    # Old contract checks only the original measurement language, including units,
    # timestamps and unsupported outcomes. Revised schedule prose has its own rules.
    checked = validate_generated({"public": {"input": inp}}, {
        "summary": {k: v for k, v in base["trajectory"].items() if k != "status"},
        "timestamps": [{k: v for k, v in s.items() if k != "status"} for s in base["timestamps"]]})
    if checked != base:
        raise ValueError("event enrichment requires unreviewed original measurement annotations")
    context = derive(inp)
    summary = []
    cutoff = inp["observation_cutoff"]
    for event in context["events"]:
        eid = event["event_id"]
        targets = ", ".join(event["target_entity_ids"]) or "no declared intervention target"
        related = [link for link in context["state_links"] if link["event_id"] == eid]
        active = [link for link in related if link["temporal_relationship"] == "scheduled_active"]
        first, last = related[0], related[-1]
        if event["temporal_semantics"] == "half_open_interval":
            text = f'Declared intervention {eid} targets {targets} on [{event["start_time"]}, {event["end_time"]}) s.'
            if last["temporal_relationship"] == "scheduled_future":
                text += f' It is scheduled future, not yet started at the {cutoff} s observation cutoff; no saved observed state has active overlap.'
            elif active:
                text += " It is scheduled active at " + ", ".join(str(v["timestamp"]) + " s" for v in active) + "; timing does not verify application or establish a cause of measured change."
            elif last["temporal_relationship"] == "scheduled_empty_interval":
                text += " The scheduled interval is empty; it has no active timestamp."
            elif context["between_state_links"] and any(b["event_id"] == eid for b in context["between_state_links"]):
                text += " There is no endpoint-active saved state; intervening schedule links are reported separately."
            else:
                text += " Its scheduled interval ended before the saved observations; physical effects are not determined by interval timing."
        elif event["temporal_semantics"] == "declared_point":
            text = f'Declared point event {eid}: {event["point_definition"]} at {event["start_time"]} s; a point event is not an active intervention interval.'
        else:
            text = f'Public event {eid} has unresolved temporal semantics; no active-interval or phase claim is made.'
        summary.append(claim("event_schedule", text, event["bindings"] + ["/observation_cutoff"] + [f"/states/{i}/timestamp" for i in range(len(inp["states"]))], [v["link_id"] for v in related]))
        for value in event["controller"]["claims"]:
            summary.append(claim("controller_definition", value["text"], value["bindings"]))
    times = []
    for i, sentence in enumerate(base["timestamps"]):
        extra = []
        state_id = sentence["state_id"]
        for link in (v for v in context["state_links"] if v["state_id"] == state_id):
            event = next(e for e in context["events"] if e["event_id"] == link["event_id"])
            eid = event["event_id"]
            relation = link["temporal_relationship"]
            targets = ", ".join(link["target_entity_ids"])
            if relation == "scheduled_active":
                extra.append(claim("event_schedule", f'At this saved timestamp, intervention {eid} is scheduled active on {targets}; application and causation are not verified by timing.', link["bindings"], [link["link_id"]]))
                phase = next((p for p in event["controller"]["phases"] if p["phase_id"] == link["scheduled_phase_id"]), None)
                if phase:
                    extra.append(claim("controller_phase", f'Scheduled active phase: {phase["target_entity_ids"][0]} {phase["quantity"]} {phase["value"]} {phase["unit"]} in {phase["frame"]}, on [{phase["start_time_decimal"]}, {phase["end_time_decimal"]}) s; this is declared control, not verified application.', phase["bindings"] + [f"/states/{i}/timestamp"], [link["link_id"]]))
                else:
                    for value in event["controller"]["claims"]:
                        extra.append(claim("controller_definition", value["text"], value["bindings"], [link["link_id"]]))
            elif relation == "scheduled_future" and i == len(base["timestamps"]) - 1:
                extra.append(claim("event_schedule", f'Declared intervention {eid} on {targets} has not yet started at this observed timestamp.', link["bindings"], [link["link_id"]]))
            elif relation == "scheduled_interval_ended":
                prior = next((v for v in context["state_links"] if i > 0 and v["event_id"] == eid and v["state_id"] == base["timestamps"][i - 1]["state_id"]), None)
                if prior is None or prior["temporal_relationship"] != relation:
                    extra.append(claim("event_schedule", f'The scheduled interval for intervention {eid} has ended; this does not establish that its physical effects have ended.', link["bindings"], [link["link_id"]]))
            elif relation == "declared_point_at_timestamp":
                extra.append(claim("event_schedule", f'Declared point event {eid} is at this timestamp: {event["point_definition"]}; it is not an active interval.', link["bindings"], [link["link_id"]]))
            elif relation == "temporal_semantics_unresolved" and i == len(base["timestamps"]) - 1:
                extra.append(claim("event_schedule", f'Event {eid} has unresolved temporal semantics; active status is not inferred.', link["bindings"], [link["link_id"]]))
        for link in (v for v in context["between_state_links"] if v["state_id"] == state_id):
            if link["temporal_relationship"] == "interval_between_saved_states":
                segment = link["scheduled_overlap"]
                text = f'Between the preceding saved state and this one, intervention {link["event_id"]} has scheduled interval overlap [{segment[0]}, {segment[1]}) s; this is separate from endpoint-active status.'
            else:
                text = f'Declared point event {link["event_id"]} falls between the preceding saved state and this one, not at either endpoint.'
            if link["boundaries"]:
                text += " Unsampled declared boundaries: " + ", ".join(b["kind"] + " at " + str(b["timestamp"]) + " s" for b in link["boundaries"]) + "; no boundary state is invented."
            extra.append(claim("between_saved_states", text, link["bindings"], [link["link_id"]]))
        times.append(compose(sentence, extra))
    return {"trajectory": compose(base["trajectory"], summary), "timestamps": times,
            "event_context": {"versions": versions(), "cache_identity": identity(inp, base),
                              "measurement_annotations_sha256": digest(base), "links": context}}

def measurement_base(language):
    def recover(sentence):
        if not sentence.get("claims") or sentence["claims"][0]["kind"] != "measurement":
            raise ValueError("missing original measurement claim")
        c = sentence["claims"][0]
        value = {k: deepcopy(v) for k, v in sentence.items() if k in ("status", "state_id", "timestamp")}
        value.update(text=c["text"], bindings=deepcopy(c["bindings"]))
        return value
    return {"trajectory": recover(language["trajectory"]), "timestamps": [recover(s) for s in language["timestamps"]]}

def validate_view(inp, language, annotation_version):
    if annotation_version != CONTRACT:
        raise ValueError("event annotation contract version mismatch")
    Draft202012Validator(read(Path(__file__).with_name("event_language.schema.json"))).validate(language)
    for sentence in [language["trajectory"]] + language["timestamps"]:
        for c in sentence["claims"]:
            for b in c["bindings"]:
                pointer(inp, b)
    base = measurement_base(language)
    expected = render(inp, base)
    if language != expected:
        raise ValueError("event annotation differs from grounded deterministic public reconstruction")

def enrich(record):
    if record["annotation_version"] == CONTRACT or "event_context" in record["public"]["annotations"]:
        raise ValueError("already enriched; use original SPQ01 record/cache to resume")
    result = deepcopy(record)
    inp = record["public"]["input"]
    base = record["public"]["annotations"]
    result["annotation_version"] = CONTRACT
    result["public"]["annotations"] = render(inp, base)
    revision = {**versions(), "method": "deterministic_schedule_enrichment_of_existing_model_language",
                "source_annotation_version": record["annotation_version"],
                "source_annotation_sha256": digest(base), "source_record_sha256": digest(record),
                "cache_identity": identity(inp, base), "new_model_requests": 0, "new_attempts": 0,
                "new_estimated_spend_usd": 0, "human_assessment": "pending"}
    # Preserve original provider identity/settings/attempts verbatim; revision has
    # distinct deterministic provenance and never pretends to be a new model run.
    result["private"].setdefault("generation_job", {})["event_enrichment"] = revision
    validate_view(inp, result["public"]["annotations"], CONTRACT)
    return result
