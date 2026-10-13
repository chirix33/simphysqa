import sys,unittest
from pathlib import Path
ROOT=Path(__file__).parent/'complement-analysis-src-1.0.1';sys.path.insert(0,str(ROOT));sys.path.insert(0,str(ROOT/'src'))
from finish_complement import complete_coverage,metrics
class Coverage(unittest.TestCase):
 def setUp(self):
  self.i=['MOCK-I'];self.c=['MOCK-C'];self.stages={'MOCK-I':('key','process','hash','completed'),'MOCK-C':('key','process','hash','failed')};self.routes={'MOCK-C':{'status':'supported'}};self.raw={'MOCK-I':{'completion_status':'completed'},'MOCK-C':{'completion_status':'failed'}}
 def test_canonical_failed_output_retained_as_completed_accounting(self):self.assertTrue(complete_coverage(self.i,self.c,self.stages,self.routes,self.raw))
 def test_missing_or_conflicted_bytes_not_qualified(self):
  del self.raw['MOCK-C'];self.assertFalse(complete_coverage(self.i,self.c,self.stages,self.routes,self.raw))
 def test_unsupported_conditional_never_invented(self):
  self.routes['MOCK-C']['status']='unexecuted_conditional';del self.stages['MOCK-C'];del self.raw['MOCK-C'];self.assertTrue(complete_coverage(self.i,self.c,self.stages,self.routes,self.raw))
 def test_unknown_reservation_and_uncollected_route_not_complete(self):
  self.stages['MOCK-I']=('key','process','hash','reserved_unknown');self.assertFalse(complete_coverage(self.i,self.c,self.stages,self.routes,self.raw));self.routes={};self.assertFalse(complete_coverage(self.i,self.c,self.stages,self.routes,self.raw))
 def test_absent_measurement_is_null_not_zero(self):
  m=metrics({},['MOCK-I']);self.assertIsNone(m['stage_latency_seconds']);self.assertIsNone(m['device_sampled_peak_mib']);self.assertIsNone(m['successful_device_samples'])
if __name__=='__main__':unittest.main(verbosity=2)