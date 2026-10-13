"""SPQ06 serial candidate processor with separate cumulative provider/solve ceilings."""
import argparse
from copy import deepcopy
from hashlib import sha256
import json
from pathlib import Path
import subprocess
import time

from .io import ROOT, canonical, digest, external, parse, read, write
from .formal_sampling import source_record, file_hash, save_bytes
from .spq01a import retained, verify_manifest
from .job import locked
from .heldout_scope import formal_scope

LIMITS = {'initial_requests':676, 'total_attempts':1352, 'attempts_per_item':2,
          'usd_cap':320, 'wall_seconds':14400, 'total_input_tokens':18000000,
          'total_output_tokens':2768896, 'framing_token_reserve':4096}
SIM_LIMITS = {'maximum_simulation_executions':1612, 'per_execution_seconds':180,
              'total_wall_seconds':14400}
WSL_PYTHON = '/mnt/c/Users/aashraf/Desktop/Work/phi-jepa/phi-jepa/.dataset-bullet-venv/bin/python'


class CeilingReached(RuntimeError):
    pass


class GlobalProviderFailure(RuntimeError):
    pass


def linux_path(path):
    p = str(Path(path).resolve()).replace('\\','/')
    if len(p)<3 or p[1:3] != ':/':
        raise ValueError('explicit Windows absolute path required for WSL')
    return '/mnt/'+p[0].lower()+p[2:]


def settings():
    provider = read(ROOT/'configs/simphysqa/annotation_spq01.json')
    provider['version']='simphysqa-SPQ06-authorized-provider/1.0.0'
    provider['budget']=deepcopy(LIMITS)
    provider['pricing'].update(verified_date='2026-10-09',cache_write_per_million=5)
    provider['scope']='SPQ06 frozen candidates only, target400 distinct items; user additional ceilings authorized2026-10-09'
    return provider


def execution_plan(output):
    plan=read(output/'execution-plan.json')
    for path in sorted((output/'execution-plan-revisions').glob('*.json')):
        revision=read(path)
        if revision['previous_plan_sha256']!=digest(plan):raise ValueError('execution revision chain changed')
        if any(revision[k]!=plan[k] for k in ('candidates','excluded_groups','provider_config','simulation_limits','candidate_order_sha256')):
            raise ValueError('repair changed frozen design/budget')
        plan=revision
    return plan


def pair_for(candidate):
    wrapper=source_record(candidate['source'])
    row=candidate['source']; folder=Path(row['source']['path']).parent.parent
    config=read(folder/'config.json')
    scenario=next(s for s in read(folder/'partitions.json') if s['group']==row['trajectory_id'])
    sources=[parse(line) for line in Path(row['source']['path']).read_text(encoding='utf-8-sig').splitlines() if line.strip()]
    sources=[s for s in sources if s['metadata']['base_scenario_id']==row['trajectory_id']]
    if digest(config)!=wrapper['private']['metadata']['simulation']['config_sha256']:
        raise ValueError('source config hash mismatch')
    return {'pair_id':'spq06-pair-'+digest({'source':row['sample_id'],'group':row['group_id']})[:24],
            'source_wrapper':wrapper,'source_records':sources,'scenario':scenario,'config':config,
            'original_environment':read(folder/'environment.json')}


def freeze(preparation, output):
    preparation=Path(preparation);output=external(output);protocol=read(preparation/'protocol.json')
    candidates=read(preparation/'candidate-order.json')
    if digest(candidates)!=protocol['candidate_order_sha256']:raise ValueError('candidate ordering changed')
    for relative,h in protocol['source_code_schema_pins'].items():
        actual=file_hash(ROOT/relative)
        if actual!=h:
            # This exact pre-execution hash-convention fix belongs to the isolated
            # answering worker, which this generation job does not import or run.
            if not (relative=='src/simphysqa/local_pilot_worker.py'
                    and h=='27c82623e418c630d9931336681a5fadca621fdb2b387a1ff904e042c57aaf3a'
                    and actual=='177e2d041b43d0a12860dc6c75d1720aa5a01544a81afc65b96d75411cc93978'):
                raise ValueError('preparation source changed: '+relative)
    provider=settings();payloads={}
    from .annotation import payload
    for c in candidates:
        saved=read(preparation/'prepared-annotation-requests'/(c['candidate_id']+'.json'))
        if saved!=payload(source_record(c['source']),provider):raise ValueError('authorized payload does not match execution')
        payloads[c['candidate_id']]=digest(saved)
    producer=subprocess.check_output(['git','rev-parse','HEAD'],cwd=ROOT,text=True).strip()
    pins={p.relative_to(ROOT).as_posix():file_hash(p) for folder in ('src/simphysqa','src/phi_jepa/simulation')
          for p in (ROOT/folder).rglob('*') if p.suffix in ('.py','.json')}
    for rel in ('dataset.schema.json','configs/simphysqa/development_exclusions.json','configs/simphysqa/annotation_spq01.json'):
        pins[rel]=file_hash(ROOT/rel)
    plan={'version':'SPQ06-authorized-execution/1.0.0','producer_commit':producer,
        'preparation_protocol_sha256':file_hash(preparation/'protocol.json'),'candidate_order_sha256':digest(candidates),
        'candidates':candidates,'excluded_groups':protocol['excluded_groups'],'provider_config':provider,
        'simulation_limits':SIM_LIMITS,'scientific_source_pins':pins,'prepared_payload_sha256':payloads,
        'target_items':400,'nested_core_items':200,'preflight_estimates':protocol['estimates'],
        'authorization':{'date':'2026-10-09','user_verbatim':'Authorize these SPQ06 ceilings and annotation payloads',
          'proposal_sha256':file_hash(preparation.parent/'generation-budget-proposal-1.0.0.json'),
          'endpoint':'https://api.openai.com/v1/responses','scope':'SPQ06 annotation and private verification only; no main answering'},
        'pricing_evidence':{'checked':'2026-10-09','sources':provider['pricing']['verified_sources']},
        'procedure_scope':'Unchanged family scientific checks; only final historical development-membership guard superseded for exact frozen excluded-free held-out sources',
        'wall_accounting':'cumulative annotation attempts including validation; unknown retains120s; cumulative WSL workers and static compilations; unknown retains full reservation',
        'preparation_code_overlay':{'src/simphysqa/local_pilot_worker.py':{'commit':'14d491d','reason':'canonical JSON template hash convention; isolated answering code unused by generation'}},
        'simulator_python':WSL_PYTHON,'credential_reference_only':True,'main_answering_enabled':False}
    retained(output/'execution-plan.json',plan)
    print(canonical({'preflight':{'plan_sha256':digest(plan),'producer_commit':producer,'model':provider['model'],
      'max_output_tokens':provider['max_output_tokens'],'timeout_seconds':provider['timeout_seconds'],
      'annotation_limits':LIMITS,'simulation_limits':SIM_LIMITS,'pricing_date':'2026-10-09',
      'estimates':protocol['estimates'],'new_executions':0,'main_answering_enabled':False}}).decode(),flush=True)
    return plan


def annotation_ledger(output):
    result=[]
    for path in sorted((output/'annotation/attempts').glob('*.json')):
        attempt=read(path); response=output/'annotation/responses'/path.name
        if response.exists():
            value=read(response)
            result.append({**attempt,**value['accounting'],'wall_seconds':value['wall_seconds']})
        else:
            result.append({**attempt,'charged_upper_bound_usd':attempt['reservation']['usd'],
                           'recorded_cost_usd':None,'wall_seconds':120,'status':'interrupted_unknown_reserved'})
    return result


def admit_annotation(history, bound, initial, budget=LIMITS):
    if (len(history)>=budget['total_attempts'] or (initial and sum(a['initial_request'] for a in history)>=budget['initial_requests'])
        or sum(a['charged_upper_bound_usd'] for a in history)+bound['usd']>budget['usd_cap']
        or sum(a['reservation']['input_token_upper_bound'] for a in history)+bound['input_token_upper_bound']>budget['total_input_tokens']
        or sum(a['reservation']['output_token_limit'] for a in history)+bound['output_token_limit']>budget['total_output_tokens']
        or sum(a['wall_seconds'] for a in history)+120>budget['wall_seconds']):
        raise CeilingReached('annotation cumulative ceiling reached; no enlargement')


def annotate(wrapper, candidate, output, config):
    from .annotation import payload,reservation,http_call,load_key,decode,usage_cost,validate_generated,ProviderError,PROMPT,PROMPT_VERSION,schema
    from .dataset import attach_annotation,VERSION
    path=output/'annotation/items'/(candidate['candidate_id']+'.json')
    def completed_item(annotation, raw):
        own=[a for a in annotation_ledger(output) if a['candidate_id']==candidate['candidate_id']]
        provenance={'status':'generated_unreviewed','model_identity':raw['model'],'prompt_version':PROMPT_VERSION,
                    'schema_version':VERSION,'generation_settings':{k:v for k,v in config.items() if k!='credential_reference_file'},
                    'validation_failures':[read(output/'annotation/responses'/(str(a['attempt_number']).zfill(4)+'.json'))['failure']
                                           if (output/'annotation/responses'/(str(a['attempt_number']).zfill(4)+'.json')).exists()
                                           else 'interrupted_unknown_reserved' for a in own[:-1]],
                    'attempts':own,'retries':len(own)-1,'repairs':len(own)-1}
        value={'annotations':annotation,'provenance':provenance,'candidate_id':candidate['candidate_id'],
               'source_sha256':candidate['source']['source']['record_sha256']}
        write(path,value)
        return value
    if path.exists():
        item=read(path)
    else:
        item=None
        own=[a for a in annotation_ledger(output) if a['candidate_id']==candidate['candidate_id']]
        if own:
            response=output/'annotation/responses'/(str(own[-1]['attempt_number']).zfill(4)+'.json')
            if response.exists() and read(response)['failure'] is None:
                raw=read(response)['raw_response']
                item=completed_item(validate_generated(wrapper,decode(raw)),raw)
        for round_no in range(2):
            if item is not None:break
            history=annotation_ledger(output)
            own=[a for a in history if a['candidate_id']==candidate['candidate_id']]
            if len(own)>round_no:continue
            feedback=None
            if own:
                response=output/'annotation/responses'/(str(own[-1]['attempt_number']).zfill(4)+'.json')
                feedback=read(response)['failure'] if response.exists() else 'interrupted_unknown_reserved'
            body=payload(wrapper,config,feedback);bound=reservation(body,config)
            if not own and digest(body)!=execution_plan(output)['prepared_payload_sha256'][candidate['candidate_id']]:raise ValueError('initial authorized payload changed')
            admit_annotation(history,bound,not own)
            key=load_key(Path(config['credential_reference_file'])) # Explicit authorized boundary; never logged.
            number=len(history)+1; name=str(number).zfill(4)+'.json'
            attempt={'attempt_number':number,'candidate_id':candidate['candidate_id'],'sample_id':wrapper['sample_id'],
                     'initial_request':not own,'repair':bool(own),'reservation':bound,'request_sha256':digest(body)}
            write(output/'annotation/attempts'/name,attempt)
            write(output/'annotation/requests'/name,body)
            started=time.monotonic();raw=None;failure=None;annotation=None;global_failure=False
            account={'recorded_cost_usd':None,'charged_upper_bound_usd':bound['usd'],'status':'unknown_usage_reserved'}
            try:
                raw=http_call(body,config,key)
                account=usage_cost(raw,config,bound)
                if account['status']=='pricing_or_token_bound_violation':
                    raise ProviderError('pricing_or_token_bound_violation')
                if not raw.get('model') or not (raw['model']==config['model'] or raw['model'].startswith(config['model']+'-')):
                    raise ProviderError('returned_model_identity_mismatch')
                annotation=validate_generated(wrapper,decode(raw))
            except Exception as exc:
                # No provider body, key or unrelated environment in failure logs.
                failure=str(exc)[:240] if isinstance(exc,(ValueError,ProviderError)) else type(exc).__name__
                global_failure=isinstance(exc,ProviderError) and not (failure.startswith('incomplete_') or failure in ('timeout','refusal','missing_or_multiple_final_text'))
            write(output/'annotation/responses'/name,{'raw_response':raw,'accounting':account,
                  'failure':failure,'wall_seconds':time.monotonic()-started})
            print(canonical({'attempt':number,'candidate':candidate['candidate_id'],'failure':failure,
                             'charged_usd':account['charged_upper_bound_usd']}).decode(),flush=True)
            if global_failure:
                raise GlobalProviderFailure(failure)
            if not failure:
                item=completed_item(annotation,raw);break
        if item is None:raise ValueError('annotation_failed_after_two_logged_attempts')
    if item['source_sha256']!=candidate['source']['source']['record_sha256']:
        raise ValueError('saved annotation source mismatch')
    enriched=attach_annotation(wrapper,{'sample_id':wrapper['sample_id'],'annotation_version':'SPQ06-public-language/1.0.0',
                             'annotations':item['annotations'],'provenance':item['provenance']})
    from .event_language import enrich
    return enrich(enriched)


def simulate(pair, candidate, output, plan):
    case=output/'cases'/candidate['candidate_id']; runs=case/'runs'
    receipt=runs/'pairs'/(pair['pair_id']+'.json')
    if receipt.exists():
        if read(case/'simulation-plan.json')['pairs']!=[pair]:
            raise ValueError('saved simulation pair identity changed')
        verify_manifest(runs)
        return read(receipt),runs
    charged_wall=simulation_wall(output)
    executions=len(list((output/'cases').glob('*/runs/executions/*/reservation.json')))
    remaining=14400-charged_wall
    if executions+4>1612 or remaining<=0:
        raise CeilingReached('simulation cumulative ceiling reached; no enlargement')
    subplan={'version':'SPQ06-bounded-single-pair/1.0.0','base_commit':plan['producer_commit'], 'pairs':[pair],
             'limits':{'maximum_simulation_executions':4,'total_wall_seconds':remaining,'per_execution_seconds':180},
             'replay_criterion':{'version':'canonical-exact-replay/1.0.0','status':'approved','numeric_tolerance':0,
                 'authority':'Existing explicit exact-replay authority retained by SPQ06; separate admission mandatory'}}
    path=case/'simulation-plan.json'
    if path.exists():
        subplan=read(path)
        if subplan['pairs']!=[pair]:raise ValueError('saved simulation pair identity changed')
    else:write(path,subplan)
    wsl_args=['wsl.exe','-d','Ubuntu-24.04','--','env','PYTHONDONTWRITEBYTECODE=1',
              'PYTHONPATH='+linux_path(ROOT/'src'),WSL_PYTHON,'-m','simphysqa.spq02_worker',
              '--plan',linux_path(path),'--output',linux_path(runs)]
    work_path=output/'simulation-work'/(candidate['candidate_id']+'.json')
    if work_path.exists():raise CeilingReached('interrupted simulation worker retained; no automatic retry')
    # Reserve full remaining window on interruption. Normal completion replaces only in a separate receipt.
    write(work_path,{'candidate_id':candidate['candidate_id'],'reserved_wall_seconds':remaining,
                     'maximum_executions':4,'plan_sha256':digest(subplan)})
    started=time.monotonic()
    try:
        with (case/'simulation-worker.log').open('xb') as log:
            done=subprocess.run(wsl_args,stdout=log,stderr=subprocess.STDOUT,timeout=remaining)
        wall=time.monotonic()-started
    except subprocess.TimeoutExpired:
        raise CeilingReached('simulation worker total time ceiling reached') from None
    # Immutable original reservation plus distinct measured receipt; budget ledger uses receipt when present.
    write(output/'simulation-work-completed'/(candidate['candidate_id']+'.json'),{'wall_seconds':wall,
          'returncode':done.returncode,'candidate_id':candidate['candidate_id']})
    if done.returncode or not receipt.exists():raise ValueError('simulation_worker_failed; inspect saved private log')
    return read(receipt),runs


def simulation_wall(output):
    total=0
    for p in (output/'simulation-work').glob('*.json'):
        receipt=output/'simulation-work-completed'/p.name
        total += read(receipt)['wall_seconds'] if receipt.exists() else read(p)['reserved_wall_seconds']
    return total


def derive(parent, pair, runs, family, case):
    from .dataset import validate
    from .answer_annotations import enrich as answer_enrich
    from .answer_export import context_for
    from .direct import build_direct
    if family=='direct':
        result=build_direct(parent)
        return answer_enrich(result,context_for(result,None,None,{},{})),None
    implementation={}
    for rel in ('src/phi_jepa/simulation/engines.py','src/phi_jepa/simulation/bullet.py','src/phi_jepa/simulation/scenes.py'):
        path=(runs/'source-snapshot'/rel) if pair else ROOT/rel
        text=path.read_text(encoding='utf-8')
        implementation[Path(rel).stem]={'source_path':rel,'sha256':sha256(text.encode()).hexdigest(),'text':text}
    arm={}
    if parent['public']['input']['domain']=='robotic_arm':
        if pair:
            arm_path=case/'arm-interpretation.json'
            if not arm_path.exists():
                args=['wsl.exe','-d','Ubuntu-24.04','--','env','PYTHONDONTWRITEBYTECODE=1',
                      'PYTHONPATH='+linux_path(ROOT/'src'),WSL_PYTHON,'-m','simphysqa.spq02_arm_inspect',
                      '--plan',linux_path(case/'simulation-plan.json'),'--output',linux_path(arm_path)]
                output=case.parent.parent
                remaining=14400-simulation_wall(output)
                if remaining<=0:raise CeilingReached('simulation/compilation wall ceiling reached')
                token=case.name+'-static-arm'
                work=output/'simulation-work'/(token+'.json')
                if work.exists():raise CeilingReached('interrupted static model compilation retained')
                write(work,{'candidate_id':case.name,'reserved_wall_seconds':min(180,remaining),
                            'model_compilations':1,'maximum_executions':0})
                started=time.monotonic()
                done=subprocess.run(args,stdout=subprocess.DEVNULL,stderr=subprocess.DEVNULL,
                                    timeout=min(180,remaining))
                write(output/'simulation-work-completed'/(token+'.json'),{'wall_seconds':time.monotonic()-started,
                      'returncode':done.returncode,'model_compilations':1,'candidate_id':case.name})
                if done.returncode:raise ValueError('static model interpretation failed')
            arm=read(arm_path)
        else:
            arm={'status':'implementation_interpretation_from_retained_source_not_new_model_compilation',
                 'source_sha256':file_hash(ROOT/'src/phi_jepa/simulation/engines.py'),
                 'interpretation':'Generalized hinge-coordinate torque; raw historical frame remains unchanged.'}
    if family=='predictive':
        context=context_for(parent,None,None,implementation,arm)
        context['implementation_role']='Original admitted factual source; no additional replay for this predictive candidate.'
        return answer_enrich(parent,context),None
    from .counterfactual import build
    key=pair['pair_id']
    receipt=read(runs/'pairs'/(key+'.json'))
    if receipt['status']!='completed':raise ValueError('paired_replay_or_admission_failed')
    alternative=read(runs/'alternative-records'/(key+'.json'))
    proofs={'pair_receipt':receipt,'replay':read(runs/'verification'/(key+'-replay.json')),
            'original_admission':read(runs/'verification'/(key+'-original-admission.json')),
            'alternative_admission':read(runs/'verification'/(key+'-alternative-admission.json'))}
    artifacts={}
    for role in ('original-coarse','original-fine','alternative-coarse','alternative-fine'):
        folder=runs/'executions'/(key+'-'+role)
        r=read(folder/'result.json');reservation=read(folder/'reservation.json')
        artifacts[role]={'run_id':key+'-'+role,'result_sha256':file_hash(folder/'result.json'),
                         'reservation_sha256':file_hash(folder/'reservation.json'),
                         'integration_timestep_s':reservation['dt'],'wall_seconds':r['wall_seconds']}
    specs=sorted(parent['public']['input']['answer_spec'],key=lambda t:t['target_id'])
    target=next(t for t in specs if t['answer_type'] in ('number','integer','vector','boolean'))
    counterfactual=build(parent,alternative,pair,proofs,artifacts,target)
    context=context_for(counterfactual,pair,runs,implementation,arm)
    context['implementation_role']='Saved SPQ06 executed source; exact replay and separate admission receipts for this candidate only.'
    counterfactual=answer_enrich(counterfactual,context)
    validate(counterfactual)
    if family=='counterfactual':return counterfactual,None
    if family=='explanation':
        from .explanation import build
        return build(counterfactual),None
    if family=='clarification':
        from .clarification import build
        result,selection=build(counterfactual,runs)
        return result,selection
    raise ValueError('unknown family')


def process(output):
    output=external(output);plan=execution_plan(output)
    if plan['provider_config']!=settings() or plan['simulation_limits']!=SIM_LIMITS:
        raise ValueError('authorization/config identity mismatch')
    for relative,expected in plan['scientific_source_pins'].items():
        if file_hash(ROOT/relative)!=expected:raise ValueError('frozen executed source changed:'+relative)
    config=plan['provider_config'];completed=[];failures=[];stop=None
    print(canonical({'preflight':{'model':config['model'],'output_tokens':2048,'annotation_limits':LIMITS,
           'simulation_limits':SIM_LIMITS,'pricing_verified':'2026-10-09','target_unique_QA':400}}).decode(),flush=True)
    with locked(output/'.candidate-processing.lock'),formal_scope(plan['candidates'],plan['excluded_groups']):
        counts={}
        for candidate in plan['candidates']:
            cell=candidate['cell']
            if counts.get(cell,0)>=20:continue
            case=output/'cases'/candidate['candidate_id']; status_path=case/'status.json'
            if status_path.exists():
                status=read(status_path)
                if status['status']=='completed':
                    record=read(case/'record.json')
                    from .dataset import validate
                    validate(record);completed.append(record);counts[cell]=counts.get(cell,0)+1
                else:failures.append(status)
                continue
            pair=None;runs=None;selection=None;stage='source_eligibility'
            try:
                parent=source_record(candidate['source'])
                family=candidate['question_type']
                if family in ('counterfactual','explanation','clarification'):
                    pair=pair_for(candidate)
                    from .counterfactual import public_input
                    target=next(t for t in sorted(parent['public']['input']['answer_spec'],key=lambda t:t['target_id']) if t['answer_type'] in ('number','integer','vector','boolean'))
                    public_input(pair['source_records'][next(i for i,s in enumerate(pair['source_records']) if s['sample_id']==parent['sample_id'])],pair['pair_id'],target)
                    stage='simulation_qualification'
                    # Cumulative worker time, rather than renewing per-candidate old allowances.
                    receipt,runs=simulate(pair,candidate,output,plan)
                    if receipt['status']!='completed':raise ValueError('saved_replay_or_admission_rejection')
                stage='public_annotation'
                parent=annotate(parent,candidate,output,config)
                stage='family_qualification'
                record,selection=derive(parent,pair,runs,family,case)
                if selection is not None:write(case/'clarification-eligibility.json',selection)
                if record is None:raise ValueError('no_scorer_disjoint_query_gap')
                from .dataset import validate,restore,public_record
                validate(record)
                if digest(restore(record))!=candidate['source']['source']['record_sha256']:
                    raise ValueError('source_restore_mismatch')
                view=public_record(record,association_version='simphysqa-associations/1.1.1')
                write(case/'record.json',record);write(case/'public-view.json',view)
                status={'candidate_id':candidate['candidate_id'],'cell':cell,'rank':candidate['rank'],
                        'status':'completed','sample_id':record['sample_id'],'record_sha256':digest(record),
                        'group_id':candidate['source']['group_id'],'source_sample_id':candidate['source']['sample_id']}
                write(status_path,status);completed.append(record);counts[cell]=counts.get(cell,0)+1
                print(canonical({'completed':len(completed),'cell':cell,'cell_count':counts[cell]}).decode(),flush=True)
            except (CeilingReached,GlobalProviderFailure) as exc:
                stop=str(exc);break
            except Exception as exc:
                failure={'candidate_id':candidate['candidate_id'],'cell':cell,'rank':candidate['rank'],
                         'status':'rejected','stage':stage,'reason':type(exc).__name__+': '+str(exc)[:300],
                         'source_sample_id':candidate['source']['sample_id'],'group_id':candidate['source']['group_id']}
                write(status_path,failure);failures.append(failure)
                print(canonical(failure).decode(),flush=True)
                if not isinstance(exc,(ValueError,StopIteration)):
                    stop='unexpected_adapter_error_requires_versioned_repair: '+failure['reason'];break
        history=annotation_ledger(output)
        snapshot={'version':plan['version'],'completed_items':len(completed),'target_items':400,
            'shortfall':400-len(completed),'allocation':counts,'rejections':failures,'stop_reason':stop,
            'initial_requests':sum(h['initial_request'] for h in history),'annotation_attempts':len(history),
            'repairs':sum(h['repair'] for h in history),'charged_usd':sum(h['charged_upper_bound_usd'] for h in history),
            'annotation_work_seconds':sum(h['wall_seconds'] for h in history),
            'simulation_work_seconds':simulation_wall(output),
            'simulation_executions':len(list((output/'cases').glob('*/runs/executions/*/reservation.json'))),
            'static_model_compilations':sum(read(p).get('model_compilations',0) for p in (output/'simulation-work').glob('*.json')),
            'ratings_collected':0,'answering_calls':0}
        number=len(list((output/'summaries').glob('*.json')))+1
        write(output/'summaries'/(str(number).zfill(3)+'.json'),snapshot)
        print(canonical(snapshot).decode(),flush=True)
        return snapshot


def main():
    p=argparse.ArgumentParser();p.add_argument('command',choices=('freeze','run'))
    p.add_argument('--preparation',type=Path);p.add_argument('--output',type=Path,required=True)
    a=p.parse_args()
    if a.command=='freeze':freeze(a.preparation,a.output)
    else:process(a.output)


if __name__=='__main__':main()
