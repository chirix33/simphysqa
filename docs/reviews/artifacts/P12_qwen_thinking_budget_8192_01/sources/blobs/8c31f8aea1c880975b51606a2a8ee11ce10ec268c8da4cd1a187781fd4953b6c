"""Autonomous full-vector feedback. No reference/evaluator API or file handle."""
import math
import torch
from phi_jepa.integration.contracts import FullAugmentedPrediction, PhysicalRollout
from phi_jepa.solvers.rk4 import rk4


@torch.no_grad()
def rollout(model, problem, embedding, times, solver, stats):
    inp = problem.input
    if not times or any(type(t) not in (int, float) or not math.isfinite(t) for t in times):
        raise ValueError('finite external physical grid required')
    if times[0] != inp['observation_cutoff'] or any(b <= a for a, b in zip(times, times[1:])):
        raise ValueError('grid must start at last public observation and increase')
    if times[-1] != max(spec['end_time'] for spec in inp['answer_spec']):
        raise ValueError('grid must end at requested horizon')
    if embedding.shape != (1, model.projection.settings.embedding_width):
        raise ValueError('one public context required')
    numerical = torch.tensor([model.layout.flatten(inp['states'][-1], inp)],
                             dtype=torch.float32, device=embedding.device)
    initial_p = model.projection(embedding)
    state = torch.cat((numerical, initial_p), dim=-1)
    predictions = []
    for start, end in zip(times, times[1:]):
        state = rk4(model, state, start, end, solver, stats)
        # Presentation conversion is outside the recurrent path. Neither p nor
        # any predicted numeric coordinate is replaced, rounded or reset.
        predictions.append(FullAugmentedPrediction(model.layout.sha256, model.layout.d,
                                                   tuple(state[0].cpu().tolist()), end))
    return PhysicalRollout(problem.sample_id, tuple(predictions))
