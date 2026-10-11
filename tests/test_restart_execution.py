"""Synthetic offline fixtures only; no real stages or model execution."""
import json,sqlite3,unittest
from unittest.mock import patch
import test_execution_readiness as fixtures
from simphysqa import execution_adapter as a,main_allocation as allocation,restart_execution as recovery

class Recovery(unittest.TestCase):
 def setUp(self):
  self.f=fixtures.Readiness();self.f.setUp();self.f.ledger.db.close()
  self.base=allocation.Ledger(self.f.root/'FIXTURE.sqlite')
  allocation.install(self.base,{'FIXTURE-EXECUTOR':1000,'COLLABORATOR':240})
  self.original=self.base.reserve(self.f.assignment['id'],'FIXTURE-EXECUTOR',[self.f.key],{self.f.key:a.digest(self.f.q)},self.f.qhash)
  self.base.db.execute("UPDATE processes SET state='interrupted' WHERE id=?",(self.original['id'],))
  self.base.db.execute("UPDATE stages SET state='interrupted' WHERE key=?",(self.f.key,))
  self.freeze={'explicit_post_result_authorization':True,'authorization_text':'OFFLINE FIXTURE ONLY; after result disclosure',
   'executor':'FIXTURE-EXECUTOR','maximum_processes':2,'remaining_at_freeze_seconds':self.base.remaining('FIXTURE-EXECUTOR'),
   'eligible':[{'key':self.f.key,'original_process':self.original['id'],'request_sha256':a.digest(self.f.q)}]}
  recovery.install(self.base,self.freeze);self.r=recovery.Ledger(self.base.path)
 def tearDown(self):self.r.db.close();self.base.db.close();self.f.temp.cleanup()
 def reserve(self):
  process=self.r.reserve_overhead(self.f.assignment['id'],'FIXTURE-EXECUTOR')
  return self.r.reserve(self.f.assignment['id'],'FIXTURE-EXECUTOR',[self.f.key],{self.f.key:a.digest(self.f.q)},self.f.qhash,process=process)
 def test_original_unknown_charge_and_budget_not_released(self):
  with self.assertRaisesRegex(sqlite3.IntegrityError,'executor'):self.reserve()
  self.assertEqual(self.base.used(),610);self.assertEqual(self.base.db.execute('SELECT * FROM stages').fetchone()[1],self.original['id'])
 def enough(self):
  # Test-only fixture allocation chosen before attempts; no production ceiling edit.
  self.base.db.execute('DROP TRIGGER allocations_no_update')
  self.base.db.execute("UPDATE executor_allocations SET ceiling=1200 WHERE owner='FIXTURE-EXECUTOR'")
  self.base.db.execute("UPDATE meta SET v='1500' WHERE k='ceiling'")
  self.base.db.execute("UPDATE executor_allocations SET ceiling=300 WHERE owner='COLLABORATOR'")
  self.base.db.execute("UPDATE processes SET actual=1,state='complete' WHERE id=?",(self.original['id'],))
 def test_single_recovery_attempt_resume_and_original_preservation(self):
  self.enough();before=self.base.db.execute('SELECT * FROM stages').fetchall();t=self.reserve()
  self.assertNotIn(self.f.key,self.r.pending(self.f.assignment['id'],'FIXTURE-EXECUTOR'))
  with self.assertRaisesRegex(ValueError,'never-reserved'):self.r.reserve(self.f.assignment['id'],'FIXTURE-EXECUTOR',[self.f.key],{self.f.key:a.digest(self.f.q)},self.f.qhash)
  self.assertEqual(before,self.base.db.execute('SELECT * FROM stages').fetchall());self.assertNotEqual(t['id'],self.original['id'])
 def test_other_missing_key_and_old_unsupported_continuation_excluded(self):
  self.assertNotIn(self.f.other,self.r.pending(self.f.assignment['id'],'FIXTURE-EXECUTOR'))
  self.assertNotIn(self.f.second,self.r.pending(self.f.assignment['id'],'FIXTURE-EXECUTOR'))
  with self.assertRaises(ValueError):self.r.reserve(self.f.assignment['id'],'FIXTURE-EXECUTOR',[self.f.other],{self.f.other:a.digest(self.f.q_other)},self.f.qhash)
 def test_changed_request_and_unqualified_rejected(self):
  self.enough();p=self.r.reserve_overhead(self.f.assignment['id'],'FIXTURE-EXECUTOR')
  with self.assertRaisesRegex(ValueError,'unqualified'):self.r.reserve(self.f.assignment['id'],'FIXTURE-EXECUTOR',[self.f.key],{self.f.key:a.digest(self.f.q)},'unknown',process=p)
  with self.assertRaisesRegex(ValueError,'exact request'):self.r.reserve(self.f.assignment['id'],'FIXTURE-EXECUTOR',[self.f.key],{self.f.key:'changed'},self.f.qhash,process=p)
 def test_genuine_original_discovery_stops_inference(self):
  self.enough()
  with patch('simphysqa.restart_execution.original_records',return_value={self.f.key:{'raw_output':'saved'}}):
   with self.assertRaisesRegex(ValueError,'genuine saved'):self.reserve()
 def test_combined_conflict_cannot_choose_recovery(self):
  with patch('simphysqa.restart_execution.original_records',return_value={self.f.key:{'raw_output':'original'}}),patch('simphysqa.main_record_index.canonical_records',return_value={self.f.key:{'raw_output':'different'}}):
   with self.assertRaisesRegex(ValueError,'conflicting genuine'):recovery.combined_records(self.r)
 def test_null_history_preserved_new_actual_history_only(self):
  self.enough();first=self.reserve();self.r.settle(first['id'],5,'complete')
  old={'key':self.f.second,'actual_raw':None,'request':None,'status':'unexecuted_conditional','reason':'external interruption'}
  self.base.db.execute('INSERT INTO routes VALUES(?,?)',(self.f.second,a.canonical(old).decode()))
  actual={'raw_output':'  VERBATIM MOCK first turn\n'};q2={**self.f.q,'stage':2,'messages':self.f.q['messages']+[{'role':'assistant','content':actual['raw_output']},{'role':'user','content':'recorded query reply'}]}
  new={'key':self.f.second,'initial_key':self.f.key,'status':'supported','actual_raw':actual['raw_output'],'initial_result_sha256':a.digest(actual),'request':q2,'request_sha256':a.digest(q2)}
  def mocked_route(ledger,key,preparation,output):
   ledger.db.execute('INSERT INTO routes VALUES(?,?)',(self.f.second,a.canonical(new).decode()));a.put(output,new);return new
  with patch('simphysqa.execution_adapter.coordinate_reply',side_effect=mocked_route):recovery.route(self.r,self.f.key,'MOCK-NOT-MAIN',self.f.root/'new-route.json')
  self.assertEqual(json.loads(self.base.db.execute('SELECT body FROM routes').fetchone()[0]),old)
  self.assertEqual(a.read(self.f.root/'new-route.json.history.json')['original_null_response_receipt'],old)
  self.assertIn(self.f.second,self.r.pending(self.f.assignment['id'],'FIXTURE-EXECUTOR'))
  process=self.r.reserve_overhead(self.f.assignment['id'],'FIXTURE-EXECUTOR')
  with patch('simphysqa.execution_adapter.canonical_records',return_value={self.f.key:actual}):
   with self.assertRaisesRegex(ValueError,'exact request'):self.r.reserve(self.f.assignment['id'],'FIXTURE-EXECUTOR',[self.f.second],{self.f.second:'authored substitute'},self.f.qhash,process=process)
   self.r.reserve(self.f.assignment['id'],'FIXTURE-EXECUTOR',[self.f.second],{self.f.second:a.digest(q2)},self.f.qhash,process=process)
  self.assertEqual(q2['messages'][-2]['content'],actual['raw_output'])
 def test_immutable_import_duplicate_conflict_failure_preservation(self):
  self.enough();process=self.r.reserve_overhead(self.f.assignment['id'],'FIXTURE-EXECUTOR')
  jobroot=self.f.root/'recovered';ticket=a.prepare_job(self.r,self.f.assignment['id'],'FIXTURE-EXECUTOR',self.f.qhash,[self.f.key],self.f.bindings,jobroot,process=process)
  context=a.read(jobroot/'execution-context.json');stem='FIXTURE-NOT-MAIN-stage1.json'
  a.put(jobroot/'worker-output/executed-requests'/stem,self.f.q)
  a.put(jobroot/'worker-output/tokenized-prompts'/stem,{'prompt':'MOCK ONLY','token_ids':[1,2]})
  raw={'sample_id':'FIXTURE-NOT-MAIN','condition_id':self.f.cid,'stage':1,'representation':'enriched','stage_key':self.f.key,
   'request_sha256':a.digest(self.f.q),'completion_status':'completed','raw_output':'{"abstained":true}',
   'response_origin':'MOCK_BACKEND_FIXTURE','execution_version':a.VERSION,'cpu_fallback':False,'execution_scope':'main','qualification_status':'task_qualified',
   'termination':{'category':'complete'},'device_memory':{'status':'unavailable','sampled_peak_mib':None},'total_stage_seconds':2,'latency_seconds':1}
  for k in ('qualification_sha256','assignment_sha256','hardware_runtime_sha256','worker_sha256','scientific_condition_sha256','process_reservation'):raw[k]=context[k]
  raw['stage_reservation']=context['stage_reservations'][self.f.key];a.put(jobroot/'worker-output/results'/stem,raw)
  runtime={**{k:context[k] for k in ('qualification_sha256','worker_sha256','process_reservation')},'gpu_name':'FIXTURE GPU','runtime_versions':{'fixture':'1'},'device_uuid':'FIXTURE-GPU',
   'hardware_runtime_observed':{'driver':'fixture','os':'FIXTURE OS','vram_mib':1}}
  a.put(jobroot/'worker-output/runtime.json',runtime);a.put(jobroot/'process-receipt.json',{'elapsed_seconds':5,'state':'complete','process_reservation':ticket['id']})
  out=self.f.root/'returned';a.export_return(jobroot,out)
  one=a.import_return(self.r,out,self.f.root/'immutable');two=a.import_return(self.r,out,self.f.root/'immutable')
  self.assertEqual(one['accepted_keys'],[self.f.key]);self.assertTrue(two['identical_duplicate_transport'])
  raw['raw_output']='DIFFERENT MOCK ONLY';(jobroot/'worker-output/results'/stem).write_bytes(a.canonical(raw))
  a.export_return(jobroot,self.f.root/'other-return');conflict=a.import_return(self.r,self.f.root/'other-return',self.f.root/'immutable')
  self.assertIn(self.f.key,conflict['conflicts']);self.assertEqual(recovery.combined_records(self.r),{})
if __name__=='__main__':unittest.main()
