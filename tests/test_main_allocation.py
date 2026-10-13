"""Offline synthetic allocation tests; never creates a real main reservation."""
import sqlite3
import unittest
import test_execution_readiness as fixtures
from simphysqa import main_allocation as allocation, execution_adapter as adapter

class Allocation(unittest.TestCase):
    def setUp(self):
        self.fixture = fixtures.Readiness(); self.fixture.setUp()
        self.fixture.ledger.db.close()
        self.ledger = allocation.Ledger(self.fixture.root/'FIXTURE.sqlite')
        allocation.install(self.ledger, {'FIXTURE-EXECUTOR':700,'COLLABORATOR-UNASSIGNED':540})
        self.assignment = self.fixture.assignment['id']
    def tearDown(self):
        self.ledger.db.close(); self.fixture.temp.cleanup()
    def insert(self, identity, bound):
        self.ledger.db.execute('INSERT INTO processes VALUES(?,?,?,?,?)',(identity,self.assignment,bound,None,'reserved_unknown'))
    def test_executor_limit_even_bare_connection(self):
        self.insert('p',600)
        bare = adapter.Ledger(self.ledger.path)
        with self.assertRaisesRegex(sqlite3.IntegrityError,'executor'): bare.db.execute('INSERT INTO processes VALUES(?,?,?,?,?)',('other',self.assignment,101,None,'reserved_unknown'))
        bare.db.close(); self.assertEqual(self.ledger.used(),600)
    def test_extension_rollback_and_unknown_bound(self):
        self.insert('p',600)
        with self.assertRaises(sqlite3.IntegrityError): self.ledger.db.execute('UPDATE processes SET bound=701 WHERE id="p"')
        self.ledger.settle('p',2,'unknown'); self.assertEqual(self.ledger.used(),600)
    def test_settled_overrun_retained_stops_issue(self):
        self.insert('p',600); self.ledger.settle('p',800,'complete')
        self.assertEqual(self.ledger.remaining('FIXTURE-EXECUTOR'),-100)
        with self.assertRaises(sqlite3.IntegrityError): self.insert('next',1)
    def test_control_and_gap_charged_once(self):
        c=self.ledger.reserve_control('FIXTURE-EXECUTOR','mock verification',50)
        self.insert('p',600); self.ledger.settle('p',20,'complete'); self.ledger.settle_control(c,4)
        self.ledger.add_dispatcher_gap('p',2,{'fixture':True}); self.assertEqual(self.ledger.used(),26)
        with self.assertRaises(sqlite3.IntegrityError): self.ledger.add_dispatcher_gap('p',2,{})
    def test_allocation_immutable(self):
        with self.assertRaises(sqlite3.IntegrityError): self.ledger.db.execute('UPDATE executor_allocations SET ceiling=1000')
    def test_unallocated_executor_rejected(self):
        with self.assertRaises(ValueError): self.ledger.reserve_control('unknown','mock',1)

if __name__=='__main__': unittest.main()
