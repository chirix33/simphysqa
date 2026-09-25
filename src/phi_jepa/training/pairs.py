from dataclasses import asdict, dataclass
import copy
import time
import torch
from phi_jepa.solvers.rk4 import rk4, SolveStats


@dataclass(frozen=True)
class TrainingSettings:
    learning_rate: float = 0.001
    gradient_clip: float = 1.0
    weighting: str = 'equal_question_pairs'
    loss: str = 'raw_full_augmented_coordinate_mse'
    context_mode: str = 'enriched'

    def __post_init__(self):
        import math
        if any(type(x) not in (int, float) or not math.isfinite(x) or x <= 0
               for x in (self.learning_rate, self.gradient_clip)):
            raise ValueError('finite positive optimizer settings required')
        if self.weighting != 'equal_question_pairs' or self.loss != 'raw_full_augmented_coordinate_mse':
            raise ValueError('only the user-approved loss/weighting is active')
        if self.context_mode not in ('enriched','public_base_for_offline_audit'):
            raise ValueError('explicit enriched or approved no-enrichment variant required')


def finite_tree(value):
    if torch.is_tensor(value):
        return bool(torch.isfinite(value).all())
    if isinstance(value, dict):
        return all(finite_tree(v) for v in value.values())
    if isinstance(value, (list, tuple)):
        return all(finite_tree(v) for v in value)
    if isinstance(value, float):
        import math
        return math.isfinite(value)
    return True


class PairTrainer:
    def __init__(self, model, solver, settings: TrainingSettings):
        self.model, self.solver, self.settings = model, solver, settings
        # Includes P and vector field, no frozen encoder or extra regularizer.
        self.optimizer = torch.optim.Adam(model.parameters(), lr=settings.learning_rate)
        self.stats = SolveStats()
        self.updates = 0
        self.failed_updates = 0
        self.attempted_updates = 0

    def step(self, pairs, embeddings):
        self.attempted_updates += 1
        try:
            return self._step(pairs, embeddings)
        except BaseException:
            self.failed_updates += 1
            raise

    def _step(self, pairs, embeddings):
        started = time.perf_counter()
        if not pairs or embeddings.shape[0] != len(pairs):
            raise ValueError('pair/context batch mismatch')
        if any(p.registry_sha256 != self.model.layout.sha256 or p.identity.split != 'train'
               or p.weight != 1.0 or p.context_mode != self.settings.context_mode for p in pairs):
            raise ValueError('layout/split/weight/context-mode mismatch')
        if any(p.end_time <= p.start_time for p in pairs):
            raise ValueError('nonpositive recorded interval')
        current = torch.tensor([p.n_current for p in pairs], dtype=torch.float32, device=embeddings.device)
        target_n = torch.tensor([p.n_next for p in pairs], dtype=torch.float32, device=embeddings.device)
        self.optimizer.zero_grad(set_to_none=True)
        x, target, p = self.model.projection.pair(current, target_n, embeddings,
                                                 layout_sha256=self.model.layout.sha256)
        predicted = rk4(self.model, x, [p.start_time for p in pairs], [p.end_time for p in pairs], self.solver, self.stats)
        residual = predicted - target
        loss = residual.square().mean()  # equal pair weights, equal coordinate weights
        if not torch.isfinite(loss):
            raise ValueError('nonfinite loss')
        loss.backward()
        norm = torch.nn.utils.clip_grad_norm_(self.model.parameters(), self.settings.gradient_clip, error_if_nonfinite=True)
        projection_norm = torch.linalg.vector_norm(torch.cat([p.grad.flatten() for p in self.model.projection.parameters()]))
        # Preserve last finite optimizer/model state if the step itself overflows.
        before_model, before_optimizer = copy.deepcopy(self.model.state_dict()), copy.deepcopy(self.optimizer.state_dict())
        self.optimizer.step()
        if not finite_tree(self.model.state_dict()) or not finite_tree(self.optimizer.state_dict()):
            self.model.load_state_dict(before_model)
            self.optimizer.load_state_dict(before_optimizer)
            raise ValueError('nonfinite optimizer update rejected; previous finite state restored')
        self.updates += 1
        d = self.model.layout.d
        return {'update': self.updates, 'batch_size': len(pairs), 'd': d, 'loss': float(loss.detach()),
            'numeric_sse': float(residual[:, :d].detach().square().sum()),
            'context_sse': float(residual[:, d:].detach().square().sum()),
            'numeric_mse': float(residual[:, :d].detach().square().mean()),
            'context_mse': float(residual[:, d:].detach().square().mean()),
            'p_l2_mean': float(p.detach().norm(dim=1).mean()), 'gradient_norm_before_clip': float(norm),
            'projection_gradient_norm_after_clip': float(projection_norm), 'stats': self.stats.manifest(),
            'wall_seconds': time.perf_counter() - started}
