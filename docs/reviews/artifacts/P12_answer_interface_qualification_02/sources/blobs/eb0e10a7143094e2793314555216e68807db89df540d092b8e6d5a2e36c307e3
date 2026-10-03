"""Offline pinned-tokenizer boundary checks; never load model weights."""
import json
import unittest
from phi_jepa.providers.explicit_reasoning import DELIMITER, ExplicitFinalProcessor, separate_explicit
from phi_jepa.providers.compact_answer import compact_schema, adapt_answer
from phi_jepa.providers.constrained_local import prepare_request
from p12_answer_interface import settings_and_tokenizer, ASSET
from p12_common import load
from test_p12_answer_interface import fixture, valid


class ExplicitBoundaryTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        import torch
        import xgrammar as xgr
        from transformers import AutoConfig
        torch.set_num_threads(2)
        cls.torch = torch
        cls.settings, cls.tokenizer = settings_and_tokenizer('llama31_8b_direct')
        cfg = AutoConfig.from_pretrained(cls.settings.model, revision=cls.settings.revision,
            cache_dir='/home/aashraf/phi-jepa/model-cache', local_files_only=True)
        cls.vocab = cfg.vocab_size
        cls.compiled = xgr.GrammarCompiler(xgr.TokenizerInfo.from_huggingface(cls.tokenizer,
            vocab_size=cls.vocab, stop_token_ids=cls.tokenizer.eos_token_id)).compile_json_schema(compact_schema(fixture()))

    def test_actual_tokenizer_streaming_delimiter_and_straddling(self):
        torch, tok = self.torch, self.tokenizer
        overlaps = set()
        for reasoning in ('Calculation.\n', 'A quoted JSON example {"fake": 9} is reasoning.\n\n', 'Reasoning '):
            for gap in ('', '\n', '\n\n'):
                text = reasoning + DELIMITER + gap + json.dumps(valid())
                ids = tok.encode(text, add_special_tokens=False) + [tok.eos_token_id]
                gate = ExplicitFinalProcessor(self.compiled, tok, 1)
                prefix = [1]
                for token in ids:
                    scores = torch.zeros((1, self.vocab))
                    output = gate(torch.tensor([prefix]), scores)
                    if gate.active:
                        self.assertTrue(torch.isfinite(output[0, token]), (gap, tok.decode([token])))
                    else:
                        self.assertIs(output, scores)
                        self.assertTrue(torch.equal(output, torch.zeros_like(output)))
                    prefix.append(token)
                parts = separate_explicit(ids, tok)
                self.assertIsNone(parts['separation_failure'])
                self.assertEqual(parts['reasoning'], reasoning + DELIMITER)
                self.assertEqual(json.loads(parts['final_text']), valid())
                self.assertEqual(len(parts['reasoning_token_ids']) + len(parts['final_token_ids']), len(ids))
                self.assertTrue(gate.matcher.accept_token(tok.eos_token_id))
                adapt_answer(fixture(), parts['final_text'])
                overlaps.add(gate.boundary_token_suffix)
        self.assertIn('\n', overlaps)
        # Generation can use a different tokenization than encode(full_text).
        # The actual vocabulary contains a single token for '>{'.
        crossing = tok.encode('>{', add_special_tokens=False)
        self.assertEqual(len(crossing), 1)
        prefix = tok.encode('Reasoning\n' + DELIMITER[:-1], add_special_tokens=False) + crossing
        gate = ExplicitFinalProcessor(self.compiled, tok, 0)
        for i in range(len(prefix) + 1):
            gate(torch.tensor([prefix[:i]], dtype=torch.long), torch.zeros((1, self.vocab)))
        self.assertEqual(gate.boundary_token_suffix, '{')
        tail = tok.encode(json.dumps(valid())[1:], add_special_tokens=False)
        for token in tail:
            self.assertTrue(gate.matcher.accept_token(token))
        self.assertTrue(gate.matcher.accept_token(tok.eos_token_id))
        parts = separate_explicit(prefix + tail + [tok.eos_token_id], tok)
        self.assertEqual(json.loads(parts['final_text']), valid())

    def test_missing_partial_duplicate_and_arbitrary_json_do_not_recover(self):
        for text in ('Reasoning ' + json.dumps(valid()), DELIMITER[:-1] + json.dumps(valid()), ''):
            parts = separate_explicit(self.tokenizer.encode(text, add_special_tokens=False), self.tokenizer)
            self.assertEqual(parts['separation_failure'], 'missing_final_boundary')
            self.assertEqual(parts['final_text'], '')
        parts = separate_explicit(self.tokenizer.encode(DELIMITER + '{}' + DELIMITER + '{}',
            add_special_tokens=False), self.tokenizer)
        self.assertEqual(parts['separation_failure'], 'duplicate_final_boundary')

    def test_illegal_boundary_suffix_fails_without_repair(self):
        # Feed a token prefix completing a delimiter and illegal following text.
        # If a tokenizer doesn't merge the illegal suffix, the next mask rejects it.
        tok, torch = self.tokenizer, self.torch
        ids = tok.encode('Reasoning\n' + DELIMITER + 'x', add_special_tokens=False)
        gate = ExplicitFinalProcessor(self.compiled, tok, 0)
        for i in range(len(ids) + 1):
            try:
                output = gate(torch.tensor([ids[:i]], dtype=torch.long), torch.zeros((1, self.vocab)))
            except ValueError as exc:
                self.assertIn(str(exc), ('invalid_boundary_token_suffix', 'invalid_final_token'))
                break
            if gate.active and i < len(ids) and not torch.isfinite(output[0, ids[i]]):
                break
        else:
            self.fail('illegal answer suffix accepted')

    def test_public_problem_and_native_template_preserved(self):
        p = fixture()
        direct = prepare_request(self.tokenizer, p, load(ASSET)['prompt'], self.settings)
        cot = prepare_request(self.tokenizer, p, load(ASSET)['prompt'], self.settings, True)
        self.assertEqual(direct['messages'][1], cot['messages'][1])
        self.assertEqual(direct['schema_json'], cot['schema_json'])
        self.assertEqual(cot['settings']['enable_thinking'], None)
        self.assertEqual(cot['reasoning_mode'], 'explicit_cot')
        self.assertIn('reason step by step', cot['messages'][0]['content'])
        self.assertEqual(cot['final_delimiter'], DELIMITER)


if __name__ == '__main__':
    unittest.main()
