"""Deployment-only stage. It never opens training/evaluator references."""
from dataclasses import asdict
import torch
from p10_common import *
from phi_jepa.integration.contracts import PublicProblem
from phi_jepa.inference.rollout import rollout
from phi_jepa.inference.readout import named_forecast,read_targets
from phi_jepa.training.checkpoint import load_checkpoint as load_primary
from phi_jepa.baselines.checkpoint import load_checkpoint as load_baseline
from phi_jepa.baselines.conventional import forecast as baseline_forecast
from phi_jepa.solvers.rk4 import SolverSettings,SolveStats


def grid(problem):
    a=problem.input['observation_cutoff']; b=max(t['end_time'] for t in problem.input['answer_spec'])
    return [round(a+.02*i,8) for i in range(round((b-a)/.02)+1)]


def load_selected(run,variant):
    folder=run.root/'numerical'/variant; job=load(folder/'job.json'); chosen=load(folder/'selected.json')
    directory=folder/chosen['directory']; layout=run.layout()
    if load(directory/'latest.json')!=chosen['checkpoint']: raise ValueError('selected_checkpoint_pointer_changed')
    if job['primary']: model,solver=load_primary(directory,layout=layout,context_identity=job['context_identity'],training=False)
    else: model,_,_,_=load_baseline(directory,layout=layout,context_identity=job['context_identity'],method=job['method'],training=False); solver=SolverSettings(**run.c['solver'])
    return model,solver,job


def predict(run,model,solver,job,row):
    p=PublicProblem.parse(row['public']); sid=p.sample_id
    embedding=torch.tensor([run.embedding(sid,job['context_identity']['mode'])]) if job['method']!='no_text_conditioning' else None
    stats=SolveStats()
    with torch.no_grad():
        if job['primary']: trajectory=rollout(model,p,embedding,grid(p),solver,stats); usage=stats.manifest()
        else: trajectory,usage=baseline_forecast(model,p,embedding,grid(p),solver=solver)
    named=named_forecast(p,run.layout(),trajectory,numerical_only=not job['primary'])
    return {'status':'success','sample_id':sid,'trajectory':asdict(trajectory),'named':named,'readout':read_targets(p,named),'usage':usage}


def forecast(run,job=None):
    guard_deployment_io()
    torch.set_num_threads(2)
    for variant in run.methods():
        folder=run.root/'numerical'/variant
        if not (folder/'selected.json').exists():
            for row in run.rows(): save(folder/'forecasts'/f"{row['sample_id']}.json",{'status':'failure','reason':'selected_checkpoint_unavailable'})
            continue
        try: model,solver,settings=load_selected(run,variant)
        except (ValueError,RuntimeError,FileNotFoundError) as exc:
            for row in run.rows():
                destination=folder/'forecasts'/f"{row['sample_id']}.json"
                if not destination.exists(): save(destination,{'status':'failure','reason':'checkpoint_unavailable_or_invalid:'+str(exc)})
            continue
        selected=load(folder/'selected.json')
        for row in run.rows():
            path=folder/'forecasts'/f"{row['sample_id']}.json"
            embedding=run.root/'embeddings'/settings['context_identity']['mode']/f"{row['sample_id']}.json"
            identity={'checkpoint_sha256':selected['checkpoint']['sha256'],'public_sha256':digest(row['public']),
                'embedding_sha256':file_hash(embedding) if settings['method']!='no_text_conditioning' and embedding.exists() else None,
                'layout_sha256':run.layout().sha256,'solver':asdict(solver)}
            if path.exists():
                if load(path).get('prediction_identity')!=identity: raise ValueError('stale_forecast_requires_separate_evidence_run')
                continue
            try: result=predict(run,model,solver,settings,row)
            except FileNotFoundError: result={'status':'failure','reason':'required_public_context_cache_unavailable','sample_id':row['sample_id']}
            except (ValueError,RuntimeError) as exc: result={'status':'failure','reason':str(exc),'sample_id':row['sample_id']}
            save(path,{**result,'prediction_identity':identity})
        print(json.dumps({'forecast_complete':variant,'queries':len(run.rows())}),flush=True)
    save(run.root/'deployment_guard.json',{'status':'passed','reference_or_credential_open_forbidden':True,'predicted_methods':run.methods()})
