"""Separately versioned CENTRAL complement adapter /1.0.0.

No automatic launch. Registration/issuance require future explicit execution AND
recorded revised budget. Workers/public package remain sealed1.1.1. Current
preparation calls only dry_plan; fixture tests alone exercise writes.
"""
import argparse,json,re,types,uuid
from datetime import datetime,timezone
from pathlib import Path
from . import execution_adapter as a,main_allocation,main_record_index,main_import
from .complement_preparation import SCOPE,COMBINATIONS,validate,ledger_snapshot

VERSION='SPQ06-complement-central/1.0.0'

class Connection:
 def __init__(self,db):self.original=db
 def execute(self,sql,args=()):
  for table in ('stages','routes','returns','transports'):sql=re.sub(r'\b'+table+r'\b','complement_'+table,sql)
  return self.original.execute(sql,args)
 def __getattr__(self,k):return getattr(self.original,k)


def register(ledger,prepared,approval):
 if approval.get('explicit_human_complement_execution') is not True or approval.get('conditional_draft') is not False or not approval.get('authorization_text'):
  raise ValueError('separate explicit execution authorization required; conditional paragraph not adopted')
 if ledger.meta('fixture')!='True':validate(prepared)
 allocations=dict(ledger.db.execute('SELECT owner,ceiling FROM executor_allocations'))
 if allocations!={'Ashraf':126000.0,'Collaborator':100800.0} or float(ledger.meta('ceiling'))!=226800 or not ledger.db.execute("SELECT 1 FROM budget_revision_events WHERE state='applied'").fetchone():
  raise ValueError('approved prospective central budget revision must precede any extension issue')
 prepared=Path(prepared);cm=a.read(prepared/'complement-manifest.json');public=a.read(prepared/'public/execution-inputs.json');old=json.loads(ledger.meta('spec'))
 if {r['sample_id'] for r in old['items']}&{r['sample_id'] for r in cm['items']} or {r['group_id'] for r in old['items']}&{r['group_id'] for r in cm['items']}:raise ValueError('core/complement identity overlap')
 if public['source_execution_package_manifest_sha256']!=ledger.meta('package_hash'):raise ValueError('sealed package changed')
 spec={**old,'items':cm['items'],'requests':{k:{**r,'path':str((prepared/'public'/r['path']).resolve())} for k,r in public['requests'].items()},
  'complement_manifest_sha256':a.sha(prepared/'complement-manifest.json'),'scope':SCOPE,'shards':[]}
 stages=a.read(prepared/'stage-ownership-plan.json')['stages']
 for cid,label in COMBINATIONS:
  spec['shards'].append({'shard_id':SCOPE+'::'+cid+'--'+label,'owner':None,'keys':[r['worker_key'] for r in stages if (r['condition_id'],r['representation'])==(cid,label)]})
 cutoff=a.read(prepared/'authorization-record.json')['result_import_cutoff_utc']
 if datetime.now(timezone.utc)>=datetime.fromisoformat(cutoff):raise ValueError('frozen import cutoff passed; no implicit calendar revision')
 db=ledger.db
 db.executescript("""
 CREATE TABLE complement_registry(scope TEXT PRIMARY KEY,body TEXT NOT NULL);
 CREATE TABLE complement_stages(key TEXT PRIMARY KEY,process TEXT NOT NULL REFERENCES processes(id),request_hash TEXT NOT NULL,state TEXT NOT NULL);
 CREATE TABLE complement_routes(key TEXT PRIMARY KEY,body TEXT NOT NULL);
 CREATE TABLE complement_returns(key TEXT NOT NULL,artifact TEXT NOT NULL,source TEXT NOT NULL,valid INTEGER NOT NULL,reason TEXT,PRIMARY KEY(key,artifact));
 CREATE TABLE complement_transports(id TEXT PRIMARY KEY,body TEXT NOT NULL);
 CREATE TRIGGER complement_registry_no_update BEFORE UPDATE ON complement_registry BEGIN SELECT RAISE(ABORT,'immutable complement authorization'); END;
 CREATE TRIGGER complement_registry_no_delete BEFORE DELETE ON complement_registry BEGIN SELECT RAISE(ABORT,'immutable complement authorization'); END;
 """)
 body={'version':VERSION,'scope':SCOPE,'prepared':str(prepared.resolve()),'manifest_sha256':a.sha(prepared/'manifest.json'),'spec':spec,'authorization':approval,'cutoff_utc':cutoff,
  'selected_complement_sha256':a.sha(prepared/'complement-manifest.json'),'stage_namespace':'scope|sample_id|condition_id|representation|stage; worker four-part keys remain unchanged',
  'sealed_package_hash':ledger.meta('package_hash')}
 ledger.db.execute('INSERT INTO complement_registry VALUES(?,?)',(SCOPE,a.canonical(body).decode()));return body

class Ledger(main_allocation.Ledger):
 def __init__(self,path):
  super().__init__(path);self.db=Connection(self.db)
  row=self.db.execute('SELECT body FROM complement_registry WHERE scope=?',(SCOPE,)).fetchone()
  if row is None:raise ValueError('explicit complement registration required')
  self.registry=json.loads(row[0])
 def transaction(self,operation):
  def guarded():
   with main_record_index.transaction_snapshot(self):return operation()
  return super().transaction(guarded)
 def meta(self,key):return a.canonical(self.registry['spec']).decode() if key=='spec' else super().meta(key)
 def check(self):
  if a.sha(Path(self.registry['prepared'])/'manifest.json')!=self.registry['manifest_sha256'] or a.sha(Path(self.registry['prepared'])/'complement-manifest.json')!=self.registry['selected_complement_sha256']:raise ValueError('frozen complement changed')
  if datetime.now(timezone.utc)>=datetime.fromisoformat(self.registry['cutoff_utc']):raise ValueError('import/write-up cutoff; stop further issue')
 def issue(self,owner,shards):
  self.check()
  if owner!='Ashraf':raise ValueError('collaborator conditions are outside complement authorization')
  return super().issue(owner,shards)
 def reserve(self,*args,**kwargs):
  self.check()
  keys=kwargs.get('keys',args[2] if len(args)>2 else [])
  spec=self.registry['spec'];package=Path(super().meta('package'))
  bound=600+sum(a.read(package/spec['conditions'][k.split('|')[1]]['path'])['settings']['max_seconds'] for k in keys)
  remaining=(datetime.fromisoformat(self.registry['cutoff_utc'])-datetime.now(timezone.utc)).total_seconds()
  if bound+600>remaining:raise ValueError('conservative batch/import bound exceeds frozen cutoff; shrink never-reserved batch by time only')
  return super().reserve(*args,**kwargs)

def prepare_job(ledger,*args,**kwargs):
 """Exact sealed prepare code, with central request-registry read injection only.

The public validation function retains its original module globals and validates
ONLY the unchanged sealed package. Scientific condition/worker/rendering code is
unchanged. The read hook is restricted to the sealed spec path during preparation.
 """
 ledger.check();package=Path(ledger.meta('package'));spec=ledger.registry['spec'];original_read=a.read
 def read(path):return spec if Path(path).resolve()==(package/'execution-spec.json').resolve() else original_read(path)
 globals_={**a.prepare_job.__globals__,'read':read}
 function=types.FunctionType(a.prepare_job.__code__,globals_,a.prepare_job.__name__,a.prepare_job.__defaults__,a.prepare_job.__closure__)
 ticket=function(ledger,*args,**kwargs)
 output=Path(args[5] if len(args)>5 else kwargs['output'])
 context=a.read(output/'execution-context.json')
 context.update(complement_scope=SCOPE,complement_registry_sha256=a.digest(ledger.registry),complement_manifest_sha256=ledger.registry['selected_complement_sha256'])
 # Extra context is provenance only; never a model message or generation option.
 (output/'execution-context.json').write_bytes(a.canonical(context))
 a.put(output/'complement-scope-link.json',{'version':VERSION,'scope':SCOPE,'registry_sha256':a.digest(ledger.registry),'manifest_sha256':ledger.registry['selected_complement_sha256'],
  'process_reservation':ticket['id'],'stage_keys':[SCOPE+'|'+k for k in ticket['keys']],'sealed_prepare_source_sha256':a.sha(Path(a.__file__))})
 return ticket

def import_return(ledger,source,root):
 # Same immutable transport, conflict, hardware/request/reservation/history checks.
 # Plain historical import has no matching original-stage reservation for these
 # keys and cannot accept extension responses as core outputs.
 receipt=main_import.import_return(ledger,source,root)
 path=Path(receipt['source_root']);context=a.read(path/'execution-context.json') if (path/'execution-context.json').exists() else {}
 if (context.get('complement_scope'),context.get('complement_registry_sha256'),context.get('complement_manifest_sha256'))!=(SCOPE,a.digest(ledger.registry),ledger.registry['selected_complement_sha256']):
  reason='complement namespace/registry/manifest provenance invalid; source bytes preserved'
  ledger.db.execute('UPDATE returns SET valid=0,reason=? WHERE source=?',(reason,str(path)))
  receipt={**receipt,'accepted_keys':[],'validation_failures':receipt['validation_failures']+[{'source':str(path),'reason':reason}]}
  a.put(Path(root)/('scope-disposition-'+str(uuid.uuid4())+'.json'),receipt)
 return receipt

def route(ledger,key,preparation,output):
 ledger.check()
 if key.split('|')[0] not in {r['sample_id'] for r in ledger.registry['spec']['items']}:raise ValueError('complement first response only')
 # Legacy guard verifies the preserved original core source pin; the new registry
 # separately pins the exact complement manifest/item set and private record hash.
 return a.coordinate_reply(ledger,key,preparation,output)

def dry_plan(prepared,output):
 prepared,output=Path(prepared),Path(output);validate(prepared);cm=a.read(prepared/'complement-manifest.json');public=a.read(prepared/'public/execution-inputs.json');items=cm['items'];batches=[]
 for cid,label in COMBINATIONS:
  condition=a.read(prepared/'public/conditions'/f'{cid}.json');allowance=condition['settings']['max_seconds']
  for start in range(0,200,50):
   keys=[a.stage_key(r['sample_id'],cid,label,1) for r in items[start:start+50]]
   batches.append({'condition_id':cid,'representation':label,'stage':1,'keys':keys,'scoped_keys':[SCOPE+'|'+k for k in keys],
    'maximum_initials':50,'process_reservation_seconds':600+50*allowance,'central_import_reservation_seconds':600,'reserved':False})
  keys=[a.stage_key(r['sample_id'],cid,label,2) for r in items if r['family']=='clarification']
  batches.append({'condition_id':cid,'representation':label,'stage':2,'possible_keys':keys,'possible_scoped_keys':[SCOPE+'|'+k for k in keys],
   'eligibility':'supported recorded reply from imported actual first response; never-reserved only','maximum_calls':40,
   'maximum_process_reservation_seconds':600+40*allowance,'central_import_reservation_seconds':600,'reserved':False})
 plan={'version':VERSION,'scope':SCOPE,'batches':batches,'authorization_required':True,'execution_started':False,'assignment_issued':False,
  'first_normal_batch':'qwen3_8b_direct enriched, first50 manifest-order initials; import and exact integrity/scoring-join check before other issue; not an accuracy gate',
  'frozen_sequence':[cid+'--'+label for cid,label in COMBINATIONS],'dynamic_batch_shrink':'by remaining executor/shared budget and remaining calendar bound only; never correctness',
  'fresh_preflight_requirements':['exact artifact/template/runtime/hardware pins','numeric CUDA index-to-UUID mapping','constrained cache symlinks','exact vLLM ModelConfig where applicable','actual request render/token capacity','scope/assignment/configuration/worker hashes'],
  'single_attempt':'only never-reserved logical complement stages; unknown work retains bound; no scope alias retry',
  'startup_queue':'pause related condition representations after shared startup incompatibility; no automatic unblock',
  'timing_accounting':'full preparation/preflight/loading/process/stages/teardown charged once; loading/stage metrics nested; central imports/analysis separately reserved',
  'importer':'complement ledger alias+unchanged main immutable importer; identical transports once, conflicting artifacts block key/conditional pending explicit disposition',
  'final_analysis':'core-only200, complement-only200, combined400 only complete; unchanged assess/paired_intervals, seed20261009,10000 reps,20 draws/union cell; keep200 common subset for unexpanded conditions',
  'future_budget_apply_command':'python -m simphysqa.complement_budget apply --ledger <SAME main.sqlite> --approval <actual explicit approval.json> --output <exclusive receipt.json> --authorize-budget-revision',
  'fresh_public_executor_launch_command':'<pinned interpreter> <sealed package>/procedures/public_executor.py launch --package <sealed package> --job <new centrally issued complement job> --authorize-main',
  'no_gpu_launcher_in_this_plan':True}
 a.put(output,plan);return plan

if __name__=='__main__':
 p=argparse.ArgumentParser();s=p.add_subparsers(dest='command',required=True)
 q=s.add_parser('dry-plan');q.add_argument('--prepared',required=True);q.add_argument('--output',required=True)
 q=s.add_parser('register')
 for n in ('ledger','prepared','approval','output'):q.add_argument('--'+n,required=True)
 q.add_argument('--authorize-complement',action='store_true')
 q=s.add_parser('issue-all')
 for n in ('ledger','output'):q.add_argument('--'+n,required=True)
 q=s.add_parser('prepare-job')
 for n in ('ledger','assignment','qualification','keys','bindings','output','preflight','process'):q.add_argument('--'+n,required=True)
 q=s.add_parser('import')
 for n in ('ledger','source','output'):q.add_argument('--'+n,required=True)
 q=s.add_parser('route')
 for n in ('ledger','key','preparation','output'):q.add_argument('--'+n,required=True)
 q=s.add_parser('reserve-overhead')
 for n in ('ledger','assignment','condition','representation','output'):q.add_argument('--'+n,required=True)
 z=p.parse_args()
 if z.command=='dry-plan':r=dry_plan(z.prepared,z.output)
 elif z.command=='register':
  if not z.authorize_complement or Path(z.output).exists():raise ValueError('future explicit authorization and exclusive receipt required')
  ledger=main_allocation.Ledger(z.ledger)
  try:r=register(ledger,z.prepared,a.read(z.approval));a.put(z.output,r)
  finally:ledger.db.close()
 else:
  ledger=Ledger(z.ledger)
  try:
   if z.command=='issue-all':
    if Path(z.output).exists():raise ValueError('exclusive assignment output')
    r=ledger.issue('Ashraf',[x['shard_id'] for x in ledger.registry['spec']['shards']]);a.put(z.output,r)
   elif z.command=='reserve-overhead':
    from .main_execution_queue import reserve_overhead
    ledger.check();r=reserve_overhead(ledger,z.assignment,'Ashraf',z.condition,z.representation);a.put(z.output,r)
   elif z.command=='prepare-job':r=prepare_job(ledger,z.assignment,'Ashraf',z.qualification,a.read(z.keys),a.read(z.bindings),z.output,a.read(z.preflight),z.process)
   elif z.command=='import':r=ledger.transaction(lambda:import_return(ledger,z.source,z.output))
   else:r=ledger.transaction(lambda:route(ledger,z.key,z.preparation,z.output))
  finally:ledger.db.close()
 print(json.dumps(r))
