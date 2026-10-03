from dataclasses import asdict, dataclass
import torch


@dataclass(frozen=True)
class SolverSettings:
    substeps: int = 1
    method: str = 'rk4'

    def __post_init__(self):
        if type(self.substeps) is not int or self.substeps < 1 or self.method != 'rk4':
            raise ValueError('explicit positive RK4 substeps required')


@dataclass
class SolveStats:
    solves: int = 0
    sample_intervals: int = 0
    nfe: int = 0
    sample_nfe: int = 0
    failures: int = 0

    def manifest(self):
        return asdict(self)


def rk4(field, initial, start, end, settings: SolverSettings, stats: SolveStats):
    """All augmented coordinates evolve. The supplied clock controls integration."""
    stats.solves += 1
    try:
        if initial.ndim != 2 or initial.dtype != torch.float32 or not torch.isfinite(initial).all():
            raise ValueError('finite FP32 batch required')
        batch = initial.shape[0]
        if not batch:
            raise ValueError('empty batch')
        def time_tensor(value):
            result = torch.as_tensor(value, dtype=initial.dtype, device=initial.device)
            if result.ndim == 0:
                result = result.expand(batch)
            if result.shape != (batch,) or not torch.isfinite(result).all():
                raise ValueError('invalid physical times')
            return result.reshape(batch, 1)
        time, finish = time_tensor(start), time_tensor(end)
        if not torch.all(finish > time):
            raise ValueError('physical interval must be positive')
        stats.sample_intervals += batch
        step = (finish - time) / settings.substeps
        def evaluate(t, x):
            stats.nfe += 1
            stats.sample_nfe += batch
            result = field(t, x)
            if result.shape != initial.shape or not torch.isfinite(result).all():
                raise ValueError('invalid vector field shape/nonfinite derivative')
            return result
        state = initial
        for index in range(settings.substeps):
            current_time = time + index * step
            k1 = evaluate(current_time, state)
            k2 = evaluate(current_time + step / 2, state + step * k1 / 2)
            k3 = evaluate(current_time + step / 2, state + step * k2 / 2)
            k4 = evaluate(current_time + step, state + step * k3)
            state = state + step * (k1 + 2*k2 + 2*k3 + k4) / 6
            if not torch.isfinite(state).all():
                raise ValueError('nonfinite solver state')
        return state
    except BaseException:
        stats.failures += 1
        raise
