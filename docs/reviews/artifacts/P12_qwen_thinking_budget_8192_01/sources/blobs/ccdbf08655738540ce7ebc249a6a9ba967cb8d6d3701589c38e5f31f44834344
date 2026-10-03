"""Versioned Qwen budget-only orchestration checks; no model generation."""
from copy import deepcopy
import unittest
from p12_qwen_completion_prepare import assert_budget_only
from p12_qwen_completion_run import reserve,overhead,CONDITIONS


class QwenBudgetTests(unittest.TestCase):
    def test_only_two_setting_changes_allowed(self):
        old=dict(settings=dict(max_new_tokens=4096,max_seconds=240,temperature=.6),input_token_ids=[1,2],schema_json='unchanged')
        new=deepcopy(old);new['settings'].update(max_new_tokens=8192,max_seconds=360)
        assert_budget_only(old,new)
        new['input_token_ids']=[1,3]
        with self.assertRaisesRegex(ValueError,'outside'):assert_budget_only(old,new)
        new=deepcopy(old);new['settings'].update(max_new_tokens=8192,max_seconds=360,temperature=.7)
        with self.assertRaisesRegex(ValueError,'outside'):assert_budget_only(old,new)

    def test_eight_attempts_single_hour_and_no_reset(self):
        self.assertEqual(CONDITIONS,('qwen3_8b_thinking',))
        ledger=dict(started_unix=100.,deadline_unix=3700.,finished_unix=None,attempts=[])
        a=reserve(ledger,CONDITIONS[0],'a','sha',110,360);a['finished_unix']=120
        with self.assertRaisesRegex(ValueError,'already counted'):reserve(ledger,CONDITIONS[0],'a','sha',125,360)
        with self.assertRaisesRegex(ValueError,'shared window'):reserve(ledger,CONDITIONS[0],'b','sha',3400,360)
        with self.assertRaisesRegex(ValueError,'overhead'):reserve(ledger,CONDITIONS[0],'b','sha',840,360)
        ledger['attempts']*=8
        with self.assertRaisesRegex(ValueError,'8-attempt cap'):reserve(ledger,CONDITIONS[0],'b','sha',130,360)
        self.assertEqual(ledger['deadline_unix'],3700.)


if __name__=='__main__':unittest.main()
