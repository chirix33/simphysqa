"""Offline full-release selection and run-local context preparation tests."""
import json
from pathlib import Path
import sys
import tempfile
import unittest
from unittest.mock import patch, Mock
from dataclasses import asdict
sys.path.insert(0, str(Path(__file__).resolve().parents[1]/'tools'))
import answer_pipeline as runner
import answer_inventory as inventory
import answer_context as context
from test_p04a import example
from phi_jepa.providers.contracts import EncoderSettings


class ExpandedInventoryTests(unittest.TestCase):
    def test_release_selection_never_opens_reference_and_preserves_partition(self):
        p, _ = example()
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory); calls = []
            public = [{'sample_id': sid, 'schema_version': p.schema_version, 'input': p.input} for sid in ('a', 'z')]
            (root/'inputs.jsonl').write_text('\n'.join(json.dumps(r) for r in public))
            metadata = [{'sample_id': r['sample_id'], 'metadata': {'split': 'test_id', 'record_origin': 'simulation',
                        'validation': {'status': 'accepted'}, 'base_scenario_id': r['sample_id'], 'split_group_id': r['sample_id']}} for r in public]
            (root/'evaluator.jsonl').write_text('\n'.join(json.dumps(r) for r in metadata))
            prepared = [{'sample_id': 'z', 'scenario_id': 'z', 'split': 'test_id', 'domain': p.input['domain'], 'appendix': False, 'public': public[1]}]
            runner.save(root/'selected-public.json', prepared)
            cat = Mock(identity='release')
            def verified(domain, split, name):
                self.assertEqual(split, 'test_id'); self.assertNotEqual(name, 'references.jsonl')
                calls.append(name); return root/name
            cat.verified_file.side_effect = verified
            with patch.dict(inventory.RUNS, {'p11': root}), patch.object(inventory, 'catalog', return_value=cat):
                rows = inventory.inventory([p.input['domain']], 'test_id', expand=True)
            chosen = runner.select_rows(rows, [p.input['domain']], count=2)
            self.assertEqual([r['sample_id'] for r in chosen], ['z', 'a'])
            self.assertTrue(all(r['split'] == 'test_id' for r in chosen))
            self.assertEqual(set(calls), {'inputs.jsonl', 'evaluator.jsonl'})
            with self.assertRaisesRegex(ValueError, 'available 2'):
                runner.select_rows(rows, [p.input['domain']], count=3)

    def test_missing_enrichment_stays_failure_without_zero_budget_call(self):
        p, _ = example()
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory); old = root/'old'; output = root/'out'
            row = {'sample_id': p.sample_id, 'domain': p.input['domain'], 'public': {'sample_id': p.sample_id, 'schema_version': p.schema_version, 'input': p.input}}
            caps = dict(provider_usd=0, provider_attempts=0, provider_input_tokens=0, provider_output_tokens=0, artifact_bytes=1000000, cpu_seconds=100, gpu_seconds=100)
            runner.save(output/'config.json', {'methods': ['phi_jepa'], 'caps': caps, 'export_directory': str(root/'unused')})
            runner.save(output/'selection.json', [row])
            with patch.dict(context.RUNS, {'p11': old, 'p10': old}), patch.object(context, 'guard_deployment_io'), \
                 patch('phi_jepa.providers.openai_enrichment.OpenAIEnrichment._http', side_effect=AssertionError('no paid call')):
                context.enrich(output)
            self.assertFalse((output/'context/enrichment'/f'{p.sample_id}.json').exists())
            self.assertIn('requires_positive_api_budget', runner.load(output/'context/failures'/f'{p.sample_id}.json')['reason'])

    def test_missing_embedding_is_created_by_frozen_backend_without_reference(self):
        p, _ = example()
        expected = runner.load(runner.ROOT/'configs/model_context_p02b.json')['encoder']
        settings = EncoderSettings(provider='local_transformers', implementation_revision='fixture-runtime', mode='local',
                                   **{k: expected[k] for k in context.ENCODER_KEYS})
        backend = Mock(settings=settings)
        backend.tokenize.return_value = (1, 2, 3)
        backend.encode_tokens.return_value = (0.1,)*1024
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory); old = root/'old'; output = root/'out'
            runner.save(old/'encoding-report.json', {'settings': asdict(settings)})
            runner.save(output/'config.json', {'methods': ['phi_jepa']})
            runner.save(output/'selection.json', [{'sample_id': p.sample_id, 'domain': p.input['domain'],
                        'public': {'sample_id': p.sample_id, 'schema_version': p.schema_version, 'input': p.input}}])
            runner.save(output/'context/enrichment'/f'{p.sample_id}.json', {'public_input': p.input, 'notes': ['Public fixture description.']})
            with patch.dict(context.RUNS, {'p11': old, 'p10': old}), patch.object(context, 'guard_deployment_io'), \
                 patch('phi_jepa.providers.qwen.QwenEncoder', return_value=backend):
                context.encode(output)
            result = runner.load(output/'context/embeddings/enriched'/f'{p.sample_id}.json')
            self.assertEqual(len(result['values']), 1024)
            backend.encode_tokens.assert_called_once()
            serialized = backend.tokenize.call_args.args[0]
            self.assertIn('Public fixture description.', serialized)
            self.assertNotIn('structured_label', serialized)

    def test_direct_only_and_numerical_only_need_no_context_preparation(self):
        row = {'domain': 'robotic_arm'}
        self.assertEqual(context.modes({'methods': ['vanilla_llm', 'no_text_conditioning']}, row), [])
        self.assertEqual(context.modes({'methods': ['rnn']}, row), [])


if __name__ == '__main__': unittest.main()
