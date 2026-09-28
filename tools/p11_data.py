"""Frozen-cohort caches and private training targets, without silent omission."""
from p11_common import *
from dataclasses import asdict
from phi_jepa.integration.contracts import PublicProblem,enriched_context,validate_enrichment

def encode():
    from phi_jepa.providers.qwen import QwenEncoder
    from phi_jepa.providers.context import ContextEncoder
    from phi_jepa.providers.cache import FrozenOutputCache
    c=load(ROOT/'configs/model_context_p02b.json');backend=None;records=[]
    for row in load(OUT/'selected-public.json'):
        time_guard();p=PublicProblem.parse(row['public']);sid=p.sample_id;path=OUT/'embeddings/enriched'/f'{sid}.json'
        if path.exists():continue
        source=OUT/'enrichment'/f'{sid}.json'
        if not source.exists(): records.append({'sample_id':sid,'status':'missing_enrichment'});continue
        notes=load(source);validate_enrichment(p,notes);text=enriched_context(p,notes,p.input['observation_cutoff'])
        prior=NATIVE/'p10-qualification-01/embeddings/enriched'/f'{sid}.json'
        if prior.exists() and load(prior)['context_sha256']==digest(text):save(path,load(prior));continue
        if backend is None:backend=QwenEncoder(str(NATIVE/'model-cache'),runtime_versions=c['encoder']['runtime_versions']);enc=ContextEncoder(backend,FrozenOutputCache(OUT/'embedding_cache'))
        start=time.time()
        try:save(path,asdict(enc.encode(p,p.input['observation_cutoff'],mode='enriched',enrichment=notes)));status='success'
        except Exception as exc:status='failure';save(OUT/'failures/embedding'/f'{sid}.json',{'reason':str(exc),'type':type(exc).__name__})
        records.append({'sample_id':sid,'domain':row['domain'],'seconds':time.time()-start,'status':status});save(OUT/'encoding-progress.json',records)
    settings=asdict(backend.settings) if backend else load(NATIVE/'p10-qualification-01/encoding-report.json')['settings']
    save(OUT/'encoding-report.json',{'settings':settings,'records':records,'expected':272,'available':len(list((OUT/'embeddings/enriched').glob('*.json')))})

def references():
    cat=catalog();rows=load(OUT/'selected-public.json')
    for domain in sorted({r['domain'] for r in rows}):
        for split in ('train','validation'):
            path=OUT/'private'/domain/f'{split}-references.json'
            if path.exists():continue
            ids={r['sample_id'] for r in rows if r['domain']==domain and r['split']==split}
            save(path,{p.sample_id:ref for p,ref,ident in cat.records(domain,split) if p.sample_id in ids})

def custom_prepare():
    from transformers import AutoTokenizer
    from phi_jepa.baselines.custom_io import TextCodec,public_text,training_targets
    c=load(ROOT/'configs/custom_p06.json');tok=AutoTokenizer.from_pretrained(c['model'],revision=c['revision'],cache_dir=str(NATIVE/'model-cache'),local_files_only=True);tok.model_max_length=c['max_input_tokens'];codec=TextCodec(tok)
    public=[];targets=[];lengths=[];failures=[]
    for row in [r for r in load(OUT/'selected-public.json') if r['appendix']]:
        p=PublicProblem.parse(row['public']);path=OUT/'enrichment'/f'{p.sample_id}.json'
        try:
            notes=load(path)['notes'];ids={b:codec.tokens(public_text(p,notes,branch=b),c['max_input_tokens']) for b in ('coconut','teacher','student')}
            public.append({**row,'branch_input_ids':ids});length={'sample_id':p.sample_id,'domain':row['domain'],'split':row['split'],'input_tokens':{b:len(v) for b,v in ids.items()}}
            if row['split']=='train':
                ref=load(OUT/'private'/row['domain']/'train-references.json')[p.sample_id];teacher,student=training_targets(p,ref)
                tl=codec.tokens(teacher,c['max_target_tokens']);sl=codec.tokens(student,c['max_target_tokens']);targets.append({'sample_id':p.sample_id,'teacher_labels':tl,'student_labels':sl,'target_sha256':digest([teacher,student])});length.update(teacher_tokens=len(tl),student_tokens=len(sl))
            lengths.append(length)
        except Exception as exc:failures.append({'sample_id':p.sample_id,'reason':str(exc),'type':type(exc).__name__})
    save(OUT/'custom-public.json',public);save(OUT/'private/custom-targets.json',targets);save(OUT/'custom-preflight.json',{'lengths':lengths,'failures':failures,'truncated':False,'heldout_targets_opened':False,'expected_training':64,'prepared_training':len(targets)})
    if len(targets)!=64:raise ValueError('incomplete_training_cohort_no_silent_removal')

if __name__=='__main__':
    archive_sources('data-'+sys.argv[1]);globals()[sys.argv[1]]()
