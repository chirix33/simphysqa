import tempfile
import unittest
from pathlib import Path
from phi_jepa.pilot_budget import PilotBudget, BudgetExceeded


class PilotBudgetTests(unittest.TestCase):
    def config(self):
        return {'caps':{'artifact_bytes':1000000,'gpu_seconds':10,'cpu_seconds':10,'provider_attempts':1,'provider_input_tokens':10000,'provider_output_tokens':100,'provider_usd':1},'bucket_seconds':{'test':10}}
    def test_unknown_usage_keeps_reservation_and_stops_second_call(self):
        with tempfile.TemporaryDirectory() as tmp:
            b=PilotBudget(tmp,self.config())
            def timeout(payload,seconds): raise TimeoutError()
            call=b.transport(timeout)
            with self.assertRaises(TimeoutError): call({'model':'fixture','max_output_tokens':20},1)
            row=b.read()['provider'][0]
            self.assertFalse(row['usage_known']); self.assertEqual(row['charged_output'],20)
            with self.assertRaises(BudgetExceeded): call({'model':'fixture','max_output_tokens':20},1)
            self.assertEqual(len(b.read()['provider']),1)
    def test_compute_charged_and_artifact_reservation_fails_before_write(self):
        with tempfile.TemporaryDirectory() as tmp:
            b=PilotBudget(tmp,self.config())
            with b.operation('fixture','cpu',('test',)): pass
            state=b.read(); self.assertIsNone(state['active']); self.assertEqual(state['seconds']['cpu'],state['seconds']['test'])
            with self.assertRaises(BudgetExceeded): b.check(1000001)
    def test_reported_usage_releases_unused_reservation(self):
        with tempfile.TemporaryDirectory() as tmp:
            b=PilotBudget(tmp,self.config())
            body={'status':'completed','usage':{'input_tokens':10,'output_tokens':2},'output':[{'type':'message','content':[{'type':'output_text','text':'ok'}]}]}
            b.transport(lambda payload,timeout:body)({'model':'fixture','max_output_tokens':20},1)
            row=b.read()['provider'][0]
            self.assertTrue(row['usage_known']); self.assertEqual(row['charged_input'],10); self.assertEqual(row['charged_output'],2)


if __name__=='__main__': unittest.main()
