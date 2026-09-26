"""Public-only calibration/sealed-cohort preparation and separate evaluation.

These stages never train. Sealed outcome access requires a separately authorized
study configuration. A missing forecast/generation is an explicit failed target.
"""
from p10_common import *
from phi_jepa.integration.readers import json_lines,PublicInputReader
from phi_jepa.integration.contracts import PublicProblem

ROLES=('calibration','test_id','ood_parameter_extrapolation','ood_unseen_combination','ood_timed_event')


def cohort_rows(run,role):
    if role not in ROLES: raise ValueError('explicit_cohort_role_required')
    return load(run.root/'cohorts'/run.c['domain']/f'{role}.json')['public_rows']


def prepare_evaluation(run,job=None):
    inventory=load(run.root/'sealed_inventory.json'); cat=run.catalog()
    for domain,partitions in inventory['domains'].items():
        for role in ROLES:
            split='validation' if role=='calibration' else role; chosen=partitions[role]; ids=set(chosen['sample_ids'])
            metadata={r['sample_id']:r['metadata'] for r in json_lines(cat.verified_file(domain,split,'evaluator.jsonl')) if r['sample_id'] in ids}
            path=cat.verified_file(domain,split,'inputs.jsonl'); public=[]
            for p in PublicInputReader(path,file_hash(path)):
                if p.sample_id not in ids: continue
                m=metadata[p.sample_id]; public.append({'sample_id':p.sample_id,'scenario_id':m['base_scenario_id'],'split_group':m['split_group_id'],
                    'split':split,'role':role,'public':{'sample_id':p.sample_id,'schema_version':p.schema_version,'input':p.input}})
            if {r['sample_id'] for r in public}!=ids: raise ValueError('cohort_sample_inventory_mismatch')
            save(run.root/'cohorts'/domain/f'{role}.json',{'role':role,'partition':split,'public_rows':public,'reference_opened':False,
                'release_identity':cat.identity,'public_file_sha256':file_hash(path),'inventory_sha256':digest(chosen),'status':'public_prepared_outcomes_sealed'})


def public_cohort(run,job):
    """job is one of ROLE--enrich/encode/forecast/answers; never modifies training selection."""
    role,action=job.split('--'); rows=cohort_rows(run,role)
    if run.c.get('evaluation_authorized') is not True: raise ValueError('cohort_execution_requires_separate_study_authorization')
    original=run.rows; run.rows=lambda:rows
    try:
        if action in ('enrich','encode'):
            import p10_data; getattr(p10_data,action)(run)
        elif action=='forecast':
            from p10_inference import forecast
            forecast(run)
        elif action=='answers':
            from p10_benchmark import answers
            answers(run,rows=rows)
        else: raise ValueError('unknown_public_cohort_action')
    finally: run.rows=original


def benchmark_cohort(run,job):
    from phi_jepa.typed_evaluation import evaluate_targets,trajectory_errors
    from phi_jepa.capabilities import target_coverage
    if run.c.get('evaluation_authorized') is not True: raise ValueError('sealed_evaluation_requires_separate_study_authorization')
    rows=cohort_rows(run,job); split='validation' if job=='calibration' else job; selected={r['sample_id'] for r in rows}
    # This is the only cohort stage opening evaluator outcomes.
    refs={p.sample_id:reference for p,reference,ident in run.catalog().records(run.c['domain'],split) if p.sample_id in selected}
    scores=[]; errors=[]; coverage=[]
    for row in rows:
        p=PublicProblem.parse(row['public'])
        for method in run.methods():
            path=run.root/'numerical'/method/'forecasts'/f'{p.sample_id}.json'
            value=load(path) if path.exists() else {'status':'failure','reason':'forecast_not_run'}
            failure=None if value['status']=='success' else value['reason']; readout=value.get('readout',[])
            scores.append({**evaluate_targets(p,refs[p.sample_id],readout,method=method,failure=failure),'role':job,'condition':'numerical_readout','scenario_id':row['scenario_id']})
            coverage.extend({'method':method,'sample_id':p.sample_id,**v} for v in target_coverage(p,readout,forecast_failure=failure))
            errors.append({'method':method,'sample_id':p.sample_id,**trajectory_errors(value.get('named',{}).get('states',[]),refs[p.sample_id]['states'],mode='autonomous')})
        for method in [*run.methods(),'public_only']:
            path=run.root/'answers'/method/f'{p.sample_id}.json'; value=load(path) if path.exists() else {'status':'not_run','reason':'generation_not_run'}
            answer=value.get('answer')
            scores.append({**evaluate_targets(p,refs[p.sample_id],answer['targets'] if answer else [],method=method,failure=None if answer else value.get('reason','invalid_answer')),
                'role':job,'condition':'frozen_answer_llm','scenario_id':row['scenario_id']})
        for short in ('coconut','codi'):
            directory=run.root/'custom'/f'{short}_broad'; selection=load(directory/'selected.json') if (directory/'selected.json').exists() else {'update':0}
            path=directory/'cohorts'/job/'generations'/f"{selection['update']}-{p.sample_id}.json"; generated=load(path) if path.exists() else {}
            branches=generated.get('branches',{})|({'hybrid':generated['hybrid']} if 'hybrid' in generated else {})
            for branch in (('coconut',) if short=='coconut' else ('student','teacher','hybrid')):
                value=branches.get(branch,{}); answer=value.get('answer')
                scores.append({**evaluate_targets(p,refs[p.sample_id],answer['targets'] if answer else [],method=short+'_'+branch,failure=None if answer else value.get('reason','generation_not_run')),
                    'role':job,'condition':'custom_answer','scenario_id':row['scenario_id'],'generation_status':value.get('status','not_run'),
                    'fallback_used':value.get('fallback_used',False)})
    save(run.root/'evaluation/cohorts'/f'{job}.json',{'answer_results':scores,'physical_results':errors,'coverage':coverage,'references_opened_only_by_evaluator':True,
        'questions':len(rows),'role':job,'calibrated_ood_detection':'ineligible until all assessment components and calibration are available'})


def custom_cohort(run,job):
    guard_deployment_io()
    import torch
    from transformers import AutoTokenizer
    from phi_jepa.baselines.custom_io import TextCodec,public_text
    from phi_jepa.baselines.custom_checkpoint import load_checkpoint
    from p10_custom import generate
    if run.c.get('evaluation_authorized') is not True: raise ValueError('cohort_execution_requires_separate_study_authorization')
    role,short=job.split('--')
    if short not in ('coconut','codi'): raise ValueError('explicit_custom_method_required')
    torch.set_num_threads(2); config=load(ROOT/'configs/custom_p06.json'); rows=cohort_rows(run,role)
    tok=AutoTokenizer.from_pretrained(config['model'],revision=config['revision'],cache_dir=str(run.native/'model-cache'),local_files_only=True)
    tok.model_max_length=config['max_input_tokens']; codec=TextCodec(tok); folder=run.root/'custom'/f'{short}_broad'
    chosen=load(folder/'selected.json'); model,_,update=load_checkpoint(folder/chosen['directory'],identity=load(folder/'identity.json'),device='cuda',training=False)
    for row in rows:
        path=folder/'cohorts'/role/'generations'/f"{update}-{row['sample_id']}.json"
        if path.exists():
            if load(path).get('checkpoint_sha256')!=chosen['checkpoint']['sha256']: raise ValueError('stale_custom_generation_requires_separate_evidence_run')
            continue
        p=PublicProblem.parse(row['public']); notes=load(run.root/'enrichment'/f'{p.sample_id}.json')['notes']
        row={**row,'branch_input_ids':{branch:codec.tokens(public_text(p,notes,branch=branch),config['max_input_tokens']) for branch in ('coconut','student','teacher')}}
        generate(run,model,codec,row,folder/'cohorts'/role,update,short,chosen['checkpoint']['sha256'])


def assessment_cohort(run,job):
    from phi_jepa.assessment.reference import ReferenceBank
    from phi_jepa.assessment.checks import contract_score,physical_checks
    from phi_jepa.assessment.fixed import combine,apply_threshold
    if run.c.get('evaluation_authorized') is not True: raise ValueError('cohort_execution_requires_separate_study_authorization')
    info=load(run.root/'assessment/bank_identity.json'); bank=ReferenceBank.load(run.root/info['path'],identity=info['identity']); layout=run.layout()
    profile=load(ROOT/'configs/assessment_p04b.json'); asset={'prompt':load(ROOT/'docs/assets/prompts.json')['JUDGE_PROMPT'],'schema':load(ROOT/'docs/assets/judge_schema.json')}
    folder=run.root/'numerical'/run.methods()[0]; selected=load(folder/'selected.json')
    if selected['checkpoint']['sha256']!=info['identity']['checkpoint_sha256']: raise ValueError('rebuild_bank_for_selected_checkpoint')
    identity={**info['identity'],'bank_sha256':bank.sha256,'judge_asset_sha256':digest(asset)}
    for row in cohort_rows(run,job):
        p=PublicProblem.parse(row['public']); sid=p.sample_id; destination=run.root/'assessment'/job/f'{sid}.json'
        if destination.exists(): continue
        saved=load(folder/'forecasts'/f'{sid}.json')
        if saved['status']!='success': save(destination,{'status':'failure','reason':'forecast_failure'}); continue
        embedding=load(run.root/'embeddings/enriched'/f'{sid}.json')
        query={'sample_id':sid,'scenario_id':row['scenario_id'],'split':row['split'],'domain':run.c['domain'],'layout_sha256':layout.sha256,'origin':'autonomous_prediction',
            'cutoff':p.input['observation_cutoff'],'times':[r['physical_time'] for r in saved['trajectory']['predictions']],
            'trajectory':[r['values'] for r in saved['trajectory']['predictions']],'embedding':embedding['values']}
        judged={'status':'unavailable','score':None,'reason':'judge_not_enabled'}
        if run.c.get('assessment_judge_enabled') is True:
            from phi_jepa.providers.openai_judge import OpenAIJudge
            from phi_jepa.providers.credentials import load_openai_key
            from phi_jepa.providers.cache import FrozenOutputCache
            config={**load(ROOT/'configs/baselines_p05b.json')['answer_profile'],'max_attempts_per_request':1,'max_output_tokens':2048}
            ledger=run.root/'provider_ledgers'/f'judge-{sid}.json'
            obj=OpenAIJudge(load_openai_key(ROOT/'.env'),config,asset,FrozenOutputCache(run.root/'provider-cache'/f'judge-{sid}'),event_sink=lambda v:save(ledger,v),ledger=load(ledger) if ledger.exists() else None)
            obj.transport=run.b.transport(obj._http)
            try: judged=obj.judge(p)
            except Exception as exc: judged={'status':'unavailable','score':None,'reason':str(exc)}
        result=combine(bank.assess(query,layout,identity=info['identity']),contract_score(p,saved['named'],p.input['controller'].get('constraints',[])),judged,profile=profile,identity=identity)
        calibration=run.root/'assessment/calibration.json'
        if job!='calibration' and calibration.exists() and load(calibration).get('status')=='calibrated': result=apply_threshold(result,load(calibration))
        save(destination,{'sample_id':sid,'scenario_id':row['scenario_id'],'split':row['split'],'distribution':'id' if job in ('calibration','test_id') else job,
            'role':'calibration' if job=='calibration' else 'evaluation','assessment':result,'physical_checks':physical_checks(p,saved['named'],profile['physical_checks'])})
