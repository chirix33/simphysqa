"""Post-core remaining-200 preparation /1.0.0. Offline; no execution authority.

Never writes to the live ledger or reads correctness to select/forecast. Exact
400-pool bytes, admission/exclusion evidence and sealed workers are reused.
"""
import argparse,collections,json,math,sqlite3,subprocess,time
from copy import deepcopy
from datetime import datetime,timezone,timedelta
from pathlib import Path
from . import execution_adapter as a
from .main_public import request_from
from .spq06 import public_request
from .heldout_scope import formal_scope
from .spq01a import verify_manifest
from .io import DOMAINS,QUESTION_TYPES

VERSION='SPQ06-complement-preparation/1.0.2'
SCOPE='spq06-complement-1.0.0'
COMBINATIONS=[('qwen3_8b_direct','enriched'),('qwen3_8b_thinking','enriched'),('llama31_8b_direct','enriched'),
 ('llama31_8b_cot','enriched'),('qwen3_32b_awq_off','enriched'),('qwen3_32b_awq_on','enriched'),
 ('qwen3_8b_direct','structured_only'),('qwen3_32b_awq_on','structured_only')]
DEADLINE='2026-10-13T11:59:00+00:00'
CUTOFF='2026-10-12T23:00:00+00:00'  # 18:00 Chicago Oct12; 12h59 writing reserve.


def scoped_key(key):
 if len(key.split('|'))!=4:raise ValueError('exact worker logical stage key required')
 return SCOPE+'|'+key

def select(core,pool,excluded):
 if len(core)!=200 or len(pool)!=400:raise ValueError('frozen 200/400 counts required')
 for rows in (core,pool):
  if len({r['sample_id'] for r in rows})!=len(rows) or len({r['group_id'] for r in rows})!=len(rows):raise ValueError('sample/group uniqueness')
 c={r['sample_id']:r for r in core};cg={r['group_id'] for r in core};p={r['sample_id']:r for r in pool}
 if not c.keys()<=p.keys() or any(c[k]!=p[k] for k in c):raise ValueError('core must be exact frozen pool subset')
 result=[]
 for item in pool:
  bysample=item['sample_id'] in c;bygroup=item['group_id'] in cg
  if bysample!=bygroup:raise ValueError('sample AND original group complement disagreement')
  if not bysample:result.append(deepcopy(item))
 if len(result)!=200 or {r['group_id'] for r in result}&cg:raise ValueError('exact disjoint complement')
 if any(r['group_id'] in excluded or r['split']!='test_id' for r in result):raise ValueError('excluded group or original split mismatch')
 cells=collections.defaultdict(list)
 for item in result:cells[(item['domain'],item['family'])].append(item['qualified_cell_rank'])
 if set(cells)!={(d,f) for d in DOMAINS for f in QUESTION_TYPES} or any(sorted(ranks)!=list(range(11,21)) for ranks in cells.values()):raise ValueError('ten frozen extension ranks per domain/family')
 if set(collections.Counter(r['family'] for r in result).values())!={40}:raise ValueError('forty per family')
 return result

def ledger_snapshot(path):
 conn=sqlite3.connect('file:'+Path(path).resolve().as_posix()+'?mode=ro',uri=True)
 try:
  conn.execute('BEGIN')
  tables=[r[0] for r in conn.execute("SELECT name FROM sqlite_master WHERE type='table'")]
  rows={t:conn.execute('SELECT * FROM '+t).fetchall() for t in tables}
  allocations=dict(rows['executor_allocations']);meta=dict(rows['meta']);owners={r[0]:r[1] for r in rows['assignments']}
  byowner={o:{'process_seconds':0,'control_seconds':0,'dispatcher_seconds':0} for o in allocations}
  for _,assignment,bound,actual,state in rows['processes']:
   byowner[owners[assignment]]['process_seconds']+=max(bound,actual or 0) if actual is None or state in ('unknown','interrupted') else actual
  for _,owner,_,bound,actual,state in rows['control_work']:
   byowner[owner]['control_seconds']+=max(bound,actual or 0) if actual is None or state in ('unknown','interrupted') else actual
  processes={r[0]:r for r in rows['processes']}
  for pid,seconds,_ in rows['dispatcher_gaps']:byowner[owners[processes[pid][1]]]['dispatcher_seconds']+=seconds
  for owner,x in byowner.items():x.update(ceiling_seconds=allocations[owner],accounted_seconds=sum(x.values()));x['remaining_seconds']=allocations[owner]-x['accounted_seconds']
  charges=sum(r['accounted_seconds'] for r in byowner.values())
  unknown=[r for r in rows['processes'] if r[3] is None or r[4] in ('unknown','interrupted')]
  return {'version':VERSION,'path':str(Path(path).resolve()),'read_only':True,'captured_utc':datetime.now(timezone.utc).isoformat(),
    'table_rows':rows,'table_digests':{k:a.digest(v) for k,v in rows.items()},'allocations':byowner,'shared_ceiling_seconds':float(meta['ceiling']),
    'accounted_seconds':charges,'shared_remaining_seconds':float(meta['ceiling'])-charges,
    'active_or_unknown_processes':unknown,'active_or_unknown_controls':[r for r in rows['control_work'] if r[4] is None or r[5] in ('unknown','interrupted')],
    'assignments':[{'assignment_id':r[0],'executor':r[1],'body':json.loads(r[2])} for r in rows['assignments']]}
 finally:conn.close()

def copy(source,target):
 target.parent.mkdir(parents=True,exist_ok=True)
 data=Path(source).read_bytes()
 if target.exists():
  if target.read_bytes()!=data:raise ValueError('existing prepared bytes differ; no overwrite')
  return  # Repeated condition/worker reuse inside one fresh export only.
 with target.open('xb') as f:f.write(data)

def task_view(q):
 message=next(m for m in q['messages'] if m['role']=='user')
 return json.JSONDecoder().raw_decode(message['content'].split('\n',1)[1].lstrip())[0]

def prepare(base,repo,output,historical,audit):
 base,repo,output,historical,audit=map(Path,(base,repo,output,historical,audit));output.mkdir(parents=True,exist_ok=False)
 prep=base/'main-preparation-1.0.0';package=base/'execution-public-1.1.1';ledger=base/'central-main-1.0.0/main.sqlite'
 before=ledger_snapshot(ledger);a.put(output/'organizer/ledger-before.json',before)
 verify_manifest(prep);a.validate_package(package)
 protocol=a.read(base/'heldout-preparation-1.0.0/protocol.json');core=a.read(prep/'nested-200-manifest.json');pool=a.read(prep/'nested-400-manifest.json')
 if not core['complete'] or not pool['complete']:raise ValueError('existing qualified frozen manifests required')
 dev=a.read(repo/'configs/simphysqa/development_exclusions.json');old=a.read(historical);audit_manifest=audit/'manifest.json';audit_final=audit/'final-140-manifest.json';aud=a.read(audit_final)
 if a.sha(historical)!=protocol['historical_prompt_use_sha256'] or a.sha(audit_manifest)!=protocol['spq05_actual_status']['manifest_sha256']:raise ValueError('authoritative exclusion receipt changed')
 audit_items=aud['assignments'];audit_groups={r['group_id'] for r in audit_items}
 if audit_groups!=set(protocol['spq05_actual_status']['groups']):raise ValueError('actual annotation audit group disagreement')
 prompt_groups={r.get('split_group') or r.get('scenario_id') for r in old['items']};prompt_ids={r['sample_id'] for r in old['items']}
 if None in prompt_groups:raise ValueError('missing original prompt-use group identity')
 categories={'development':set(dev['excluded_groups']),'annotation_audit':audit_groups,'historical_prompt_use':prompt_groups,'frozen_prior_exclusions':set(pool['exclusions'])}
 excluded=set().union(*categories.values())
 if not excluded<=set(pool['exclusions']) or set(core['exclusions'])!=set(pool['exclusions']):raise ValueError('new or inconsistent exclusions; no silent replacement')
 items=select(core['items'],pool['items'],excluded)
 if {r['sample_id'] for r in items}&prompt_ids:raise ValueError('prompt-used sample selected')
 scope=a.read(prep/'private/generation-scope.json');capacity_path=base/'main-tokenization-1.0.0/capacity-checks.json';capacity=a.read(capacity_path)
 cap={(r['sample_id'],r['condition_id'],r['input_condition']):r for r in capacity['items']};sealed_spec=a.read(package/'execution-spec.json')
 sources=[prep/'manifest.json',prep/'nested-200-manifest.json',prep/'nested-400-manifest.json',package/'package-manifest.json',historical,audit_manifest,audit_final,capacity_path,repo/'configs/simphysqa/development_exclusions.json',base/'heldout-preparation-1.0.0/protocol.json']
 sourcehashes={str(p):a.sha(p) for p in sources};requests={};stage_rows=[];fidelity=[];reused_capacity=[]
 with formal_scope(scope['candidates'],scope['excluded_groups']):
  records={i['sample_id']:a.read(prep/i['private_record']) for i in items}
  for item in items:
   if a.digest(records[item['sample_id']])!=item['record_sha256']:raise ValueError('admitted record identity changed')
  for cid,label in COMBINATIONS:
   public_c=a.read(package/sealed_spec['conditions'][cid]['path']);original_c=a.read(prep/'conditions'/f'{cid}.json')
   copy(package/sealed_spec['conditions'][cid]['path'],output/'public/conditions'/f'{cid}.json')
   worker=package/sealed_spec['conditions'][cid]['worker'];copy(worker,output/'public/workers'/f'{cid}.py')
   for item in items:
    sid=item['sample_id'];src=prep/'public/400'/label/cid/(sid+'.json');q=a.read(src)
    expected,_=request_from(public_request(records[sid],original_c),label=='structured_only')
    if q!=expected or a.sha(src)!=a.digest(q):raise ValueError('saved exact main projection/request-byte mismatch')
    a.assert_public(q);logical=a.stage_key(sid,cid,label,1);rel='requests/'+label+'/'+cid+'/'+sid+'.json'
    copy(src,output/'public'/rel)
    check=cap[(sid,cid,label)]
    if check['request_sha256']!=a.sha(src) or not check['initial_capacity_ok']:raise ValueError('saved exact request capacity mismatch')
    requests[logical]={'path':rel,'sha256':a.sha(src),'original_source':str(src),'original_source_sha256':a.sha(src)}
    reused_capacity.append(check)
    for stage in ((1,2) if item['family']=='clarification' else (1,)):
     key=a.stage_key(sid,cid,label,stage);stage_rows.append({'scoped_key':scoped_key(key),'worker_key':key,'scope':SCOPE,'sample_id':sid,'group_id':item['group_id'],
      'domain':item['domain'],'family':item['family'],'split':item['split'],'condition_id':cid,'representation':label,'stage':stage,
      'request_sha256':a.sha(src) if stage==1 else None,'executor':'Ashraf','reservation_issued':False,'conditional':stage==2})
    fidelity.append({'sample_id':sid,'condition_id':cid,'representation':label,'request_sha256':a.sha(src),'exact_main_projection':True,'source_record_sha256':item['record_sha256']})
  for cid in ('qwen3_8b_direct','qwen3_32b_awq_on'):
   for item in items:
    sid=item['sample_id'];e=task_view(a.read(output/'public/requests/enriched'/cid/(sid+'.json')));s=task_view(a.read(output/'public/requests/structured_only'/cid/(sid+'.json')))
    e.pop('language_annotations',None)
    if e!=s:raise ValueError('matched underlying task facts/comparison/gap mismatch')
 copy(package/'workers/execution_support.py',output/'public/workers/execution_support.py')
 manifest={'version':VERSION,'scope':SCOPE,'post_core_results_decision':True,'selection_rule':'frozen400 minus exact core sample AND original group; retained pool order, no correctness access',
  'items':items,'core_manifest_sha256':a.sha(prep/'nested-200-manifest.json'),'pool_manifest_sha256':a.sha(prep/'nested-400-manifest.json'),'source_hashes':sourcehashes,
  'counts':{'items':200,'groups':200,'initials':1600,'maximum_supported_continuations':320,'maximum_calls':1920},
  'cells':{d+'/'+f:n for (d,f),n in collections.Counter((r['domain'],r['family']) for r in items).items()},
  'excluded_counts':{k:len(v) for k,v in categories.items()},'excluded_groups':sorted(excluded),'scientific_settings_unchanged':True,'execution_authorized':False,'budget_revision_authorized':False}
 a.put(output/'complement-manifest.json',manifest);a.put(output/'organizer/fidelity.json',fidelity);a.put(output/'organizer/reused-capacity-evidence.json',{'source':str(capacity_path),'sha256':a.sha(capacity_path),'items':reused_capacity,
  'continuation_limits_are_conservative':True,'actual_assistant_history_must_be_checked':True,'worst_allowance_continuation_failures':sum(not r.get('continuation_capacity_ok',True) for r in reused_capacity)})
 public_items=[{k:i[k] for k in ('sample_id','group_id','domain','family','split','candidate_id','candidate_rank','qualified_cell_rank','original_source_sha256','record_sha256')} for i in items]
 public={'version':VERSION,'scope':SCOPE,'items':public_items,'requests':requests,'combinations':[list(x) for x in COMBINATIONS],
  'source_execution_package_manifest_sha256':a.sha(package/'package-manifest.json'),'conditions':{cid:sealed_spec['conditions'][cid] for cid in {c for c,_ in COMBINATIONS}},
  'conditional_policy':'no initial assistant reference; only supported actual first turn with verbatim history and recorded public updates; capacity checked unchanged; unsupported stages unexecuted',
  'original_core_and400_pool_unchanged':True,'execution_enabled':False}
 a.put(output/'public/execution-inputs.json',public);a.put(output/'stage-ownership-plan.json',{'issued':False,'prospective_executor':'Ashraf','scope':SCOPE,'stages':stage_rows,'initials_and_continuations_stay_together':True})
 a.put(output/'authorization-record.json',{'date':datetime.now(timezone.utc).isoformat(),'scope':'offline complement preparation only','post_core_results':True,
  'budget_change_approved':False,'answering_inference_approved':False,'conditional_execution_paragraph_not_adopted':True,
  'proposed_cumulative_ceiling_seconds':{'Ashraf':126000,'Collaborator':100800,'shared':226800},'current_live_allocations':before['allocations'],
  'deadline_utc':DEADLINE,'result_import_cutoff_utc':CUTOFF,'deadline_Chicago':'2026-10-13 06:59 CDT','cutoff_Chicago':'2026-10-12 18:00 CDT',
  'original_12_hour_minimum_writing_reserve_preserved':True})
 a.put(output/'analysis-plan.json',{'version':VERSION,'core_only_items':200,'complement_only_items':200,'combined_items_if_complete':400,'combined_per_family':80,'combined_per_domain_family':20,
  'denominators_fixed':True,'incomplete_execution_is_not_complete400':True,'same200_common_subset_for_nonexpanded_conditions':True,'compare_all_results_regardless_direction':True,
  'procedure':'unchanged main_analysis.assess and paired_intervals; concatenate disjoint item rows then resample union groups, never average CI endpoints',
  'bootstrap_replicates':10000,'bootstrap_seed':20261009,'bootstrap_unit':'paired whole trajectory within domain/family strata; same draws for conditions/representations',
  'union_stratum_draws':20,'primary_scorer_hashes':{n:a.sha(repo/'src/simphysqa'/(n+'.py')) for n in ('spq06','scoring','main_analysis','clarification_evaluation','explanation_evaluation')},
  'reasoning_and_prose_quality_not_inferred':True,'human_ratings':'uncollected'})
 after=ledger_snapshot(ledger)
 if before['table_digests']!=after['table_digests']:raise ValueError('live ledger changed during preparation; preserve outputs and refresh coordination before planning')
 a.put(output/'organizer/ledger-after.json',after);a.put(output/'manifest.json',{'version':VERSION,'files':a.files(output),'no_live_ledger_mutations':True,'inference_calls':0,'simulation_calls':0,'annotation_calls':0})
 return manifest

def validate(output):
 output=Path(output);m=a.read(output/'manifest.json');actual=a.files(output);actual.pop('manifest.json')
 if actual!=m['files']:raise ValueError('complement preparation byte/hash mismatch')
 cm=a.read(output/'complement-manifest.json');public=a.read(output/'public/execution-inputs.json');stages=a.read(output/'stage-ownership-plan.json')['stages']
 if len(stages)!=1920 or len({r['scoped_key'] for r in stages})!=1920 or len(public['requests'])!=1600:raise ValueError('exhaustive exact eight-combination stage coverage')
 if public['execution_enabled'] or cm['execution_authorized']:raise ValueError('offline preparation cannot grant execution')
 for key,entry in public['requests'].items():
  path=a.within(output/'public',entry['path']);q=a.read(path)
  if a.sha(path)!=entry['sha256'] or a.stage_key(q['sample_id'],q['condition_id'],q['input_condition'],1)!=key:raise ValueError('exact request identity')
  a.assert_public(q)
 return {'version':VERSION,'unique_items':200,'initial_requests':1600,'possible_stages':1920,'hashes_verified':len(actual),'inference_calls':0}

def forecast(base,prepared,output,now=None):
 base,prepared,output=map(Path,(base,prepared,output));snapshot=ledger_snapshot(base/'central-main-1.0.0/main.sqlite')
 manifest=a.read(prepared/'complement-manifest.json');items={r['sample_id']:r for r in a.read(base/'main-preparation-1.0.0/nested-200-manifest.json')['items']}
 # Only actual saved measurement fields are inspected; parsing/correctness unused.
 jobs=[p for root in (base/'main-ashraf-1.0.0',base/'restart-execution-1.0.0') for p in (root/'jobs').iterdir()]
 raw={};runtime={};process_counts={};measured_process={};cells=collections.defaultdict(list)
 for job in jobs:
  c=a.read(job/'condition.json');cid=c['condition_id'];label=a.read(job/'execution-context.json')['representation'];combo=(cid,label)
  if combo not in COMBINATIONS:continue
  process_counts[combo]=process_counts.get(combo,0)+1
  if (job/'worker-output/runtime.json').exists():runtime.setdefault(combo,[]).append(a.read(job/'worker-output/runtime.json'))
  if (job/'process-receipt.json').exists():measured_process[combo]=measured_process.get(combo,0)+a.read(job/'process-receipt.json')['elapsed_seconds']
  for p in (job/'worker-output/results').glob('*.json'):
   r=a.read(p);key=a.stage_key(r['sample_id'],cid,label,r['stage'])
   if key in raw:raise ValueError('multiple actual saved outputs for logical key; no score-based choice')
   raw[key]=r
   if r.get('latency_seconds') is not None and r['completion_status'] in ('completed','length_limited'):
    cells[(cid,label,items[r['sample_id']]['family'],r['stage'])].append(r['latency_seconds'])
 estimates=[];worst_stage=0;point_stage=0;load_point=0;reservation_process=0
 for cid,label in COMBINATIONS:
  combo=(cid,label);c=a.read(base/'execution-public-1.1.1/conditions'/f'{cid}.json');limit=c['settings']['max_seconds'];parts=[]
  for family in ('direct','predictive','counterfactual','explanation','clarification'):
   for stage in ((1,2) if family=='clarification' else (1,)):
    values=cells[(cid,label,family,stage)];per=sum(values)/len(values) if values else limit
    parts.append({'family':family,'stage':stage,'planned_calls':40,'observed_calls':len(values),'mean_observed_seconds':per if values else None,
     'measured_total_seconds':sum(values),'forecast_seconds':40*per,'timeout_fallback':not bool(values),'frozen_stage_reservation_seconds':40*limit,'source':'saved actual latency only; no correctness/JSON use'})
  loading=[r['load_seconds'] for r in runtime.get(combo,[]) if r.get('load_seconds') is not None]
  load=5*(sum(loading)/len(loading)) if loading else 5*600
  point=sum(p['forecast_seconds'] for p in parts);point_stage+=point;worst_stage+=240*limit;load_point+=load;reservation_process+=5*600
  stage_total=sum(r.get('total_stage_seconds') or 0 for k,r in raw.items() if k.split('|')[1:3]==[cid,label])
  estimates.append({'condition_id':cid,'representation':label,'parts':parts,'generation_forecast_seconds':point,'loading_forecast_seconds':load,
   'loading_observed_count':len(loading),'actual_processes':process_counts.get(combo,0),'observed_process_lifecycle_seconds':measured_process.get(combo),
   'observed_total_stage_seconds':stage_total,'observed_loading_seconds':sum(loading),'planned_processes_minimum':5,
   'process_reservation_seconds':3000,'stage_reservation_seconds':240*limit,
   'unmeasured':'new groups, response length, unknown original lifecycle and future startup/hash variability; actual routing success unknown; all40 continuations budgeted'})
 ash=snapshot['allocations']['Ashraf'];current=ash['accounted_seconds'];original_unknown=sum(r[2] for r in snapshot['active_or_unknown_processes'] if r[3] is None and r[4]=='interrupted')
 historical_extrapolation=current-original_unknown;reserve=.25*historical_extrapolation;full=historical_extrapolation+reserve
 if now is None:now=datetime.now(timezone.utc)
 cutoff=datetime.fromisoformat(CUTOFF);deadline=datetime.fromisoformat(DEADLINE);available=max(0,(cutoff-now).total_seconds())
 observed_process=sum(r[3] for r in snapshot['table_rows']['processes'] if r[3] is not None and r[4]=='complete')
 controls=sum(r[4] for r in snapshot['table_rows']['control_work'] if r[4] is not None and r[5]=='complete')
 gaps=sum(r[1] for r in snapshot['table_rows']['dispatcher_gaps'])
 # Separate descriptive historical lifecycle overhead; do not add nested loading
 # or stage time a second time. Unknown job031 has no measured lifecycle.
 known_ids={r[0] for r in snapshot['table_rows']['processes'] if r[3] is not None and r[4]=='complete'}
 known_stage_total=sum(r['total_stage_seconds'] for r in raw.values() if r['process_reservation'] in known_ids and r.get('total_stage_seconds') is not None)
 known_loading=sum(r['load_seconds'] for rr in runtime.values() for r in rr if r.get('load_seconds') is not None and r['process_reservation'] in known_ids)
 overhead=max(0,observed_process-known_stage_total-known_loading)
 component_point=point_stage+load_point+overhead+controls+gaps
 component_reserved=1.25*component_point
 result={'component_point_extrapolation_seconds':component_point,'component_plus_reserve_seconds':component_reserved,'component_definition':'family/stage measured means with all possible continuations + planned loading + historical known lifecycle overhead + central overhead + dispatcher gaps; loading/stages not double-counted',
  'version':VERSION,'scope':SCOPE,'forecast_captured_utc':now.isoformat(),'live_ledger_summary':{k:v for k,v in snapshot.items() if k not in ('table_rows','assignments')},
  'condition_family_forecast':estimates,'generation_point_seconds':point_stage,'loading_point_seconds':load_point,'observed_known_process_lifecycle_seconds':observed_process,
  'known_lifecycle_overhead_seconds':overhead,'known_lifecycle_overhead_definition':'known ended process minus its nested total stages and model loading; unknown original process not measured zero',
  'observed_central_overhead_seconds':controls,'observed_dispatcher_gap_seconds':gaps,'historical_point_extrapolation_seconds':historical_extrapolation,
  'historical_point_definition':'live Ashraf cumulative charges minus retained historical interruption bound; includes known execution, all central work and recovery; unknown lifecycle component remains unmeasured',
  'forecast_reserve_fraction':.25,'forecast_reserve_seconds':reserve,'historical_plus_reserve_seconds':full,'hard_execution_bound_is_not_forecast':True,
  'all_stage_timeout_reservations_seconds':worst_stage,'minimum_40_process_reservations_seconds':reservation_process,'central_reservation_design':{'fresh_preparation':600,'per_import_control':600,'imports_minimum':40,'analysis_export':3600},
  'worst_case_upfront_bounds_do_not_fit_proposed_budget':True,'sequential_reservations_required':True,'original_unknown_charge_remains_in_cumulative_accounting':original_unknown,
  'current_ashraf_remaining_seconds':ash['remaining_seconds'],'forecast_shortfall_current_seconds':max(0,full-ash['remaining_seconds']),
  'proposed_allocations_seconds':{'Ashraf':126000,'Collaborator':100800,'shared':226800},'proposed_ashraf_remaining_seconds':126000-current,
  'proposed_forecast_margin_seconds':126000-current-full,'proposed_revision_approved':False,
  'calendar':{'deadline_utc':DEADLINE,'deadline_Chicago':'2026-10-13 06:59 CDT','cutoff_utc':CUTOFF,'cutoff_Chicago':'2026-10-12 18:00 CDT',
   'writing_reserve_seconds':(deadline-cutoff).total_seconds(),'available_until_import_cutoff_seconds':available,
   'point_completion_utc':(now+timedelta(seconds=historical_extrapolation)).isoformat(),'with_reserve_completion_utc':(now+timedelta(seconds=full)).isoformat(),
   'point_fits_cutoff':historical_extrapolation<=available,'reserve_forecast_fits_cutoff':full<=available,'reserve_shortfall_calendar_seconds':max(0,full-available),
   'includes_future_budget_response_wait':False,'unmeasured_future_transfer_and_writeup_time':True,'refresh_required_before_any_launch':True},
  'answer_scores_read':False,'new_inference_calls':0,'collaborator_forecast_not_assumed':True}
 a.put(output,result);return result

if __name__=='__main__':
 p=argparse.ArgumentParser();s=p.add_subparsers(dest='command',required=True)
 q=s.add_parser('prepare')
 for name in ('base','repo','output','historical','audit'):q.add_argument('--'+name,required=True)
 q=s.add_parser('validate');q.add_argument('--output',required=True)
 q=s.add_parser('forecast')
 for name in ('base','prepared','output'):q.add_argument('--'+name,required=True)
 z=p.parse_args()
 if z.command=='prepare':r=prepare(z.base,z.repo,z.output,z.historical,z.audit)
 elif z.command=='validate':r=validate(z.output)
 else:r=forecast(z.base,z.prepared,z.output)
 print(json.dumps({k:r[k] for k in ('version','inference_calls','new_inference_calls','unique_items','initial_requests','scope') if k in r}))
