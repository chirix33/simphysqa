"""Deadline study identities and the explicitly remaining provider allowance."""
from p10_common import *
from datetime import datetime,timezone
OUT=Path('/home/aashraf/phi-jepa/p11-tonight-01');NATIVE=OUT.parent
DEADLINE=datetime(2026,9,26,4,59,tzinfo=timezone.utc).timestamp()
EXPENSIVE_STOP=DEADLINE-20*60

def bootstrap():
    OUT.mkdir(exist_ok=True);path=OUT/'execution.json'
    if path.exists(): return load(path)
    old=load(NATIVE/'p10-qualification-01/budget.json'); used={k:sum(r[k] for r in old['provider']) for k in ('charged_input','charged_output','charged_usd')}
    remaining={'provider_attempts':old['caps']['provider_attempts']-len(old['provider']),
        'provider_input_tokens':old['caps']['provider_input_tokens']-used['charged_input'],
        'provider_output_tokens':old['caps']['provider_output_tokens']-used['charged_output'],
        'provider_usd':old['caps']['provider_usd']-used['charged_usd']}
    c={'run_root':str(OUT),'export_directory':'docs/reviews/artifacts/P11','caps':{**remaining,'gpu_seconds':EXPENSIVE_STOP-time.time(),'cpu_seconds':EXPENSIVE_STOP-time.time(),'artifact_bytes':8000000000},
        'deadline_utc':DEADLINE,'expensive_stop_utc':EXPENSIVE_STOP,'timezone':'America/Chicago','report_reserve_seconds':1200,
        'base_commit':subprocess.check_output(['git','rev-parse','HEAD'],cwd=ROOT,text=True).strip(),'prior_budget_sha256':file_hash(NATIVE/'p10-qualification-01/budget.json'),
        'provider_authority':'Unused P10 allowance only, until separately recorded additional authorization','new_local_authority':'user deadline-driven study instruction; no 900-hour profiles'}
    save(path,c);QualificationBudget(OUT,c);return c

def budget(): return QualificationBudget(OUT,bootstrap())

def time_guard():
    if time.time()>=EXPENSIVE_STOP: raise RuntimeError('absolute_expensive_work_deadline')

def catalog():
    c=load(ROOT/'configs/model_training_p02a.json');return ReleaseCatalog(ROOT/c['export_root'],c['export_index_sha256'],c['release_manifest_sha256'])

class StudyRun:
    def __init__(self,domain,cohort='main'):
        self.domain=domain;self.cohort=cohort;self.root=OUT/'models'/cohort/domain;self.root.mkdir(parents=True,exist_ok=True)
        self.native=NATIVE;self.old=NATIVE/'p10-qualification-01';self.b=budget()
        self.c={**load(ROOT/'configs/qualification_p10.json'),'domain':domain,'seed':11,'numerical_updates':20000,'checkpoint_milestones':[5000,10000,20000],
            'mixed_horizon_equal_pair_sampling':True,'numerical_job_seconds':2400,'run_root':str(self.root)}
    def rows(self): return [r for r in load(OUT/'selected-public.json') if r['domain']==self.domain and (self.cohort=='main' or r['appendix'])]
    def layout(self):
        m=load(ROOT/f'docs/reviews/artifacts/P02a/{self.domain}.state_plus_fixed_conditioning.json');return StateLayout.from_manifest(m,digest(m))
    def embedding(self,sid,mode='enriched'):return load(OUT/'embeddings'/mode/(sid+'.json'))['values']
    def methods(self):return ['phi_jepa']

def archive_sources(stage):
    from hashlib import sha256
    paths=list(ROOT.glob('src/phi_jepa/**/*.py'))+list(ROOT.glob('tools/p11*.py'))+list(ROOT.glob('tools/p10*.py'))+list(ROOT.glob('configs/*p0*.lock.txt'))+[ROOT/'configs/study_p11_frozen.json',ROOT/'configs/custom_p06.json',ROOT/'configs/model_context_p02b.json',ROOT/'configs/model_training_p02a.json',ROOT/'configs/baselines_p05b.json',ROOT/'configs/assessment_p04b.json',ROOT/'configs/qualification_p10.json',ROOT/'docs/assets/p11_direct_answer_v1.json',ROOT/'docs/assets/p04a_answer_v1.json']
    paths.extend([ROOT/'tests/test_p11.py',ROOT/'configs/report-p10.lock.txt',ROOT/'docs/assets/prompts.json',ROOT/'docs/assets/judge_schema.json',ROOT/load(ROOT/'configs/model_context_p02b.json')['enrichment_asset']])
    paths=list(dict.fromkeys(paths))
    snapshots={str(p.relative_to(ROOT)):p.read_bytes() for p in paths}
    hashes={name:sha256(data).hexdigest() for name,data in snapshots.items()}
    record={'stage':stage,'commit':subprocess.check_output(['git','rev-parse','HEAD'],cwd=ROOT,text=True).strip(),'plan_sha256':file_hash(OUT/'plan.json'),'files':hashes}
    save(OUT/'sources'/f'{stage}-{digest(record)}.json',record)
    for name,data in snapshots.items():
        dest=OUT/'sources/blobs'/hashes[name]
        if not dest.exists():dest.parent.mkdir(parents=True,exist_ok=True);dest.write_bytes(data)
    return digest(record)
