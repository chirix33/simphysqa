"""Post-generation evaluator for only the authorized eight development questions."""
from collections import Counter,defaultdict
import json
import math
from pathlib import Path
import shutil
import statistics
import time

from p12_common import ROOT,load,save,catalog
from p12_qwen_completion_run import RUN,EXPORT,PLAN,checked
from p12_qwen_completion_prepare import CONDITIONS,settings


def percentile(values,q):
    if not values:return None
    ordered=sorted(values);x=(len(ordered)-1)*q;i=int(x)
    return ordered[i]+(ordered[min(i+1,len(ordered)-1)]-ordered[i])*(x-i)


def references(rows):
    """Parse reference values only on selected development lines; no confirmation."""
    cat=catalog();found={}
    for domain in sorted({r['domain'] for r in rows}):
        selected={r['sample_id'] for r in rows if r['domain']==domain}
        public_path=cat.verified_file(domain,'validation','inputs.jsonl')
        ref_path=cat.verified_file(domain,'validation','references.jsonl')
        with public_path.open() as public,ref_path.open() as refs:
            for line,ref_line in zip(public,refs):
                sid=json.loads(line)['sample_id']
                if sid in selected:
                    ref=json.loads(ref_line)
                    if ref['sample_id']!=sid:raise ValueError('reference alignment mismatch')
                    found[sid]=ref['reference']
    if set(found)!={r['sample_id'] for r in rows}:raise ValueError('missing development reference')
    return found


def main():
    from phi_jepa.integration.contracts import PublicProblem
    from phi_jepa.integration.readers import file_hash
    from phi_jepa.inference.readout import BINDING
    from phi_jepa.typed_evaluation import evaluate_targets
    from phi_jepa.providers.compact_answer import adapt_answer
    from p12_evaluate import summarize
    cfg,rows=checked();ledger=load(RUN/'budget.json')
    if ledger.get('finished_unix') is None:raise ValueError('generation must finish before evaluation')
    if any(r['split']!='validation' for r in rows) or len(rows)!=8:raise ValueError('exact development cohort required')
    start=time.perf_counter();refs=references(rows);summaries={};audit=[]
    for condition in (*CONDITIONS,'hold_last'):
        records=[];costs=[];repetition=[];abstentions=0;per_quantity=defaultdict(list)
        for row in rows:
            p=PublicProblem.parse(row['public']);sid=p.sample_id
            specs={s['target_id']:s for s in p.input['answer_spec']}
            hold=[]
            for s in specs.values():
                matches=[m['value'] for m in p.input['states'][-1]['measurements'] if
                    (m['entity_id'],m['name'],m['unit'],m['frame'])==(s['entity_id'],s['quantity'],s['unit'],s['frame'])]
                hold.append({**{k:s[k] for k in BINDING},'status':'supported' if len(matches)==1 else 'unsupported',
                    'value':matches[0] if len(matches)==1 else None,'reason':None if len(matches)==1 else 'no observed channel'})
            if condition=='hold_last':
                result=dict(answer={'targets':hold},status='deterministic_control',full_contract_valid=True)
            else:
                path=RUN/'round-1'/condition/(sid+'.json')
                result=load(path) if path.exists() else dict(answer=None,status='not_attempted',failure='unattempted')
                if path.exists():
                    req=load(RUN/'requests'/condition/(sid+'.json'))
                    from phi_jepa.artifacts import digest
                    if result['request_sha256']!=digest(req):raise ValueError('result request identity mismatch')
                    stream=RUN/'tokens'/condition/(sid+'.jsonl')
                    streamed=[]
                    if stream.exists():
                        for line in stream.read_text().splitlines():
                            try:streamed.extend(json.loads(line))
                            except json.JSONDecodeError:break
                    if result['status']=='success' and streamed!=result['generated_token_ids']:
                        raise ValueError('raw token archive differs from returned generation')
                    if result.get('full_contract_valid') and adapt_answer(p,result['final_text'])!=result['answer']:
                        raise ValueError('adapter replay changed predictions')
                    if result.get('raw_completion') is None:
                        # This is lossless decoding of saved IDs, not answer recovery.
                        _,tok=settings(condition)
                        from phi_jepa.providers.explicit_reasoning import separate_explicit
                        from phi_jepa.providers.local_answer import separate_output
                        ids=result.get('generated_token_ids',[])
                        parts=separate_explicit(ids,tok) if condition=='llama31_8b_cot' else separate_output(ids,tok,condition=='qwen3_8b_thinking')
                        result.update(parts,raw_completion=tok.decode(ids,skip_special_tokens=False),
                            reasoning_tokens=len(parts['reasoning_token_ids']),final_answer_tokens=len(parts['final_token_ids']))
                        save(RUN/'partial-decoded'/condition/(sid+'.json'),result)
                    audit.append(dict(condition=condition,sample_id=sid,raw_archive_matches_returned=streamed==result.get('generated_token_ids'),
                        adapter_replayed=bool(result.get('full_contract_valid')),request_sha256=result['request_sha256']))
            answer=result.get('answer');predictions=answer['targets'] if answer else []
            ev=evaluate_targets(p,refs[sid],predictions,method=condition,failure=None if answer else result.get('failure',result['status']))
            for t in ev['targets']:
                t['quantity']=specs[t['target_id']]['quantity']
                if t['answer_type']!='boolean':per_quantity[(row['domain'],t['quantity'],t['unit'])].append(t)
            ev.update(domain=row['domain'],distribution=row['distribution'],scenario_id=row['scenario_id'],
                typed_output_valid=answer is not None,generation_failure=result.get('failure'))
            records.append(ev)
            costs.append({k:v for k,v in result.items() if k not in ('identity','answer','raw_completion','reasoning','final_text','generated_token_ids','reasoning_token_ids','final_token_ids')})
            for pred in predictions:
                if pred['status']=='unsupported':abstentions+=1;continue
                s=specs[pred['target_id']];matches=[]
                for state in p.input['states']:
                    for m in state['measurements']:
                        if (m['entity_id'],m['name'],m['unit'],m['frame'])==(s['entity_id'],s['quantity'],s['unit'],s['frame']) and m['value']==pred['value']:
                            matches.append(state['timestamp'])
                h=next(t for t in hold if t['target_id']==pred['target_id'])
                repetition.append(dict(sample_id=sid,target_id=pred['target_id'],answer_type=s['answer_type'],
                    matches_any_observed=bool(matches),matching_times=matches,
                    matches_hold_last=h['status']=='supported' and h['value']==pred['value']))
        metrics=summarize(records);targets=[t for r in records for t in r['targets']]
        numeric=[t for t in targets if t['answer_type']!='boolean'];boolean=[t for t in targets if t['answer_type']=='boolean']
        latencies=[c['latency_seconds'] for c in costs if c.get('latency_seconds') is not None]
        count=lambda key:sum(bool(c.get(key)) for c in costs)
        total=lambda key:sum(c.get(key) or 0 for c in costs)
        peak=lambda key:max((c[key] for c in costs if c.get(key) is not None),default=None)
        attempts=[a for a in ledger['attempts'] if a['condition']==condition]
        summary=dict(requests_attempted=len(attempts),requests_completed=count('EOS_terminated'),
            syntax_valid=count('syntax_valid'),full_contract_valid=count('full_contract_valid'),
            complete_correct=sum(r['complete_success'] for r in records),questions=8,
            supported_targets=metrics['supported_targets'],eligible_targets=len(targets),
            supported_target_coverage=metrics['supported_target_coverage'],abstentions=abstentions,abstention_rate=abstentions/len(targets),
            numeric_correct=sum(t['success'] for t in numeric),numeric_evaluated=sum(t['status']=='valid' for t in numeric),numeric_eligible=len(numeric),
            boolean_correct=sum(t['success'] for t in boolean),boolean_evaluated=sum(t['status']=='valid' for t in boolean),boolean_eligible=len(boolean),
            numeric_exact_any_observed=sum(t['matches_any_observed'] for t in repetition if t['answer_type']!='boolean'),
            numeric_exact_hold_last=sum(t['matches_hold_last'] for t in repetition if t['answer_type']!='boolean'),
            boolean_exact_any_observed=sum(t['matches_any_observed'] for t in repetition if t['answer_type']=='boolean'),
            boolean_exact_hold_last=sum(t['matches_hold_last'] for t in repetition if t['answer_type']=='boolean'),
            repetition_supported_denominator=len(repetition),input_tokens=total('input_tokens'),output_tokens=total('output_tokens'),
            reasoning_tokens=total('reasoning_tokens'),final_tokens=total('final_answer_tokens'),
            generation_seconds=sum(latencies),latency_min=min(latencies) if latencies else None,
            latency_median=statistics.median(latencies) if latencies else None,latency_p95=percentile(latencies,.95),latency_max=max(latencies) if latencies else None,
            peak_allocated_bytes=peak('peak_allocated_bytes'),peak_reserved_bytes=peak('peak_reserved_bytes'),
            process_gpu_memory='not sampled; CUDA allocation/reservation peaks reported',
            load_setup_seconds=sum(w.get('ready_unix',w['started_unix'])-w['started_unix'] for w in ledger['workers'] if w['condition']==condition),
            constraint_compile_seconds=total('constraint_compile_seconds'),
            constraint_processing_seconds=sum(c.get('constraint_processing',{}).get('seconds',0) for c in costs),
            token_caps=count('token_cap_termination'),time_caps=count('time_cap_termination'),
            missing_boundaries=sum(c.get('separation_failure') in ('missing_thinking_end','missing_final_boundary') for c in costs),
            runtime_failures=sum(c.get('status')=='runtime_failure' for c in costs),
            failures=dict(Counter(c['failure'] for c in costs if c.get('failure'))),
            boundary_failures=dict(Counter(c['separation_failure'] for c in costs if c.get('separation_failure'))),retries=0,repairs=0)
        per=[]
        for (domain,quantity,unit),ts in per_quantity.items():
            errors=[t['error'] for t in ts if t['status']=='valid']
            per.append(dict(domain=domain,quantity=quantity,unit=unit,eligible=len(ts),evaluated=len(errors),
                mae=sum(errors)/len(errors) if errors else None,rmse=math.sqrt(sum(e*e for e in errors)/len(errors)) if errors else None))
        save(RUN/'evaluation'/(condition+'.json'),dict(summary=summary,metrics=metrics,per_quantity=per,records=records,cost=costs,repetition=repetition))
        summaries[condition]=summary
    save(RUN/'evaluation/summary.json',summaries)
    save(RUN/'evaluation/audit.json',dict(rows=audit,selected_reference_questions=8,scientific_source_sha256=cfg['source_sha256'],
        evaluation_seconds=time.perf_counter()-start,fresh_validation_run=False,confirmation_access=False))
    EXPORT.mkdir(parents=True,exist_ok=True)
    for path in RUN.rglob('*'):
        if path.is_file() and path.name!='supervisor.lock':
            dest=EXPORT/path.relative_to(RUN);dest.parent.mkdir(parents=True,exist_ok=True);shutil.copyfile(path,dest)
    save(EXPORT/'artifact-index.json',{str(p.relative_to(EXPORT)):file_hash(p) for p in EXPORT.rglob('*') if p.is_file() and p.name!='artifact-index.json'})
    print(json.dumps(summaries,indent=2))


if __name__=='__main__':main()
