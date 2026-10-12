"""Bounded final documentation and file verification, no model execution."""
import subprocess,time,json,sys
from pathlib import Path
from simphysqa import complement_execution as c, execution_adapter as a
B=Path('C:/Users/aashraf/.codex/visualizations/2026/10/06/01a1131b-eac2-7a31-afb4-f219a8dd6471/spq06/2026-10-09')
RUN=B/'complement-execution-1.0.0'; O=B/'complement-analysis-1.0.1'
R=Path('C:/Users/aashraf/.codex/worktrees/simphysqa/phi-jepa')
ledger=c.Ledger(B/'central-main-1.0.0/main.sqlite'); control=ledger.reserve_control('Ashraf','final completion documentation and artifact verification',300)
started=time.monotonic()
try:
 log=RUN/'final-documentation-1.0.0.log'
 with log.open('x',encoding='utf8') as f:
  subprocess.run([sys.executable,str(B/'complement-final-docs-1.0.0.py')],stdout=f,stderr=subprocess.STDOUT,check=True,timeout=300)
 manifest=a.read(O/'manifest.json');bad=[]
 for name,expected in manifest['files'].items():
  if a.sha(O/name)!=expected:bad.append(name)
 archive=R/'docs/simphysqa/prompt_archive/SPQ06/complement-analysis-1.0.1'
 for entry in a.read(archive/'file-index.json')['entries']:
  if a.sha(archive/entry['file'])!=entry['sha256'] or a.sha(Path(entry['source']))!=entry['sha256']:bad.append(entry['file'])
 if bad:raise ValueError('final file hash mismatch: '+str(bad))
 subprocess.run(['git','diff','--check'],cwd=R,check=True,timeout=30)
 ledger.settle_control(control,time.monotonic()-started,'complete')
 a.put(RUN/'final-delivery-1.0.0.json',{'control':control,'analysis_files_verified':len(manifest['files']),'archive_sources_verified':True,'git_diff_check_passed':True,'accounting':ledger.summary(),'analysis_manifest_sha256':a.sha(O/'manifest.json'),'audit_zip_sha256':a.sha(O/'audit-bundle-1.0.0.zip'),'model_calls':0,'no_push_merge_rebase':True})
 print(a.canonical(ledger.summary()).decode())
except BaseException:
 if ledger.db.execute('SELECT actual FROM control_work WHERE id=?',(control,)).fetchone()[0] is None:ledger.settle_control(control,time.monotonic()-started,'unknown')
 raise
finally:ledger.db.close()
