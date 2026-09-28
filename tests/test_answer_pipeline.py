"""Offline runner contracts. Mock answers are not empirical model evidence."""
import json
from pathlib import Path
import sys
import tempfile
import unittest
from contextlib import redirect_stdout
import io
from unittest.mock import patch

sys.path.insert(0, str(Path(__file__).resolve().parents[1]/'tools'))
import answer_pipeline as runner
from test_p04a import example, llm_result
from phi_jepa.inference.readout import read_targets, target_result
from phi_jepa.providers.openai_answer import OpenAIAnswer
from phi_jepa.providers.cache import FrozenOutputCache
from phi_jepa.providers.contracts import ProviderFailure


class AnswerPipelineTests(unittest.TestCase):
    def test_same_outcome_blind_selection_and_explicit_ids(self):
        rows = [{'domain': d, 'sample_id': str(i), 'split': s, 'appendix': i < 2}
                for d in ('a', 'b') for i in range(4) for s in ('train', 'test_id')]
        got = runner.select_rows(list(reversed(rows)), ['a', 'b'])
        self.assertEqual([(r['domain'], r['sample_id']) for r in got],
                         [(d, str(i)) for d in ('a', 'b') for i in range(3)])
        self.assertTrue(all(r['split'] == 'test_id' for r in got))
        self.assertEqual(len(runner.select_rows(rows, ['a'], sample_ids=['2'])), 1)
        with self.assertRaises(ValueError): runner.select_rows(rows, ['a'], sample_ids=['9'])
        with self.assertRaises(ValueError): runner.select_rows(rows, ['a'], sample_ids=['2', '2'])
        with self.assertRaises(ValueError): runner.select_rows(rows, ['a'], count=3, cohort='appendix')

    def test_missing_domain_checkpoint_is_not_substituted(self):
        route = runner.route('rnn', 'robotic_arm', 'main')
        self.assertFalse(route['available'])
        self.assertEqual(route['reason'], 'no_checkpoint_for_domain')

    def test_exact_cache_reuse_and_no_historical_writes(self):
        with tempfile.TemporaryDirectory() as d:
            root = Path(d); old = FrozenOutputCache(root/'old')
            identity = {'public': 'same', 'model': 'same'}; old.write(identity, {'text': 'a'})
            before = {p.name: p.read_bytes() for p in (root/'old').iterdir()}
            cache = runner.ReadThroughCache(root/'new', [root/'old'])
            self.assertEqual(cache.read(identity), {'text': 'a'})
            self.assertIsNone(cache.read({**identity, 'public': 'different'}))
            self.assertEqual(before, {p.name: p.read_bytes() for p in (root/'old').iterdir()})

    def test_request_capture_does_not_change_cache_or_readout_policy(self):
        p, forecast = example(); outcomes = read_targets(p, forecast)
        answer = llm_result(p, outcomes); requests = []; captures = []
        def transport(payload, timeout):
            requests.append(payload)
            return {'status': 'completed', 'model': 'fixture', 'usage': {'input_tokens': 2, 'output_tokens': 4},
                    'output': [{'type': 'message', 'content': [{'type': 'output_text', 'text': json.dumps(answer)}]}]}
        config = {'model': 'fixture', 'max_attempts_per_request': 1, 'max_total_attempts': 2,
                  'timeout_seconds': 1, 'max_output_tokens': 100, 'reasoning_effort': 'medium'}
        with tempfile.TemporaryDirectory() as d:
            obj = OpenAIAnswer('fake-secret', config, {'prompt': 'fixture'}, FrozenOutputCache(Path(d)), transport=transport)
            self.assertEqual(obj.answer(p, forecast, outcomes, condition='main_phi', request_sink=captures.append), answer)
            obj.answer(p, forecast, outcomes, condition='main_phi', request_sink=captures.append)
        self.assertEqual(len(requests), 1)
        self.assertEqual(captures[0], captures[1])
        self.assertNotIn('fake-secret', json.dumps(captures))
        payload = json.loads(requests[0]['input'])
        self.assertEqual(payload['physical_forecast'], forecast)
        self.assertEqual(payload['output_readout'], outcomes)
        self.assertNotIn('reference', payload)

    def test_direct_request_contains_only_public_information(self):
        p, _ = example(); outcome = target_result(p.input['answer_spec'][0], 'supported', value=True, source='direct')
        result = llm_result(p, [outcome]); captured = []
        cfg = {'model': 'fixture', 'max_attempts_per_request': 1, 'max_total_attempts': 1,
               'timeout_seconds': 1, 'max_output_tokens': 100, 'reasoning_effort': 'medium'}
        def transport(payload, timeout):
            captured.append(json.loads(payload['input']))
            return {'status': 'completed', 'output': [{'type': 'message', 'content': [{'type': 'output_text', 'text': json.dumps(result)}]}]}
        obj = OpenAIAnswer('mock', cfg, {'prompt': 'fixture'}, None, transport=transport)
        obj.answer(p, None, [], condition='direct_llm', boolean_policy='direct_prediction')
        self.assertIsNone(captured[0]['physical_forecast'])
        self.assertEqual(captured[0]['output_readout'], [])
        self.assertEqual(captured[0]['public_problem']['input'], p.input)

    def test_budget_denies_transport_before_call(self):
        with tempfile.TemporaryDirectory() as d:
            caps = {'provider_usd': 0, 'provider_attempts': 0, 'provider_input_tokens': 0,
                    'provider_output_tokens': 0, 'artifact_bytes': 1000000, 'cpu_seconds': 10, 'gpu_seconds': 10}
            budget = runner.QualificationBudget(Path(d), {'caps': caps, 'export_directory': str(Path(d)/'unused')})
            calls = []
            bounded = budget.transport(lambda *a: calls.append(a))
            with self.assertRaises(RuntimeError): bounded({'model': 'fixture', 'max_output_tokens': 100}, 1)
            self.assertEqual(calls, [])
            self.assertEqual(budget.read()['provider'], [])

    def test_fresh_vanilla_bypasses_every_cache(self):
        p, _ = example(); outcome = target_result(p.input['answer_spec'][0], 'supported', value=True, source='direct')
        answer = llm_result(p, [outcome]); calls = []
        def transport(payload, timeout):
            calls.append(payload)
            return {'status': 'completed', 'model': 'mock-returned-model',
                    'output': [{'type': 'message', 'content': [{'type': 'output_text', 'text': json.dumps(answer)}]}]}
        with tempfile.TemporaryDirectory() as d:
            output = Path(d); dest = output/'case'; dest.mkdir()
            caps = {'provider_usd': 5, 'provider_attempts': 2, 'provider_input_tokens': 10000,
                    'provider_output_tokens': 10000, 'artifact_bytes': 1000000, 'cpu_seconds': 10, 'gpu_seconds': 10}
            runner.save(output/'config.json', {'caps': caps, 'vanilla_answers': 'fresh', 'phi_answers': 'cache',
                                               'export_directory': str(output/'unused')})
            job = {'method': 'vanilla_llm', 'cohort': 'main', 'row': {'sample_id': p.sample_id,
                   'public': {'sample_id': p.sample_id, 'schema_version': p.schema_version, 'input': p.input}}}
            with patch.object(runner, 'guard_deployment_io'), patch('phi_jepa.providers.credentials.load_openai_key', return_value='mock'), \
                 patch.object(runner.QualificationBudget, 'transport', return_value=transport), \
                 patch.object(FrozenOutputCache, 'read', side_effect=AssertionError('fresh must not read cache')):
                runner.answer_worker(job, dest, output)
                runner.answer_worker(job, dest, output)
            result = runner.load(dest/'answer.json')
            self.assertEqual(result['status'], 'success')
            self.assertEqual(result['origin'], 'fresh_provider_generation')
            self.assertIsNone(result['cache'])
            self.assertEqual(len(calls), 2)

    def test_failures_have_no_repaired_prose(self):
        self.assertIn('No valid final answer', runner.prose({'status': 'generation_or_parse_failure', 'reason': 'target_count', 'answer': None}))
        answer = {'targets': [{'entity_id': 'load', 'quantity': 'angle', 'value': -0.2, 'unit': 'rad'}]}
        text = runner.prose({'status': 'success', 'answer': answer})
        self.assertIn('not model-generated prose', text)
        self.assertIn('-0.2', text)
        self.assertNotIn('plain_text_answer', answer)

    def test_gold_export_preserves_types_bindings_and_precision(self):
        p, _ = example()
        public = {'sample_id': p.sample_id, 'schema_version': p.schema_version, 'input': p.input}
        specs = public['input']['answer_spec']
        specs.extend([{**specs[0], 'target_id': 'load:angle', 'quantity': 'angle', 'answer_type': 'number', 'unit': 'rad'},
                      {**specs[0], 'target_id': 'load:position', 'quantity': 'position', 'answer_type': 'vector', 'unit': 'm'}])
        values = [False, -0.48077106495733646, [0.05047588642485897, 0.0, 1.426361248206019]]
        labels = [{'target_id': s['target_id'], 'unit': s['unit'], 'frame': s['frame'], 'value': v} for s, v in zip(specs, values)]
        row = {'sample_id': p.sample_id, 'scenario_id': 's', 'domain': p.input['domain'], 'split': 'test_id', 'public': public}
        exported = runner.gold_record(row, {'structured_label': labels, 'states': ['private trajectory']}, '/ref', 'abc')
        self.assertEqual([t['value'] for t in exported['targets']], values)
        self.assertIs(exported['targets'][0]['value'], False)
        self.assertEqual(exported['targets'][1]['unit'], 'rad')
        self.assertNotIn('states', exported)
        with self.assertRaisesRegex(ValueError, 'gold_target_identity'):
            runner.gold_record(row, {'structured_label': labels + [labels[0]]}, '/ref', 'abc')

    def test_gold_table_keeps_failure_and_unsupported_status(self):
        p, _ = example()
        row = {'sample_id': p.sample_id, 'scenario_id': 's', 'domain': p.input['domain'], 'split': 'test_id',
               'public': {'sample_id': p.sample_id, 'schema_version': p.schema_version, 'input': p.input}}
        spec = p.input['answer_spec'][0]
        gold = runner.gold_record(row, {'structured_label': [{'target_id': spec['target_id'], 'unit': '1', 'frame': 'world', 'value': False}]}, '/ref', 'abc')
        unsupported = target_result(spec, 'unsupported', reason='missing contact | history', source='rule')
        results = {'phi_jepa': {'status': 'success', 'answer': llm_result(p, [unsupported])},
                   'vanilla_llm': {'status': 'answer_failure', 'reason': 'token_cap', 'answer': None}}
        text = '\n'.join(runner.gold_comparison(row, gold, results))
        self.assertIn('| false | unsupported:', text)
        self.assertIn('answer_failure: token_cap', text)
        self.assertIn('contact \\| history', text)
        with self.assertRaisesRegex(ValueError, 'gold_public_identity_mismatch'):
            runner.gold_comparison(row, {**gold, 'public_sha256': 'wrong'}, results)

    def test_evaluation_exports_gold_without_changing_answers_or_calling_models(self):
        p, _ = example(); spec = p.input['answer_spec'][0]
        public = {'sample_id': p.sample_id, 'schema_version': p.schema_version, 'input': p.input}
        row = {'sample_id': p.sample_id, 'scenario_id': 's', 'domain': p.input['domain'], 'split': 'test_id', 'public': public}
        target = target_result(spec, 'supported', value=False, source='direct')
        with tempfile.TemporaryDirectory() as d:
            output = Path(d)/'run'; source = Path(d)/'history'
            runner.save(source/'private'/row['domain']/'test_id-references.json', {p.sample_id: {'structured_label': [
                {'target_id': spec['target_id'], 'unit': spec['unit'], 'frame': spec['frame'], 'value': False}]}})
            runner.save(output/'config.json', {'domains': [row['domain']], 'split': 'test_id', 'methods': ['vanilla_llm'],
                       'vanilla_answers': 'fresh', 'phi_answers': 'cache', 'caps': {'provider_usd': 5}})
            runner.save(output/'selection.json', [row])
            runner.save(output/'budget.json', {'provider': [], 'operations': []})
            answer_path = output/row['domain']/p.sample_id/'vanilla_llm/answer.json'
            runner.save(answer_path, {'status': 'success', 'answer': llm_result(p, [target])})
            before = answer_path.read_bytes()
            with patch.dict(runner.RUNS, {'p11': source}), patch.object(OpenAIAnswer, 'answer', side_effect=AssertionError('no generation')), redirect_stdout(io.StringIO()) as stdout:
                runner.evaluate_run(output)
                runner.report(output)
            self.assertEqual(before, answer_path.read_bytes())
            exported = runner.load(output/'evaluation/private/gold_answers.json')
            self.assertIs(exported[p.sample_id]['targets'][0]['value'], False)
            self.assertIn('Gold answer', (output/'report.md').read_text())
            self.assertIn('| false | false |', stdout.getvalue())
            self.assertTrue(runner.load(output/'evaluation/answers.json')[0]['complete_success'])


if __name__ == '__main__': unittest.main()
