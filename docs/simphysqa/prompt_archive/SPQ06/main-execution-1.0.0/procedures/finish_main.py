"""Central actual-main analysis and prospective prose packets /1.0.3.

No answering, ratings, simulations or annotation. Uses unchanged accepted scorers
and paired uncertainty on the original fixed 200 groups; missing collaborator
conditions remain visible in the full plan and are excluded from Ashraf-share claims.
"""
import csv,io,json,time,sys
from collections import Counter
from pathlib import Path
from simphysqa import execution_adapter as adapter,main_allocation
from simphysqa.main_analysis import paired_intervals
from simphysqa.spq06 import parse_answer
from simphysqa.execution_adapter import read,put,sha,digest,canonical
sys.path.insert(0,'C:/Users/aashraf/.codex/visualizations/2026/10/06/01a1131b-eac2-7a31-afb4-f219a8dd6471/spq06/2026-10-09/main-src-1.0.1')
from main_run import BASE,RUN,CENTRAL,SHARDS,PACKAGE,REPO

def observed_sum(values):
    values=[v for v in values if v is not None]
    return sum(values) if values else None

def prose(records,output):
    preparation=BASE/'main-preparation-1.0.0';frozen=read(preparation/'model-prose-assessment-subset.json')
    forms=BASE/'model-prose-forms-1.0.0';assignments=read(forms/'assignments.json');codes=read(forms/'private/condition-code-map.json')
    assert assignments['subset_sha256']==sha(preparation/'model-prose-assessment-subset.json')
    identities={(a['sample_id'],a['blind_condition']):a for a in assignments['items']}
    mapping=[];available=[];missing=[]
    for item in frozen['items']:
        sid=item['sample_id']
        for cid in frozen['conditions']:
            key=adapter.stage_key(sid,cid,'enriched',1);raw=records.get(key)
            identity=identities[(sid,codes[cid])];code=identity['assessment_id']
            if raw is None:missing.append({'assessment_id':code,'sample_id':sid,'blind_condition':codes[cid],'condition_id':cid,'reason':'no canonical main response; collaborator not executed' if cid+'--enriched' not in SHARDS else 'no canonical returned main response; preserve execution status'});continue
            request=read(PACKAGE/read(PACKAGE/'execution-spec.json')['requests'][key]['path'])
            response=None;error=None
            try:response,_=parse_answer(raw['raw_output'])
            except (ValueError,TypeError) as exc:error=str(exc)
            # Task content, parsed response and actual returned words retain exact values.
            # Only model/runtime metadata and automatic scores are withheld.
            public_messages=[m for m in request['messages'] if m['role']=='user']
            packet={'assessment_id':code,'blind_condition':codes[cid],'sample_id':sid,'domain':item['domain'],'public_task_messages':public_messages,
                    'final_response':response,'completion_status':raw['completion_status'],'parser_failure':error,
                    'actual_returned_text':raw['raw_output'],'raw_response_available':bool(raw['raw_output']),'assessment_status':'uncollected',
                    'presentation':'exact actual returned text and separately parsed final object; model/runtime labels and automatic scores withheld. Judge requested explanation against supplied evidence, not nonempty reasoning. Content can incidentally reveal a reasoning mode; blinding removes metadata, not words from actual responses.'}
            record=read(preparation/item['private_record'])
            packet['source_evidence']={'public_input':record['public']['input'],'evidence_bindings':record['private']['evidence_bindings'],'comparison_evidence_pointer':record['private']['explanation_evidence'],'source':record['source']}
            put(output/'packets'/(code+'.json'),packet)
            put(output/'auditor-private'/'source-evidence'/(sid+'.json'),record) if not (output/'auditor-private'/'source-evidence'/(sid+'.json')).exists() else None
            mapping.append({'assessment_id':code,'stage_key':key,'condition_id':cid,'raw_output':raw['raw_output'],'raw_sha256':digest(raw),'private_record_sha256':item['record_sha256']})
            available.append({'assessment_id':code,'blind_condition':codes[cid],'sample_id':sid,'domain':item['domain'],'completion_status':raw['completion_status'],'parser_available':response is not None})
    put(output/'auditor-private'/'mapping.json',{'mapping':mapping,'missing_planned_responses':missing,'frozen_subset_sha256':sha(preparation/'model-prose-assessment-subset.json'),'original_condition_code_map_sha256':sha(forms/'private/condition-code-map.json')})
    # Preserve the original planned 72 rows, including uncollected missing-condition rows.
    # This keeps the existing immutable submission importer and blind identities usable.
    for name in ('assignments.json','private/condition-code-map.json','P1.csv','P2.csv'):
        target=output/name;target.parent.mkdir(parents=True,exist_ok=True)
        with target.open('xb') as f:f.write((forms/name).read_bytes())
    for reviewer in ('P1','P2'):
        form_rows=list(csv.DictReader(io.StringIO((output/(reviewer+'.csv')).read_text(encoding='utf8'))))
        assert len(form_rows)==72 and len({r['assessment_id'] for r in form_rows})==72
        assert all(r['assessor_id']==reviewer and not any(r[k] for k in ('judgment','criterion_findings','error_categories','source_locations','claim_excerpts','comments')) for r in form_rows)
    put(output/'index.json',{'frozen_unique_tasks':8,'planned_enriched_responses':72,'available_responses':available,'missing_planned_count':len(missing),'submitted_judgments':0,'annotation_audit_used_as_model_answer_study':False,'human_quality_claim':False})
    guide=(REPO/'docs/simphysqa/spq06_main_design.md').read_text(encoding='utf8').split('## Separate human model-answer prose assessment',1)[1]
    with (output/'README.md').open('x',encoding='utf8') as f:
        f.write('# Prospective model-answer prose assessment\n\nOriginal assessment IDs, blinded codes, 72-row P1/P2 forms and frozen subset are reused byte-for-byte. Forms remain blank; missing-condition rows are uncollected and have no fabricated packet. Give reviewers README, packets, index.json and their own form; keep private/ and auditor-private/ separate. Returned words and parsed final objects are preserved. Content may incidentally reveal reasoning mode; metadata blinding does not edit actual responses.\n\n## Frozen guide\n'+guide+'\n## Available actual packets\n\n')
        for item in sorted(available,key=lambda x:x['assessment_id']):
            f.write('- ['+item['assessment_id']+'](packets/'+item['assessment_id']+'.json) — '+item['sample_id']+' / '+item['blind_condition']+'\n')

def finish():
    if not (RUN/'execution-completion.json').exists() or (RUN/'QUEUE-PAUSED.json').exists():raise ValueError('main queue has not completed; preserve partial execution and do not present complete-share results')
    ledger=main_allocation.Ledger(CENTRAL/'main.sqlite');control=ledger.reserve_control('Ashraf','unchanged central main analysis, fixed denominators, uncertainty and prospective prose export',1800);start=time.monotonic()
    output=RUN/'delivery-1.0.0';output.mkdir(exist_ok=False)
    try:
        put(RUN/'analysis-procedure-freeze-1.0.3.json',{'scope':'offline central actual-main analysis','sources':adapter.files(Path(__file__).parent),'unchanged_scoring_sources':{name:sha(REPO/'src/simphysqa'/(name+'.py')) for name in ('spq06','scoring','main_analysis','explanation_evaluation','clarification_evaluation')},'frozen_prose_forms':adapter.files(BASE/'model-prose-forms-1.0.0'),'answering_calls':0})
        result=adapter.analysis_bridge(ledger,BASE/'main-run-preflight-1.0.0/main-run-plan.json',RUN/'central-analysis-1.0.0')
        rows=[r for r in result['items'] if r['condition_id']+'--'+r['input_condition'] in SHARDS]
        if len(rows)!=1600 or len({r['sample_id'] for r in rows})!=200:raise ValueError('fixed Ashraf denominators changed')
        uncertainty=paired_intervals(rows);put(output/'ashraf-fixed-denominator-analysis.json',{'scope':'Ashraf completed share only','items':rows,'uncertainty':uncertainty,'missing_collaborator_rows':600,'human_explanation_quality':'uncollected'})
        records=adapter.canonical_records(ledger);metrics=[]
        for shard in SHARDS:
            cid,label=shard.split('--');initials=[r for k,r in records.items() if k.split('|')[1:3]==[cid,label] and k.endswith('|1')];seconds=[r for k,r in records.items() if k.split('|')[1:3]==[cid,label] and k.endswith('|2')]
            chosen=[r for r in rows if r['condition_id']==cid and r['input_condition']==label]
            jobs=[p for p in (RUN/'jobs').iterdir() if read(p/'condition.json')['condition_id']==cid and read(p/'execution-context.json')['representation']==label]
            runtime=[read(p/'worker-output/runtime.json') for p in jobs if (p/'worker-output/runtime.json').exists()]
            memory=[r['device_memory'] for r in initials+seconds]
            stage_latencies=[r['latency_seconds'] for r in initials+seconds];stage_total=[r['total_stage_seconds'] for r in initials+seconds]
            process_seconds=[read(p/'process-receipt.json')['elapsed_seconds'] if (p/'process-receipt.json').exists() else None for p in jobs]
            metrics.append({'condition_id':cid,'representation':label,'primary_items':200,'initial_statuses':dict(Counter(r['completion_status'] for r in initials)),
                'continuation_statuses':dict(Counter(r['completion_status'] for r in seconds)),'initial_missing_or_invalid':200-len(initials),
                'conditional_unexecuted':40-len(seconds),'parsing':dict(Counter(r['parsing'] for r in chosen)),'answer_valid_count':sum(r['answer_valid'] for r in chosen),
                'generation_latency_seconds':observed_sum(stage_latencies),'generation_latency_unavailable':sum(v is None for v in stage_latencies),'total_stage_seconds':observed_sum(stage_total),'total_stage_unavailable':sum(v is None for v in stage_total),'adapter_process_lifecycle_seconds':observed_sum(process_seconds),'process_lifecycle_unavailable_receipts':sum(v is None for v in process_seconds),
                'loading_seconds':observed_sum(r.get('load_seconds') for r in runtime),'loading_unavailable_receipts':sum(r.get('load_seconds') is None for r in runtime),
                'input_tokens':observed_sum(r.get('input_tokens') for r in initials+seconds),'output_tokens':observed_sum(r.get('output_tokens') for r in initials+seconds),
                'token_measurement_scope':'sum of saved canonical actual stage records; missing or interrupted-without-output stages have unavailable counts, not zero; not a complete count of tokens processed by an interrupted worker',
                'missing_initial_stage_measurements':200-len(initials),'missing_initial_measurement_reason':'no canonical saved initial result; inspect preserved reservation and return failure evidence' if len(initials)<200 else None,
                'termination_categories':dict(Counter(r['termination']['category'] for r in initials+seconds)),'termination_sources':dict(Counter(r['termination']['reason_source'] for r in initials+seconds)),
                'failure_reasons':dict(Counter(r['failure_reason'] for r in initials+seconds if r.get('failure_reason'))),'clarification_categories':dict(Counter(r.get('clarification_category','not_scored_or_unavailable') for r in chosen if r['family']=='clarification')), 
                'sampled_stage_device_peak_mib':max((m['sampled_peak_mib'] for m in memory if m['sampled_peak_mib'] is not None),default=None),
                'memory_availability':dict(Counter(m['status'] for m in memory)),'memory_successful_samples':sum(m['successful_sample_count'] for m in memory),
                'memory_errors':sum(len(m['errors']) for m in memory),'runtime_receipts':[{'path':str(p/'worker-output/runtime.json'),'sha256':sha(p/'worker-output/runtime.json'),'record':read(p/'worker-output/runtime.json')} for p in jobs if (p/'worker-output/runtime.json').exists()],
                'family_endpoints':[s for s in uncertainty['summaries'] if s['condition_id']==cid and s['input_condition']==label]})
        put(output/'actual-execution-results.json',{'combinations':metrics,'canonical_stage_count':len(records),'initial_reserved':ledger.db.execute("SELECT COUNT(*) FROM stages WHERE key LIKE '%|1'").fetchone()[0],
            'continuation_reserved':ledger.db.execute("SELECT COUNT(*) FROM stages WHERE key LIKE '%|2'").fetchone()[0],'conflicts':adapter.conflicts(ledger),'invalid_returns':list(ledger.db.execute('SELECT key,reason FROM returns WHERE valid=0')),
            'calls_are_not_independent_items':True,'collaborator_complete':False,'stage_2_now_exercised':[m['condition_id']+'--'+m['representation'] for m in metrics if m['continuation_statuses']]})
        from verify_delivery import verify
        verify(RUN,PACKAGE,BASE/'main-preparation-1.0.0',output/'final-offline-verification.json')
        prose(records,RUN/'model-prose-packets-1.0.0')
        preservation=read(output/'final-offline-verification.json')
        put(output/'preservation-after.json',{'files_checked':preservation['preserved_file_count'],'main_freeze_files':preservation['main_freeze_file_count'],'historical_package_files':preservation['historical_package_file_count'],'changed':preservation['preservation_changed'],'all_preserved':not preservation['preservation_changed']})
        index=adapter.files(RUN);mappings=[]
        for path,h in index.items():
            if path.startswith(('returns/','immutable-imports/')):kind='immutable transport copy; never an additional answering call'
            elif '/worker-output/results/' in path:kind='actual executed answering response'
            elif '/worker-output/executed-requests/' in path:kind='exact actual executed answering request'
            elif '/worker-output/tokenized-prompts/' in path:kind='deterministic rendering/tokenization of executed request'
            elif path.startswith('routes/'):kind='central actual-first-response routing and recorded reply assembly'
            elif path.startswith('preflights/'):kind='executed offline metadata/artifact/render verification; zero answering calls'
            elif path.startswith('central-analysis-'):kind='canonical projection and unchanged deterministic parsing/scoring/uncertainty'
            elif path.startswith('model-prose-packets-'):kind='prospective blinded projection of actual answers; no human judgments'
            elif path.startswith('delivery-'):kind='deterministic reporting/verification/accounting'
            elif '/requests/' in path:kind='reused frozen initial or conditional actual-history request'
            else:kind='execution procedure, qualification, reservation, lifecycle or provenance evidence; inspect source contract'
            mappings.append({'path':path,'sha256':h,'procedure_class':kind})
        put(output/'per-file-procedure-index.json',{'files':mappings,'new_annotation_calls':0,'new_simulations':0,'transport_copies_are_not_independent_outputs':True})
        final_index=adapter.files(RUN)
        ledger.settle_control(control,time.monotonic()-start);put(output/'resource-accounting.json',ledger.summary())
        put(output/'remaining-shared-work-forecast.json',{'observed_ashraf_accounting':ledger.executor_used('Ashraf'),'Ashraf_remaining_seconds':ledger.remaining('Ashraf'),'collaborator_reserved_seconds':100800,'shared_remaining_seconds':172800-ledger.used(),
            'missing_collaborator_combinations':['gemma3_27b_qat_direct--enriched','gemma3_27b_qat_cot--enriched','deepseek_r1_distill_qwen32b--enriched'],
            'forecast':'No measured second-machine schedule. Collaborator requires fresh machine/package/task qualification and centrally issued disjoint reservations; no inference authorized here.',
            'historical_size_forecast_preserved':True,'selected_size':200,'shared_ceiling_seconds':172800})
        final_index['delivery-1.0.0/resource-accounting.json']=sha(output/'resource-accounting.json')
        final_index['delivery-1.0.0/remaining-shared-work-forecast.json']=sha(output/'remaining-shared-work-forecast.json')
        put(output/'file-index.json',{'files':final_index,'private_raw_evidence_external':True,'all_main_outputs_actual':True,'snapshot_excludes_this_index_file':True,'central_control_boundary':'analysis/prose/preservation/index scans complete before terminal accounting/index receipt serialization'})
        print('actual main stages',len(records),'accounting',ledger.summary(),flush=True)
    except BaseException:
        row=ledger.db.execute('SELECT actual FROM control_work WHERE id=?',(control,)).fetchone()
        if row and row[0] is None:ledger.settle_control(control,time.monotonic()-start,'unknown')
        raise
    finally:ledger.db.close()

if __name__=='__main__':finish()
