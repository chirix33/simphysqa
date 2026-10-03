"""Compile measured qualification facts and explicitly extrapolated planning costs."""
from p12_common import *
from collections import defaultdict
from importlib.metadata import version

def main():
    plan=load(OUT/'proposed-training-plan.json');audit=load(OUT/'audit.json');history=load(OUT/'historical-reconciliation.json')
    summary={'commit':history['current_commit'],'source':snapshot('final-report-data'),'training_totals':audit['training_totals'],
             'history':{k:history[k] for k in ('inspected_questions','inspected_scenarios','confirmation_overlap')},
             'bad_historical_source_blobs':sum(len(s['missing_or_mismatched_blobs']) for r in history['runs'] for s in r['source_stages']),
             'historical_blob_gaps_by_run':{r['root']:sum(len(s['missing_or_mismatched_blobs']) for s in r['source_stages']) for r in history['runs'] if any(s['missing_or_mismatched_blobs'] for s in r['source_stages'])},
             'local':{},'training':{},'runtime':{k:version(k) for k in ('torch','transformers','tokenizers','safetensors','huggingface-hub')}}
    for cfg in CONFIG['models']:
        folder=OUT/'local'/cfg['condition'];q=load(folder/'qualification.json');evaluation=load(OUT/'evaluation'/f'{cfg["condition"]}.json')
        rows=[load(p) for p in folder.glob('*.json') if len(p.stem)==32]
        r={'status':q['status'],'requests':len(rows),'valid':sum(v['status']=='success' for v in rows),
           'generation_seconds':sum(v['latency_seconds'] for v in rows),'load_seconds':q.get('load_seconds'),
           'peak_allocated_bytes':max((v['peak_allocated_bytes'] for v in rows),default=None),
           'input_tokens':sum(v['input_tokens'] for v in rows),'reasoning_tokens':sum(v['reasoning_tokens'] for v in rows),
           'final_tokens':sum(v['final_answer_tokens'] for v in rows),'failures':evaluation['whole_task']['failure_reasons'],
           'complete_successes':evaluation['whole_task']['grouped']['pooled']['complete_successes'],
           'per_domain':{},'cost_extrapolation_not_measurement':True}
        for d in plan['domains']:
            values=[v for v in rows if v['domain']==d];questions=80 if d=='driving' else 140
            r['per_domain'][d]={'diagnostic_seconds':sum(v['latency_seconds'] for v in values),
                'confirmation_estimate_seconds':sum(v['latency_seconds'] for v in values)/len(values)*questions if values else None}
        summary['local'][cfg['condition']]=r
    cpu={r['domain']:r for r in load(OUT/'numerical-profile-cpu.json') if r['batch_pairs']==256}
    gpu={r['domain']:r for r in load(OUT/'numerical-profile-cuda.json') if r['batch_pairs']==256}
    context={r['domain']:r for r in load(OUT/'context-profile.json')['results']}
    for domain,proposed in plan['domains'].items():
        missing=sum(audit['partitions'][domain+'/'+split]['questions']-audit['partitions'][domain+'/'+split]['embedding_covered'] for split in ('train','validation'))
        val_questions=audit['partitions'][domain+'/validation']['questions']
        # Use 90 intervals/question conservatively for all horizons; training probes were 40 or 90.
        seconds_per_interval=gpu[domain]['rollout_seconds']/gpu[domain]['rollout_intervals']
        summary['training'][domain]={**proposed,'cpu_seconds_per_update_measured':cpu[domain]['seconds_per_update'],
            'gpu_seconds_per_update_measured':gpu[domain]['seconds_per_update'],'gpu_peak_allocated_bytes':gpu[domain]['peak_allocated_bytes'],
            'cpu_update_seconds_estimate':cpu[domain]['seconds_per_update']*proposed['optimizer_updates'],
            'gpu_update_seconds_estimate':gpu[domain]['seconds_per_update']*proposed['optimizer_updates'],
            'validation_seconds_estimate_gpu_timing_proxy':10*val_questions*90*seconds_per_interval,
            'missing_embeddings':missing,'embedding_seconds_estimate':missing*context[domain]['seconds'],
            'qualification_encoder_tokens':context[domain]['tokens']}
    save(OUT/'report-data.json',summary)
    locks={}
    acquisition=load(OUT/'model-acquisition.json')
    for cfg in CONFIG['models']:
        path=OUT/'local'/cfg['condition']/'preflight.json'
        locks[cfg['condition']]={'config':cfg,'acquisition':acquisition[cfg['model']],
                                'qualified_settings':load(path)['settings'] if path.exists() else None,
                                'status':summary['local'][cfg['condition']]['status']}
    save(ROOT/'configs/local_answers_p12.lock.json',locks)
    print(json.dumps(summary,indent=2))

if __name__=='__main__':main()
