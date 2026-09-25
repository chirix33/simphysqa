"""Close resource accounting after the review export; no empirical work."""
import shutil
import time
from p08_common import *

b=budget(); b.check(); provenance('final_export')
with b.operation('review_export_and_original_integrity_checks','cpu',cap=300,reserve_bytes=200000000):
    deadline=b.read()['active']['deadline']
    subprocess.run([sys.executable,str(ROOT/'tools/export_p08.py')],check=True,timeout=max(.1,deadline-time.time()))
state=b.read(); charges=state['provider']
state['provider_totals']={'attempts':len(charges),'input_tokens_charged':sum(r['charged_input'] for r in charges),
    'output_tokens_charged':sum(r['charged_output'] for r in charges),'usd_charged':sum(r['charged_usd'] for r in charges),
    'unknown_usage_attempts':sum(not r['usage_known'] for r in charges)}
state['accounting_closed_after_export']=True
save(RUN/'evaluation/resource-accounting.json',state)
destination=ROOT/'docs/reviews/artifacts/P08'
shutil.copy2(b.path,destination/'budget.json')
shutil.copy2(RUN/'evaluation/resource-accounting.json',destination/'evaluation/resource-accounting.json')
manifest=load(destination/'manifest.json')
manifest['files']={str(p.relative_to(destination)):{'sha256':file_hash(p),'bytes':p.stat().st_size} for p in destination.rglob('*') if p.is_file() and p.name!='manifest.json'}
manifest['native_bytes']=b.size(); manifest['export_bytes']=sum(v['bytes'] for v in manifest['files'].values())
manifest['aggregate_new_bytes']=manifest['native_bytes']+manifest['export_bytes']
assert manifest['aggregate_new_bytes']+1000000<CONFIG['caps']['artifact_bytes']
save(destination/'manifest.json',manifest)
print(json.dumps({'seconds':state['seconds'],'provider':state['provider_totals'],'aggregate_new_bytes':manifest['aggregate_new_bytes'],'stopped':state['stopped']}))
