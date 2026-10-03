"""New bounded Llama qualification after HF access approval; preserve P12 history."""
from p12_common import *
from collections import Counter
from datetime import datetime,timezone
import shutil,time

RUN=NATIVE/'p12-llama-qualification-01'
DEST=ROOT/'docs/reviews/artifacts/P12_llama'
CONDITION='llama31_8b_direct'
MODEL='meta-llama/Llama-3.1-8B-Instruct'
REVISION='0e9e39f249a16976918f6564b8830bc894c89659'

def prepare():
    if (RUN/'config.json').exists():print('Existing frozen qualification; use acquire/generate/evaluate/report.');return
    rows=load(OUT/'diagnostic-public.json')
    if len(rows)!=8 or any(r['split']!='validation' for r in rows) or set(Counter(r['domain'] for r in rows).values())!={2}:raise ValueError('frozen validation cohort invalid')
    old=load(OUT/'model-acquisition.json')[MODEL]
    if old['revision']!=REVISION:raise ValueError('historical checkpoint pin differs')
    cfg={**CONFIG,'run_root':str(RUN),'models':[next(c for c in CONFIG['models'] if c['condition']==CONDITION)],
         'authorization':'User confirmed approved HF access and WSL login; proceed with bounded Llama qualification.',
         'authorized_at_utc':datetime.now(timezone.utc).isoformat(),
         'qualification':{**CONFIG['qualification'],'maximum_generation_requests':8,'gpu_seconds':1200,'download_bytes':20000000000},
         'generation_wall_seconds_cap':1500,'revision':REVISION,'runner_sha256':file_hash(__file__),
         'diagnostic_public_sha256':file_hash(OUT/'diagnostic-public.json'),'base_config_sha256':file_hash(ROOT/'configs/qualification_p12.json')}
    save(RUN/'config.json',cfg);save(RUN/'model-acquisition.json',{MODEL:old})
    shutil.copyfile(OUT/'diagnostic-public.json',RUN/'diagnostic-public.json')
    save(RUN/'historical-blocked-qualification.json',load(OUT/'local'/CONDITION/'qualification.json'))
    shutil.copyfile(__file__,RUN/'runner.py');print({'prepared':True,'revision':REVISION,'validation_questions':8})

def config():
    cfg=load(RUN/'config.json')
    if file_hash(__file__)!=cfg['runner_sha256'] or file_hash(ROOT/'configs/qualification_p12.json')!=cfg['base_config_sha256']:raise ValueError('frozen qualification source/config changed')
    if file_hash(RUN/'diagnostic-public.json')!=cfg['diagnostic_public_sha256']:raise ValueError('cohort changed')
    return cfg

def acquire():
    import p12_models
    cfg=config();p12_models.CONFIG=cfg;p12_models.OUT=RUN
    p12_models.main()
    record=load(RUN/'model-acquisition.json')[MODEL]
    if record['revision']!=REVISION:raise ValueError('checkpoint revision changed')
    if record['status']!='available':raise ValueError('pinned checkpoint acquisition failed: '+record.get('failure_type','unknown'))

def generate():
    import p12_local,signal
    cfg=config();acq=load(RUN/'model-acquisition.json')[MODEL]
    if acq['status']!='available' or acq['revision']!=REVISION:raise ValueError('pinned acquisition not complete')
    p12_local.CONFIG=cfg;p12_local.OUT=RUN;p12_local.snapshot=lambda stage:snapshot(stage,output=RUN)
    timer=RUN/'generation-window.json'
    if not timer.exists():save(timer,{'deadline_unix':time.time()+cfg['generation_wall_seconds_cap']})
    remaining=load(timer)['deadline_unix']-time.time()
    if remaining<=0:raise TimeoutError('qualification wall budget expired')
    def expired(*_):raise TimeoutError('qualification wall budget expired')
    signal.signal(signal.SIGALRM,expired);signal.setitimer(signal.ITIMER_REAL,remaining)
    try:p12_local.main(CONDITION)
    finally:signal.setitimer(signal.ITIMER_REAL,0)

def evaluate():
    import p12_evaluate
    p12_evaluate.CONFIG=config();p12_evaluate.OUT=RUN;p12_evaluate.main()

def report():
    cfg=config();folder=RUN/'local'/CONDITION;q=load(folder/'qualification.json');evaluation=load(RUN/'evaluation'/f'{CONDITION}.json')
    values=[load(folder/(r['sample_id']+'.json')) for r in load(RUN/'diagnostic-public.json')]
    summary={'diagnostic_only':True,'qualification':q,'acquisition':load(RUN/'model-acquisition.json')[MODEL],
        'download_cost':load(RUN/'download-cost.json'),'requests':len(values),'valid_answers':sum(v['status']=='success' for v in values),
        'complete_successes':evaluation['whole_task']['grouped']['pooled']['complete_successes'],
        'statuses':dict(Counter(v['status'] for v in values)),'failure_reasons':dict(Counter(v.get('failure') for v in values if v.get('failure'))),
        'input_tokens':sum(v['input_tokens'] for v in values),'input_tokens_min':min(v['input_tokens'] for v in values),'input_tokens_max':max(v['input_tokens'] for v in values),
        'output_tokens':sum(v['output_tokens'] for v in values),'reasoning_tokens':sum(v['reasoning_tokens'] for v in values),
        'final_answer_tokens':sum(v['final_answer_tokens'] for v in values),'generation_seconds':sum(v['latency_seconds'] for v in values),
        'peak_allocated_bytes':max(v['peak_allocated_bytes'] for v in values),'peak_reserved_bytes':max(v['peak_reserved_bytes'] for v in values),
        'EOS_terminated':sum(v['EOS_terminated'] for v in values),'token_cap_termination':sum(v['token_cap_termination'] for v in values),
        'time_cap_termination':sum(v['time_cap_termination'] for v in values),'per_domain':{},
        'raw_completions_and_token_ids_preserved':True,'enrichment_supplied':False,'paid_api_calls':0,
        'source_snapshot':q['source'],'runner_sha256':cfg['runner_sha256'],'config_sha256':file_hash(RUN/'config.json')}
    for domain in sorted({v['domain'] for v in values}):
        selected=[v for v in values if v['domain']==domain];seconds=sum(v['latency_seconds'] for v in selected)
        summary['per_domain'][domain]={'requests':len(selected),'seconds':seconds,'valid':sum(v['status']=='success' for v in selected),
            'input_tokens':[v['input_tokens'] for v in selected], 'confirmation_generation_seconds_estimate':seconds/len(selected)*(80 if domain=='driving' else 140)}
    summary['confirmation_500_generation_hours_estimate']=sum(v['confirmation_generation_seconds_estimate'] for v in summary['per_domain'].values())/3600
    save(RUN/'summary.json',summary);DEST.mkdir(parents=True,exist_ok=True)
    for path in RUN.rglob('*'):
        if not path.is_file() or path.name.endswith('.pending'):continue
        target=DEST/path.relative_to(RUN);target.parent.mkdir(parents=True,exist_ok=True);shutil.copyfile(path,target)
    save(DEST/'artifact-index.json',{'native_root':str(RUN),'files':{str(p.relative_to(RUN)):file_hash(p) for p in RUN.rglob('*') if p.is_file()}})
    print(json.dumps({k:v for k,v in summary.items() if k not in ('acquisition','qualification')},indent=2))

if __name__=='__main__':globals()[sys.argv[1]]()
