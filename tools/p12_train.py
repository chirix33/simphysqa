"""Expanded-study preflight and bounded CPU trainer. Disabled until separately authorized."""
from p12_common import *
import argparse
import math
import time
from collections import Counter
from p12_training_plan import (build_plan, preflight, bound_path, require_training_authorization,
                               check_training_identity, PLAN_PATH, export)

def plan():
    return build_plan()

def execution_window(folder, proposal, domain):
    path=folder/'execution-window.json'
    if not path.exists():
        if any((folder/name).exists() for name in ('initialization.json','history.jsonl','resume/latest.json')):
            raise ValueError('unbudgeted historical training artifacts; preserve and reconcile')
        save(path,{'plan_sha256':digest(proposal),'deadline_unix':time.time()+proposal['domains'][domain]['wall_seconds_cap']})
    record=load(path)
    if record['plan_sha256']!=digest(proposal):raise ValueError('resume plan changed')
    if time.time()>=record['deadline_unix']:raise TimeoutError('domain execution window expired; no automatic budget renewal')
    return record['deadline_unix']


def check_resume_boundary(folder, updates, checkpoints):
    history=folder/'history.jsonl'
    if history.exists():
        from phi_jepa.integration.readers import json_lines
        recorded=[r['update'] for r in json_lines(history)]
        if recorded!=list(range(1,updates+1)):
            raise ValueError('history/checkpoint update mismatch; explicit reconciliation required')
    elif updates:
        raise ValueError('missing update history')
    path=folder/'last-update-attempt.json'
    if path.exists():
        attempt=load(path)
        if attempt['status']!='success' or attempt['update']!=updates:
            raise ValueError('unresolved or uncheckpointed update; explicit reconciliation required')
    elif updates:
        raise ValueError('missing durable update accounting')
    if (folder/'validation-inflight.json').exists() or (updates in checkpoints and not (folder/'validation'/f'{updates}.json').exists()):
        raise ValueError('incomplete pass validation; explicit reconciliation required')

def train(proposal,domain):
    require_training_authorization(proposal);check_training_identity(proposal)
    if domain not in proposal['domains']:raise ValueError('unknown training domain')
    if not preflight(proposal)['can_train']:raise ValueError('incomplete context coverage; no subset fallback')
    folder=Path(proposal['study_root'])/domain
    if not folder.resolve().is_relative_to(NATIVE) or folder.resolve().is_relative_to(OUT):raise ValueError('separate native study directory required')
    folder.mkdir(parents=True,exist_ok=True)
    import fcntl
    with (folder/'worker.lock').open('a') as lock:
        fcntl.flock(lock,fcntl.LOCK_EX|fcntl.LOCK_NB)
        if (folder/'complete.json').exists():
            if load(folder/'complete.json').get('plan_sha256')!=digest(proposal):raise ValueError('completed domain plan mismatch')
            print('Domain already complete; no optimizer updates.');return
        deadline=execution_window(folder,proposal,domain)
        _execute(proposal,domain,folder,deadline)


def _execute(proposal,domain,folder,deadline):
    import torch
    from phi_jepa.integration.layout import StateLayout
    from phi_jepa.integration.readers import make_pairs,forecast_states
    from phi_jepa.models.augmented_ode import AugmentedODE,ODESettings
    from phi_jepa.models.context_projection import ProjectionSettings
    from phi_jepa.models.conditioning import NumericalConditioning
    from phi_jepa.training.pairs import PairTrainer,TrainingSettings
    from phi_jepa.training.sampling import fixed_pair_batches
    from phi_jepa.training.checkpoint import write_checkpoint,load_checkpoint
    from phi_jepa.solvers.rk4 import SolverSettings,SolveStats
    from phi_jepa.inference.rollout import rollout
    from phi_jepa.inference.readout import named_forecast,read_targets
    from phi_jepa.typed_evaluation import evaluate_targets
    torch.set_num_threads(proposal['torch_num_threads']);cat=catalog();budget_start=time.monotonic();source=proposal['training_implementation_sha256']
    if cat.identity!=load(bound_path(proposal,'population_audit'))['release_identity']:raise ValueError('release identity changed')
    save(folder/'execution-source.json',{'identity':source,'files':proposal['training_source_files'],'plan_sha256':digest(proposal)})
    import atexit
    prior=load(folder/'cost.json')['seconds'] if (folder/'cost.json').exists() else 0
    def charge():save(folder/'cost.json',{'seconds':prior+time.monotonic()-budget_start})
    atexit.register(charge)
    def guard():
        if time.time()>=deadline or time.monotonic()-budget_start+prior>=proposal['domains'][domain]['wall_seconds_cap']:raise TimeoutError('domain training wall cap')
    def artifact_guard():
        if sum(p.stat().st_size for p in folder.rglob('*') if p.is_file())>=proposal['artifact_bytes_cap']/len(proposal['domains'])-100000000:
            raise ValueError('domain artifact cap; checkpoint reserve exhausted')
    settings=proposal['domains'][domain];coverage={r['sample_id']:r for r in load(bound_path(proposal,'cache_coverage'))}
    m=load(proposal['layout_files'][domain]['path']);layout=StateLayout.from_manifest(m,digest(m))
    pairs=[];embeddings={};validation=[]
    def context(p):
        from phi_jepa.integration.contracts import enriched_context
        row=coverage[p.sample_id];notes=load(row['enrichment_path']);e=load(row['embedding_path'])
        if file_hash(row['embedding_path'])!=row['embedding_file_sha256'] or file_hash(row['enrichment_path'])!=row['enrichment_file_sha256']:
            raise ValueError('cached context content changed since coverage audit')
        if e['request_sha256']!=row['embedding_request_sha256'] or e['context_sha256']!=digest(enriched_context(p,notes,p.input['observation_cutoff'])):
            raise ValueError('stale context during preparation')
        embeddings[p.sample_id]=torch.tensor(e['values'],dtype=torch.float32);return notes
    for problem,ref,identity in cat.records(domain,'train'):
        guard()
        states=forecast_states(problem,ref);counts=Counter({digest((domain,identity.group_id,a['timestamp'],b['timestamp'])):1 for a,b in zip(states,states[1:])})
        pairs.extend(make_pairs(problem,ref,identity,layout,cat.identity,counts,context_mode='enriched',enrichment=context(problem),duplicate_policy='equal_question_pairs'))
    if len(pairs)!=settings['pairs_per_pass']:raise ValueError('full training pair count changed')
    for problem,ref,identity in cat.records(domain,'validation'):
        guard();context(problem);validation.append((problem,ref,identity))
    ctx={'encoder':proposal['encoder_settings'],'mode':'enriched','run':'p12-expanded-seed11'}
    provenance={'source':source,'plan':digest(proposal),'pair_population':digest([p.pair_id for p in pairs]),'release':cat.identity}
    if (folder/'resume/latest.json').exists():
        trainer,sampler,old=load_checkpoint(folder/'resume',layout=layout,context_identity=ctx,training=True)
        if old['plan']!=provenance['plan'] or old['pair_population']!=provenance['pair_population']:raise ValueError('resume population/config mismatch')
        if sampler['next_update']!=trainer.updates:raise ValueError('resume sampler/update mismatch')
        check_resume_boundary(folder,trainer.updates,settings['checkpoints'])
    else:
        check_resume_boundary(folder,0,settings['checkpoints'])
        transform=NumericalConditioning.fit([p.n_current for p in pairs],layout_sha256=layout.sha256,
            provenance={'split':'train','sample_ids':sorted({p.identity.sample_id for p in pairs}),'scenario_ids':sorted({p.identity.scenario_id for p in pairs})})
        model=AugmentedODE(layout,ProjectionSettings(**proposal['projection_settings']),ODESettings(**proposal['ode_settings']),transform)
        with torch.no_grad():model.field[-1].bias[:layout.d].copy_(torch.tensor([[(b-a)/p.dt for a,b in zip(p.n_current,p.n_next)] for p in pairs]).mean(0));model.field[-1].bias[layout.d:].zero_()
        trainer=PairTrainer(model,SolverSettings(**proposal['solver_settings']),TrainingSettings(**proposal['training_settings']))
        save(folder/'initialization.json',{'fresh':True,'seed':11,'diagnostic_weights_used':False,'manifest':model.manifest()})
    def checkpoint():
        artifact_guard()
        save(folder/'cost.json',{'seconds':prior+time.monotonic()-budget_start,'updates':trainer.updates,'pair_exposure':trainer.updates*settings['batch_pairs']})
        return write_checkpoint(folder/'resume',trainer,context_identity=ctx,provenance=provenance,sampler_state={'next_update':trainer.updates})
    for index,ids in enumerate(fixed_pair_batches(pairs,settings['batch_pairs'],settings['optimizer_updates'],proposal['seed'])):
        if index<trainer.updates:continue
        guard();batch=[pairs[k] for k in ids]
        save(folder/'last-update-attempt.json',{'status':'reserved','update':trainer.updates+1,'pairs':len(batch)})
        record=trainer.step(batch,torch.stack([embeddings[p.identity.sample_id] for p in batch]))
        with (folder/'history.jsonl').open('ab') as f:f.write(canonical({**record,'pair_ids_sha256':digest([p.pair_id for p in batch])})+b'\n')
        save(folder/'last-update-attempt.json',{'status':'success','update':trainer.updates,'pairs':len(batch)})
        if trainer.updates%proposal['checkpoint_every_updates']==0:checkpoint()
        if trainer.updates in settings['checkpoints']:
            save(folder/'validation-inflight.json',{'update':trainer.updates,'plan_sha256':digest(proposal)})
            scores=[];records=[];started=time.perf_counter()
            for p,ref,identity in validation:
                guard();a=p.input['observation_cutoff'];b=max(s['end_time'] for s in p.input['answer_spec']);times=[round(a+0.02*i,8) for i in range(round((b-a)/0.02)+1)]
                try:
                    stats=SolveStats();prediction=rollout(trainer.model,p,embeddings[p.sample_id][None],times,trainer.solver,stats)
                    result=evaluate_targets(p,ref,read_targets(p,named_forecast(p,layout,prediction)),method='Phi-JEPA numerical/readout')
                    nums=[t for t in result['targets'] if t['answer_type']!='boolean']
                    score=sum(t['error']/max(t.get('tolerance',0),1e-12) if t['status']=='valid' else 1e12 for t in nums)/len(nums)
                except (ValueError,RuntimeError,OverflowError) as exc:score=1e12;result={'failure':type(exc).__name__}
                scores.append(score);records.append({'sample_id':p.sample_id,'score':score,'result':result,'stats':stats.manifest()})
            score=sum(scores)/len(scores);checkpoint()
            pointer=write_checkpoint(folder/'checkpoints'/str(trainer.updates),trainer,context_identity=ctx,provenance=provenance,sampler_state={},deployment=True)
            save(folder/'validation'/f'{trainer.updates}.json',{'score':score,'seconds':time.perf_counter()-started,'records':records})
            if not (folder/'selected.json').exists() or score<load(folder/'selected.json')['score']:
                save(folder/'selected.json',{'update':trainer.updates,'score':score,'checkpoint':pointer,'split':'validation'})
            (folder/'validation-inflight.json').unlink()
    checkpoint();save(folder/'complete.json',{'plan_sha256':digest(proposal),'updates':trainer.updates,'pair_exposure':trainer.updates*settings['batch_pairs'],'complete_passes':trainer.updates*settings['batch_pairs']//len(pairs),'convergence_claimed':False})

if __name__=='__main__':
    parser=argparse.ArgumentParser();parser.add_argument('command',choices=['plan','preflight','train']);parser.add_argument('--approved-plan',type=Path);parser.add_argument('--domain')
    args=parser.parse_args();proposal=load(args.approved_plan) if args.approved_plan else plan()
    if args.command=='train':train(proposal,args.domain)
    else:
        report=preflight(proposal);export()
        print(json.dumps({k:v for k,v in report.items() if k not in ('missing_sample_ids','scopes')}|{'plan':str(PLAN_PATH)}))
