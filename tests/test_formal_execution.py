"""Offline ceiling/recovery/scope controls; no provider or simulator calls."""
from copy import deepcopy
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch
from simphysqa.formal_live import admit_annotation, LIMITS, CeilingReached, simulation_wall, simulate
from simphysqa.formal_scope import formal_scope
from simphysqa.io import write, digest

class FormalExecutionTests(unittest.TestCase):
    def test_all_annotation_axes_block_before_request(self):
        bound={'usd':1,'input_token_upper_bound':10,'output_token_limit':20}
        history=[{'initial_request':True,'charged_upper_bound_usd':1,'reservation':bound,'wall_seconds':120}]
        admit_annotation(history,bound,False)
        for key,value,initial in [('total_attempts',1,False),('initial_requests',1,True),('usd_cap',1.9,False),
                                  ('total_input_tokens',19,False),('total_output_tokens',39,False),('wall_seconds',239,False)]:
            budget=deepcopy(LIMITS);budget[key]=value
            with self.subTest(key=key),self.assertRaises(CeilingReached):admit_annotation(history,bound,initial,budget)
    def test_completed_worker_receipt_replaces_unknown_full_reservation(self):
        with tempfile.TemporaryDirectory() as folder:
            root=Path(folder)
            write(root/'simulation-work/a.json',{'reserved_wall_seconds':3600})
            self.assertEqual(simulation_wall(root),3600)
            write(root/'simulation-work-completed/a.json',{'wall_seconds':12})
            self.assertEqual(simulation_wall(root),12)
            write(root/'simulation-work/b.json',{'reserved_wall_seconds':180,'model_compilations':1})
            self.assertEqual(simulation_wall(root),192)
    def test_saved_solve_reuse_before_budget_admission(self):
        with tempfile.TemporaryDirectory() as folder:
            root=Path(folder);pair={'pair_id':'p'};candidate={'candidate_id':'c'}
            write(root/'cases/c/simulation-plan.json',{'pairs':[pair]})
            write(root/'cases/c/runs/pairs/p.json',{'status':'completed'})
            write(root/'simulation-work/a.json',{'reserved_wall_seconds':3600})
            with patch('simphysqa.formal_live.verify_manifest'),patch('simphysqa.formal_live.subprocess.run',side_effect=AssertionError('no new solve')):
                result,runs=simulate(pair,candidate,root,{})
            self.assertEqual(result['status'],'completed')
    def test_scoped_guard_catches_only_exact_final_membership_error(self):
        from simphysqa import explanation,clarification
        source={'metadata':{'split_group_id':'g'}}
        record={'trajectory_id':'g','private':{'metadata':{'split_group_id':'g'}}}
        candidates=[{'source':{'group_id':'g','source':{'record_sha256':digest(source)}}}]
        original_e=explanation.validate_explanation
        with patch('simphysqa.formal_scope.restore',return_value=source),patch.object(explanation,'validate_explanation',side_effect=ValueError('explanation development group missing formal exclusion')):
            mocked=explanation.validate_explanation
            with formal_scope(candidates,[]):self.assertTrue(explanation.validate_explanation(record))
            self.assertIs(explanation.validate_explanation,mocked)
        self.assertIs(explanation.validate_explanation,original_e)
        with patch('simphysqa.formal_scope.restore',return_value=source),patch.object(clarification,'validate_clarification',side_effect=ValueError('acceptance regions overlap')):
            with formal_scope(candidates,[]),self.assertRaisesRegex(ValueError,'overlap'):clarification.validate_clarification(record)
        with self.assertRaisesRegex(ValueError,'duplicate/excluded'):
            with formal_scope(candidates,['g']):pass
        with patch('simphysqa.formal_scope.restore',return_value={'metadata':{'split_group_id':'different'}}),patch.object(clarification,'validate_clarification',side_effect=ValueError('development exclusion missing')):
            with formal_scope(candidates,[]),self.assertRaisesRegex(ValueError,'exclusion'):clarification.validate_clarification(record)

if __name__=='__main__':unittest.main()
