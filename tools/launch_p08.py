"""One worker at a time; external enforcement of active deadlines and disk cap."""
import argparse
import os
import signal
import subprocess
import time
from p08_common import *

p=argparse.ArgumentParser(); p.add_argument('--name',required=True); p.add_argument('--env',choices=('phi-core','phi-coconut-custom','phi-codi-custom'),default='phi-core')
p.add_argument('script'); p.add_argument('arguments',nargs='*'); args=p.parse_args()
RUN.mkdir(parents=True,exist_ok=True); b=budget(); b.check()
# Older completed preparation/numerical launches predate whole-process overhead
# accounting. Reconcile once, between workers, without rewriting their reports.
state=b.read()
if state['active'] is None:
    reconciled=state.setdefault('overhead_reconciliations',{})
    for oldpath in (RUN/'launches').glob('*.json'):
        old=load(oldpath)
        if old.get('status')=='running' or 'resource' in old or old['name'] in reconciled: continue
        cmd=old['command']; script=Path(cmd[1]).name
        kind=('gpu' if script=='run_p08_custom.py' or (script=='prepare_p08.py' and 'encoding' in cmd)
              else 'cpu' if script in ('run_p08_numerical.py','evaluate_p08_numerical.py') or (script=='prepare_p08.py' and 'custom_preparation' in cmd) else None)
        if kind is None: continue
        accounted=sum(o['seconds'] for o in state['operations'] if o.get('resource')==kind and old['started']<=o.get('started',-1)<=old['started']+old['wall_seconds'])
        extra=max(0.,old['wall_seconds']-accounted); state['seconds'][kind]=state['seconds'].get(kind,0)+extra
        if kind=='gpu': state['seconds']['shared_gpu']=state['seconds'].get('shared_gpu',0)+extra
        reconciled[old['name']]={'resource':kind,'added_seconds':extra,'basis':'completed launcher wall minus already charged operations'}
    save(b.path,state)
b.check()
report_path=RUN/'launches'/f'{args.name}.json'; log_path=RUN/'logs'/f'{args.name}.log'
if report_path.exists(): raise FileExistsError('preserve_existing_attempt')
if b.read()['active']: raise RuntimeError('another_operation_is_active')
log_path.parent.mkdir(exist_ok=True)
command=[str(NATIVE/'.venvs'/args.env/'bin/python'),str(ROOT/'tools'/args.script),*args.arguments]
started=time.time(); record={'name':args.name,'command':command,'started':started,'status':'running','source_sha256':provenance('launch-'+args.name)}
save(report_path,record)
resource = ('gpu' if args.script=='run_p08_custom.py' or (args.script=='prepare_p08.py' and 'encoding' in args.arguments)
            else 'cpu' if args.script in ('run_p08_numerical.py','evaluate_p08_numerical.py','summarize_p08.py','report_p08_tables.py','verify_p08_artifacts.py','finish_p08.py') or (args.script=='prepare_p08.py' and 'custom_preparation' in args.arguments)
            else None)
initial_seconds = b.read()['seconds'].get(resource,0) if resource else 0
with log_path.open('w') as stream:
    process=subprocess.Popen(command,cwd=ROOT,stdout=stream,stderr=subprocess.STDOUT,start_new_session=True)
    reason=None
    while process.poll() is None:
        state=b.read(); active=state['active']
        if state['stopped']: reason=state['stopped']
        elif resource and initial_seconds+time.time()-started>=CONFIG['caps'][resource+'_seconds']: reason=resource+'_seconds'
        elif active and time.time()>=active['deadline']: reason='active_operation_deadline:'+active['name']
        elif b.size()>=CONFIG['caps']['artifact_bytes']: reason='artifact_bytes'
        if reason:
            os.killpg(process.pid,signal.SIGTERM)
            try: process.wait(timeout=2)
            except subprocess.TimeoutExpired: os.killpg(process.pid,signal.SIGKILL); process.wait()
            state=b.read(); active=state['active']
            if active:
                elapsed=time.time()-active['started']
                for key in [active['resource'],*active['buckets']]: state['seconds'][key]=state['seconds'].get(key,0)+elapsed
                state['operations'].append({**active,'seconds':elapsed,'interrupted':True}); state['active']=None
                if state['seconds'][active['resource']]>=CONFIG['caps'][active['resource']+'_seconds']: state['stopped']=reason
            if reason in ('artifact_bytes','gpu_seconds','cpu_seconds'): state['stopped']=reason
            save(b.path,state); break
        time.sleep(.25)
wall=time.time()-started
if resource:
    state=b.read(); charged=state['seconds'].get(resource,0)-initial_seconds; overhead=max(0.,wall-charged)
    state['seconds'][resource]=state['seconds'].get(resource,0)+overhead
    if resource=='gpu': state['seconds']['shared_gpu']=state['seconds'].get('shared_gpu',0)+overhead
    state['operations'].append({'name':'supervisor_overhead:'+args.name,'resource':resource,'seconds':overhead})
    save(b.path,state)
record.update(status='complete' if process.returncode==0 else 'failed_or_capped',exit_code=process.returncode,reason=reason,wall_seconds=wall,artifact_bytes=b.size(),resource=resource)
save(report_path,record); print(json.dumps(record),flush=True)
raise SystemExit(0 if process.returncode==0 else 2)
