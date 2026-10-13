"""Explicitly enabled future local main runner; preparation never launches it."""
from pathlib import Path
import argparse,subprocess,time
from .io import ROOT,read,write,external,digest,canonical
from .spq01a import retained,verify_manifest
from .formal_sampling import file_hash
from .job import locked
from .spq06 import ABLATION,parse_answer
from .main_public import continuation
from .heldout_scope import formal_scope
from .pilot_control import linux

def preflight(preparation,decision,output):
    preparation=external(preparation);output=external(output);verify_manifest(preparation)
    selected=read(decision);size=selected['final_size']
    if size not in (200,400) or selected['blockers']:raise ValueError('no final qualified runtime-based size decision')
    if not selected.get('capacity_evidence_path') or file_hash(selected['capacity_evidence_path'])!=selected['capacity_evidence_sha256']:raise ValueError('saved tokenization/capacity evidence missing or changed')
    data=read(preparation/('nested-'+str(size)+'-manifest.json'))
    if not data['complete'] or file_hash(preparation/('nested-'+str(size)+'-manifest.json'))!=selected['evaluation_manifest_sha256']:raise ValueError('frozen decision/manifest mismatch')
    conditions=[read(p) for p in sorted((preparation/'conditions').glob('*.json'))]
    if len(conditions)!=9:raise ValueError('nine conditions required')
    plan={'version':'SPQ06-main-run/1.0.0','preparation':str(preparation),'preparation_manifest_sha256':file_hash(preparation/'manifest.json'),
        'decision_sha256':file_hash(decision),'size':size,'items':data['items'],'conditions':conditions,
        'capacity_evidence_sha256':selected['capacity_evidence_sha256'],'capacity':selected['tokenization_capacity'][str(size)],
        'ablation_conditions':list(ABLATION),'limits':{'initial_requests':size*11,'clarification_continuations':size//5*11,
            'total_calls':5280 if size==400 else 2640,'gpu_work_seconds':172800,'per_process_loading_seconds':600,'maximum_shard_items':50},
        'failure_policy':'single reserved attempt/stage; incomplete, invalid and unknown failures retained; resume only never-reserved item/stages',
        'generation_settings':'exact qualified condition settings; no answering tools or model substitutions',
        'runner_sha256':file_hash(__file__),'main_execution_authorized_in_preparation':False,'hosted_answering':False,
        'generation_candidate_scope':read(preparation/'private/generation-scope.json')}
    retained(output/'main-run-plan.json',plan)
    print(canonical({'preflight_plan_sha256':digest(plan),'items':size,'limits':plan['limits'],'model_calls':0,
        'main_execution_authorized':False}).decode());return plan

def records(root):return list(root.glob('jobs/*/reservations/*.json'))

def execute(root,plan,condition,label,stage,requests):
    cid=condition['condition_id'];limits=plan['limits'];existing=records(root)
    already={(read(p)['condition_id'],read(p)['sample_id'],read(p)['stage'],p.parents[1].name.split('--')[1]) for p in existing}
    pending=[q for q in requests if (cid,q['sample_id'],stage,label) not in already]
    while pending:
        work=sum(read(p.with_name('process-result.json'))['wall_seconds'] if p.with_name('process-result.json').exists() else read(p)['reserved_seconds'] for p in root.glob('jobs/*/process-reservation.json'))
        capacity=int((limits['gpu_work_seconds']-work-600)//condition['settings']['max_seconds'])
        if capacity<=0:raise RuntimeError('main cumulative GPU ceiling reached; retained shortfall')
        chunk=pending[:min(50,capacity)];pending=pending[len(chunk):]
        initial=sum(read(p)['stage']==1 for p in records(root));continued=len(records(root))-initial
        if initial+(len(chunk) if stage==1 else 0)>limits['initial_requests'] or continued+(len(chunk) if stage==2 else 0)>limits['clarification_continuations']:raise ValueError('main cumulative call ceiling')
        number=1+len(list(root.glob('jobs/*')));name=cid+'--'+label+'--stage'+str(stage)+'--'+str(number).zfill(4)
        job=root/'jobs'/name;reserved=600+len(chunk)*condition['settings']['max_seconds']
        write(job/'process-reservation.json',{'reserved_seconds':reserved,'condition_id':cid,'input_condition':label,'stage':stage,'requests':len(chunk)})
        write(job/'request-list.json',chunk)
        prepared=Path(plan['preparation']);worker=prepared/'workers'/(cid+'.py')
        if file_hash(worker)!=condition['worker_sha256']:raise ValueError('frozen standalone worker changed')
        args=['wsl.exe','-d','Ubuntu-24.04','--','env','PYTHONDONTWRITEBYTECODE=1','HF_HUB_OFFLINE=1','TRANSFORMERS_OFFLINE=1',
            'timeout','--kill-after=5',str(reserved),condition['local_python'],linux(worker),'--condition',linux(prepared/'conditions'/(cid+'.json')),
            '--requests',linux(job/'request-list.json'),'--output',linux(job)]
        started=time.monotonic()
        try:
            with (job/'process.log').open('xb') as f:done=subprocess.run(args,stdout=f,stderr=subprocess.STDOUT,timeout=reserved+30)
            write(job/'process-result.json',{'returncode':done.returncode,'wall_seconds':time.monotonic()-started})
            if done.returncode:raise RuntimeError('local main process failed; preserve reservations; inspect private process log')
        except subprocess.TimeoutExpired:raise RuntimeError('main process ceiling reached; full unknown reservation retained') from None

def run(output,authorize,gpu_hours):
    if not authorize or gpu_hours!=48:raise ValueError('larger benchmark requires separate explicit execution authorization and unchanged48GPUhour cap')
    root=external(output);plan=read(root/'main-run-plan.json');prepared=Path(plan['preparation'])
    verify_manifest(prepared)
    if file_hash(prepared/'manifest.json')!=plan['preparation_manifest_sha256'] or file_hash(__file__)!=plan['runner_sha256']:raise ValueError('main frozen source changed')
    scope=plan['generation_candidate_scope'];size=plan['size']
    with locked(root/'.main-gpu.lock'),formal_scope(scope['candidates'],scope['excluded_groups']):
        for c in plan['conditions']:
            cid=c['condition_id']
            for label in ('enriched','structured_only'):
                if label=='structured_only' and cid not in ABLATION:continue
                initial=read(prepared/'request-lists'/str(size)/(cid+'-'+label+'-stage1.json'))
                execute(root,plan,c,label,1,initial)
                routed=[]
                for item in plan['items']:
                    if item['family']!='clarification':continue
                    sid=item['sample_id'];paths=list(root.glob('jobs/'+cid+'--'+label+'--stage1--*/results/'+sid+'-stage1.json'))
                    if len(paths)>1:raise ValueError('duplicate actual main first turn')
                    if not paths:continue
                    actual=read(paths[0]);routing={'sample_id':sid,'status':actual['completion_status']}
                    if actual['completion_status']=='completed':
                        try:
                            response,_=parse_answer(actual['raw_output']);record=read(prepared/item['private_record'])
                            q,route=continuation(record,c,actual['raw_output'],response,label=='structured_only');routing={'sample_id':sid,'status':route['status']}
                            if q:routed.append(q)
                        except (ValueError,TypeError,KeyError):routing={'sample_id':sid,'status':'invalid_first_turn'}
                    retained(root/'private-routing'/cid/label/(sid+'.json'),routing)
                execute(root,plan,c,label,2,routed)
    print(canonical({'reserved_stages':len(records(root)),'independent_items':size,'main_run':'execution_finished_with_all_failures_retained'}).decode())

if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('command',choices=('preflight','run'));p.add_argument('--preparation',type=Path);p.add_argument('--decision',type=Path);p.add_argument('--output',type=Path,required=True)
    p.add_argument('--authorize-local-main',action='store_true');p.add_argument('--gpu-hours',type=int);a=p.parse_args()
    if a.command=='preflight':preflight(a.preparation,a.decision,a.output)
    else:run(a.output,a.authorize_local_main,a.gpu_hours)
