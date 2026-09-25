"""Independent no-enrichment and numerical-only fits under approved per-method caps."""
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
from phi_jepa.models.augmented_ode import AugmentedODE,ODESettings
from phi_jepa.models.context_projection import ProjectionSettings
from phi_jepa.training.pairs import PairTrainer,TrainingSettings
from phi_jepa.training.checkpoint import write_checkpoint,load_checkpoint as load_primary
from phi_jepa.inference.rollout import rollout
from phi_jepa.solvers.rk4 import SolverSettings,SolveStats
from phi_jepa.baselines.conventional import NumericalComparator,BaselineSettings,forecast
from phi_jepa.baselines.training import ComparatorTrainer
from phi_jepa.baselines.checkpoint import save_checkpoint,load_checkpoint as load_baseline
from phi_jepa.inference.readout import named_forecast,read_targets


def save(path,value): path.write_bytes(canonical(value))


def main():
    parser=argparse.ArgumentParser()
    for name in ('profile','primary_run','cache_dir','output'): parser.add_argument('--'+name.replace('_','-'),type=Path,required=True)
    args=parser.parse_args(); root=Path(__file__).resolve().parents[1]; args.output.mkdir(parents=True,exist_ok=False)
    torch.set_num_threads(2); torch.manual_seed(11)
    config=json.loads((root/'configs/ablations_p05b.json').read_text())
    if config['max_pairs']>20 or config['max_updates_per_method']>200 or config['max_seconds_per_method']>900: raise ValueError('ablation_budget')
    primary=json.loads((args.primary_run/'summary.json').read_text()); domain='tethered_load'
    selected={r['split']:r for r in json.loads((args.profile/'selected-public.json').read_text()) if r['domain']==domain}
    problems={split:PublicProblem.parse(r['public']) for split,r in selected.items()}
    manifest=json.loads((root/f'docs/reviews/artifacts/P02a/{domain}.state_plus_fixed_conditioning.json').read_text()); layout=StateLayout.from_manifest(manifest,digest(manifest))
    context=json.loads((root/'configs/model_context_p02b.json').read_text())
    backend=QwenEncoder(str(args.cache_dir),runtime_versions=context['encoder']['runtime_versions'],load_model=False)
    encoder=ContextEncoder(backend,FrozenOutputCache(args.profile/'embedding-cache')); encoded={}
    for split,p in problems.items():
        encoded[split]=encoder.encode(p,p.input['observation_cutoff'],mode=config['context_mode'])
        if not encoded[split].cache_hit: raise ValueError('existing_base_context_cache_required')
    release=json.loads((root/'configs/model_training_p02a.json').read_text()); catalog=ReleaseCatalog(root/release['export_root'],release['export_index_sha256'],release['release_manifest_sha256'])
    p,reference,identity=next(r for r in catalog.records(domain,'train') if r[0].sample_id==problems['train'].sample_id)
    states=forecast_states(p,reference); counts=Counter({digest((domain,identity.group_id,a['timestamp'],b['timestamp'])):1 for a,b in zip(states,states[1:])})
    pairs=list(make_pairs(p,reference,identity,layout,'p05b-base',counts,context_mode=config['context_mode'],duplicate_policy='equal_question_pairs'))[:config['max_pairs']]
    if [r.transition_id for r in pairs]!=[digest((domain,identity.group_id,round(.2+.02*i,8),round(.22+.02*i,8))) for i in range(len(pairs))]: raise ValueError('transition_selection')
    if set(r.transition_id for r in pairs)!=set(primary['provenance']['unique_transition_ids']): raise ValueError('primary_transition_mismatch')
    val=problems['validation']; grid=[round(i*.02,8) for i in range(round(val.input['observation_cutoff']/.02),round(max(t['end_time'] for t in val.input['answer_spec'])/.02)+1)]
    base_identity={'variant':'no_enrichment','encoder':asdict(backend.settings),'context_mode':config['context_mode'],'generated_enrichment':'excluded'}
    numerical_identity={'variant':'no_text_conditioning','encoder':None,'projection':None,'contextual_state':None}
    identities={'no_enrichment':base_identity,'no_text_conditioning':numerical_identity}
    provenance={'source':code_provenance(),'config_sha256':digest(config),'primary_weights_loaded':False,
        'training_pair_ids':[r.pair_id for r in pairs],'transition_ids':[r.transition_id for r in pairs],
        'primary_pair_ids':primary['provenance']['pair_ids'],'training_scenario':identity.group_id,
        'validation_sample_id':val.sample_id,'base_context_request_ids':{k:v.request_sha256 for k,v in encoded.items()}}
    train_e=torch.tensor([encoded['train'].values]*len(pairs)); val_e=torch.tensor([encoded['validation'].values])
    solver=SolverSettings(**config['solver']); summaries={}
    for method in config['methods']:
        directory=args.output/method; directory.mkdir(); history=[]
        if method=='no_enrichment':
            model=AugmentedODE(layout,ProjectionSettings(1024,seed=config['seed']),ODESettings(hidden_width=config['hidden_width'],seed=config['seed']))
            trainer=PairTrainer(model,solver,TrainingSettings(context_mode=config['context_mode']))
        else:
            model=NumericalComparator(layout,BaselineSettings(method,embedding_width=0,hidden_width=config['hidden_width'],seed=config['seed']))
            trainer=ComparatorTrainer(model,solver=solver)
        start=time.perf_counter()
        for _ in range(config['max_updates_per_method']):
            if time.perf_counter()-start>=config['max_seconds_per_method']: break
            history.append(trainer.step(pairs,train_e if method=='no_enrichment' else None))
            if trainer.updates==100:
                if method=='no_enrichment':
                    write_checkpoint(directory/'training',trainer,context_identity=identities[method],provenance=provenance,sampler_state={'updates':100})
                    trainer,_,_=load_primary(directory/'training',layout=layout,context_identity=identities[method],training=True); model=trainer.model
                else:
                    save_checkpoint(directory/'training',model,context_identity=identities[method],provenance=provenance,trainer=trainer,sampler={'updates':100})
                    model,trainer,_,_=load_baseline(directory/'training',layout=layout,context_identity=identities[method],method=method,training=True)
        fit_seconds=time.perf_counter()-start
        if method=='no_enrichment':
            train_pointer=write_checkpoint(directory/'training',trainer,context_identity=identities[method],provenance=provenance,sampler_state={'updates':trainer.updates})
            deploy_pointer=write_checkpoint(directory/'deployment',trainer,context_identity=identities[method],provenance=provenance,sampler_state={},deployment=True)
            model,solver=load_primary(directory/'deployment',layout=layout,context_identity=identities[method],training=False)
            stats=SolveStats(); predicted=rollout(model,val,val_e,grid,solver,stats); usage={'solver':stats.manifest()}
            initial_loss,final_loss=history[0]['loss'],history[-1]['loss']
        else:
            train_pointer=save_checkpoint(directory/'training',model,context_identity=identities[method],provenance=provenance,trainer=trainer,sampler={'updates':trainer.updates})
            deploy_pointer=save_checkpoint(directory/'deployment',model,context_identity=identities[method],provenance=provenance,deployment=True)
            model,_,_,_=load_baseline(directory/'deployment',layout=layout,context_identity=identities[method],method=method,training=False)
            predicted,usage=forecast(model,val,None,grid,solver=solver)
            initial_loss,final_loss=history[0]['numerical_mse'],history[-1]['numerical_mse']
        named=named_forecast(val,layout,predicted,numerical_only=method=='no_text_conditioning')
        save(directory/'trajectory.json',asdict(predicted)); save(directory/'named-forecast.json',named); save(directory/'readout.json',read_targets(val,named)); save(directory/'training-history.json',history)
        report={'method':method,'kind':'independently_retrained_component_ablation','state_width':2*layout.d if method=='no_enrichment' else layout.d,
            'loss':'full_augmented_mse' if method=='no_enrichment' else 'numerical_mse','initial_loss':initial_loss,'final_preupdate_loss':final_loss,
            'updates':trainer.updates,'fit_seconds':fit_seconds,'parameter_count':sum(p.numel() for p in model.parameters()),
            'training_stats':trainer.stats.manifest(),'forecast_usage':usage,'training_checkpoint':train_pointer,'deployment_checkpoint':deploy_pointer}
        save(directory/'summary.json',report); summaries[method]=report; print(json.dumps(report),flush=True)
    save(args.output/'summary.json',{'config':config,'provenance':provenance,'identities':identities,'methods':summaries,'encoder_cache':encoder.coverage,
        'scope':'bounded correctness only; no exact capacity matching or benchmark claims','full_training':False})
    save(args.output/'validation-public.json',{'sample_id':val.sample_id,'schema_version':val.schema_version,'input':val.input})


if __name__=='__main__': main()
