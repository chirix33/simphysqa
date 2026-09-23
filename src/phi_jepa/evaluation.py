"""External numerical predictions only. No models, LLM answers, or physics oracle calls."""
from dataclasses import asdict
from hashlib import sha256
from math import isfinite, sqrt
from pathlib import Path
from .artifacts import code_provenance, digest, environment, read_run, write_run
from .benchmarks.physical_checks import CHECK_NAMES, passive_checks
from .contracts import PhysicalPrediction, ScenarioInput
from .data import EvaluationTruth, TargetScaler, TrainingExample, fit_scaler
from .validation import convert, load_json


def checked_dataset(payloads: dict):
    inputs = [ScenarioInput.from_dict(row) for row in payloads["inputs.json"]]
    truths = tuple(convert(EvaluationTruth, row) for row in payloads["truths.json"])
    scenarios = {s.scenario_id: s for s in inputs}
    targets = {t.scenario_id: t for t in truths}
    if len(scenarios) != len(inputs) or len(targets) != len(truths) or scenarios.keys() != targets.keys():
        raise ValueError("duplicate or unmatched dataset identities")
    for key, scenario in scenarios.items():
        truth = targets[key]
        if (scenario.family_id != truth.family_id or scenario.initial_time != 0 or scenario.horizon != truth.times[-1]
                or tuple(o.quantity_id for o in scenario.observables) != truth.observable_ids
                or tuple(o.unit for o in scenario.observables) != truth.units
                or tuple(o.frame for o in scenario.observables) != truth.frames):
            raise ValueError("dataset input/truth metadata mismatch")
    scaler = convert(TargetScaler, payloads["scaler.json"])
    recomputed = fit_scaler(tuple(TrainingExample(scenarios[t.scenario_id], t) for t in truths if t.split == "train"))
    if scaler != recomputed:
        raise ValueError("scaler is not fitted solely to supplied training terminals")
    return scenarios, targets, scaler


def prediction_map(envelope: dict, ids: set[str]) -> tuple[str, dict]:
    if type(envelope) is not dict or set(envelope) != {"producer", "predictions"} or type(envelope["producer"]) is not str or not envelope["producer"].strip() or type(envelope["predictions"]) is not list:
        raise ValueError("prediction file requires producer and predictions array only")
    rows = {}
    for row in envelope["predictions"]:
        if type(row) is not dict or type(row.get("scenario_id")) is not str or row["scenario_id"] not in ids:
            raise ValueError("unknown or absent prediction scenario_id")
        if row["scenario_id"] in rows:
            raise ValueError("duplicate prediction scenario_id")
        rows[row["scenario_id"]] = row
    return envelope["producer"], rows


def trajectory_error(prediction: PhysicalPrediction, truth: EvaluationTruth) -> tuple[str, list | None]:
    if prediction.times is None and prediction.trajectory is None:
        return "not_supplied", None
    if (prediction.times != truth.times or prediction.trajectory is None or len(prediction.trajectory) != len(truth.times)
            or any(len(row) != len(truth.terminal) for row in prediction.trajectory)
            or prediction.trajectory[-1] != prediction.values):
        return "invalid_grid_dimensions_or_terminal", None
    try:
        errors = [[(a - b)**2 for a, b in zip(row, ref)] for row, ref in zip(prediction.trajectory, truth.trajectory)]
        if not all(isfinite(value) for row in errors for value in row):
            raise ValueError("nonfinite derived error")
        return "valid", errors
    except (ValueError, OverflowError):
        return "invalid_numerical_error", None


def summarize(records: list[dict], scaler: TargetScaler) -> dict:
    valid = [row for row in records if row["status"] == "valid"]
    count, total = len(valid), len(records)
    width = len(scaler.observable_ids)
    errors = {}
    mse = []
    for i, name in enumerate(scaler.observable_ids):
        coordinate_mse = sum(row["squared_error"][i] / count for row in valid) if count else None
        errors[name] = {"unit": scaler.units[i], "valid_denominator": count,
                        "rmse": sqrt(coordinate_mse) if count else None,
                        "mae": sum(abs(row["signed_error"][i]) / count for row in valid) if count else None}
        if count:
            mse.append(coordinate_mse / scaler.scales[i]**2)
    normalized = sum(mse) / width if count else None
    checks = [check for row in records for check in row["physical_checks"]]
    evaluated = len(checks)
    eligible = sum(row["eligible_checks"] for row in records)
    unsupported = sum(row["unsupported_checks"] for row in records)
    violations = sum(check["violated"] for check in checks)
    families = {}
    for row in records:
        if row["physical_checks"]:
            families.setdefault(row["family_id"], []).extend(row["physical_checks"])
    family_rates = [sum(c["violated"] for c in checks) / len(checks) for checks in families.values()]
    trajectories = [row["trajectory_squared_errors"] for row in records if row["trajectory_status"] == "valid"]
    trajectory_points = sum(len(rows) for rows in trajectories)
    trajectory_rmse = {name: sqrt(sum(row[i] / trajectory_points for rows in trajectories for row in rows)) if trajectory_points else None
                       for i, name in enumerate(scaler.observable_ids)}
    return {"expected_predictions": total, "valid_predictions": count, "missing_predictions": sum(r["status"] == "missing" for r in records),
            "invalid_predictions": sum(r["status"] == "invalid" for r in records), "failed_predictions": total - count,
            "valid_prediction_coverage": count / total if total else None, "endpoint_errors_valid_only": errors,
            "train_normalized_macro_mse_valid_only": normalized, "train_normalized_macro_rmse_valid_only": sqrt(normalized) if normalized is not None else None,
            "pcvr": {"violation_numerator": violations, "evaluated_denominator": evaluated,
                     "ratio": violations / evaluated if evaluated else None, "eligible_checks": eligible,
                     "evaluated_checks": evaluated, "unsupported_checks": unsupported,
                     "unevaluated_eligible_checks": eligible - evaluated, "coverage": evaluated / eligible if eligible else None,
                     "failed_samples": sum(any(c["violated"] for c in row["physical_checks"]) for row in records),
                     "family_macro_ratio": sum(family_rates) / len(family_rates) if family_rates else None,
                     "evaluated_families": len(family_rates), "expected_families": len({r["family_id"] for r in records}),
                     "checks": {name: {"violated": sum(c["violated"] for c in checks if c["name"] == name),
                                       "evaluated": sum(c["name"] == name for c in checks)} for name in CHECK_NAMES}},
            "trajectory": {"supplied": sum(r["trajectory_status"] != "not_supplied" for r in records),
                           "valid": len(trajectories), "invalid_or_unusable": sum(r["trajectory_status"] not in ("valid", "not_supplied") for r in records),
                           "expected_samples": total, "coverage": len(trajectories) / total if total else None,
                           "timepoint_denominator": trajectory_points, "rmse_physical_units": trajectory_rmse},
            "provenance_schema": {"prediction_schema_valid": count, "expected": total,
                                  "interpretation": "numerical envelope compatibility only; not physical compliance or LLM extraction quality"}}


def evaluate(payloads: dict, envelope: dict) -> dict:
    scenarios, truths, scaler = checked_dataset(payloads)
    producer, predictions = prediction_map(envelope, set(scenarios))
    records = []
    for scenario_id, scenario in scenarios.items():
        truth = truths[scenario_id]
        supported = passive_checks(scenario, (0.0, 0.0)) is not None
        record = {"scenario_id": scenario_id, "family_id": scenario.family_id, "split": truth.split,
                  "status": "missing", "reason": "prediction_absent", "physical_checks": [],
                  "eligible_checks": len(CHECK_NAMES) if supported else 0, "unsupported_checks": 0 if supported else len(CHECK_NAMES),
                  "trajectory_status": "not_supplied", "trajectory_squared_errors": None}
        raw = predictions.get(scenario_id)
        if raw is not None:
            if raw.get("trajectory") is not None or raw.get("times") is not None:
                record["trajectory_status"] = "invalid_prediction"
            try:
                prediction = convert(PhysicalPrediction, raw)
                if (prediction.observable_ids != truth.observable_ids or prediction.units != truth.units or prediction.frames != truth.frames
                        or prediction.observable_names != tuple(o.name for o in scenario.observables) or prediction.time != truth.times[-1]):
                    raise ValueError("observable order/names/units/frame/time mismatch")
                signed = [a - b for a, b in zip(prediction.values, truth.terminal)]
                squared = [value**2 for value in signed]
                if not all(isfinite(value) for value in (*signed, *squared, *(s / scale**2 for s, scale in zip(squared, scaler.scales)))):
                    raise ValueError("nonfinite derived endpoint error")
                checks = passive_checks(scenario, prediction.values) or []
                if any(not isfinite(c["excess"]) for c in checks):
                    raise ValueError("nonfinite physical-check calculation")
                trajectory_status, trajectory_squared = trajectory_error(prediction, truth)
                record.update(status="valid", reason=None, signed_error=signed, squared_error=squared,
                              physical_checks=checks, trajectory_status=trajectory_status, trajectory_squared_errors=trajectory_squared)
            except (ValueError, OverflowError) as exc:
                record.update(status="invalid", reason=str(exc))
        records.append(record)
    return {"producer": producer, "fixture_only": payloads["generation.json"]["fixture_only"],
            "interpretation": "evaluator verification, not Phi-JEPA performance" if "fixture" in producer else "external numerical predictions; no model executed",
            "scaler_sha256": digest(asdict(scaler)), "overall": summarize(records, scaler),
            "by_split": {split: summarize([r for r in records if r["split"] == split], scaler) for split in payloads["partitions.json"]},
            "records": records, "usage": {"model_calls": 0, "solves": 0, "retries": 0}}


def evaluate_run(dataset: Path, predictions: Path, output: Path) -> Path:
    payloads, _ = read_run(dataset)
    report = evaluate(payloads, load_json(predictions))
    return write_run(output, {"metrics.json": report}, {"phase": "P01", "fixture_only": report["fixture_only"],
                     "dataset_manifest_sha256": dataset.name, "prediction_file_sha256": sha256(predictions.read_bytes()).hexdigest(),
                     "producer": report["producer"], "code": code_provenance(), "environment": environment(), "usage": report["usage"]})
