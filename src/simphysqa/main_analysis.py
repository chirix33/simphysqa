"""Offline future main analysis: accepted scorers and paired stratified bootstrap.

Never runs a model or treats explanation factual checks as prose quality.
"""
from collections import Counter,defaultdict
from pathlib import Path
from itertools import combinations
import argparse,random
from jsonschema.exceptions import ValidationError
from .io import read,write,external,canonical,digest
from .formal_sampling import file_hash
from .spq01a import verify_manifest
from .spq06 import parse_answer,ABLATION
from .heldout_scope import formal_scope

def unique_result(run,cid,label,sid,stage):
    paths=list(run.glob('jobs/'+cid+'--'+label+'--stage'+str(stage)+'--*/results/'+sid+'-stage'+str(stage)+'.json'))
    if len(paths)>1:raise ValueError('duplicate actual model item/stage')
    return (read(paths[0]),file_hash(paths[0])) if paths else (None,None)

def clarification_category(checks):
    if checks['premature_structured_answer']:return 'premature_structured_answer'
    if not checks['gap_recognition_declaration']:return 'absent_structured_clarification'
    if not checks['response_contract_valid']:return 'unsupported_clarification_contract'
    if not checks['structured_slot_matches_gap']:return 'ineffective_request_for_other_slot'
    return 'supported_recorded_reply_mechanism'

def assess(record,condition,first,second):
    from .scoring import score
    from .explanation_evaluation import check_facts
    from .clarification_evaluation import inspect_stage1,route_reply,check_stage2
    family=record['question_type'];cid=condition['condition_id']
    row={'completion_status':first['completion_status'] if first else 'missing',
        'parsing':'uncollected' if not first else 'not_completed','answer_valid':False,
        'endpoints':{'typed_correct':0} if family in ('direct','predictive','counterfactual') else
        {'structured_facts_all_correct':0} if family=='explanation' else
        {'declared_gap_recognition':0,'structured_slot_match':0,'premature_structured_answer':0,'reply_routed':0,'resolved_answer_correct':0},
        'reasoning_format':first.get('reasoning_format_diagnostics') if first else None,
        'prose_adequacy':'human_judgment_uncollected','numerical_details':None}
    if not first or first['completion_status']!='completed':return row
    try:
        response,diagnostics=parse_answer(first['raw_output']);row['parsing']='valid_json_suffix'
        row['reasoning_format']={**(row['reasoning_format'] or {}),**diagnostics}
        if family in ('direct','predictive','counterfactual'):
            scored=score([record],[{'condition_id':cid,'sample_id':record['sample_id'],
                'annotation_version':record['annotation_version'],'status':'abstained' if response.get('abstained') is True else 'completed',
                'targets':response.get('targets',[])}],[cid])['items'][0]
            row['answer_valid']=scored['valid_targets']==scored['expected_targets']
            row['endpoints']['typed_correct']=int(scored['whole_question_correct']);row['numerical_details']=scored
        elif family=='explanation':
            facts=check_facts(record,response);row['answer_valid']=True;row['structured_facts']=facts
            row['endpoints']['structured_facts_all_correct']=int(facts['factual_components_all_correct'])
        else:
            checks=inspect_stage1(record,response);route=route_reply(record,response)
            row['clarification_category']=clarification_category(checks)
            row['clarification_behavior']=checks;row['answer_valid']=checks['response_contract_valid']
            row['endpoints'].update({'declared_gap_recognition':int(checks['gap_recognition_declaration']),
                'structured_slot_match':int(checks['structured_slot_matches_gap']),
                'premature_structured_answer':int(checks['premature_structured_answer']),
                'reply_routed':int(route['status']=='recorded_reply_routed')})
            row['continuation_status']=second['completion_status'] if second else 'unexecuted'
            if route['status']=='recorded_reply_routed' and second and second['completion_status']=='completed':
                resolved,_=parse_answer(second['raw_output']);facts=check_stage2(record,resolved)
                row['resolved_answer']=facts;row['endpoints']['resolved_answer_correct']=int(facts['answer_correct_under_existing_typed_scorer'])
    except (ValueError,TypeError,KeyError,ValidationError) as exc:
        row['parse_or_scoring_failure']=type(exc).__name__;row['answer_valid']=False
    return row

def percentile(values,p):
    ordered=sorted(values);at=(len(ordered)-1)*p;lo=int(at);hi=min(lo+1,len(ordered)-1)
    return ordered[lo]+(at-lo)*(ordered[hi]-ordered[lo])

def paired_intervals(rows,replicates=10000,seed=20261009):
    """One QA per group; identical stratified group draws for every condition."""
    if replicates<=0:raise ValueError('positive bootstrap replicates required')
    groups={};byfamily=defaultdict(list)
    for row in rows:
        sid=row['sample_id'];identity=(row['group_id'],row['domain'],row['family'])
        if sid in groups and groups[sid]!=identity:raise ValueError('inconsistent item identity')
        groups[sid]=identity
    if len({v[0] for v in groups.values()})!=len(groups):raise ValueError('duplicate/cross-stratum trajectory groups')
    for sid,(group,domain,family) in groups.items():byfamily[family].append((sid,domain))
    rng=random.Random(seed);summaries=[];contrasts=[]
    for family,items in sorted(byfamily.items()):
        family_rows=[r for r in rows if r['family']==family]
        labels=sorted({(r['condition_id'],r['input_condition']) for r in family_rows})
        values={(r['condition_id'],r['input_condition'],r['sample_id']):r['endpoints'] for r in family_rows}
        if len(values)!=len(family_rows) or len(values)!=len(labels)*len(items):raise ValueError('every configured condition must retain every selected item exactly once')
        strata=defaultdict(list)
        for sid,domain in items:strata[domain].append(sid)
        if len(strata)!=4 or len({len(s) for s in strata.values()})!=1:raise ValueError('four balanced domain strata required')
        metrics=sorted(family_rows[0]['endpoints']);main=[k for k in labels if k[1]=='enriched']
        pairs=list(combinations(main,2))+[((c,'structured_only'),(c,'enriched')) for c in ABLATION if (c,'structured_only') in labels]
        distributions={(label,metric):[] for label in labels for metric in metrics}
        for _ in range(replicates):
            sampled=[rng.choices(ids,k=len(ids)) for ids in strata.values()]
            for label in labels:
                for metric in metrics:
                    point=sum(sum(values[(*label,sid)][metric] for sid in ids)/len(ids) for ids in sampled)/4
                    distributions[(label,metric)].append(point)
        for label in labels:
            for metric in metrics:
                point=sum(sum(values[(*label,sid)][metric] for sid in ids)/len(ids) for ids in strata.values())/4
                dist=distributions[(label,metric)]
                summaries.append({'condition_id':label[0],'input_condition':label[1],'family':family,'endpoint':metric,
                    'balanced_domain_mean':point,'interval_95':[percentile(dist,.025),percentile(dist,.975)],
                    'independent_qa_items':len(items),'trajectory_groups':len(items)})
        for a,b in pairs:
            for metric in metrics:
                diff=[x-y for x,y in zip(distributions[(a,metric)],distributions[(b,metric)])]
                point=sum(sum(values[(*a,sid)][metric]-values[(*b,sid)][metric] for sid in ids)/len(ids) for ids in strata.values())/4
                contrasts.append({'family':family,'endpoint':metric,'condition_a':list(a),'condition_b':list(b),
                    'difference_a_minus_b':point,'paired_interval_95':[percentile(diff,.025),percentile(diff,.975)],
                    'multiplicity':'descriptive prespecified comparisons; intervals are marginal, not simultaneous'})
    return {'summaries':summaries,'paired_comparisons':contrasts,'replicates':replicates,'seed':seed,
        'method':'paired whole-trajectory percentile bootstrap within domain/family strata; balanced domain means',
        'claims':'qualified balanced benchmark; not natural release frequency, prose quality, power or OOD'}

def analyse(run,output):
    run=external(run);output=external(output);plan=read(run/'main-run-plan.json');preparation=Path(plan['preparation'])
    verify_manifest(preparation)
    if file_hash(preparation/'manifest.json')!=plan['preparation_manifest_sha256']:raise ValueError('frozen main preparation changed')
    if not list(run.glob('jobs/*/reservations/*.json')):raise ValueError('no executed main answering stages; preparation does not produce results')
    rows=[];scope=plan['generation_candidate_scope']
    with formal_scope(scope['candidates'],scope['excluded_groups']):
        for c in plan['conditions']:
            for label in ('enriched','structured_only'):
                if label=='structured_only' and c['condition_id'] not in ABLATION:continue
                for item in plan['items']:
                    sid=item['sample_id'];record=read(preparation/item['private_record'])
                    if digest(record)!=item['record_sha256']:raise ValueError('frozen scoring record changed')
                    first,h1=unique_result(run,c['condition_id'],label,sid,1);second,h2=unique_result(run,c['condition_id'],label,sid,2)
                    row={**item,'condition_id':c['condition_id'],'input_condition':label,**assess(record,c,first,second),
                        'raw_initial_result_sha256':h1,'raw_continuation_result_sha256':h2}
                    rows.append(row)
    coverage=[{'condition_id':cid,'input_condition':label,'family':family,
        'items':len(sub),'completion_counts':dict(Counter(r['completion_status'] for r in sub)),
        'valid_answers':sum(r['answer_valid'] for r in sub)} for cid,label,family in
        sorted({(r['condition_id'],r['input_condition'],r['family']) for r in rows})
        for sub in [[r for r in rows if (r['condition_id'],r['input_condition'],r['family'])==(cid,label,family)]]]
    result={'version':'SPQ06-main-analysis/1.0.0','items':rows,'coverage':coverage,
        'uncertainty':paired_intervals(rows),'model_calls':0,'human_judgments':'uncollected',
        'numerical_error_policy':'per-target quantities/units/frames retained; no pooled cross-unit errors; failures remain in all-item denominators'}
    write(output/'main-analysis.json',result);return result

if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('--run',type=Path,required=True);p.add_argument('--output',type=Path,required=True)
    a=p.parse_args();result=analyse(a.run,a.output);print(canonical({'independent_items':len({r['sample_id'] for r in result['items']}),'scored_condition_rows':len(result['items']),'model_calls':0}).decode())
