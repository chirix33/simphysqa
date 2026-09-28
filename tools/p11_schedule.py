"""Deadline supervisor: one GPU worker, independent CPU and provider ownership."""
from p11_common import *
import signal

def launch(name,script,args,resource,envname='phi-core'):
    time_guard();folder=OUT/'operations';folder.mkdir(exist_ok=True);start=time.time();log=folder/f'{name}-{int(start)}.log'
    command=[str(NATIVE/'.venvs'/envname/'bin/python'),str(ROOT/'tools'/script),*args]
    with log.open('w') as output:
        p=subprocess.Popen(command,cwd=ROOT,stdout=output,stderr=subprocess.STDOUT,start_new_session=True,env={**os.environ,'HF_HUB_OFFLINE':'1','TOKENIZERS_PARALLELISM':'false','OMP_NUM_THREADS':'2'})
        while p.poll() is None:
            if time.time()>=EXPENSIVE_STOP:
                os.killpg(p.pid,signal.SIGTERM);p.wait();break
            # Separate provider ledger is read, never mutated by this supervisor.
            try:budget().check()
            except Exception:
                os.killpg(p.pid,signal.SIGTERM);p.wait();break
            time.sleep(2)
    value={'name':name,'resource':resource,'start_utc':start,'seconds':time.time()-start,'exit_code':p.returncode,'log':str(log),'command':command,'status':'complete' if p.returncode==0 else 'failed_or_capped'}
    save(folder/f'{name}-{int(start)}.json',value);print(json.dumps(value),flush=True);return p.returncode==0

def cpu():
    for cohort in ('main','appendix'):
        for domain in load(OUT/'plan.json')['cohorts']:
            if launch(f'{cohort}-{domain}-train','p11_numerical.py',['train',domain,cohort],'cpu'):
                launch(f'{cohort}-{domain}-forecast','p11_numerical.py',['inference',domain,cohort],'cpu')
    save(OUT/'cpu_done.json',{'time':time.time()})

def gpu():
    rows=load(OUT/'selected-public.json')
    while any(not (OUT/'enrichment'/f"{r['sample_id']}.json").exists() and not (OUT/'failures/enrichment'/f"{r['sample_id']}.json").exists() for r in rows):
        time_guard();time.sleep(3)
    if not launch('private-train-selection-preparation','p11_data.py',['references'],'cpu'):return
    if not launch('qwen-encoding','p11_data.py',['encode'],'gpu'):return
    if not launch('custom-preparation','p11_data.py',['custom_prepare'],'cpu','phi-coconut-custom'):return
    # Numerical fits use CPU only; they cannot compete for the GPU.
    cpu_log=(OUT/'operations/cpu-supervisor.log').open('w')
    child=subprocess.Popen([str(NATIVE/'.venvs/phi-core/bin/python'),str(Path(__file__).resolve()),'cpu'],cwd=ROOT,stdout=cpu_log,stderr=subprocess.STDOUT,start_new_session=True)
    for short in ('coconut','codi'):
        if launch(short+'-train','p11_custom.py',['train',short],'gpu',f'phi-{short}-custom'):
            launch(short+'-test','p11_custom.py',['inference',short],'gpu',f'phi-{short}-custom')
    while child.poll() is None and time.time()<EXPENSIVE_STOP:time.sleep(2)
    save(OUT/'gpu_done.json',{'time':time.time(),'cpu_exit':child.poll()})

if __name__=='__main__':globals()[sys.argv[1]]()
