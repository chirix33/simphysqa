"""Budgeted fresh-study confirmation inference; public inputs and verified contexts only."""
from p12_common import *
from dataclasses import asdict
import time

def main(plan_path):
    import torch
    from p10_common import guard_deployment_io
    from phi_jepa.integration.contracts import PublicProblem,enriched_context
    from phi_jepa.integration.layout import StateLayout
    from phi_jepa.training.checkpoint import load_checkpoint
    from phi_jepa.inference.rollout import rollout
    from phi_jepa.inference.readout import named_forecast,read_targets
    from phi_jepa.solvers.rk4 import SolveStats
    guard_deployment_io();proposal=load(plan_path);study_lock(proposal);root=Path(proposal['study_root']);torch.set_num_threads(2)
    if file_hash(OUT/'confirmation-cache-coverage.json')!=proposal['confirmation_cache_sha256'] or file_hash(OUT/'confirmation-enrichment-origin-audit.json')!=proposal['confirmation_origins_sha256']:
        raise ValueError('confirmation cache audit changed since approval')
    coverage={r['sample_id']:r for r in load(OUT/'confirmation-cache-coverage.json')}
    origins={r['sample_id']:r for r in load(OUT/'confirmation-enrichment-origin-audit.json')['records']}
    rows=load(OUT/'confirmation-public.json')
    if any(not coverage[r['sample_id']]['embedding_path'] or origins.get(r['sample_id'],{}).get('status')!='verified' for r in rows):
        raise ValueError('incomplete identity-verified confirmation contexts; no subset inference')
    context_identity={'encoder':load(NATIVE/'p11-tonight-01/encoding-report.json')['settings'],'mode':'enriched','run':'p12-expanded-seed11'}
    started=time.monotonic();folder=root/'numerical';folder.mkdir(exist_ok=True)
    prior=sum(load(p).get('latency_seconds',0) for p in folder.glob('*.json'))
    for domain in proposal['domains']:
        selected=load(root/domain/'selected.json');directory=root/domain/'checkpoints'/str(selected['update'])
        if load(directory/'latest.json')!=selected['checkpoint']:raise ValueError('selected deployment identity mismatch')
        manifest=load(ROOT/f'docs/reviews/artifacts/P02a/{domain}.state_plus_fixed_conditioning.json');layout=StateLayout.from_manifest(manifest,digest(manifest))
        model,solver=load_checkpoint(directory,layout=layout,context_identity=context_identity,training=False)
        for row in rows:
            if row['domain']!=domain:continue
            p=PublicProblem.parse(row['public']);entry=coverage[p.sample_id]
            for kind in ('embedding','enrichment'):
                if file_hash(entry[kind+'_path'])!=entry[kind+'_file_sha256']:raise ValueError('context content changed since audit')
            e=load(entry['embedding_path']);notes=load(entry['enrichment_path'])
            if e['context_sha256']!=digest(enriched_context(p,notes,p.input['observation_cutoff'])):raise ValueError('public context binding changed')
            identity={'sample_id':p.sample_id,'public_sha256':digest(p.input),'checkpoint':selected['checkpoint']['sha256'],'embedding_sha256':entry['embedding_file_sha256'],'solver':asdict(solver)}
            path=folder/(p.sample_id+'.json')
            if path.exists():
                if load(path)['request_sha256']!=digest(identity):raise ValueError('inference resume identity mismatch')
                continue
            if prior+time.monotonic()-started>=proposal['numerical_inference_seconds_cap']:raise TimeoutError('numerical confirmation budget exhausted')
            t0=time.perf_counter();stats=SolveStats();value={'sample_id':p.sample_id,'request_sha256':digest(identity),'identity':identity,'answer':None}
            try:
                a=p.input['observation_cutoff'];b=max(s['end_time'] for s in p.input['answer_spec']);times=[round(a+0.02*i,8) for i in range(round((b-a)/0.02)+1)]
                trajectory=rollout(model,p,torch.tensor([e['values']]),times,solver,stats)
                named=named_forecast(p,layout,trajectory);readout=read_targets(p,named)
                value.update(status='success',failure=None,trajectory=asdict(trajectory),named=named,answer={'targets':readout})
            except (ValueError,RuntimeError,OverflowError) as exc:value.update(status='runtime_failure',failure=type(exc).__name__)
            save(path,value|{'stats':stats.manifest(),'latency_seconds':time.perf_counter()-t0})

if __name__=='__main__':main(Path(sys.argv[1]))
