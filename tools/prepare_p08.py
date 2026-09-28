"""Explicit P08 selection, provider and encoding boundaries; no dataset generation."""
import argparse
from collections import defaultdict
from dataclasses import asdict
import time
from p08_common import *
from phi_jepa.integration.contracts import PublicProblem
from phi_jepa.integration.readers import PublicInputReader, json_lines


def selection():
    if (RUN/'selection.json').exists(): raise FileExistsError('selection already frozen')
    RUN.mkdir(parents=True,exist_ok=True); b=budget()
    with b.operation('freeze_selection','cpu'):
        cat=catalog(); selected=[]; all_training_groups=set()
        for split,count in [('train',32),('validation',8)]:
            metas=list(json_lines(cat.verified_file(CONFIG['domain'],split,'evaluator.jsonl')))
            metadata={r['sample_id']:r['metadata'] for r in metas}
            path=cat.verified_file(CONFIG['domain'],split,'inputs.jsonl'); groups=defaultdict(list)
            for p in PublicInputReader(path,file_hash(path)):
                m=metadata[p.sample_id]; group=m['split_group_id']
                if split=='train': all_training_groups.add(group)
                groups[group].append({'sample_id':p.sample_id,'scenario_id':m['base_scenario_id'],'split_group':group,'split':split,
                    'horizon':max(s['end_time'] for s in p.input['answer_spec']), 'public':{'sample_id':p.sample_id,'schema_version':p.schema_version,'input':p.input}})
            order=sorted(groups,key=lambda group:digest(f"11|{split}|{group}"))
            if split=='train': order=[CONFIG['diagnostic_scenario']]+[x for x in order if x!=CONFIG['diagnostic_scenario']]
            for group in order[:count]:
                row=min(groups[group],key=lambda r:(r['horizon'],r['sample_id']))
                if group==CONFIG['diagnostic_scenario']: row=next(r for r in groups[group] if r['sample_id']==CONFIG['diagnostic_sample'])
                layout().flatten(row['public']['input']['states'][-1],row['public']['input'])
                selected.append(row)
        assert len({r['scenario_id'] for r in selected})==40
        assert not all_training_groups.intersection(r['split_group'] for r in selected if r['split']=='validation')
        save(RUN/'selected-public.json',selected)
        save(RUN/'selection.json',{'config':CONFIG,'release_identity':cat.identity,'selection_rule':CONFIG['selection'],
            'rows':[{k:v for k,v in r.items() if k!='public'} for r in selected], 'entire_validation_scenarios_absent_from_all_training':True})
        # Private files are preparation/evaluator artifacts, never generation inputs.
        selected_ids={r['sample_id'] for r in selected}
        for split in ('train','validation'):
            refs={p.sample_id:ref for p,ref,identity in cat.records(CONFIG['domain'],split) if p.sample_id in selected_ids}
            save(RUN/'private'/f'{split}-references.json',refs)
        save(RUN/'config.json',CONFIG); provenance('selection')
        print(json.dumps({'selection_frozen':40,'training':32,'validation':8,'selection_sha256':file_hash(RUN/'selection.json')}),flush=True)


def enrichment():
    from phi_jepa.providers.openai_enrichment import OpenAIEnrichment
    from phi_jepa.providers.credentials import load_openai_key
    from phi_jepa.providers.cache import FrozenOutputCache
    b=budget(); provenance('enrichment'); c=load(ROOT/'configs/model_context_p02b.json')
    key=load_openai_key(ROOT/'.env'); asset=load(ROOT/c['enrichment_asset'])
    cache=ReadThroughCache(FrozenOutputCache(RUN/'enrichment-cache'),FrozenOutputCache(NATIVE/'p02b-profile/enrichment-cache'))
    for row in public_records():
        b.check(); sid=row['sample_id']; out=RUN/'enrichment'/f'{sid}.json'
        if out.exists(): continue
        p=PublicProblem.parse(row['public']); ledger=RUN/'provider-ledgers'/f'enrichment-{sid}.json'
        provider=OpenAIEnrichment(key,c['enrichment_provider'],asset,cache,event_sink=lambda value:save(ledger,value),ledger=load(ledger) if ledger.exists() else None)
        provider.transport=b.transport(provider._http)
        try:
            value=provider.enrich(p,p.input['observation_cutoff']); save(out,value)
            print(json.dumps({'enriched':sid,'cache_hits':provider.cache_hits,'attempts':len(b.read()['provider'])}),flush=True)
        except Exception as exc:
            save(RUN/'failures'/f'enrichment-{sid}.json',{'type':type(exc).__name__,'reason':str(exc)}); raise


def encoding():
    import torch
    from phi_jepa.providers.qwen import QwenEncoder
    from phi_jepa.providers.context import ContextEncoder
    from phi_jepa.providers.cache import FrozenOutputCache
    b=budget(); provenance('encoding'); c=load(ROOT/'configs/model_context_p02b.json'); torch.set_num_threads(2)
    with b.operation('Qwen_model_load','gpu',('shared_gpu',)):
        backend=QwenEncoder(str(NATIVE/'model-cache'),runtime_versions=c['encoder']['runtime_versions'])
    cache=ReadThroughCache(FrozenOutputCache(RUN/'embedding-cache'),FrozenOutputCache(NATIVE/'p02b-profile/embedding-cache'))
    encoder=ContextEncoder(backend,cache); torch.cuda.reset_peak_memory_stats()
    for row in public_records():
        p=PublicProblem.parse(row['public']); sid=p.sample_id
        for mode in ('enriched','public_base_for_offline_audit'):
            out=RUN/'embeddings'/mode/f'{sid}.json'
            if out.exists(): continue
            with b.operation('encode:'+sid+':'+mode,'gpu',('shared_gpu',)):
                e=encoder.encode(p,p.input['observation_cutoff'],mode=mode,enrichment=load(RUN/'enrichment'/f'{sid}.json') if mode=='enriched' else None)
                save(out,asdict(e)); print(json.dumps({'encoded':sid,'mode':mode,'tokens':e.token_count,'cache_hit':e.cache_hit}),flush=True)
    save(RUN/'encoding-report.json',{'coverage':encoder.coverage,'settings':asdict(backend.settings),'peak_allocated_bytes':torch.cuda.max_memory_allocated(),'peak_reserved_bytes':torch.cuda.max_memory_reserved()})


def custom_preparation():
    from transformers import AutoTokenizer
    from phi_jepa.baselines.custom_io import TextCodec,public_text,training_targets,FORMAT
    b=budget(); provenance('custom_preparation')
    with b.operation('T5_tokenization_and_target_preflight','cpu'):
        c=load(ROOT/'configs/custom_p06.json'); tok=AutoTokenizer.from_pretrained(c['model'],revision=c['revision'],cache_dir=str(NATIVE/'model-cache'),local_files_only=True)
        tok.model_max_length=c['max_input_tokens']; codec=TextCodec(tok)
        refs=load(RUN/'private/train-references.json'); public=[]; training=[]; lengths=[]
        for row in public_records():
            p=PublicProblem.parse(row['public']); notes=load(RUN/'enrichment'/f'{p.sample_id}.json')['notes']; text=public_text(p,notes)
            ids=codec.tokens(text,c['max_input_tokens']); value={**row,'input_ids':ids,'input_sha256':digest(text),'tokens':len(ids)}
            public.append(value); record={'sample_id':p.sample_id,'split':row['split'],'input_tokens':len(ids)}
            if row['split']=='train':
                teacher,student=training_targets(p,refs[p.sample_id]); tl=codec.tokens(teacher,c['max_target_tokens']); sl=codec.tokens(student,c['max_target_tokens'])
                training.append({**value,'teacher_labels':tl,'student_labels':sl,'target_sha256':digest([teacher,student])})
                record.update(teacher_tokens=len(tl),student_tokens=len(sl),teacher_eos_index=len(tl)-1,student_eos_index=len(sl)-1)
            lengths.append(record)
        save(RUN/'public-prepared.json',public); save(RUN/'private/training-prepared.json',training)
        save(RUN/'preflight.json',{'format':FORMAT,'lengths':lengths,'roundtrips_exact':True,'truncations':0,'config':c})
        print(json.dumps({'public_examples':len(public),'training_examples':len(training),'maximum_input':max(r['input_tokens'] for r in lengths)}),flush=True)


if __name__=='__main__':
    parser=argparse.ArgumentParser(); parser.add_argument('stage',choices=('selection','enrichment','encoding','custom_preparation')); args=parser.parse_args()
    globals()[args.stage]()
