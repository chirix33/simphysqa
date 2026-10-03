"""Equal-transition independent baseline training, no sequence reweighting."""
import copy
import json
import torch
from phi_jepa.solvers.rk4 import SolveStats,SolverSettings
from phi_jepa.training.pairs import finite_tree


def validate_pairs(model,pairs,embeddings):
    numerical_only=model.settings.method=='no_text_conditioning'
    mode='public_base_for_offline_audit' if numerical_only else 'enriched'
    if numerical_only and embeddings is not None: raise ValueError('numerical_only_rejects_embedding')
    if not pairs or (not numerical_only and (embeddings is None or len(pairs)!=embeddings.shape[0])) or any(p.identity.split!='train' or p.weight!=1. or p.registry_sha256!=model.layout.sha256 or p.context_mode!=mode or abs(p.dt-.02)>1e-8 for p in pairs): raise ValueError('pair_split_layout_context_weight_or_interval')
    current=torch.tensor([p.n_current for p in pairs],dtype=torch.float32)
    target=torch.tensor([p.n_next for p in pairs],dtype=torch.float32)
    if not torch.isfinite(current).all() or not torch.isfinite(target).all(): raise ValueError('nonfinite_pair')
    return current,target


class ComparatorTrainer:
    def __init__(self,model,*,learning_rate=.001,gradient_clip=1.,solver=None):
        if model.settings.method=='fixed_projection_lr': raise ValueError('lr_requires_one_least_squares_fit')
        self.model=model; self.solver=solver or SolverSettings(); self.gradient_clip=gradient_clip
        self.learning_rate=learning_rate; self.optimizer=torch.optim.Adam(model.parameters(),lr=learning_rate)
        self.stats=SolveStats(); self.updates=0; self.attempts=0; self.failures=0; self.recurrent_calls=0

    def step(self,pairs,embeddings):
        self.attempts+=1
        try: return self._step(pairs,embeddings)
        except BaseException: self.failures+=1; raise

    def _step(self,pairs,embeddings):
        model=self.model; model.train(); n,target=validate_pairs(model,pairs,embeddings)
        self.optimizer.zero_grad(set_to_none=True); p=model.projection(embeddings) if model.projection is not None else None
        if model.settings.method in ('constant_context_text_ode','no_text_conditioning'):
            predicted,_=model.next_state(n,p,[r.start_time for r in pairs],[r.end_time for r in pairs],solver=self.solver,stats=self.stats)
        else:
            predictions=[]; hidden=None; previous=None
            for index,pair in enumerate(pairs):
                key=(pair.identity.group_id,pair.identity.sample_id,pair.context_json)
                if previous is not None and previous[0]==key:
                    if pair.start_time!=previous[1].end_time or pair.start_state_id!=previous[1].end_state_id or pair.n_current!=previous[1].n_next: raise ValueError('rnn_requires_chronological_adjacent_sequence')
                    if not torch.equal(embeddings[index],embeddings[index-1]): raise ValueError('rnn_context_changed_within_sequence')
                else:
                    if any((r.identity.group_id,r.identity.sample_id,r.context_json)==key for r in pairs[:index]): raise ValueError('interleaved_sequence')
                    if pair.start_time!=json.loads(pair.context_json)['C']['observation_cutoff']: raise ValueError('rnn_sequence_must_start_at_cutoff')
                    hidden=None
                self.recurrent_calls+=1
                value,hidden=model.next_state(n[index:index+1],p[index:index+1],pair.start_time,pair.end_time,solver=self.solver,stats=self.stats,hidden=hidden)
                predictions.append(value); previous=(key,pair)
            predicted=torch.cat(predictions)
        loss=(predicted-target).square().mean()  # each transition/coordinate once
        if not torch.isfinite(loss): raise ValueError('nonfinite_baseline_loss')
        loss.backward()
        norm=torch.nn.utils.clip_grad_norm_(model.parameters(),self.gradient_clip,error_if_nonfinite=True)
        pgrad=float(torch.linalg.vector_norm(torch.cat([x.grad.flatten() for x in model.projection.parameters()]))) if model.projection is not None else None
        state,optim=copy.deepcopy(model.state_dict()),copy.deepcopy(self.optimizer.state_dict())
        self.optimizer.step()
        if not finite_tree(model.state_dict()) or not finite_tree(self.optimizer.state_dict()):
            model.load_state_dict(state); self.optimizer.load_state_dict(optim); raise ValueError('nonfinite_baseline_update_rolled_back')
        self.updates+=1
        return {'update':self.updates,'transitions':len(pairs),'numerical_mse':float(loss.detach()),
            'gradient_norm_before_clip':float(norm),'projection_gradient_norm_after_clip':pgrad,
            'projection_norm_mean':float(p.detach().norm(dim=-1).mean()) if p is not None else None,'solver':self.stats.manifest(),'recurrent_calls':self.recurrent_calls}
