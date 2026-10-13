"""Fixture-only duplicate/conflicting lifecycle regression tests."""
import shutil,unittest
from pathlib import Path
import test_execution_readiness as fixtures
from simphysqa import execution_adapter as adapter,main_import

class Import(unittest.TestCase):
    def setUp(self):self.f=fixtures.Readiness();self.f.setUp()
    def tearDown(self):self.f.tearDown()
    def first(self):
        job=self.f.job();source=self.f.root/'return';adapter.export_return(job,source)
        receipt=main_import.import_return(self.f.ledger,source,self.f.root/'immutable')
        self.assertEqual(receipt['validation_failures'],[]);return source
    def test_identical_transport_counts_once(self):
        source=self.first();receipt=main_import.import_return(self.f.ledger,source,self.f.root/'immutable')
        self.assertTrue(receipt['identical_duplicate_transport']);self.assertEqual(self.f.ledger.db.execute('SELECT COUNT(*) FROM returns').fetchone()[0],1)
    def test_conflicting_lifecycle_keeps_both_and_bound(self):
        source=self.first();other=self.f.root/'different';shutil.copytree(source,other)
        receipt=adapter.read(other/'process-receipt.json');receipt['elapsed_seconds']+=1
        (other/'process-receipt.json').write_bytes(adapter.canonical(receipt))
        envelope=adapter.read(other/'return-envelope.json');hashes=adapter.files(other);hashes.pop('return-envelope.json');envelope['files']=hashes
        (other/'return-envelope.json').write_bytes(adapter.canonical(envelope))
        result=main_import.import_return(self.f.ledger,other,self.f.root/'immutable')
        self.assertTrue(result['validation_failures']);self.assertEqual(result['conflicts'],[self.f.key]);self.assertEqual(adapter.canonical_records(self.f.ledger),{})
        self.assertEqual(self.f.ledger.db.execute('SELECT COUNT(*) FROM returns').fetchone()[0],2)
        state,bound=self.f.ledger.db.execute('SELECT state,bound FROM processes').fetchone();self.assertEqual(state,'unknown');self.assertEqual(self.f.ledger.used(),bound)

if __name__=='__main__':unittest.main()
