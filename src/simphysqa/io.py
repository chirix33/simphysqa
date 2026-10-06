"""Strict JSON and explicit external artifact roots; no network."""
from __future__ import annotations
from hashlib import sha256
import json
import os
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[2]
DOMAINS = ("robotic_arm", "driving", "object_pushing_stacking", "tethered_load")
QUESTION_TYPES = ("direct", "predictive", "counterfactual", "explanation", "clarification")

def canonical(value: Any) -> bytes:
    return (json.dumps(value, sort_keys=True, ensure_ascii=False, separators=(",", ":"), allow_nan=False) + "\n").encode()

def digest(value: Any) -> str:
    return sha256(canonical(value)).hexdigest()

def read(path: Path | str) -> Any:
    def bad(value):
        raise ValueError("nonfinite JSON: " + value)
    def pairs(values):
        result = {}
        for key, value in values:
            if key in result:
                raise ValueError("duplicate JSON key: " + key)
            result[key] = value
        return result
    return json.loads(Path(path).read_text(encoding="utf-8-sig"), parse_constant=bad, object_pairs_hook=pairs)

def parse(line: str) -> Any:
    # Reuse the same strict decoder without opening a file.
    def bad(value):
        raise ValueError("nonfinite JSON: " + value)
    def pairs(values):
        out = {}
        for k, v in values:
            if k in out:
                raise ValueError("duplicate JSON key: " + k)
            out[k] = v
        return out
    return json.loads(line, parse_constant=bad, object_pairs_hook=pairs)

def external(path: Path | str) -> Path:
    result = Path(path).expanduser().resolve()
    if result == ROOT or ROOT in result.parents:
        raise ValueError("new data/caches/outputs must be outside the source worktree")
    return result

def output_root(path: Path | None) -> Path:
    value = path or os.environ.get("SIMPHYSQA_OUTPUT_ROOT")
    if not value:
        raise ValueError("set --output or SIMPHYSQA_OUTPUT_ROOT to an external path")
    return external(value)

def write(path: Path, value: Any) -> None:
    path = external(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("xb") as stream:
        stream.write(canonical(value))

def manifest(folder: Path, details: dict) -> dict:
    files = {p.relative_to(folder).as_posix(): sha256(p.read_bytes()).hexdigest()
             for p in sorted(folder.rglob("*")) if p.is_file() and p.name != "manifest.json"}
    result = {"manifest_version": "simphysqa-manifest/0.1.0", **details, "files": files}
    write(folder / "manifest.json", result)
    return result
