"""Offline behavioral checks; no network or model generation."""
from copy import deepcopy
import json
import unittest
from unittest.mock import Mock
from test_p04a import example, replace_input, measurement
from phi_jepa.artifacts import canonical
from phi_jepa.providers.compact_answer import compact_schema, compact_messages, adapt_answer
from phi_jepa.providers.constrained_local import FinalOnlyProcessor, CPUMaskProcessor, decoder_schema
from phi_jepa.providers.openai_answer import AnswerParseFailure


def fixture():
    p, _ = example()
    inp = deepcopy(p.input)
    base = inp['answer_spec'][0]
    inp['answer_spec'] = [dict(base, target_id='load:scalar', quantity='scalar', answer_type='number'),
                          dict(base, target_id='load:position', quantity='position', answer_type='vector'), base]
    for s in inp['states']:
        s['measurements'].append(measurement('load', 'scalar', 2.))
    return replace_input(p, inp)


def valid():
    return {'load:scalar': {'status': 'supported', 'value': -1.2345678901234567, 'reason': None},
            'load:position': {'status': 'supported', 'value': [0., -2., 3.], 'reason': None},
            'load:boundary_crossed': {'status': 'supported', 'value': False, 'reason': None}}


class InterfaceTests(unittest.TestCase):
    def test_values_and_metadata_preserved_without_mutation(self):
        p = fixture(); before = canonical(p.input); raw = valid()
        result = adapt_answer(p, json.dumps(raw))
        self.assertEqual(canonical(p.input), before)
        self.assertEqual(result['plain_text_answer'], '')
        for spec, row in zip(p.input['answer_spec'], result['targets']):
            self.assertEqual(row['value'], raw[spec['target_id']]['value'])
            self.assertIs(type(row['value']), type(raw[spec['target_id']]['value']))
            self.assertEqual(row['end_time'], spec['end_time'])

    def test_unknown_missing_duplicate_and_extra_fields(self):
        cases = []
        r = valid(); del r['load:scalar']; cases.append(json.dumps(r))
        r = valid(); r['unknown'] = r['load:scalar']; cases.append(json.dumps(r))
        r = valid(); r['load:scalar']['unit'] = 'm'; cases.append(json.dumps(r))
        text = json.dumps(valid()); cases.append('{"load:scalar":null,' + text[1:])
        cases += ['```json\n' + text + '\n```', text + ' extra']
        for text in cases:
            with self.subTest(text=text), self.assertRaises(AnswerParseFailure):
                adapt_answer(fixture(), text)

    def test_wrong_types_shapes_and_nonfinite(self):
        for key, values in [('load:scalar', [True, None, '2', float('nan'), float('inf')]),
                            ('load:position', [[0, 1], [0, 1, 2, 3], [0, False, 2], [0, float('inf'), 2]]),
                            ('load:boundary_crossed', [0, 1, 'false', None])]:
            for value in values:
                r = valid(); r[key]['value'] = value
                with self.subTest(key=key, value=value), self.assertRaises(AnswerParseFailure):
                    adapt_answer(fixture(), json.dumps(r))
        with self.assertRaises(AnswerParseFailure):
            adapt_answer(fixture(), json.dumps(valid()).replace('-1.2345678901234567', '1e999'))

    def test_supported_reason_and_unsupported_contract(self):
        r = valid(); r['load:scalar']['reason'] = 'explanation'
        with self.assertRaises(AnswerParseFailure): adapt_answer(fixture(), json.dumps(r))
        for reason in [None, '', '   ', 42]:
            r = valid(); r['load:scalar'] = dict(status='unsupported', value=None, reason=reason)
            with self.assertRaises(AnswerParseFailure): adapt_answer(fixture(), json.dumps(r))
        r['load:scalar'] = dict(status='unsupported', value=None, reason='cannot estimate')
        self.assertIsNone(adapt_answer(fixture(), json.dumps(r))['targets'][0]['value'])
        r['load:scalar']['value'] = 0
        with self.assertRaises(AnswerParseFailure): adapt_answer(fixture(), json.dumps(r))

    def test_full_public_content_and_times(self):
        p = fixture(); before = canonical(p.input)
        msg = compact_messages(p, 'instruction')[1]['content']
        header, body = msg.split('\n\n', 1)
        self.assertIn('CUTOFF: 0.2', header)
        self.assertIn('[0.44, 0.44]', header)
        self.assertEqual(canonical(json.loads(body)['public_problem']), before)
        self.assertEqual(set(json.loads(body)), {'public_problem', 'required_answer_schema'})

    def test_reasoning_logits_untouched_and_activation_exact(self):
        import torch
        inner = Mock(side_effect=lambda ids, scores: scores - 3)
        gate = FinalOnlyProcessor(inner, 2, 99)
        scores = torch.zeros(1, 120)
        for seq in ([1, 2], [1, 2, 7], [1, 2, 7, 8]):
            self.assertIs(gate(torch.tensor([seq]), scores), scores)
        inner.assert_not_called()
        self.assertTrue(torch.equal(gate(torch.tensor([[1, 2, 7, 8, 99]]), scores), scores - 3))
        self.assertEqual(gate.activation_offset, 3)
        gate(torch.tensor([[1, 2, 7, 8, 99, 10]]), scores)
        self.assertEqual(inner.call_count, 2)
        direct = FinalOnlyProcessor(inner, 2)
        direct(torch.tensor([[1, 2]]), scores)
        self.assertEqual(direct.final_steps, 1)

    def test_budget_counts_unresolved_attempt_and_never_renews_deadline(self):
        from p12_answer_interface import reserve_attempt
        ledger = dict(started_unix=10., deadline_unix=7210., attempts=[])
        reserve_attempt(ledger, 'qwen', 'a', 'hash', 100., 120.)
        with self.assertRaisesRegex(ValueError, 'already counted'):
            reserve_attempt(ledger, 'qwen', 'a', 'hash', 101., 120.)
        with self.assertRaisesRegex(ValueError, 'window exhausted'):
            reserve_attempt(ledger, 'qwen', 'b', 'hash', 7200., 120.)
        self.assertEqual(ledger['deadline_unix'], 7210.)
        ledger['attempts'] *= 48
        with self.assertRaisesRegex(ValueError, 'cap exhausted'):
            reserve_attempt(ledger, 'qwen', 'b', 'hash', 200., 120.)


class GrammarTests(unittest.TestCase):
    """Exercise the actual installed XGrammar compiler; no mock constraint claims."""
    @classmethod
    def setUpClass(cls):
        import xgrammar as xgr
        cls.xgr = xgr
        info = xgr.TokenizerInfo([bytes([i]) for i in range(256)] + [b'<eos>'], stop_token_ids=[256])
        cls.compiled = xgr.GrammarCompiler(info).compile_json_schema(compact_schema(fixture()))

    def accepted(self, text):
        m = self.xgr.GrammarMatcher(self.compiled)
        return m._debug_accept_string(text) and m.accept_token(256)

    def test_grammar_enforces_fields_types_dimensions_and_branches(self):
        self.assertTrue(self.accepted(json.dumps(valid())))
        variants = []
        r = valid(); del r['load:scalar']; variants.append(r)
        r = valid(); r['extra'] = r['load:scalar']; variants.append(r)
        r = valid(); r['load:position']['value'] = [0, 1]; variants.append(r)
        r = valid(); r['load:boundary_crossed']['value'] = 0; variants.append(r)
        r = valid(); r['load:scalar']['reason'] = 'not null'; variants.append(r)
        r = valid(); r['load:scalar'] = dict(status='unsupported', value=1, reason='unknown'); variants.append(r)
        r = valid(); r['load:scalar'] = dict(status='unsupported', value=None, reason=''); variants.append(r)
        r = valid(); r['load:scalar'] = dict(status='unsupported', value=None, reason='   '); variants.append(r)
        for r in variants:
            with self.subTest(r=r): self.assertFalse(self.accepted(json.dumps(r)))
        text = json.dumps(valid())
        self.assertFalse(self.accepted('{"load:scalar":null,' + text[1:]))
        self.assertFalse(self.accepted('```json\n' + text + '\n```'))

    def test_grammar_limits_are_still_checked_by_canonical_parser(self):
        # JSON number syntax permits overflowing exponents; the final boundary must reject them.
        text = json.dumps(valid()).replace('-1.2345678901234567', '1e999')
        self.assertTrue(self.accepted(text))
        with self.assertRaises(AnswerParseFailure): adapt_answer(fixture(), text)
        r = valid(); r['load:scalar'] = dict(status='unsupported', value=None, reason='   ')
        with self.assertRaises(AnswerParseFailure): adapt_answer(fixture(), json.dumps(r))

    def test_cpu_mask_on_actual_cuda_logits(self):
        import torch
        from xgrammar.contrib.hf import LogitsProcessor
        # This test intentionally covers the native runtime path before loading any model.
        if not torch.cuda.is_available(): self.skipTest('CUDA required for transfer-path check')
        inner = LogitsProcessor(self.compiled)
        processor = CPUMaskProcessor(inner)
        ids = torch.tensor([[1, 2]], device='cuda')
        scores = torch.zeros((1, 257), device='cuda')
        result = processor(ids, scores)
        self.assertEqual(result.device.type, 'cuda')
        self.assertTrue(torch.isfinite(result[0, ord('{')]))
        self.assertTrue(torch.isneginf(result[0, ord('x')]))
        # Subsequent sampled token is accepted by the matcher, preserving allowed scores.
        result = processor(torch.tensor([[1,2,ord('{')]],device='cuda'), scores)
        self.assertTrue(torch.isfinite(result[0, ord('"')]))

    def test_saved_request_preserves_schema_order_and_branch_choices(self):
        p = fixture(); schema = compact_schema(p)
        original = json.dumps(schema, ensure_ascii=False)
        request = json.loads(canonical({'schema':schema, 'schema_json':original}))
        # Canonical JSON reordered the map, but the executable schema string is exact.
        self.assertNotEqual(list(request['schema']['properties']), list(schema['properties']))
        self.assertEqual(decoder_schema(request,p), original)
        info = self.xgr.TokenizerInfo([bytes([i]) for i in range(256)]+[b'<eos>'], stop_token_ids=[256])
        compiled = self.xgr.GrammarCompiler(info).compile_json_schema(decoder_schema(request,p))
        for row in (valid(), {k:dict(status='unsupported',value=None,reason='not enough information') for k in valid()}):
            matcher=self.xgr.GrammarMatcher(compiled)
            self.assertTrue(matcher._debug_accept_string(json.dumps(row)))
            self.assertTrue(matcher.accept_token(256))
        request['schema_json']=json.dumps(request['schema'],ensure_ascii=False)
        with self.assertRaisesRegex(ValueError,'identity mismatch'):decoder_schema(request,p)


if __name__ == '__main__': unittest.main()
