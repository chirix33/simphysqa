"""Truth/partition/scaler contracts. This module contains no benchmark dynamics."""
from dataclasses import asdict, dataclass
from math import sqrt
from typing import Literal
from .artifacts import digest
from .contracts import ScenarioInput
from .validation import StrictFrozen

Split = Literal["train", "selection", "calibration", "id_test", "parameter_low", "parameter_high", "combination", "event"]


@dataclass(frozen=True)
class EvaluationTruth(StrictFrozen):
    scenario_id: str
    family_id: str
    split: Split
    ood_type: Literal["id", "parameter_low", "parameter_high", "combination", "event"]
    observable_ids: tuple[str, ...]
    units: tuple[str, ...]
    frames: tuple[str, ...]
    times: tuple[float, ...]
    trajectory: tuple[tuple[float, ...], ...]
    terminal: tuple[float, ...]

    def __post_init__(self):
        super().__post_init__()
        width = len(self.observable_ids)
        if not width or len(set(self.observable_ids)) != width or len(self.units) != width or len(self.frames) != width:
            raise ValueError("invalid truth layout")
        if len(self.times) < 2 or self.times[0] != 0 or list(self.times) != sorted(set(self.times)):
            raise ValueError("invalid truth time grid")
        if len(self.trajectory) != len(self.times) or len(self.terminal) != width or any(len(row) != width for row in self.trajectory):
            raise ValueError("invalid truth dimensions")
        if self.terminal != self.trajectory[-1]:
            raise ValueError("terminal must equal final trajectory row")
        expected = "id" if self.split in ("train", "selection", "calibration", "id_test") else self.split
        if self.ood_type != expected:
            raise ValueError("split and OOD type disagree")


@dataclass(frozen=True)
class TrainingExample(StrictFrozen):
    scenario: ScenarioInput
    truth: EvaluationTruth

    def __post_init__(self):
        super().__post_init__()
        if self.truth.split != "train" or self.scenario.scenario_id != self.truth.scenario_id or self.scenario.family_id != self.truth.family_id:
            raise ValueError("training example requires aligned training-only truth")
        if (tuple(o.quantity_id for o in self.scenario.observables) != self.truth.observable_ids
                or tuple(o.unit for o in self.scenario.observables) != self.truth.units
                or tuple(o.frame for o in self.scenario.observables) != self.truth.frames
                or self.scenario.horizon != self.truth.times[-1]):
            raise ValueError("training metadata mismatch")


@dataclass(frozen=True)
class TargetScaler(StrictFrozen):
    observable_ids: tuple[str, ...]
    units: tuple[str, ...]
    frames: tuple[str, ...]
    means: tuple[float, ...]
    scales: tuple[float, ...]
    constant_coordinates: tuple[bool, ...]
    training_family_ids: tuple[str, ...]
    training_scenario_ids: tuple[str, ...]
    training_targets_sha256: str
    policy: str = "population_std; std<=1e-12 uses 1 physical unit; terminals only; unique family/time"

    def __post_init__(self):
        super().__post_init__()
        width = len(self.observable_ids)
        if not width or any(len(v) != width for v in (self.units, self.frames, self.means, self.scales, self.constant_coordinates)) or any(s <= 0 for s in self.scales):
            raise ValueError("invalid scaler layout/scales")
        if not self.training_family_ids or not self.training_scenario_ids:
            raise ValueError("scaler lacks training provenance")


def fit_scaler(examples: tuple[TrainingExample, ...]) -> TargetScaler:
    if not examples or any(type(e) is not TrainingExample or e.truth.split != "train" for e in examples):
        raise ValueError("scaling accepts nonempty TrainingExample records only")
    layout = examples[0].truth
    unique = {}
    for example in sorted(examples, key=lambda e: e.scenario.scenario_id):
        truth = example.truth
        if (truth.observable_ids, truth.units, truth.frames) != (layout.observable_ids, layout.units, layout.frames):
            raise ValueError("mixed scaler layout")
        key = (truth.family_id, truth.times[-1])
        if key in unique and unique[key].terminal != truth.terminal:
            raise ValueError("conflicting paraphrase targets")
        unique.setdefault(key, truth)
    rows = [unique[key] for key in sorted(unique)]
    means = tuple(sum(t.terminal[i] for t in rows) / len(rows) for i in range(len(layout.terminal)))
    deviations = tuple(sqrt(sum((t.terminal[i] - mean)**2 for t in rows) / len(rows)) for i, mean in enumerate(means))
    return TargetScaler(layout.observable_ids, layout.units, layout.frames, means,
                        tuple(1.0 if s <= 1e-12 else s for s in deviations), tuple(s <= 1e-12 for s in deviations),
                        tuple(sorted({e.truth.family_id for e in examples})),
                        tuple(sorted(e.truth.scenario_id for e in examples)), digest([asdict(t) for t in rows]))
