"""Private pilot parsing/family scoring and timing; no main-set model outputs."""
from pathlib import Path
from collections import Counter,defaultdict
import argparse
from jsonschema.exceptions import ValidationError
from .io import read,write,external,canonical
from .spq06 import parse_answer

def analyse(pilot,output):
    pilot=external(pilot);output=external(output);plan=read(pilot/'pilot-plan.json');rows=[];tables=[]
    from .scoring import score
    from .explanation_evaluation import check_facts
    from .clarification_evaluation import inspect_stage1,check_stage2
    for condition in plan['conditions']:
        cid=condition['condition_id'];condition_rows=[]
        for item in plan['selected']:
            sid=item['sample_id'];family=item['family'];record=read(pilot/'private-records'/(sid+'.json'))
            path=pilot/'executions'/(cid+'-stage1')/'results'/(sid+'-stage1.json')
            actual=read(path) if path.exists() else None
            row={**item,'condition_id':cid,'execution_status':actual['completion_status'] if actual else 'missing',
                'latency_seconds':actual['latency_seconds'] if actual else None,'input_tokens':actual['input_tokens'] if actual else None,
                'output_tokens':actual['output_tokens'] if actual else None,'parse_status':'unattempted','reasoning_compliance':'separate_descriptive_format_check',
                'answer_valid':False,'answer_correct':False,'human_prose_judgment':'uncollected'}
            if actual:
                row['failure_reason']=actual['failure_reason'];row['reasoning_format']=actual['reasoning_format_diagnostics']
            if actual and actual['completion_status']=='completed':
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
                        continuation=pilot/'executions'/(cid+'-stage2')/'results'/(sid+'-stage2.json')
                        second=read(continuation) if continuation.exists() else None
                        row['continuation_status']=second['completion_status'] if second else 'unexecuted';row['continuation_latency_seconds']=second['latency_seconds'] if second else None
                        if second and second['completion_status']=='completed':
                            resolved,_=parse_answer(second['raw_output']);row['resolved_answer']=check_stage2(record,resolved)
                            row['answer_correct']=row['resolved_answer']['answer_correct_under_existing_typed_scorer']
                except (ValueError,TypeError,KeyError,ValidationError) as exc:row['parse_or_score_failure']=type(exc).__name__;row['answer_valid']=False
            rows.append(row);condition_rows.append(row)
        runtime_paths=list((pilot/'executions').glob(cid+'-stage*/runtime.json'))
        loading=sum(read(p)['load_seconds'] for p in runtime_paths)
        tables.append({'condition_id':cid,'initial_items':20,'returned_results':sum(r['execution_status']!='missing' for r in condition_rows),
            'completion_counts':dict(Counter(r['execution_status'] for r in condition_rows)),
            'loading_seconds':loading,'qualification':'actual_task_execution_available' if runtime_paths else 'blocked_or_not_yet_run',
            'family_timings':{f:{'measured_requests':sum(r['latency_seconds'] is not None for r in condition_rows if r['family']==f),
                'actual_inference_requests':sum(r['latency_seconds'] is not None and 'context_capacity' not in str(r.get('failure_reason')) for r in condition_rows if r['family']==f),
                'initial_seconds':sum(r['latency_seconds'] or 0 for r in condition_rows if r['family']==f),
                'continuation_seconds':sum(r.get('continuation_latency_seconds') or 0 for r in condition_rows if r['family']==f)} for f in ('direct','predictive','counterfactual','explanation','clarification')}})
    result={'version':'SPQ06-pilot-analysis/1.0.0','items':rows,'conditions':tables,'selected_development_items':plan['selected'],
        'purpose':'execution qualification and timing; one item per cell does not establish quality or powered subgroup performance',
        'main_model_outputs':0,'human_judgments':0,'size_decision_uses_correctness':False}
    write(output/'pilot-analysis.json',result);print(canonical({'conditions':tables,'raw_results':sum(r['execution_status']!='missing' for r in rows),'main_outputs':0}).decode())
    return result

if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('--pilot',type=Path,required=True);p.add_argument('--output',type=Path,required=True);a=p.parse_args();analyse(a.pilot,a.output)
