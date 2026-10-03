"""Fresh, discarded train-only pair probes. Never silently train on incomplete caches."""
from p12_common import *
import time
from collections import Counter
from phi_jepa.integration.layout import StateLayout
from phi_jepa.integration.readers import forecast_states,make_pairs

def main(device):
    import torch
    from phi_jepa.models.augmented_ode import AugmentedODE,ODESettings
    from phi_jepa.models.context_projection import ProjectionSettings
    from phi_jepa.models.conditioning import NumericalConditioning
    from phi_jepa.training.pairs import PairTrainer,TrainingSettings
    from phi_jepa.training.sampling import fixed_pair_batches
    from phi_jepa.solvers.rk4 import SolverSettings
    torch.set_num_threads(2);source=snapshot('numerical-profile-'+device);started=time.perf_counter();cat=catalog()
    coverage=load(OUT/'cache-coverage.json');records=[]
    for domain in sorted({r['domain'] for r in coverage}):
        eligible={r['sample_id']:r for r in coverage if r['domain']==domain and r['split']=='train' and r['embedding_path']}
        chosen=set(sorted(eligible)[:2]);pairs=[];embeddings={};t0=time.perf_counter()
        manifest=load(ROOT/f'docs/reviews/artifacts/P02a/{domain}.state_plus_fixed_conditioning.json')
        layout=StateLayout.from_manifest(manifest,digest(manifest))
        for problem,ref,ident in cat.records(domain,'train'):
            if problem.sample_id not in chosen:continue
            entry=eligible[problem.sample_id];notes=load(entry['enrichment_path'])
            states=forecast_states(problem,ref)
            multiplicity=Counter({digest((domain,ident.group_id,a['timestamp'],b['timestamp'])):1 for a,b in zip(states,states[1:])})
            pairs.extend(make_pairs(problem,ref,ident,layout,cat.identity,multiplicity,context_mode='enriched',enrichment=notes,duplicate_policy='equal_question_pairs'))
            embeddings[problem.sample_id]=load(entry['embedding_path'])['values']
            if set(embeddings)==chosen:break
        if not pairs:raise ValueError('no_identity_matching_cached_training_diagnostic')
        preparation=time.perf_counter()-t0
        # A public-only rollout timing probe uses the same diagnostic training input.
        rollout_problem=problem
        transform=NumericalConditioning.fit([p.n_current for p in pairs],layout_sha256=layout.sha256,
                     provenance={'split':'train','sample_ids':sorted(chosen),'scenario_ids':sorted({p.identity.scenario_id for p in pairs})})
        derivative=torch.tensor([[(b-a)/p.dt for a,b in zip(p.n_current,p.n_next)] for p in pairs]).mean(0)
        for batch_size in CONFIG['qualification']['batch_pairs']:
            if time.perf_counter()-started>CONFIG['qualification']['numerical_seconds']:raise TimeoutError('numerical profile cap')
            model=AugmentedODE(layout,ProjectionSettings(1024,seed=11),ODESettings(seed=11),transform)
            with torch.no_grad():model.field[-1].bias[:layout.d].copy_(derivative);model.field[-1].bias[layout.d:].zero_()
            model=model.to(device);trainer=PairTrainer(model,SolverSettings(),TrainingSettings())
            if device=='cuda':torch.cuda.synchronize();torch.cuda.reset_peak_memory_stats()
            t0=time.perf_counter();history=[];exposure=0
            for ids in fixed_pair_batches(pairs,batch_size,CONFIG['qualification']['updates_per_batch_probe'],11):
                batch=[pairs[i] for i in ids]
                emb=torch.tensor([embeddings[p.identity.sample_id] for p in batch],dtype=torch.float32,device=device)
                history.append(trainer.step(batch,emb));exposure+=len(batch)
            if device=='cuda':torch.cuda.synchronize()
            seconds=time.perf_counter()-t0
            record={'domain':domain,'device':device,'batch_pairs':batch_size,'updates':trainer.updates,'pair_exposure':exposure,
                    'unique_diagnostic_pairs':len(pairs),'source_training_samples':sorted(chosen),'seconds':seconds,
                    'seconds_per_update':seconds/trainer.updates,'pairs_per_second':exposure/seconds,
                    'peak_allocated_bytes':torch.cuda.max_memory_allocated() if device=='cuda' else None,
                    'preparation_seconds':preparation,'history':history,'weights':'discarded_without_checkpoint','source':source}
            records.append(record);save(OUT/f'numerical-profile-{device}.json',records)
            if batch_size==256:
                from phi_jepa.inference.rollout import rollout
                from phi_jepa.solvers.rk4 import SolveStats
                a=rollout_problem.input['observation_cutoff'];b=max(s['end_time'] for s in rollout_problem.input['answer_spec'])
                times=[round(a+0.02*i,8) for i in range(round((b-a)/0.02)+1)]
                stats=SolveStats();start_rollout=time.perf_counter()
                rollout(model,rollout_problem,torch.tensor([embeddings[rollout_problem.sample_id]],device=device),times,trainer.solver,stats)
                if device=='cuda':torch.cuda.synchronize()
                record.update(rollout_seconds=time.perf_counter()-start_rollout,rollout_intervals=len(times)-1,rollout_stats=stats.manifest())
                save(OUT/f'numerical-profile-{device}.json',records)
            print(json.dumps({k:v for k,v in record.items() if k not in ('history','source_training_samples')}),flush=True)
            del trainer,model
            if device=='cuda':torch.cuda.empty_cache()
    save(OUT/f'numerical-cost-{device}.json',{'seconds':time.perf_counter()-started,'weights_saved':False,'model_downloads':0,'paid_calls':0})

if __name__=='__main__':main(sys.argv[1])
