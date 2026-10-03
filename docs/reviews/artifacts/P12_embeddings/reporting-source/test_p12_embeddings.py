"""Offline cache, scope and cap checks; no encoder/model or provider calls."""
import math
import sys
import tempfile
import unittest
import io
import json
from contextlib import redirect_stdout
from dataclasses import asdict
from pathlib import Path
from unittest.mock import patch

sys.path.insert(0, str(Path(__file__).resolve().parents[1]/'tools'))
from p12_embeddings import validate_vector, validate_population, identity, check_budget, verified_notes
from phi_jepa.artifacts import digest
from phi_jepa.providers.cache import FrozenOutputCache
from phi_jepa.integration.readers import file_hash
from test_p04a import example
from p12_enrichment import policy, request_identity


class EmbeddingPreparationTests(unittest.TestCase):
    def test_status_detects_stale_worker_label_and_counts_saved_outputs(self):
        import p12_embedding_status
        from p12_common import save
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            save(root/'config.json', {'reuse_counts': {'train_validation': 224}})
            save(root/'status.json', {'status': 'running'})
            save(root/'attempts/a.json', {'status': 'success', 'scope': 'confirmation', 'domain': 'driving', 'seconds': .2})
            save(root/'attempts/b.json', {'status': 'reserved', 'seconds': 120})
            (root/'worker.lock').touch()
            for locked in (False, True):
                output = io.StringIO()
                with patch('p12_embedding_status.RUN', root), patch('fcntl.flock', side_effect=BlockingIOError if locked else None), redirect_stdout(output):
                    p12_embedding_status.main()
                result = json.loads(output.getvalue())
                self.assertEqual(result['stale_running_label'], not locked)
                self.assertEqual(result['new_vectors_saved'], 1)
                self.assertEqual(result['reserved_or_failed_seconds'], 120)
                self.assertEqual(result['status_check_model_calls'], 0)

    def test_vector_requires_exact_identity_shape_finiteness_and_normalization(self):
        row = {'embedding_request_sha256': 'request', 'context_sha256': 'context', 'token_count': 5}
        value = {'request_sha256': 'request', 'context_sha256': 'context', 'token_count': 5, 'values': [1.] + [0.]*1023}
        validate_vector(value, row)
        for changed in ({'request_sha256': 'other'}, {'context_sha256': 'other'}, {'token_count': 4},
                        {'values': [1.]}, {'values': [float('nan')]*1024}, {'values': [2.]+[0.]*1023}):
            with self.assertRaises(ValueError):validate_vector({**value, **changed}, row)

    def test_request_binds_encoder_text_tokens_and_enriched_mode(self):
        request = identity({'model_revision': 'frozen'}, 'public and notes', [1, 2])
        self.assertEqual(request['serialization'], 'P02a-Q-C-enrichment-v1')
        self.assertEqual(request['context_mode'], 'enriched')
        for changed in (identity({'model_revision': 'new'}, 'public and notes', [1, 2]),
                        identity({'model_revision': 'frozen'}, 'changed', [1, 2]),
                        identity({'model_revision': 'frozen'}, 'public and notes', [1, 3])):
            self.assertNotEqual(digest(request), digest(changed))

    def test_scope_counts_and_scenario_group_isolation(self):
        rows = [{'sample_id': str(i), 'scenario_id': str(i), 'split_group': str(i), 'domain': 'fixture',
                 'scope': 'train_validation' if i < 8038 else 'confirmation',
                 'split': 'train' if i < 8038 else 'test_id'} for i in range(8538)]
        validate_population(rows)
        with self.assertRaises(ValueError):validate_population(rows[:-1])
        rows[-1]['scenario_id'] = rows[0]['scenario_id']
        with self.assertRaisesRegex(ValueError, 'leakage'):validate_population(rows)
        rows[-1]['scenario_id'] = '8537';rows[-1]['sample_id'] = '0'
        with self.assertRaisesRegex(ValueError, 'duplicate'):validate_population(rows)

    def test_time_and_call_reservations_fail_closed(self):
        cfg = {'maximum_model_calls': 8, 'per_call_seconds_cap': 120, 'encoding_seconds_cap': 3600}
        with patch('p12_embeddings.time.time', return_value=100):
            check_budget(cfg, 0, 0, 200)
            with self.assertRaises(TimeoutError):check_budget(cfg, 0, 0, 99)
            with self.assertRaises(ValueError):check_budget(cfg, 8, 0, 200)
            with self.assertRaises(TimeoutError):check_budget(cfg, 1, 3481, 200)

    def test_enrichment_reuse_checks_public_identity_model_and_cache_hash(self):
        problem, _ = example();config, asset = policy();request = request_identity(problem, config, asset)
        with tempfile.TemporaryDirectory() as tmp:
            cache = FrozenOutputCache(Path(tmp));cache.write(request, {'text': '{"notes": ["Public diagnostic note."]}', 'metadata': {'returned_model': config['model']}})
            path = Path(tmp)/(digest(request)+'.json')
            origin = {'cache_file': str(path), 'cache_sha256': file_hash(path), 'request_sha256': digest(request)}
            self.assertEqual(verified_notes(problem, origin, config, asset)['public_input'], problem.input)
            with self.assertRaisesRegex(ValueError, 'binding'):verified_notes(problem, {**origin, 'request_sha256': 'other'}, config, asset)
            with self.assertRaisesRegex(ValueError, 'changed'):verified_notes(problem, {**origin, 'cache_sha256': 'other'}, config, asset)
            cache.write(request, {'text': '{"notes": []}', 'metadata': {'returned_model': 'unapproved'}})
            with self.assertRaisesRegex(ValueError, 'model binding'):verified_notes(problem, {**origin, 'cache_sha256': file_hash(path)}, config, asset)


if __name__ == '__main__':
    unittest.main()
