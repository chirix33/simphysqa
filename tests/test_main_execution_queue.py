"""Temporary synthetic ledgers only; no real main reservations or model calls."""
import unittest
from unittest.mock import patch
from pathlib import Path
import test_execution_readiness as fixtures
from simphysqa import main_execution_queue as queue,execution_adapter as adapter

class Queue(unittest.TestCase):
    def setUp(self):
        self.f=fixtures.Readiness();self.f.setUp()
        c=adapter.read(self.f.package/'condition.json');c['model_id']='FIXTURE-NOT-A-MODEL'
        (self.f.package/'condition.json').write_bytes(adapter.canonical(c))
    def tearDown(self):self.f.tearDown()
    def test_overhead_reserved_before_metadata_and_unknown_retained(self):
        f=self.f;t=queue.reserve_overhead(f.ledger,f.assignment['id'],'FIXTURE-EXECUTOR',f.cid,'enriched')
        self.assertEqual(t['stage_keys'],[]);self.assertEqual(f.ledger.used(),600)
        self.assertEqual(f.ledger.db.execute('SELECT COUNT(*) FROM stages').fetchone()[0],0)
        f.ledger.settle(t['id'],2,'unknown');self.assertEqual(adapter.Ledger.used(f.ledger),600)
    def test_bound_and_assignment_rejected_before_insert(self):
        f=self.f
        with self.assertRaises(ValueError):queue.reserve_overhead(f.ledger,f.assignment['id'],'OTHER',f.cid,'enriched')
        with self.assertRaises(ValueError):queue.reserve_overhead(f.ledger,f.assignment['id'],'FIXTURE-EXECUTOR',f.cid,'structured_only')
        f.ledger.db.execute("UPDATE meta SET v='599' WHERE k='ceiling'")
        with self.assertRaises(ValueError):queue.reserve_overhead(f.ledger,f.assignment['id'],'FIXTURE-EXECUTOR',f.cid,'enriched')
        self.assertEqual(f.ledger.used(),0)
    def test_shared_startup_block_prevents_another_representation(self):
        f=self.f;queue.ensure_tables(f.ledger)
        f.ledger.db.execute('INSERT INTO startup_blocks VALUES(?,?)',(queue.identity(f.ledger,'FIXTURE-EXECUTOR',f.cid),'preserved shared startup failure'))
        with self.assertRaisesRegex(ValueError,'shared startup queue paused'):
            queue.reserve_overhead(f.ledger,f.assignment['id'],'FIXTURE-EXECUTOR',f.cid,'enriched')
        self.assertEqual(f.ledger.used(),0)
    def test_corrected_adapter_cannot_accept_unmapped_task_evidence(self):
        f=self.f
        with self.assertRaisesRegex(ValueError,'corrected main qualification mapping'):
            adapter.Ledger.approve_qualification(f.ledger,f.qual)
    def test_preflight_failure_blocks_queue_and_preserves_allocation(self):
        f=self.f;t=queue.reserve_overhead(f.ledger,f.assignment['id'],'FIXTURE-EXECUTOR',f.cid,'enriched')
        queue.block_startup(f.ledger,f.assignment['id'],'FIXTURE-EXECUTOR',f.cid,t['id'],'fixture ModelConfig failure',3)
        self.assertEqual(adapter.Ledger.used(f.ledger),3)
        self.assertEqual(f.ledger.db.execute('SELECT COUNT(*) FROM processes').fetchone()[0],1)
        with self.assertRaisesRegex(ValueError,'paused'):queue.check_queue(f.ledger,'FIXTURE-EXECUTOR',f.cid)
    def test_gguf_preflight_does_not_invent_torch_measurement(self):
        from simphysqa.execution_preflight import verify_preflight
        import time
        f=self.f;q={**f.qual,'hardware_runtime':{**f.qual['hardware_runtime'],'backend_versions':{'llama.cpp':'FIXTURE'}}}
        p={k:q[k] for k in ('bindings_sha256','resolved_condition_sha256','worker_sha256','support_sha256','scientific_condition_sha256')}
        p.update(status='passed',qualification_sha256=adapter.digest(q),hardware_runtime_sha256=adapter.digest(q['hardware_runtime']),verified_unix_seconds=time.time(),device_binding={'status':'passed','device_uuid':'FIXTURE-GPU','torch_device_uuid':None})
        verify_preflight(p,q)
        q['hardware_runtime']['backend_versions']={'torch':'FIXTURE'}
        p.update(qualification_sha256=adapter.digest(q),hardware_runtime_sha256=adapter.digest(q['hardware_runtime']))
        with self.assertRaisesRegex(ValueError,'physical GPU'):verify_preflight(p,q)
