"""Power-loss fixtures only; no main reservations, weights or inference."""
import unittest,json
import test_execution_readiness as fixtures
from simphysqa import execution_adapter as adapter, main_restart

class Restart(unittest.TestCase):
    def setUp(self):
        self.f=fixtures.Readiness(); self.f.setUp()
        spec=json.loads(self.f.ledger.meta('spec'))
        spec['items']=[{'sample_id':self.f.key.split('|')[0],'family':'direct'}]
        self.f.ledger.db.execute("UPDATE meta SET v=? WHERE k='spec'",(json.dumps(spec),))
    def tearDown(self): self.f.tearDown()
    def setup_partial(self, missing=False):
        f=self.f;job=f.job()
        (job/'process-receipt.json').unlink()
        if (job/'worker-output/completed.json').exists(): (job/'worker-output/completed.json').unlink()
        if missing:
            for p in (job/'worker-output/results').glob('*.json'): p.unlink()
        evidence=f.root/'stopped.txt';evidence.write_text('OFFLINE FIXTURE: worker stopped')
        return job,{'worker_stopped':True,'evidence_files':{str(evidence):adapter.sha(evidence)}}
    def test_saved_result_imported_unknown_bound_retained(self):
        f=self.f;job,evidence=self.setup_partial();before=adapter.files(job)
        result=main_restart.recover(f.ledger,job,f.root/'return',f.root/'immutable',evidence,f.root/'routes')
        self.assertEqual(result['accepted_saved_keys'],[f.key])
        self.assertEqual(adapter.files(job),before)
        bound,actual,state=f.ledger.db.execute('SELECT bound,actual,state FROM processes').fetchone()
        self.assertIsNone(actual);self.assertEqual(state,'interrupted');self.assertEqual(f.ledger.used(),bound)
        self.assertNotIn(f.key,f.ledger.pending(f.assignment['id'],'FIXTURE-EXECUTOR'))
        self.assertEqual(f.ledger.pending(f.assignment['id'],'FIXTURE-EXECUTOR'),[k for k in f.assignment['keys'] if k!=f.key and k.endswith('|1')])
        self.assertEqual(len(adapter.canonical_records(f.ledger)),1)
    def test_missing_output_preserved_as_failure_never_retried(self):
        f=self.f;job,evidence=self.setup_partial(missing=True)
        spec=json.loads(f.ledger.meta('spec'));spec['items'][0]['family']='clarification'
        f.ledger.db.execute("UPDATE meta SET v=? WHERE k='spec'",(json.dumps(spec),))
        result=main_restart.recover(f.ledger,job,f.root/'return',f.root/'immutable',evidence,f.root/'routes')
        self.assertEqual(result['accepted_saved_keys'],[])
        self.assertEqual(result['interrupted_missing_or_invalid_keys'],[f.key])
        self.assertTrue(result['import_receipt']['validation_failures'])
        self.assertNotIn(f.key,f.ledger.pending(f.assignment['id'],'FIXTURE-EXECUTOR'))
        self.assertEqual(f.ledger.pending(f.assignment['id'],'FIXTURE-EXECUTOR'),[k for k in f.assignment['keys'] if k!=f.key and k.endswith('|1')])
        self.assertEqual(adapter.canonical_records(f.ledger),{})
        route=json.loads(f.ledger.db.execute('SELECT body FROM routes').fetchone()[0])
        self.assertEqual(route['status'],'unexecuted_conditional');self.assertIsNone(route['actual_raw']);self.assertIsNone(route['request'])
        self.assertFalse(f.ledger.db.execute('SELECT 1 FROM stages WHERE key=?',(f.key[:-1]+'2',)).fetchone())
    def test_without_stopped_evidence_no_export_or_change(self):
        f=self.f;job,evidence=self.setup_partial();evidence['worker_stopped']=False
        with self.assertRaisesRegex(ValueError,'stopped-worker'):
            main_restart.recover(f.ledger,job,f.root/'return',f.root/'immutable',evidence,f.root/'routes')
        self.assertFalse((f.root/'return').exists())
        self.assertEqual(f.ledger.db.execute('SELECT state FROM processes').fetchone()[0],'reserved_unknown')

if __name__=='__main__':unittest.main()
