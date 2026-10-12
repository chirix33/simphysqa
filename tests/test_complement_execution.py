"""Synthetic registry/job fixtures only; no real main reservations or inference."""
import json,unittest
from unittest.mock import patch
import test_execution_readiness as fixtures
from simphysqa import execution_adapter as a,main_allocation as m,complement_budget as budget,complement_execution as e
from simphysqa.complement_preparation import SCOPE

class Extension(unittest.TestCase):
 def setUp(self):
  self.f=fixtures.Readiness();self.f.setUp();self.f.ledger.db.close();self.l=m.Ledger(self.f.root/'FIXTURE.sqlite')
  self.l.db.execute("UPDATE meta SET v='172800' WHERE k='ceiling'")
  body=self.f.assignment.copy();body['owner']='Ashraf';self.l.db.execute('UPDATE assignments SET owner=?,body=? WHERE id=?',('Ashraf',json.dumps(body),body['id']))
  m.install(self.l,{'Ashraf':72000,'Collaborator':100800})
  spec=json.loads(self.l.meta('spec'));spec['items']=[{'sample_id':'FIXTURE-NOT-MAIN','group_id':'OLD-FIXTURE'}];self.l.db.execute("UPDATE meta SET v=? WHERE k='spec'",(json.dumps(spec),))
  self.prep=self.f.root/'PREPARED-NOT-MAIN';self.prep.mkdir();self.sid='FIXTURE-COMPLEMENT';self.key=a.stage_key(self.sid,self.f.cid,'enriched',1)
  self.q={**self.f.q,'sample_id':self.sid};a.put(self.prep/'public/request.json',self.q)
  a.put(self.prep/'complement-manifest.json',{'items':[{'sample_id':self.sid,'group_id':'NEW-FIXTURE'}]})
  a.put(self.prep/'public/execution-inputs.json',{'requests':{self.key:{'path':'request.json','sha256':a.digest(self.q)}},'source_execution_package_manifest_sha256':self.l.meta('package_hash')})
  a.put(self.prep/'stage-ownership-plan.json',{'stages':[{'condition_id':self.f.cid,'representation':'enriched','worker_key':self.key}]})
  a.put(self.prep/'authorization-record.json',{'result_import_cutoff_utc':'2099-01-01T00:00:00+00:00'})
  a.put(self.prep/'manifest.json',{'fixture_only':True})
  qual={**self.f.qual,'executor_id':'Ashraf'};self.qhash=a.digest(qual);self.l.db.execute('INSERT INTO qualifications VALUES(?,?)',(self.qhash,a.canonical(qual).decode()))
  self.approval={'explicit_human_complement_execution':True,'conditional_draft':False,'authorization_text':'OFFLINE ONLY synthetic execution approval'}
 def tearDown(self):self.l.db.close();self.f.temp.cleanup()
 def revise(self):budget.apply(self.l,{'explicit_human_budget_approval':True,'conditional_draft':False,'authorization_text':'OFFLINE ONLY','authorization_utc':'2026-10-12T00:00:00Z','new_cumulative_seconds':budget.PROPOSED})
 def register(self):
  with patch.object(e,'COMBINATIONS',[(self.f.cid,'enriched')]):return e.register(self.l,self.prep,self.approval)
 def test_preparation_or_conditional_paragraph_cannot_issue(self):
  with self.assertRaisesRegex(ValueError,'separate explicit'):e.register(self.l,self.prep,{'conditional_draft':True})
  with self.assertRaisesRegex(ValueError,'budget revision'):self.register()
  self.assertEqual(self.l.db.execute("SELECT name FROM sqlite_master WHERE name='complement_registry'").fetchall(),[])
 def test_expired_frozen_cutoff_stops_registration(self):
  self.revise();(self.prep/'authorization-record.json').write_bytes(a.canonical({'result_import_cutoff_utc':'2000-01-01T00:00:00+00:00'}))
  with self.assertRaisesRegex(ValueError,'cutoff passed'):self.register()
  self.assertEqual(self.l.db.execute("SELECT name FROM sqlite_master WHERE name='complement_registry'").fetchall(),[])
 def test_calendar_revision_requires_dated_explicit_approval(self):
  self.revise();self.approval['result_import_cutoff_utc']='2099-01-02T00:00:00+00:00'
  with self.assertRaisesRegex(ValueError,'calendar revision'):self.register()
  self.approval.update(explicit_human_calendar_revision=True,authorization_utc='2026-10-12T07:38:00Z')
  body=self.register();self.assertEqual(body['cutoff_utc'],'2099-01-02T00:00:00+00:00')
  self.assertEqual(body['original_cutoff_utc'],'2099-01-01T00:00:00+00:00')
 def test_actual_history_only_complement_routing(self):
  from contextlib import nullcontext
  self.revise();self.register();ledger=e.Ledger(self.l.path)
  try:
   record={'MOCK_ONLY':True};item={'sample_id':self.sid,'group_id':'NEW-FIXTURE','family':'clarification','private_record':'private/mock.json','record_sha256':a.digest(record)}
   (self.prep/'complement-manifest.json').write_bytes(a.canonical({'items':[item]}))
   ledger.registry['selected_complement_sha256']=a.sha(self.prep/'complement-manifest.json')
   organizer=self.f.root/'ORGANIZER-MOCK';a.put(organizer/'private/mock.json',record)
   a.put(organizer/'conditions'/(self.f.cid+'.json'),{'MOCK_ONLY':True});a.put(organizer/'private/generation-scope.json',{'candidates':[],'excluded_groups':[]})
   ledger.registry['spec']['conditions'][self.f.cid]['original_sha256']=a.sha(organizer/'conditions'/(self.f.cid+'.json'))
   actual={'completion_status':'completed','raw_output':'  ACTUAL MOCK FIRST TURN\n'}
   def continuation(record,condition,raw,response,structured):
    self.assertEqual(raw,actual['raw_output'])
    return {'messages':[{'role':'assistant','content':raw},{'role':'user','content':'RECORDED MOCK REPLY'}]}, {'status':'recorded_reply_routed'}
   with patch.object(ledger,'check'),patch.object(a,'canonical_records',return_value={self.key:actual}),patch('simphysqa.spq06.parse_answer',return_value=({'MOCK_ONLY':True},{})),patch('simphysqa.main_public.continuation',side_effect=continuation),patch('simphysqa.heldout_scope.formal_scope',return_value=nullcontext()):
    result=e.route(ledger,self.key,organizer,self.f.root/'mock-route.json')
   self.assertEqual(result['actual_raw'],actual['raw_output']);self.assertEqual(result['request']['messages'][-2]['content'],actual['raw_output'])
   self.assertEqual(self.l.db.execute('SELECT COUNT(*) FROM routes').fetchone()[0],0)
   self.assertEqual(ledger.db.execute('SELECT COUNT(*) FROM routes').fetchone()[0],1)
  finally:ledger.db.close()
 def test_central_registry_preserves_requests_and_original_stage_table(self):
  self.revise();self.register();ledger=e.Ledger(self.l.path)
  try:
   assignment=ledger.issue('Ashraf',[SCOPE+'::'+self.f.cid+'--enriched'])
   before=self.l.db.execute('SELECT * FROM stages').fetchall()
   with patch('simphysqa.execution_adapter.verify_preflight',return_value=None):ticket=e.prepare_job(ledger,assignment['id'],'Ashraf',self.qhash,[self.key],self.f.bindings,self.f.root/'EXTENSION-JOB')
   self.assertEqual(a.read(self.f.root/'EXTENSION-JOB/requests.json'),[self.q])
   self.assertEqual(before,self.l.db.execute('SELECT * FROM stages').fetchall())
   self.assertEqual(ledger.db.execute('SELECT key FROM stages').fetchall(),[(self.key,)])
   self.assertNotIn(self.key,ledger.pending(assignment['id'],'Ashraf'))
   self.assertEqual(a.read(self.f.root/'EXTENSION-JOB/complement-scope-link.json')['stage_keys'],[SCOPE+'|'+self.key])
   with self.assertRaisesRegex(ValueError,'collaborator'):ledger.issue('Collaborator',[SCOPE+'::'+self.f.cid+'--enriched'])
  finally:ledger.db.close()
if __name__=='__main__':unittest.main()
