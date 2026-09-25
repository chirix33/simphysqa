"""Bounded source/artifact audit. No optimizer steps, GPU/encoder/provider calls."""
import argparse,json,sys,math
from pathlib import Path
from copy import deepcopy
from collections import Counter
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'src'))
import torch
from phi_jepa.artifacts import canonical,digest
from phi_jepa.integration.contracts import PublicProblem,DOMAINS
from phi_jepa.integration.layout import StateLayout
from phi_jepa.integration.readers import ReleaseCatalog,PublicInputReader,file_hash,forecast_states,make_pairs
from phi_jepa.providers.context import ContextEncoder
from phi_jepa.providers.cache import FrozenOutputCache
from phi_jepa.providers.qwen import QwenEncoder
from phi_jepa.training.checkpoint import load_checkpoint
from phi_jepa.solvers.rk4 import rk4,SolveStats
from phi_jepa.inference.rollout import rollout
from phi_jepa.inference.readout import read_targets
from phi_jepa.typed_evaluation import trajectory_errors,physical_error
from phi_jepa.coordinate_diagnostics import decompose,coordinate_unit

def load(p): return json.loads(p.read_text())
def save(p,x): p.write_bytes(canonical(x))

def main():
    parser=argparse.ArgumentParser(); parser.add_argument('--native-root',type=Path,required=True); parser.add_argument('--output',type=Path,required=True); args=parser.parse_args()
    args.output.mkdir(parents=True,exist_ok=False); out=args.output; root=Path(__file__).resolve().parents[1]; native=args.native_root
    torch.set_num_threads(2); torch.manual_seed(11)
    r=load(root/'configs/model_training_p02a.json'); catalog=ReleaseCatalog(root/r['export_root'],r['export_index_sha256'],r['release_manifest_sha256'])
    pilot=load(root/'configs/pilot_p07.json'); primary=native/'p03-correctness-01'; profile=native/'p02b-profile'
    summary=load(primary/'summary.json'); layout_data=load(root/'docs/reviews/artifacts/P02a/tethered_load.state_plus_fixed_conditioning.json'); layout=StateLayout.from_manifest(layout_data,digest(layout_data))
    model,solver=load_checkpoint(primary/'deployment',layout=layout,context_identity=summary['context_identity'],training=False)
    context=load(root/'configs/model_context_p02b.json'); backend=QwenEncoder(str(native/'model-cache'),runtime_versions=context['encoder']['runtime_versions'],load_model=False)
    def forbid(*args,**kwargs): raise RuntimeError('audit_forbids_new_encoder_call')
    backend.encode_tokens=forbid; encoder=ContextEncoder(backend,FrozenOutputCache(profile/'embedding-cache'))
    examples={}; encodings={}
    for split in ('train','validation'):
        sid=pilot['training_sample_id' if split=='train' else 'validation_sample_id']
        examples[split]=next(x for x in catalog.records('tethered_load',split) if x[0].sample_id==sid)
        p,ref,identity=examples[split]; enrichment=load(profile/'enrichment'/f'{sid}.json')
        encodings[split]=encoder.encode(p,p.input['observation_cutoff'],mode='enriched',enrichment=enrichment)
        if not encodings[split].cache_hit: raise ValueError('cache_required')
    p,ref,identity=examples['train']; states=forecast_states(p,ref)
    mult=Counter({digest(('tethered_load',identity.group_id,a['timestamp'],b['timestamp'])):3 for a,b in zip(states,states[1:])})
    pairs=list(make_pairs(p,ref,identity,layout,'audit',mult,context_mode='enriched',enrichment=load(profile/'enrichment'/f'{p.sample_id}.json')))[:20]
    if [x.pair_id for x in pairs]!=summary['provenance']['pair_ids']: raise ValueError('actual_training_pair_identity')
    e=torch.tensor([encodings['train'].values]); n=torch.tensor([pairs[0].n_current]); y=torch.tensor([pairs[0].n_next]); x,target,projected=model.projection.pair(n,y,e,layout_sha256=layout.sha256)
    stats=SolveStats(); predicted=rk4(model,x,pairs[0].start_time,pairs[0].end_time,solver,stats); loss=(predicted-target).square().mean(); w=model.projection.linear.weight
    grad=torch.autograd.grad(loss,w,retain_graph=True)[0]; incoming=torch.autograd.grad((predicted-target.detach()).square().mean(),w,retain_graph=True)[0]; outgoing=torch.autograd.grad((predicted.detach()-target).square().mean(),w)[0]
    pval,refval,ival=examples['validation']; statesval=forecast_states(pval,refval); inp=pval.input
    current=torch.tensor([layout.flatten(s,inp) for s in statesval[:-1]]); truth=torch.tensor([layout.flatten(s,inp) for s in statesval[1:]])
    emb=torch.tensor([encodings['validation'].values]*len(current)); times=[s['timestamp'] for s in statesval]
    with torch.no_grad(): one=rk4(model,torch.cat((current,model.projection(emb)),dim=-1),times[:-1],times[1:],solver,stats)
    saved=load(primary/'autonomous-trajectory.json'); auto=torch.tensor([v['values'] for v in saved['predictions']]); starts=[]; old=model.forward
    def traced(t,x):
        starts.append((t.detach().clone(),x.detach().clone())); return old(t,x)
    model.forward=traced
    replay=rollout(model,pval,emb[:1],times,solver,stats); model.forward=old
    assert [v.values for v in replay.predictions]==[tuple(v['values']) for v in saved['predictions']]
    assert all(torch.equal(starts[4*i][1][0],auto[i-1]) for i in range(1,len(auto)))
    structure={path:value for path,typ,value in layout.structure}; columns=[]
    for path,typ in layout.entries:
        group='fixed_conditioning' if path[0]==('key','fixed_conditioning') else ('state_time_index' if path[-1] in (('key','timestamp'),('key','step_index')) else 'physical_state')
        columns.append({'name':'/'.join(':'.join(map(str,x)) for x in path),'group':group,'unit':coordinate_unit(path,structure),'reference_type':typ})
    diagnostics={name:decompose(values[:,:layout.d].double().tolist(),truth.double().tolist(),columns) for name,values in [('one_step',one),('autonomous',auto)]}
    save(out/'coordinate-errors.json',diagnostics)
    lines=['# Coordinate error breakdown','', 'Each contribution is coordinate MSE divided by d=140; contributions sum to raw numerical MSE. Mixed units are not a physical metric. Targets are recorded next states at the exact external times.','', '| Mode | Coordinate | Unit | Group | Prediction range | Target range | MSE contribution | Fraction |','| --- | --- | --- | --- | --- | --- | ---: | ---: |']
    for name,report in diagnostics.items():
        for row in sorted(report['coordinates'],key=lambda r:-r['raw_numerical_mse_contribution']):
            lines.append(f"| {name} | {row['name']} | {row['unit']} | {row['group']} | {row['prediction_range']} | {row['target_range']} | {row['raw_numerical_mse_contribution']:.12g} | {row['fraction_of_raw_mse']:.8%} |")
    (out/'Coordinate_error_breakdown.md').write_text('\n'.join(lines)+'\n')
    named=load(native/'p04a-answers-01/named-forecast.json'); hold=deepcopy(named)
    measurements=[m for m in inp['states'][-1]['measurements'] if type(m['value']) is not bool]
    for row in hold['states']: row['measurements']=deepcopy(measurements)
    hold_errors=trajectory_errors(hold['states'],refval['states'],mode='autonomous')
    hold_targets=read_targets(pval,hold); auto_targets=read_targets(pval,named)
    physical_diagnostic={'label':'hold_last_observed_physical_state_diagnostic_not_paper_baseline','trajectory':hold_errors,'endpoint_targets':[{**t,'truth_error':physical_error(t['value'],next(r['value'] for r in refval['structured_label'] if r['target_id']==t['target_id']),t['quantity'])[0]} for t in hold_targets if t['answer_type']!='boolean'],'model_trajectory':trajectory_errors(named['states'],refval['states'],mode='autonomous')}
    save(out/'hold-last-physical.json',physical_diagnostic)
    reversed_forecast=deepcopy(named)
    for a,b in zip(reversed_forecast['states'],reversed(named['states'])): a['measurements']=deepcopy(b['measurements'])
    rev=read_targets(pval,reversed_forecast); answers={k:load(native/'p04a-answers-01'/f'{k}.json')['answer']['targets'] for k in ('predicted','public_only','reversed_forecast')}
    controls=[]
    for spec,a,b in zip(inp['answer_spec'],auto_targets,rev):
        gold=next(r['value'] for r in refval['structured_label'] if r['target_id']==spec['target_id'])
        tolerance=spec['absolute_tolerance']+spec['relative_tolerance']*(math.hypot(*gold) if isinstance(gold,list) else abs(gold))
        delta=physical_error(a['value'],b['value'],spec['quantity'])[0]
        controls.append({'target_id':spec['target_id'],'unit':spec['unit'],'type':spec['answer_type'],'prediction':a['value'],'reversed_prediction':b['value'],'change':delta,'existing_tolerance':tolerance,'change_over_tolerance':delta/tolerance if tolerance else None,'answer_errors':{k:physical_error(next(r['value'] for r in rows if r['target_id']==spec['target_id']),gold,spec['quantity'])[0] if next(r['status'] for r in rows if r['target_id']==spec['target_id'])=='supported' else None for k,rows in answers.items()}})
    save(out/'controls-common-targets.json',{'rows':controls,'common_target_ids':[r['target_id'] for r in controls if all(v is not None for v in r['answer_errors'].values())],'common_comparison':'three numerical targets; Boolean public-only deliberately unsupported; no changed tolerance'})
    trace={'sample_id':p.sample_id,'pair_id':pairs[0].pair_id,'start_state_id':pairs[0].start_state_id,'end_state_id':pairs[0].end_state_id,'interval':[pairs[0].start_time,pairs[0].end_time],'d':layout.d,'embedding_width':len(e[0]),'p_width':projected.shape[1],'augmented_width':x.shape[1],'same_p_values':torch.equal(x[:,layout.d:],target[:,layout.d:]),'input_p_requires_grad':x.requires_grad,'target_p_requires_grad':target.requires_grad,'pair_weights':sorted(set(r.weight for r in pairs)),'gradient_norms':{'input':float(incoming.norm()),'target':float(outgoing.norm()),'sum_residual':float((grad-incoming-outgoing).norm())},'pair_loss':float(loss.detach()),'adjacent_alignment':all(a.n_next==b.n_current and a.end_time==b.start_time for a,b in zip(pairs,pairs[1:])),'exact_saved_autonomous_replay':True,'complete_predicted_feedback_verified':True,'external_grid':times,'reference_state_indices':[s['step_index'] for s in statesval],'encoder_cache':encoder.coverage,'encoding_identities':{k:vars(v)|{'values':'omitted; verified cache'} for k,v in encodings.items()},'solver_stats':stats.manifest(),'optimizer_steps':0,'heldout_scenario':ival.group_id,'training_scenario':identity.group_id}
    save(out/'primary-trace.json',trace); save(out/'derived-one-step-trajectory.json',{'physical_times':times[1:],'values':one.detach().tolist(),'mode':'recorded_input_diagnostic_not_autonomous'})
    inventory={}; event_types=Counter(); constraints=Counter()
    for domain in sorted(DOMAINS):
        for split in ('train','validation'):
            path=catalog.verified_file(domain,split,'inputs.jsonl')
            for problem in PublicInputReader(path,file_hash(path)):
                data=problem.input; constraints[domain]+=len(data['controller'].get('constraints',[]))
                for event in data['known_events']: event_types[(domain,str(event.get('event_type',event.get('type','unspecified'))))]+=1
                future=[{'timestamp':round(i*.02,8),'measurements':[m for m in data['states'][-1]['measurements'] if type(m['value']) is not bool]} for i in range(round(data['observation_cutoff']/.02)+1,round(max(s['end_time'] for s in data['answer_spec'])/.02)+1)]
                rows=read_targets(problem,{'sample_id':problem.sample_id,'states':future,'source':'autonomous_numeric_forecast'})
                for spec,result in zip(data['answer_spec'],rows):
                    key=(domain,spec['entity_id'],spec['quantity'],spec['answer_type'],spec['unit'],spec['frame'])
                    item=inventory.setdefault(key,{'domain':domain,'entity':spec['entity_id'],'quantity':spec['quantity'],'answer_type':spec['answer_type'],'unit':spec['unit'],'frame':spec['frame'],'rule':spec['rule_definition'],'questions':0,'qualified_public_interface':0,'unsupported_reasons':Counter()})
                    item['questions']+=1
                    if result['status']=='supported': item['qualified_public_interface']+=1
                    else: item['unsupported_reasons'][result['reason']]+=1
        print(json.dumps({'inventory_domain_completed':domain}),flush=True)
    save(out/'coverage-inventory.json',{'scope':'all 8038 train/validation public contexts; no held-out test/OOD outcomes; static interface qualification using a hypothetical complete constant numerical path, not a forecast performance measurement','targets':list(inventory.values()),'public_constraint_counts':dict(constraints),'known_event_types':[{'domain':d,'event_type':e,'count':v} for (d,e),v in event_types.items()]})
    print(json.dumps({'raw_mse':{k:v['raw_numerical_mse'] for k,v in diagnostics.items()},'top_coordinates':{k:sorted(v['coordinates'],key=lambda x:-x['raw_numerical_mse_contribution'])[:2] for k,v in diagnostics.items()},'trace':{k:v for k,v in trace.items() if k in ('gradient_norms','solver_stats','d','exact_saved_autonomous_replay')}}),flush=True)

if __name__=='__main__': main()
