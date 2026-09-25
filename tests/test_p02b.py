"""Offline fixture mechanics only: no model quality or token-coverage claims."""
from dataclasses import replace
import importlib.util
import json
from pathlib import Path
import tempfile
import unittest

from phi_jepa.artifacts import digest
from phi_jepa.integration.contracts import PublicProblem
from phi_jepa.integration.layout import StateLayout
from phi_jepa.providers.attempts import AttemptPolicy, AttemptRunner
from phi_jepa.providers.cache import FrozenOutputCache
from phi_jepa.providers.context import ContextEncoder, parse_notes
from phi_jepa.providers.contracts import (AttemptResult, EncoderSettings, FailureCode,
                                        ProviderFailure, Usage)
from test_p02a import fixture


class FixtureEncoder:
    """Deliberately artificial character tokenizer, never a model fallback."""
    settings = EncoderSettings('fixture', 'character-sum', 'fixture-v1', 'fixture-v1',
                               'fixture-v1', 'sum', 100000, 'float32', 'none', 2, 'fixture')

    def __init__(self):
        self.calls = 0
        self.texts = []

    def tokenize(self, text):
        self.texts.append(text)
        return tuple(text.encode('utf-8'))

    def encode_tokens(self, tokens):
        self.calls += 1
        return (float(sum(tokens)), float(len(tokens)))


class ProviderTests(unittest.TestCase):
    def setUp(self):
        self.public, _ = fixture()
        self.problem = PublicProblem.parse(self.public)

    def encode(self, encoder, problem=None, **kwargs):
        return encoder.encode(problem or self.problem, 0.2,
                              mode='public_base_for_offline_audit', **kwargs)

    def assert_code(self, code, operation):
        with self.assertRaises(ProviderFailure) as caught:
            operation()
        self.assertEqual(caught.exception.code, code)

    def test_public_serialization_retains_facts_without_metadata(self):
        backend = FixtureEncoder()
        result = self.encode(ContextEncoder(backend))
        context = json.loads(backend.texts[-1])
        self.assertEqual(context['Q'], self.public['input']['question'])
        self.assertEqual(context['C'], {k: v for k, v in self.public['input'].items() if k != 'question'})
        self.assertNotIn('sample_id', context)
        self.assertEqual(result.token_count, len(backend.texts[-1].encode()))

    def test_enrichment_cannot_modify_original_input_or_add_numeric_slots(self):
        original = self.problem.input_json
        proposal = parse_notes(self.problem, '{"notes":["Public note"]}')
        backend = FixtureEncoder()
        ContextEncoder(backend).encode(self.problem, 0.2, mode='enriched', enrichment=proposal)
        self.assertEqual(json.loads(backend.texts[-1])['public_enrichment'], ['Public note'])
        self.assertEqual(self.problem.input_json, original)
        proposal['public_input']['controller']['torque'] = 900
        with self.assertRaises(ValueError):
            ContextEncoder(backend).encode(self.problem, 0.2, mode='enriched', enrichment=proposal)
        self.assertEqual(self.problem.input_json, original)

    def test_notes_json_failures_and_missing_enrichment_have_no_fallback(self):
        for response, code in [('{', FailureCode.MALFORMED_JSON),
                ('{"notes":[],"notes":[]}', FailureCode.MALFORMED_JSON),
                ('{}', FailureCode.INCOMPLETE_JSON), ('[]', FailureCode.INCOMPLETE_JSON),
                ('{"notes":[],"predictions":{}}', FailureCode.INVALID_OUTPUT),
                ('{"notes":[{"label":"secret"}]}', FailureCode.INVALID_OUTPUT),
                ('{"notes":[0]}', FailureCode.INVALID_OUTPUT)]:
            with self.subTest(response=response):
                self.assert_code(code, lambda: parse_notes(self.problem, response))
        encoder = ContextEncoder(FixtureEncoder())
        self.assert_code(FailureCode.MISSING_BINDING, lambda: encoder.encode(self.problem, 0.2, mode='enriched'))
        self.assertEqual(encoder.coverage['model_calls'], 0)

    def test_cache_binds_exact_question_settings_and_content(self):
        with tempfile.TemporaryDirectory() as directory:
            backend = FixtureEncoder()
            encoder = ContextEncoder(backend, FrozenOutputCache(Path(directory)))
            first = self.encode(encoder)
            second = self.encode(encoder)
            self.assertEqual(first.values, second.values)
            self.assertTrue(second.cache_hit)
            self.assertEqual(backend.calls, 1)
            changed = json.loads(json.dumps(self.public))
            changed['input']['question'] = 'Another permitted question?'
            third = self.encode(encoder, PublicProblem.parse(changed))
            self.assertNotEqual(first.request_sha256, third.request_sha256)
            self.assertNotEqual(first.values, third.values)
            backend.settings = replace(backend.settings, model_revision='fixture-v2')
            fourth = self.encode(encoder)
            self.assertNotEqual(first.request_sha256, fourth.request_sha256)
            self.assertEqual(backend.calls, 3)

    def test_corrupt_cache_fails_without_reencoding(self):
        with tempfile.TemporaryDirectory() as directory:
            backend = FixtureEncoder()
            encoder = ContextEncoder(backend, FrozenOutputCache(Path(directory)))
            self.encode(encoder)
            path = next(Path(directory).glob('*.json'))
            record = json.loads(path.read_text())
            record['output']['values'][0] += 1
            path.write_text(json.dumps(record))
            self.assert_code(FailureCode.CACHE_INTEGRITY, lambda: self.encode(encoder))
            self.assertEqual(backend.calls, 1)

    def test_overlength_measured_before_model_call(self):
        backend = FixtureEncoder()
        backend.settings = replace(backend.settings, max_length=4)
        encoder = ContextEncoder(backend)
        self.assert_code(FailureCode.OVERLENGTH, lambda: self.encode(encoder))
        self.assertEqual(backend.calls, 0)
        self.assertGreater(encoder.token_lengths[0], 4)
        self.assertEqual(encoder.coverage['overlength'], 1)
        self.assertEqual(encoder.coverage['accepted'], 0)

    def test_pre_cutoff_context_rejected_before_tokenization(self):
        backend = FixtureEncoder()
        with self.assertRaises(ValueError):
            ContextEncoder(backend).encode(self.problem, 0.0, mode='public_base_for_offline_audit')
        self.assertFalse(backend.texts)

    def test_unpinned_or_missing_encoder_settings_fail(self):
        for edit in ({'model_revision': 'main'}, {'tokenizer_revision': None},
                     {'pooling': ''}, {'max_length': True}):
            with self.subTest(edit=edit), self.assertRaises(ValueError):
                replace(FixtureEncoder.settings, **edit)

    def test_invalid_embedding_never_cached(self):
        with tempfile.TemporaryDirectory() as directory:
            backend = FixtureEncoder()
            backend.encode_tokens = lambda _: (float('nan'), 1.0)
            encoder = ContextEncoder(backend, FrozenOutputCache(Path(directory)))
            self.assert_code(FailureCode.INVALID_OUTPUT, lambda: self.encode(encoder))
            self.assertFalse(list(Path(directory).glob('*.json')))

    def test_retry_accounting_unknown_usage_and_exhaustion(self):
        runner = AttemptRunner(AttemptPolicy(3, 3, 2.0))
        timeouts = []
        def fail(timeout):
            timeouts.append(timeout)
            raise TimeoutError('sensitive adapter message must not be logged')
        self.assert_code(FailureCode.RETRY_EXHAUSTED, lambda: runner.run('key', fail, str))
        self.assertEqual(timeouts, [2.0] * 3)
        self.assertEqual(len(runner.events), 3)
        self.assertIsNone(runner.events[0]['usage']['cost_usd'])
        self.assertNotIn('sensitive', json.dumps(runner.events))
        self.assert_code(FailureCode.BUDGET_EXHAUSTED, lambda: runner.run('key', fail, str))
        self.assertEqual(len(timeouts), 3)

    def test_success_after_timeout_and_no_retry_on_content_failure(self):
        runner = AttemptRunner(AttemptPolicy(3, 4, 2.0))
        results = iter([AttemptResult(Usage(None, None, None), failure=FailureCode.TIMEOUT),
                        AttemptResult(Usage(10, 5, 0.02), text='{"notes":[]}')])
        result = runner.run('key', lambda _: next(results), lambda t: parse_notes(self.problem, t))
        self.assertEqual(result['notes'], [])
        self.assertEqual(len(runner.events), 2)
        self.assertEqual(runner.events[1]['usage']['cost_usd'], 0.02)  # synthetic accounting only
        self.assert_code(FailureCode.MALFORMED_JSON, lambda: runner.run('bad',
            lambda _: AttemptResult(Usage(10, 1, 0.01), text='{'), lambda t: parse_notes(self.problem, t)))
        self.assertEqual(len(runner.events), 3)

    def test_terminal_failures_count_once_and_sanitize_exceptions(self):
        for code in (FailureCode.REFUSAL, FailureCode.MISSING_CREDENTIALS,
                     FailureCode.MISSING_BINDING, FailureCode.INCOMPATIBLE_UNITS):
            runner = AttemptRunner(AttemptPolicy(3, 3, 1.0))
            self.assert_code(code, lambda: runner.run('key',
                lambda _: AttemptResult(Usage(None, None, None), failure=code), str))
            self.assertEqual(len(runner.events), 1)
        runner = AttemptRunner(AttemptPolicy(3, 3, 1.0))
        def unexpected(_):
            raise RuntimeError('secret')
        self.assert_code(FailureCode.INVALID_OUTPUT, lambda: runner.run('key', unexpected, str))
        self.assertNotIn('secret', json.dumps(runner.events))


@unittest.skipUnless(importlib.util.find_spec('torch'), 'P02b tensor gate pending: isolated core Torch unavailable')
class ProjectionTests(unittest.TestCase):
    def setUp(self):
        import torch
        from phi_jepa.models.context_projection import ContextProjection, ProjectionSettings
        self.torch = torch
        public, _ = fixture()
        inp = public['input']
        self.layout = StateLayout.build(inp['states'][-1], inp, 'state_plus_fixed_conditioning', 'train')
        self.projection = ContextProjection(self.layout, ProjectionSettings(2))
        self.e = torch.tensor([[1.0, 2.0]])
        self.n = torch.ones(1, self.layout.d)

    def pair(self):
        return self.projection.pair(self.n, self.n * 2, self.e, layout_sha256=self.layout.sha256)

    def test_both_gradient_paths_and_projection_recomputed(self):
        torch = self.torch
        x, y, p = self.pair()
        self.assertEqual(x.shape[1], 2 * self.layout.d)
        torch.testing.assert_close(x[:, self.layout.d:], y[:, self.layout.d:])
        # A stand-in differentiable map exposes independent input and target paths;
        # this is not an implemented ODE or empirical training run.
        prediction = x * 2
        loss = ((prediction - y) ** 2).mean()
        parameter = self.projection.linear.weight
        full = torch.autograd.grad(loss, parameter, retain_graph=True)[0]
        input_only = torch.autograd.grad(((prediction - y.detach()) ** 2).mean(), parameter, retain_graph=True)[0]
        target_only = torch.autograd.grad(((prediction.detach() - y) ** 2).mean(), parameter)[0]
        self.assertGreater(input_only.abs().sum().item(), 0)
        self.assertGreater(target_only.abs().sum().item(), 0)
        torch.testing.assert_close(full, input_only + target_only)
        previous = p.detach().clone()
        optimizer = torch.optim.SGD(self.projection.parameters(), lr=0.1)
        parameter.grad = full
        optimizer.step()
        self.assertFalse(torch.equal(previous, self.pair()[2]))

    def test_frozen_encoder_stays_eval_through_parent_train(self):
        from phi_jepa.models.context_projection import FrozenModule
        torch = self.torch
        encoder = FrozenModule(torch.nn.Sequential(torch.nn.Linear(2, 2), torch.nn.Dropout(0.9)))
        parent = torch.nn.ModuleList([encoder, self.projection])
        parent.train()
        self.assertFalse(encoder.encoder.training)
        self.assertTrue(self.projection.training)
        e = encoder(self.e.requires_grad_())
        self.assertFalse(e.requires_grad)
        self.projection(e).sum().backward()
        self.assertTrue(all(p.grad is None and not p.requires_grad for p in encoder.parameters()))
        self.assertIsNotNone(self.projection.linear.weight.grad)

    def test_layout_mismatch_and_initialization_reproducibility(self):
        from phi_jepa.models.context_projection import ContextProjection
        torch = self.torch
        rng = torch.random.get_rng_state().clone()
        other = ContextProjection(self.layout, self.projection.settings)
        torch.testing.assert_close(rng, torch.random.get_rng_state())
        torch.testing.assert_close(self.projection(self.e), other(self.e))
        with self.assertRaises(ValueError):
            self.projection.pair(self.n, self.n, self.e, layout_sha256='wrong-layout')
        with self.assertRaises(ValueError):
            self.projection(self.e.requires_grad_())


if __name__ == '__main__':
    unittest.main()
