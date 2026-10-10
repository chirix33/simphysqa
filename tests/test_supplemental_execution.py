"""Temporary MOCK fixtures only. No actual development/main reservations or weights."""
import json
from pathlib import Path
import sqlite3
import unittest
from unittest.mock import patch
import test_execution_readiness as fixtures
from simphysqa import supplemental_execution as dev
from simphysqa import execution_readiness as main


class Development(unittest.TestCase):
    def setUp(self):
        self.fixture=fixtures.Readiness();self.fixture.setUp();f=self.fixture
        f.ledger.db.close();f.spec.update(prior_accounting={'charged_seconds':1894.0963235319355,'combined_ceiling':20400},main_package_sha256='FIXTURE-CORRECTED-MAIN',items=[{'sample_id':'FIXTURE-NOT-MAIN','family':'clarification','split':'train'}, {'sample_id':'FIXTURE-OTHER','family':'direct','split':'train'}],proposal_sha256='fixture-proposal')
        (f.package/'execution-spec.json').write_bytes(dev.canonical(f.spec))
        f.ledger=dev.Ledger.create(f.root/'FIXTURE-DEVELOPMENT.sqlite',f.package,fixture=True,ceiling=1240)
        f.assignment=f.ledger.issue('FIXTURE-EXECUTOR',['fixture-shard'])
        f.qual.update(target_main_package_sha256='FIXTURE-CORRECTED-MAIN',status='runtime_qualified',execution_scope=dev.SCOPE,task_rehearsal={'status':'not_yet_collected'})
        f.qhash=f.ledger.approve_qualification(f.qual)

    def tearDown(self):self.fixture.tearDown()

    def job(self):
        f=self.fixture
        with patch('test_execution_readiness.prepare_job',dev.prepare_job):job=f.job()
        p=job/'worker-output/results/FIXTURE-NOT-MAIN-stage1.json';r=dev.read(p);r.update(execution_scope=dev.SCOPE,qualification_status='runtime_qualified');p.write_bytes(dev.canonical(r))
        return job

    def returned(self,job,name='dev-return'):
        f=self.fixture;out=f.root/name;dev.export_return(job,out);return out

    def test_runtime_qualification_not_task_claim(self):
        f=self.fixture;job=self.job();ctx=dev.read(job/'execution-context.json')
        self.assertEqual(ctx['execution_scope'],dev.SCOPE);self.assertEqual(ctx['qualification_status'],'runtime_qualified')
        self.assertEqual(ctx['development_manifest_sha256'],'fixture-proposal')
        self.assertEqual(f.qual['task_rehearsal']['status'],'not_yet_collected')
        with self.assertRaises(ValueError):main.Ledger.approve_qualification(f.ledger,f.qual)

    def test_cache_resolution_pins_bytes_and_rejects_outside(self):
        f=self.fixture;c=dev.resolved_condition(f.package,f.cid,f.bindings)
        self.assertEqual(c['snapshot_path'],str(f.snapshot))
        changed={**f.bindings,'artifact_cache':str(f.snapshot)}
        dev.resolved_condition(f.package,f.cid,changed)
        changed['artifact_cache']=str(f.root/'unrelated')
        with self.assertRaisesRegex(ValueError,'outside explicit cache'):dev.resolved_condition(f.package,f.cid,changed)

    def test_tampered_artifact_rejected(self):
        f=self.fixture;(f.snapshot/'fixture.bin').write_bytes(b'changed pinned bytes')
        with self.assertRaisesRegex(ValueError,'pinned artifact mismatch'):dev.resolved_condition(f.package,f.cid,f.bindings)

    def test_verified_numeric_binding_not_identity_relaxation(self):
        f=self.fixture;b={**f.bindings,'cuda_visible_devices':'0'}
        self.assertFalse(dev.device_binding_valid(b,f.qual))
        proof={**f.qual,'device_binding':{'status':'passed','physical_index':0,'device_uuid':'FIXTURE-GPU','torch_device_uuid':'FIXTURE-GPU'}}
        self.assertTrue(dev.device_binding_valid(b,proof))
        proof['device_binding']['torch_device_uuid']='WRONG-GPU'
        self.assertFalse(dev.device_binding_valid(b,proof))

    def test_vllm_uuid_visibility_rejected_before_reservation(self):
        f=self.fixture;q={**f.qual,'hardware_runtime':{**f.qual['hardware_runtime'],'backend_versions':{'vllm':'fixture'}}}
        self.assertFalse(dev.device_binding_valid(f.bindings,q))

    def test_startup_reserves_no_scientific_keys_or_calls(self):
        f=self.fixture;t=dev.reserve_startup(f.ledger,f.assignment['id'],'FIXTURE-EXECUTOR',f.cid,'enriched',{'fixture':True})
        self.assertEqual(t['stage_keys'],[]);self.assertEqual(t['answering_call_ceiling'],0);self.assertEqual(f.ledger.used(),600)
        self.assertEqual(f.ledger.db.execute('SELECT COUNT(*) FROM stages').fetchone()[0],0)
        self.assertIn(f.key,f.ledger.pending(f.assignment['id'],'FIXTURE-EXECUTOR'))
        f.ledger.settle(t['id'],7,'interrupted');self.assertEqual(f.ledger.used(),600)

    def test_unknown_startup_and_process_ceiling(self):
        f=self.fixture
        with patch.object(dev,'PROCESS_LIMIT',1):
            t=dev.reserve_startup(f.ledger,f.assignment['id'],'FIXTURE-EXECUTOR',f.cid,'enriched',{})
            f.ledger.settle(t['id'],3,'unknown');self.assertEqual(f.ledger.used(),600)
            with self.assertRaisesRegex(ValueError,'worker-process'):dev.reserve_startup(f.ledger,f.assignment['id'],'FIXTURE-EXECUTOR',f.cid,'enriched',{})

    def test_main_import_rejects_development(self):
        f=self.fixture;source=self.returned(self.job());e=dev.read(source/'return-envelope.json');e['kind']=dev.SCOPE
        (source/'return-envelope.json').write_bytes(dev.canonical(e))
        result=main.import_return(f.ledger,source,f.root/'main-reject')
        self.assertEqual(result['accepted_keys'],[]);self.assertTrue(result['validation_failures'])

    def test_main_package_rejects_development_selection(self):
        f=self.fixture
        with self.assertRaises((ValueError,KeyError)):main.validate_package(f.package)

    def test_actual_development_import_and_duplicate_transport(self):
        f=self.fixture;source=self.returned(self.job());root=f.root/'immutable'
        first=dev.import_return(f.ledger,source,root);second=dev.import_return(f.ledger,source,root)
        self.assertEqual(first['accepted_keys'],[f.key]);self.assertEqual(first['validation_failures'],[])
        self.assertTrue(second['identical_duplicate_transport']);self.assertEqual(len(dev.canonical_records(f.ledger)),1)
        self.assertEqual(f.ledger.used(),5)

    def test_conflicting_development_preserved_not_preferred(self):
        f=self.fixture;job=self.job();first=self.returned(job);dev.import_return(f.ledger,first,f.root/'imports')
        p=job/'worker-output/results/FIXTURE-NOT-MAIN-stage1.json';r=dev.read(p);r['raw_output']='different';p.write_bytes(dev.canonical(r))
        second=self.returned(job,'conflicting-return');result=dev.import_return(f.ledger,second,f.root/'imports')
        self.assertIn(f.key,result['conflicts']);self.assertNotIn(f.key,dev.canonical_records(f.ledger))
        self.assertEqual(len([p for p in (f.root/'imports').iterdir() if p.is_dir()]),2)

    def test_scope_corruption_rejected(self):
        f=self.fixture;job=self.job();p=job/'worker-output/results/FIXTURE-NOT-MAIN-stage1.json';r=dev.read(p);r['execution_scope']='main';p.write_bytes(dev.canonical(r))
        result=dev.import_return(f.ledger,self.returned(job),f.root/'imports');self.assertFalse(result['accepted_keys'])

    def test_failed_actual_stage_kept_never_resumed(self):
        f=self.fixture;job=self.job();p=job/'worker-output/results/FIXTURE-NOT-MAIN-stage1.json';r=dev.read(p);r.update(completion_status='failed',failure_reason='fixture failure',raw_output='partial');p.write_bytes(dev.canonical(r))
        dev.import_return(f.ledger,self.returned(job),f.root/'imports');self.assertEqual(dev.canonical_records(f.ledger)[f.key]['raw_output'],'partial')
        self.assertNotIn(f.key,f.ledger.pending(f.assignment['id'],'FIXTURE-EXECUTOR'))

    def test_overlapping_reservation_across_roots_rejected(self):
        f=self.fixture;self.job();other=dev.Ledger(f.root/'FIXTURE-DEVELOPMENT.sqlite')
        try:
            with self.assertRaises(sqlite3.IntegrityError):other.reserve(f.assignment['id'],'FIXTURE-EXECUTOR',[f.key],{f.key:dev.digest(f.q)},f.qhash)
        finally:other.db.close()

    def test_process_limit_includes_failed_startups(self):
        f=self.fixture
        with patch.object(dev,'PROCESS_LIMIT',1):
            t=f.ledger.reserve(f.assignment['id'],'FIXTURE-EXECUTOR',[f.key],{f.key:dev.digest(f.q)},f.qhash)
            f.ledger.settle(t['id'],0.5,'failed')
            with self.assertRaisesRegex(ValueError,'worker-process'):f.ledger.reserve(f.assignment['id'],'FIXTURE-EXECUTOR',[f.other],{f.other:dev.digest(f.q_other)},f.qhash)

    def test_initial_call_limit_and_atomic_budget(self):
        f=self.fixture
        with patch.object(dev,'INITIAL_LIMIT',0):
            with self.assertRaisesRegex(ValueError,'call ceiling'):f.ledger.reserve(f.assignment['id'],'FIXTURE-EXECUTOR',[f.key],{f.key:dev.digest(f.q)},f.qhash)
        self.assertEqual(f.ledger.used(),0)
        f.ledger.db.execute("UPDATE meta SET v='600' WHERE k='ceiling'")
        with self.assertRaisesRegex(ValueError,'aggregate'):f.ledger.reserve(f.assignment['id'],'FIXTURE-EXECUTOR',[f.key],{f.key:dev.digest(f.q)},f.qhash)
        self.assertEqual(f.ledger.used(),0)

    def test_unknown_and_overrun_retained(self):
        f=self.fixture;t=f.ledger.reserve(f.assignment['id'],'FIXTURE-EXECUTOR',[f.key],{f.key:dev.digest(f.q)},f.qhash)
        f.ledger.settle(t['id'],700,'unknown');self.assertEqual(f.ledger.used(),700)
        self.assertNotIn(f.key,f.ledger.pending(f.assignment['id'],'FIXTURE-EXECUTOR'))

    def test_unqualified_rejected_before_reservation(self):
        f=self.fixture
        with self.assertRaisesRegex(ValueError,'unqualified'):f.ledger.reserve(f.assignment['id'],'FIXTURE-EXECUTOR',[f.key],{f.key:dev.digest(f.q)},'unknown')
        self.assertEqual(f.ledger.used(),0)

    def test_unsupported_conditional_not_reserved(self):
        f=self.fixture;dev.put(f.root/'unexecuted.json',{'fixture':True})
        f.ledger.db.execute('INSERT INTO routes VALUES(?,?)',(f.second,dev.canonical({'status':'unexecuted_conditional','reason':'unsupported actual first turn'}).decode()))
        self.assertNotIn(f.second,f.ledger.pending(f.assignment['id'],'FIXTURE-EXECUTOR'))
        with self.assertRaisesRegex(ValueError,'unexecuted'):f.ledger.reserve(f.assignment['id'],'FIXTURE-EXECUTOR',[f.second],{f.second:'none'},f.qhash)

    def test_supported_actual_history_stage2_import(self):
        f=self.fixture;first_job=self.job();dev.import_return(f.ledger,self.returned(first_job),f.root/'imports')
        first=dev.canonical_records(f.ledger)[f.key];q={**f.q,'stage':2,'messages':f.q['messages']+[{'role':'assistant','content':first['raw_output']},{'role':'user','content':'Recorded fixture reply; not a gold answer'}]}
        route={'initial_key':f.key,'initial_result_sha256':dev.digest(first),'status':'supported','actual_raw':first['raw_output'],'request':q,'request_sha256':dev.digest(q)}
        f.ledger.db.execute('INSERT INTO routes VALUES(?,?)',(f.second,dev.canonical(route).decode()))
        second_job=f.root/'fixture-stage2';dev.prepare_job(f.ledger,f.assignment['id'],'FIXTURE-EXECUTOR',f.qhash,[f.second],f.bindings,second_job)
        context=dev.read(second_job/'execution-context.json');stem='FIXTURE-NOT-MAIN-stage2.json';base=second_job/'worker-output'
        dev.put(base/'executed-requests'/stem,q);dev.put(base/'tokenized-prompts'/stem,{'prompt':'fixture actual dialogue','token_ids':[1,2,3]})
        raw={**first,'stage':2,'stage_key':f.second,'request_sha256':dev.digest(q),'stage_reservation':context['stage_reservations'][f.second]}
        for name in ('qualification_sha256','assignment_sha256','hardware_runtime_sha256','worker_sha256','scientific_condition_sha256','process_reservation'):raw[name]=context[name]
        dev.put(base/'results'/stem,raw);runtime=dev.read(first_job/'worker-output/runtime.json');runtime['process_reservation']=context['process_reservation'];dev.put(base/'runtime.json',runtime)
        dev.put(second_job/'process-receipt.json',{'elapsed_seconds':4,'state':'complete','process_reservation':context['process_reservation']})
        result=dev.import_return(f.ledger,self.returned(second_job,'second-return'),f.root/'imports')
        self.assertEqual(result['accepted_keys'],[f.second]);self.assertEqual(q['messages'][-2]['content'],first['raw_output'])
        self.assertEqual(f.ledger.used(),9)

    def test_bytecode_side_effect_rejects_sealed_package(self):
        f=self.fixture;manifest=dev.files(f.package);manifest.pop('package-manifest.json')
        (f.package/'package-manifest.json').write_bytes(dev.canonical({'scope':dev.SCOPE,'files':manifest}))
        before=dev.files(f.package);dev.put(f.package/'unexpected-cache.json',{'fixture':'side effect'})
        actual=dev.files(f.package);self.assertNotEqual(before,actual)
        with self.assertRaises(ValueError):dev.validate_package(f.package)

    def test_missing_runtime_startup_preserved_and_measured_once(self):
        f=self.fixture;job=self.job();(job/'worker-output/runtime.json').unlink()
        result=dev.import_return(f.ledger,self.returned(job),f.root/'imports')
        self.assertFalse(result['accepted_keys']);self.assertTrue(result['validation_failures']);self.assertEqual(f.ledger.used(),5)
        self.assertNotIn(f.key,f.ledger.pending(f.assignment['id'],'FIXTURE-EXECUTOR'))

    def test_return_bytes_and_null_memory(self):
        f=self.fixture;source=self.returned(self.job());self.assertEqual((source/'worker-output/executed-requests/FIXTURE-NOT-MAIN-stage1.json').read_bytes(),dev.canonical(f.q))
        result=dev.read(source/'worker-output/results/FIXTURE-NOT-MAIN-stage1.json');self.assertIsNone(result['device_memory']['sampled_peak_mib'])
        self.assertEqual(result['total_stage_seconds'],2);self.assertEqual(result['termination']['category'],'complete')




class Supplemental(unittest.TestCase):
    setUp=Development.setUp
    tearDown=Development.tearDown
    def test_combined_ceiling_counts_prior_unknown_work(self):
        f=self.fixture
        spec=dev.read(f.package/'execution-spec.json');spec['prior_accounting']['charged_seconds']=20395
        f.ledger.db.execute("UPDATE meta SET v=? WHERE k='spec'",(dev.canonical(spec).decode(),))
        with self.assertRaisesRegex(ValueError,'combined development'):
            dev.reserve_startup(f.ledger,f.assignment['id'],'FIXTURE-EXECUTOR',f.cid,'enriched',{})
        self.assertEqual(f.ledger.used(),0)

    def test_two_phase_process_allocation_does_not_double_charge(self):
        f=self.fixture;t=dev.reserve_startup(f.ledger,f.assignment['id'],'FIXTURE-EXECUTOR',f.cid,'enriched',{})
        ticket=f.ledger.reserve(f.assignment['id'],'FIXTURE-EXECUTOR',[f.key],{f.key:dev.digest(f.q)},f.qhash,process=t['id'])
        self.assertEqual(ticket['id'],t['id']);self.assertEqual(f.ledger.used(),610)
        self.assertEqual(f.ledger.db.execute('SELECT COUNT(*) FROM processes').fetchone()[0],1)
        with self.assertRaises(Exception):
            f.ledger.reserve(f.assignment['id'],'FIXTURE-EXECUTOR',[f.other],{f.other:dev.digest(f.q_other)},f.qhash,process=t['id'])
        self.assertEqual(f.ledger.used(),610)

    def test_fresh_preflight_requires_all_bound_identities(self):
        from simphysqa.execution_preflight import verify_preflight
        import time
        f=self.fixture;q=f.qual
        p={k:q[k] for k in ('bindings_sha256','resolved_condition_sha256','worker_sha256','support_sha256','scientific_condition_sha256')}
        p.update(status='passed',qualification_sha256=dev.digest(q),hardware_runtime_sha256=dev.digest(q['hardware_runtime']),verified_unix_seconds=time.time(),device_binding={'status':'passed','device_uuid':'FIXTURE-GPU','torch_device_uuid':'FIXTURE-GPU'})
        verify_preflight(p,q)
        for key in ('bindings_sha256','worker_sha256','qualification_sha256'):
            with self.assertRaises(ValueError):verify_preflight({**p,key:'WRONG'},q)
        with self.assertRaisesRegex(ValueError,'stale'):verify_preflight({**p,'verified_unix_seconds':0},q)
        with self.assertRaises(ValueError):verify_preflight(None,q)

    def test_device_mapping_is_rechecked_and_mismatch_rejected(self):
        from simphysqa.execution_preflight import live_device_check
        from types import SimpleNamespace
        f=self.fixture;b={**f.bindings,'cuda_visible_devices':'0'}
        with patch('simphysqa.execution_preflight.subprocess.run',return_value=SimpleNamespace(stdout='0, FIXTURE-GPU\n')):
            self.assertEqual(live_device_check(b),{'0':'FIXTURE-GPU'})
        with patch('simphysqa.execution_preflight.subprocess.run',return_value=SimpleNamespace(stdout='0, OTHER-GPU\n')):
            with self.assertRaises(ValueError):live_device_check(b)

    def test_corrected_main_cache_and_interrupted_orphan(self):
        from simphysqa import execution_adapter as adapter
        f=self.fixture;adapter.resolved_condition(f.package,f.cid,f.bindings)
        with self.assertRaises(ValueError):adapter.resolved_condition(f.package,f.cid,{**f.bindings,'artifact_cache':str(f.root/'UNRELATED')})
        t=dev.reserve_startup(f.ledger,f.assignment['id'],'FIXTURE-EXECUTOR',f.cid,'enriched',{})
        f.ledger.settle(t['id'],1,'interrupted')
        self.assertEqual(adapter.Ledger.used(f.ledger),600)
