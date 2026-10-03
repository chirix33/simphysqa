"""Approved Stage 6 n-only comparisons, each with its own projection.

ODE/RNN projection gradients come from numerical targets only. LR projection is
fixed random. All autonomous methods reuse initial p and preserve complete n,
including fixed-conditioning coordinates. None modifies the primary Phi-JEPA.
"""
from dataclasses import dataclass,asdict
import math
import numpy as np
import torch
from torch import nn
from phi_jepa.models.context_projection import ContextProjection,ProjectionSettings
from phi_jepa.solvers.rk4 import rk4,SolverSettings,SolveStats


@dataclass(frozen=True)
class BaselineSettings:
    method: str
    embedding_width: int=1024
    hidden_width: int=128
    seed: int=11
    interval_seconds: float=.02
    lr_rcond: float=1e-12

    def __post_init__(self):
        if self.method not in ('constant_context_text_ode','fixed_projection_lr','constant_context_text_rnn','no_text_conditioning'): raise ValueError('unknown_comparator')
        if type(self.hidden_width) is not int or self.hidden_width<1 or type(self.embedding_width) is not int or self.embedding_width<(0 if self.method=='no_text_conditioning' else 1) or type(self.seed) is not int or self.seed<0: raise ValueError('baseline_dimensions_or_seed')
        if self.method=='no_text_conditioning' and self.embedding_width!=0: raise ValueError('numerical_only_has_no_embedding')
        if self.interval_seconds!=.02 or self.lr_rcond!=1e-12: raise ValueError('unsupported_interval_or_rank_policy')


class NumericalComparator(nn.Module):
    def __init__(self,layout,settings,conditioning=None):
        super().__init__(); self.layout=layout; self.settings=settings
        self.conditioning=conditioning
        if conditioning is not None and (settings.method not in ('constant_context_text_ode','no_text_conditioning') or len(conditioning.center)!=layout.d or conditioning.manifest()['layout_sha256']!=layout.sha256):
            raise ValueError('conditioning_only_for_matching_numerical_ODE')
        self.projection=(None if settings.method=='no_text_conditioning' else
                         ContextProjection(layout,ProjectionSettings(settings.embedding_width,seed=settings.seed)))
        d,h=layout.d,settings.hidden_width
        with torch.random.fork_rng(devices=[]):
            torch.manual_seed(settings.seed)
            if settings.method in ('constant_context_text_ode','no_text_conditioning'):
                input_width=d+1 if settings.method=='no_text_conditioning' else 2*d+1
                self.field=nn.Sequential(nn.Linear(input_width,h),nn.Tanh(),nn.Linear(h,h),nn.Tanh(),nn.Linear(h,d)).float()
                for layer in self.field:
                    if isinstance(layer,nn.Linear): nn.init.xavier_uniform_(layer.weight); nn.init.zeros_(layer.bias)
                with torch.no_grad(): self.field[-1].weight.mul_(.01)
            elif settings.method=='constant_context_text_rnn':
                self.rnn=nn.RNN(2*d,h,batch_first=True,nonlinearity='tanh').float()
                self.readout=nn.Linear(h,d).float()
            else:
                self.projection.requires_grad_(False)
                self.register_buffer('coefficients',torch.zeros(2*d+1,d,dtype=torch.float64))
                self.register_buffer('fitted',torch.tensor(False))

    def manifest(self):
        result = {'version':'p05b-v1','settings':asdict(self.settings),'layout':self.layout.manifest(),
            'layout_sha256':self.layout.sha256,'projection':self.projection.manifest() if self.projection is not None else None,
            'projection_trainable':self.projection is not None and self.settings.method!='fixed_projection_lr','loss':'raw_numerical_next_state_mse_equal_transitions',
            'output':'complete_n_only','context_feedback':'absent_numerical_only_component_ablation' if self.projection is None else 'initial_p_reused_constant',
            'initialization':'last_public_observation; RNN zero hidden; no earlier-history warmup',
            'precision':'float32 neural; float64 least_squares_coefficients'}
        if self.conditioning is not None: result['conditioning']=self.conditioning.manifest()
        return result

    def next_state(self,n,p,start,end,*,solver,stats,hidden=None):
        if n.ndim!=2 or n.shape[1]!=self.layout.d or not torch.isfinite(n).all(): raise ValueError('numerical_shape_or_value')
        method=self.settings.method
        if method=='no_text_conditioning':
            if p is not None: raise ValueError('numerical_only_rejects_context')
            return rk4(lambda time,value:self.field(torch.cat((self.conditioning(value) if self.conditioning is not None else value,time),dim=-1)),n,start,end,solver,stats),None
        if p is None or n.shape!=p.shape or not torch.isfinite(p).all(): raise ValueError('context_shape_or_value')
        if method=='constant_context_text_ode':
            def field(time,value): return self.field(torch.cat((self.conditioning(value) if self.conditioning is not None else value,p,time),dim=-1))
            return rk4(field,n,start,end,solver,stats),None
        dt=torch.as_tensor(end)-torch.as_tensor(start)
        if not torch.all(torch.abs(dt-self.settings.interval_seconds)<1e-7): raise ValueError('discrete_model_requires_0.02_seconds')
        if method=='fixed_projection_lr':
            if not self.fitted: raise ValueError('unfitted_lr')
            x=torch.cat((n,p,torch.ones_like(n[:,:1])),dim=-1).double()
            output=(x@self.coefficients).float(); following=None
        else:
            output,following=self.rnn(torch.cat((n,p),dim=-1).unsqueeze(1),hidden)
            output=self.readout(output[:,0,:])
        if not torch.isfinite(output).all() or (following is not None and not torch.isfinite(following).all()): raise ValueError('nonfinite_baseline_output')
        return output,following

    def fit_lr(self,current,target,embedding):
        if self.settings.method!='fixed_projection_lr': raise ValueError('lr_method_required')
        with torch.no_grad(): p=self.projection(embedding)
        if current.shape!=target.shape or current.shape!=p.shape or not torch.isfinite(current).all() or not torch.isfinite(target).all(): raise ValueError('lr_training_shapes_or_values')
        x=torch.cat((current,p,torch.ones_like(current[:,:1])),dim=-1).double().cpu().numpy()
        y=target.double().cpu().numpy()
        coefficients,residuals,rank,singular=np.linalg.lstsq(x,y,rcond=self.settings.lr_rcond)
        if not np.isfinite(coefficients).all(): raise ValueError('nonfinite_lr_fit')
        self.coefficients.copy_(torch.from_numpy(coefficients)); self.fitted.fill_(True)
        return {'fit':'numpy.linalg.lstsq_SVD','rcond':self.settings.lr_rcond,'rank':int(rank),
            'design_rows':x.shape[0],'design_columns':x.shape[1],'rank_deficient':bool(rank<min(x.shape)),
            'underdetermined':x.shape[0]<x.shape[1],'singular_values':singular.tolist(),
            'residual_sum_squares':float(np.square(x@coefficients-y).sum()),
            'projection':'fixed_seeded_random_not_learned','fits':1}

    def lr_diagnostics(self,current,target,embedding):
        """Read-only diagnostics of an already fitted matrix; no second fit."""
        if self.settings.method!='fixed_projection_lr' or not self.fitted: raise ValueError('fitted_lr_required')
        with torch.no_grad(): p=self.projection(embedding)
        x=torch.cat((current,p,torch.ones_like(current[:,:1])),dim=-1).double().cpu().numpy()
        y=target.double().cpu().numpy(); coefficients=self.coefficients.cpu().numpy()
        singular=np.linalg.svd(x,compute_uv=False)
        rank=int(np.sum(singular>self.settings.lr_rcond*singular[0]))
        return {'fit':'numpy.linalg.lstsq_SVD','rcond':self.settings.lr_rcond,'rank':rank,
            'design_rows':x.shape[0],'design_columns':x.shape[1],'rank_deficient':rank<min(x.shape),
            'underdetermined':x.shape[0]<x.shape[1],'singular_values':singular.tolist(),
            'residual_sum_squares':float(np.square(x@coefficients-y).sum()),
            'projection':'fixed_seeded_random_not_learned','fits':1,
            'recovery':'diagnostics recomputed from preserved fitted coefficients; no repeated fit'}


@dataclass(frozen=True)
class NumericalPrediction:
    layout_sha256: str
    d: int
    values: tuple
    physical_time: float

    def __post_init__(self):
        if len(self.values)!=self.d or any(type(v) not in (int,float) or not math.isfinite(v) for v in (*self.values,self.physical_time)): raise ValueError('invalid_numerical_prediction')


@dataclass(frozen=True)
class NumericalRollout:
    sample_id: str
    predictions: tuple
    method: str
    mode: str='autonomous'


@torch.no_grad()
def forecast(model,problem,embedding,grid,*,solver=None,stats=None):
    inp=problem.input; solver=solver or SolverSettings(); stats=stats or SolveStats()
    if not grid or grid[0]!=inp['observation_cutoff'] or any(b<=a for a,b in zip(grid,grid[1:])): raise ValueError('forecast_grid')
    if grid[-1]!=max(t['end_time'] for t in inp['answer_spec']): raise ValueError('forecast_horizon')
    model.eval(); n=torch.tensor([model.layout.flatten(inp['states'][-1],inp)],dtype=torch.float32)
    if model.settings.method=='no_text_conditioning':
        if embedding is not None: raise ValueError('numerical_only_rejects_embedding')
        p=None
    else: p=model.projection(embedding)
    hidden=None; rows=[]; model_calls=0
    for a,b in zip(grid,grid[1:]):
        model_calls+=1
        n,hidden=model.next_state(n,p,a,b,solver=solver,stats=stats,hidden=hidden)
        rows.append(NumericalPrediction(model.layout.sha256,model.layout.d,tuple(n[0].tolist()),b))
    return NumericalRollout(problem.sample_id,tuple(rows),model.settings.method),{'forecast_steps':model_calls,
        'discrete_model_calls':model_calls if model.settings.method in ('constant_context_text_rnn','fixed_projection_lr') else 0,'solver':stats.manifest()}
