"""Authorized power-loss recovery; zero answering calls, no attempt releases."""
import sys,time,subprocess
from pathlib import Path
from simphysqa import main_record_index,main_restart,execution_adapter as adapter
from simphysqa.execution_adapter import read,put,sha
BASE=Path(__file__).resolve().parents[1]
RUN=BASE/'main-ashraf-1.0.0';ROOT=RUN/'restart-recovery-1.0.0'
REPO=Path('C:/Users/aashraf/.codex/worktrees/simphysqa/phi-jepa')
sys.path.insert(0,str(BASE/'main-src-1.0.1'))
from main_run import central_verify,command,wsl,linux

def recover():
    ROOT.mkdir(exist_ok=False)
    ledger=main_record_index.Ledger(BASE/'central-main-1.0.0/main.sqlite')
    control=ledger.reserve_control('Ashraf','power-loss partial return/import, actual token checks, scoring joins and interrupted receipt preservation',600)
    started=time.monotonic()
    try:
        put(ROOT/'freeze.json',{'version':'SPQ06-main-restart/1.0.0','reason':'user reported abrupt PC restart',
            'sources':{str(p):sha(p) for p in (Path(__file__),REPO/'src/simphysqa/main_restart.py',REPO/'tests/test_main_restart.py',BASE/'main-restart-offline-1.0.3.log')},
            'unchanged_worker_package_sha256':sha(BASE/'execution-public-1.1.1/package-manifest.json'),
            'scientific_retries':0,'reservation_releases':0,'accounting_before':ledger.summary()})
        processes=subprocess.run(['wsl.exe','-d','Ubuntu-24.04','--','ps','-eo','pid,comm,args'],capture_output=True,check=True)
        with (ROOT/'stopped-process-inspection.txt').open('xb') as f:f.write(processes.stdout)
        text=processes.stdout.decode('utf8')
        if any(token in text for token in ('public_executor.py','qwen3_8b_direct.py','qwen3_32b_awq','llama31_8b','main_preflight.py')):
            raise ValueError('answering/preflight worker still present; no resume')
        gpu=subprocess.run(['wsl.exe','-d','Ubuntu-24.04','--','/usr/lib/wsl/lib/nvidia-smi','--query-gpu=index,name,uuid,memory.total,memory.used,driver_version','--format=csv,noheader,nounits'],capture_output=True,check=True)
        with (ROOT/'gpu-after-restart.txt').open('xb') as f:f.write(gpu.stdout)
        evidence={'worker_stopped':True,'user_report':'abrupt PC restart',
            'evidence_files':{str(ROOT/'stopped-process-inspection.txt'):sha(ROOT/'stopped-process-inspection.txt'),str(ROOT/'gpu-after-restart.txt'):sha(ROOT/'gpu-after-restart.txt')}}
        name='031--qwen3_8b_direct--structured_only--stage1';job=RUN/'jobs'/name
        result=main_restart.recover(ledger,job,RUN/'returns'/name,RUN/'immutable-imports',evidence,RUN/'routes/qwen3_8b_direct--structured_only')
        put(ROOT/'recovery-receipt.json',result)
        bindings=read(job/'bindings.json')
        command(wsl(bindings,BASE/'main-src-1.0.1/main_verify.py',['--package',linux(BASE/'execution-public-1.1.1'),'--job',linux(job),
            '--preflight',linux(RUN/'preflights'/name/'render-verification.json'),'--output',linux(ROOT/'actual-output-verification.json')]),ROOT/'actual-output-verification.log',timeout=600)
        central_verify(ledger,result['accepted_saved_keys'],ROOT/'central-parsed-records.json')
        ledger.settle_control(control,time.monotonic()-started)
        put(ROOT/'accounting-after.json',ledger.summary())
        put(ROOT/'completion.json',{'saved_initials_imported':len(result['accepted_saved_keys']),
            'interrupted_missing_initials':len(result['interrupted_missing_or_invalid_keys']),
            'unknown_process_bound_retained':result['original_bound_seconds'],'actual_duration':None,
            'never_reserved_resume_only':True,'answering_calls':0,'scientific_retries':0,'original_job_bytes_preserved':True})
        print('recovery complete',read(ROOT/'completion.json'),ledger.summary(),flush=True)
    except BaseException:
        row=ledger.db.execute('SELECT actual FROM control_work WHERE id=?',(control,)).fetchone()
        if row and row[0] is None:ledger.settle_control(control,time.monotonic()-started,'unknown')
        raise
    finally:ledger.db.close()

if __name__=='__main__':recover()
