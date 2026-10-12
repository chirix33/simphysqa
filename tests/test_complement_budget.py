"""Synthetic budget history/guards; no real main ledger or model execution."""
import json,sqlite3,unittest
import test_execution_readiness as fixtures
from simphysqa import main_allocation as m,complement_budget as b

class Budget(unittest.TestCase):
 def setUp(self):
  self.f=fixtures.Readiness();self.f.setUp();self.f.ledger.db.close();self.l=m.Ledger(self.f.root/'FIXTURE.sqlite')
  self.l.db.execute("UPDATE meta SET v='172800' WHERE k='ceiling'")
  body=self.f.assignment.copy();body['owner']='Ashraf';self.l.db.execute('UPDATE assignments SET owner=?,body=? WHERE id=?',('Ashraf',json.dumps(body),body['id']))
  m.install(self.l,{'Ashraf':72000,'Collaborator':100800})
  self.l.db.execute('INSERT INTO processes VALUES(?,?,?,?,?)',('OFFLINE-UNKNOWN',body['id'],6600,None,'interrupted'))
  c=self.l.reserve_control('Collaborator','OFFLINE FIXTURE control',25);self.l.settle_control(c,10)
  self.approval={'explicit_human_budget_approval':True,'conditional_draft':False,'authorization_text':'OFFLINE ONLY synthetic approval','authorization_utc':'2026-10-12T00:00:00Z','new_cumulative_seconds':b.PROPOSED}
 def tearDown(self):self.l.db.close();self.f.temp.cleanup()
 def test_conditional_draft_never_changes_live_tables(self):
  x={**self.approval,'conditional_draft':True};before=self.l.summary()
  with self.assertRaisesRegex(ValueError,'separate explicit'):b.apply(self.l,x)
  self.assertEqual(self.l.summary(),before)
  self.assertEqual(self.l.db.execute("SELECT name FROM sqlite_master WHERE name='budget_revision_events'").fetchall(),[])
 def test_prospective_history_and_unknown_charge_preserved(self):
  r=b.apply(self.l,self.approval);self.assertEqual(r['event']['previous']['shared_ceiling_seconds'],172800)
  self.assertEqual(self.l.used(),6610);self.assertEqual(self.l.executor_used('Collaborator'),10)
  self.assertEqual(self.l.remaining('Ashraf'),119400);self.assertEqual(self.l.meta('ceiling'),'226800')
  with self.assertRaises(sqlite3.IntegrityError):self.l.db.execute('UPDATE budget_revision_events SET state="changed"')
  with self.assertRaises(sqlite3.IntegrityError):self.l.db.execute('DELETE FROM budget_revision_events')
  with self.assertRaises(sqlite3.IntegrityError):self.l.db.execute('UPDATE executor_allocations SET ceiling=999999')
 def test_double_apply_and_bare_client_overrun_rejected(self):
  b.apply(self.l,self.approval)
  with self.assertRaisesRegex(ValueError,'current allocation differs'):b.apply(self.l,self.approval)
  with self.assertRaises(sqlite3.IntegrityError):self.l.db.execute('INSERT INTO processes VALUES(?,?,?,?,?)',('TOO-MUCH',self.f.assignment['id'],120000,None,'reserved_unknown'))
 def test_collaborator_allocation_cannot_be_changed(self):
  x={**self.approval,'new_cumulative_seconds':{'Ashraf':126000,'Collaborator':99000,'shared':225000}}
  with self.assertRaisesRegex(ValueError,'exact prospectively'):b.apply(self.l,x)
if __name__=='__main__':unittest.main()
