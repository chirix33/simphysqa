"""Hash verification of preserved pre-recovery scientific artifacts; no model calls."""
from pathlib import Path
import json,hashlib,time
from simphysqa import complement_execution as c, execution_adapter as a
B=Path('C:/Users/aashraf/.codex/visualizations/2026/10/06/01a1131b-eac2-7a31-afb4-f219a8dd6471/spq06/2026-10-09')
RUN=B/'complement-execution-1.0.0'; output=RUN/'final-preservation-1.0.1.json'
if output.exists():raise ValueError('exclusive receipt already exists')
ledger=c.Ledger(B/'central-main-1.0.0/main.sqlite')
control=ledger.reserve_control('Ashraf','final historical artifact hash preservation verification',300)
started=time.monotonic()
try:
 baseline=B/'restart-execution-1.0.0/preservation-before.json'; hashes=a.read(baseline)
 hashes.update(a.read(RUN/'execution-freeze.json')['identities'])
 cm=a.read(B/'complement-preparation-1.0.1/complement-manifest.json')
 hashes.update(cm['source_hashes'])
 changed=[];excluded=[]
 for name,expected in hashes.items():
  p=Path(name)
  if p.name in ('main.sqlite','main.sqlite-shm','main.sqlite-wal'):
   excluded.append({'path':name,'reason':'live central ledger; original rows checked separately'});continue
  if not p.is_file() or a.sha(p)!=expected:changed.append(name)
 ledger.settle_control(control,time.monotonic()-started,'complete')
 a.put(output,{'version':'SPQ06-complement-preservation/1.0.1','baseline_sha256':a.sha(baseline),'historical_hashes_checked':len(hashes)-len(excluded),'changed':changed,'excluded':excluded,'preserved':not changed,'control':control,'accounting':ledger.summary(),'model_calls':0})
 if changed:raise ValueError('preservation discrepancy: '+str(changed[:8]))
 print(json.dumps({'preserved':True,'checked':len(hashes)-len(excluded),'accounting':ledger.summary()}))
finally:ledger.db.close()
