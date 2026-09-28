"""Bounded selected-checkpoint evaluation gradients; no optimizer or provider."""
from collections import Counter
import torch
from p10_common import *
from p10_inference import load_selected,grid
from phi_jepa.integration.contracts import PublicProblem
from phi_jepa.integration.readers import forecast_states
from phi_jepa.solvers.rk4 import rk4,SolveStats


def diagnose(run,job=None):
    torch.set_num_threads(2); layout=run.layout(); records=[]
    groups={'physical':[],'time_index':[],'fixed_conditioning':[],'contextual':list(range(layout.d,2*layout.d))}
    for i,(path,typ) in enumerate(layout.entries):
        name='fixed_conditioning' if path[0]==('key','fixed_conditioning') else 'time_index' if path[-1] in (('key','timestamp'),('key','step_index')) else 'physical'
        groups[name].append(i)
    variants=[x for x in ('conditioned_full','biasinit_conditioned_full','continued_biasinit_conditioned_full') if (run.root/'numerical'/x/'selected.json').exists()]
    for variant in variants:
        model,solver,settings=load_selected(run,variant); model.eval(); before={k:v.detach().clone() for k,v in model.state_dict().items()}
        for split in ('train','validation'):
            refs=load(run.root/'private'/f'{split}-references.json'); ns=[]; targets=[]; es=[]; starts=[]; ends=[]; identities=[]
            for row in [r for r in run.rows() if r['split']==split][:2]:
                p=PublicProblem.parse(row['public']); states=forecast_states(p,refs[p.sample_id])
                for i in (0,len(states)-2):
                    ns.append(layout.flatten(states[i],p.input)); targets.append(layout.flatten(states[i+1],p.input)); es.append(run.embedding(p.sample_id))
                    starts.append(states[i]['timestamp']); ends.append(states[i+1]['timestamp']); identities.append({'sample_id':p.sample_id,'scenario_id':row['scenario_id'],'start':starts[-1],'end':ends[-1]})
            n=torch.tensor(ns); target_n=torch.tensor(targets); e=torch.tensor(es); times=torch.tensor(starts)[:,None]
            x,target,p=model.projection.pair(n,target_n,e,layout_sha256=layout.sha256)
            squared=(rk4(model,x,starts,ends,solver,SolveStats())-target).square(); named=list(model.named_parameters()); blocks={}
            for name,cols in groups.items():
                loss=squared[:,cols].sum()/squared.numel(); gs=torch.autograd.grad(loss,[p for k,p in named],retain_graph=True,allow_unused=True)
                norm=lambda selected:float(torch.sqrt(sum(g.square().sum() for (k,p),g in zip(named,gs) if g is not None and selected(k))))
                blocks[name]={'raw_augmented_loss_contribution':float(loss.detach()),'parameter_gradient_norm':norm(lambda k:True),
                    'projection_gradient_norm':norm(lambda k:k.startswith('projection.')),'vector_field_gradient_norm':norm(lambda k:k.startswith('field.'))}
            with torch.no_grad():
                z=torch.cat((model.conditioning(n) if model.conditioning is not None else n,p,times),dim=-1)
                h1=model.field[1](model.field[0](z)); h2=model.field[3](model.field[2](h1)); derivative=model(times,x)
                # Deliberate diagnostic interventions, not forecast conditions.
                varying_p=model(times[:1].expand(len(n),1),torch.cat((n[:1].expand_as(n),p),dim=-1))
                varying_n=model(times,torch.cat((n,p[:1].expand_as(p)),dim=-1))
            record={'method':variant,'split':split,'mode':'evaluation_gradients_no_training_or_selection','examples':identities,'blocks':blocks,
                'tanh1_saturation':float((h1.abs()>.99).float().mean()),'tanh2_saturation':float((h2.abs()>.99).float().mean()),
                'physical_derivative_range_by_coordinate':(derivative[:,groups['physical']].max(0).values-derivative[:,groups['physical']].min(0).values).tolist(),
                'context_only_physical_derivative_max_difference':float((varying_p[:,groups['physical']]-varying_p[:1,groups['physical']]).abs().max()),
                'state_time_only_physical_derivative_max_difference':float((varying_n[:,groups['physical']]-varying_n[:1,groups['physical']]).abs().max()),
                'interpretation':'Sensitivity diagnostic only; context swaps can be counterfactual. Neither variation nor error reduction proves text usefulness or chaos.'}
            records.append(record)
        if any(not torch.equal(v,model.state_dict()[k]) for k,v in before.items()): raise ValueError('diagnostic_changed_checkpoint_parameters')
    coverage=[]
    for row in run.rows():
        if row['split']!='train': continue
        p=PublicProblem.parse(row['public']); times=grid(p)
        for event in p.input.get('known_events',[]):
            if 'start_time' not in event or 'end_time' not in event: continue
            for label,intervals in [('early',list(zip(times,times[1:]))[:20]),('full',list(zip(times,times[1:])))]:
                counts=Counter('before_event' if (a+b)/2<event['start_time'] else 'within_event' if (a+b)/2<event['end_time'] else 'after_event' for a,b in intervals)
                coverage.append({'sample_id':p.sample_id,'scenario_id':row['scenario_id'],'coverage':label,'public_event':event,'interval_counts':dict(counts),
                    'straddling_intervals':[(a,b) for a,b in intervals if any(a<t<b for t in (event['start_time'],event['end_time']))]})
    save(run.root/'diagnostics/selected_gradients_and_sensitivity.json',{'records':records,'optimizer_updates':0,'selection_unchanged':True,'physical_coordinate_indices':groups['physical']})
    save(run.root/'diagnostics/public_event_training_coverage.json',coverage)
