import unittest
from enrichment_two_record_recovery import validate_scope

class RecoveryTests(unittest.TestCase):
    def setUp(self):
        self.config={'enabled':True,'authorization':'fixture','usd_cap':2,'attempt_cap':6,'wall_seconds_cap':1800}
        self.rows=[{'sample_id':s,'domain':'tethered_load','split':'train'} for s in ('b06de105f9948d5fb26f82e9194d2239','757d9982860c372fb1ac7fed9ddb8ffb')]
    def test_authorized_scope_and_caps(self):
        validate_scope(self.config,self.rows)
        for key,value in [('enabled',False),('authorization',None),('usd_cap',2.01),('attempt_cap',7),('wall_seconds_cap',1801)]:
            with self.assertRaises(ValueError):validate_scope(self.config|{key:value},self.rows)
    def test_confirmation_and_additional_or_substituted_records_rejected(self):
        for rows in (self.rows+[self.rows[0]],self.rows[:1],[self.rows[0],self.rows[1]|{'split':'test_id'}],
                     [self.rows[0],self.rows[1]|{'sample_id':'different'}]):
            with self.assertRaises(ValueError):validate_scope(self.config,rows)

if __name__=='__main__':unittest.main()
