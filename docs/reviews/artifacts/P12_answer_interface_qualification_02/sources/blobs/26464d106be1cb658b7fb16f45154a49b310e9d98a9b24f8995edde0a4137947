"""Explicit Llama CoT boundary, qualified against the pinned tokenizer/XGrammar.

The first exact delimiter is authoritative. No search for JSON or output repair.
One token can span the delimiter and JSON: validate its answer suffix verbatim
before masking subsequent tokens. Invalid suffixes fail closed.
"""
import time

DELIMITER = '<<<FINAL_ANSWER>>>'
COT_INSTRUCTION = (
    '\n\nFor this condition, reason step by step using only the public problem before '
    'giving your answer. Consider the observation cutoff, requested absolute times, '
    'and scheduled controls/interventions. After your reasoning, emit the exact '
    'delimiter <<<FINAL_ANSWER>>> exactly once, then the required compact JSON object. '
    'Do not quote or discuss that delimiter in your reasoning. The final-answer '
    'JSON-only rule applies after the delimiter; reasoning before it is allowed. '
    'Do not put Markdown fences or further commentary after the delimiter.'
)


def separate_explicit(ids, tokenizer):
    raw = tokenizer.decode(ids, skip_special_tokens=False, clean_up_tokenization_spaces=False)
    if DELIMITER not in raw:
        return dict(reasoning_token_ids=list(ids), final_token_ids=[], reasoning=raw,
                    final_text='', separation_failure='missing_final_boundary', boundary_token_suffix='')
    end = raw.index(DELIMITER) + len(DELIMITER)
    # Find the first token completing the exact delimiter, including a straddling token.
    offset = next(i for i in range(1, len(ids) + 1) if DELIMITER in tokenizer.decode(
        ids[:i], skip_special_tokens=False, clean_up_tokenization_spaces=False))
    prefix = tokenizer.decode(ids[:offset], skip_special_tokens=False, clean_up_tokenization_spaces=False)
    suffix = prefix[end:]
    final = suffix + tokenizer.decode(ids[offset:], skip_special_tokens=True, clean_up_tokenization_spaces=False)
    return dict(reasoning_token_ids=list(ids[:offset]), final_token_ids=list(ids[offset:]),
                reasoning=raw[:end], final_text=final.strip(), boundary_token_suffix=suffix,
                boundary_token_offset=offset,
                separation_failure='duplicate_final_boundary' if raw.count(DELIMITER) != 1 else None)


class ExplicitFinalProcessor:
    """Unmasked reasoning, then the same compiled v1.1 grammar on CPU.

    XGrammar 0.1.19 exposes string ingestion only as _debug_accept_string. This
    pinned, offline-tested API consumes ONLY the suffix of the boundary token;
    it never consumes reasoning, alters values, or synthesizes predictions.
    """
    def __init__(self, compiled, tokenizer, prompt_length):
        import xgrammar as xgr
        self.xgr, self.tokenizer, self.prompt_length = xgr, tokenizer, prompt_length
        self.matcher = xgr.GrammarMatcher(compiled)
        self.mask = xgr.allocate_token_bitmask(1, compiled.tokenizer_info.vocab_size)
        self.active = False
        self.activation_offset = None
        self.boundary_token_suffix = ''
        self.last_output_ids = []
        self.calls = self.reasoning_steps = self.final_steps = 0
        self.seconds = 0.0

    def __call__(self, input_ids, scores):
        start = time.perf_counter()
        try:
            if input_ids.shape[0] != 1:
                raise ValueError('single-stream decoder required')
            ids = input_ids[0, self.prompt_length:].tolist()
            previous = len(self.last_output_ids)
            self.last_output_ids = ids
            self.calls += 1
            if not self.active:
                raw = self.tokenizer.decode(ids, skip_special_tokens=False, clean_up_tokenization_spaces=False)
                if DELIMITER not in raw:
                    self.reasoning_steps += 1
                    return scores
                parts = separate_explicit(ids, self.tokenizer)
                if parts['separation_failure'] or parts['boundary_token_offset'] != len(ids):
                    raise ValueError('ambiguous_or_late_final_boundary')
                self.boundary_token_suffix = parts['boundary_token_suffix']
                # As in final_text.strip(), JSON envelope whitespace is immaterial.
                # Keep it in raw output; never trim inside the JSON object/values.
                grammar_prefix = self.boundary_token_suffix.lstrip(' \t\r\n')
                if grammar_prefix and not self.matcher._debug_accept_string(grammar_prefix):
                    raise ValueError('invalid_boundary_token_suffix')
                self.active, self.activation_offset = True, len(ids)
            else:
                if len(ids) != previous + 1 or not self.matcher.accept_token(ids[-1]):
                    raise ValueError('invalid_final_token')
            self.final_steps += 1
            self.matcher.fill_next_token_bitmask(self.mask)
            cpu_scores = scores.to('cpu')
            self.xgr.apply_token_bitmask_inplace(cpu_scores, self.mask)
            return cpu_scores.to(scores.device)
        finally:
            self.seconds += time.perf_counter() - start
