"""Hash pinned local model/license/runtime files once; no inference or network."""
from pathlib import Path
import argparse,json,hashlib,time
def read(p):return json.loads(p.read_bytes())
def sha(p):
    with p.open('rb') as f:return hashlib.file_digest(f,'sha256').hexdigest()
def main(pilot,output):
    checked={};conditions=[];started=time.monotonic()
    for original in sorted((pilot/'conditions').glob('*.json')):
        c=read(original);cid=c['condition_id']
        for rev in sorted((pilot/'condition-revisions'/cid).glob('*.json')):c=read(rev)
        files={}
        if 'snapshot_path' in c:
            root=Path(c['snapshot_path'])
            for rel,expected in c['weight_files'].items():files[root/rel]=expected['sha256']
        else:files[Path(c['gguf_path'])]=c['gguf_sha256'];files[Path(c['server_path'])]=c['server_sha256']
        for path,expected in files.items():
            if str(path) not in checked:checked[str(path)]={'sha256':sha(path),'bytes':path.stat().st_size}
            if checked[str(path)]['sha256']!=expected:raise ValueError('pinned artifact changed: '+str(path))
        conditions.append({'condition_id':cid,'artifact_revision':c['artifact_revision'],'verified_files':len(files)})
        print(json.dumps({'condition_id':cid,'verified_files':len(files),'new_model_calls':0}),flush=True)
    result={'version':'SPQ06-local-artifact-integrity/1.0.0','conditions':conditions,'files':checked,
        'unique_bytes':sum(v['bytes'] for v in checked.values()),'wall_seconds':time.monotonic()-started,'new_calls':0,'network':False}
    output.parent.mkdir(parents=True,exist_ok=True)
    with output.open('xb') as f:f.write((json.dumps(result,sort_keys=True,separators=(',',':'))+'\n').encode())
if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('--pilot',type=Path,required=True);p.add_argument('--output',type=Path,required=True)
    a=p.parse_args();main(a.pilot,a.output)
