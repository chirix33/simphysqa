"""Behavioral numerical tests. Fixtures are not empirical model performance."""
from collections import Counter
from dataclasses import replace
import importlib.util
import json
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest

from phi_jepa.artifacts import digest
from phi_jepa.integration.contracts import PublicProblem, Identity
from phi_jepa.integration.layout import StateLayout
from phi_jepa.integration.readers import make_pairs
from test_p02a import fixture


@unittest.skipUnless(importlib.util.find_spec('torch'), 'requires isolated core Torch')
class P03Tests(unittest.TestCase):
    def setUp(self):
        import torch
        from phi_jepa.models.augmented_ode import AugmentedODE, ODESettings
        from phi_jepa.models.context_projection import ProjectionSettings
        from phi_jepa.solvers.rk4 import SolverSettings
        from phi_jepa.training.pairs import PairTrainer, TrainingSettings
        self.torch = torch
        self.problem = PublicProblem.parse(fixture()[0])
        self.reference = fixture()[1]
        inp = self.problem.input
        self.layout = StateLayout.build(inp['states'][-1], inp, 'state_plus_fixed_conditioning', 'train')
        self.model = AugmentedODE(self.layout, ProjectionSettings(2), ODESettings(hidden_width=8))
        self.solver = SolverSettings(2)
        self.trainer = PairTrainer(self.model, self.solver, TrainingSettings())
        self.e = torch.tensor([[0.4, 0.7], [0.4, 0.7]])
        mult = Counter({digest(('robotic_arm','group', a,b)): 3 for a,b in ((0.2,0.22),(0.22,0.24))})
        self.pairs = list(make_pairs(self.problem, self.reference,
            Identity('sample','group','group','robotic_arm','train'), self.layout, 'fixture-provenance', mult,
            context_mode='enriched', enrichment={'public_input': inp, 'notes': []},
            duplicate_policy='equal_question_pairs'))

    def test_equal_pair_weight_and_joint_parameter_updates(self):
        torch = self.torch
        self.assertEqual([p.weight for p in self.pairs], [1, 1])
        before = {k: v.clone() for k, v in self.model.state_dict().items()}
        log = self.trainer.step(self.pairs, self.e)
        self.assertTrue(any(not torch.equal(v, self.model.state_dict()[k]) for k,v in before.items() if k.startswith('projection.')))
        self.assertTrue(any(not torch.equal(v, self.model.state_dict()[k]) for k,v in before.items() if k.startswith('field.')))
        self.assertEqual(log['stats']['nfe'], 8)
        self.assertEqual(log['stats']['sample_nfe'], 16)
        self.assertGreater(log['projection_gradient_norm_after_clip'], 0)

    def test_target_state_and_both_context_gradient_paths_affect_loss(self):
        from phi_jepa.solvers.rk4 import rk4, SolveStats
        torch = self.torch
        current = torch.tensor([p.n_current for p in self.pairs])
        next_n = torch.tensor([p.n_next for p in self.pairs])
        x, y, p = self.model.projection.pair(current, next_n, self.e, layout_sha256=self.layout.sha256)
        pred = rk4(self.model, x, 0.2, 0.22, self.solver, SolveStats())
        param = self.model.projection.linear.weight
        loss = ((pred-y)**2).mean()
        full = torch.autograd.grad(loss, param, retain_graph=True)[0]
        incoming = torch.autograd.grad(((pred-y.detach())**2).mean(), param, retain_graph=True)[0]
        target = torch.autograd.grad(((pred.detach()-y)**2).mean(), param)[0]
        self.assertGreater(target.abs().sum().item(), 0)
        self.assertGreater(incoming.abs().sum().item(), 0)
        torch.testing.assert_close(full, incoming+target, rtol=1e-4, atol=1e-8)
        changed = y.detach().clone(); changed[0, 0] += 4
        self.assertNotEqual(float(loss.detach()), float(((pred.detach()-changed)**2).mean()))

    def test_rk4_refinement_physical_times_batches_and_counts(self):
        from phi_jepa.solvers.rk4 import rk4, SolveStats, SolverSettings
        torch = self.torch
        x = torch.ones(2, 4)
        stats = SolveStats()
        coarse = rk4(lambda t,x: x, x, [0., 0.], [1., 0.5], SolverSettings(1), stats)
        fine = rk4(lambda t,x: x, x, [0., 0.], [1., 0.5], SolverSettings(8), stats)
        expected = torch.exp(torch.tensor([[1.], [0.5]])).expand_as(x)
        self.assertLess((fine-expected).abs().max(), (coarse-expected).abs().max())
        timed = rk4(lambda t,x: t.expand_as(x), x[:1], 2., 3., SolverSettings(1), stats)
        torch.testing.assert_close(timed, torch.full((1,4), 3.5))
        self.assertEqual(stats.nfe, 40)
        with self.assertRaises(ValueError):
            rk4(lambda t,x:x, x, 0.2, 0.2, SolverSettings(), stats)
        self.assertEqual(stats.failures, 1)

    def test_full_prediction_feedback_and_reference_independence(self):
        from phi_jepa.inference.rollout import rollout
        from phi_jepa.solvers.rk4 import SolveStats, SolverSettings
        torch = self.torch
        seen = []
        d = self.layout.d
        def field(t, x):
            seen.append(x.clone())
            return torch.cat((x[:, d:], torch.ones_like(x[:, d:])), dim=1)
        self.model.forward = field
        original_p = self.model.projection(self.e[:1]).detach()
        first = rollout(self.model, self.problem, self.e[:1], [0.2,0.22,0.24], SolverSettings(), SolveStats())
        torch.testing.assert_close(seen[4][0], torch.tensor(first.predictions[0].values))
        torch.testing.assert_close(seen[4][:, d:], original_p + 0.02)
        self.reference.clear()  # deployment never receives a reference handle
        second = rollout(self.model, self.problem, self.e[:1], [0.2,0.22,0.24], SolverSettings(), SolveStats())
        self.assertEqual(first, second)
        with self.assertRaises(ValueError):
            rollout(self.model, self.problem, self.e[:1], [0.,0.24], SolverSettings(), SolveStats())

    def test_checkpoint_deterministic_resume_and_role_integrity(self):
        from phi_jepa.training.checkpoint import write_checkpoint, load_checkpoint
        torch = self.torch
        self.trainer.step(self.pairs, self.e)
        with tempfile.TemporaryDirectory() as directory:
            write_checkpoint(directory, self.trainer, context_identity='E-pinned',
                provenance={'pair_ids':[p.pair_id for p in self.pairs]}, sampler_state={'epoch':1,'position':0})
            expected_rng = torch.rand(4)
            expected = self.trainer.step(self.pairs, self.e)
            state = {k:v.clone() for k,v in self.model.state_dict().items()}
            restored, sampler, provenance = load_checkpoint(directory, layout=self.layout, context_identity='E-pinned', training=True)
            torch.testing.assert_close(torch.rand(4), expected_rng, rtol=0, atol=0)
            actual = restored.step(self.pairs, self.e)
            self.assertEqual(actual['loss'], expected['loss'])
            self.assertEqual(actual['stats'], expected['stats'])
            for key,value in state.items():
                torch.testing.assert_close(restored.model.state_dict()[key], value, rtol=0, atol=0)
            self.assertEqual(sampler, {'epoch':1,'position':0})
            with self.assertRaises(ValueError):
                load_checkpoint(directory, layout=self.layout, context_identity='different-E', training=True)
            with self.assertRaises(ValueError):
                load_checkpoint(directory, layout=self.layout, context_identity='E-pinned', training=False)
            pointer = json.loads((Path(directory)/'latest.json').read_text())
            path = Path(directory)/pointer['file']; path.write_bytes(path.read_bytes()+b'corrupt')
            with self.assertRaises(ValueError):
                load_checkpoint(directory, layout=self.layout, context_identity='E-pinned', training=True)

    def test_deployment_fresh_process_parity_and_wrong_layout(self):
        from phi_jepa.training.checkpoint import write_checkpoint, load_checkpoint
        from phi_jepa.inference.rollout import rollout
        from phi_jepa.solvers.rk4 import SolveStats
        with tempfile.TemporaryDirectory() as directory:
            write_checkpoint(directory, self.trainer, context_identity='E-pinned', provenance={}, sampler_state={}, deployment=True)
            with self.assertRaises(ValueError):
                load_checkpoint(directory, layout=replace(self.layout, domain='driving'), context_identity='E-pinned', training=False)
            (Path(directory)/'input.json').write_text(json.dumps({'public':fixture()[0], 'embedding':self.e[:1].tolist(), 'layout':self.layout.manifest()}))
            code = '''import json,sys,torch
from pathlib import Path
from phi_jepa.artifacts import digest
from phi_jepa.integration.contracts import PublicProblem
from phi_jepa.integration.layout import StateLayout
from phi_jepa.training.checkpoint import load_checkpoint
from phi_jepa.inference.rollout import rollout
from phi_jepa.solvers.rk4 import SolveStats
p=Path(sys.argv[1]); data=json.loads((p/'input.json').read_text())
layout=StateLayout.from_manifest(data['layout'],digest(data['layout']))
model,solver=load_checkpoint(p,layout=layout,context_identity='E-pinned',training=False)
result=rollout(model,PublicProblem.parse(data['public']),torch.tensor(data['embedding']),[0.2,0.22,0.24],solver,SolveStats())
print(json.dumps([x.values for x in result.predictions]))
'''
            actual = json.loads(subprocess.check_output([sys.executable,'-c',code,directory],text=True))
            expected = rollout(self.model,self.problem,self.e[:1],[0.2,0.22,0.24],self.solver,SolveStats())
            self.assertEqual(actual,[list(x.values) for x in expected.predictions])

    def test_invalid_supervision_and_nonfinite_solver_fail_explicitly(self):
        from phi_jepa.solvers.rk4 import rk4, SolveStats
        for change in ({'weight':0.5}, {'context_mode':'public_base_for_offline_audit'},
                       {'registry_sha256':'wrong'}):
            with self.subTest(change=change), self.assertRaises(ValueError):
                self.trainer.step([replace(self.pairs[0],**change)],self.e[:1])
        stats = SolveStats()
        with self.assertRaises(ValueError):
            rk4(lambda t,x:x*float('inf'),self.torch.ones(1,2),0.,1.,self.solver,stats)
        self.assertEqual((stats.nfe,stats.failures),(1,1))
        self.assertEqual((self.trainer.attempted_updates,self.trainer.failed_updates),(3,3))

    def test_nonfinite_optimizer_update_restores_last_finite_state(self):
        torch = self.torch
        before = {k:v.clone() for k,v in self.model.state_dict().items()}
        def corrupt():
            with torch.no_grad():
                self.model.field[-1].weight.fill_(float('inf'))
        self.trainer.optimizer.step = corrupt
        with self.assertRaises(ValueError):
            self.trainer.step(self.pairs,self.e)
        for key,value in before.items():
            torch.testing.assert_close(value,self.model.state_dict()[key],rtol=0,atol=0)
        self.assertEqual((self.trainer.updates,self.trainer.failed_updates),(0,1))


if __name__ == '__main__': unittest.main()
