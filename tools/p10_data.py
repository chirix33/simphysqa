"""Pinned dataset preparation, public context caches, sealed scenario inventories."""
from collections import defaultdict
from dataclasses import asdict
import shutil
from p10_common import *
from phi_jepa.integration.contracts import PublicProblem,enriched_context,validate_enrichment
from phi_jepa.integration.readers import json_lines,PublicInputReader


def validate_release(run,job=None):
    """Public-only all-domain layout preflight; no evaluator outcomes opened."""
    from collections import Counter
    from phi_jepa.capabilities import TARGETS
    cat=run.catalog(); reports=[]
    for domain in sorted({d for d,s in cat.partitions}):
        manifest=load(ROOT/f'docs/reviews/artifacts/P02a/{domain}.state_plus_fixed_conditioning.json')
        layout=StateLayout.from_manifest(manifest,digest(manifest))
        for split in ('train','validation'):
            path=cat.verified_file(domain,split,'inputs.jsonl'); reasons=Counter(); count=0; failures=[]; horizons=Counter(); bindings=Counter()
            for p in PublicInputReader(path,file_hash(path)):
                count+=1; horizons[max(t['end_time'] for t in p.input['answer_spec'])]+=1
                bindings.update((s['entity_id'],s['quantity'],s['answer_type'],s['unit'],s['frame']) for s in p.input['answer_spec'])
                try: layout.flatten(p.input['states'][-1],p.input)
                except ValueError as exc:
                    reasons[str(exc)]+=1
                    if len(failures)<10: failures.append({'sample_id':p.sample_id,'reason':str(exc)})
            reports.append({'domain':domain,'split':split,'questions':count,'compatible':count-sum(reasons.values()),'failure_counts':dict(reasons),
                'representative_failures':failures,'horizon_counts':dict(horizons),'layout_sha256':layout.sha256,'input_file_sha256':file_hash(path),'outcomes_opened':False,
                'requested_bindings':[dict(zip(('entity_id','quantity','answer_type','unit','frame'),key))|{'count':n,'inventoried':key[:2] in TARGETS.get(domain,[])} for key,n in sorted(bindings.items())]})
    save(run.root/'release_layout_validation.json',{'reports':reports,'status':'complete' if all(r['compatible']==r['questions'] for r in reports) else 'incompatible_layouts_present'})


def seal(run,job=None):
    cat=run.catalog(); selected=run.rows() if (run.root/'selected-public.json').exists() else []
    held={r['scenario_id'] for r in selected if r['split']=='validation'}
    inventory={}
    for domain in sorted({d for d,s in cat.partitions}):
        inventory[domain]={}; used=set()
        for split in ('train','validation','test_id','ood_parameter_extrapolation','ood_unseen_combination','ood_timed_event'):
            records=list(json_lines(cat.verified_file(domain,split,'evaluator.jsonl')))
            groups=defaultdict(list)
            for r in records: groups[r['metadata']['base_scenario_id']].append(r['sample_id'])
            if used.intersection(groups): raise ValueError('cross_partition_scenario_leakage')
            used.update(groups)
            ordered=sorted(groups,key=lambda x:digest(f"{run.c.get('selection_seed',run.c['seed'])}|{domain}|{split}|{x}"))
            if split=='train': inventory[domain][split]={'scenarios':len(groups),'questions':len(records)}; continue
            if split=='validation':
                excluded=held if domain==run.c['domain'] else set(ordered[:run.c['validation_scenarios']])
                chosen=[x for x in ordered if x not in excluded][:run.c['calibration_scenarios']]
                inventory[domain]['calibration']={'role':'validation_id_calibration','scenario_ids':chosen,'selection_excluded':sorted(excluded),
                    'sample_ids':[sid for x in chosen for sid in groups[x]],'required':run.c['calibration_scenarios'],
                    'status':'prepared' if len(chosen)==run.c['calibration_scenarios'] else 'insufficient_scenarios'}
            else:
                chosen=ordered[:run.c['sealed_scenarios_per_partition']]
                inventory[domain][split]={'status':'sealed_not_evaluated','scenario_ids':chosen,'sample_ids':[sid for x in chosen for sid in groups[x]],'reference_opened':False}
    save(run.root/'sealed_inventory.json',{'release_identity':cat.identity,'domains':inventory,'outcomes_opened':False})


def prepare(run,job=None):
    if run.c.get('questions_per_scenario') not in (1,'all'):
        raise ValueError('questions_per_scenario_must_be_one_or_all')
    if (run.root/'selection.json').exists():
        seal(run); return
    cat=run.catalog(); copied={}
    if run.c['reuse_selection']:
        for name in ('selected-public.json','selection.json','encoding-report.json','private/train-references.json','private/validation-references.json'):
            src=run.old/name; dst=run.root/name; dst.parent.mkdir(parents=True,exist_ok=True); shutil.copyfile(src,dst); copied[name]=file_hash(src)
        if load(run.root/'selection.json')['release_identity']!=cat.identity: raise ValueError('cached_selection_release_changed')
        for row in run.rows():
            p=PublicProblem.parse(row['public']); sid=p.sample_id
            if p.input['domain']!=run.c['domain']: raise ValueError('cached_domain_mismatch')
            notes=load(run.old/'enrichment'/f'{sid}.json'); validate_enrichment(p,notes)
            for name in [f'enrichment/{sid}.json',f'embeddings/enriched/{sid}.json',f'embeddings/public_base_for_offline_audit/{sid}.json']:
                src=run.old/name; dst=run.root/name; dst.parent.mkdir(parents=True,exist_ok=True); shutil.copyfile(src,dst); copied[name]=file_hash(src)
            for mode in ('enriched','public_base_for_offline_audit'):
                e=load(run.root/'embeddings'/mode/f'{sid}.json')
                text=enriched_context(p,notes,p.input['observation_cutoff']) if mode=='enriched' else p.context(p.input['observation_cutoff'])
                if e['context_sha256']!=digest(text) or len(e['values'])!=1024: raise ValueError('cache_public_context_changed')
    else:
        selected=[]
        for split,count in [('train',run.c['training_scenarios']),('validation',run.c['validation_scenarios'])]:
            metadata={r['sample_id']:r['metadata'] for r in json_lines(cat.verified_file(run.c['domain'],split,'evaluator.jsonl'))}
            candidates=defaultdict(list)
            path=cat.verified_file(run.c['domain'],split,'inputs.jsonl')
            for p in PublicInputReader(path,file_hash(path)):
                m=metadata[p.sample_id]; group=m['base_scenario_id']; horizon=max(t['end_time'] for t in p.input['answer_spec'])
                row={'public':{'sample_id':p.sample_id,'schema_version':p.schema_version,'input':p.input},'sample_id':p.sample_id,
                    'scenario_id':group,'split_group':m['split_group_id'],'split':split,'horizon':horizon}
                candidates[group].append(row)
            chosen=sorted(candidates,key=lambda x:digest(f"{run.c.get('selection_seed',run.c['seed'])}|{run.c['domain']}|{split}|{x}"))[:count]
            if len(chosen)!=count: raise ValueError('insufficient_selected_scenarios')
            for scenario in chosen:
                ordered=sorted(candidates[scenario],key=lambda r:(r['horizon'],r['sample_id']))
                selected.extend(ordered if run.c['questions_per_scenario']=='all' else ordered[:1])
        save(run.root/'selected-public.json',selected)
        selected_ids={r['sample_id'] for r in selected}
        for split in ('train','validation'):
            refs={p.sample_id:ref for p,ref,ident in cat.records(run.c['domain'],split) if p.sample_id in selected_ids}
            save(run.root/'private'/f'{split}-references.json',refs)
        save(run.root/'selection.json',{'release_identity':cat.identity,'rows':[{k:v for k,v in r.items() if k!='public'} for r in selected]})
    rows=run.rows(); train={r['scenario_id'] for r in rows if r['split']=='train'}; val={r['scenario_id'] for r in rows if r['split']=='validation'}
    if train&val or (len(train),len(val))!=(run.c['training_scenarios'],run.c['validation_scenarios']): raise ValueError('scenario_selection_mismatch')
    for r in rows: run.layout().flatten(r['public']['input']['states'][-1],r['public']['input'])
    save(run.root/'preparation.json',{'status':'complete','reused_files':copied,'new_provider_calls':0,'validation_scenarios_excluded':True,
        'source_selection_preserved':run.c['reuse_selection'],'release_identity':cat.identity})
    seal(run)
    print(json.dumps({'prepared':len(rows),'cache_files_reused':len(copied)}),flush=True)


def enrich(run,job=None):
    from phi_jepa.providers.openai_enrichment import OpenAIEnrichment
    from phi_jepa.providers.credentials import load_openai_key
    from phi_jepa.providers.cache import FrozenOutputCache
    c=load(ROOT/'configs/model_context_p02b.json'); asset=load(ROOT/c['enrichment_asset'])
    for row in run.rows():
        path=run.root/'enrichment'/f"{row['sample_id']}.json"
        if path.exists(): continue
        p=PublicProblem.parse(row['public'])
        for source in run.c.get('context_source_roots',[]):
            prior=Path(source)/'enrichment'/f'{p.sample_id}.json'
            if not prior.exists(): continue
            notes=load(prior)
            try: validate_enrichment(p,notes)
            except ValueError: continue
            save(path,notes); break
        if path.exists(): continue
        if not run.c['provider_enabled']: raise ValueError('provider_disabled')
        pc={**c['enrichment_provider'],'max_attempts_per_request':1}
        ledger=run.root/'provider_ledgers'/f'enrich-{p.sample_id}.json'
        obj=OpenAIEnrichment(load_openai_key(ROOT/'.env'),pc,asset,FrozenOutputCache(Path(run.c.get('shared_context_cache',str(run.root/'context_cache')))),event_sink=lambda x:save(ledger,x),ledger=load(ledger) if ledger.exists() else None)
        obj.transport=run.b.transport(obj._http); save(path,obj.enrich(p,p.input['observation_cutoff']))


def encode(run,job=None):
    from phi_jepa.providers.qwen import QwenEncoder
    from phi_jepa.providers.context import ContextEncoder
    from phi_jepa.providers.cache import FrozenOutputCache
    c=load(ROOT/'configs/model_context_p02b.json')
    backend=None
    for row in run.rows():
        p=PublicProblem.parse(row['public'])
        for mode in ('enriched','public_base_for_offline_audit'):
            path=run.root/'embeddings'/mode/f'{p.sample_id}.json'
            if path.exists(): continue
            notes=load(run.root/'enrichment'/f'{p.sample_id}.json') if mode=='enriched' else None
            text=enriched_context(p,notes,p.input['observation_cutoff']) if notes is not None else p.context(p.input['observation_cutoff'])
            for source in run.c.get('context_source_roots',[]):
                prior=Path(source)/'embeddings'/mode/f'{p.sample_id}.json'; report=Path(source)/'encoding-report.json'
                if not prior.exists() or not report.exists(): continue
                settings=load(report)['settings']; value=load(prior)
                if any(settings.get(k)!=c['encoder'][k] for k in ('model','model_revision','tokenizer_revision','pooling','max_length','precision','normalization','embedding_width')): continue
                if value['context_sha256']!=digest(text): continue
                save(path,value); save(run.root/'encoding-report.json',{'settings':settings,'reused_from':str(report),'source_sha256':file_hash(report)}); break
            if path.exists(): continue
            if backend is None:
                backend=QwenEncoder(str(run.native/'model-cache'),runtime_versions=c['encoder']['runtime_versions']); enc=ContextEncoder(backend,FrozenOutputCache(Path(run.c.get('shared_embedding_cache',str(run.root/'embedding_cache')))))
            value=enc.encode(p,p.input['observation_cutoff'],mode=mode,enrichment=load(run.root/'enrichment'/f'{p.sample_id}.json') if mode=='enriched' else None)
            save(path,asdict(value)); run.b.check()
    if backend is not None: save(run.root/'encoding-report.json',{'settings':asdict(backend.settings),'coverage':enc.coverage})


def custom_prepare(run,job=None):
    from transformers import AutoTokenizer
    from phi_jepa.baselines.custom_io import TextCodec,public_text,training_targets,FORMAT
    c=load(ROOT/'configs/custom_p06.json'); tok=AutoTokenizer.from_pretrained(c['model'],revision=c['revision'],cache_dir=str(run.native/'model-cache'),local_files_only=True)
    tok.model_max_length=c['max_input_tokens']; codec=TextCodec(tok); refs=load(run.root/'private/train-references.json')
    # Validation labels are for checkpoint-selection loss/evaluation only, stored
    # privately and never consumed by custom_forecast.
    valrefs=load(run.root/'private/validation-references.json'); public=[]; targets=[]; lengths=[]
    for row in run.rows():
        p=PublicProblem.parse(row['public']); notes=load(run.root/'enrichment'/f'{p.sample_id}.json')['notes']; ids={}
        for branch in ('coconut','teacher','student'):
            ids[branch]=codec.tokens(public_text(p,notes,branch=branch),c['max_input_tokens'])
        public.append({**row,'branch_input_ids':ids,'instruction_version':'p10-branch-exact-target-inventory-v1'})
        ref=(refs if row['split']=='train' else valrefs)[p.sample_id]; teacher,student=training_targets(p,ref)
        tl=codec.tokens(teacher,c['max_target_tokens']); sl=codec.tokens(student,c['max_target_tokens'])
        targets.append({'sample_id':p.sample_id,'split':row['split'],'teacher_labels':tl,'student_labels':sl,'target_sha256':digest([teacher,student])})
        lengths.append({'sample_id':p.sample_id,'input_tokens':{b:len(v) for b,v in ids.items()},'teacher_tokens':len(tl),'student_tokens':len(sl),'roundtrip_exact':True})
    save(run.root/'custom-public.json',public); save(run.root/'private/custom-targets.json',targets)
    save(run.root/'custom-preflight.json',{'format':FORMAT,'lengths':lengths,'truncated':False,'instruction_version':'p10-branch-exact-target-inventory-v1'})
