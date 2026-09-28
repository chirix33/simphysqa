"""Layout-specific trainable P; no ODE/training loop is implemented in P02b."""
from dataclasses import asdict, dataclass

import torch
from torch import nn

from phi_jepa.providers.contracts import positive_int


@dataclass(frozen=True)
class ProjectionSettings:
    embedding_width: int
    seed: int = 11
    initialization: str = 'xavier_uniform_zero_bias'
    precision: str = 'float32'
    sharing: str = 'one_instance_per_layout'

    def __post_init__(self):
        positive_int(self.embedding_width, 'embedding_width')
        if type(self.seed) is not int or self.seed < 0:
            raise ValueError('nonnegative seed required')
        if (self.initialization, self.precision, self.sharing) != (
                'xavier_uniform_zero_bias', 'float32', 'one_instance_per_layout'):
            raise ValueError('unsupported projection setting')


class ContextProjection(nn.Module):
    def __init__(self, layout, settings: ProjectionSettings):
        super().__init__()
        positive_int(layout.d, 'layout.d')
        self.layout_sha256 = layout.sha256
        self.d = layout.d
        self.settings = settings
        # CPU initialization is reproducible without changing the caller's RNG.
        with torch.random.fork_rng(devices=[]):
            torch.manual_seed(settings.seed)
            self.linear = nn.Linear(settings.embedding_width, self.d, device='cpu', dtype=torch.float32)
            nn.init.xavier_uniform_(self.linear.weight)
            nn.init.zeros_(self.linear.bias)

    def manifest(self):
        return {'version': 1, 'layout_sha256': self.layout_sha256, 'd': self.d,
                'ode_width': 2 * self.d, **asdict(self.settings)}

    def forward(self, embedding):
        if embedding.ndim != 2 or embedding.shape[1] != self.settings.embedding_width:
            raise ValueError('expected batch by embedding_width')
        if embedding.requires_grad:
            raise ValueError('E output must be frozen; P itself remains trainable')
        if embedding.dtype != self.linear.weight.dtype or not torch.isfinite(embedding).all():
            raise ValueError('embedding precision/nonfinite mismatch')
        p = self.linear(embedding)
        if not torch.isfinite(p).all():
            raise ValueError('nonfinite projection')
        return p

    def pair(self, n_current, n_next, embedding, *, layout_sha256):
        """Compute p exactly once, retaining BOTH autograd paths.

        The Stage 3 optimizer must include this module's parameters. No projected
        output cache is provided; call this again after every optimizer update.
        """
        if layout_sha256 != self.layout_sha256:
            raise ValueError('projection/layout mismatch')
        if embedding.ndim != 2:
            raise ValueError('expected batch by embedding_width')
        expected = (embedding.shape[0], self.d)
        for n in (n_current, n_next):
            if n.shape != expected or n.dtype != self.linear.weight.dtype or not torch.isfinite(n).all():
                raise ValueError('invalid recorded numerical batch')
            if n.device != embedding.device:
                raise ValueError('numerical/context device mismatch')
        p = self(embedding)
        return torch.cat((n_current, p), dim=-1), torch.cat((n_next, p), dim=-1), p


class FrozenModule(nn.Module):
    """Freeze an already locally loaded E; loading/pooling remain adapter-specific."""
    def __init__(self, encoder: nn.Module):
        super().__init__()
        self.encoder = encoder
        self.encoder.requires_grad_(False)
        self.train(False)

    def train(self, mode=True):
        # Parent model.train() must never enable E's dropout/batch-stat updates.
        super().train(False)
        return self

    def forward(self, *args, **kwargs):
        with torch.no_grad():
            return self.encoder(*args, **kwargs)
