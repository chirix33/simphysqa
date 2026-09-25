"""Read-only post-run EOS/transport/stopping/split audit; no model generation."""
import argparse,json,sys
from pathlib import Path
from collections import Counter
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'src'))
import torch
from transformers import AutoTokenizer,T5Config,T5ForConditionalGeneration,GenerationConfig
from phi_jepa.artifacts import canonical,digest
from phi_jepa.integration.contracts import PublicProblem,DOMAINS
from phi_jepa.integration.readers import ReleaseCatalog,json_lines
from phi_jepa.baselines.custom_io import TextCodec,parse_typed_answer,decode_result
from phi_jepa.baselines.custom_t5 import eos_positions

p=argparse.ArgumentParser(); p.add_argument('--native-root',type=Path,required=True); args=p.parse_args()
root=Path(__file__).resolve().parents[1]; config=json.loads((root/'configs/custom_p06.json').read_text()); pilot=json.loads((root/'configs/pilot_p07.json').read_text())
cache=args.native_root/'model-cache'; profile=args.native_root/'p06-profile'; run=args.native_root/'p06-correctness-02'
tokenizer=AutoTokenizer.from_pretrained(config['model'],revision=config['revision'],cache_dir=str(cache),local_files_only=True); codec=TextCodec(tokenizer)
prepared=json.loads((profile/'training-prepared.json').read_text()); targets=[]
for row in prepared:
    problem=PublicProblem.parse(row['public']); decoded=[]
    for name in ('teacher_labels','student_labels'):
        ids=row[name]; text=codec.generated_text(ids); parsed=parse_typed_answer(text,problem,explanation_required=name=='teacher_labels')
        if codec.tokens(text,config['max_target_tokens'])!=ids: raise ValueError('target_token_roundtrip')
        positions=eos_positions(torch.tensor([ids]),tokenizer.eos_token_id)
        if positions.item()!=len(ids)-1 or any(x in (tokenizer.unk_token_id,tokenizer.pad_token_id,-100) for x in ids): raise ValueError('target_special_token_or_mask')
        decoded.append(text); targets.append({'sample_id':problem.sample_id,'target_kind':name,'tokens':len(ids),'limit':config['max_target_tokens'],'eos_index':positions.item(),'typed_targets':len(parsed['targets']),'exact_roundtrip':True,'padding_tokens':0})
    if digest(decoded)!=row['target_sha256']: raise ValueError('target_identity')
stopping=[]; failures=[]
public={r['public']['sample_id']:PublicProblem.parse(r['public']) for r in json.loads((profile/'public-prepared.json').read_text())}
for method in config['methods']:
    directory=run/method; pointer=json.loads((directory/'checkpoint/latest.json').read_text())
    payload=torch.load(directory/'checkpoint'/pointer['file'],map_location='cpu',weights_only=True)
    if payload['identity']['config']!=config: raise ValueError('saved_runtime_settings_changed')
    t5config=T5Config(**payload['t5_config']); generation=GenerationConfig.from_model_config(t5config); generation.update(**config['generation'])
    if (generation.eos_token_id,generation.pad_token_id,generation.decoder_start_token_id)!=(1,0,0) or generation.max_new_tokens!=2048 or generation.do_sample or generation.num_beams!=1: raise ValueError('generation_stopping_changed')
    with torch.device('meta'): shell=T5ForConditionalGeneration(t5config)
    tether=next(r for r in prepared if r['public']['sample_id']==pilot['training_sample_id']); actual=[]
    for name in ('teacher_labels','student_labels'):
        labels=torch.tensor([tether[name]]); shifted=shell._shift_right(labels); pos=eos_positions(labels,1).item()
        if shifted[0,pos]!=labels[0,pos-1]: raise ValueError('EOS_prediction_shift')
        actual.append({'target_kind':name,'eos_prediction_index':pos,'decoder_input_token_id':shifted[0,pos].item(),'decoder_input_token':tokenizer.convert_ids_to_tokens(shifted[0,pos].item())})
    if payload['identity']['training_scenario']!=pilot['training_scenario_id']: raise ValueError('custom_training_scenario')
    stopping.append({'method':method,'checkpoint_sha256':pointer['sha256'],'updates':payload['updates'],'generation':{k:getattr(generation,k) for k in ('eos_token_id','pad_token_id','decoder_start_token_id','max_new_tokens','num_beams','do_sample','no_repeat_ngram_size','forced_eos_token_id','min_length','min_new_tokens')},'actual_EOS_shift':actual})
    del payload,shell
    for row in json.loads((directory/'generations.json').read_text()):
        for branch,output in row['branches'].items():
            ids=output.get('token_ids',[]); repeated=decode_result(codec,ids,public[row['sample_id']],teacher=branch!='student')
            if any(repeated[k]!=output[k] for k in ('status','reason') if k in output): raise ValueError('parse_failure_not_reproducible')
            missing=tokenizer.eos_token_id not in ids; capped=len(ids)-1==generation.max_new_tokens
            failures.append({'sample_id':row['sample_id'],'split':row['split'],'method':method,'branch':branch,'invalid_typed_output':output['status']!='success','typed_parse_failure_after_valid_EOS':output['status']!='success' and not missing,'missing_EOS':missing,'token_cap_termination':capped,'generated_tokens':len(ids)-1,'reason':output.get('reason'),'fallback_attempted':row.get('hybrid',{}).get('fallback_attempted',False) if branch=='student' else False,'fallback_recovered':row.get('hybrid',{}).get('fallback_used',False) if branch=='student' else False,'reparse_matches':True})
release=json.loads((root/'configs/model_training_p02a.json').read_text()); catalog=ReleaseCatalog(root/release['export_root'],release['export_index_sha256'],release['release_manifest_sha256'])
validation=next(row for row in json_lines(catalog.verified_file('tethered_load','validation','evaluator.jsonl')) if row['sample_id']==pilot['validation_sample_id'])['metadata']
overlap=[]; count=0
for domain in sorted(DOMAINS):
    for row in json_lines(catalog.verified_file(domain,'train','evaluator.jsonl')):
        count+=1; metadata=row['metadata']
        if metadata['base_scenario_id']==validation['base_scenario_id'] or metadata['split_group_id']==validation['split_group_id']: overlap.append(row['sample_id'])
if overlap or validation['split_group_id']!=pilot['validation_scenario_id']: raise ValueError('whole_validation_scenario_not_excluded')
primary=json.loads((args.native_root/'p03-correctness-01/summary.json').read_text())
expected={digest(('tethered_load',pilot['training_scenario_id'],round(.2+.02*i,8),round(.22+.02*i,8))) for i in range(20)}
if set(primary['provenance']['unique_transition_ids'])!=expected: raise ValueError('primary_physical_training_selection')
for name in ('p05b-correctness-01','p05b-ablations-01'):
    provenance=json.loads((args.native_root/name/'summary.json').read_text())['provenance']
    if provenance['training_scenario']!=pilot['training_scenario_id'] or set(provenance['transition_ids'])!=expected: raise ValueError('baseline_training_selection')
report={'status':'passed','target_audit':targets,'stopping_and_checkpoint_audit':stopping,'output_failures':failures,'whole_scenario_exclusion':{'training_metadata_rows_checked':count,'validation_base_scenario':validation['base_scenario_id'],'validation_split_group':validation['split_group_id'],'overlapping_training_questions':overlap,'all_method_training_scenarios_match':True,'primary_and_comparator_20_transition_sets_match':True},'new_model_generations':0,'targets_truncated':0,'answers_repaired':0,'limits_increased':False,'interpretation':'Serialization/stopping/parsing checks passed; output-quality failures persist after two updates, without a convergence or quality ranking inference.'}
destination=root/'docs/reviews/artifacts/P07/output-and-split-audit.json'; destination.write_bytes(canonical(report)); print(json.dumps(report))
