"""Offline transport fixtures. No network calls or real credentials."""
import importlib.util
import json
from pathlib import Path
import tempfile
import unittest

from phi_jepa.integration.contracts import PublicProblem
from phi_jepa.providers.cache import FrozenOutputCache
from phi_jepa.providers.contracts import FailureCode, ProviderFailure
from phi_jepa.providers.credentials import load_openai_key
from phi_jepa.providers.openai_enrichment import OpenAIEnrichment, response_result
from test_p02a import fixture

ROOT = Path(__file__).resolve().parents[1]


def response(text='{"notes":["The supplied quantity uses metres."]}', **changes):
    result = {'status': 'completed', 'id': 'fixture-response', 'model': 'gpt-5.6-sol',
        'usage': {'input_tokens': 100, 'output_tokens': 10, 'input_tokens_details': {'cached_tokens': 20}},
        'output': [{'type': 'message', 'content': [{'type': 'output_text', 'text': text}]}]}
    result.update(changes)
    return result


class LiveBoundaryTests(unittest.TestCase):
    def setUp(self):
        self.problem = PublicProblem.parse(fixture()[0])
        self.asset = json.loads((ROOT / 'docs/assets/p02b_enrichment_v1.json').read_text())
        self.config = {'model': 'gpt-5.6-sol', 'reasoning_effort': 'medium',
            'max_output_tokens': 2048, 'max_attempts_per_request': 3,
            'max_total_attempts': 24, 'timeout_seconds': 120}

    def test_request_only_contains_public_context_and_no_tools(self):
        requests = []
        def transport(payload, timeout):
            requests.append(payload)
            self.assertEqual(timeout, 120)
            return response()
        with tempfile.TemporaryDirectory() as directory:
            provider = OpenAIEnrichment('synthetic-credential', self.config, self.asset,
                                       FrozenOutputCache(Path(directory)), transport=transport)
            before = self.problem.input_json
            first = provider.enrich(self.problem, 0.2)
            second = provider.enrich(self.problem, 0.2)
            self.assertEqual(first, second)
            self.assertEqual(self.problem.input_json, before)
            self.assertEqual(len(requests), 1)
            self.assertEqual(provider.cache_hits, 1)
            self.assertEqual(requests[0]['input'], self.problem.context(0.2))
            self.assertFalse(requests[0]['store'])
            self.assertNotIn('tools', requests[0])
            self.assertNotIn('synthetic-credential', json.dumps(provider.runner.events))
            self.assertAlmostEqual(provider.runner.events[0]['usage']['cost_usd'], 0.000528)

    def test_schema_prompt_and_revision_changes_invalidate_enrichment_cache(self):
        with tempfile.TemporaryDirectory() as directory:
            cache = FrozenOutputCache(Path(directory))
            count = []
            def transport(*_):
                count.append(1)
                return response()
            for edition in ('v1', 'v2'):
                asset = {**self.asset, 'version': edition}
                OpenAIEnrichment('fixture', self.config, asset, cache, transport=transport).enrich(self.problem, 0.2)
            self.assertEqual(len(count), 2)

    def test_refusal_and_incomplete_keep_usage(self):
        refused = response(output=[{'type': 'message', 'content': [{'type': 'refusal', 'refusal': 'fixture'}]}])
        for body, code in ((refused, FailureCode.REFUSAL), (response(status='incomplete'), FailureCode.INCOMPLETE_JSON)):
            result = response_result(body)
            self.assertEqual(result.failure, code)
            self.assertEqual(result.usage.output_tokens, 10)

    def test_resume_retains_attempts_and_dispatch_is_durable(self):
        saved = []
        ledger = {'events': [{'attempt': 1, 'request_sha256': 'old', 'failure': 'timeout',
                             'usage': {'input_tokens': None, 'output_tokens': None, 'cost_usd': None}}],
                  'responses': []}
        def transport(*_):
            self.assertEqual(len(saved[-1]['events']), 2)
            return response()
        provider = OpenAIEnrichment('fixture', self.config, self.asset, None, transport=transport,
            ledger=ledger, event_sink=lambda event: saved.append(json.loads(json.dumps(event))))
        provider.enrich(self.problem, 0.2)
        self.assertEqual(len(provider.runner.events), 2)
        self.assertEqual(saved[-1]['events'][0]['failure'], 'timeout')
        self.assertEqual(saved[-1]['events'][1]['usage']['output_tokens'], 10)

    def test_bad_notes_fail_once_and_do_not_cache(self):
        with tempfile.TemporaryDirectory() as directory:
            provider = OpenAIEnrichment('fixture', self.config, self.asset,
                FrozenOutputCache(Path(directory)), transport=lambda *_: response('{"notes":[1]}'))
            with self.assertRaises(ProviderFailure):
                provider.enrich(self.problem, 0.2)
            self.assertEqual(len(provider.runner.events), 1)
            self.assertEqual(provider.runner.events[0]['usage']['output_tokens'], 10)
            self.assertFalse(list(Path(directory).glob('*.json')))

    @unittest.skipUnless(importlib.util.find_spec('dotenv'), 'python-dotenv absent in legacy Windows runtime')
    def test_dotenv_references_key_without_environment_mutation(self):
        import os
        before = dict(os.environ)
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory)
            (path / '.env').write_text('OPENAI_API_KEY_FILE=key.txt\n')
            (path / 'key.txt').write_text('synthetic-only\n')
            self.assertEqual(load_openai_key(path / '.env'), 'synthetic-only')
            self.assertEqual(dict(os.environ), before)
            (path / 'key.txt').unlink()
            with self.assertRaises(ProviderFailure) as caught:
                load_openai_key(path / '.env')
            self.assertEqual(caught.exception.code, FailureCode.MISSING_CREDENTIALS)


if __name__ == '__main__':
    unittest.main()
