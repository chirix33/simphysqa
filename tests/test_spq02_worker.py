"""Synthetic software probes of replay/failure policy, with zero real simulations."""
from copy import deepcopy
from pathlib import Path
from types import SimpleNamespace
import importlib.util,os,tempfile,unittest
from unittest.mock import patch
from simphysqa.io import read,write

class ReplayPolicySoftwareTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        if not importlib.util.find_spec('numpy'):raise unittest.SkipTest('replay policy tests need the pinned simulator runtime; do not install into CPU annotation environment')
        path=os.environ.get('SIMPHYSQA_SPQ02_PLAN')
        if not path:raise unittest.SkipTest('set frozen existing-development plan')
        from simphysqa import spq02_worker
        cls.worker=spq02_worker;cls.plan=read(Path(path))

    def test_exact_criterion_distinct_from_answer_tolerance(self):
        # Stored records stand in for a rollout ONLY to test comparator software.
        for pair in self.plan['pairs'][:4]:
            source=pair['source_records'][0]
            result=SimpleNamespace(states=deepcopy(source['input']['states']+source['reference']['states']),
                events=deepcopy(source['reference']['events']),
                public={k:deepcopy(source['input'][k]) for k in ('entities','global_context','controller','known_events','coordinate_convention')})
            self.assertTrue(self.worker.replay(result,[source],self.plan)['passed'])
            numeric=next(m for m in result.states[-1]['measurements'] if type(m['value']) is float or isinstance(m['value'],list))
            if isinstance(numeric['value'],list):numeric['value'][0]+=1e-7
            else:numeric['value']+=1e-7
            self.assertFalse(self.worker.replay(result,[source],self.plan)['passed'])

    def test_frame_and_private_event_changes_fail_comparison(self):
        source=self.plan['pairs'][0]['source_records'][0]
        result=SimpleNamespace(states=deepcopy(source['input']['states']+source['reference']['states']),
            events=deepcopy(source['reference']['events']),public={})
        result.states[0]['measurements'][0]['frame']='WRONG'
        self.assertFalse(self.worker.replay(result,[source],self.plan)['passed'])
        result.states=deepcopy(source['input']['states']+source['reference']['states']);result.events=[]
        self.assertFalse(self.worker.replay(result,[source],self.plan)['passed'])

    def test_missing_decision_does_not_reserve_or_simulate(self):
        with tempfile.TemporaryDirectory() as tmp:
            root=Path(tmp);write(root/'plan.json',self.plan)
            with patch.object(self.worker,'adapter') as adapter:
                with self.assertRaisesRegex(ValueError,'criterion pending'):self.worker.run(root/'plan.json',root/'runs')
                adapter.assert_not_called()
            self.assertFalse((root/'runs').exists())

    def test_simulator_exception_has_durable_failure_receipt(self):
        with tempfile.TemporaryDirectory() as tmp:
            path=Path(tmp)/'software-failure.json'
            with patch.object(self.worker,'adapter') as adapter:
                adapter.return_value.simulate.side_effect=RuntimeError('SYNTHETIC_TEST_ONLY_FAILURE')
                self.worker.simulate_to_file(self.plan['pairs'][0],.0001,True,path,'test-only-reservation')
                adapter.return_value.simulate.assert_called_once()
            result=read(path)
            self.assertEqual(result['status'],'failed');self.assertIn('SYNTHETIC_TEST_ONLY_FAILURE',result['error'])
            self.assertEqual(result['reservation_sha256'],'test-only-reservation')

    def test_prerequisite_failures_resume_without_calls_or_overwrite(self):
        with tempfile.TemporaryDirectory() as tmp:
            root=Path(tmp);plan=deepcopy(self.plan);plan['replay_criterion']['status']='approved'
            plan['replay_criterion']['authority']='SYNTHETIC_SOFTWARE_TEST_ONLY_NOT_A_SCIENTIFIC_DECISION'
            write(root/'plan.json',plan)
            with patch.object(self.worker.importlib.metadata,'version',return_value='test-only-mismatch'),patch.object(self.worker,'adapter') as adapter:
                first=self.worker.run(root/'plan.json',root/'runs')
                before={p.relative_to(root/'runs').as_posix():p.read_bytes() for p in (root/'runs').rglob('*') if p.is_file()}
                second=self.worker.run(root/'plan.json',root/'runs')
                after={p.relative_to(root/'runs').as_posix():p.read_bytes() for p in (root/'runs').rglob('*') if p.is_file()}
                adapter.assert_not_called()
            self.assertEqual(first['failed_pairs'],8);self.assertEqual(second['execution_reservations'],0)
            self.assertEqual(before,after)

    def test_existing_physics_threshold_edges(self):
        result=SimpleNamespace(diagnostics={'min_forward_velocity':-.02})
        self.assertTrue(self.worker.physics(result,'driving'))
        result.diagnostics['min_forward_velocity']=-.020001
        self.assertFalse(self.worker.physics(result,'driving'))
        result.diagnostics={'min_tension_N':1.,'max_length_error_m':0.}
        self.assertTrue(self.worker.physics(result,'tethered_load'))
        result.diagnostics['max_length_error_m']=1e-6
        self.assertFalse(self.worker.physics(result,'tethered_load'))

if __name__=='__main__':unittest.main()
