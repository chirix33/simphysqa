"""Offline preparation: public lengths plus explicitly separated training targets."""
import argparse,json,sys
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'src'))
from transformers import AutoTokenizer
from phi_jepa.artifacts import canonical,digest
from phi_jepa.integration.contracts import DOMAINS,PublicProblem
from phi_jepa.integration.readers import ReleaseCatalog,PublicInputReader,file_hash
from phi_jepa.baselines.custom_io import TextCodec,public_text,training_targets,FORMAT

p=argparse.ArgumentParser(); p.add_argument('--profile',type=Path,required=True); p.add_argument('--output',type=Path,required=True); p.add_argument('--cache-dir',required=True); args=p.parse_args()
root=Path(__file__).resolve().parents[1]; c=json.loads((root/'configs/custom_p06.json').read_text()); r=json.loads((root/'configs/model_training_p02a.json').read_text())
catalog=ReleaseCatalog(root/r['export_root'],r['export_index_sha256'],r['release_manifest_sha256']); args.output.mkdir(parents=True,exist_ok=True)
t=AutoTokenizer.from_pretrained(c['model'],revision=c['revision'],cache_dir=args.cache_dir,local_files_only=True); t.model_max_length=c['max_input_tokens']; codec=TextCodec(t)
selected=json.loads((args.profile/'selected-public.json').read_text()); public_records=[]; training_records=[]; lengths=[]
for row in selected:
    problem=PublicProblem.parse(row['public']); enrich=json.loads((args.profile/'enrichment'/f'{problem.sample_id}.json').read_text())
    notes=enrich['notes']; text=public_text(problem,notes); ids=codec.tokens(text,c['max_input_tokens'])
    record={'public':row['public'],'enrichment':notes,'split':row['split'],'input_ids':ids,'input_sha256':digest(text),'tokens':len(ids)}
    public_records.append(record)
    if row['split']=='train':
        _,ref,identity=next(x for x in catalog.records(row['domain'],'train') if x[0].sample_id==problem.sample_id)
        teacher,student=training_targets(problem,ref)
        teacher_ids=codec.tokens(teacher,c['max_target_tokens']); student_ids=codec.tokens(student,c['max_target_tokens'])
        training_records.append({**record,'teacher_labels':teacher_ids,'student_labels':student_ids,'scenario_id':identity.group_id,'target_sha256':digest([teacher,student])})
    lengths.append({'sample_id':problem.sample_id,'domain':row['domain'],'split':row['split'],'input_tokens':len(ids)})
    print(json.dumps(lengths[-1]),flush=True)
(args.output/'public-prepared.json').write_bytes(canonical(public_records)); (args.output/'training-prepared.json').write_bytes(canonical(training_records))
report={'format':FORMAT,'config_sha256':digest(c),'release_identity':catalog.identity,'selected_lengths':lengths,'target_lengths':[{k:v for k,v in x.items() if k in ('scenario_id','target_sha256')}|{'sample_id':x['public']['sample_id'],'teacher_tokens':len(x['teacher_labels']),'student_tokens':len(x['student_labels']),'teacher_eos_index':len(x['teacher_labels'])-1,'student_eos_index':len(x['student_labels'])-1,'student_preceding_token':t.convert_ids_to_tokens(x['student_labels'][-2])} for x in training_records], 'scope':'eight existing enriched contexts; maximum case among this approved bounded profile, not full-release qualification','all_roundtrips_exact':True,'truncations':0}
(args.output/'preparation.json').write_bytes(canonical(report)); print(json.dumps(report),flush=True)
