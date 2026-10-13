"""Offline software probes. Saved first turns are read-only; stage2 mocks are fixtures."""
import copy
import hashlib
import json
import os
import sqlite3
import tempfile
import time
import unittest
import zipfile
from pathlib import Path
from unittest.mock import patch

from simphysqa import execution_adapter as a, main_allocation, main_record_index as index
from simphysqa import native_reconciliation as native, native_remote as remote

ROOT = Path(os.environ.get('SIMPHYSQA_NATIVE_TEST_TEMP_ROOT', tempfile.gettempdir()))
BASE = Path(os.environ.get('SIMPHYSQA_NATIVE_TEST_BASE', 'native-test-inputs-not-configured'))
SOURCE = Path(os.environ.get('SIMPHYSQA_NATIVE_TEST_METADATA', 'native-metadata-not-configured.zip'))
RAW = Path(os.environ.get('SIMPHYSQA_NATIVE_TEST_RAW', str(SOURCE.with_name('SimPhysQA-results-600.zip'))))
PACKAGE = Path(os.environ.get('SIMPHYSQA_NATIVE_TEST_PACKAGE', str(BASE/'execution-public-1.1.1')))
FIRST = 'spq-clarification-cc02e01f8d454b2374dd51c6|deepseek_r1_distill_qwen32b|enriched|1'


@unittest.skipUnless(SOURCE.is_file() and PACKAGE.is_dir(), 'saved native audit inputs not configured')
class Native(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory(dir=ROOT)
        self.root = Path(self.tmp.name)
        a.Ledger.create(self.root/'fixture.sqlite', PACKAGE, fixture=True, ceiling=226800).db.close()
        self.ledger = main_allocation.Ledger(self.root/'fixture.sqlite')
        main_allocation.install(self.ledger, {'Ashraf':126000,'Collaborator':100800})
        self.auth = {'explicit_human_native_reconciliation':True,'authorization_text':'SYNTHETIC TEST AUTHORITY ONLY',
                     'native_archive_sha256':a.sha(SOURCE),'original_raw_archive_sha256':a.sha(RAW),
                     'unchanged_budgets':native.budgets(self.ledger)}

    def tearDown(self):
        self.ledger.db.close()
        self.tmp.cleanup()

    def reconcile(self):
        return native.reconcile(self.ledger,SOURCE,RAW,self.auth,self.root/'immutable')

    def route(self):
        self.ledger.db.execute('BEGIN IMMEDIATE')
        try:
            with index.transaction_snapshot(self.ledger):
                r=a.coordinate_reply(self.ledger,FIRST,BASE/'main-preparation-1.0.0',self.root/'route.json')
            self.ledger.db.execute('COMMIT')
            return r
        except BaseException:
            self.ledger.db.execute('ROLLBACK');raise

    def issue(self):
        return native.issue(self.ledger,FIRST[:-1]+'2',self.root/'issued.json','TEST-EXECUTOR', '2099-01-01T00:00:00+00:00')

    def job(self):
        self.reconcile();route=self.route();issue=self.issue()
        registry=json.loads(self.ledger.db.execute('SELECT body FROM native_registry').fetchone()[0])
        seed=registry['seed_metadata']['deepseek_r1_distill_qwen32b'];c=seed['condition'];hw=seed['context']['hardware_runtime']
        return {'issue':issue,'condition':c,'request':route['request'],'actual_first_response':route['actual_raw'],
                'bindings':{'interpreter':c['local_python'],'cuda_visible_devices':'0','nvidia_smi':seed['context']['nvidia_smi']},
                'worker_sha256':seed['context']['worker_sha256'],'scientific_condition_sha256':seed['context']['scientific_condition_sha256'],
                'support_sha256':seed['qualification']['support_sha256'],'hardware_runtime':hw,
                'reviewed_task_evidence':{'status':'passed','evidence_sha256':'FIXTURE-TASK-EVIDENCE'},
                'reviewed_stop_evidence':{'status':'passed','evidence_sha256':'FIXTURE-STOP-EVIDENCE'}},route

    def proof(self,job):
        c=job['condition'];hw=job['hardware_runtime'];issue=job['issue']
        render={'prompt':'SYNTHETIC RENDER NOT MODEL EVIDENCE','token_ids':[1,2,3]}
        q={'status':'task_qualified','executor_id':'Collaborator','condition_id':c['condition_id'],
           'representation':'enriched','execution_scope':'main','package_sha256':issue['assignment']['package_sha256'],
           'worker_sha256':job['worker_sha256'],'support_sha256':job['support_sha256'],
           'scientific_condition_sha256':job['scientific_condition_sha256'],'hardware_runtime':hw,
           'bindings_sha256':a.digest(job['bindings']),'resolved_condition_sha256':a.digest(c),
           'quantization':c['settings']['quantization'],'precision':c['settings']['precision'],
           'tokenizer_files':{'template_sha256':c['template_sha256']},
           'model_files':{k:v['sha256'] for k,v in c['weight_files'].items()},
           'task_rehearsal':job['reviewed_task_evidence'],'stop_verification':job['reviewed_stop_evidence']}
        return {'status':'passed','answering_calls':0,'weights_loaded':False,'verified_unix_seconds':time.time(),
                'request_sha256':issue['request_sha256'],'job_sha256':a.digest(job),'condition_sha256':a.digest(c),
                'bindings_sha256':a.digest(job['bindings']),'remote_executor_sha256':issue['remote_executor_sha256'],
                'device_binding':{'status':'passed','physical_index':0,'device_uuid':hw['device_uuid'],'torch_device_uuid':hw['device_uuid']},
                'backend_config_verification':{'status':'passed','gpu_memory_utilization':.93},
                'stage2_render':render,'qualification':q}

    def transport(self, job, route, activation=True, result=True):
        dest=self.root/'fixture-transport';dest.mkdir()
        self.ledger.db.execute('INSERT INTO native_job_payloads VALUES(?,?)',(job['issue']['process'],a.canonical(job).decode()))
        a.put(dest/'job.json',job);a.put(dest/'route.json',route)
        issue=job['issue'];entries=[]
        a.put(dest/'process-receipt.json',{'process_reservation':issue['process'],'elapsed_seconds':2.0,
              'state':'complete' if result else 'failed','inference_started':bool(activation and result)})
        if activation:
            proof=self.proof(job);qual=proof['qualification'];ctx=remote.execution_context(job,qual)
            a.put(dest/'metadata-proof.json',proof);a.put(dest/'qualification.json',qual);a.put(dest/'execution-context.json',ctx)
            a.put(dest/'activation.json',{'activated_unix_seconds':time.time(),'central_issue_process':issue['process'],
                  'remote_executor_sha256':issue['remote_executor_sha256'],'metadata_proof_sha256':a.digest(proof)})
            if result:
                sid=issue['key'].split('|')[0];stem=sid+'-stage2.json'
                raw={'sample_id':sid,'condition_id':job['condition']['condition_id'],'representation':'enriched',
                     'stage':2,'stage_key':issue['key'],'stage_reservation':issue['process']+':'+issue['key'],
                     'request_sha256':issue['request_sha256'],'response_origin':'actual_local_model','cpu_fallback':False,
                     'execution_version':a.VERSION,'execution_scope':'main','qualification_status':'task_qualified',
                     'raw_output':'SYNTHETIC SOFTWARE FIXTURE ONLY','completion_status':'completed','termination':{},
                     'device_memory':{},'total_stage_seconds':1.0,'input_tokens':3,'output_tokens':2,'output_token_ids':[4,5]}
                for f in ('assignment_sha256','qualification_sha256','hardware_runtime_sha256','worker_sha256','scientific_condition_sha256','process_reservation'):
                    raw[f]=ctx[f]
                entry={'key':issue['key'],'request':'worker-output/executed-requests/'+stem,
                       'prompt':'worker-output/tokenized-prompts/'+stem,'result':'worker-output/results/'+stem,'routing':'route.json'}
                a.put(dest/entry['request'],route['request']);a.put(dest/entry['prompt'],proof['stage2_render']);a.put(dest/entry['result'],raw)
                a.put(dest/'worker-output/runtime.json',{'process_reservation':issue['process'],'qualification_sha256':ctx['qualification_sha256'],
                      'worker_sha256':ctx['worker_sha256'],'device_uuid':job['hardware_runtime']['device_uuid'],
                      'runtime_versions':job['hardware_runtime']['backend_versions'],
                      'hardware_runtime_observed':{k:job['hardware_runtime'][k] for k in ('driver','os','vram_mib')}})
                entries=[entry]
        a.put(dest/'return-envelope.json',{'version':native.VERSION,'kind':'prospective_central_stage2','assignment':issue['assignment']['id'],
              'executor':'Collaborator','process_reservation':issue['process'],'entries':entries,'files':a.files(dest)})
        return dest

    def test_native_import_preserves_local_authority_no_historical_tickets(self):
        self.reconcile();self.assertEqual(len(index.canonical_records(self.ledger)),600)
        self.assertEqual(self.ledger.db.execute('SELECT COUNT(*) FROM assignments').fetchone()[0],0)
        self.assertEqual(self.ledger.db.execute('SELECT COUNT(*) FROM stages').fetchone()[0],0)
        self.assertEqual(self.ledger.db.execute('SELECT COUNT(*) FROM qualifications').fetchone()[0],0)
        e=json.loads(self.ledger.db.execute('SELECT body FROM native_entries LIMIT 1').fetchone()[0])
        self.assertFalse(e['original_organizer_approved']);self.assertFalse(e['original_shared_ledger'])

    def test_duplicate_does_not_charge_again_or_change_budgets(self):
        before=native.budgets(self.ledger);self.reconcile();used=self.ledger.used()
        r=native.reconcile(self.ledger,SOURCE,RAW,self.auth,self.root/'not-created')
        self.assertTrue(r['identical_duplicate']);self.assertEqual(self.ledger.used(),used);self.assertEqual(native.budgets(self.ledger),before)
        self.assertEqual(self.ledger.db.execute("SELECT COUNT(*) FROM control_work WHERE state='unknown'").fetchone()[0],15)

    def test_no_authorization_no_registration(self):
        self.auth['explicit_human_native_reconciliation']=False
        with self.assertRaisesRegex(ValueError,'explicit human'):self.reconcile()
        self.assertFalse(native.exists(self.ledger,'native_entries'))

    def test_budget_failure_rolls_back_all_historical_registration(self):
        self.ledger.db.execute('DROP TRIGGER allocations_no_update')
        self.ledger.db.execute("UPDATE executor_allocations SET ceiling=10 WHERE owner='Collaborator'")
        self.ledger.db.execute("UPDATE executor_allocations SET ceiling=226790 WHERE owner='Ashraf'")
        self.auth['unchanged_budgets']=native.budgets(self.ledger)
        with self.assertRaises(sqlite3.IntegrityError):self.reconcile()
        self.assertEqual(self.ledger.db.execute('SELECT COUNT(*) FROM native_entries').fetchone()[0],0)
        self.assertEqual(self.ledger.used(),0)

    def test_archive_tamper_rejected_by_canonical_join(self):
        result=self.reconcile();Path(result['registry']['source']).write_bytes(b'SYNTHETIC TAMPER')
        with self.assertRaisesRegex(ValueError,'immutable native archive'):index.canonical_records(self.ledger)

    def test_initial_rerun_guard_and_provenance_delete_guard(self):
        self.reconcile()
        with self.assertRaisesRegex(sqlite3.IntegrityError,'cannot be rerun'):
            self.ledger.db.execute('INSERT INTO stages VALUES(?,?,?,?)',(FIRST,'MISSING-PROCESS','x','reserved_unknown'))
        with self.assertRaisesRegex(sqlite3.IntegrityError,'immutable'):
            self.ledger.db.execute('DELETE FROM native_entries WHERE key=?',(FIRST,))

    def test_frozen_route_is_verbatim_and_issue_is_future_only(self):
        self.reconcile();route=self.route();original=native.canonical_native(self.ledger)[FIRST]
        self.assertEqual(route['request']['messages'][-2],{'role':'assistant','content':original['raw_output']})
        issued=self.issue();self.assertEqual(issued['status'],'issued_pending_remote_metadata');self.assertEqual(issued['bound_seconds'],960)
        self.assertEqual(len(self.ledger.assignment(issued['assignment']['id'],'Collaborator')['keys']),1)
        with self.assertRaises(sqlite3.IntegrityError):self.issue()

    def test_unsupported_or_past_cutoff_cannot_issue(self):
        self.reconcile()
        with self.assertRaisesRegex(ValueError,'supported canonical'):self.issue()
        self.route()
        with self.assertRaisesRegex(ValueError,'cutoff passed'):
            native.issue(self.ledger,FIRST[:-1]+'2',self.root/'past.json','X','2000-01-01T00:00:00+00:00')

    def test_first_turn_conflict_blocks_second_turn(self):
        self.reconcile();self.route()
        self.ledger.db.execute('INSERT INTO returns VALUES(?,?,?,?,?)',(FIRST,'CONFLICT','NONE',0,'fixture conflicting transfer'))
        self.assertNotIn(FIRST,index.canonical_records(self.ledger))
        with self.assertRaisesRegex(ValueError,'history missing'):self.issue()

    def test_metadata_gates_and_actual_history(self):
        job,_=self.job();proof=self.proof(job);self.assertTrue(remote.validate_proof(job,proof))
        for change in ('stale','calls','artifact','device','overflow','worker','runtime','scope','wording'):
            j,p=copy.deepcopy(job),copy.deepcopy(proof)
            if change=='stale':p['verified_unix_seconds']-=301
            elif change=='calls':p['answering_calls']=1
            elif change=='artifact':p['qualification']['model_files']={}
            elif change=='device':p['device_binding']['torch_device_uuid']='OTHER'
            elif change=='overflow':p['stage2_render']['token_ids']=[1]*32768
            elif change=='worker':p['qualification']['worker_sha256']='OTHER'
            elif change=='runtime':p['backend_config_verification']['gpu_memory_utilization']=.89
            elif change=='scope':p['qualification']['execution_scope']='development'
            elif change=='wording':j['request']['messages'][-2]['content']='AUTHORED SUBSTITUTE'
            with self.subTest(change=change),self.assertRaises(ValueError):remote.validate_proof(j,p)

    def test_pending_resolved_scores_block_analysis(self):
        self.reconcile();self.route()
        with self.assertRaisesRegex(ValueError,'pending'):native.analyse_core(self.ledger,None,self.root/'analysis')
        self.issue()
        with self.assertRaisesRegex(ValueError,'pending'):native.analyse_core(self.ledger,None,self.root/'analysis')

    def test_metadata_failure_has_no_result_but_preserves_charge(self):
        job,route=self.job();dest=self.transport(job,route,activation=False,result=False)
        receipt=native.import_continuation(self.ledger,dest,self.root/'returned')
        self.assertEqual(receipt['accepted_keys'],[])
        self.assertEqual(self.ledger.db.execute('SELECT state FROM stages').fetchone()[0],'metadata_failed_unexecuted')
        self.assertEqual(self.ledger.db.execute('SELECT actual FROM processes').fetchone()[0],2)

    def test_successful_fixture_return_duplicate_accounted_once(self):
        job,route=self.job();dest=self.transport(job,route)
        receipt=native.import_continuation(self.ledger,dest,self.root/'returned');used=self.ledger.used()
        self.assertEqual(receipt['accepted_keys'],[job['issue']['key']]);self.assertIn(job['issue']['key'],index.canonical_records(self.ledger))
        self.assertTrue(native.import_continuation(self.ledger,dest,self.root/'returned')['identical_duplicate_transport'])
        self.assertEqual(self.ledger.used(),used)

    def test_changed_returned_assignment_rejected(self):
        job,route=self.job();dest=self.transport(job,route);e=a.read(dest/'return-envelope.json');e['executor']='OTHER'
        (dest/'return-envelope.json').write_bytes(a.canonical(e))
        with self.assertRaisesRegex(ValueError,'envelope assignment'):native.import_continuation(self.ledger,dest,self.root/'returned')

    def test_zip_traversal_rejected_and_original_retained(self):
        src=self.root/'fixture-unsafe.zip'
        with zipfile.ZipFile(src,'w') as z:z.writestr('../outside.json','{}')
        with self.assertRaisesRegex(ValueError,'unsafe'):native.unpack_return(src,self.root/'unpack')
        self.assertEqual(len(list((self.root/'unpack').glob('original-*.zip'))),1)
        self.assertFalse((self.root/'outside.json').exists())


if __name__=='__main__':unittest.main()
