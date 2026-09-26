"""Separate evaluator/report stages. No truth is sent to deployment/providers."""
import os
import subprocess
import sys
from p10_common import *
from collections import defaultdict,Counter
from copy import deepcopy
from dataclasses import asdict
import math
import shutil
import time


def select_methods(run,job=None):
    # A recorded engineering condition, not post-hoc selection of the best
    # temporal window. Keep both factorial comparisons in the exported report.
    save(run.root/'active_methods.json',{'methods':['biasinit_conditioned_full','biasinit_constant_context_text_ode','fixed_projection_lr','constant_context_text_rnn','biasinit_no_enrichment','biasinit_no_text_conditioning'],
        'reason':'Qualify the combined full-interval/input-conditioning remedy with separately disclosed train-derived output-bias initialization. Early-only validation scores remain reported; full coverage is not claimed to be superior.',
        'initialization':'Existing numerical output bias initialized from mean supervised training derivative; remains trainable; contextual bias zero; raw loss and derivatives unchanged.',
        'controls':['raw_early','conditioned_early','raw_full','conditioned_full','biasinit_raw_early','biasinit_conditioned_early','biasinit_raw_full','biasinit_conditioned_full']})


def verify(run,job=None):
    env={**os.environ,'PYTHONPATH':str(ROOT/'src')+os.pathsep+str(ROOT/'tests')}
    command=[sys.executable,'-m','unittest','test_p10','test_p03','test_p04a','test_p04b','test_p05b','test_p06','test_p08_budget','test_clarification','-v']
    result=subprocess.run(command,cwd=ROOT,env=env,text=True,capture_output=True)
    attempt=str(time.time_ns()); folder=run.root/'verification'; folder.mkdir(exist_ok=True)
    output=result.stdout+result.stderr; (folder/f'{attempt}.log').write_text(output)
    record={'command':command,'exit_code':result.returncode,'archived_log':str((folder/f'{attempt}.log').relative_to(run.root))}
    save(folder/f'{attempt}.json',record)
    (run.root/'tests.log').write_text(output); save(run.root/'tests.json',record)
    if result.returncode: raise RuntimeError('targeted_tests_failed_see_tests.log')


def diagnostic_physical_rows(record,reference):
    """Retain every expected channel/time when a whole diagnostic fails."""
    from phi_jepa.typed_evaluation import trajectory_errors
    rows=[]
    for mode,kind in (('physical_one_step','recorded_input_one_step_diagnostic'),('physical_autonomous','autonomous')):
        values=record[mode] if record['status']=='success' else trajectory_errors([],reference['states'],mode=kind)
        rows.extend({'mode':mode,**value,**({'diagnostic_failure':record.get('reason','diagnostic_unavailable')} if record['status']!='success' else {})} for value in values['per_time_channel'])
    return rows


def cached_numerical_diagnostic(run,model,solver,settings,subset,refs,folder,checkpoint):
    from p10_numerical import diagnostic
    identity={'checkpoint':checkpoint,'public_inputs':digest([r['public'] for r in subset]),
        'references':digest({r['sample_id']:refs[r['sample_id']] for r in subset}),
        'solver':asdict(solver),'settings':settings,
        'sources':{name:file_hash(ROOT/name) for name in ('tools/p10_numerical.py','src/phi_jepa/typed_evaluation.py','src/phi_jepa/coordinate_diagnostics.py')}}
    manifest=folder/'identity.json'
    paths=[folder/f"{r['sample_id']}.json" for r in subset]
    if manifest.exists() and load(manifest)==identity and all(p.exists() for p in paths):
        return {'rows':[load(p) for p in paths],'cache_hit':True}
    if manifest.exists() and load(manifest)!=identity:
        old=load(manifest); comparable=deepcopy(identity)
        comparable['sources']['tools/p10_numerical.py']=old['sources']['tools/p10_numerical.py']
        previous=run.root/'sources/blobs'/old['sources']['tools/p10_numerical.py'] if run is not None else None
        if (old==comparable and previous is not None and previous.exists()
                and file_hash(previous)==old['sources']['tools/p10_numerical.py']
                and diagnostic_code_unchanged(previous.read_text(),(ROOT/'tools/p10_numerical.py').read_text())
                and all(p.exists() for p in paths)):
            save(folder/'source_compatibility'/f'{digest(identity)}.json',{'old_identity':old,'current_identity':identity,
                'proof':'AST identical except numerical training entrypoint; diagnostic code/imports/helpers unchanged',
                'new_solver_calls':0,'historical_manifest_preserved':True})
            return {'rows':[load(p) for p in paths],'cache_hit':True}
        raise ValueError('changed_diagnostic_identity_requires_separate_evidence_run')
    result=diagnostic(run,model,solver,settings,subset,refs,save_folder=folder)
    save(manifest,identity)
    return result


def diagnostic_code_unchanged(before,after):
    """Exclude only the uncalled training entrypoint, never diagnostic helpers."""
    import ast
    def projected(source):
        tree=ast.parse(source)
        tree.body=[node for node in tree.body if not (isinstance(node,(ast.FunctionDef,ast.AsyncFunctionDef)) and node.name=='numerical')]
        return ast.dump(tree,include_attributes=False)
    return projected(before)==projected(after)


def evaluate(run,job=None):
    import torch
    from p10_inference import load_selected,grid
    from phi_jepa.integration.contracts import PublicProblem
    from phi_jepa.typed_evaluation import evaluate_targets,trajectory_errors,physical_error
    from phi_jepa.inference.readout import read_targets
    from phi_jepa.capabilities import matrix,target_coverage
    torch.set_num_threads(2); rows=run.rows(); records=[]; physical=[]; coverage=[]; control_changes=[]
    refs=load(run.root/'private/train-references.json')|load(run.root/'private/validation-references.json')
    for variant in run.methods():
        folder=run.root/'numerical'/variant
        try:
            model,solver,settings=load_selected(run,variant)
        except (ValueError,RuntimeError,FileNotFoundError) as exc:
            for row in rows:
                failed={'status':'failure','reason':'selected_checkpoint_unavailable_or_invalid:'+str(exc)}
                physical.extend({'method':variant,'split':row['split'],'scenario_id':row['scenario_id'],'sample_id':row['sample_id'],**e} for e in diagnostic_physical_rows(failed,refs[row['sample_id']]))
        else:
            for split in ('train','validation'):
                subset=[r for r in rows if r['split']==split]
                result=cached_numerical_diagnostic(run,model,solver,settings,subset,refs,run.root/'evaluation/numerical'/variant/split,
                    load(folder/'selected.json')['checkpoint']['sha256'])
                for r in result['rows']:
                    physical.extend({'method':variant,'split':split,'scenario_id':r['scenario_id'],'sample_id':r['sample_id'],**e} for e in diagnostic_physical_rows(r,refs[r['sample_id']]))
        for row in rows:
            p=PublicProblem.parse(row['public']); fpath=folder/'forecasts'/f'{p.sample_id}.json'
            saved=load(fpath) if fpath.exists() else {'status':'failure','reason':'forecast_not_run'}
            failure=None if saved['status']=='success' else saved['reason']; readout=saved.get('readout',[])
            result=evaluate_targets(p,refs[p.sample_id],readout,method=variant,failure=failure)
            records.append({**result,'split':row['split'],'scenario_id':row['scenario_id'],'condition':'numerical_readout'})
            coverage.extend({'method':variant,'sample_id':p.sample_id,'split':row['split'],**r} for r in target_coverage(p,readout,forecast_failure=failure))
    for row in rows:
        p=PublicProblem.parse(row['public']); reference=refs[p.sample_id]
        measures=[m for m in p.input['states'][-1]['measurements'] if type(m['value']) is not bool]
        hold={'sample_id':p.sample_id,'source':'autonomous_numeric_forecast','states':[{'timestamp':s['timestamp'],'measurements':deepcopy(measures)} for s in reference['states']]}
        diagnostic_hold=trajectory_errors(hold['states'],reference['states'],mode='autonomous')
        physical.extend({'method':'hold_last_diagnostic','split':row['split'],'scenario_id':row['scenario_id'],'sample_id':p.sample_id,'mode':'physical_autonomous',**e} for e in diagnostic_hold['per_time_channel'])
        save(run.root/'evaluation/hold_last'/f'{p.sample_id}.json',diagnostic_hold)
        if row['split']!='validation': continue
        primary=run.methods()[0]; original_path=run.root/'numerical'/primary/'forecasts'/f'{p.sample_id}.json'
        if original_path.exists() and load(original_path)['status']=='success':
            original=load(original_path); reversed_named=deepcopy(original['named'])
            measurements=[deepcopy(s['measurements']) for s in reversed(reversed_named['states'])]
            for state,values in zip(reversed_named['states'],measurements): state['measurements']=values
            reversed_readout=read_targets(p,reversed_named)
            result=evaluate_targets(p,reference,reversed_readout,method='reversed_primary_forecast_readout')
            records.append({**result,'split':'validation','scenario_id':row['scenario_id'],'condition':'runtime_forecast_intervention'})
            normal={v['target_id']:v for v in original['readout']}; reversed_values={v['target_id']:v for v in reversed_readout}; gold={v['target_id']:v for v in reference['structured_label']}
            for spec in p.input['answer_spec']:
                if spec['answer_type']=='boolean': continue
                a=normal[spec['target_id']]; b=reversed_values[spec['target_id']]
                value={'sample_id':p.sample_id,'target_id':spec['target_id'],'quantity':spec['quantity'],'unit':spec['unit'],'original_status':a['status'],'reversed_status':b['status']}
                if a['status']==b['status']=='supported':
                    delta,kind=physical_error(a['value'],b['value'],spec['quantity']); truth=gold[spec['target_id']]['value']
                    tolerance=spec['absolute_tolerance']+spec['relative_tolerance']*(math.hypot(*truth) if isinstance(truth,list) else abs(truth))
                    value.update(physical_change=delta,error_kind=kind,tolerance=tolerance,change_over_tolerance=delta/tolerance if tolerance else None)
                control_changes.append(value)
        for method in [*run.methods(),'public_only']:
            path=run.root/'answers'/method/f'{p.sample_id}.json'
            saved=load(path) if path.exists() else {'status':'not_run','reason':'answer_generation_not_run'}
            answer=saved.get('answer'); values=answer['targets'] if answer else []
            records.append({**evaluate_targets(p,reference,values,method=method,failure=None if answer else saved.get('reason',saved['status'])),
                'split':'validation','scenario_id':row['scenario_id'],'condition':'frozen_answer_llm'})
        for short in ('coconut','codi'):
            folder=run.root/'custom'/f'{short}_broad'; selection=load(folder/'selected.json') if (folder/'selected.json').exists() else {'update':0}
            path=folder/'validation/generations'/f"{selection['update']}-{p.sample_id}.json"
            saved=load(path) if path.exists() else {}; branches=saved.get('branches',{})
            if short=='codi': branches={**branches,'hybrid':saved.get('hybrid',{})}
            for branch in (('coconut',) if short=='coconut' else ('student','teacher','hybrid')):
                value=branches.get(branch,{}); answer=value.get('answer')
                records.append({**evaluate_targets(p,reference,answer['targets'] if answer else [],method=short+'_'+branch,failure=None if answer else value.get('reason','generation_not_run')),
                    'split':'validation','scenario_id':row['scenario_id'],'condition':'custom_answer','generation_status':value.get('status','not_run'),
                    'EOS_terminated':value.get('EOS_terminated'),'token_cap_termination':value.get('token_cap_termination'),
                    'fallback_attempted':value.get('fallback_attempted',False),'fallback_used':value.get('fallback_used',False)})
    grouped=defaultdict(list)
    for r in records: grouped[(r['condition'],r['method'],r['split'])].append(r)
    summaries=[]
    for (condition,method,split),values in grouped.items():
        summaries.append({'condition':condition,'method':method,'split':split,'questions':len(values),'complete_successes':sum(v['complete_success'] for v in values),
            'eligible_targets':sum(v['eligible_targets'] for v in values),'valid_targets':sum(v['valid_targets'] for v in values),
            'boolean_eligible':sum(v['boolean_eligible'] for v in values),'boolean_supported':sum(v['boolean_supported'] for v in values),'boolean_correct':sum(v['boolean_correct'] for v in values),
            'numeric_eligible':sum(t['answer_type']!='boolean' for v in values for t in v['targets']),
            'numeric_correct':sum(t['success'] for v in values for t in v['targets'] if t['answer_type']!='boolean')})
    pg=defaultdict(list)
    for e in physical:
        for window in ('full_horizon','early' if e['time']<=.6+1e-8 else 'late'):
            pg[(e['method'],e['split'],e['mode'],e['entity_id'],e['quantity'],e['unit'],window)].append(e)
    metrics=[]
    for key,es in pg.items():
        valid=[e['error'] for e in es if e['status']=='valid']
        metrics.append(dict(zip(('method','split','mode','entity','quantity','unit','window'),key))|{'eligible':len(es),'valid':len(valid),'rmse':math.sqrt(sum(v*v for v in valid)/len(valid)) if valid else None})
    save(run.root/'evaluation/answers.json',records); save(run.root/'evaluation/summary.json',summaries)
    save(run.root/'evaluation/physical_by_time.json',physical); save(run.root/'evaluation/physical_summary.json',metrics)
    save(run.root/'evaluation/capabilities.json',{'matrix':matrix(),'requested_targets':coverage,'executed_domains':[run.c['domain']],
        'other_domains':'interfaces/rules inventoried; no performance claims without trained runs','contact_mechanism':'unsupported_not_guessed'})
    save(run.root/'evaluation/control_inventory.json',{'controls':[
        {'name':'no_assessment','effective':False,'reason':'assessment is reported separately and does not alter predictions/answers'},
        {'name':'no_fallback','effective':False,'reason':'autonomous numerical/answer fallback is inactive'},
        {'name':'public_only','effective':True,'reason':'forecast/readout evidence absent; Boolean policy differs; common numerical targets compared separately'},
        {'name':'reversed_forecast','effective':'measured_per_target','reason':'reverses named measurement sequence at fixed physical times; offline readout intervention only, not retraining or a paid answer condition'}],
        'reversed_query_changes':control_changes,'tolerances_changed':False,'original_predictions_changed':False})
    print(json.dumps({'evaluated_answer_conditions':len(records),'physical_error_rows':len(physical)}),flush=True)


def assessment(run,job=None):
    import torch
    from phi_jepa.integration.contracts import PublicProblem
    from phi_jepa.assessment.reference import ReferenceBank
    from phi_jepa.assessment.checks import physical_checks,contract_score
    from phi_jepa.assessment.fixed import combine
    primary=run.methods()[0]; folder=run.root/'numerical'/primary; selected=load(folder/'selected.json'); settings=load(folder/'job.json'); l=run.layout()
    profile=load(ROOT/'configs/assessment_p04b.json')
    asset={'prompt':load(ROOT/'docs/assets/prompts.json')['JUDGE_PROMPT'],'schema':load(ROOT/'docs/assets/judge_schema.json')}
    bundle=torch.load(folder/selected['directory']/selected['checkpoint']['file'],map_location='cpu',weights_only=True)
    projection={k:digest(v.tolist()) for k,v in bundle['state'].items() if k.startswith('projection.')}
    identity={'checkpoint_sha256':selected['checkpoint']['sha256'],'projection_sha256':digest(projection),
        'encoder_sha256':digest(settings['context_identity']),'solver_sha256':digest(run.c['solver']),'layout_sha256':l.sha256,'profile_sha256':digest(profile)}
    entries=[]; queries={}
    for row in run.rows():
        path=folder/'forecasts'/f"{row['sample_id']}.json"; saved=load(path)
        if saved['status']!='success': continue
        e=load(run.root/'embeddings/enriched'/f"{row['sample_id']}.json")
        entry={'sample_id':row['sample_id'],'scenario_id':row['scenario_id'],'split':row['split'],'domain':run.c['domain'],'origin':'autonomous_prediction',
            'layout_sha256':l.sha256,'cutoff':row['public']['input']['observation_cutoff'],'times':[v['physical_time'] for v in saved['trajectory']['predictions']],
            'trajectory':[v['values'] for v in saved['trajectory']['predictions']],'embedding':e['values'],'public_sha256':digest(row['public']['input']),'embedding_request_sha256':e['request_sha256']}
        if row['split']=='train': entries.append(entry)
        else: queries[row['sample_id']]=entry
    bank=ReferenceBank.build(identity,entries); bank_path=bank.write(run.root/'assessment/bank')
    save(run.root/'assessment/bank_identity.json',{'identity':identity,'path':str(bank_path.relative_to(run.root)),'sha256':bank.sha256})
    old_public={r['sample_id']:r['public'] for r in load(run.old/'selected-public.json')} if (run.old/'selected-public.json').exists() else {}
    for row in run.rows():
        if row['split']!='validation': continue
        sid=row['sample_id']; p=PublicProblem.parse(row['public']); saved=load(folder/'forecasts'/f'{sid}.json')
        if saved['status']!='success': save(run.root/'assessment'/f'{sid}.json',{'status':'failure','reason':'forecast_failure'}); continue
        judged={'status':'unavailable','score':None,'reason':'judge_not_run'}; prior=run.old/'assessment'/f'{sid}.json'; reuse=None
        if prior.exists() and old_public.get(sid)==row['public']:
            previous=load(prior)['assessment']
            if previous['identity']['judge_asset_sha256']==digest(asset):
                judged=previous['components']['semantic_v1']; reuse={'source_sha256':file_hash(prior),'reason':'identical_public_input_unchanged_V1_scope','asset_sha256':digest(asset)}
        ident={**identity,'bank_sha256':bank.sha256,'judge_asset_sha256':digest(asset)}
        result=combine(bank.assess(queries[sid],l,identity=identity),contract_score(p,saved['named'],p.input['controller'].get('constraints',[])),judged,profile=profile,identity=ident)
        save(run.root/'assessment'/f'{sid}.json',{'assessment':result,'judge_cache_reuse':reuse,'physical_checks':physical_checks(p,saved['named'],profile['physical_checks'])})
    calibrate(run)


def calibrate(run,job=None):
    from phi_jepa.assessment.fixed import calibrate as fit_calibration
    profile=load(ROOT/'configs/assessment_p04b.json'); inventory=load(run.root/'sealed_inventory.json')['domains'][run.c['domain']]['calibration']
    available=[]; missing=[]
    for sid in inventory['sample_ids']:
        path=run.root/'assessment/calibration'/f'{sid}.json'
        if not path.exists(): missing.append(sid); continue
        record=load(path)
        if record.get('assessment',{}).get('status')!='complete': missing.append(sid)
        else: available.append(record)
    if missing or not available:
        save(run.root/'assessment/calibration.json',{'status':'uncalibrated','threshold':None,'reason':'required_complete_assessment_components_unavailable',
            'prepared_scenario_ids':inventory['scenario_ids'],'missing_complete_records':len(missing),'required_contract_evidence':'No immutable typed public constraint declarations; answer thresholds are not constraints.'})
        return
    ident=available[0]['assessment']['identity']; selected=[r['scenario_id'] for r in run.rows() if r['split']=='validation']
    result=fit_calibration(available,assessment_identity=ident,profile_sha256=digest(profile),policy=profile['calibration'],selection_scenarios=selected)
    save(run.root/'assessment/calibration.json',result)


def answers(run,job=None,rows=None):
    from phi_jepa.integration.contracts import PublicProblem
    from phi_jepa.providers.openai_answer import OpenAIAnswer
    from phi_jepa.providers.credentials import load_openai_key
    from phi_jepa.providers.cache import FrozenOutputCache
    from phi_jepa.inference.readout import target_result
    if not run.c['provider_enabled']: raise ValueError('provider_disabled')
    # Local qualification is a prerequisite, not a desired-outcome acceptance gate.
    if not (run.root/'evaluation/summary.json').exists(): raise ValueError('complete_local_evaluation_before_paid_answers')
    config={**load(ROOT/'configs/baselines_p05b.json')['answer_profile'],'max_attempts_per_request':1}
    original_config=load(ROOT/'configs/baselines_p05b.json')['answer_profile']; asset=load(ROOT/'docs/assets/p04a_answer_v1.json')
    for row in rows if rows is not None else [r for r in run.rows() if r['split']=='validation']:
        p=PublicProblem.parse(row['public'])
        for method in [*run.methods(),'public_only']:
            path=run.root/'answers'/method/f'{p.sample_id}.json'
            pc=original_config if method=='public_only' else config
            forecast=None
            if method=='public_only': outcomes=[target_result(t,'unsupported',reason='no_forecast_in_public_only_control',source='control') for t in p.input['answer_spec']]
            else:
                saved=load(run.root/'numerical'/method/'forecasts'/f'{p.sample_id}.json')
                if saved['status']!='success': save(path,{'status':'forecast_failure','answer':None,'reason':saved['reason']}); continue
                forecast=saved['named']; outcomes=saved['readout']
            answer_identity={'public_sha256':digest(row['public']),'forecast_sha256':digest(forecast),'readout_sha256':digest(outcomes),
                'asset_sha256':digest(asset),'provider_config_sha256':digest(pc),'condition':method,'implementation':'p04a-answer-v1'}
            if path.exists():
                if load(path).get('answer_identity')!=answer_identity: raise ValueError('stale_answer_requires_separate_evidence_run')
                continue
            # Public-only results are reused only through the original content-
            # addressed request identity, never merely by matching a sample ID.
            current_cache=FrozenOutputCache(Path(run.c['shared_answer_cache']) if run.c.get('shared_answer_cache') else run.root/'provider-cache'/f'answer-{method}-{p.sample_id}')
            if method=='public_only':
                previous_cache=FrozenOutputCache(run.old/'provider-cache'/f'answer-{method}-{p.sample_id}')
                class ReadOnlyPrevious:
                    def read(self,key):
                        value=current_cache.read(key)
                        return previous_cache.read(key) if value is None else value
                    def write(self,key,value): current_cache.write(key,value)
                cache=ReadOnlyPrevious()
            else: cache=current_cache
            ledger=run.root/'provider_ledgers'/f'answer-{method}-{p.sample_id}.json'
            obj=OpenAIAnswer(load_openai_key(ROOT/'.env'),pc,asset,cache,event_sink=lambda value:save(ledger,value),ledger=load(ledger) if ledger.exists() else None)
            obj.transport=run.b.transport(obj._http)
            try:
                answer=obj.answer(p,forecast,outcomes,condition=method)
                result={'status':'success','answer':answer,'cache_hits':obj.cache_hits}
            except Exception as exc:
                result={'status':'api_or_parse_failure','answer':None,'reason':str(exc),'type':type(exc).__name__}
            save(path,{**result,'method':method,'sample_id':p.sample_id,'forecast_sha256':digest(forecast) if forecast else None,'answer_identity':answer_identity})
            print(json.dumps({'answer':method,'sample':p.sample_id,'status':result['status'],'calls':len(run.b.read()['provider'])}),flush=True)
            run.b.check()


def export(run,job=None):
    destination=ROOT/run.c['export_directory']; destination.mkdir(parents=True,exist_ok=True)
    selected=[]
    for path in run.root.rglob('*'):
        if not path.is_file() or (path.suffix not in ('.json','.csv','.log','.png','.svg','.md') and path.name!='final-source.zip'): continue
        rel=path.relative_to(run.root)
        if any(part in ('private','provider-cache','context_cache','embedding_cache','enrichment','embeddings','public-prepared','custom-public','report-env') for part in rel.parts): continue
        if path.name in ('selected-public.json','custom-public.json'): continue
        selected.append((path,rel))
    total=sum(p.stat().st_size for p,rel in selected)
    if run.b.size()+total>run.c['caps']['artifact_bytes']: raise ValueError('export_would_exceed_new_artifact_cap')
    for path,rel in selected:
        target=destination/rel; target.parent.mkdir(parents=True,exist_ok=True); shutil.copyfile(path,target)
    files={str(rel):{'sha256':file_hash(destination/rel),'bytes':(destination/rel).stat().st_size} for path,rel in selected}
    save(destination/'manifest.json',{'files':files,'native_root':str(run.root),'aggregate_new_bytes':run.b.size(),'export_bytes':total,
        'source_commit':subprocess.check_output(['git','rev-parse','HEAD'],cwd=ROOT,text=True).strip(),'historical_runs_unchanged':True})
    print(json.dumps({'exported':len(files),'bytes':total}),flush=True)
