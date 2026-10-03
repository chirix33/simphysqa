"""Separate validation-only evaluator. Never changes tolerances or local generation."""
from p12_common import *
from collections import defaultdict,Counter
from phi_jepa.integration.contracts import PublicProblem
from phi_jepa.typed_evaluation import evaluate_targets,grouped_summary
from phi_jepa.capabilities import capability

def summarize(records):
    targets=[t for r in records for t in r['targets']]
    numeric=defaultdict(list)
    for row in records:
        for t in row['targets']:
            if t['answer_type']!='boolean':numeric[(row['domain'],t['quantity'],t['unit'])].append(t)
    import math
    return {'grouped':grouped_summary(records,resamples=100,seed=11),
            'valid_output_questions':sum(r['typed_output_valid'] for r in records),'eligible_questions':len(records),
            'eligible_targets':len(targets),'supported_targets':sum(t['status']=='valid' for t in targets),
            'supported_target_coverage':sum(t['status']=='valid' for t in targets)/len(targets) if targets else None,
            'boolean_accuracy_all_eligible':sum(t['success'] for t in targets if t['answer_type']=='boolean')/sum(t['answer_type']=='boolean' for t in targets) if any(t['answer_type']=='boolean' for t in targets) else None,
            'unsupported_targets':sum(t['status']=='unsupported' for t in targets),
            'failure_reasons':dict(Counter(r.get('generation_failure') for r in records if r.get('generation_failure'))),
            'numeric':[{ 'domain':k[0],'quantity':k[1],'unit':k[2],'eligible':len(v),'valid':sum(t['status']=='valid' for t in v),
                        'rmse_valid_only':math.sqrt(sum(t['error']**2 for t in v if t['status']=='valid')/sum(t['status']=='valid' for t in v)) if any(t['status']=='valid' for t in v) else None}
                       for k,v in numeric.items()]}

def main(plan_path=None):
    run_root=OUT;diagnostic=plan_path is None
    if plan_path is not None:
        proposal=load(plan_path);study_lock(proposal);run_root=Path(proposal['study_root'])
    cat=catalog();rows=load(OUT/('diagnostic-public.json' if diagnostic else 'confirmation-public.json'));refs={}
    if diagnostic and any(r['split']!='validation' for r in rows):raise ValueError('only validation diagnostics authorized')
    for domain,split in sorted({(r['domain'],r['split']) for r in rows}):
        ids={r['sample_id'] for r in rows if (r['domain'],r['split'])==(domain,split)}
        refs.update({p.sample_id:ref for p,ref,ident in cat.records(domain,split) if p.sample_id in ids})
    summaries={}
    conditions=CONFIG['models']+([] if diagnostic else [{'condition':'phi_jepa_numerical'}])
    for cfg in conditions:
        records=[];common=[];cost=[]
        for row in rows:
            sid=row['sample_id'];path=(run_root/'numerical' if cfg['condition']=='phi_jepa_numerical' else run_root/'local'/cfg['condition'])/(sid+'.json')
            value=load(path) if path.exists() else {'status':'unavailable','failure':'checkpoint_access_unavailable' if diagnostic else 'missing_output','answer':None}
            p=PublicProblem.parse(row['public']);answer=value.get('answer')
            evaluated=evaluate_targets(p,refs[sid],answer['targets'] if answer else [],method=cfg['condition'],failure=None if answer else value.get('failure',value['status']))
            specs={s['target_id']:s for s in p.input['answer_spec']}
            for t in evaluated['targets']:t['quantity']=specs[t['target_id']]['quantity']
            record={**evaluated,'domain':row['domain'],'distribution':row['distribution'],'scenario_id':row['scenario_id'],
                    'typed_output_valid':answer is not None,'generation_failure':value.get('failure')}
            records.append(record)
            keep=[t for t in record['targets'] if capability(row['domain'],specs[t['target_id']]['entity_id'],specs[t['target_id']]['quantity'])['implemented']]
            if keep:
                boolean=[t for t in keep if t['answer_type']=='boolean']
                common.append({**record,'targets':keep,'complete_success':all(t['success'] for t in keep),
                               'eligible_targets':len(keep),'valid_targets':sum(t['status']=='valid' for t in keep),
                               'boolean_eligible':len(boolean),'boolean_supported':sum(t['status']=='valid' for t in boolean),
                               'boolean_correct':sum(t['success'] for t in boolean)})
            cost.append({k:value.get(k) for k in ('sample_id','input_tokens','output_tokens','reasoning_tokens','final_answer_tokens','latency_seconds','peak_allocated_bytes','peak_reserved_bytes','EOS_terminated','token_cap_termination','time_cap_termination')})
        report={'diagnostic_only':diagnostic,'whole_task':summarize(records),'predefined_common_supported':summarize(common),
                'common_set_policy':'existing deterministic Phi readout capability by public domain/entity/quantity; stable_stack and support_lost excluded; no outcome selection',
                'records':records,'cost':cost}
        save(run_root/'evaluation'/f'{cfg["condition"]}.json',report);summaries[cfg['condition']]=report['whole_task']
    save(run_root/'evaluation/summary.json',summaries)

if __name__=='__main__':
    import argparse
    parser=argparse.ArgumentParser();parser.add_argument('--approved-plan',type=Path);args=parser.parse_args();main(args.approved_plan)
