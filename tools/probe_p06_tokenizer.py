import json
from pathlib import Path
from transformers import AutoTokenizer
root=Path(__file__).resolve().parents[1]
c=json.loads((root/'configs/custom_p06.json').read_text())
t=AutoTokenizer.from_pretrained(c['model'],revision=c['revision'],cache_dir='/home/aashraf/phi-jepa/model-cache',local_files_only=True)
for s in ['{ -1.23e-4 true false [ ] }','<extra_id_0> "value": [-1.23e-4, true] <extra_id_1>','angle_rad | m/s^2 | x_y | ≥ ± °']:
    ids=t.encode(s); print(json.dumps({'text':s,'ids':ids,'decoded':t.decode(ids),'unknown':t.unk_token_id in ids}))
import sys
sys.path.insert(0,str(root/'src'))
from phi_jepa.integration.readers import ReleaseCatalog
r=json.loads((root/'configs/model_training_p02a.json').read_text()); catalog=ReleaseCatalog(root/r['export_root'],r['export_index_sha256'],r['release_manifest_sha256'])
p,ref,i=next(catalog.records('tethered_load','train'))
print(json.dumps({'reference_keys':list(ref),'explanation':ref['explanation'],'labels':ref['structured_label'],'spec':p.input['answer_spec']}))
