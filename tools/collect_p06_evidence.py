"""Copy compact evidence and hash native artifacts; excludes weights/raw targets."""
import argparse,json,sys,shutil
from pathlib import Path
from hashlib import sha256
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'src'))
from phi_jepa.artifacts import canonical
p=argparse.ArgumentParser(); p.add_argument('--profile',type=Path,required=True); p.add_argument('--run',type=Path,required=True); args=p.parse_args()
root=Path(__file__).resolve().parents[1]; target=root/'docs/reviews/artifacts/P06'; target.mkdir(parents=True,exist_ok=True)
files={}
for source in (args.profile,args.run):
    for path in sorted(source.rglob('*')):
        if not path.is_file(): continue
        with path.open('rb') as f:
            import hashlib
            hash_value=hashlib.file_digest(f,'sha256').hexdigest()
        files[str(path)]={'sha256':hash_value,'bytes':path.stat().st_size}
        if path.name in ('preparation.json','model-download.json','evaluation.json','checkpoint-identity.json','qualify-report.json','fit-report.json','infer-report.json'):
            relative=Path(source.name)/path.relative_to(source); dest=target/relative; dest.parent.mkdir(parents=True,exist_ok=True); shutil.copyfile(path,dest)
(target/'native-artifacts.json').write_bytes(canonical(files)); print(json.dumps({'files_hashed':len(files),'destination':str(target)}))
generation=[]
for path in sorted(args.run.glob('*/generations.json')):
    for row in json.loads(path.read_text()):
        generation.append({'method':path.parent.name,'sample_id':row['sample_id'],'split':row['split'],
            'branches':{k:{'status':v['status'],'reason':v.get('reason'),'text_sha256':sha256((v.get('text') or '').encode()).hexdigest(),'token_ids_sha256':sha256(canonical(v.get('token_ids'))).hexdigest()} for k,v in row['branches'].items()},
            'costs':row['costs'],'hybrid_cost':row.get('hybrid_cost'),'fallback_attempted':row.get('hybrid',{}).get('fallback_attempted',False),'fallback_used':row.get('hybrid',{}).get('fallback_used',False)})
(target/args.run.name/'generation-summary.json').write_bytes(canonical(generation)); print(json.dumps(generation))
