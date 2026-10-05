"""Lossless v1 migration. References stay private; language completion stays explicit."""
from __future__ import annotations
from copy import deepcopy
from dataclasses import dataclass
from hashlib import sha256
from pathlib import Path
from typing import Iterator
from jsonschema import Draft202012Validator
from phi_jepa.simulation.validation import validate as validate_source
from .io import DOMAINS, QUESTION_TYPES, canonical, digest, parse, read

VERSION = "simphysqa/0.1.0"

@dataclass(frozen=True)
class SourceLocation:
    path: str
    line: int
    file_sha256: str

def iter_source(path: Path) -> Iterator[tuple[dict, SourceLocation]]:
    files = sorted((path / "shards").glob("*.jsonl")) if path.is_dir() else [path]
    if not files:
        raise ValueError("no source shards: " + str(path))
    for file in files:
        file_hash = sha256(file.read_bytes()).hexdigest()
        with file.open(encoding="utf-8-sig") as stream:
            for number, line in enumerate(stream, 1):
                if line.strip():
                    yield parse(line), SourceLocation(str(file.resolve()), number, file_hash)

def restore(record: dict) -> dict:
    if record["question_type"] in ("direct", "counterfactual"):
        return deepcopy(record["private"]["source_record"])
    return {"schema_version": record["source_schema_version"], "sample_id": record["sample_id"],
            "input": deepcopy(record["public"]["input"]),
            "reference": deepcopy(record["private"]["reference"]),
            "metadata": deepcopy(record["private"]["metadata"])}

def migrate(source: dict, location: SourceLocation) -> dict:
    validate_source(source, admission=True)
    if source["input"]["domain"] not in DOMAINS:
        raise ValueError("domain outside current release")
    if source["input"]["task_type"] != "future_state_prediction":
        raise ValueError("unsupported legacy task; never infer a new QA family")
    bindings = []
    for target in source["input"]["answer_spec"]:
        state = next(s for s in source["reference"]["states"] if s["timestamp"] == target["end_time"])
        supports = [e["evidence_id"] for e in source["reference"]["evidence"] if state["state_id"] in e["state_ids"]]
        bindings.append({"target_id": target["target_id"], "kind": "recorded_readout",
                         "state_ids": [state["state_id"]], "event_ids": [], "evidence_ids": supports})
    result = {"schema_version": VERSION, "source_schema_version": source["schema_version"],
              "sample_id": source["sample_id"], "trajectory_id": source["metadata"]["base_scenario_id"],
              "question_type": "predictive", "annotation_version": "legacy-unenriched/0",
              "source": {"path": location.path, "line": location.line, "file_sha256": location.file_sha256,
                         "record_sha256": digest(source)},
              "public": {"input": deepcopy(source["input"]),
                         "annotations": {"trajectory": {"status": "pending", "text": None, "bindings": []},
                                         "timestamps": []}},
              "private": {"reference": deepcopy(source["reference"]), "metadata": deepcopy(source["metadata"]),
                          "evidence_bindings": bindings,
                          "annotation_provenance": {"status": "legacy_import", "model_identity": None,
                              "prompt_version": None, "schema_version": source["schema_version"],
                              "generation_settings": {}, "validation_failures": [], "attempts": [],
                              "retries": 0, "repairs": 0}},
              "completion": {"trajectory_description": "pending", "timestamp_descriptions": "pending",
                             "direct_qa": "pending", "predictive_qa": "existing_simulator_reference",
                             "counterfactual_qa": "pending_matched_intervention",
                             "explanation_qa": "pending_claim_evidence",
                             "clarification_qa": "pending_information_gap",
                             "evidence_bindings": "recorded_readouts_only"}}
    validate(result)
    if restore(result) != source:
        raise ValueError("migration changed source")
    return result

def pointer(root: dict, path: str):
    if not isinstance(path, str) or not path.startswith("/"):
        raise ValueError("evidence binding must be a JSON pointer into public input")
    value = root
    for part in path[1:].split("/"):
        key = part.replace("~1", "/").replace("~0", "~")
        value = value[int(key)] if isinstance(value, list) else value[key]
    return value

def validate(record: dict) -> None:
    canonical(record)
    if record.get("question_type") == "counterfactual" and record.get("schema_version") != "simphysqa/0.3.0":
        raise ValueError("counterfactual QA requires matched alternative evidence, never relabeling")
    Draft202012Validator(read(Path(__file__).with_name("record.schema.json"))).validate(record)
    if record["question_type"] == "counterfactual":
        from .counterfactual import validate_counterfactual
        validate_counterfactual(record)
        return
    source = restore(record)
    validate_source(source, admission=True)
    if record["source"]["record_sha256"] != digest(source):
        raise ValueError("source hash differs; revisions require a separate lineage record")
    if record["trajectory_id"] != source["metadata"]["base_scenario_id"]:
        raise ValueError("trajectory identity changed")
    inp = record["public"]["input"]
    if record["question_type"] == "direct":
        from .direct import validate_direct
        validate_direct(record, source)
    elif record["question_type"] != "predictive" or record["sample_id"] != source["sample_id"]:
        raise ValueError("unsupported family or changed source identity")
    reference = record["private"]["reference"]
    state_ids = {s["state_id"] for s in source["input"]["states"] + source["reference"]["states"]}
    event_ids = {e["event_id"] for e in reference["events"]}
    evidence_ids = {e["evidence_id"] for e in reference["evidence"]}
    bindings = record["private"]["evidence_bindings"]
    if len(bindings) != len(inp["answer_spec"]) or {b["target_id"] for b in bindings} != {t["target_id"] for t in inp["answer_spec"]}:
        raise ValueError("question-specific evidence must cover each target once")
    for binding in bindings:
        if not set(binding["state_ids"]) <= state_ids or not set(binding["event_ids"]) <= event_ids or not set(binding["evidence_ids"]) <= evidence_ids:
            raise ValueError("unresolved private evidence binding")
        target = next(t for t in inp["answer_spec"] if t["target_id"] == binding["target_id"])
        terminal = next(s["state_id"] for s in reference["states"] if s["timestamp"] == target["end_time"])
        if terminal not in binding["state_ids"]:
            raise ValueError("target readout evidence does not bind its requested time")
    language = record["public"]["annotations"]
    for sentence in [language["trajectory"]] + language["timestamps"]:
        if sentence["status"] != "pending" and (not sentence["text"] or not sentence["bindings"]):
            raise ValueError("completed description needs text and public evidence")
        for binding in sentence["bindings"]:
            pointer(inp, binding)
        if sentence["status"] == "pending" and sentence["text"] is not None:
            raise ValueError("pending annotation cannot carry completed text")
        if "state_id" in sentence:
            observed = next((s for s in inp["states"] if s["state_id"] == sentence["state_id"]), None)
            if observed is None or observed["timestamp"] != sentence["timestamp"]:
                raise ValueError("public timestamp annotation references an unobserved state")
    generated = language["trajectory"]["status"] == "generated_unreviewed"
    if "event_context" in language or record["annotation_version"].startswith("simphysqa-event-language/"):
        from .event_language import validate_view
        validate_view(inp, language, record["annotation_version"])
    elif any("claims" in s for s in [language["trajectory"]] + language["timestamps"]):
        raise ValueError("event claims require the revised annotation contract")
    elif generated:
        from .annotation import validate_generated
        validate_generated(record, {"summary": {k: v for k, v in language["trajectory"].items() if k != "status"},
            "timestamps": [{k: v for k, v in s.items() if k != "status"} for s in language["timestamps"]]})

def public_record(record: dict, *, association_version: str | None = None) -> dict:
    validate(record)
    result = {"schema_version": record["schema_version"], "sample_id": record["sample_id"],
            "question_type": record["question_type"], "annotation_version": record["annotation_version"],
            "input": deepcopy(record["public"]["input"]),
            "annotations": deepcopy(record["public"]["annotations"])}
    if association_version is not None:
        from .associations import VERSION, associated_view
        if association_version != VERSION:
            raise ValueError("unsupported association export version")
        return associated_view(result)
    return result

def attach_annotation(record: dict, result: dict) -> dict:
    # A provider integration may supply this contract. No provider calls in this milestone.
    out = deepcopy(record)
    required = {"sample_id", "annotation_version", "annotations", "provenance"}
    if set(result) != required or result["sample_id"] != record["sample_id"]:
        raise ValueError("annotation result identity/fields mismatch")
    provenance = result["provenance"]
    needed = {"status", "model_identity", "prompt_version", "schema_version", "generation_settings",
              "validation_failures", "attempts", "retries", "repairs"}
    if set(provenance) != needed or any(not provenance[k] for k in ("model_identity", "prompt_version", "schema_version", "attempts")):
        raise ValueError("exact generation provenance required")
    if provenance["schema_version"] != VERSION:
        raise ValueError("annotation schema version mismatch")
    if not result["annotation_version"] or result["annotation_version"] == record["annotation_version"]:
        raise ValueError("annotation import needs a new version")
    out["annotation_version"] = result["annotation_version"]
    out["public"]["annotations"] = deepcopy(result["annotations"])
    out["private"]["annotation_provenance"] = deepcopy(provenance)
    out["completion"]["trajectory_description"] = out["public"]["annotations"]["trajectory"]["status"]
    out["completion"]["timestamp_descriptions"] = "generated_unreviewed" if out["public"]["annotations"]["timestamps"] else "pending"
    validate(out)
    return out

def load(path: Path) -> Iterator[dict]:
    seen = set()
    for raw, location in iter_source(path):
        record = raw if raw.get("schema_version") in (VERSION, "simphysqa/0.2.0", "simphysqa/0.3.0") else migrate(raw, location)
        validate(record)
        if record["sample_id"] in seen:
            raise ValueError("duplicate sample ID")
        seen.add(record["sample_id"])
        yield record
