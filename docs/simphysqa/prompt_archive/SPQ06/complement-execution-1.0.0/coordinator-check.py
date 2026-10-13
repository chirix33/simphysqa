import sys,time,json
from pathlib import Path
B=Path('C:/Users/aashraf/.codex/visualizations/2026/10/06/01a1131b-eac2-7a31-afb4-f219a8dd6471/spq06/2026-10-09');S=B/'complement-live-src-1.0.1';RUN=B/'complement-execution-1.0.0'
sys.path.insert(0,str(S));import complement_run as driver
from simphysqa import complement_execution as c,execution_adapter as a,main_record_index,main_execution_queue as queue
ledger=c.Ledger(B/'central-main-1.0.0/main.sqlite');control=ledger.reserve_control('Ashraf','coordinator exact-config repair; saved first return scoring/routing and first-batch integrity verification; no inference',600);start=time.monotonic()
try:
 pause=a.read(RUN/'QUEUE-PAUSED.json')
 if 'FileNotFoundError' not in pause['reason'] or 'clarification_rubric.json' not in pause['reason']:raise ValueError('repair narrowly scoped to documented coordinator config omission')
 queue.check_queue(ledger,'Ashraf','qwen3_8b_direct')
 keys=a.read(RUN/'key-batches/043--qwen3_8b_direct--enriched--stage1.json')
 original=a.read(RUN/'import-receipts/043--qwen3_8b_direct--enriched--stage1.json')
 if original['validation_failures'] or original['conflicts'] or set(original['accepted_keys'])!=set(keys):raise ValueError('first actual import integrity failed')
 checks=a.read(RUN/'verification/043--qwen3_8b_direct--enriched--stage1.json')
 if len(checks['actual_stages'])!=50:raise ValueError('actual token/measurement verification incomplete')
 actual=main_record_index.canonical_records(ledger)
 if not set(keys)<=set(actual):raise ValueError('actual first records missing')
 old=S.parent/'complement-live-src-1.0.0/src/simphysqa'
 for p in (S/'src/simphysqa').rglob('*'):
  if p.is_file() and p.suffix!='.pyc' and '__pycache__' not in p.parts:
   if a.sha(p)!=a.sha(old/p.relative_to(S/'src/simphysqa')):raise ValueError('scientific source changed during config repair')
 configuration={}
 repo=Path('C:/Users/aashraf/.codex/worktrees/simphysqa/phi-jepa')
 for p in (S/'configs/simphysqa').rglob('*'):
  if p.is_file():
   source=repo/'configs/simphysqa'/p.relative_to(S/'configs/simphysqa')
   if a.sha(p)!=a.sha(source):raise ValueError('configuration substitution')
   configuration[str(p)]=a.sha(p)
 output=RUN/'central-stage-records-repair-1.0.1/043.json';driver.central_verify(ledger,keys,output)
 def routes():
  for k in keys:
   item=next(r for r in ledger.registry['spec']['items'] if r['sample_id']==k.split('|')[0])
   if item['family']=='clarification':c.route(ledger,k,B/'main-preparation-1.0.0',RUN/'routes-1.0.1/qwen3_8b_direct--enriched'/(item['sample_id']+'.json'))
 ledger.transaction(routes)
 identities={str(p):a.sha(p) for p in S.rglob('*') if p.is_file() and p.suffix!='.pyc' and '__pycache__' not in p.parts}
 a.put(RUN/'orchestration-overlay-1.0.1.json',{'version':'1.0.1','identities':identities,'unchanged_scientific_sources':True,'exact_configurations_restored':configuration,'old_snapshot_preserved':True,'no_inference_repeated':True})
 a.put(RUN/'first-main-batch-integrity.json',{'passed':True,'name':'043--qwen3_8b_direct--enriched--stage1','initials':50,'import_receipt_sha256':a.sha(RUN/'import-receipts/043--qwen3_8b_direct--enriched--stage1.json'),'actual_token_checks_sha256':a.sha(RUN/'verification/043--qwen3_8b_direct--enriched--stage1.json'),'central_scoring_join_sha256':a.sha(output),'main_scope':True,'complement_scope':c.SCOPE,'accuracy_not_gate':True,'coordinator_dependency_repair_only':True})
 ledger.settle_control(control,time.monotonic()-start)
 a.put(RUN/'coordinator-repair-disposition-1.0.1.json',{'original_pause_sha256':a.sha(RUN/'QUEUE-PAUSED.json'),'original_failed_control_untouched':True,'scope':'coordinator dependency packaging only; no startup/runtime integrity failure','first_batch_verified':True,'new_snapshot':str(S),'overlay_sha256':a.sha(RUN/'orchestration-overlay-1.0.1.json'),'repeat_answering_calls':0,'repair_control':control,'seconds':time.monotonic()-start,'accounting':ledger.summary()})
 print(json.dumps({'first_integrity_passed':True,'initials':50,'routes':ledger.db.execute('SELECT COUNT(*) FROM routes').fetchone()[0],'repeat_calls':0,'accounting':ledger.summary()}))
except BaseException:
 ledger.settle_control(control,time.monotonic()-start,'unknown');raise
finally:ledger.db.close()