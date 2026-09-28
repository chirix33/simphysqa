"""Independent bounded numerical fits and separately invoked public-only rollout."""
import argparse
from collections import Counter
from dataclasses import asdict
import time
import torch
from p08_common import *
from phi_jepa.integration.contracts import PublicProblem, Identity
from phi_jepa.integration.readers import make_pairs, forecast_states
from phi_jepa.models.augmented_ode import AugmentedODE, ODESettings
from phi_jepa.models.context_projection import ProjectionSettings
from phi_jepa.training.pairs import PairTrainer, TrainingSettings
from phi_jepa.training.checkpoint import write_checkpoint, load_checkpoint as load_primary
from phi_jepa.baselines.conventional import NumericalComparator, BaselineSettings, forecast
from phi_jepa.baselines.training import ComparatorTrainer
from phi_jepa.baselines.checkpoint import save_checkpoint, load_checkpoint as load_baseline
from phi_jepa.inference.rollout import rollout
from phi_jepa.inference.readout import named_forecast,read_targets
from phi_jepa.solvers.rk4 import SolverSettings,SolveStats


def embeddings(row, mode): return load(RUN/'embeddings'/mode/f"{row['sample_id']}.json")['values']


def train(method):
    b=budget(); l=layout(); folder=RUN/'numerical'/method
    folder.mkdir(parents=True,exist_ok=False); source=provenance('train-'+method)
    primary=method in ('phi_jepa','no_enrichment'); base=method in ('no_enrichment','no_text_conditioning')
    mode='public_base_for_offline_audit' if base else 'enriched'; solver=SolverSettings(**CONFIG['solver'])
    context={'encoder':load(RUN/'encoding-report.json')['settings'] if method!='no_text_conditioning' else None,'mode':mode,'method':method}
    rows=[r for r in public_records() if r['split']=='train']; refs=load(RUN/'private/train-references.json')
    batches=[]; es=[]
    for row in rows:
        p=PublicProblem.parse(row['public']); ident=Identity(p.sample_id,row['scenario_id'],row['split_group'],CONFIG['domain'],'train')
        states=forecast_states(p,refs[p.sample_id])
        counts=Counter({digest((CONFIG['domain'],ident.group_id,a['timestamp'],z['timestamp'])):1 for a,z in zip(states,states[1:])})
        pairs=list(make_pairs(p,refs[p.sample_id],ident,l,'p08-frozen',counts,context_mode=mode,
            enrichment=load(RUN/'enrichment'/f'{p.sample_id}.json') if not base else None,duplicate_policy='equal_question_pairs'))[:20]
        assert len(pairs)==20 and all(r.weight==1 for r in pairs)
        batches.append(pairs)
        es.append(torch.tensor([embeddings(row,mode)]*20) if method!='no_text_conditioning' else None)
    order=schedule(32,CONFIG['numerical_updates']); history=[]; stats=SolveStats()
    provenance_data={'source_sha256':source,'selection_sha256':file_hash(RUN/'selection.json'),'training_scenarios':[r['scenario_id'] for r in rows],
        'training_pair_ids':[p.pair_id for batch in batches for p in batch],'physical_transition_ids':[p.transition_id for batch in batches for p in batch],
        'primary_weights_loaded':False,'batch_question_schedule':[rows[i]['sample_id'] for i in order]}
    limit=CONFIG['lr_seconds'] if method=='fixed_projection_lr' else CONFIG['numerical_seconds_per_method']
    with b.operation('numerical_fit:'+method,'cpu',cap=limit,reserve_bytes=50000000):
        start=time.monotonic(); torch.manual_seed(11)
        if primary:
            model=AugmentedODE(l,ProjectionSettings(1024,seed=11),ODESettings(hidden_width=128,seed=11))
            trainer=PairTrainer(model,solver,TrainingSettings(context_mode=mode))
        else:
            model=NumericalComparator(l,BaselineSettings(method,embedding_width=0 if method=='no_text_conditioning' else 1024,hidden_width=128,seed=11))
            trainer=None if method=='fixed_projection_lr' else ComparatorTrainer(model,solver=solver)
        save(folder/'initialization.json',{'source_sha256':source,'seed':11,'fresh':True,'state_tensor_hashes':{k:__import__('hashlib').sha256(v.detach().numpy().tobytes()).hexdigest() for k,v in model.state_dict().items()}})
        if method=='fixed_projection_lr':
            pairs=[p for batch in batches for p in batch]
            fit=model.fit_lr(torch.tensor([p.n_current for p in pairs]),torch.tensor([p.n_next for p in pairs]),torch.cat(es))
            history=[fit]
        else:
            for i,index in enumerate(order):
                if time.monotonic()-start>limit-5: break
                b.check(); item=trainer.step(batches[index],es[index]); history.append({**item,'sample_id':rows[index]['sample_id'],'elapsed_seconds':time.monotonic()-start})
                if trainer.updates%100==0:
                    if primary: write_checkpoint(folder/'training',trainer,context_identity=context,provenance=provenance_data,sampler_state={'next':i+1})
                    else: save_checkpoint(folder/'training',model,context_identity=context,provenance=provenance_data,trainer=trainer,sampler={'next':i+1})
                    save(folder/'history.json',history); print(json.dumps({'method':method,'updates':trainer.updates,'loss':item.get('loss',item.get('numerical_mse'))}),flush=True)
        if primary:
            training=write_checkpoint(folder/'training',trainer,context_identity=context,provenance=provenance_data,sampler_state={'next':len(history)})
            deployment=write_checkpoint(folder/'deployment',trainer,context_identity=context,provenance=provenance_data,sampler_state={},deployment=True)
        else:
            training=save_checkpoint(folder/'training',model,context_identity=context,provenance=provenance_data,trainer=trainer,sampler={'next':len(history)})
            deployment=save_checkpoint(folder/'deployment',model,context_identity=context,provenance=provenance_data,deployment=True)
        save(folder/'history.json',history)
        save(folder/'fit.json',{'status':'complete','method':method,'updates':trainer.updates if trainer else 0,'least_squares_fits':int(trainer is None),
            'context_identity':context,'training_checkpoint':training,'deployment_checkpoint':deployment,'provenance':provenance_data,
            'parameters':sum(p.numel() for p in model.parameters()),'state_width':2*l.d if primary else l.d,'fit_seconds':time.monotonic()-start,
            'training_stats':trainer.stats.manifest() if trainer else None,'rnn_calls':getattr(trainer,'recurrent_calls',0)})


def inference(method):
    # Only public preparation, frozen E and model checkpoints are read here.
    b=budget(); l=layout(); folder=RUN/'numerical'/method; info=load(folder/'fit.json'); primary=method in ('phi_jepa','no_enrichment')
    mode=info['context_identity']['mode']; provenance('forecast-'+method)
    with b.operation('numerical_forecast:'+method,'cpu'):
        if primary: model,solver=load_primary(folder/'deployment',layout=l,context_identity=info['context_identity'],training=False)
        else: model,_,_,_=load_baseline(folder/'deployment',layout=l,context_identity=info['context_identity'],method=method,training=False); solver=SolverSettings(**CONFIG['solver'])
        records=[]
        for row in public_records():
            if row['split']!='validation' and method!='phi_jepa': continue
            sid=row['sample_id']; p=PublicProblem.parse(row['public']); grid=[round(i*.02,8) for i in range(round(p.input['observation_cutoff']/.02),round(row['horizon']/.02)+1)]
            e=torch.tensor([embeddings(row,mode)]) if method!='no_text_conditioning' else None; stats=SolveStats(); started=time.monotonic()
            try:
                if primary: result=rollout(model,p,e,grid,solver,stats); usage=stats.manifest()
                else: result,usage=forecast(model,p,e,grid,solver=solver)
                named=named_forecast(p,l,result,numerical_only=not primary)
                value={'status':'success','trajectory':asdict(result),'named':named,'readout':read_targets(p,named),'usage':usage}
            except (ValueError,RuntimeError) as exc: value={'status':'failure','reason':str(exc),'usage':stats.manifest()}
            value.update(sample_id=sid,split=row['split'],seconds=time.monotonic()-started)
            save(folder/'forecasts'/f'{sid}.json',value); records.append({k:v for k,v in value.items() if k not in ('trajectory','named','readout')})
        save(folder/'forecast-summary.json',records)


if __name__=='__main__':
    torch.set_num_threads(2)
    p=argparse.ArgumentParser(); p.add_argument('stage',choices=('train','inference')); p.add_argument('method',choices=CONFIG['numerical_methods']); a=p.parse_args()
    globals()[a.stage](a.method)
