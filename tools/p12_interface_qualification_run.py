"""Authorized development-only supervisor. Frozen scientific interface is imported unchanged."""
import argparse
import json
import os
from pathlib import Path
import signal
import subprocess
import sys
import time

from p12_common import ROOT, NATIVE, load, save
from p12_answer_interface_followup import DEST as PREP, CONDITIONS, settings, verify
from phi_jepa.artifacts import digest
from phi_jepa.integration.readers import file_hash

PLAN = PREP/'development/plan.json'
RUN = NATIVE/'p12-answer-interface-qualification-02'
EXPORT = ROOT/'docs/reviews/artifacts/P12_answer_interface_qualification_02'
SMI = '/usr/lib/wsl/lib/nvidia-smi'


def execution_files():
    return {str(p.relative_to(ROOT)):file_hash(p) for p in
            (Path(__file__),ROOT/'tools/p12_interface_qualification_report.py',ROOT/'tests/test_p12_qualification_run.py')}


def checked():
    cfg=load(PLAN)
    if cfg['kind']!='development' or cfg['proposed_run_root']!=str(RUN):
        raise ValueError('development-only fixed run required')
    for rel,sha in cfg['source_files'].items():
        if file_hash(ROOT/rel)!=sha: raise ValueError('frozen scientific source changed: '+rel)
    for package,expected in cfg['runtime'].items():
        from importlib.metadata import version
        if version(package)!=expected: raise ValueError('runtime changed: '+package)
    auth=load(RUN/'authorization.json')
    if auth['proposal_sha256']!=file_hash(PLAN) or auth['execution_files']!=execution_files():
        raise ValueError('authorization/source identity mismatch')
    rows=load(RUN/'diagnostic-public.json')
    if digest(rows)!=cfg['selection_sha256']: raise ValueError('cohort changed')
    for row in cfg['request_manifest']:
        if file_hash(ROOT/row['path'])!=row['sha256']: raise ValueError('frozen request changed')
    return cfg,rows


def initialize():
    verify()
    RUN.mkdir(parents=True,exist_ok=True)
    cfg=load(PLAN)
    auth=dict(version='p12-development-execution-authorization-v1',date='2026-09-30',
        user_instruction='Execute the prepared 32-request development qualification, with 4096 token allowances for Qwen-thinking-on and Llama CoT.',
        proposal_sha256=file_hash(PLAN),freeze_sha256=file_hash(PREP/'freeze.json'),
        execution_files=execution_files(),scientific_source_sha256=cfg['source_sha256'],
        fresh_validation_authorized=False,expanded_study_authorized=False,paid_calls=0)
    path=RUN/'authorization.json'
    if path.exists():
        if load(path)!=auth: raise ValueError('existing execution identity differs')
        checked(); return
    if (RUN/'budget.json').exists(): raise ValueError('unowned budget exists')
    save(path,auth)
    save(RUN/'approved-plan.json',{**cfg,'enabled':True,'execution_authorized':True,'authorization':auth})
    save(RUN/'diagnostic-public.json',load(PREP/'development/public-cohort.json'))
    save(RUN/'budget.json',dict(started_unix=None,deadline_unix=None,finished_unix=None,
        maximum_attempts=32,attempts=[],workers=[],status='prepared'))
    for rel,sha in {**cfg['source_files'],**auth['execution_files']}.items():
        dest=RUN/'sources/blobs'/sha
        dest.parent.mkdir(parents=True,exist_ok=True)
        if not dest.exists():dest.write_bytes((ROOT/rel).read_bytes())
    for r in cfg['request_manifest']:
        dest=RUN/'requests'/r['condition']/(r['sample_id']+'.json')
        dest.parent.mkdir(parents=True,exist_ok=True);dest.write_bytes((ROOT/r['path']).read_bytes())
    checked()


def overhead(ledger,now):
    if ledger['started_unix'] is None:return 0.
    end=ledger.get('finished_unix') or now
    request_seconds=sum((a.get('finished_unix',end)-a['started_unix']) for a in ledger['attempts'])
    return max(0.,end-ledger['started_unix']-request_seconds)


def reserve(ledger,condition,sid,sha,now,limit):
    if len(ledger['attempts'])>=32: raise ValueError('32-attempt cap exhausted')
    if ledger['started_unix'] is None:raise ValueError('window must start before loading')
    if now+limit>ledger['deadline_unix']:raise ValueError('insufficient remaining shared window')
    if overhead(ledger,now)>=1440:raise ValueError('setup/overhead allowance exhausted')
    if any(a['condition']==condition and a['sample_id']==sid for a in ledger['attempts']):
        raise ValueError('attempt already counted; no retry')
    entry=dict(condition=condition,sample_id=sid,request_sha256=sha,round=1,
        started_unix=now,deadline_unix=now+limit,status='reserved')
    ledger['attempts'].append(entry)
    return entry


def terminate(process):
    if process.poll() is None:
        os.killpg(process.pid,signal.SIGKILL)
    process.wait(timeout=10)


def wait_for_file(process,path,deadline):
    while True:
        now=time.time()
        if path.exists():
            value=load(path)
            # Results produced past the hard deadline cannot become successful on resume.
            if value.get('worker_finished_unix',now)>deadline:return 'hard_time_cap'
            return 'ready'
        if now>=deadline:return 'hard_time_cap'
        if process.poll() is not None:return 'worker_exit'
        time.sleep(min(.05,deadline-now))


class TokenArchive:
    """Observational HF streamer: records tokens but does not modify generation."""
    def __init__(self,path,prompt_ids):
        self.file=Path(path).open('x',buffering=1)
        self.prompt_ids=prompt_ids
        self.first=True

    def put(self,value):
        ids=value.detach().cpu().tolist()
        if ids and isinstance(ids[0],list):
            if len(ids)!=1:raise ValueError('batch one required')
            ids=ids[0]
        if self.first:
            self.first=False
            if ids!=self.prompt_ids:raise ValueError('streamed prompt identity mismatch')
            return
        self.file.write(json.dumps(ids)+'\n')

    def end(self):
        self.file.flush()

    def close(self):
        self.file.close()


def worker(condition,folder):
    from p10_common import guard_deployment_io
    guard_deployment_io()
    cfg,rows=checked()
    import torch
    from transformers import AutoModelForCausalLM
    from phi_jepa.integration.contracts import PublicProblem
    from phi_jepa.providers.constrained_local import ConstrainedLocalBackend
    torch.set_num_threads(2)
    start=time.perf_counter()
    s,tok=settings(condition)
    model=AutoModelForCausalLM.from_pretrained(s.model,revision=s.revision,cache_dir=str(NATIVE/'model-cache'),
        local_files_only=True,trust_remote_code=False,use_safetensors=True,
        torch_dtype=torch.bfloat16,attn_implementation='sdpa').to('cuda')
    from p12_answer_interface import ASSET
    backend=ConstrainedLocalBackend(model,tok,s,load(ASSET)['prompt'],explicit_cot=condition=='llama31_8b_cot')
    original_generate=model.generate
    active={}
    def logged_generate(*args,**kwargs):
        return original_generate(*args,**kwargs,streamer=active['streamer'])
    model.generate=logged_generate
    save(folder/'ready.json',dict(worker_finished_unix=time.time(),pid=os.getpid(),
        load_and_backend_seconds=time.perf_counter()-start,compiler_setup_seconds=backend.compiler_setup_seconds,
        gpu=torch.cuda.get_device_name(),cuda=torch.version.cuda,generation_config=model.generation_config.to_dict()))
    by_id={r['sample_id']:r for r in rows}
    for line in sys.stdin:
        command=json.loads(line);sid=command['sample_id'];row=by_id[sid]
        req=load(RUN/'requests'/condition/(sid+'.json'))
        path=RUN/'round-1'/condition/(sid+'.json')
        if path.exists():raise ValueError('refuse result overwrite')
        tokens=RUN/'tokens'/condition/(sid+'.jsonl');tokens.parent.mkdir(parents=True,exist_ok=True)
        archive=TokenArchive(tokens,req['input_token_ids']);active['streamer']=archive
        try:
            result=backend.answer(PublicProblem.parse(row['public']),req)
        finally:
            archive.close()
        result.update(condition=condition,domain=row['domain'],scenario_id=row['scenario_id'],
            split='validation',round=1,source_sha256=cfg['source_sha256'],worker_finished_unix=time.time())
        save(path,result)


def incomplete_record(row,condition,request,failure,started):
    tokens=RUN/'tokens'/condition/(row['sample_id']+'.jsonl')
    ids=[]
    if tokens.exists():
        for line in tokens.read_text().splitlines():
            try:ids.extend(json.loads(line))
            except json.JSONDecodeError:break  # retain interrupted final line in the original log
    return dict(sample_id=row['sample_id'],condition=condition,domain=row['domain'],scenario_id=row['scenario_id'],
        split='validation',round=1,identity=request,request_sha256=digest(request),answer=None,
        status='runtime_failure',failure=failure,syntax_valid=False,full_contract_valid=False,
        EOS_terminated=False,token_cap_termination=False,time_cap_termination=failure=='hard_time_cap',
        input_tokens=len(request['input_token_ids']),output_tokens=len(ids),generated_token_ids=ids,
        raw_completion=None,reasoning_tokens=None,final_answer_tokens=None,
        latency_seconds=time.time()-started,peak_allocated_bytes=None,peak_reserved_bytes=None,
        retries=0,repairs=0,partial_tokens_note='Durable HF stream; decode after execution without recovery or scoring it as a successful answer.')


def run():
    import fcntl
    initialize();cfg,rows=checked()
    handle=(RUN/'supervisor.lock').open('a');fcntl.flock(handle,fcntl.LOCK_EX|fcntl.LOCK_NB)
    ledger=load(RUN/'budget.json')
    if ledger.get('finished_unix') is not None:
        print('Run already closed; no new attempts.');return
    busy=subprocess.check_output([SMI,'--query-compute-apps=pid,process_name,used_memory','--format=csv,noheader'],text=True).strip()
    if busy:raise ValueError('GPU busy; serialize after active worker: '+busy)
    if ledger['started_unix'] is None:
        now=time.time();ledger.update(started_unix=now,deadline_unix=now+7200,status='running')
        save(RUN/'budget.json',ledger)
    # Crash recovery retains every reservation. Never repeat a model request.
    for a in ledger['attempts']:
        if a['status']=='reserved':
            path=RUN/'round-1'/a['condition']/(a['sample_id']+'.json')
            if not path.exists():
                row=next(r for r in rows if r['sample_id']==a['sample_id'])
                req=load(RUN/'requests'/a['condition']/(a['sample_id']+'.json'))
                save(path,incomplete_record(row,a['condition'],req,'interrupted_attempt',a['started_unix']))
            a.update(status='finished',finished_unix=min(time.time(),a['deadline_unix']),result_status=load(path)['status'])
    process=None
    try:
        for condition in CONDITIONS:
            settings_dict=cfg['conditions'][condition]['settings'];limit=settings_dict['max_seconds']
            for row in rows:
                sid=row['sample_id']
                if any(a['condition']==condition and a['sample_id']==sid for a in ledger['attempts']):continue
                now=time.time()
                if now+limit>ledger['deadline_unix'] or overhead(ledger,now)>=1440:
                    raise TimeoutError('shared window/setup allowance exhausted')
                if process is None:
                    folder=RUN/'workers'/f'{len(ledger["workers"]):02d}-{condition}'
                    folder.mkdir(parents=True,exist_ok=True)
                    log=(folder/'worker.log').open('a')
                    start=time.time()
                    process=subprocess.Popen([sys.executable,str(Path(__file__).resolve()),'worker','--condition',condition,'--folder',str(folder)],
                        stdin=subprocess.PIPE,stdout=log,stderr=subprocess.STDOUT,text=True,cwd=ROOT,start_new_session=True)
                    w=dict(condition=condition,pid=process.pid,started_unix=start,folder=str(folder))
                    ledger['workers'].append(w);save(RUN/'budget.json',ledger)
                    deadline=min(ledger['deadline_unix']-limit,start+1440-overhead(ledger,start))
                    status=wait_for_file(process,folder/'ready.json',deadline)
                    if status!='ready':raise RuntimeError('model setup failed: '+status)
                    w.update(ready_unix=time.time(),runtime=load(folder/'ready.json'));save(RUN/'budget.json',ledger)
                req=load(RUN/'requests'/condition/(sid+'.json'))
                a=reserve(ledger,condition,sid,digest(req),time.time(),limit)
                save(RUN/'budget.json',ledger)
                path=RUN/'round-1'/condition/(sid+'.json');path.parent.mkdir(parents=True,exist_ok=True)
                process.stdin.write(json.dumps({'sample_id':sid})+'\n');process.stdin.flush()
                status=wait_for_file(process,path,min(a['deadline_unix'],ledger['deadline_unix']))
                if status!='ready':
                    terminate(process);process=None
                    if path.exists():
                        path.rename(path.with_suffix('.late.json'))
                    save(path,incomplete_record(row,condition,req,status,a['started_unix']))
                result=load(path)
                a.update(status='finished',finished_unix=time.time(),result_status=result['status'],failure=result.get('failure'))
                save(RUN/'budget.json',ledger)
                print(json.dumps({k:result.get(k) for k in ('condition','sample_id','status','failure','output_tokens','reasoning_tokens','latency_seconds')}),flush=True)
            if process is not None:
                process.stdin.close()
                try:process.wait(timeout=min(10,max(.01,ledger['deadline_unix']-time.time())))
                except subprocess.TimeoutExpired:terminate(process)
                process=None
        ledger['status']='completed'
    except Exception as exc:
        ledger.update(status='stopped',stop_reason=type(exc).__name__+': '+str(exc))
        raise
    finally:
        if process is not None:terminate(process)
        ledger['finished_unix']=time.time()
        ledger['model_window_elapsed_seconds']=ledger['finished_unix']-ledger['started_unix']
        ledger['setup_and_other_overhead_seconds']=overhead(ledger,ledger['finished_unix'])
        save(RUN/'budget.json',ledger)
        print(json.dumps({k:ledger.get(k) for k in ('status','stop_reason','model_window_elapsed_seconds','setup_and_other_overhead_seconds')}),flush=True)


if __name__=='__main__':
    parser=argparse.ArgumentParser(description=__doc__);parser.add_argument('stage',choices=('initialize','run','worker'))
    parser.add_argument('--condition',choices=CONDITIONS);parser.add_argument('--folder',type=Path)
    args=parser.parse_args()
    if args.stage=='worker':worker(args.condition,args.folder)
    else:globals()[args.stage]()
