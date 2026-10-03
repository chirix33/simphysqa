"""Qualification planning invariants, without models or reference access."""
from dataclasses import replace
import unittest
from unittest.mock import patch
from p12_answer_interface_followup import budget_spec, CONDITIONS, settings
from phi_jepa.providers.local_answer import LocalAnswerSettings


class FollowupTests(unittest.TestCase):
    def test_four_conditions_and_nonrenewable_feasible_budget(self):
        budget = budget_spec()
        self.assertEqual(len(CONDITIONS), 4)
        self.assertEqual(budget['maximum_attempts'], 4 * 8)
        self.assertEqual(budget['maximum_per_request_time_sum_seconds'], 8 * (120+240+120+240))
        self.assertEqual(budget['model_window_seconds'], budget['maximum_per_request_time_sum_seconds'] +
                         budget['loading_setup_and_overhead_allowance_seconds'])
        self.assertEqual(budget['maximum_rounds'], 1)

    def test_settings_change_only_explicit_limits_not_sampling(self):
        base = LocalAnswerSettings(model='meta-llama/Llama-3.1-8B-Instruct',revision='a'*40,
            tokenizer_revision='a'*40,template_sha256='b'*64,runtime=(),enable_thinking=None)
        with patch('p12_answer_interface_followup.settings_and_tokenizer', return_value=(base,object())) as loader:
            for c in CONDITIONS:
                result, _ = settings(c)
                self.assertEqual(replace(result,max_new_tokens=base.max_new_tokens,max_seconds=base.max_seconds),base)
                self.assertEqual(result.max_new_tokens,4096 if c.endswith(('thinking','cot')) else 1024)
                self.assertEqual(result.max_seconds,240 if c.endswith(('thinking','cot')) else 120)
            self.assertEqual(loader.call_args.args,('llama31_8b_direct',))


if __name__ == '__main__':
    unittest.main()
