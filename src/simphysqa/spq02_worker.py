"""Budgeted serial simulator replay/omission verification; failures remain durable."""
from dataclasses import asdict
from copy import deepcopy
from hashlib import sha256
import argparse,importlib.metadata,json,time,traceback,platform,multiprocessing,math
from pathlib import Path
from simphysqa.io import read,write,canonical,digest,ROOT,external,manifest
from simphysqa.spq01a import retained,verify_manifest
from simphysqa.scoring import distance
from phi_jepa.simulation.common import Scenario,Rollout
from phi_jepa.simulation.pipeline import adapter,comparison
from phi_jepa.simulation.validation import validate

def physics(result,domain):
    if domain=='driving':return result.diagnostics['min_forward_velocity']>=-.02
    if domain=='tethered_load':return result.diagnostics['min_tension_N']>0 and result.diagnostics['max_length_error_m']<1e-6
    return True

def simulate_to_file(pair,dt,omit,result_path,reservation_hash):
    """One isolated real simulation; parent enforces wall-time and call budgets."""
    now=time.perf_counter()
    try:
        result=adapter(pair['scenario']['domain']).simulate(Scenario(**pair['scenario']),pair['config'],dt,omit_scheduled_intervention=omit)
        data={'status':'completed','wall_seconds':time.perf_counter()-now,'rollout':asdict(result),'reservation_sha256':reservation_hash}
    except Exception as exc:
        data={'status':'failed','wall_seconds':time.perf_counter()-now,'error':type(exc).__name__+': '+str(exc),'traceback':traceback.format_exc(),'reservation_sha256':reservation_hash}
    write(result_path,data)

def field_differences(expected,actual,path=''):
    """Exact JSON scientific comparison: type-sensitive, no rounding or tolerance."""
    if canonical(expected)==canonical(actual):return []
    if isinstance(expected,dict) and isinstance(actual,dict):
        out=[]
        for key in sorted(set(expected)|set(actual)):
            pointer=path+'/'+key.replace('~','~0').replace('/','~1')
            if key not in expected or key not in actual:out.append({'path':pointer,'expected_present':key in expected,'actual_present':key in actual})
            else:out.extend(field_differences(expected[key],actual[key],pointer))
        return out
    if isinstance(expected,list) and isinstance(actual,list):
        out=[]
        if len(expected)!=len(actual):out.append({'path':path+'/length','expected':len(expected),'actual':len(actual)})
        for i,(a,b) in enumerate(zip(expected,actual)):out.extend(field_differences(a,b,path+'/'+str(i)))
        return out
    return [{'path':path,'expected':expected,'actual':actual,'expected_type':type(expected).__name__,'actual_type':type(actual).__name__}]

def replay(result,sources,plan):
    differences=[];boolean_differences=[];event_differences=[];all_fields=[]
    source_events=[];source_states=[];source_labels=[];source_public=[];checked=0
    for source in sources:
        sample=source['sample_id']
        for state in source['input']['states']+source['reference']['states']:
            actual=next((s for s in result.states if s['timestamp']==state['timestamp']),None)
            changes=field_differences(state,actual,'/states/'+str(state['timestamp']))
            all_fields.extend({'source_sample_id':sample,'scope':'saved_state',**d} for d in changes)
            source_states.append(not changes)
            if actual is None:continue
            for b in state['measurements']:
                a=next((m for m in actual['measurements'] if (m['entity_id'],m['name'])==(b['entity_id'],b['name'])),None)
                checked+=1
                if a is None:continue
                row={'source_sample_id':sample,'timestamp':state['timestamp'],'entity':b['entity_id'],'quantity':b['name'],'unit':b['unit'],'frame':b['frame']}
                if type(b['value']) is bool:
                    if canonical(a['value'])!=canonical(b['value']):boolean_differences.append({**row,'expected':b['value'],'actual':a['value']})
                else:
                    av=a['value'] if isinstance(a['value'],list) else [a['value']]
                    bv=b['value'] if isinstance(b['value'],list) else [b['value']]
                    if len(av)==len(bv) and all(type(v) in (int,float) for v in av+bv):
                        components=[abs(x-y) for x,y in zip(av,bv)]
                        error=math.sqrt(sum(v*v for v in components))
                        if canonical(a['value'])!=canonical(b['value']):differences.append({**row,'component_max_error':max(components),'euclidean_error':error,'exact_value_equal':False})
        events=[e for e in result.events if e['start_time']<=source['reference']['states'][-1]['timestamp']]
        from phi_jepa.simulation.records import labels
        event_changes=field_differences(source['reference']['events'],events,'/reference/events')
        event_differences.extend({'source_sample_id':sample,**d} for d in event_changes)
        all_fields.extend({'source_sample_id':sample,'scope':'private_event',**d} for d in event_changes)
        source_events.append(not event_changes)
        label_changes=field_differences(source['reference']['structured_label'],labels(result.states,source['input']['answer_spec']),'/reference/structured_label')
        all_fields.extend({'source_sample_id':sample,'scope':'structured_label',**d} for d in label_changes);source_labels.append(not label_changes)
        public_keys=('global_context','entities','controller','known_events','coordinate_convention')
        public_changes=field_differences({k:source['input'][k] for k in public_keys},result.public,'/public_model')
        all_fields.extend({'source_sample_id':sample,'scope':'public_model_controller',**d} for d in public_changes);source_public.append(not public_changes)
    return {'passed':all(source_states) and all(source_events) and all(source_labels) and all(source_public),'criterion':plan['replay_criterion'],
        'all_structured_labels_exact':all(source_labels),'all_saved_states_exact':all(source_states),
        'all_private_events_equal':all(source_events),'all_public_definitions_exact':all(source_public),
        'excluded_fields':'Only non-scientific runtime/creation/output-path metadata; no physical fields excluded',
        'measurements_checked':checked,'numeric_max_error':max((d['euclidean_error'] for d in differences),default=0),
        'first_differing_fields':all_fields[:20],'differing_field_count':len(all_fields),
        'numeric_differences_by_quantity_unit_timestamp':differences,'boolean_differences':boolean_differences,'event_differences':event_differences}

def alternative_record(pair,result,agreement,provenance):
    source=deepcopy(pair['source_records'][0])
    # Use the exact selected question horizon/specification, not the first shard row.
    original=next(s for s in pair['source_records'] if s['sample_id']==pair['source_wrapper']['sample_id'])
    source=deepcopy(original);inp=source['input'];cutoff=inp['observation_cutoff'];end=max(t['end_time'] for t in inp['answer_spec'])
    from phi_jepa.simulation.records import labels,answer_text
    from phi_jepa.simulation.common import opaque
    inp['known_events']=[]
    inp['controller']['description']+=' Matched alternative: omit only the scheduled intervention; event-dependent controller terms are disabled, all remaining controls and laws are unchanged.'
    inp['question']='Under the matched omission of the scheduled intervention, '+inp['question']
    source['sample_id']=pair['pair_id']+'-alternative'
    ref=source['reference'];ref['states']=[s for s in result.states if cutoff<s['timestamp']<=end]
    ref['events']=[e for e in result.events if e['start_time']<=end]
    ref['structured_label']=labels(result.states,inp['answer_spec']);ref['label']=answer_text(inp['answer_spec'],ref['structured_label'])
    terminal=next(s for s in ref['states'] if s['timestamp']==end)
    ref['evidence']=[{'evidence_id':opaque(pair['pair_id'],'alternative-evidence',end),'state_ids':[terminal['state_id']],'event_ids':[],'description':'Matched omission simulator terminal readout.'}]
    ref['explanation']='Alternative simulator terminal readouts; not a causal explanation annotation.'
    sim=source['metadata']['simulation']
    sim['generator_commit']=provenance['base_commit'];sim['runtime_environment']=[{'entity_id':'runtime','name':'spq02_implementation_sha256','value':provenance['implementation_sha256'],'unit':'text','frame':'not_applicable'}]
    sim['engine_version']=result.version
    sim['config_sha256']=digest({'original_config_sha256':sim['config_sha256'],'omit_scheduled_intervention':True,'implementation_sha256':provenance['implementation_sha256']})
    checks=[{'name':'semantic','status':'pass','details':'Existing source validator verifies states, labels, event definitions and bindings.'},
            {'name':'refined_timestep','status':'pass' if agreement['passed'] else 'fail','details':json.dumps(agreement)},
            {'name':'domain_physics','status':'pass' if physics(result,inp['domain']) else 'fail','details':'Same existing admission conditions; no threshold changes.'}]
    source['metadata']['validation']={'status':'accepted' if all(c['status']=='pass' for c in checks) else 'pending','checks':checks}
    validate(source,admission=True)
    return source

def run(plan_path,output):
    plan=read(plan_path);output=external(output)
    if (output/'manifest.json').exists():verify_manifest(output)
    if plan['replay_criterion']['status']!='approved':
        if not (plan_path.parent/'replay-criterion.json').exists():raise ValueError('explicit original replay criterion pending: canonical exact equality proposed; no simulations executed')
        criterion=read(plan_path.parent/'replay-criterion.json')
        if criterion['status']!='approved' or criterion['version']!=plan['replay_criterion']['version']:raise ValueError('explicit original replay criterion confirmation pending')
        plan['replay_criterion']=criterion
    started=time.monotonic()
    prior_wall=sum(read(p)['wall_seconds'] for p in (output/'executions').glob('*/result.json'))
    packages={p:importlib.metadata.version(p) for p in ('mujoco','pybullet','numpy','jsonschema','psutil')}
    files=('src/phi_jepa/simulation/engines.py','src/phi_jepa/simulation/bullet.py','src/phi_jepa/simulation/scenes.py','src/phi_jepa/simulation/common.py','src/phi_jepa/simulation/records.py','src/phi_jepa/simulation/validation.py','src/phi_jepa/simulation/pipeline.py','src/phi_jepa/artifacts.py','dataset.schema.json','src/simphysqa/spq02_worker.py')
    provenance={'base_commit':plan['base_commit'],'source_files':{p:sha256((ROOT/p).read_text(encoding='utf-8').encode()).hexdigest() for p in files},'packages':packages,'platform':platform.platform(),'python':platform.python_version()}
    provenance['implementation_sha256']=digest(provenance['source_files'])
    provenance['generator_commit_role']='Committed base; executed modifications pinned by source snapshots and hashes'
    for relative in files:
        path=output/'source-snapshot'/relative
        text=(ROOT/relative).read_text(encoding='utf-8').encode()
        if path.exists():
            if path.read_bytes()!=text:raise ValueError('simulation source snapshot changed')
        else:
            path.parent.mkdir(parents=True,exist_ok=True)
            with path.open('xb') as stream:stream.write(text)
    retained(output/'runtime.json',provenance)
    retained(output/'resolved-plan.json',plan)
    retained(output/'environment-comparison.json',{
        'version':'spq02-environment-comparison/1.0.0','current_runtime':provenance,
        'cases':[{'pair_id':pair['pair_id'],'original_environment':pair['original_environment'],
            'original_simulation_settings':pair['source_wrapper']['private']['metadata']['simulation'],
            'current_packages':packages,
            'package_differences':{key:{'original':value,'current':packages.get(key,'not_an_execution_dependency')} for key,value in pair['original_environment']['packages'].items() if key in packages and value!=packages[key]},
            'configuration_difference':'None; immutable original scenario/configuration at coarse dt; refined dt explicitly halved for admission'} for pair in plan['pairs']]})
    print(json.dumps({'pairs':len(plan['pairs']),'limits':plan['limits'],'packages':packages,'new_model_calls':0}),flush=True)
    def execute(pair,role,dt,omit):
        folder=output/'executions'/(pair['pair_id']+'-'+role)
        result_path=folder/'result.json'
        reservation={'pair_id':pair['pair_id'],'role':role,'scenario_sha256':digest(pair['scenario']),'config_sha256':digest(pair['config']),'dt':dt,'omit_scheduled_intervention':omit,'runtime_sha256':digest(provenance)}
        if result_path.exists():
            data=read(result_path)
            if read(folder/'reservation.json')!=reservation or data['reservation_sha256']!=digest(reservation):raise RuntimeError('retained execution identity changed')
            if data['status']!='completed':raise RuntimeError('retained failed execution: '+data['error'])
            return Rollout(**data['rollout'])
        if (folder/'reservation.json').exists():raise RuntimeError('interrupted execution reservation: explicit recovery needed; no automatic retry')
        count=len(list((output/'executions').glob('*/reservation.json')))
        remaining=plan['limits']['total_wall_seconds']-prior_wall-(time.monotonic()-started)
        if count>=plan['limits']['maximum_simulation_executions'] or remaining<=0:raise RuntimeError('simulation budget exhausted')
        write(folder/'reservation.json',reservation)
        now=time.perf_counter()
        process=multiprocessing.get_context('spawn').Process(target=simulate_to_file,args=(pair,dt,omit,result_path,digest(reservation)))
        process.start();process.join(min(plan['limits']['per_execution_seconds'],remaining))
        if process.is_alive():
            process.terminate();process.join()
            if not result_path.exists():write(result_path,{'status':'failed','wall_seconds':time.perf_counter()-now,'error':'TimeoutError: configured simulation wall limit exceeded','reservation_sha256':digest(reservation)})
            raise RuntimeError('simulation wall limit exceeded; execution retained as failure')
        if not result_path.exists():write(result_path,{'status':'failed','wall_seconds':time.perf_counter()-now,'error':'Simulator subprocess exited without result: '+str(process.exitcode),'reservation_sha256':digest(reservation)})
        data=read(result_path)
        if data['status']!='completed':raise RuntimeError(data['error'])
        return Rollout(**data['rollout'])
    # Qualify one selected case per domain before the remaining selected cases.
    for pair in plan['pairs']:
        receipt=output/'qualifications'/(pair['pair_id']+'.json')
        if receipt.exists():continue
        phase='prerequisites';dt=pair['source_wrapper']['private']['metadata']['simulation']['integration_timestep_s']
        try:
            engine=pair['source_wrapper']['private']['metadata']['simulation']['engine']
            expected=pair['original_environment']['packages']
            if any(packages[p]!=expected[p] for p in (engine,'numpy','jsonschema','psutil')):raise RuntimeError('original runtime package versions do not match')
            phase='original-coarse';original=execute(pair,phase,dt,False)
            phase='original-replay';rep=replay(original,pair['source_records'],plan)
            write(output/'verification'/(pair['pair_id']+'-replay.json'),rep)
            if not rep['passed']:raise RuntimeError('original replay qualification failed')
            phase='original-fine';fine=execute(pair,phase,dt/2,False)
            agreement=comparison(original,fine,pair['scenario']['domain'],pair['config']['time']['default_target_times_s'],pair['config']['time']['default_cutoff_s'])
            write(output/'verification'/(pair['pair_id']+'-original-admission.json'),{'refinement':agreement,'domain_physics':physics(original,pair['scenario']['domain'])})
            if not agreement['passed'] or not physics(original,pair['scenario']['domain']):raise RuntimeError('original refinement/domain admission failed')
            write(receipt,{'pair_id':pair['pair_id'],'domain':pair['scenario']['domain'],'status':'qualified','source_sample_id':pair['source_wrapper']['sample_id'],'original_replay':rep})
        except Exception as exc:
            write(receipt,{'pair_id':pair['pair_id'],'domain':pair['scenario']['domain'],'status':'failed','phase':phase,'error':type(exc).__name__+': '+str(exc),'traceback':traceback.format_exc(),'qualified':False})
        print(json.dumps(read(receipt)),flush=True)
    for pair in plan['pairs']:
        receipt=output/'pairs'/(pair['pair_id']+'.json')
        if receipt.exists():continue
        qualification=read(output/'qualifications'/(pair['pair_id']+'.json'))
        if qualification['status']!='qualified':
            write(receipt,qualification);continue
        dt=pair['source_wrapper']['private']['metadata']['simulation']['integration_timestep_s']
        phase='alternative-coarse'
        try:
            original=execute(pair,'original-coarse',dt,False)
            alternative=execute(pair,phase,dt,True)
            # Nonphysical IDs and raw source scenario are identical; only omission flag differs.
            if alternative.asset!=original.asset or alternative.public['entities']!=original.public['entities']:raise RuntimeError('matched model/physical prior changed')
            if canonical([s for s in alternative.states if s['timestamp']<=pair['source_wrapper']['public']['input']['observation_cutoff']])!=canonical(pair['source_wrapper']['public']['input']['states']):raise RuntimeError('alternative pre-intervention observed prefix differs')
            if any(e['type']=='applied_intervention' for e in alternative.events):raise RuntimeError('omitted intervention remained in alternative')
            phase='alternative-fine';alternative_fine=execute(pair,phase,dt/2,True)
            agreement_alt=comparison(alternative,alternative_fine,pair['scenario']['domain'],pair['config']['time']['default_target_times_s'],pair['config']['time']['default_cutoff_s'])
            write(output/'verification'/(pair['pair_id']+'-alternative-admission.json'),{'refinement':agreement_alt,'domain_physics':physics(alternative,pair['scenario']['domain'])})
            phase='alternative-record-admission';source=alternative_record(pair,alternative,agreement_alt,provenance)
            write(output/'alternative-records'/(pair['pair_id']+'.json'),source)
            write(receipt,{'pair_id':pair['pair_id'],'domain':pair['scenario']['domain'],'status':'completed','source_sample_id':pair['source_wrapper']['sample_id'],'original_replay':qualification['original_replay'],'alternative_sha256':digest(source),'qualified':True})
        except Exception as exc:
            write(receipt,{'pair_id':pair['pair_id'],'domain':pair['scenario']['domain'],'status':'failed','phase':phase,'error':type(exc).__name__+': '+str(exc),'traceback':traceback.format_exc(),'qualified':False})
        print(json.dumps(read(receipt)),flush=True)
    receipts=[read(p) for p in (output/'pairs').glob('*.json')]
    calls=[read(p) for p in (output/'executions').glob('*/result.json')]
    ledger=[]
    for path in sorted((output/'executions').glob('*/result.json')):
        result=read(path);reservation=read(path.parent/'reservation.json')
        diag=result.get('rollout',{}).get('diagnostics',{})
        ledger.append({**reservation,'status':result['status'],'wall_seconds':result['wall_seconds'],
            'integration_steps':diag.get('steps'),'solve_calls':diag.get('solve_calls'),'error':result.get('error')})
    retained(output/'execution-ledger.json',ledger)
    summary={'completed_pairs':sum(r['status']=='completed' for r in receipts),'failed_pairs':sum(r['status']=='failed' for r in receipts),'pending_pairs':len(plan['pairs'])-len(receipts),'execution_reservations':len(list((output/'executions').glob('*/reservation.json'))),'successful_executions':sum(r['status']=='completed' for r in calls),'failed_executions':sum(r['status']=='failed' for r in calls),'simulation_wall_seconds':sum(r['wall_seconds'] for r in calls),'run_wall_seconds':time.monotonic()-started,'new_model_calls':0}
    # A resume receipt has separate measured wall time; existing run summary stays intact.
    if not (output/'run-summary.json').exists():write(output/'run-summary.json',summary)
    if not (output/'manifest.json').exists():manifest(output,{'purpose':'SPQ02_private_simulation_execution_and_verification','resolved_plan_sha256':digest(plan),'summary':summary})
    print(json.dumps(summary),flush=True)
    return summary

def preflight(plan_path,output):
    """Resolve prerequisites and exact budget without reserving/starting simulations."""
    plan=read(plan_path)
    packages={p:importlib.metadata.version(p) for p in ('mujoco','pybullet','numpy','jsonschema','psutil')}
    decision=plan_path.parent/'replay-criterion.json'
    criterion=read(decision) if decision.exists() else plan['replay_criterion']
    prerequisites=[]
    for pair in plan['pairs']:
        engine=pair['source_wrapper']['private']['metadata']['simulation']['engine']
        expected=pair['original_environment']['packages']
        prerequisites.append({'pair_id':pair['pair_id'],'domain':pair['scenario']['domain'],
            'matching_runtime':all(packages[p]==expected[p] for p in (engine,'numpy','jsonschema','psutil')),
            'source_observed_states':len(pair['source_wrapper']['public']['input']['states']),
            'stored_coarse_timestep_s':pair['source_wrapper']['private']['metadata']['simulation']['integration_timestep_s']})
    result={'version':'spq02-preflight/1.0.0','plan_sha256':digest(plan),'pairs':len(plan['pairs']),
        'maximum_requested_simulations':len(plan['pairs'])*4,'limits':plan['limits'],'packages':packages,
        'criterion':criterion,'prerequisites':prerequisites,'simulation_executions':0,'model_calls':0,
        'status':'ready' if criterion['status']=='approved' and all(p['matching_runtime'] for p in prerequisites) else 'pending_prerequisite'}
    retained(output,result)
    print(json.dumps(result),flush=True)
    return result

if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('--plan',type=Path,required=True);p.add_argument('--output',type=Path,required=True);p.add_argument('--preflight',action='store_true')
    a=p.parse_args()
    if a.preflight:preflight(a.plan,a.output)
    else:run(a.plan,a.output)
