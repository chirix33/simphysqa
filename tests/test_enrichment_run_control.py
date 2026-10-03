"""Offline supervisor reporting checks; no credentials or provider calls."""
import unittest,tempfile
from pathlib import Path
from unittest.mock import patch
import enrichment_run_control as control

class SupervisorTests(unittest.TestCase):
    def test_inflight_reservation_and_failures_remain_visible(self):
        with tempfile.TemporaryDirectory() as directory:
            root=Path(directory)/'native';export=Path(directory)/'export'
            control.atomic_json(root/'spend-ledger.json',{'stopped':None,'attempts':[
                {'scope':'train_validation','charged_nano_usd':300000000,'usage':None,'status':'reserved'},
                {'scope':'confirmation','charged_nano_usd':40000000,'usage':{'input_tokens':200,'output_tokens':20}}]})
            control.atomic_json(root/'results/a.json',{'scope':'train_validation','status':'failure'})
            control.atomic_json(root/'results/b.json',{'scope':'confirmation','status':'success'})
            with patch.object(control,'RUN',root),patch.object(control,'EXPORT',export):result=control.summary()
            self.assertEqual(result['charged_usd'],.34)
            self.assertEqual(result['scopes']['train_validation']['unknown_usage_attempts'],1)
            self.assertEqual(result['scopes']['train_validation']['results'],{'failure':1})
            self.assertFalse(result['all_records_successful'])
            self.assertEqual(control.load(export/'status.json'),result)

    def test_start_rejects_unapproved_scope_before_launch(self):
        with tempfile.TemporaryDirectory() as directory:
            config=Path(directory)/'config.json';control.atomic_json(config,{'enabled':False,'authorized_scopes':[]})
            with patch.object(control,'APPROVED',config),patch.object(control.subprocess,'Popen') as launch:
                with self.assertRaisesRegex(ValueError,'both-scope'):control.start()
                launch.assert_not_called()

if __name__=='__main__':unittest.main()
