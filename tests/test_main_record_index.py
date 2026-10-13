"""No network/model calls; verify byte/tamper/conflict equivalence on fixtures."""
import unittest
from unittest.mock import patch
from pathlib import Path
import test_execution_readiness as fixtures
from simphysqa import execution_adapter as adapter, main_record_index as index

class Index(unittest.TestCase):
    def setUp(self):self.f=fixtures.Readiness();self.f.setUp()
    def tearDown(self):self.f.tearDown()
    def imported(self):
        job=self.f.job();root=self.f.root/'transport';adapter.export_return(job,root)
        receipt=adapter.import_return(self.f.ledger,root,self.f.root/'immutable')
        self.assertEqual(receipt['validation_failures'],[]);return Path(receipt['source_root'])
    def test_same_records_as_sealed_adapter(self):
        self.imported();self.assertEqual(index.canonical_records(self.f.ledger),adapter.canonical_records(self.f.ledger))
    def test_tamper_rejected(self):
        source=self.imported();(source/'condition.json').write_text('{}')
        with self.assertRaisesRegex(ValueError,'immutable'):index.canonical_records(self.f.ledger)
    def test_conflict_blocks_initial_and_conditional(self):
        source=self.imported();self.f.ledger.db.execute('INSERT INTO returns VALUES(?,?,?,?,?)',(self.f.key,'conflict',str(source),0,'fixture differing bytes'))
        self.assertEqual(index.canonical_records(self.f.ledger),{})
    def test_one_hash_pass_per_source(self):
        self.imported()
        with patch.object(adapter,'files',wraps=adapter.files) as hashes:index.canonical_records(self.f.ledger)
        self.assertEqual(hashes.call_count,1)
    def test_transaction_snapshot_requires_lock_and_expires(self):
        self.imported()
        with self.assertRaises(ValueError):
            with index.transaction_snapshot(self.f.ledger):pass
        self.f.ledger.db.execute('BEGIN IMMEDIATE')
        with patch.object(adapter,'files',wraps=adapter.files) as hashes:
            with index.transaction_snapshot(self.f.ledger):
                adapter.canonical_records(self.f.ledger);adapter.canonical_records(self.f.ledger)
            self.assertEqual(hashes.call_count,1)
        self.f.ledger.db.execute('COMMIT')
        self.assertEqual(index.canonical_records(self.f.ledger),adapter.canonical_records(self.f.ledger))

if __name__=='__main__':unittest.main()
