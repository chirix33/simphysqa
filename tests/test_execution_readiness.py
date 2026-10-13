"""Offline only: synthetic fixture namespaces, no answering weights or main ledger."""
from copy import deepcopy
import json
from pathlib import Path
import sqlite3
import tempfile
import unittest
from unittest.mock import patch

from simphysqa.execution_readiness import (VERSION, Ledger, canonical, read, put, sha, digest, stage_key,
    within, assert_public, resolved_condition, prepare_job, export_return, import_return, canonical_records, conflicts)
from simphysqa.execution_support import MemoryMonitor, termination, Instrumentation


class Readiness(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory(); self.root = Path(self.temp.name); self.package = self.root / 'fixture-package'
        self.package.mkdir(); self.cid = 'fixture-condition'; self.key = stage_key('FIXTURE-NOT-MAIN', self.cid, 'enriched', 1)
        self.second = stage_key('FIXTURE-NOT-MAIN', self.cid, 'enriched', 2)
        self.other = stage_key('FIXTURE-OTHER', self.cid, 'enriched', 1)
        self.snapshot = self.root / 'FIXTURE-REV'; self.snapshot.mkdir()
        (self.snapshot / 'fixture.bin').write_bytes(b'not model weights')
        self.c = {'condition_id': self.cid, 'artifact_revision': 'FIXTURE-REV', 'template_sha256': 'fixture-template',
                  'backend': 'fixture', 'runtime_versions': {'fixture': '1'}, 'weight_files': {'fixture.bin': {'sha256': sha(self.snapshot / 'fixture.bin')}},
                  'settings': {'precision': 'fixture', 'quantization': 'none', 'max_seconds': 10}}
        put(self.package / 'condition.json', self.c)
        (self.package / 'workers').mkdir(); (self.package / 'workers/fixture.py').write_text('# NO INFERENCE\n')
        (self.package / 'workers/execution_support.py').write_text('# fixture support\n')
        self.q = {'sample_id': 'FIXTURE-NOT-MAIN', 'condition_id': self.cid, 'stage': 1, 'input_condition': 'enriched', 'tools': [],
                  'messages': [{'role': 'user', 'content': 'fixture public question'}]}
        put(self.package / 'request.json', self.q)
        self.q_other = {**self.q, 'sample_id': 'FIXTURE-OTHER'}; put(self.package / 'other.json', self.q_other)
        self.spec = {'conditions': {self.cid: {'path': 'condition.json', 'sha256': digest(self.c), 'worker': 'workers/fixture.py',
                                               'worker_sha256': sha(self.package / 'workers/fixture.py')}},
                     'shards': [{'shard_id': 'fixture-shard', 'keys': [self.key, self.second, self.other], 'owner': None}],
                     'requests': {self.key: {'path': 'request.json', 'sha256': sha(self.package / 'request.json')},
                                  self.other: {'path': 'other.json', 'sha256': sha(self.package / 'other.json')}}}
        put(self.package / 'execution-spec.json', self.spec); put(self.package / 'package-manifest.json', {'fixture': True})
        self.ledger = Ledger.create(self.root / 'FIXTURE.sqlite', self.package, fixture=True, ceiling=1240)
        self.assignment = self.ledger.issue('FIXTURE-EXECUTOR', ['fixture-shard'])
        self.bindings = {'interpreter': 'fixture-python', 'environment': {}, 'artifact_cache': str(self.root), 'snapshot_path': str(self.snapshot),
                         'device_uuid': 'FIXTURE-GPU', 'cuda_visible_devices': 'FIXTURE-GPU', 'nvidia_smi': 'fixture-smi'}
        resolved = resolved_condition(self.package, self.cid, self.bindings)
        evidence = {'status': 'passed', 'evidence_sha256': 'fixture-not-empirical'}
        self.qual = {'status': 'task_qualified', 'executor_id': 'FIXTURE-EXECUTOR', 'condition_id': self.cid, 'representation': 'enriched',
                     'package_sha256': self.ledger.meta('package_hash'), 'worker_sha256': sha(self.package / 'workers/fixture.py'),
                     'support_sha256': sha(self.package / 'workers/execution_support.py'), 'scientific_condition_sha256': digest(self.c),
                     'bindings_sha256': digest(self.bindings), 'resolved_condition_sha256': digest(resolved),
                     'hardware_runtime': {'gpu_name': 'FIXTURE GPU', 'device_uuid': 'FIXTURE-GPU', 'vram_mib': 1,
                                          'os': 'FIXTURE OS', 'wsl': 'not_wsl', 'driver': 'fixture', 'cuda_runtime': 'fixture', 'backend_versions': {'fixture': '1'}},
                     'model_files': {'fixture.bin': sha(self.snapshot / 'fixture.bin')}, 'tokenizer_files': {'template_sha256': 'fixture-template'},
                     'quantization': 'none', 'precision': 'fixture', 'render_verification': evidence, 'stop_verification': evidence, 'task_rehearsal': evidence}
        self.qhash = self.ledger.approve_qualification(self.qual)

    def tearDown(self):
        self.ledger.db.close(); self.temp.cleanup()

    def reserve(self, key=None):
        key = key or self.key
        return self.ledger.reserve(self.assignment['id'], 'FIXTURE-EXECUTOR', [key],
                                   {key: self.spec['requests'][key]['sha256']}, self.qhash)

    def job(self, status='completed', raw='{"abstained":true}'):
        job = self.root / ('fixture-job-' + str(len(list(self.root.glob('fixture-job-*')))))
        ticket = prepare_job(self.ledger, self.assignment['id'], 'FIXTURE-EXECUTOR', self.qhash, [self.key], self.bindings, job)
        context = read(job / 'execution-context.json')
        base = job / 'worker-output'; stem = 'FIXTURE-NOT-MAIN-stage1.json'
        put(base / 'executed-requests' / stem, self.q); put(base / 'tokenized-prompts' / stem, {'prompt': 'fixture rendered', 'token_ids': [1, 2]})
        result = {'sample_id': self.q['sample_id'], 'condition_id': self.cid, 'stage': 1, 'representation': 'enriched', 'stage_key': self.key,
                  'request_sha256': digest(self.q), 'completion_status': status, 'raw_output': raw, 'output_token_ids': [3],
                  'response_origin': 'MOCK_BACKEND_FIXTURE', 'execution_version': VERSION, 'cpu_fallback': False,
                  'execution_scope': 'main', 'qualification_status': 'task_qualified',
                  'termination': termination(status), 'device_memory': {'status': 'unavailable', 'sampled_peak_mib': None},
                  'total_stage_seconds': 2, 'latency_seconds': 1}
        result['stage_reservation'] = context['stage_reservations'][self.key]
        for name in ('qualification_sha256', 'assignment_sha256', 'hardware_runtime_sha256', 'worker_sha256', 'scientific_condition_sha256', 'process_reservation'):
            result[name] = context[name]
        put(base / 'results' / stem, result)
        put(base / 'runtime.json', {**{k: context[k] for k in ('qualification_sha256', 'worker_sha256', 'process_reservation')},
                                   'gpu_name': 'FIXTURE GPU', 'runtime_versions': {'fixture': '1'}, 'device_uuid': 'FIXTURE-GPU',
                                   'hardware_runtime_observed': {'driver': 'fixture', 'os': 'FIXTURE OS', 'vram_mib': 1}})
        put(job / 'process-receipt.json', {'elapsed_seconds': 5, 'state': 'complete', 'process_reservation': ticket['id']})
        return job

    def return_from(self, job, name='fixture-return'):
        output = self.root / name; export_return(job, output); return output

    def test_exact_bytes_and_relative_paths(self):
        job = self.job(); result = self.return_from(job)
        self.assertEqual((result / 'worker-output/executed-requests/FIXTURE-NOT-MAIN-stage1.json').read_bytes(), canonical(self.q))
        self.assertEqual(within(self.package, 'request.json'), self.package / 'request.json')
        for unsafe in ('../escape', str(self.root / 'absolute'), '.'):
            with self.assertRaises(ValueError): within(self.package, unsafe)

    def test_public_comparison_preserved_private_rejected(self):
        public = {'messages': [{'role': 'user', 'content': 'Task\n' + json.dumps({'input': {'supplied_comparison': {'value': False}}})}]}
        assert_public(public)
        private = {'messages': [{'role': 'user', 'content': 'Task\n' + json.dumps({'private': {'gold': 1}})}]}
        with self.assertRaises(ValueError): assert_public(private)

    def test_explicit_filter_and_overlapping_assignment(self):
        with self.assertRaises(ValueError): self.ledger.issue('', ['fixture-shard'])
        with self.assertRaises(sqlite3.IntegrityError): self.ledger.issue('OTHER', ['fixture-shard'])
        with self.assertRaises(ValueError): self.ledger.pending(self.assignment['id'], 'OTHER')
        self.assertEqual(self.ledger.pending(self.assignment['id'], 'FIXTURE-EXECUTOR'), [self.key, self.other])

    def test_cross_root_overlap_and_orphan_resume(self):
        self.reserve(); second_ledger = Ledger(self.root / 'FIXTURE.sqlite')
        try:
            with self.assertRaises(sqlite3.IntegrityError):
                second_ledger.reserve(self.assignment['id'], 'FIXTURE-EXECUTOR', [self.key], {self.key: digest(self.q)}, self.qhash)
        finally: second_ledger.db.close()
        self.assertEqual(self.ledger.used(), 610)
        self.assertEqual(self.ledger.pending(self.assignment['id'], 'FIXTURE-EXECUTOR'), [self.other])

    def test_budget_unknown_charges_loading_once(self):
        first = self.reserve(); self.assertEqual(first['bound_seconds'], 610)
        self.reserve(self.other); self.assertEqual(self.ledger.used(), 1220)
        self.ledger.settle(first['id'], 1, 'unknown'); self.assertEqual(self.ledger.used(), 1220)
        with self.assertRaises(ValueError): self.ledger.settle(first['id'], 1, 'complete')

    def test_ceiling_enforced_atomically(self):
        self.ledger.db.execute("UPDATE meta SET v='609' WHERE k='ceiling'")
        with self.assertRaisesRegex(ValueError, 'ceiling'): self.reserve()
        self.assertEqual(self.ledger.db.execute('SELECT COUNT(*) FROM stages').fetchone()[0], 0)

    def test_unqualified_runtime_and_scientific_override_rejected(self):
        with self.assertRaisesRegex(ValueError, 'unqualified'):
            self.ledger.reserve(self.assignment['id'], 'FIXTURE-EXECUTOR', [self.key], {self.key: digest(self.q)}, 'no-receipt')
        bad = {**self.bindings, 'temperature': .1}
        with self.assertRaisesRegex(ValueError, 'scientific'): resolved_condition(self.package, self.cid, bad)
        badqual = deepcopy(self.qual); badqual['precision'] = 'different'
        with self.assertRaises(ValueError): self.ledger.approve_qualification(badqual)

    def test_duplicate_transport_counted_once(self):
        source = self.return_from(self.job()); first = import_return(self.ledger, source, self.root / 'imports')
        second = import_return(self.ledger, source, self.root / 'imports')
        self.assertEqual(first['validation_failures'], []); self.assertTrue(second['identical_duplicate_transport'])
        self.assertEqual(len(canonical_records(self.ledger)), 1); self.assertEqual(self.ledger.used(), 5)
        self.assertEqual(len(list((self.root / 'imports').glob('*-*'))), 4)  # two roots and two receipts

    def test_conflict_preserved_no_success_preference(self):
        job = self.job(status='failed', raw='partial'); first = self.return_from(job)
        import_return(self.ledger, first, self.root / 'imports')
        resultpath = job / 'worker-output/results/FIXTURE-NOT-MAIN-stage1.json'
        result = read(resultpath); result.update(completion_status='completed', raw_output='{"targets":[]}')
        resultpath.write_bytes(canonical(result))  # mutable MOCK fixture; imported source is never changed
        second = self.return_from(job, 'fixture-return-different'); receipt = import_return(self.ledger, second, self.root / 'imports')
        self.assertEqual(receipt['conflicts'], [self.key]); self.assertEqual(canonical_records(self.ledger), {})
        self.assertEqual(len(list((self.root / 'imports').glob('*/worker-output/results/*.json'))), 2)

    def test_hash_corruption_and_cpu_fallback_preserved(self):
        source = self.return_from(self.job()); (source / 'requests.json').write_bytes(b'CORRUPTED FIXTURE')
        receipt = import_return(self.ledger, source, self.root / 'imports')
        self.assertIn('hash', receipt['validation_failures'][0]['reason']); self.assertEqual(canonical_records(self.ledger), {})
        self.assertEqual(self.ledger.used(), 610)  # invalid receipt does not release unknown work

    def test_actual_history_only_conditional_reservation(self):
        with self.assertRaisesRegex(ValueError, 'actual supported'):
            self.ledger.reserve(self.assignment['id'], 'FIXTURE-EXECUTOR', [self.second], {self.second: 'fake'}, self.qhash)
        source = self.return_from(self.job(raw='VERBATIM first actual fixture response')); import_return(self.ledger, source, self.root / 'imports')
        initial = canonical_records(self.ledger)[self.key]
        q2 = deepcopy(self.q); q2['stage'] = 2; q2['messages'] += [{'role': 'assistant', 'content': initial['raw_output']}, {'role': 'user', 'content': 'Recorded clarification reply: fixture query information'}]
        route = {'status': 'supported', 'initial_key': self.key, 'initial_result_sha256': digest(initial), 'actual_raw': initial['raw_output'], 'request': q2, 'request_sha256': digest(q2)}
        self.ledger.db.execute('INSERT INTO routes VALUES(?,?)', (self.second, canonical(route).decode()))
        self.assertIn(self.second, self.ledger.pending(self.assignment['id'], 'FIXTURE-EXECUTOR'))
        with self.assertRaisesRegex(ValueError, 'exact request'):
            self.ledger.reserve(self.assignment['id'], 'FIXTURE-EXECUTOR', [self.second], {self.second: 'authored-substitute'}, self.qhash)
        self.ledger.reserve(self.assignment['id'], 'FIXTURE-EXECUTOR', [self.second], {self.second: digest(q2)}, self.qhash)

    def test_unexecuted_conditional_never_infers(self):
        route = {'status': 'unexecuted_conditional', 'reason': 'wrong requested slot', 'actual_raw': 'fixture wrong slot'}
        self.ledger.db.execute('INSERT INTO routes VALUES(?,?)', (self.second, canonical(route).decode()))
        self.assertNotIn(self.second, self.ledger.pending(self.assignment['id'], 'FIXTURE-EXECUTOR'))
        self.assertEqual(self.ledger.used(), 0)

    def test_missing_memory_is_null_and_termination_has_source(self):
        def failure(): raise RuntimeError('fixture unavailable')
        monitor = MemoryMonitor('NOT EXECUTED', 'FIXTURE', reader=failure); monitor.sample()
        report = monitor.report(); self.assertIsNone(report['sampled_peak_mib']); self.assertEqual(report['successful_sample_count'], 0)
        self.assertEqual(report['status'], 'unavailable'); self.assertTrue(report['errors'])
        self.assertEqual(termination('completed', evidence={'eos': 1})['reason_source'], 'derived')
        self.assertIsNone(termination('timeout')['raw_backend_reason'])
        monitor = MemoryMonitor('NOT EXECUTED', 'FIXTURE', reader=lambda: {'device_uuid': 'FIXTURE', 'used_mib': 5}); monitor.sample()
        self.assertEqual(monitor.report()['sampled_peak_mib'], 5)

    def test_common_timing_enrichment_does_not_change_raw(self):
        instrument = Instrumentation.__new__(Instrumentation); instrument.context = {'representation': 'enriched',
            'qualification_status': 'task_qualified',
            'stage_reservations': {self.key: 'FIXTURE reservation'}, 'qualification_sha256': 'q', 'assignment_sha256': 'a',
            'hardware_runtime_sha256': 'h', 'worker_sha256': 'w', 'scientific_condition_sha256': 'c', 'process_reservation': 'p'}
        instrument.monitor = MemoryMonitor('NOT EXECUTED', 'FIXTURE', reader=lambda: {'used_mib': 0})
        instrument.begin_stage()
        original = {'sample_id': 'FIXTURE-NOT-MAIN', 'condition_id': self.cid, 'stage': 1, 'completion_status': 'failed', 'raw_output': 'partial exact', 'latency_seconds': 1}
        enriched = instrument.enrich(Path('results/fixture.json'), original)
        self.assertEqual(enriched['raw_output'], original['raw_output']); self.assertEqual(enriched['latency_seconds'], 1)
        self.assertGreaterEqual(enriched['total_stage_seconds'], 0); self.assertEqual(enriched['termination']['category'], 'failed')
        self.assertNotIn('total_stage_seconds', original)

    def test_missing_result_preserved_unknown_never_retried(self):
        job = self.job(); (job / 'worker-output/results/FIXTURE-NOT-MAIN-stage1.json').unlink()  # temp only
        receipt = import_return(self.ledger, self.return_from(job), self.root / 'imports')
        self.assertTrue(receipt['validation_failures']); self.assertEqual(canonical_records(self.ledger), {})
        self.assertNotIn(self.key, self.ledger.pending(self.assignment['id'], 'FIXTURE-EXECUTOR'))

    def test_analysis_endpoint_failure_compatibility(self):
        from simphysqa.main_analysis import assess, paired_intervals
        source = self.return_from(self.job(status='length_limited', raw='{"targets":[]}'))
        import_return(self.ledger, source, self.root / 'imports'); raw = canonical_records(self.ledger)[self.key]
        result = assess({'question_type': 'direct'}, {'condition_id': self.cid}, raw, None)
        self.assertEqual(result['endpoints']['typed_correct'], 0); self.assertFalse(result['answer_valid'])
        rows = [{'sample_id': 'FIXTURE-' + d, 'group_id': d, 'domain': d, 'family': 'direct', 'condition_id': c,
                 'input_condition': 'enriched', 'endpoints': {'typed_correct': 0}} for d in ('a', 'b', 'c', 'd') for c in ('A', 'B')]
        self.assertEqual(paired_intervals(rows, 10)['summaries'][0]['independent_qa_items'], 4)

    def test_cpu_fallback_even_hash_valid_is_rejected(self):
        job = self.job(); path = job / 'worker-output/results/FIXTURE-NOT-MAIN-stage1.json'
        result = read(path); result['cpu_fallback'] = True; path.write_bytes(canonical(result))
        receipt = import_return(self.ledger, self.return_from(job), self.root / 'imports')
        self.assertIn('fallback', receipt['validation_failures'][0]['reason']); self.assertEqual(canonical_records(self.ledger), {})

    def test_main_continuation_assembler_retains_actual_turn_verbatim(self):
        from simphysqa.main_public import continuation, project
        initial = {'sample_id': 'FIXTURE', 'question_type': 'clarification', 'schema_version': 's', 'export_version': 'v', 'input': {'query': {}, 'states': []}}
        resolved = deepcopy(initial); resolved['input']['query']['timestamp'] = 1.0
        original = {'messages': [{'role': 'user', 'content': 'Task\n' + canonical(initial).decode()}], 'tools': [], 'sample_id': 'FIXTURE'}
        record = {'private': {'initial_view': initial}}
        actual = '<think>RAW NOT AUTHORED</think>\n{"response_kind":"clarify"}'
        with patch('simphysqa.clarification_evaluation.route_reply', return_value={'status': 'recorded_reply_routed', 'reply': {'timestamp': 1.0}, 'resolved_view': resolved}), patch('simphysqa.spq06.public_request', return_value=original):
            request, _ = continuation(record, {}, actual, {})
        self.assertEqual(request['messages'][-2], {'role': 'assistant', 'content': actual})
        self.assertEqual(len(request['messages']), 3)
        self.assertTrue(request['messages'][-1]['content'].startswith('Recorded clarification reply: '))
        from simphysqa.public_updates import apply
        text = request['messages'][-1]['content']; changes = json.loads(text.split('answer.\n', 1)[1])['public_task_updates']
        self.assertEqual(apply(project(initial), changes), project(resolved))

    def test_transformed_generation_calls_unchanged_and_workers_public_only(self):
        import ast
        import simphysqa
        root = Path(simphysqa.__file__).parent / 'execution_workers'
        transformations = read(root / 'transformations.json')
        for receipt in transformations['workers']:
            text = (root / (receipt['condition_id'] + '.py')).read_text(encoding='utf-8')
            original = text
            # Reverse every asserted replacement; insertion-only instrumentation does
            # not alter any generate/SamplingParams/LLM/model-load call arguments.
            for change in reversed(receipt['changes']):
                if 'before' in change and change['after']: original = original.replace(change['after'], change['before'])
            def calls(source):
                return [ast.dump(n, include_attributes=False) for n in ast.walk(ast.parse(source)) if isinstance(n, ast.Call) and
                        ((isinstance(n.func, ast.Attribute) and n.func.attr in ('generate', 'from_pretrained')) or
                         (isinstance(n.func, ast.Name) and n.func.id in ('SamplingParams', 'LLM')))]
            self.assertEqual(calls(text), calls(original))
            tree = ast.parse(text)
            imported = [n.module for n in ast.walk(tree) if isinstance(n, ast.ImportFrom)]
            self.assertFalse(any(m and ('simphysqa' in m or 'scoring' in m) for m in imported))

    def test_canonical_source_tampering_is_detected(self):
        receipt = import_return(self.ledger, self.return_from(self.job()), self.root / 'imports')
        imported = Path(receipt['source_root']); (imported / 'requests.json').write_bytes(b'CORRUPTED FIXTURE')
        with self.assertRaisesRegex(ValueError, 'immutable'): canonical_records(self.ledger)

    def test_instrumented_transformers_worker_with_mock_backend(self):
        import contextlib, runpy, sys, time, types
        import simphysqa
        from simphysqa.execution_support import Instrumentation as RealInstrumentation
        worker = Path(simphysqa.__file__).parent / 'execution_workers/qwen3_8b_direct.py'
        class FakeTokens:
            shape = (1, 2)
            def __getitem__(self, index): return self
            def tolist(self): return [1, 2]
            def to(self, device): return self
        class FakeGenerated:
            def __getitem__(self, index): return types.SimpleNamespace(tolist=lambda: [3, 99])
        class Tokenizer:
            chat_template = 'FIXTURE TEMPLATE'; pad_token_id = 99; eos_token_id = 99
            def apply_chat_template(self, messages, **kwargs): return 'FIXTURE rendered exact'
            def __call__(self, text, **kwargs): return {'input_ids': FakeTokens()}
            def decode(self, output, **kwargs): return '{"abstained":true}'
        class Model:
            generation_config = types.SimpleNamespace(eos_token_id=99)
            def to(self, device): return self
            def eval(self): return self
            def generate(self, **kwargs):
                self.kwargs = kwargs
                return FakeGenerated()
        model = Model(); tokenizer = Tokenizer()
        cuda = types.SimpleNamespace(is_available=lambda: True, get_device_name=lambda index: 'FIXTURE GPU', get_device_capability=lambda index: (0, 0),
            reset_peak_memory_stats=lambda: None, manual_seed_all=lambda seed: None, max_memory_allocated=lambda: 1,
            max_memory_reserved=lambda: 2, synchronize=lambda: None)
        torch = types.SimpleNamespace(cuda=cuda, bfloat16='fixture', version=types.SimpleNamespace(cuda='fixture'),
                                      manual_seed=lambda seed: None, inference_mode=contextlib.nullcontext)
        transformers = types.SimpleNamespace(AutoTokenizer=types.SimpleNamespace(from_pretrained=lambda *a, **k: tokenizer),
            AutoModelForCausalLM=types.SimpleNamespace(from_pretrained=lambda *a, **k: model), StoppingCriteria=object, StoppingCriteriaList=list)
        context = {'representation': 'enriched', 'stage_reservations': {self.key: 'FIXTURE reservation'}, 'qualification_sha256': 'q', 'assignment_sha256': 'a',
            'qualification_status': 'task_qualified',
            'hardware_runtime_sha256': 'h', 'worker_sha256': 'w', 'scientific_condition_sha256': 'c', 'process_reservation': 'p',
            'gpu_name': 'FIXTURE GPU', 'device_uuid': 'FIXTURE-GPU', 'hardware_runtime': {'cuda_runtime': 'fixture'}}
        class MockInstrumentation(RealInstrumentation):
            def __init__(self, *args):
                self.context = context; self.process_start = time.monotonic(); self.stage_start = None
                self.observed_hardware = {'fixture': True}
                self.monitor = MemoryMonitor('NOT EXECUTED', 'FIXTURE', reader=lambda: {'used_mib': 1})
            def enrich(self, path, value):
                result = super().enrich(path, value)
                if path.parent.name == 'results': result['response_origin'] = 'MOCK_BACKEND_FIXTURE'
                return result
        from simphysqa.execution_support import termination as classify
        support = types.SimpleNamespace(Instrumentation=MockInstrumentation, termination=classify)
        condition = {**self.c, 'backend': 'transformers', 'snapshot_path': str(self.snapshot), 'model_id': 'FIXTURE MODEL',
                     'template_sha256': digest('FIXTURE TEMPLATE'), 'settings': {'seed': 11, 'max_new_tokens': 10, 'max_input_and_output': 32,
                        'max_seconds': 1, 'enable_thinking': False, 'temperature': .7, 'top_p': .8, 'top_k': 20}}
        put(self.root / 'mock-condition.json', condition); put(self.root / 'mock-requests.json', [self.q])
        args = [str(worker), '--condition', str(self.root / 'mock-condition.json'), '--requests', str(self.root / 'mock-requests.json'),
                '--output', str(self.root / 'MOCK-WORKER-OUTPUT'), '--execution-context', 'MOCK-NOT-MAIN']
        with patch.dict(sys.modules, {'torch': torch, 'transformers': transformers, 'execution_support': support}), patch('sys.argv', args), patch('importlib.metadata.version', return_value='1'):
            runpy.run_path(str(worker), run_name='__main__')
        result = read(self.root / 'MOCK-WORKER-OUTPUT/results/FIXTURE-NOT-MAIN-stage1.json')
        self.assertEqual(result['completion_status'], 'completed'); self.assertEqual(result['raw_output'], '{"abstained":true}')
        self.assertEqual(result['termination']['reason_source'], 'derived'); self.assertEqual(result['termination']['derivation']['last_token'], 99)
        self.assertEqual(result['response_origin'], 'MOCK_BACKEND_FIXTURE'); self.assertIn('total_stage_seconds', result)
        self.assertEqual(model.kwargs['temperature'], .7); self.assertEqual(model.kwargs['top_p'], .8)

    def test_conflicting_process_accounting_keeps_full_reserve(self):
        job = self.job(); source = self.return_from(job); import_return(self.ledger, source, self.root / 'imports')
        receipt = read(job / 'process-receipt.json'); receipt['elapsed_seconds'] = 6
        (job / 'process-receipt.json').write_bytes(canonical(receipt))
        other = self.return_from(job, 'fixture-accounting-conflict'); result = import_return(self.ledger, other, self.root / 'imports')
        self.assertEqual(self.ledger.used(), 610); self.assertIn(self.key, result['conflicts'])
        self.assertTrue(any('lifecycle' in reason['reason'] for reason in result['validation_failures']))

    def test_entry_hash_does_not_conflict_unrelated_item(self):
        from simphysqa.execution_readiness import entry_identity
        entry = {'key': self.key, 'request': 'worker-output/executed-requests/A-stage1.json',
                 'result': 'worker-output/results/A-stage1.json', 'prompt': 'worker-output/tokenized-prompts/A-stage1.json'}
        original = {'qualification.json': 'same', 'worker-output/results/A-stage1.json': 'same', 'worker-output/results/B-stage1.json': 'old'}
        changed_other = {**original, 'worker-output/results/B-stage1.json': 'new'}
        self.assertEqual(entry_identity(entry, original), entry_identity(entry, changed_other))
        self.assertNotEqual(entry_identity(entry, original), entry_identity(entry, {**original, 'worker-output/results/A-stage1.json': 'new'}))

    def test_analysis_bridge_preserves_parsed_objects_and_versions(self):
        from simphysqa.execution_readiness import analysis_bridge
        source = self.return_from(self.job()); import_return(self.ledger, source, self.root / 'imports')
        preparation = self.root / 'FIXTURE-PRIVATE-PREP'; put(preparation / 'nested-200-manifest.json', {'fixture': True})
        spec = json.loads(self.ledger.meta('spec')); spec['selected_manifest_sha256'] = sha(preparation / 'nested-200-manifest.json')
        self.ledger.db.execute("UPDATE meta SET v=? WHERE k='spec'", (canonical(spec).decode(),))
        plan = self.root / 'FIXTURE-plan.json'; put(plan, {'preparation': str(preparation), 'fixture': True})
        with patch('simphysqa.main_analysis.analyse', return_value={'MOCK': True}) as analyse:
            analysis_bridge(self.ledger, plan, self.root / 'FIXTURE-analysis')
        self.assertEqual(analyse.call_count, 1)
        saved = read(self.root / 'FIXTURE-analysis/central-parsed-records.json')
        self.assertEqual(saved['stages'][0]['parsed_response'], {'abstained': True})
        self.assertIn('scoring', saved['versions_sha256']); self.assertIn('main_analysis', saved['versions_sha256'])

    def test_returned_continuation_requires_coordinator_history(self):
        firstjob = self.job(raw='EXACT MOCK FIRST TURN'); import_return(self.ledger, self.return_from(firstjob), self.root / 'imports')
        initial = canonical_records(self.ledger)[self.key]
        q2 = deepcopy(self.q); q2['stage'] = 2; q2['messages'] += [{'role': 'assistant', 'content': initial['raw_output']}, {'role': 'user', 'content': 'Recorded query-only reply'}]
        route = {'status': 'supported', 'initial_key': self.key, 'initial_result_sha256': digest(initial), 'actual_raw': initial['raw_output'], 'request': q2, 'request_sha256': digest(q2)}
        self.ledger.db.execute('INSERT INTO routes VALUES(?,?)', (self.second, canonical(route).decode()))
        secondjob = self.root / 'MOCK-CONTINUATION'
        ticket = prepare_job(self.ledger, self.assignment['id'], 'FIXTURE-EXECUTOR', self.qhash, [self.second], self.bindings, secondjob)
        context = read(secondjob / 'execution-context.json'); base = secondjob / 'worker-output'; stem = 'FIXTURE-NOT-MAIN-stage2.json'
        put(base / 'executed-requests' / stem, q2); put(base / 'tokenized-prompts' / stem, {'prompt': 'EXACT MOCK HISTORY RENDER', 'token_ids': [1, 2, 3]})
        raw = {**initial, 'stage': 2, 'stage_key': self.second, 'request_sha256': digest(q2), 'raw_output': 'MOCK RESOLVED RESPONSE'}
        for name in ('qualification_sha256', 'assignment_sha256', 'hardware_runtime_sha256', 'worker_sha256', 'scientific_condition_sha256', 'process_reservation'):
            raw[name] = context[name]
        raw['stage_reservation'] = context['stage_reservations'][self.second]
        put(base / 'results' / stem, raw)
        runtime = read(firstjob / 'worker-output/runtime.json'); runtime['process_reservation'] = ticket['id']; put(base / 'runtime.json', runtime)
        put(secondjob / 'process-receipt.json', {'elapsed_seconds': 6, 'state': 'complete', 'process_reservation': ticket['id']})
        source = self.return_from(secondjob, 'MOCK-CONTINUATION-RETURN'); receipt = import_return(self.ledger, source, self.root / 'imports')
        self.assertEqual(receipt['validation_failures'], []); self.assertIn(self.second, canonical_records(self.ledger))
        # Altering first-turn artifacts later blocks both history and continuation.
        path = firstjob / 'worker-output/results/FIXTURE-NOT-MAIN-stage1.json'
        changed = read(path); changed['raw_output'] = 'CONFLICTING MOCK TURN'; path.write_bytes(canonical(changed))
        import_return(self.ledger, self.return_from(firstjob, 'MOCK-FIRST-CONFLICT'), self.root / 'imports')
        self.assertNotIn(self.second, canonical_records(self.ledger))

    def test_rehearsal_cannot_become_main_result_or_bypass_runtime_gate(self):
        job = self.job(); path = job / 'worker-output/results/FIXTURE-NOT-MAIN-stage1.json'
        raw = read(path); raw.update(execution_scope='development_rehearsal', qualification_status='runtime_qualified'); path.write_bytes(canonical(raw))
        result = import_return(self.ledger, self.return_from(job), self.root / 'imports')
        self.assertTrue(result['validation_failures']); self.assertEqual(canonical_records(self.ledger), {})
        context = {'version': VERSION, 'worker_sha256': sha(self.package / 'workers/fixture.py'), 'resolved_condition_sha256': sha(self.package / 'condition.json'),
                   'qualification_status': 'runtime_qualified', 'process_reservation': 'FIXTURE', 'stage_reservations': {self.key: 'FIXTURE'}}
        put(self.root / 'unqualified-main-context.json', context)
        with self.assertRaisesRegex(ValueError, 'qualified runtime'):
            Instrumentation(self.root / 'unqualified-main-context.json', self.package / 'workers/fixture.py', self.package / 'condition.json')
        context['execution_scope'] = 'development_rehearsal'; put(self.root / 'unqualified-development-context.json', context)
        with self.assertRaisesRegex(ValueError, 'prespecified development'):
            Instrumentation(self.root / 'unqualified-development-context.json', self.package / 'workers/fixture.py', self.package / 'condition.json')


if __name__ == '__main__': unittest.main()
