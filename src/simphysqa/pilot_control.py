"""Local pilot scheduling/routing/scoring; never an answering API client."""
import argparse
from pathlib import Path
import subprocess
import time
from .io import canonical, read, write, external
from .spq01a import retained
from .spq06 import parse_answer
from .public_updates import continuation_request
from .formal_sampling import file_hash


def prepare_continuations(pilot,condition_id):
    pilot=external(pilot);condition=read(pilot/'conditions'/(condition_id+'.json'));plan=read(pilot/'pilot-plan.json')
    requests=[];checks=[]
    for item in plan['selected']:
        if item['family']!='clarification':continue
        sid=item['sample_id'];result=pilot/'executions'/(condition_id+'-stage1')/'results'/(sid+'-stage1.json')
        if not result.exists():checks.append({'sample_id':sid,'status':'missing_or_unknown_first_turn'});continue
        actual=read(result)
        if actual['completion_status']!='completed':checks.append({'sample_id':sid,'status':actual['completion_status'],'failure_reason':actual['failure_reason']});continue
        try:
            response,diagnostics=parse_answer(actual['raw_output']);record=read(pilot/'private-records'/(sid+'.json'))
            request,routed=continuation_request(record,condition,actual['raw_output'],response)
            checks.append({'sample_id':sid,'status':routed['status'],'checks':routed['checks'],'parsed_response':response,'reasoning_format':diagnostics})
            if request:requests.append(request)
        except (ValueError,TypeError,KeyError) as exc:checks.append({'sample_id':sid,'status':'invalid_first_turn','exception_type':type(exc).__name__})
    if len(requests)>4:raise ValueError('condition continuation ceiling')
    retained(pilot/'request-lists'/(condition_id+'-stage2.json'),requests)
    retained(pilot/'private-routing'/(condition_id+'.json'),{'checks':checks,'routed_continuations':len(requests),
        'policy':'actual raw first-turn assistant; recorded reply; verified exact public initial-to-resolved update; no authored assistant'})
    print(canonical({'condition':condition_id,'routed_continuations':len(requests),'checks':[{'sample_id':c['sample_id'],'status':c['status']} for c in checks]}).decode())
    return requests


def linux(path):
    text=str(Path(path).resolve()).replace('\\','/')
    if text[1:3]!=':/':raise ValueError('explicit Windows path required')
    return '/mnt/'+text[0].lower()+text[2:]


def run(pilot,worker,condition_id,stage):
    pilot=external(pilot);plan=read(pilot/'pilot-plan.json');condition=read(pilot/'conditions'/(condition_id+'.json'))
    request_path=pilot/'request-lists'/(condition_id+'-stage'+str(stage)+'.json')
    requests=read(request_path)
    if stage==1 and len(requests)!=20 or stage==2 and len(requests)>4:raise ValueError('pilot call allocation')
    reservations=list((pilot/'executions').glob('*/reservations/*.json'));initials=sum(read(p)['stage']==1 for p in reservations);continued=len(reservations)-initials
    pending=[q for q in requests if not (pilot/'executions'/(condition_id+'-stage'+str(stage))/'reservations'/(q['sample_id']+'-stage'+str(stage)+'.json')).exists()]
    if initials+(len(pending) if stage==1 else 0)>180 or continued+(len(pending) if stage==2 else 0)>36:raise ValueError('cumulative pilot request ceiling')
    work=0
    for p in (pilot/'process-reservations').glob('*.json'):
        result=p.with_name(p.stem+'-result.json')
        if p.name.endswith('-result.json'):continue
        work+=read(result)['wall_seconds'] if result.exists() else read(p)['reserved_seconds']
    # The two earlier manually launched processes have immutable item reservations.
    # Conservatively retain their full 600s loading + item timeout bounds; do not
    # invent missing historical process-wall measurements or call these preflight receipts.
    for folder in (pilot/'executions').iterdir():
        if folder.is_dir() and not (pilot/'process-reservations'/(folder.name+'.json')).exists():
            work+=600+sum(read(p)['maximum_seconds'] for p in (folder/'reservations').glob('*.json'))
    timeout=600+sum(condition['settings']['max_seconds'] for q in pending)
    if work+timeout>64800:raise ValueError('cumulative pilot GPU work ceiling')
    if not pending:return
    name=condition_id+'-stage'+str(stage);reservation=pilot/'process-reservations'/(name+'.json')
    if reservation.exists():
        previous=reservation.with_name(reservation.stem+'-result.json')
        log=reservation.with_suffix('.log')
        zero_call_wsl_denial=(previous.exists() and read(previous)['returncode']!=0 and log.exists()
            and 'Wsl/E_ACCESSDENIED' in log.read_bytes().decode('utf-16-le',errors='ignore')
            and not list((pilot/'executions'/name/'reservations').glob('*.json')))
        if not zero_call_wsl_denial:raise ValueError('prior unknown/failed process retained; no automatic model retry')
        reservation=reservation.with_name(reservation.stem+'-launch2.json')
        if reservation.exists():raise ValueError('second process launch already recorded')
    if not requests:return
    write(reservation,{'condition_id':condition_id,'stage':stage,'reserved_seconds':timeout,'maximum_requests':len(pending),'worker_path':str(worker),'worker_sha256':file_hash(worker),'previous_work_charged_seconds':work})
    args=['wsl.exe','-d','Ubuntu-24.04','--','env','PYTHONDONTWRITEBYTECODE=1','HF_HUB_OFFLINE=1','TRANSFORMERS_OFFLINE=1',
        'timeout','--kill-after=5',str(timeout),condition['local_python'],linux(worker),
        '--condition',linux(pilot/'conditions'/(condition_id+'.json')),'--requests',linux(request_path),
        '--output',linux(pilot/'executions'/name)]
    started=time.monotonic()
    with reservation.with_suffix('.log').open('xb') as log:
        done=subprocess.run(args,stdout=log,stderr=subprocess.STDOUT,timeout=timeout+30)
    write(reservation.with_name(reservation.stem+'-result.json'),{'returncode':done.returncode,'wall_seconds':time.monotonic()-started})
    if done.returncode:raise RuntimeError('local process failed; inspect immutable launch log')


def main():
    p=argparse.ArgumentParser();p.add_argument('command',choices=('route','run'));p.add_argument('--pilot',type=Path,required=True);p.add_argument('--condition',required=True);p.add_argument('--worker',type=Path);p.add_argument('--stage',type=int,choices=(1,2),default=1)
    a=p.parse_args()
    if a.command=='route':prepare_continuations(a.pilot,a.condition)
    else:run(a.pilot,a.worker,a.condition,a.stage)


if __name__=='__main__':main()
