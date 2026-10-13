import unittest
from simphysqa.public_updates import difference,apply
from simphysqa.heldout_live import admit_annotation,CeilingReached,LIMITS,SIM_LIMITS
from simphysqa.io import canonical

class ExecutionBoundaries(unittest.TestCase):
    def test_public_roundtrip_preserves_types_and_escaping(self):
        a={'a/b':{'x~y':[1,None,True]},'gone':'fact'}
        b={'a/b':{'x~y':[1.0,None,False]},'new':{'frame':'world'}}
        self.assertEqual(canonical(apply(a,difference(a,b))),canonical(b))
        self.assertEqual(a['gone'],'fact')
    def test_authorized_ceilings_are_separate(self):
        self.assertEqual((LIMITS['initial_requests'],LIMITS['total_attempts'],LIMITS['usd_cap']),(676,1352,320))
        self.assertEqual((SIM_LIMITS['maximum_simulation_executions'],SIM_LIMITS['total_wall_seconds']),(1612,14400))
    def test_reservations_block_spend_tokens_time_before_call(self):
        bound={'usd':1,'input_token_upper_bound':5,'output_token_limit':2}
        prior={'initial_request':True,'charged_upper_bound_usd':320,'reservation':bound,'wall_seconds':0}
        with self.assertRaises(CeilingReached):admit_annotation([prior],bound,True)
        prior['charged_upper_bound_usd']=0;prior['wall_seconds']=14300
        with self.assertRaises(CeilingReached):admit_annotation([prior],bound,True)
        prior['wall_seconds']=0;prior['reservation']={**bound,'input_token_upper_bound':18000000}
        with self.assertRaises(CeilingReached):admit_annotation([prior],bound,True)

if __name__=='__main__':unittest.main()
