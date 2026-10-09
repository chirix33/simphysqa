"""Timing-only decision: never reads parsed answers or correctness scores."""
from pathlib import Path
import argparse,math,datetime
from .io import read,write,external,canonical,digest,DOMAINS,QUESTION_TYPES
from .formal_sampling import file_hash
from .spq06 import ABLATION
from .condition_revisions import resolved_condition

def forecast(pilot,preparation,output):
    pilot=external(pilot);preparation=external(preparation);output=external(output)
    plan=read(pilot/'pilot-plan.json');manifest=read(preparation/'nested-400-manifest.json');tables=[];blockers=[]
    for base in plan['conditions']:
        cid=base['condition_id'];condition,condition_path=resolved_condition(pilot,cid);measures={};loading=[]
        runtimes=list((pilot/'executions').glob(cid+'-stage*/runtime.json'))
        if not runtimes:blockers.append(cid+': model runtime not qualified')
        for p in runtimes:loading.append(read(p)['load_seconds'])
        raw=[]
        for item in plan['selected']:
            p=pilot/'executions'/(cid+'-stage1')/'results'/(item['sample_id']+'-stage1.json')
            actual=read(p) if p.exists() else None
            did_infer=actual is not None and 'context_capacity' not in str(actual.get('failure_reason'))
            if actual is None:blockers.append(cid+': missing pilot result '+item['sample_id'])
            # A context failure gives no measured inference time. Conservatively
            # use the frozen per-call timeout for that cell; never count zero as fast.
            cost=actual['latency_seconds'] if did_infer else condition['settings']['max_seconds']
            q=pilot/'executions'/(cid+'-stage2')/'results'/(item['sample_id']+'-stage2.json')
            second=read(q) if q.exists() else None
            if item['family']=='clarification':
                continuation=second['latency_seconds'] if second and 'context_capacity' not in str(second.get('failure_reason')) else condition['settings']['max_seconds']
            else:continuation=0
            raw.append({'domain':item['domain'],'family':item['family'],'initial_seconds':cost,'initial_measured':did_infer,
                'continuation_seconds':continuation,'continuation_measured':second is not None and 'context_capacity' not in str(second.get('failure_reason')),'raw_result_sha256':file_hash(p) if p.exists() else None})
        raw_bounds=[dict(v) for v in raw]
        # Requested estimator is by condition and family. Use the largest measured
        # inference time in that family for every domain, not a zero-time capacity
        # rejection. A wholly unmeasured family retains the frozen timeout bound.
        # This is a conservative measured forecast, not a worst-case guarantee.
        for family in QUESTION_TYPES:
            measured=[v['initial_seconds'] for v in raw if v['family']==family and v['initial_measured']]
            second_measured=[v['continuation_seconds'] for v in raw if v['family']==family and v['continuation_measured']]
            for v in raw:
                if v['family']==family:
                    v['initial_seconds']=max(measured) if measured else condition['settings']['max_seconds']
                    if family=='clarification':v['continuation_seconds']=max(second_measured) if second_measured else condition['settings']['max_seconds']
                    v['forecast_basis']='largest measured same-condition/family inference; if wholly unmeasured use frozen timeout'
        per_item_sum=sum(v['initial_seconds']+v['continuation_seconds'] for v in raw)
        table={'condition_id':cid,'cell_timings':raw,'raw_cell_measurements_and_unmeasured_timeout_bounds':raw_bounds,'measured_loading_seconds':loading,'sizes':{}}
        for size in (200,400):
            n=size//20;shards=math.ceil(size/50)+math.ceil((size//5)/50)
            # Every possible continuation is budgeted, even if pilot did not route.
            load=max(loading) if loading else 600
            # Gemma's content hash check occurs before runtime load timestamp;
            # process receipts include it. Use the larger observed overhead.
            for p in (pilot/'process-reservations').glob(cid+'-stage*-result.json'):
                stage=2 if '-stage2' in p.name else 1
                consumed=sum(read(x)['latency_seconds'] for x in (pilot/'executions'/(cid+'-stage'+str(stage))/'results').glob('*.json'))
                load=max(load,max(0,read(p)['wall_seconds']-consumed))
            seconds=n*per_item_sum+shards*load
            table['sizes'][str(size)]={'initial_calls':size,'possible_continuations':size//5,'shards':shards,'load_seconds_per_shard':load,
                'without_reserve_seconds':seconds,'with_25_percent_reserve_seconds':seconds*1.25}
        tables.append(table)
    totals={}
    for size in (200,400):
        main=sum(t['sizes'][str(size)]['without_reserve_seconds'] for t in tables)
        ablation=sum(t['sizes'][str(size)]['without_reserve_seconds'] for t in tables if t['condition_id'] in ABLATION)
        totals[str(size)]={'main_seconds':main,'ablation_seconds':ablation,'total_without_reserve_hours':(main+ablation)/3600,
            'total_with_25_percent_reserve_hours':(main+ablation)*1.25/3600,'maximum_calls':5280 if size==400 else 2640}
    now=datetime.datetime.now(datetime.timezone.utc);deadline=datetime.datetime(2026,10,13,11,59,tzinfo=datetime.timezone.utc)
    core=read(preparation/'nested-200-manifest.json');decision=None;reason=[]
    if blockers:reason.append('qualification results incomplete/blocked; no final measured size decision')
    elif manifest['complete'] and totals['400']['total_with_25_percent_reserve_hours']<=48 and (deadline-now).total_seconds()>=12*3600:
        decision=400;reason.append('400 qualified; all-nine measured/conservative timing forecast fits48GPUhours and >=12h writing reserve remains')
    elif core['complete'] and totals['200']['total_with_25_percent_reserve_hours']<=48 and (deadline-now).total_seconds()>=12*3600:
        decision=200;reason.append('prespecified200core selected by runtime/preparation feasibility; no main accuracy inspected')
    else:reason.append('no ready size under frozen qualification/time/population rules; report concrete constraint')
    result={'version':'SPQ06-timing-decision/1.0.0','conditions':tables,'workloads':totals,'final_size':decision,'reason':reason,'blockers':blockers,
        'decision_utc':now.isoformat(),'submission_deadline_utc':deadline.isoformat(),'minimum_writing_reserve_hours':12,
        'main_outputs_examined':0,'pilot_correctness_read':False,'evaluation_manifest_sha256':file_hash(preparation/('nested-'+str(decision or 400)+'-manifest.json')),
        'estimator':'largest measured initial/continuation time within each condition/family, applied to all domains; wholly unmeasured family uses timeout; all possible continuations, shard loading and25%reserve',
        'caveat':'one pilot item/cell; smaller main projection not rerun on models; context rejections are retained but supply no inference timing; family timing extrapolation across those domains is an explicit feasibility inference, not a guaranteed wall bound, accuracy or achieved performance claim'}
    write(output/'runtime-forecast-and-size-decision.json',result);print(canonical({'workloads':totals,'final_size':decision,'reason':reason,'blockers':blockers}).decode());return result

if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('--pilot',type=Path,required=True);p.add_argument('--preparation',type=Path,required=True);p.add_argument('--output',type=Path,required=True)
    a=p.parse_args();forecast(a.pilot,a.preparation,a.output)
