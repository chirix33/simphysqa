"""Evaluator-only join; every frozen test question remains in denominators."""
from p11_common import *
from collections import defaultdict,Counter
from copy import deepcopy
import math
from phi_jepa.integration.contracts import PublicProblem
from phi_jepa.typed_evaluation import evaluate_targets,trajectory_errors
from phi_jepa.capabilities import matrix,target_coverage

def evaluate():
    import torch
    from p10_inference import load_selected
    from p10_numerical import diagnostic
    torch.set_num_threads(2);rows=load(OUT/'selected-public.json');cat=catalog();refs={}
    for domain in load(OUT/'plan.json')['cohorts']:
        path=OUT/'private'/domain/'test_id-references.json'
        if not path.exists():
            ids={r['sample_id'] for r in rows if r['domain']==domain and r['split']=='test_id'}
            save(path,{p.sample_id:ref for p,ref,ident in cat.records(domain,'test_id') if p.sample_id in ids})
        refs.update(load(path))
    provider_outputs={}
    for path in (OUT/'provider_responses').glob('*.json'):
        body=load(path)['response'];provider_outputs[body.get('id')]={'status':body.get('status'),'incomplete_details':body.get('incomplete_details'),'returned_model':body.get('model')}
    records=[];physical=[];coverage=[]
    for row in [r for r in rows if r['split']=='test_id']:
        p=PublicProblem.parse(row['public']);sid=p.sample_id;ref=refs[sid]
        conditions=[('main','Phi-JEPA',OUT/'answers/main_phi'/f'{sid}.json'),('main','gpt-5.6-sol direct',OUT/'answers/direct_llm'/f'{sid}.json')]
        if row['appendix']:
            conditions.extend([('appendix','Phi-JEPA',OUT/'answers/appendix_phi'/f'{sid}.json'),('appendix','custom Coconut',OUT/'custom/coconut/test_generations'/f'{sid}.json'),('appendix','custom CODI student',OUT/'custom/codi/test_generations'/f'{sid}.json')])
        for cohort,method,path in conditions:
            saved=load(path) if path.exists() else {'status':'not_run','reason':'generation_not_run'}
            value=saved.get('result',saved);answer=value.get('answer');status=value.get('status','not_run')
            termination=[provider_outputs.get(m.get('response_id'),{}) for m in saved.get('response_metadata',[])]
            token_cap=value.get('token_cap_termination') if 'result' in saved else any((t.get('incomplete_details') or {}).get('reason')=='max_output_tokens' for t in termination)
            result=evaluate_targets(p,ref,answer['targets'] if answer else [],method=method,failure=None if answer else value.get('reason',status))
            records.append({**result,'cohort':cohort,'domain':row['domain'],'scenario_id':row['scenario_id'],'generation_status':status,'generation_failure_reason':value.get('reason'),'typed_output_valid':answer is not None,'EOS_terminated':value.get('EOS_terminated'),'token_cap_termination':token_cap,'missing_EOS':value.get('missing_EOS'),'provider_termination':termination,'condition':'answer_generation'})
        hold=[{'timestamp':s['timestamp'],'measurements':deepcopy(p.input['states'][-1]['measurements'])} for s in ref['states']]
        for hold_cohort in ('main','appendix') if row['appendix'] else ('main',):
            physical.extend({'domain':row['domain'],'sample_id':sid,'scenario_id':row['scenario_id'],'cohort':hold_cohort,'method':'hold_last_diagnostic','mode':'autonomous',**e} for e in trajectory_errors(hold,ref['states'],mode='autonomous')['per_time_channel'])
        for cohort in ('main','appendix') if row['appendix'] else ('main',):
            run=StudyRun(row['domain'],cohort);path=run.root/'numerical/phi_jepa/forecasts'/f'{sid}.json';saved=load(path) if path.exists() else {'status':'failure','reason':'forecast_not_run'};failure=None if saved['status']=='success' else saved['reason']
            result=evaluate_targets(p,ref,saved.get('readout',[]),method='Phi-JEPA readout',failure=failure)
            records.append({**result,'cohort':cohort,'domain':row['domain'],'scenario_id':row['scenario_id'],'condition':'numerical_readout','typed_output_valid':failure is None})
            coverage.extend({'cohort':cohort,'sample_id':sid,**c} for c in target_coverage(p,saved.get('readout',[]),forecast_failure=failure))
            physical.extend({'domain':row['domain'],'sample_id':sid,'scenario_id':row['scenario_id'],'cohort':cohort,'method':'Phi-JEPA','mode':'autonomous',**e} for e in trajectory_errors(saved.get('named',{}).get('states',[]),ref['states'],mode='autonomous')['per_time_channel'])
    # Diagnostic caches are checkpoint-bound. Never select a checkpoint here.
    for cohort in ('main','appendix'):
        for domain in load(OUT/'plan.json')['cohorts']:
            run=StudyRun(domain,cohort);folder=run.root/'numerical/phi_jepa'
            if not (folder/'selected.json').exists():continue
            model,solver,job=load_selected(run,'phi_jepa');chosen=load(folder/'selected.json');selected_rows=[r for r in run.rows() if r['split']=='test_id']
            trainrows=[r for r in run.rows() if r['split']=='train'][:2];trainrefs=load(OUT/'private'/domain/'train-references.json')
            for r in trainrows+selected_rows:
                path=OUT/'evaluation/diagnostics'/cohort/domain/f"{r['sample_id']}.json"
                if path.exists() and load(path).get('checkpoint_sha256')==chosen['checkpoint']['sha256']:continue
                refdict=trainrefs if r['split']=='train' else refs
                result=diagnostic(run,model,solver,job,[r],refdict)['rows'][0];save(path,{**result,'checkpoint_sha256':chosen['checkpoint']['sha256']})
    coordinate_rows=[];group_rows=[];one_step_rows=[]
    for path in (OUT/'evaluation/diagnostics').glob('*/*/*.json'):
        record=load(path);cohort,domain=path.parts[-3:-1]
        if record['status']!='success':continue
        base={'cohort':cohort,'domain':domain,'sample_id':record['sample_id'],'scenario_id':record['scenario_id'],'split':record['split']}
        for mode in ('coordinate_one_step','coordinate_autonomous'):
            coordinate_rows.extend({**base,'mode':mode,**v} for v in record[mode]['coordinates'])
            group_rows.extend({**base,'mode':mode,'group':name,**value} for name,value in record[mode]['groups'].items())
        one_step_rows.extend({**base,**value} for value in record['physical_one_step']['per_time_channel'])
    save(OUT/'evaluation/coordinate_breakdown.json',coordinate_rows);save(OUT/'evaluation/coordinate_groups.json',group_rows);save(OUT/'evaluation/one_step_physical_by_time.json',one_step_rows)
    grouped=defaultdict(list)
    for r in records:grouped[(r['cohort'],r['domain'],r['condition'],r['method'])].append(r)
    summary=[]
    for key,vs in grouped.items():
        targets=[t for v in vs for t in v['targets']]
        summary.append(dict(zip(('cohort','domain','condition','method'),key))|{'questions':len(vs),'typed_valid_questions':sum(v.get('typed_output_valid',False) for v in vs),'complete_successes':sum(v['complete_success'] for v in vs),'requested_targets':len(targets),'valid_targets':sum(t['status']=='valid' for t in targets),'unsupported_targets':sum(t['status']=='unsupported' for t in targets),'failed_targets':sum(t['status'] not in ('valid','unsupported') for t in targets),'correct_targets':sum(t['success'] for t in targets),'numeric_eligible':sum(t['answer_type']!='boolean' for t in targets),'numeric_correct':sum(t['success'] for t in targets if t['answer_type']!='boolean'),'boolean_eligible':sum(t['answer_type']=='boolean' for t in targets),'boolean_supported':sum(t['status']=='valid' for t in targets if t['answer_type']=='boolean'),'boolean_correct':sum(t['success'] for t in targets if t['answer_type']=='boolean'),'missing_EOS':sum(v.get('missing_EOS') is True for v in vs),'token_cap_termination':sum(v.get('token_cap_termination') is True for v in vs),'failures':dict(Counter(v.get('generation_status','not_applicable') for v in vs))})
    pg=defaultdict(list)
    for e in physical:
        for window in ('full_horizon','0.20-0.60' if e['time']<=.6+1e-8 else '0.60-1.00' if e['time']<=1.+1e-8 else '1.00-2.00'):
            error_unit='rad' if e.get('error_kind')=='rad_rotation' or e['quantity']=='orientation' else e['unit']
            pg[(e['cohort'],e['domain'],e['method'],e['entity_id'],e['quantity'],e['unit'],error_unit,window)].append(e)
    physical_summary=[]
    for key,vs in pg.items():
        valid=[v['error'] for v in vs if v['status']=='valid'];physical_summary.append(dict(zip(('cohort','domain','method','entity_id','quantity','unit','error_unit','window'),key))|{'eligible':len(vs),'valid':len(valid),'rmse':math.sqrt(sum(x*x for x in valid)/len(valid)) if valid else None})
    fitting=[];by_id={r['sample_id']:r for r in rows}
    for path in (OUT/'custom').glob('*/training_generations/*/*.json'):
        saved=load(path);row=by_id[saved['sample_id']];value=saved['result'];answer=value.get('answer');ref=load(OUT/'private'/row['domain']/'train-references.json')[saved['sample_id']]
        result=evaluate_targets(PublicProblem.parse(row['public']),ref,answer['targets'] if answer else [],method=path.parts[-4],failure=None if answer else value.get('reason','generation_failure'))
        fitting.append({**result,'domain':row['domain'],'update':saved['update'],'split':'train','meaning':'fixed training-example fitting diagnostic; not held-out performance','typed_output_valid':answer is not None,'EOS_terminated':value.get('EOS_terminated'),'token_cap_termination':value.get('token_cap_termination'),'generation_status':value.get('status')})
    endpoint_groups=defaultdict(list)
    for record in records:
        specs={s['target_id']:s for s in by_id[record['sample_id']]['public']['input']['answer_spec']}
        for target in record['targets']:
            if target['answer_type']=='boolean':continue
            spec=specs[target['target_id']];unit='rad' if spec['quantity']=='orientation' else spec['unit']
            endpoint_groups[(record['cohort'],record['domain'],record['condition'],record['method'],spec['entity_id'],spec['quantity'],unit)].append(target)
    endpoints=[]
    for key,values in endpoint_groups.items():
        valid=[v['error'] for v in values if v['status']=='valid'];endpoints.append(dict(zip(('cohort','domain','condition','method','entity_id','quantity','error_unit'),key))|{'eligible':len(values),'valid':len(valid),'failed_or_unsupported':len(values)-len(valid),'correct':sum(v['success'] for v in values),'rmse_valid_subset':math.sqrt(sum(v*v for v in valid)/len(valid)) if valid else None})
    save(OUT/'evaluation/endpoint_error_summary.json',endpoints)
    save(OUT/'evaluation/training_generations.json',fitting)
    from phi_jepa.integration.readers import strict_json
    inventories=[]
    for path in (OUT/'custom').glob('*/test_generations/*.json'):
        saved=load(path);row=by_id[saved['sample_id']];expected={s['target_id'] for s in row['public']['input']['answer_spec']};value=saved['result']
        out={'sample_id':saved['sample_id'],'domain':row['domain'],'method':path.parts[-3],'official_status':value['status'],'official_reason':value.get('reason'),'expected_count':len(expected),'diagnostic_only':True,'values_scored_or_repaired':False}
        try:
            parsed=strict_json(value['text']);generated=parsed['targets']
            if not isinstance(generated,list):raise ValueError('targets_not_list')
            ids=[v.get('target_id') for v in generated if isinstance(v,dict) and isinstance(v.get('target_id'),str)];counts=Counter(ids)
            out.update(generated_count=len(generated),missing=sorted(expected-set(ids)),unexpected=sorted(set(ids)-expected),duplicates={k:v for k,v in counts.items() if v>1},malformed_identity_rows=len(generated)-len(ids))
        except Exception as exc:out['diagnostic_unavailable']=type(exc).__name__
        inventories.append(out)
    save(OUT/'evaluation/generation_inventory_diagnostics.json',inventories)
    failure_groups=Counter((r['cohort'],r['domain'],r['method'],r.get('generation_failure_reason')) for r in records if r['condition']=='answer_generation' and not r['typed_output_valid'])
    save(OUT/'evaluation/generation_failure_summary.json',[dict(zip(('cohort','domain','method','reason'),key))|{'questions':count} for key,count in failure_groups.items()])
    save(OUT/'evaluation/answers.json',records);save(OUT/'evaluation/summary.json',summary);save(OUT/'evaluation/physical_by_time.json',physical);save(OUT/'evaluation/physical_summary.json',physical_summary)
    save(OUT/'evaluation/capabilities.json',{'matrix':matrix(),'targets':coverage,'calibration':'unavailable_required_assessment_components_missing','clarification':'separate_human_reviewed_not_run','historical_boolean_restricted_control':'P10 preserved; new direct condition may attempt all components'})
    print(json.dumps({'records':len(records),'physical_rows':len(physical),'summary_groups':len(summary)}))

if __name__=='__main__':
    archive_sources('evaluation');evaluate()
