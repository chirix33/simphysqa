"""Frozen train-input affine parameterization, never an ODE coordinate change."""
import torch
from copy import deepcopy
from torch import nn
from phi_jepa.artifacts import digest


class NumericalConditioning(nn.Module):
    def __init__(self, manifest):
        super().__init__()
        if manifest['version']!='train_n_affine_v1' or manifest['provenance']['split']!='train':
            raise ValueError('training_only_conditioning_required')
        center=torch.tensor(manifest['center'],dtype=torch.float32)
        scale=torch.tensor(manifest['scale'],dtype=torch.float32)
        if center.ndim!=1 or center.shape!=scale.shape or not torch.isfinite(center).all() or not torch.isfinite(scale).all() or not (scale>0).all():
            raise ValueError('finite_invertible_affine_required')
        self.register_buffer('center',center); self.register_buffer('scale',scale)
        self._manifest=deepcopy(manifest)

    @classmethod
    def fit(cls, current_inputs, *, layout_sha256, provenance):
        if provenance.get('split')!='train' or not provenance.get('sample_ids') or not provenance.get('scenario_ids'):
            raise ValueError('explicit_train_inputs_and_scenarios_required')
        x=torch.as_tensor(current_inputs,dtype=torch.float64)
        if x.ndim!=2 or not len(x) or not torch.isfinite(x).all(): raise ValueError('finite_training_matrix_required')
        center=x.mean(0); sd=x.std(0,unbiased=False)
        # Near-constant coordinates are centered, with a unit scale. This is
        # invertible; no coordinate is removed, clamped or replaced with zero.
        constant=(x.max(0).values-x.min(0).values)<=1e-6*torch.maximum(center.abs(),torch.ones_like(center))
        scale=torch.where(constant,torch.ones_like(sd),sd)
        manifest={'version':'train_n_affine_v1','layout_sha256':layout_sha256,'center':center.tolist(),'scale':scale.tolist(),
            'constant_columns':constant.nonzero().flatten().tolist(),'constant_policy':'range <= 1e-6 * max(1,abs(train_mean)): scale=1',
            'fit':'population mean/std of recorded current n inputs only; context and external solver time untouched',
            'rows':len(x),'training_inputs_sha256':digest(x.tolist()),'provenance':provenance}
        return cls(manifest)

    def forward(self, numerical): return (numerical-self.center)/self.scale
    def inverse(self, conditioned): return conditioned*self.scale+self.center
    def manifest(self): return deepcopy(self._manifest)
