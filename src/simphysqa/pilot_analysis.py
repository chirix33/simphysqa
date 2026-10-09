"""Private pilot parsing/family scoring and timing; no main-set model outputs."""
from pathlib import Path
from collections import Counter,defaultdict
import argparse
from jsonschema.exceptions import ValidationError
from .io import read,write,external,canonical
from .spq06 import parse_answer
from .condition_revisions import resolved_condition
from .formal_sampling import file_hash

def actual_path(pilot,cid,sid,stage):
    paths=list((pilot/'executions').glob(cid+'-stage'+str(stage)+'*/results/'+sid+'-stage'+str(stage)+'.json'))
    if len(paths)>1:raise ValueError('duplicate actual pilot item/stage')
    return paths[0] if paths else None

def analyse(pilot,output):
    pilot=external(pilot);output=external(output);plan=read(pilot/'pilot-plan.json');rows=[];tables=[]
    from .scoring import score
    from .explanation_evaluation import check_facts
    from .clarification_evaluation import inspect_stage1,check_stage2
    for original in plan['conditions']:
        cid=original['condition_id'];condition,condition_path=resolved_condition(pilot,cid);condition_rows=[]
        for item in plan['selected']:
            sid=item['sample_id'];family=item['family'];record=read(pilot/'private-records'/(sid+'.json'))
            path=actual_path(pilot,cid,sid,1)
            actual=read(path) if path else None
            reserved=list((pilot/'executions').glob(cid+'-stage1*/reservations/'+sid+'-stage1.json'))
            invalid=path is not None and (pilot/'invalid-runtime-receipts'/(path.parents[1].name+'.json')).exists()
            row={**item,'condition_id':cid,'execution_status':actual['completion_status'] if actual else 'missing',
                'raw_result_returned':actual is not None,'stage_reserved':bool(reserved),'invalid_runtime':invalid,
                'latency_seconds':actual['latency_seconds'] if actual else None,'input_tokens':actual['input_tokens'] if actual else None,
                'output_tokens':actual['output_tokens'] if actual else None,'parse_status':'unattempted','reasoning_compliance':'separate_descriptive_format_check',
                'raw_result_sha256':file_hash(path) if path else None,
                'peak_memory':{k:v for k,v in actual.items() if k in ('peak_device_memory_mib','peak_allocated_bytes','peak_reserved_bytes')} if actual else None,
                'answer_valid':False,'answer_correct':False,'human_prose_judgment':'uncollected'}
            if actual:
                row['failure_reason']=actual['failure_reason'];row['reasoning_format']=actual['reasoning_format_diagnostics']
                if invalid:row['actual_completion_status']=actual['completion_status'];row['execution_status']='invalid_runtime_cpu'
            elif reserved:row['execution_status']='interrupted_unknown_reserved'
            if actual and not invalid and actual['completion_status']=='completed':
                try:
                    response,diagnostic=parse_answer(actual['raw_output']);row['parse_status']='valid_json_suffix';row['reasoning_format'].update(diagnostic)
                    if family in ('direct','predictive','counterfactual'):
                        pred={'condition_id':cid,'sample_id':sid,'annotation_version':record['annotation_version'],'status':'abstained' if response.get('abstain') else 'completed','targets':response.get('targets',[])}
                        scored=score([record],[pred],[cid])['items'][0];row['typed_scoring']=scored;row['answer_valid']=scored['valid_targets']==scored['expected_targets'];row['answer_correct']=scored['whole_question_correct']
                    elif family=='explanation':
                        facts=check_facts(record,response);row['structured_facts']=facts;row['answer_valid']=True;row['answer_correct']=facts['factual_components_all_correct']
                    else:
                        checks=inspect_stage1(record,response);row['clarification_behavior']=checks
                        row['answer_valid']=checks['response_contract_valid'];row['answer_correct']=False
                        continuation=actual_path(pilot,cid,sid,2)
                        second=read(continuation) if continuation else None
                        row['continuation_status']=second['completion_status'] if second else 'unexecuted';row['continuation_latency_seconds']=second['latency_seconds'] if second else None
                        if second and second['completion_status']=='completed':
                            resolved,_=parse_answer(second['raw_output']);row['resolved_answer']=check_stage2(record,resolved)
                            row['answer_correct']=row['resolved_answer']['answer_correct_under_existing_typed_scorer']
                except (ValueError,TypeError,KeyError,ValidationError) as exc:row['parse_or_score_failure']=type(exc).__name__;row['answer_valid']=False
            rows.append(row);condition_rows.append(row)
        runtime_paths=[p for p in (pilot/'executions').glob(cid+'-stage*/runtime.json') if not (pilot/'invalid-runtime-receipts'/(p.parent.name+'.json')).exists()]
        loading=sum(read(p)['load_seconds'] for p in runtime_paths)
        tables.append({'condition_id':cid,'resolved_condition':condition,'resolved_condition_file_sha256':file_hash(condition_path),
            'initial_items':20,'returned_results':sum(r['raw_result_returned'] for r in condition_rows),'reserved_stages':sum(r['stage_reserved'] for r in condition_rows),
            'completion_counts':dict(Counter(r['execution_status'] for r in condition_rows)),
            'loading_seconds':loading,'qualified_runtime_receipts':[{'path':str(p),'file_sha256':file_hash(p)} for p in runtime_paths],
            'qualification':'actual_gpu_task_execution_available_with_retained_failures' if runtime_paths and any(r['execution_status']!='completed' for r in condition_rows) else 'actual_gpu_task_execution_available' if runtime_paths else 'blocked_or_not_yet_run',
            'family_timings':{f:{'measured_requests':sum(r['latency_seconds'] is not None for r in condition_rows if r['family']==f),
                'actual_gpu_inference_requests':sum(r['latency_seconds'] is not None and not r['invalid_runtime'] and 'context_capacity' not in str(r.get('failure_reason')) for r in condition_rows if r['family']==f),
                'initial_seconds':sum(r['latency_seconds'] or 0 for r in condition_rows if r['family']==f),
                'continuation_seconds':sum(r.get('continuation_latency_seconds') or 0 for r in condition_rows if r['family']==f)} for f in ('direct','predictive','counterfactual','explanation','clarification')}})
    result={'version':'SPQ06-pilot-analysis/1.0.0','items':rows,'conditions':tables,'selected_development_items':plan['selected'],
        'purpose':'execution qualification and timing; one item per cell does not establish quality or powered subgroup performance',
        'main_model_outputs':0,'human_judgments':0,'size_decision_uses_correctness':False}
    write(output/'pilot-analysis.json',result);print(canonical({'conditions':tables,'raw_results':sum(r['raw_result_returned'] for r in rows),'reserved_stages':sum(r['stage_reserved'] for r in rows),'main_outputs':0}).decode())
    return result

if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('--pilot',type=Path,required=True);p.add_argument('--output',type=Path,required=True);a=p.parse_args();analyse(a.pilot,a.output)
