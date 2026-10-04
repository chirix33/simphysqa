"""Tool-free model request export. No simulator or private evidence in requests."""
from pathlib import Path
from .dataset import public_record
from .io import canonical, external, manifest, write

def request(record: dict, condition: dict) -> dict:
    public = public_record(record)
    text = "Answer using the observed structured inputs, public language annotations and declared controls. Return target IDs and typed values in their declared units/frames; abstain if information is insufficient."
    if condition["reasoning"] == "prompted_cot":
        text += " Explain your reasoning before the final answer."
    return {"sample_id": public["sample_id"], "condition_id": condition["condition_id"],
            "tools": [], "messages": [{"role": "user", "content": text + "\n" + canonical(public).decode()}]}

def export_requests(records: list[dict], plan: dict, output: Path) -> dict:
    output = external(output)
    output.mkdir(parents=True, exist_ok=False)
    conditions = plan["conditions"]
    if len({c["condition_id"] for c in conditions}) != len(conditions):
        raise ValueError("duplicate condition")
    for condition in conditions:
        write(output / (condition["condition_id"] + ".json"), [request(r, condition) for r in records])
    return manifest(output, {"purpose": "request_preparation_only_no_model_calls", "conditions": conditions,
        "records": len(records), "annotation_versions": sorted({r["annotation_version"] for r in records}),
        "result_dimensions": ["model", "condition", "domain", "question_type"],
        "result_status": "pending", "scoring": "private references remain in separate evaluator storage"})
