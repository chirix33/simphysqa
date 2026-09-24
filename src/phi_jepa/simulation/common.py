"""Shared deterministic records and explicit engine boundaries."""
from __future__ import annotations
from dataclasses import dataclass
from pathlib import Path
from typing import Protocol
import copy
import json
import math
from phi_jepa.artifacts import canonical, digest

ROOT = Path(__file__).resolve().parents[3]

def read(path):
    return json.loads(Path(path).read_text(encoding="utf-8"))

def write(path, value):
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_bytes(canonical(value))

def quantity(entity, name, value, unit="1", frame="world"):
    return dict(entity_id=entity, name=name, value=value, unit=unit, frame=frame)

def opaque(*parts):
    return digest(parts)[:32]

def grid_index(time, dt):
    value = time / dt
    if not math.isfinite(value) or time < 0 or abs(value-round(value)) > 1e-8:
        raise ValueError(f"time {time} is not on integration grid {dt}")
    return round(value)

def event_active(step,dt,start,end):
    return grid_index(start,dt)<=step<grid_index(end,dt)

def public_record(record):
    return copy.deepcopy({k: record[k] for k in ("schema_version", "sample_id", "input")})

@dataclass(frozen=True)
class Scenario:
    domain: str
    seed: int
    group: str
    split: str
    shift: str
    subfamily: str
    parameters: dict
    event_start: float

@dataclass
class Rollout:
    states: list[dict]
    events: list[dict]
    public: dict
    asset: str
    asset_format: str
    engine: str
    version: str
    diagnostics: dict

class EngineAdapter(Protocol):
    def simulate(self, scenario: Scenario, config: dict, dt: float) -> Rollout: ...
