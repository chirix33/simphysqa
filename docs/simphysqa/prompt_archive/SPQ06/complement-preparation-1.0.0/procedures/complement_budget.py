"""Prospective central budget revision /1.0.0. Never inferred from preparation.

Offline planning is read-only. Apply only after a separate explicit human budget
approval, in the SAME ledger; original ceilings and all charges survive as history.
"""
import argparse,json,math
from datetime import datetime,timezone
from pathlib import Path
from . import execution_adapter as a,main_allocation

VERSION='SPQ06-complement-budget/1.0.0'
PROPOSED={'Ashraf':126000,'Collaborator':100800,'shared':226800}


def validate_approval(ledger,approval):
 if approval.get('explicit_human_budget_approval') is not True or approval.get('conditional_draft') is not False or not approval.get('authorization_text') or not approval.get('authorization_utc'):
  raise ValueError('separate explicit human approval required; conditional draft is not approval')
 if approval.get('new_cumulative_seconds')!=PROPOSED:raise ValueError('exact prospectively reviewed allocation required')
 current=dict(ledger.db.execute('SELECT owner,ceiling FROM executor_allocations'))
 if current!={'Ashraf':72000.0,'Collaborator':100800.0} or float(ledger.meta('ceiling'))!=172800:raise ValueError('current allocation differs; inspect later work, never reset')
 if ledger.used()>226800 or ledger.executor_used('Ashraf')>126000 or ledger.executor_used('Collaborator')>100800:raise ValueError('actual charges exceed proposed limits')
 return current

def apply(ledger,approval):
 current=validate_approval(ledger,approval);before=ledger.summary();event={'version':VERSION,'authorization':approval,'previous':before,'new_cumulative_seconds':PROPOSED,
  'prospective_effective_utc':datetime.now(timezone.utc).isoformat(),'original_charges_preserved':True,'collaborator_allocation_changed':False}
 h=a.digest(event)
 def operation():
  validate_approval(ledger,approval)
  ledger.db.execute('CREATE TABLE IF NOT EXISTS budget_revision_events(hash TEXT PRIMARY KEY,body TEXT NOT NULL,state TEXT NOT NULL)')
  ledger.db.execute('INSERT INTO budget_revision_events VALUES(?,?,?)',(h,a.canonical(event).decode(),'applying'))
  # Replace the immutable-current-value guard ONLY inside this approved atomic
  # migration; original rows/ceilings are in the immutable event above. All
  # process/control reservation guards remain and read the prospective values.
  ledger.db.execute('DROP TRIGGER allocations_no_update')
  ledger.db.execute("UPDATE executor_allocations SET ceiling=126000 WHERE owner='Ashraf' AND ceiling=72000")
  ledger.db.execute("UPDATE meta SET v='226800' WHERE k='ceiling' AND v='172800'")
  ledger.db.execute("UPDATE budget_revision_events SET state='applied' WHERE hash=?",(h,))
  ledger.db.execute("CREATE TRIGGER allocations_no_update BEFORE UPDATE ON executor_allocations BEGIN SELECT RAISE(ABORT,'frozen executor allocation; new explicit budget revision required'); END")
  ledger.db.execute("CREATE TRIGGER budget_revision_no_update BEFORE UPDATE ON budget_revision_events BEGIN SELECT RAISE(ABORT,'immutable budget history'); END")
  ledger.db.execute("CREATE TRIGGER budget_revision_no_delete BEFORE DELETE ON budget_revision_events BEGIN SELECT RAISE(ABORT,'immutable budget history'); END")
  if ledger.executor_used('Collaborator')!=next(x['accounted_seconds'] for x in before['allocations'] if x['executor']=='Collaborator'):raise ValueError('collaborator charges changed')
 ledger.transaction(operation)
 return {'event_sha256':h,'event':event,'current':ledger.summary(),'stages_reserved':0,'inference_calls':0}

if __name__=='__main__':
 p=argparse.ArgumentParser();p.add_argument('command',choices=['inspect','apply']);p.add_argument('--ledger',required=True);p.add_argument('--approval');p.add_argument('--output');p.add_argument('--authorize-budget-revision',action='store_true');z=p.parse_args()
 if z.command=='inspect':
  from .complement_preparation import ledger_snapshot
  r=ledger_snapshot(z.ledger);r={k:v for k,v in r.items() if k not in ('table_rows','assignments')}
 else:
  if not z.authorize_budget_revision or not z.approval or not z.output:raise ValueError('explicit future authorization, receipt and exclusive output required')
  if Path(z.output).exists():raise ValueError('exclusive revision receipt required')
  ledger=main_allocation.Ledger(z.ledger)
  try:r=apply(ledger,a.read(z.approval));a.put(z.output,r)
  finally:ledger.db.close()
 print(json.dumps(r))
