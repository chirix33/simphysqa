from dataclasses import dataclass
from ..validation import StrictFrozen


@dataclass(frozen=True)
class Interval(StrictFrozen):
    low: float
    high: float

    def __post_init__(self):
        super().__post_init__()
        if self.low >= self.high:
            raise ValueError("range must have low < high")


@dataclass(frozen=True)
class Counts(StrictFrozen):
    train: int = 16
    selection: int = 4
    calibration: int = 4
    id_test: int = 4
    parameter_low: int = 1
    parameter_high: int = 1
    combination: int = 1
    event: int = 1

    def __post_init__(self):
        super().__post_init__()
        if self.train < 2 or min(vars(self).values()) < 0 or sum(vars(self).values()) > 256:
            raise ValueError("require >=2 train families, nonnegative counts, <=256 total wiring families")


@dataclass(frozen=True)
class DatasetConfig(StrictFrozen):
    seed: int = 11
    counts: Counts = Counts()
    speed: Interval = Interval(5.0, 20.0)
    friction: Interval = Interval(0.3, 0.7)
    position: Interval = Interval(-10.0, 10.0)
    horizon: Interval = Interval(0.5, 5.0)
    low_friction: Interval = Interval(0.05, 0.15)
    high_friction: Interval = Interval(0.85, 1.0)
    gravity: float = 9.81
    combination_speed_min: float = 15.0
    combination_friction_max: float = 0.4
    paraphrases: int = 2
    time_fractions: tuple[float, ...] = (0.5, 1.0)
    sample_intervals: int = 8

    def __post_init__(self):
        super().__post_init__()
        if self.seed < 0 or self.speed.low < 0 or self.friction.low < 0 or self.low_friction.low < 0 or self.gravity <= 0 or self.horizon.low <= 0:
            raise ValueError("invalid physical generation ranges")
        if not (self.low_friction.high < self.friction.low and self.high_friction.low > self.friction.high):
            raise ValueError("parameter OOD ranges must be outside ID friction")
        if not (self.speed.low < self.combination_speed_min < self.speed.high and self.friction.low < self.combination_friction_max < self.friction.high):
            raise ValueError("combination boundary must lie inside ID marginals")
        if self.paraphrases not in (1, 2) or not 1 <= self.sample_intervals <= 1000:
            raise ValueError("supported paraphrases 1/2, intervals 1..1000")
        if not self.time_fractions or len(self.time_fractions) > 4 or tuple(sorted(set(self.time_fractions))) != self.time_fractions or any(not 0 < t <= 1 for t in self.time_fractions):
            raise ValueError("one to four ordered unique time fractions in (0,1] required")
