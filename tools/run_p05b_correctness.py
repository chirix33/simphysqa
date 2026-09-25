"""Three independent bounded fits; no validation reference access or live calls."""
import argparse
from collections import Counter
from dataclasses import asdict
import json
from pathlib import Path
import sys
import time
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'src'))
import torch
from phi_jepa.artifacts import canonical,digest,code_provenance
from phi_jepa.integration.contracts import PublicProblem
from phi_jepa.integration.layout import StateLayout
from phi_jepa.integration.readers import ReleaseCatalog,make_pairs,forecast_states
from phi_jepa.providers.context import ContextEncoder
from phi_jepa.providers.qwen import QwenEncoder
from phi_jepa.providers.cache import FrozenOutputCache
from phi_jepa.baselines.conventional import NumericalComparator,BaselineSettings,forecast
from phi_jepa.baselines.training import ComparatorTrainer,validate_pairs
from phi_jepa.baselines.checkpoint import save_checkpoint,load_checkpoint
from phi_jepa.inference.readout import named_forecast,read_targets


def save(path,value): path.write_bytes(canonical(value))


def main():
    parser=argparse.ArgumentParser()
    parser.add_argument('--resume',action='store_true')
    for name in ('profile','primary_run','cache_dir','output'): parser.add_argument('--'+name.replace('_','-'),type=Path,required=True)
    args=parser.parse_args(); root=Path(__file__).resolve().parents[1]
    args.output.mkdir(parents=True,exist_ok=args.resume); torch.set_num_threads(2); torch.manual_seed(11)
    config=json.loads((root/'configs/baselines_p05b.json').read_text()); limits=config['correctness']; domain=limits['domain']
    if limits['max_pairs']>20 or limits['max_neural_updates_per_method']>200 or limits['max_seconds_per_method']>900 or limits['lr_fits']!=1: raise ValueError('correctness_budget')
    primary=json.loads((args.primary_run/'summary.json').read_text())
    selected={r['split']:r for r in json.loads((args.profile/'selected-public.json').read_text()) if r['domain']==domain}
    problems={split:PublicProblem.parse(row['public']) for split,row in selected.items()}
    context=json.loads((root/'configs/model_context_p02b.json').read_text())
    manifest=json.loads((root/f'docs/reviews/artifacts/P02a/{domain}.state_plus_fixed_conditioning.json').read_text())
    layout=StateLayout.from_manifest(manifest,digest(manifest))
    encoder=ContextEncoder(QwenEncoder(str(args.cache_dir),runtime_versions=context['encoder']['runtime_versions'],load_model=False),FrozenOutputCache(args.profile/'embedding-cache'))
    encoded={}; enrichments={}
    for split,p in problems.items():
        enrichment=json.loads((args.profile/'enrichment'/(p.sample_id+'.json')).read_text()); enrichments[split]=enrichment
        encoded[split]=encoder.encode(p,p.input['observation_cutoff'],mode='enriched',enrichment=enrichment)
        if not encoded[split].cache_hit: raise ValueError('existing_frozen_E_cache_required')
    release=json.loads((root/'configs/model_training_p02a.json').read_text())
    catalog=ReleaseCatalog(root/release['export_root'],release['export_index_sha256'],release['release_manifest_sha256'])
    p,reference,identity=next(row for row in catalog.records(domain,'train') if row[0].sample_id==problems['train'].sample_id)
    if p!=problems['train']: raise ValueError('train_public_identity')
    states=forecast_states(p,reference)
    counts=Counter({digest((domain,identity.group_id,a['timestamp'],b['timestamp'])):1 for a,b in zip(states,states[1:])})
    pairs=list(make_pairs(p,reference,identity,layout,digest(primary['provenance']),counts,context_mode='enriched',enrichment=enrichments['train'],duplicate_policy='equal_question_pairs'))[:limits['max_pairs']]
    if [p.pair_id for p in pairs]!=primary['provenance']['pair_ids']: raise ValueError('primary_pair_selection_mismatch')
    val=problems['validation']; grid=[round(i*.02,8) for i in range(round(val.input['observation_cutoff']/.02),round(max(t['end_time'] for t in val.input['answer_spec'])/.02)+1)]
    train_e=torch.tensor([encoded['train'].values]*len(pairs)); val_e=torch.tensor([encoded['validation'].values])
    provenance={'training_pair_ids':[p.pair_id for p in pairs],'transition_ids':[p.transition_id for p in pairs],
        'training_scenario':identity.group_id,'validation_sample_id':val.sample_id,'context_requests':{k:v.request_sha256 for k,v in encoded.items()},
        'config_sha256':digest(config),'source':code_provenance(),'primary_weights_loaded':False}
    summaries={}
    for method in config['methods']:
        directory=args.output/method
        if args.resume and (directory/'summary.json').exists():
            _,_,_,stored=load_checkpoint(directory/'deployment',layout=layout,context_identity=primary['context_identity'],method=method,training=False)
            if stored['config_sha256']!=digest(config) or stored['training_pair_ids']!=provenance['training_pair_ids']: raise ValueError('resume_provenance')
            summaries[method]=json.loads((directory/'summary.json').read_text()); continue
        if args.resume and (directory/'deployment/latest.json').exists():
            if method!='fixed_projection_lr': raise ValueError('incomplete_neural_run_requires_explicit_resume')
            model,_,_,stored=load_checkpoint(directory/'deployment',layout=layout,context_identity=primary['context_identity'],method=method,training=False)
            if stored['config_sha256']!=digest(config) or stored['training_pair_ids']!=provenance['training_pair_ids']: raise ValueError('resume_provenance')
            current,target=validate_pairs(model,pairs,train_e)
            report={'method':method,'fit':model.lr_diagnostics(current,target,train_e),'fit_seconds':None,
                'projection_changed':False,'parameter_count':sum(p.numel() for p in model.parameters()),'trainable_parameter_count':0,
                'deployment_checkpoint':json.loads((directory/'deployment/latest.json').read_text()),
                'training_checkpoint':json.loads((directory/'training/latest.json').read_text()),
                'forecast_usage':{'forecast_steps':40,'discrete_model_calls':40,'solver':{'solves':0,'sample_intervals':0,'nfe':0,'sample_nfe':0,'failures':0}},
                'recovered_reporting_failure':'NumPy bool rank-deficient flag was not JSON serializable; fit duration unavailable; no repeated fit or forecast'}
            if len(json.loads((directory/'trajectory.json').read_text())['predictions'])!=40: raise ValueError('recovery_trajectory_count')
            save(directory/'summary.json',report); summaries[method]=report; print(json.dumps(report),flush=True); continue
        directory.mkdir()
        settings=BaselineSettings(method,**{k:config[k] for k in ('embedding_width','hidden_width','seed','interval_seconds','lr_rcond')})
        model=NumericalComparator(layout,settings); initial_projection=model.projection.linear.weight.detach().clone()
        start=time.perf_counter(); history=[]; trainer=None
        if method=='fixed_projection_lr':
            current,target=validate_pairs(model,pairs,train_e)
            fit=model.fit_lr(current,target,train_e)
        else:
            trainer=ComparatorTrainer(model,learning_rate=config['learning_rate'],gradient_clip=config['gradient_clip'])
            for update in range(limits['max_neural_updates_per_method']):
                if time.perf_counter()-start>=limits['max_seconds_per_method']: break
                history.append(trainer.step(pairs,train_e))
                if trainer.updates==100:
                    save_checkpoint(directory/'training',model,context_identity=primary['context_identity'],provenance=provenance,trainer=trainer,sampler={'updates':100})
                    model,trainer,_,_=load_checkpoint(directory/'training',layout=layout,context_identity=primary['context_identity'],method=method,training=True)
            fit={'updates':trainer.updates,'attempts':trainer.attempts,'failures':trainer.failures,
                'initial_numerical_mse':history[0]['numerical_mse'],'final_preupdate_numerical_mse':history[-1]['numerical_mse'],
                'projection_gradient_norm_range':[min(h['projection_gradient_norm_after_clip'] for h in history),max(h['projection_gradient_norm_after_clip'] for h in history)],
                'solver':trainer.stats.manifest(),'recurrent_calls':trainer.recurrent_calls}
        seconds=time.perf_counter()-start
        projection_changed=not torch.equal(initial_projection,model.projection.linear.weight)
        if projection_changed==(method=='fixed_projection_lr'): raise ValueError('projection_fitting_policy')
        train_pointer=save_checkpoint(directory/'training',model,context_identity=primary['context_identity'],provenance=provenance,trainer=trainer,sampler={'updates':trainer.updates if trainer else 0})
        deploy_pointer=save_checkpoint(directory/'deployment',model,context_identity=primary['context_identity'],provenance=provenance,deployment=True)
        model,_,_,_=load_checkpoint(directory/'deployment',layout=layout,context_identity=primary['context_identity'],method=method,training=False)
        predicted,usage=forecast(model,val,val_e,grid)
        named=named_forecast(val,layout,predicted,numerical_only=True); readout=read_targets(val,named)
        save(directory/'trajectory.json',asdict(predicted)); save(directory/'named-forecast.json',named); save(directory/'readout.json',readout); save(directory/'training-history.json',history)
        report={'method':method,'fit':fit,'fit_seconds':seconds,'projection_changed':projection_changed,'parameter_count':sum(p.numel() for p in model.parameters()),
            'trainable_parameter_count':sum(p.numel() for p in model.parameters() if p.requires_grad),'deployment_checkpoint':deploy_pointer,'training_checkpoint':train_pointer,'forecast_usage':usage}
        save(directory/'summary.json',report); summaries[method]=report; print(json.dumps(report),flush=True)
    summary={'phase':'P05b','config':config,'provenance':provenance,'context_identity':primary['context_identity'],
        'encoder_cache':encoder.coverage,'methods':summaries,'training_examples':len(pairs),'training_questions':1,
        'validation_questions':1,'scope':'bounded correctness only; no benchmark claims','api_calls':0,'full_training':False}
    save(args.output/'summary.json',summary)
    save(args.output/'validation-public.json',{'sample_id':val.sample_id,'schema_version':val.schema_version,'input':val.input})


if __name__=='__main__': main()
