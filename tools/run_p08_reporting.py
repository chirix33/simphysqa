"""Finish the authorized evidence package after the empirical schedule closes."""
import subprocess
import re
from p08_common import *

assert load(RUN/'schedule-status.json')['status']=='complete'
b=budget(); state=b.check()
if not any(r['name']=='preflight_tests_reconciliation' for r in state['operations']):
    # This completed preflight preceded the supervised schedule. Preserve its log
    # and charge its reported elapsed time plus an explicit startup reserve.
    measured=float(re.search(r'Ran 127 tests in ([0-9.]+)s',(RUN/'tests-preflight.log').read_text()).group(1))
    reserve=15.; state['seconds']['cpu']=state['seconds'].get('cpu',0)+measured+reserve
    state['operations'].append({'name':'preflight_tests_reconciliation','resource':'cpu','seconds':measured+reserve,
        'measured_test_seconds':measured,'conservative_unmeasured_startup_reserve_seconds':reserve,'basis':'preserved unittest log; reserve is not a runtime measurement'})
    save(b.path,state); b.check()
state=b.read()
if not any(r['name']=='administrative_cpu_reserve' for r in state['operations']):
    state['seconds']['cpu']=state['seconds'].get('cpu',0)+60.
    state['operations'].append({'name':'administrative_cpu_reserve','resource':'cpu','seconds':60.,'measured':False,
        'basis':'conservative charge for selection/startup/provenance/status bookkeeping not individually timed; no additional experiment allowance'})
    save(b.path,state); b.check()
stages=[('final-summary','summarize_p08.py',[]),('artifact-verification','verify_p08_artifacts.py',[]),
    ('result-tables','report_p08_tables.py',[]),('reporting-setup','finish_p08.py',['setup']),
    ('reporting-plots','finish_p08.py',['plots']),('final-tests','finish_p08.py',['tests'])]
for name,script,args in stages:
    pointer=RUN/'launches'/f'{name}.json'
    if pointer.exists():
        if load(pointer)['status']=='complete': continue
        raise RuntimeError('Preserve failed reporting attempt for diagnosis: '+name)
    subprocess.run([sys.executable,str(ROOT/'tools/launch_p08.py'),'--name',name,script,*args],check=True)
save(RUN/'reporting-status.json',{'status':'complete','stages':len(stages),'scope':'saved-result evaluation, plots, content integrity and offline tests; no further fitting or model/provider calls'})
subprocess.run([sys.executable,str(ROOT/'tools/finalize_p08.py')],check=True,timeout=300)
