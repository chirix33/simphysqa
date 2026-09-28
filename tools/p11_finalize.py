"""Export actual results when frozen work finishes, or at the reporting reserve."""
from p11_common import *
import signal

def main():
    while time.time()<EXPENSIVE_STOP:
        local=(OUT/'cpu_done.json').exists() and (OUT/'gpu_done.json').exists()
        remote=(OUT/'answer_completion.json').exists() or budget().read()['stopped'] is not None
        if local and remote:break
        time.sleep(5)
    archive_sources('final-evidence');results=[]
    jobs=[('assessment','p11_assessment.py','phi-core'),('evaluation','p11_evaluate.py','phi-core'),('artifact-verification','p11_verify_artifacts.py','phi-core'),('plots','p11_plots.py',None),('report','p11_report.py','phi-core')]
    for name,script,env in jobs:
        remaining=DEADLINE-time.time()
        if remaining<10:break
        python=NATIVE/'.venvs'/env/'bin/python' if env else NATIVE/'p10-qualification-01/report-env/bin/python';start=time.time();log=OUT/'operations'/f'final-{name}-{int(start)}.log'
        with log.open('w') as f:
            p=subprocess.Popen([str(python),str(ROOT/'tools'/script)],cwd=ROOT,stdout=f,stderr=subprocess.STDOUT,start_new_session=True,env={**os.environ,'HF_HUB_OFFLINE':'1','TOKENIZERS_PARALLELISM':'false'})
            try:p.wait(timeout=min(240,remaining-5))
            except subprocess.TimeoutExpired:os.killpg(p.pid,signal.SIGTERM);p.wait()
        r={'name':'final-'+name,'resource':'cpu','start_utc':start,'seconds':time.time()-start,'exit_code':p.returncode,'status':'complete' if p.returncode==0 else 'failed_or_capped','log':str(log)};save(OUT/'operations'/f'final-{name}-{int(start)}.json',r);results.append(r)
        print(json.dumps(r),flush=True)
    save(OUT/'finalization.json',{'steps':results,'finished_utc':time.time(),'deadline_utc':DEADLINE,'deadline_met':time.time()<=DEADLINE})

if __name__=='__main__':main()
