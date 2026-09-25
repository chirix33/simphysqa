"""Generic time-conditioned vector field; no simulator/evaluator imports."""
from dataclasses import asdict, dataclass
import torch
from torch import nn
from .context_projection import ContextProjection, ProjectionSettings


@dataclass(frozen=True)
class ODESettings:
    hidden_width: int = 128
    seed: int = 11
    output_initialization_scale: float = 0.01

    def __post_init__(self):
        if type(self.hidden_width) is not int or self.hidden_width < 1:
            raise ValueError('positive hidden width required')
        if type(self.seed) is not int or self.seed < 0 or self.output_initialization_scale != 0.01:
            raise ValueError('unsupported initialization setting')


class AugmentedODE(nn.Module):
    def __init__(self, layout, projection_settings: ProjectionSettings, ode_settings: ODESettings):
        super().__init__()
        self.layout = layout
        self.projection = ContextProjection(layout, projection_settings)
        self.ode_settings = ode_settings
        width, hidden = 2 * layout.d, ode_settings.hidden_width
        with torch.random.fork_rng(devices=[]):
            torch.manual_seed(ode_settings.seed)
            self.field = nn.Sequential(nn.Linear(width + 1, hidden), nn.Tanh(),
                nn.Linear(hidden, hidden), nn.Tanh(), nn.Linear(hidden, width)).float()
            for layer in self.field:
                if isinstance(layer, nn.Linear):
                    nn.init.xavier_uniform_(layer.weight)
                    nn.init.zeros_(layer.bias)
            with torch.no_grad():
                self.field[-1].weight.mul_(ode_settings.output_initialization_scale)

    def forward(self, time, augmented):
        if augmented.ndim != 2 or augmented.shape[1] != 2 * self.layout.d:
            raise ValueError('expected batch by 2d augmented state')
        if time.shape != (augmented.shape[0], 1):
            raise ValueError('time must be batch by one')
        return self.field(torch.cat((augmented, time), dim=-1))

    def manifest(self):
        return {'format_version': 1, 'contract': '2.0.0-candidate.1',
                'layout': self.layout.manifest(), 'layout_sha256': self.layout.sha256,
                'projection': self.projection.manifest(), 'ode': asdict(self.ode_settings),
                'time': 'absolute_seconds_no_internal_rescaling', 'precision': 'float32'}
