"""Sequential supervised stages under one shared pilot ledger; no hidden retries."""
import subprocess
from p08_common import *

stages=[]
for method in CONFIG['numerical_methods']:
    stages.extend([(f'train-{method}','phi-core','run_p08_numerical.py',['train',method]),
                   (f'forecast-{method}','phi-core','run_p08_numerical.py',['inference',method])])
stages.append(('numerical-evaluation','phi-core','evaluate_p08_numerical.py',[]))
for short,method in [('coconut','coconut_inspired_t5_gru'),('codi','codi_inspired_t5_distillation')]:
    for stage in ('diagnostic','broad','inference'):
        stages.append((short+'-'+stage,'phi-'+short+'-custom','run_p08_custom.py',[stage,method]))
stages.extend([('answers','phi-core','answer_assess_p08.py',['answers']),('assessment','phi-core','answer_assess_p08.py',['assessment'])])
for name,environment,script,args in stages:
    previous=RUN/'launches'/f'{name}.json'
    if previous.exists():
        if load(previous)['status']=='complete': continue
        raise RuntimeError('Existing failed/capped attempt requires explicit bounded diagnosis: '+name)
    budget().check()
    result=subprocess.run([sys.executable,str(ROOT/'tools/launch_p08.py'),'--name',name,'--env',environment,script,*args],cwd=ROOT)
    if result.returncode:
        save(RUN/'schedule-status.json',{'status':'stopped','stage':name,'returncode':result.returncode})
        raise SystemExit(result.returncode)
save(RUN/'schedule-status.json',{'status':'complete','stages':len(stages)})
