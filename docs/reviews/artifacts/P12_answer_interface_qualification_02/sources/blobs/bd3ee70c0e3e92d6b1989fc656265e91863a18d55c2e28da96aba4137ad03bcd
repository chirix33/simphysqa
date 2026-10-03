"""SI passive stopping: analytic labels and independently coded forward Euler checks."""
from dataclasses import dataclass
from math import ceil, isfinite
from ..validation import StrictFrozen, convert


@dataclass(frozen=True)
class FrictionEvent(StrictFrozen):
    time: float
    mu: float

    def __post_init__(self):
        super().__post_init__()
        if self.time <= 0 or self.mu < 0:
            raise ValueError("events require positive time and nonnegative friction")


@dataclass(frozen=True)
class StoppingCase(StrictFrozen):
    x0: float
    v0: float
    mu: float
    gravity: float
    horizon: float
    events: tuple[FrictionEvent, ...] = ()

    def __post_init__(self):
        super().__post_init__()
        if self.v0 < 0 or self.mu < 0 or self.gravity <= 0 or self.horizon <= 0:
            raise ValueError("require v0/mu >= 0, gravity/horizon > 0; zero horizon unsupported")
        times = [e.time for e in self.events]
        if times != sorted(set(times)) or any(t > self.horizon for t in times):
            raise ValueError("events must be strictly ordered, unique and within horizon")
        if not all(isfinite(v) for v in (self.mu * self.gravity, self.v0 * self.horizon,
                                        self.x0 + self.v0 * self.horizon,
                                        *(e.mu * self.gravity for e in self.events))):
            raise ValueError("physical inputs overflow finite computation")


@dataclass(frozen=True)
class OracleResult:
    times: tuple[float, ...]
    states: tuple[tuple[float, ...], ...]
    steps: int
    method: str


def sample_grid(case: StoppingCase, intervals: int = 8) -> tuple[float, ...]:
    if type(intervals) is not int or not 1 <= intervals <= 1000:
        raise ValueError("intervals must be an integer in [1,1000]")
    return tuple(sorted({0.0, case.horizon, *(case.horizon * i / intervals for i in range(intervals)),
                         *(e.time for e in case.events)}))


def checked_times(case: StoppingCase, times) -> tuple[float, ...]:
    times = convert(tuple[float, ...], times)
    if len(times) < 2 or times[0] != 0 or times[-1] != case.horizon or list(times) != sorted(set(times)):
        raise ValueError("grid must strictly increase from zero to the exact horizon")
    return times


def constant_state(x: float, v: float, mu: float, gravity: float, duration: float) -> tuple[float, float]:
    """Closed form used only by the analytic benchmark, never by the numerical check."""
    if v == 0:
        return x, 0.0
    if mu == 0:
        return x + v * duration, v
    a = mu * gravity
    moving = min(duration, v / a)
    return x + (v - 0.5 * a * moving) * moving, max(v - a * duration, 0.0)


def analytic(case: StoppingCase, times) -> OracleResult:
    times = checked_times(case, times)
    states = []
    segments = 0
    # Recompute each requested sample from event segments, independent of grid density.
    for target in times:
        x, v, mu, previous = case.x0, case.v0, case.mu, 0.0
        for event in case.events:
            if event.time > target:
                break
            x, v = constant_state(x, v, mu, case.gravity, event.time - previous)
            segments += 1
            mu, previous = event.mu, event.time
        x, v = constant_state(x, v, mu, case.gravity, target - previous)
        segments += 1
        if not all(isfinite(value) for value in (x, v)):
            raise ValueError("nonfinite analytic state")
        states.append((x, v))
    return OracleResult(times, tuple(states), segments, "piecewise_closed_form_v1")


def numerical(case: StoppingCase, times, max_step: float = 0.01, max_steps: int = 200000) -> OracleResult:
    """Forward Euler: old-speed position update, nonnegative speed projection.

    No analytic stopping-time correction; O(h) position error is measured by refinement.
    Land exactly on event and observation boundaries. Friction is right-continuous;
    state is continuous at an event, including an event at the terminal time.
    """
    times = checked_times(case, times)
    max_step = convert(float, max_step)
    if max_step <= 0 or type(max_steps) is not int or max_steps <= 0:
        raise ValueError("positive numerical step and finite step budget required")
    boundaries = sorted({*times, *(event.time for event in case.events)})
    changes = {event.time: event.mu for event in case.events}
    sampled = {0.0: (case.x0, case.v0)}
    x, v, mu, previous, steps = case.x0, case.v0, case.mu, 0.0, 0
    for boundary in boundaries[1:]:
        ratio = (boundary - previous) / max_step
        if not isfinite(ratio) or ratio > max_steps - steps:
            raise ValueError("numerical step budget exceeded")
        count = max(1, ceil(ratio))
        if steps + count > max_steps:
            raise ValueError("numerical step budget exceeded")
        dt = (boundary - previous) / count
        for _ in range(count):
            x += dt * v
            if v > 0:
                v = max(0.0, v - dt * mu * case.gravity)
            steps += 1
        if not all(isfinite(value) for value in (x, v)):
            raise ValueError("nonfinite numerical state")
        sampled[boundary] = (x, v)
        mu = changes.get(boundary, mu)
        previous = boundary
    return OracleResult(times, tuple(sampled[t] for t in times), steps, "forward_euler_v1")
