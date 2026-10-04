"""Private scoring of supplied local-model predictions; no inference or oracle tools."""
from __future__ import annotations
from collections import defaultdict
import math
from pathlib import Path
from .dataset import validate
from .io import canonical, digest, external, manifest, write

def distance(value, truth, target):
    kind = target["answer_type"]
    if kind == "boolean":
        if type(value) is not bool:
            raise ValueError("Boolean target requires Boolean")
        return None, value == truth, "1"
    if kind in ("number", "integer"):
        if type(value) not in (int, float) or not math.isfinite(value) or (kind == "integer" and type(value) is not int):
            raise ValueError("invalid numeric value")
        error = abs(value - truth)
        magnitude = abs(truth)
        unit = target["unit"]
    elif kind == "vector":
        if not isinstance(value, list) or len(value) != len(truth) or any(type(v) not in (int, float) or not math.isfinite(v) for v in value):
            raise ValueError("invalid vector value")
        if target["quantity"] == "orientation":
            norm = math.sqrt(sum(v*v for v in value) * sum(v*v for v in truth))
            if norm == 0:
                raise ValueError("zero quaternion")
            error = 2 * math.acos(min(1., abs(sum(a*b for a, b in zip(value, truth))) / norm))
            magnitude, unit = 1., "rad"
        else:
            error = math.sqrt(sum((a-b)**2 for a, b in zip(value, truth)))
            magnitude, unit = math.sqrt(sum(v*v for v in truth)), target["unit"]
    else:
        return None, value == truth, target["unit"]
    tolerance = target["absolute_tolerance"] + target["relative_tolerance"] * magnitude
    return error, error <= tolerance, unit

def score(records: list[dict], predictions: list[dict], condition_ids: list[str]) -> dict:
    if not condition_ids or len(set(condition_ids)) != len(condition_ids):
        raise ValueError("choose distinct configured conditions")
    by_id = {r["sample_id"]: r for r in records}
    if len(by_id) != len(records):
        raise ValueError("duplicate evaluation record")
    for record in records:
        validate(record)
    supplied = {}
    for prediction in predictions:
        canonical(prediction)
        key = (prediction["condition_id"], prediction["sample_id"])
        if key in supplied or key[0] not in condition_ids or key[1] not in by_id:
            raise ValueError("unknown or duplicate prediction identity")
        if prediction["annotation_version"] != by_id[key[1]]["annotation_version"]:
            raise ValueError("prediction evaluated a different annotation version")
        supplied[key] = prediction
    items, channels = [], defaultdict(list)
    for condition in condition_ids:
        for record in records:
            key = (condition, record["sample_id"])
            prediction = supplied.get(key)
            status = "missing" if prediction is None else prediction["status"]
            if status not in ("missing", "completed", "failed", "invalid", "abstained"):
                raise ValueError("unrecognized prediction status")
            raw_targets = prediction.get("targets", []) if prediction else []
            target_ids = [t["target_id"] for t in raw_targets]
            if len(set(target_ids)) != len(target_ids):
                status = "invalid"
            targets = {t["target_id"]: t for t in raw_targets}
            expected = record["public"]["input"]["answer_spec"]
            if not set(targets) <= {t["target_id"] for t in expected}:
                status = "invalid"
            typed, correct, errors = 0, 0, []
            domain = record["public"]["input"]["domain"]
            for target in expected:
                truth = next(v for v in record["private"]["reference"]["structured_label"] if v["target_id"] == target["target_id"])
                candidate = targets.get(target["target_id"]) if status == "completed" else None
                valid, ok, error, metric_unit = False, False, None, "rad" if target["quantity"] == "orientation" else target["unit"]
                if candidate is not None:
                    try:
                        if (candidate["unit"], candidate["frame"]) != (truth["unit"], truth["frame"]):
                            raise ValueError("prediction unit/frame mismatch")
                        error, ok, metric_unit = distance(candidate["value"], truth["value"], target)
                        valid = True
                    except (ValueError, KeyError):
                        pass
                typed += valid
                correct += ok
                entry = {"target_id": target["target_id"], "valid": valid, "correct": ok,
                         "error": error, "metric_unit": metric_unit, "answer_type": target["answer_type"],
                         "frame": target["frame"]}
                errors.append(entry)
                channels[(condition, domain, record["question_type"], target["target_id"], metric_unit, target["frame"])].append(entry)
            items.append({"condition_id": condition, "sample_id": record["sample_id"], "trajectory_id": record["trajectory_id"],
                "domain": domain, "question_type": record["question_type"], "annotation_version": record["annotation_version"],
                "status": status, "expected_targets": len(expected), "valid_targets": typed, "correct_targets": correct,
                "whole_question_correct": typed == correct == len(expected), "targets": errors})
    groups = defaultdict(list)
    for item in items:
        groups[(item["condition_id"], item["domain"], item["question_type"])].append(item)
    tables = []
    for key, values in sorted(groups.items()):
        tables.append({"condition_id": key[0], "domain": key[1], "question_type": key[2],
            "examples": len(values), "trajectories": len({v["trajectory_id"] for v in values}),
            "whole_question_correct": sum(v["whole_question_correct"] for v in values),
            "whole_question_accuracy": sum(v["whole_question_correct"] for v in values) / len(values),
            "expected_targets": sum(v["expected_targets"] for v in values),
            "valid_targets": sum(v["valid_targets"] for v in values),
            "correct_targets": sum(v["correct_targets"] for v in values),
            "status_counts": {s: sum(v["status"] == s for v in values) for s in ("completed", "missing", "failed", "invalid", "abstained")}})
    channel_tables = []
    for key, values in sorted(channels.items()):
        numeric = [v["error"] for v in values if v["valid"] and v["error"] is not None]
        channel_tables.append({"condition_id": key[0], "domain": key[1], "question_type": key[2],
            "target_id": key[3], "metric_unit": key[4], "frame": key[5], "examples": len(values),
            "valid": sum(v["valid"] for v in values), "correct": sum(v["correct"] for v in values),
            "accuracy_all_expected": sum(v["correct"] for v in values) / len(values),
            "numeric_valid_count": len(numeric), "mae_valid_only": sum(numeric)/len(numeric) if numeric else None,
            "rmse_valid_only": math.sqrt(sum(v*v for v in numeric)/len(numeric)) if numeric else None})
    return {"version": "simphysqa-scores/0.1.0", "items": items, "tables": tables, "channel_tables": channel_tables,
            "uncertainty": {"status": "pending_analysis_freeze", "method": "paired physical-trajectory bootstrap",
                            "confidence": None, "replicates": None}, "model_calls": 0,
            "policy": "missing/invalid answers remain failures; valid-only numeric error always paired with coverage"}

def export_scores(records: list[dict], predictions: list[dict], plan: dict, conditions: list[str], output: Path) -> dict:
    known = {c["condition_id"]: c for c in plan["conditions"]}
    if not set(conditions) <= set(known):
        raise ValueError("condition not configured")
    result = score(records, predictions, conditions)
    for table in result["tables"] + result["channel_tables"]:
        table["model_id"] = known[table["condition_id"]]["model_id"]
    output = external(output)
    output.mkdir(parents=True, exist_ok=False)
    write(output / "scores.json", result)
    return manifest(output, {"purpose": "private_supplied_prediction_scoring_no_model_calls", "conditions": conditions,
        "prediction_sha256": digest(predictions),
        "record_hashes": {r["sample_id"]: __import__("simphysqa.io", fromlist=["digest"]).digest(r) for r in records},
        "uncertainty_status": "pending_analysis_freeze"})
