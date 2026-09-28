"""Read-only P08 diagnostics. No optimizer, provider, model download or generation.

Writes only the new Post_P08_diagnosis directory. References are evaluator-only.
Gradient allowance: two saved primary checkpoints, four questions, four pairs
per question. CPU only; all full gradients use the unchanged augmented loss.
"""
import csv
import json
import math
import time
import subprocess
from collections import Counter, defaultdict
from pathlib import Path
import torch
from p08_common import ROOT, RUN, CONFIG, layout
from phi_jepa.integration.contracts import PublicProblem
from phi_jepa.integration.readers import forecast_states, file_hash
from phi_jepa.training.checkpoint import load_checkpoint
from phi_jepa.solvers.rk4 import rk4, SolveStats
from phi_jepa.artifacts import digest

OUT = ROOT/'docs/reviews/artifacts/Post_P08_diagnosis'
SOURCES = {}


def read(path):
    SOURCES[str(path)] = file_hash(path)
    return json.loads(path.read_text())


def write(name, value):
    (OUT/name).write_text(json.dumps(value, indent=2, allow_nan=False)+'\n')


def table(name, rows):
    with (OUT/name).open('w', newline='') as f:
        w = csv.DictWriter(f, fieldnames=list(rows[0])); w.writeheader(); w.writerows(rows)


def phase(t, event):
    a, b = event['start_time'], event['end_time']
    return 'pre_event' if t < a else 'positive_acceleration' if t < a+.1 else 'negative_acceleration' if t < b else 'post_event'


def main():
    start = time.perf_counter(); torch.set_num_threads(2)
    OUT.mkdir(parents=True, exist_ok=True)
    rows = read(RUN/'selected-public.json'); val = [r for r in rows if r['split']=='validation']; train = [r for r in rows if r['split']=='train']
    assert len(train)==32 and len(val)==8 and not ({r['scenario_id'] for r in train}&{r['scenario_id'] for r in val})
    refs = read(RUN/'private/train-references.json') | read(RUN/'private/validation-references.json')
    errors=[]; regimes=[]
    for r in rows:
        event=r['public']['input']['known_events'][0]
        # Count intervals by midpoint; retain exact intervals straddling boundaries.
        intervals=[(.2+.02*i,.22+.02*i) for i in range(20)]
        regimes.append({'sample_id':r['sample_id'],'scenario_id':r['scenario_id'],'split':r['split'],
            'event':event,'controller':r['public']['input']['controller'],
            'selected_training_intervals':20 if r['split']=='train' else 0,
            'training_regime_counts':dict(Counter(phase((a+b)/2,event) for a,b in intervals)) if r['split']=='train' else {},
            'boundary_straddling_intervals':[(round(a,8),round(b,8)) for a,b in intervals if any(a<t<b for t in (event['start_time'],event['start_time']+.1,event['end_time']))] if r['split']=='train' else []})
    for method in [*CONFIG['numerical_methods'],'hold_last']:
        for r in val:
            path=RUN/'evaluation'/('hold-last' if method=='hold_last' else 'numerical/'+method)/(r['sample_id']+'.json')
            for e in read(path)['physical']['per_time_channel']:
                errors.append({'method':method,'scenario_id':r['scenario_id'],'sample_id':r['sample_id'],**e,
                    'window':'(0.20,0.60]' if e['time']<=.60000001 else '(0.60,1.00]',
                    'regime':phase(e['time'],r['public']['input']['known_events'][0])})
    table('physical_errors_by_time.csv', errors)
    groups=defaultdict(list)
    for e in errors:
        for sid in (e['scenario_id'],'ALL'):
            for win in (e['window'],'full_horizon'):
                groups[(e['method'],sid,e['entity_id'],e['quantity'],e['unit'],win)].append(e)
    windows=[]
    for key, values in groups.items():
        good=[e['error'] for e in values if e['status']=='valid']
        windows.append(dict(zip(('method','scenario_id','entity_id','quantity','unit','window'),key)) | {
            'eligible':len(values),'valid':len(good),'rmse':math.sqrt(sum(x*x for x in good)/len(good)) if good else None,
            'max_error':max(good) if good else None})
    table('physical_errors_by_window.csv',windows); write('scheduled_regimes.json',regimes)
    curves=[]
    for method in CONFIG['numerical_methods']:
        f=RUN/'numerical'/method; h=read(f/'history.json'); fit=read(f/'fit.json')
        if method=='fixed_projection_lr': curves.append({'method':method,'fit':h,'checkpoint':fit['deployment_checkpoint']}); continue
        losses=[x.get('loss',x.get('numerical_mse')) for x in h]
        curves.append({'method':method,'updates':len(h),'batch_exposure':dict(Counter(x['sample_id'] for x in h)),
            'transitions_per_update':sorted({x.get('batch_size',x.get('transitions')) for x in h}),
            'loss_first':losses[0],'loss_last':losses[-1],
            'loss_means_by_100':[sum(losses[i:i+100])/len(losses[i:i+100]) for i in range(0,len(h),100)],
            'gradient_clip':1.,'clip_exceeded_updates':sum(x['gradient_norm_before_clip']>1 for x in h),
            'gradient_norm_min_max':[min(x['gradient_norm_before_clip'] for x in h),max(x['gradient_norm_before_clip'] for x in h)],
            'checkpoint_policy':'last configured update; no validation checkpoint selection','checkpoint':fit['deployment_checkpoint']})
    write('training_exposure_and_curves.json',curves)
    # Inspect exact serialized targets and saved strict failures; never repair or rescore.
    from phi_jepa.baselines.custom_io import training_targets
    target_rows=[]
    for r in train:
        teacher,student=training_targets(PublicProblem.parse(r['public']),refs[r['sample_id']])
        target_rows.append({'sample_id':r['sample_id'],'teacher_target':teacher,'student_target':student})
    write('training_target_trace.json',target_rows)
    gen=[]
    for method in ('coconut_inspired_t5_gru','codi_inspired_t5_distillation'):
        for r in val:
            g=read(RUN/'custom'/method/'broad/generations'/f"180-{r['sample_id']}.json")
            specs={x['target_id']:x for x in r['public']['input']['answer_spec']}
            for branch,b in g['branches'].items():
                parsed=json.loads(b['text']) if b.get('text') else {}; ts=parsed.get('targets',[]); ids=[x.get('target_id') for x in ts if isinstance(x,dict)]
                from phi_jepa.inference.readout import BINDING
                gen.append({'method':method,'branch':branch,'sample_id':r['sample_id'],'strict_status':b['status'],'strict_reason':b.get('reason'),
                    'EOS_terminated':b['EOS_terminated'],'envelope_keys':list(parsed),'expected_ids':list(specs),'emitted_ids':ids,
                    'omitted_ids':sorted(set(specs)-set(ids)),'duplicated_ids':{k:v for k,v in Counter(ids).items() if v>1},
                    'binding_errors':[{'row':i,'target_id':x.get('target_id'),'fields':[k for k in BINDING if x.get(k)!=specs.get(x.get('target_id'),{}).get(k)]} for i,x in enumerate(ts) if isinstance(x,dict) and any(x.get(k)!=specs.get(x.get('target_id'),{}).get(k) for k in BINDING)],
                    'raw_text':b.get('text'),'diagnostic_only_no_rescoring':True})
    write('generation_failure_trace.json',gen)
    # Frozen primary gradients and field diagnostics, no optimizer construction/update.
    l=layout(); f=RUN/'numerical/phi_jepa'; info=read(f/'fit.json')
    model,solver=load_checkpoint(f/'deployment',layout=l,context_identity=info['context_identity'],training=False)
    latest=read(f/'deployment/latest.json'); SOURCES[str(f/'deployment'/latest['file'])]=file_hash(f/'deployment'/latest['file'])
    final={k:v.clone() for k,v in model.state_dict().items()}; snapshots={1000:final}
    for path in sorted((f/'training').glob('*.pt')):
        bundle=torch.load(path,map_location='cpu',weights_only=True)
        if bundle['updates']==100:
            snapshots[100]=bundle['state']; SOURCES[str(path)]=file_hash(path)
            write('optimizer_settings.json',{'training_settings':bundle['training_settings'],'param_groups':[{k:v for k,v in g.items() if k!='params'} for g in bundle['optimizer']['param_groups']]})
            break
    blocks=defaultdict(list)
    for i,(path,typ) in enumerate(l.entries):
        block='fixed_conditioning' if path[0]==('key','fixed_conditioning') else 'time_index' if path[-1] in (('key','step_index'),('key','timestamp')) else 'physical'
        blocks[block].append(i)
    blocks['contextual']=list(range(l.d,2*l.d)); measurements=[]; derivative=[]
    for step,state in sorted(snapshots.items()):
        model.load_state_dict(state); model.eval(); before=digest({k:v.tolist() for k,v in model.state_dict().items()})
        params=list(model.parameters()); names=[k for k,v in model.named_parameters()]
        chosen=[*train[:2],*val[:2]]
        for r in chosen:
            p=PublicProblem.parse(r['public']); states=forecast_states(p,refs[r['sample_id']]); inds=[0,10,19,30]
            current=torch.tensor([l.flatten(states[i],p.input) for i in inds]); target_n=torch.tensor([l.flatten(states[i+1],p.input) for i in inds])
            e=torch.tensor([read(RUN/'embeddings/enriched'/f"{r['sample_id']}.json")['values']]*4)
            x,target,_=model.projection.pair(current,target_n,e,layout_sha256=l.sha256)
            pred=rk4(model,x,[states[i]['timestamp'] for i in inds],[states[i+1]['timestamp'] for i in inds],solver,SolveStats())
            sq=(pred-target).square(); gs={}; losses={}
            for block,cols in blocks.items():
                loss=sq[:,cols].sum()/sq.numel(); losses[block]=float(loss.detach())
                grads=torch.autograd.grad(loss,params,retain_graph=True,allow_unused=True)
                gs[block]=[torch.zeros_like(par) if g is None else g for par,g in zip(params,grads)]
            full=torch.cat([g.flatten() for g in torch.autograd.grad(sq.mean(),params,allow_unused=False)])
            for block,gs0 in gs.items():
                flat=torch.cat([g.flatten() for g in gs0]); norm=float(flat.norm()); fn=float(full.norm())
                measurements.append({'checkpoint_update':step,'sample_id':r['sample_id'],'split':r['split'],'pair_start_times':[states[i]['timestamp'] for i in inds],
                    'block':block,'width':len(blocks[block]),'full_loss_contribution':losses[block],
                    'full_loss':sum(losses.values()),'gradient_norm':norm,'full_gradient_norm':fn,
                    'projection_gradient_norm':float(torch.cat([g.flatten() for name,g in zip(names,gs0) if name.startswith('projection.')]).norm()),
                    'cosine_to_full_gradient':float(torch.dot(flat,full)/(flat.norm()*full.norm())) if norm*fn>0 else None,
                    'hypothetical_common_clip_multiplier':min(1.,1./(fn+1e-6)),'optimizer_updates':0})
            with torch.no_grad():
                times=torch.tensor([[states[i]['timestamp']] for i in inds]); fields=model(times,x)
                alt=chosen[(chosen.index(r)+1)%len(chosen)]
                other=torch.tensor([read(RUN/'embeddings/enriched'/f"{alt['sample_id']}.json")['values']]*4)
                swapped=torch.cat((current,model.projection(other)),dim=-1); delta=model(times,swapped)-fields
                a1=model.field[1](model.field[0](torch.cat((x,times),dim=-1))); a2=model.field[3](model.field[2](a1))
                derivative.append({'checkpoint_update':step,'sample_id':r['sample_id'],'times':times.flatten().tolist(),
                    'field_by_coordinate':fields.tolist(),'coordinate_names':[str(path) for path,typ in l.entries]+['context_'+str(i) for i in range(l.d)],
                    'physical_derivative_max_span_across_recorded_states':float((fields[:,blocks['physical']].max(0).values-fields[:,blocks['physical']].min(0).values).abs().max()),
                    'physical_derivative_max_change_context_swap':float(delta[:,blocks['physical']].abs().max()),
                    'tanh1_fraction_abs_gt_099':float((a1.abs()>.99).float().mean()),'tanh2_fraction_abs_gt_099':float((a2.abs()>.99).float().mean()),
                    'caution':'counterfactual cached-context swap; not text usefulness or causal proof'})
        assert before==digest({k:v.tolist() for k,v in model.state_dict().items()})
    write('gradient_blocks.json',measurements); write('derivative_variation.json',derivative)
    for path,sha in SOURCES.items(): assert file_hash(Path(path))==sha
    write('manifest.json',{'source_commit':subprocess.check_output(['git','rev-parse','HEAD'],cwd=ROOT,text=True).strip(),
        'sources':SOURCES,'script_sha256':file_hash(Path(__file__)),'seconds':time.perf_counter()-start,
        'training_updates':0,'provider_calls':0,'new_generations':0,'device':'cpu','threads':2,
        'gradient_pairs':len(snapshots)*4*4,'original_sources_unchanged':True})
    print(json.dumps({'out':str(OUT),'seconds':time.perf_counter()-start,'errors':len(errors),'gradient_rows':len(measurements)}))


if __name__=='__main__': main()
