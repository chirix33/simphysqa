"""Authorized exact-key external-restart recovery driver /1.0.0; serial GPU."""
import json,sys,time,traceback
from pathlib import Path
from simphysqa import execution_adapter as a,main_allocation,main_record_index,main_import,restart_execution as recovery,main_execution_queue as queue
BASE=Path('C:/Users/aashraf/.codex/visualizations/2026/10/06/01a1131b-eac2-7a31-afb4-f219a8dd6471/spq06/2026-10-09')
ORIGINAL=BASE/'main-ashraf-1.0.0';RUN=BASE/'restart-execution-1.0.0';PACKAGE=BASE/'execution-public-1.1.1';CENTRAL=BASE/'central-main-1.0.0/main.sqlite';REPO=Path('C:/Users/aashraf/.codex/worktrees/simphysqa/phi-jepa')
SHARD='qwen3_8b_direct--structured_only';SOURCE=BASE/'main-src-1.0.1'
sys.path.insert(0,str(SOURCE))
from main_run import command,wsl,linux,central_verify
# Restore the explicit additive projection after importing the historical driver.
a.canonical_records=recovery.combined_records

def freeze():
 RUN.mkdir(exist_ok=False);ledger=main_allocation.Ledger(CENTRAL)
 before=ledger.summary();control=ledger.reserve_control('Ashraf','authorized restart eligibility/source preservation/saved-output inspection',600);start=time.monotonic()
 try:
  original_receipt=ORIGINAL/'restart-recovery-1.0.0/recovery-receipt.json';receipt=a.read(original_receipt);keys=receipt['interrupted_missing_or_invalid_keys']
  spec=a.read(PACKAGE/'execution-spec.json');job=Path(receipt['original_job']);ticket=a.read(job/'ticket.json');requests=a.read(job/'requests.json')
  original_rows={table:ledger.db.execute('SELECT * FROM '+table).fetchall() for table in ('stages','routes','returns','transports','processes')}
  actual=recovery.original_records(ledger);eligible=[];wanted={k.split('|')[0]+'-stage1.json':k for k in keys};discovered=[];searched=[]
  # Search original jobs, returned/immutable transports and central projections,
  # then all other established SPQ06 artifact roots for exact result filenames.
  for p in BASE.rglob('*.json'):
   if p.name not in wanted or p.parent.name!='results':continue
   raw=a.read(p);key=wanted[p.name]
   if raw.get('condition_id')=='qwen3_8b_direct' and raw.get('representation')=='structured_only' and raw.get('stage')==1:
    searched.append({'path':str(p),'sha256':a.sha(p),'process_reservation':raw.get('process_reservation')})
    if raw.get('process_reservation')==ticket['id']:discovered.append(str(p))
  a.put(RUN/'saved-output-search.json',{'root':str(BASE),'exact_result_candidates':searched,'genuine_original_saved_outputs':discovered,'selection_uses_scores':False})
  if discovered:raise ValueError('genuine original saved outputs discovered; import exact original return before any regeneration: '+str(discovered))
  bykey={a.stage_key(q['sample_id'],q['condition_id'],q['input_condition'],q.get('stage',1)):q for q in requests}
  items={i['sample_id']:i for i in spec['items']}
  for key in keys:
   sid,cid,label,stage=key.split('|');entry=spec['requests'][key];row=ledger.db.execute('SELECT * FROM stages WHERE key=?',(key,)).fetchone()
   if key not in ticket['keys'] or row[1]!=ticket['id'] or row[2]!=entry['sha256'] or a.digest(bykey[key])!=entry['sha256'] or a.sha(PACKAGE/entry['path'])!=entry['sha256'] or key in actual:raise ValueError('exact original missing selection/request/reservation mismatch')
   if (job/'worker-output/results'/(sid+'-stage1.json')).exists():raise ValueError('saved result present; never regenerate')
   eligible.append({'key':key,'sample_id':sid,'group_id':items[sid]['group_id'],'domain':items[sid]['domain'],'family':items[sid]['family'],'split':items[sid]['split'],
    'original_process':ticket['id'],'original_state':row[3],'request_sha256':entry['sha256'],'request_path':entry['path'],'eligibility':'external restart, interrupted reservation, no saved response; no correctness inspection'})
  condition=a.read(PACKAGE/spec['conditions']['qwen3_8b_direct']['path']);allowance=condition['settings']['max_seconds']
  bounds={'initials':35,'maximum_new_supported_continuations':10,'maximum_calls':45,'maximum_processes':2,'stage_allowance_seconds':allowance,
   'process_allowance_seconds':600,'initial_process_bound_seconds':600+35*allowance,'conditional_process_bound_seconds':600+10*allowance,
   'central_freeze_bound_seconds':600,'central_import_verification_bounds_seconds':[600,600],'central_analysis_export_bound_seconds':1800}
  if sum((bounds['initial_process_bound_seconds'],bounds['conditional_process_bound_seconds'],600,1200,1800))>before['allocations'][0]['remaining_seconds']:raise ValueError('conservative full recovery does not fit authorized remaining allocation')
  preserved={str(p):a.sha(p) for root in [ORIGINAL,PACKAGE,BASE/'main-preparation-1.0.0'] for p in root.rglob('*') if p.is_file()}
  preserved.update({str(REPO/'src/simphysqa'/(n+'.py')):a.sha(REPO/'src/simphysqa'/(n+'.py')) for n in ('execution_adapter','execution_support','spq06','scoring','main_analysis','clarification_evaluation','explanation_evaluation')})
  a.put(RUN/'preservation-before.json',preserved);a.put(RUN/'original-ledger-snapshot.json',original_rows)
  freeze={'version':recovery.VERSION,'base_commit':'6ae24f157bfa7fa0fa00be37e00f2b4ea47ef228','executor':'Ashraf','eligible':eligible,'explicit_post_result_authorization':True,
   'authorization_date_local':time.strftime('%Y-%m-%d'),'authorization_recorded_unix_seconds':time.time(),
   'authorization_text':"Ashraf explicitly authorizes recovery of execution missed because of the external workstation restart, superseding the earlier prohibition on reopening only the exact 35 restart-missing Qwen3-8B direct structured-only initials. Supported continuations must derive from actual recovered first responses; no other missing/failed stages may be retried. Same authoritative ledger; original 6600-second charge and all evidence preserved. Remaining Ashraf allocation 14883.368 seconds; collaborator unchanged.",
   'authorization_after_original_results_available':True,'original_recovery_receipt_sha256':a.sha(original_receipt),'original_analysis_sha256':a.sha(ORIGINAL/'delivery-1.0.0/ashraf-fixed-denominator-analysis.json'),
   'remaining_at_freeze_seconds':ledger.remaining('Ashraf'),'original_accounting':before,'maximum_processes':2,'bounds':bounds,
   'worker_sha256':spec['conditions']['qwen3_8b_direct']['worker_sha256'],'package_manifest_sha256':a.sha(PACKAGE/'package-manifest.json'),
   'procedure_sources':a.files(Path(__file__).parent),'central_layer_sha256':a.sha(REPO/'src/simphysqa/restart_execution.py'),
   'request_settings_unchanged':True,'original_unknown_charge_preserved':6600,'conditional_rule':'only ten recovered clarification first turns; unchanged supported actual history, never reserved stage2 only; five previously unsupported requests excluded'}
  a.put(RUN/'eligibility-freeze.json',freeze);recovery.install(ledger,freeze)
  ledger.settle_control(control,time.monotonic()-start);a.put(RUN/'freeze-accounting.json',ledger.summary());print('eligible',len(eligible),'bounds',bounds,'accounting',ledger.summary(),flush=True)
 except BaseException:
  ledger.settle_control(control,time.monotonic()-start,'unknown');raise
 finally:ledger.db.close()

def run():
 if (RUN/'QUEUE-PAUSED.json').exists():raise ValueError('preserved recovery pause; no automatic retry')
 ledger=recovery.Ledger(CENTRAL);freeze=a.read(RUN/'eligibility-freeze.json')
 if a.digest(freeze)!=ledger.authorization_hash:raise ValueError('frozen authorization changed')
 for path,h in freeze['procedure_sources'].items():
  if a.sha(Path(__file__).parent/path)!=h:raise ValueError('driver changed after freeze')
 if a.sha(REPO/'src/simphysqa/restart_execution.py')!=freeze['central_layer_sha256']:raise ValueError('central recovery layer changed')
 assignment=a.read(ORIGINAL/'assignments'/(SHARD+'.json'));bindings=a.read(ORIGINAL/'bindings'/(SHARD+'.json'));qualpath=ORIGINAL/'qualification'/(SHARD+'.json');qual=a.read(qualpath)
 try:
  for stage in (1,2):
   keys=[k for k in ledger.pending(assignment['id'],'Ashraf') if k.endswith('|'+str(stage))]
   if not keys:continue
   if len(keys)>(35 if stage==1 else 10):raise ValueError('scope exceeded')
   if ledger.remaining('Ashraf')<600+len(keys)*freeze['bounds']['stage_allowance_seconds']+600+1800:raise ValueError('remaining allocation prevents conservative reservation')
   name='recovery-stage'+str(stage);a.put(RUN/(name+'-keys.json'),keys);process=ledger.reserve_overhead(assignment['id'],'Ashraf');a.put(RUN/(name+'-overhead-reservation.json'),{'process':process,'authorization_hash':ledger.authorization_hash})
   prepared=False;metadata_start=time.monotonic()
   try:
    out=RUN/'preflights'/name
    command(wsl(bindings,SOURCE/'main_preflight.py',['--package',linux(PACKAGE),'--bindings',linux(ORIGINAL/'bindings'/(SHARD+'.json')),'--qualification',linux(qualpath),'--mapping',linux(ORIGINAL/'mappings'/(SHARD+'.json')),'--keys',linux(RUN/(name+'-keys.json')),'--routes',linux(RUN/'routes'),'--output',linux(out)]),RUN/(name+'-preflight.log'),timeout=600)
    proof=a.read(out/'proof.json');proof['accounted_preflight_seconds']=time.monotonic()-metadata_start;a.put(out/'accounted-proof.json',proof)
    queue.check_queue(ledger,'Ashraf','qwen3_8b_direct')
    job=RUN/'jobs'/name;a.prepare_job(ledger,assignment['id'],'Ashraf',a.digest(qual),keys,bindings,job,proof,process);prepared=True
    a.put(job/'recovery-attempt-link.json',{'version':recovery.VERSION,'authorization_hash':ledger.authorization_hash,'eligibility_freeze_sha256':a.sha(RUN/'eligibility-freeze.json'),
     'original_process':freeze['eligible'][0]['original_process'],'original_stage_keys':keys,'new_process':process,'exception_after_results':True})
    outer=command(wsl(bindings,PACKAGE/'procedures/public_executor.py',['launch','--package',linux(PACKAGE),'--job',linux(job),'--authorize-main']),RUN/(name+'-adapter.log'))
    receipt=a.read(job/'process-receipt.json');preparation=a.read(job/'launch.json')['preparation_elapsed_seconds'];gap=max(0,outer-(receipt['elapsed_seconds']-preparation))
    ledger.add_dispatcher_gap(process,gap,{'outer_seconds':outer,'adapter_receipt_sha256':a.sha(job/'process-receipt.json'),'formula':'outer launch minus adapter interval excluding already-counted preparation'})
    control=ledger.reserve_control('Ashraf','recovery immutable import, actual render/token verification, central joins and routing '+name,600);started=time.monotonic()
    try:
     returned=RUN/'returns'/name;a.export_return(job,returned)
     imported=ledger.transaction(lambda:main_import.import_return(ledger,returned,RUN/'immutable-imports'));a.put(RUN/'import-receipts'/(name+'.json'),imported)
     if imported['conflicts'] or imported['validation_failures'] or set(imported['accepted_keys'])!=set(keys):raise ValueError('recovery return invalid/conflicted; preserve and stop')
     command(wsl(bindings,SOURCE/'main_verify.py',['--package',linux(PACKAGE),'--job',linux(job),'--preflight',linux(out/'render-verification.json'),'--output',linux(RUN/'verification'/(name+'.json'))]),RUN/(name+'-verify.log'),timeout=600)
     central_verify(ledger,keys,RUN/'central-stage-records'/(name+'.json'))
     if stage==1:
      def routes():
       for row in freeze['eligible']:
        if row['family']=='clarification':recovery.route(ledger,row['key'],BASE/'main-preparation-1.0.0',RUN/'routes'/(row['sample_id']+'.json'))
      ledger.transaction(routes)
     ledger.settle_control(control,time.monotonic()-started)
    except BaseException:ledger.settle_control(control,time.monotonic()-started,'unknown');raise
    a.put(RUN/'accounting'/(name+'.json'),ledger.summary());print(name,'accepted',len(keys),'accounting',ledger.summary(),flush=True)
   except BaseException as exc:
    if not prepared:queue.block_startup(ledger,assignment['id'],'Ashraf','qwen3_8b_direct',process,str(exc),time.monotonic()-metadata_start)
    a.put(RUN/'QUEUE-PAUSED.json',{'process':process,'reserved_science':prepared,'reason':repr(exc),'traceback':traceback.format_exc(),'accounting':ledger.summary()});raise
  a.put(RUN/'execution-completion.json',{'recovery_initials':ledger.db.execute("SELECT COUNT(*) FROM stages WHERE key LIKE '%|1'").fetchone()[0],
   'actual_continuations':ledger.db.execute("SELECT COUNT(*) FROM stages WHERE key LIKE '%|2'").fetchone()[0],'routes':[json.loads(r[0]) for r in ledger.db.execute('SELECT body FROM routes')],
   'accounting':ledger.summary(),'original_attempts_preserved':True,'collaborator_calls':0});print('recovery execution complete',flush=True)
 finally:ledger.db.close()

if __name__=='__main__':{'freeze':freeze,'run':run}[sys.argv[1]]()
