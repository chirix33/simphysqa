"""Contract-preserving post-P07 regressions; no providers or pretrained downloads."""
import tempfile
import unittest
from collections import Counter

import torch

from phi_jepa.coordinate_diagnostics import decompose, coordinate_unit
from phi_jepa.integration.readers import make_pairs
from phi_jepa.baselines.custom_checkpoint import save_checkpoint, load_checkpoint
import test_p02a
from test_p06 import model


class PostP07Tests(unittest.TestCase):
    def test_default_equal_question_pairs_and_explicit_historical_policy(self):
        fixture = test_p02a.P02aTests(); fixture.setUp()
        original = fixture.pairs()
        multiplicity = Counter({p.transition_id: 3 for p in original})
        args = (fixture.problem, fixture.ref, fixture.identity, fixture.layout, 'test', multiplicity)
        current = list(make_pairs(*args))
        legacy = list(make_pairs(*args, duplicate_policy='inverse_transition_multiplicity'))
        self.assertEqual([p.weight for p in current], [1., 1.])
        self.assertEqual([p.weight for p in legacy], [1/3, 1/3])

    def test_coordinate_contributions_conserve_raw_mse(self):
        columns = [{'name': 'x', 'unit': 'm', 'group': 'physical'},
                   {'name': 'index', 'unit': 'count', 'group': 'index'}]
        result = decompose([[1., 2.], [3., 4.]], [[0., 0.], [0., 0.]], columns)
        self.assertEqual(result['raw_numerical_mse'], 7.5)
        self.assertEqual([r['coordinate_mse'] for r in result['coordinates']], [5., 10.])
        self.assertEqual(sum(r['raw_numerical_mse_contribution'] for r in result['coordinates']), 7.5)
        self.assertAlmostEqual(sum(g['fraction_of_raw_mse'] for g in result['groups'].values()), 1.)
        for predictions, targets in (([[1.]], [[0., 0.]]), ([[float('nan'), 0]], [[0, 0]]), ([], [])):
            with self.assertRaises(ValueError): decompose(predictions, targets, columns)

    def test_time_and_relative_tolerance_do_not_inherit_target_unit(self):
        parent = (('key', 'answer_spec'), ('target', 'load', 'position'))
        structure = {parent + (('key', 'unit'),): 'm'}
        self.assertEqual(coordinate_unit(parent + (('key', 'end_time'),), structure), 's')
        self.assertEqual(coordinate_unit(parent + (('key', 'relative_tolerance'),), structure), '1')
        self.assertEqual(coordinate_unit(parent + (('key', 'absolute_tolerance'),), structure), 'm')

    def test_standalone_resume_restores_gradient_checkpointing(self):
        m = model(); m.t5.gradient_checkpointing_enable(gradient_checkpointing_kwargs={'use_reentrant': False})
        optimizer = torch.optim.AdamW(p for p in m.parameters() if p.requires_grad)
        identity = {'config': {'correctness': {'gradient_checkpointing': True}}}
        with tempfile.TemporaryDirectory() as directory:
            save_checkpoint(directory, m, optimizer, identity=identity, updates=0)
            restored, opt, updates = load_checkpoint(directory, identity=identity, training=True)
            self.assertTrue(restored.t5.is_gradient_checkpointing)
            self.assertTrue(restored.training)
            self.assertEqual(updates, 0)
            self.assertEqual(len(opt.param_groups[0]['params']), sum(p.requires_grad for p in restored.parameters()))

    def test_generation_condition_cannot_be_mislabeled(self):
        ids = torch.tensor([[4, 1]])
        for method, wrong in (('coconut_inspired_t5_gru', 'student'), ('codi_inspired_t5_distillation', 'coconut')):
            m = model(method)
            with self.assertRaisesRegex(ValueError, 'generation_branch_method_mismatch'):
                m.generate(ids, torch.ones_like(ids), branch=wrong, generation={})


if __name__ == '__main__': unittest.main()
