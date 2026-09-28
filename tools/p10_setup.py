"""Isolated, pinned plotting environment; no model environment changes."""
import subprocess
import sys
from p10_common import *


def setup_report(run,job=None):
    directory=run.root/'report-env'; python=directory/'bin/python'
    if not python.exists(): subprocess.run([sys.executable,'-m','venv',str(directory)],check=True)
    lock=ROOT/'configs/report-p10.lock.txt'
    requirement=['-r',str(lock)] if lock.exists() else ['matplotlib==3.10.1','numpy==2.2.4']
    subprocess.run([str(python),'-m','pip','install','--no-cache-dir','--only-binary=:all:','--disable-pip-version-check',*requirement],check=True)
    frozen=subprocess.check_output([str(python),'-m','pip','freeze'],text=True)
    (run.root/'report-environment.lock.txt').write_text(frozen)
    if not lock.exists(): lock.write_text(frozen)
    subprocess.run([str(python),'-c','import matplotlib; matplotlib.use("Agg"); import matplotlib.pyplot'],check=True,
        env={**os.environ,'MPLCONFIGDIR':str(run.root/'plot-config')})
    # Account for the initial install's external pip/font caches as well. Later
    # installs disable wheel caching and keep plotting caches inside run.root.
    starts=[load(p)['started'] for p in (run.root/'attempts').glob('setup_report-*.json')]
    earliest=min(starts+[load(run.root/'stages/setup_report.json')['started']])
    external=[p for name in ('pip','matplotlib') for p in (Path.home()/'.cache'/name).rglob('*') if p.is_file() and p.stat().st_mtime>=earliest]
    save(run.root/'external-package-cache.json',{'bytes':sum(p.stat().st_size for p in external),
        'files':[{'path':str(p),'bytes':p.stat().st_size} for p in external],'since':earliest})
    save(run.root/'report-environment.json',{'python':str(python),'requirements_sha256':file_hash(lock),
        'installed':frozen.splitlines(),'model_environments_modified':False})
