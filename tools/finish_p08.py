"""Budgeted reporting dependencies, plotting and final offline checks only."""
import argparse
import os
import subprocess
from p08_common import *

parser=argparse.ArgumentParser(); parser.add_argument('stage',choices=('setup','plots','tests')); args=parser.parse_args()
b=budget(); provenance('reporting-'+args.stage); env=RUN/'reporting-env'
with b.operation('reporting:'+args.stage,'cpu',cap=300,reserve_bytes=500000000 if args.stage=='setup' else 30000000):
    if args.stage=='setup':
        if env.exists(): raise FileExistsError('Preserve existing reporting environment')
        subprocess.run([sys.executable,'-m','venv',str(env)],check=True)
        subprocess.run([str(env/'bin/python'),'-m','pip','install','--no-cache-dir','matplotlib==3.10.3'],check=True)
        result=subprocess.check_output([str(env/'bin/python'),'-m','pip','freeze'],text=True)
        (RUN/'reporting-requirements.txt').write_text(result)
    elif args.stage=='plots':
        subprocess.run([str(env/'bin/python'),str(ROOT/'tools/report_p08_plots.py')],check=True)
    elif args.stage=='tests':
        environment={**os.environ,'CUDA_VISIBLE_DEVICES':'','PYTHONPATH':str(ROOT/'src')}
        with (RUN/'tests-final.log').open('w') as stream:
            subprocess.run([sys.executable,'-m','unittest','discover','-s','tests','-p','test_p*.py'],cwd=ROOT,env=environment,stdout=stream,stderr=subprocess.STDOUT,check=True)
        subprocess.run([sys.executable,'-m','compileall','-q',*[str(p) for p in (ROOT/'tools').glob('*p08*.py')]],check=True)
