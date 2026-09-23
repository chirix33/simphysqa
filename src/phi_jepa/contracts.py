from dataclasses import dataclass
from .validation import StrictFrozen, convert


@dataclass(frozen=True)
class ObservableSpec(StrictFrozen):
    quantity_id: str
    name: str
    unit: str
    frame: str
    index: int
    output_mask: bool
    absolute_tolerance: float

    def __post_init__(self):
        super().__post_init__()
        if self.index < 0 or self.absolute_tolerance < 0:
            raise ValueError("index and tolerance must be nonnegative")


@dataclass(frozen=True)
class ObservedFact(StrictFrozen):
    quantity_id: str
    value: float | str | None
    unit: str
    source: str


@dataclass(frozen=True)
class ScenarioInput(StrictFrozen):
    scenario_id: str
    family_id: str
    question: str
    initial_facts: tuple[ObservedFact, ...]
    observables: tuple[ObservableSpec, ...]
    initial_time: float
    horizon: float
    permitted_events: tuple[str, ...] = ()
    permitted_controls: tuple[ObservedFact, ...] = ()

    def __post_init__(self):
        super().__post_init__()
        if self.horizon <= 0 or not self.observables:
            raise ValueError("positive horizon and observables required")
        if tuple(o.index for o in self.observables) != tuple(range(len(self.observables))):
            raise ValueError("observable indices must be ordered and contiguous")
        if len({o.quantity_id for o in self.observables}) != len(self.observables):
            raise ValueError("duplicate observable IDs")

    @classmethod
    def from_dict(cls, payload: dict) -> "ScenarioInput":
        return convert(cls, payload)
