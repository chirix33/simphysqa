"""Versioned compact local interface; native Qwen reasoning then XGrammar JSON."""
from dataclasses import asdict
import time
from phi_jepa.artifacts import digest
from phi_jepa.integration.readers import strict_json
from .compact_answer import VERSION, compact_messages, compact_schema, adapt_answer
from .local_answer import InputLengthFailure, separate_output
from .openai_answer import AnswerParseFailure


def prepare_request(tokenizer, problem, instruction, settings):
    if digest(tokenizer.chat_template) != settings.template_sha256:
        raise ValueError('chat template identity mismatch')
    messages = compact_messages(problem, instruction)
    kwargs = {'add_generation_prompt': True, 'truncation': False}
    if settings.enable_thinking is not None:
        kwargs['enable_thinking'] = settings.enable_thinking
    ids = tokenizer.apply_chat_template(messages, tokenize=True, **kwargs)
    rendered = tokenizer.apply_chat_template(messages, tokenize=False, **kwargs)
    if not ids or any(type(t) is not int or t < 0 for t in ids):
        raise ValueError('invalid prompt token IDs')
    if len(ids) + settings.max_new_tokens > settings.max_input_and_output:
        raise InputLengthFailure(len(ids), settings.max_new_tokens, settings.max_input_and_output)
    return {'version': VERSION, 'settings': asdict(settings), 'public_sha256': digest(problem.input),
            'messages': messages, 'rendered_prompt': rendered, 'input_token_ids': ids,
            'schema': compact_schema(problem), 'decoder': 'xgrammar==0.1.19; final-only; schema strict mode; CPU mask',
            'tools': False, 'retrieval': False, 'enrichment': False}


class FinalOnlyProcessor:
    """Single-stream processor. Never mask Qwen reasoning or consume its closing token."""
    def __init__(self, inner, prompt_length, thinking_marker=None):
        self.inner, self.prompt_length, self.marker = inner, prompt_length, thinking_marker
        self.active = thinking_marker is None
        self.activation_offset = 0 if self.active else None
        self.calls = self.reasoning_steps = self.final_steps = 0
        self.seconds = 0.0
        self.last_output_ids = []

    def __call__(self, input_ids, scores):
        start = time.perf_counter()
        try:
            if input_ids.shape[0] != 1:
                raise ValueError('single-stream decoder required')
            generated = input_ids[0, self.prompt_length:].tolist()
            self.last_output_ids = generated
            self.calls += 1
            if not self.active:
                if self.marker not in generated:
                    self.reasoning_steps += 1
                    return scores
                self.activation_offset = generated.index(self.marker) + 1
                if len(generated) != self.activation_offset:
                    raise ValueError('late answer constraint activation')
                self.active = True
            self.final_steps += 1
            return self.inner(input_ids, scores)
        finally:
            self.seconds += time.perf_counter() - start


class CPUMaskProcessor:
    """Use XGrammar's compiled CPU mask kernel; no Triton/C compiler requirement.

    Transfers and mask processing are included in the outer processor timer and
    request wall time. No sampling occurs here and no logits change except the mask.
    """
    def __init__(self, inner):
        self.inner = inner

    def __call__(self, input_ids, scores):
        return self.inner(input_ids.to('cpu'), scores.to('cpu')).to(scores.device)


class ConstrainedLocalBackend:
    def __init__(self, model, tokenizer, settings, instruction):
        import xgrammar as xgr
        self.model, self.tokenizer, self.settings, self.instruction = model, tokenizer, settings, instruction
        self.model.eval()
        for p in model.parameters():
            p.requires_grad_(False)
        start = time.perf_counter()
        eos = model.generation_config.eos_token_id
        self.eos_ids = eos if isinstance(eos, list) else [eos]
        info = xgr.TokenizerInfo.from_huggingface(tokenizer, vocab_size=model.config.vocab_size,
                                                stop_token_ids=self.eos_ids)
        self.compiler = xgr.GrammarCompiler(info)
        self.compiler_setup_seconds = time.perf_counter() - start

    def answer(self, problem, request=None):
        import torch
        from xgrammar.contrib.hf import LogitsProcessor
        request = request or prepare_request(self.tokenizer, problem, self.instruction, self.settings)
        ids = request['input_token_ids']
        record = {'sample_id': problem.sample_id, 'identity': request, 'request_sha256': digest(request),
                  'input_tokens': len(ids), 'answer': None, 'syntax_valid': False, 'full_contract_valid': False,
                  'status': 'runtime_failure', 'generated_token_ids': [], 'raw_completion': '',
                  'output_tokens': 0, 'reasoning_tokens': 0, 'final_answer_tokens': 0,
                  'EOS_terminated': False, 'token_cap_termination': False, 'time_cap_termination': False,
                  'retries': 0, 'repairs': 0}
        processor = None
        torch.manual_seed(self.settings.seed)
        torch.cuda.manual_seed_all(self.settings.seed)
        torch.cuda.synchronize()
        torch.cuda.reset_peak_memory_stats()
        start = time.perf_counter()
        try:
            compile_start = time.perf_counter()
            compiled = self.compiler.compile_json_schema(request['schema'])
            record['constraint_compile_seconds'] = time.perf_counter() - compile_start
            marker = None
            if self.settings.enable_thinking is True:
                marker = self.tokenizer.convert_tokens_to_ids('</think>')
                if marker is None or marker == self.tokenizer.unk_token_id:
                    raise ValueError('native thinking marker unavailable')
            processor = FinalOnlyProcessor(CPUMaskProcessor(LogitsProcessor(compiled)), len(ids), marker)
            inputs = torch.tensor([ids], dtype=torch.long, device=self.model.device)
            remaining = self.settings.max_seconds - (time.perf_counter() - start)
            if remaining <= 0:
                raise TimeoutError('constraint compilation exhausted request budget')
            with torch.inference_mode():
                generated = self.model.generate(input_ids=inputs, attention_mask=torch.ones_like(inputs),
                    do_sample=True, temperature=self.settings.temperature, top_p=self.settings.top_p,
                    top_k=self.settings.top_k, min_p=0.0, max_new_tokens=self.settings.max_new_tokens,
                    max_time=remaining, logits_processor=[processor],
                    eos_token_id=self.model.generation_config.eos_token_id,
                    pad_token_id=self.tokenizer.pad_token_id or self.tokenizer.eos_token_id, use_cache=True)
            output = generated[0, len(ids):].tolist()
            parts = separate_output(output, self.tokenizer, self.settings.enable_thinking is True)
            ended = bool(output and output[-1] in self.eos_ids)
            record.update(parts, generated_token_ids=output, raw_completion=self.tokenizer.decode(output, skip_special_tokens=False),
                          output_tokens=len(output), reasoning_tokens=len(parts['reasoning_token_ids']),
                          final_answer_tokens=len(parts['final_token_ids']), EOS_terminated=ended,
                          token_cap_termination=len(output) >= self.settings.max_new_tokens and not ended,
                          time_cap_termination=not ended and len(output) < self.settings.max_new_tokens)
            try:
                strict_json(parts['final_text'])
                record['syntax_valid'] = True
            except ValueError:
                pass
            if not ended:
                record.update(status='generation_incomplete', failure='token_cap' if record['token_cap_termination'] else 'time_cap')
            elif parts['separation_failure']:
                record.update(status='malformed_output', failure=parts['separation_failure'])
            else:
                try:
                    answer = adapt_answer(problem, parts['final_text'])
                    record.update(answer=answer, full_contract_valid=True, status='success', failure=None)
                except AnswerParseFailure as exc:
                    record.update(status='contract_failure', failure=exc.reason)
        except Exception as exc:
            record.update(status='runtime_failure', failure=type(exc).__name__, failure_detail=str(exc))
            if processor:
                output = processor.last_output_ids
                parts = separate_output(output, self.tokenizer, self.settings.enable_thinking is True)
                record.update(parts, generated_token_ids=output, output_tokens=len(output),
                              raw_completion=self.tokenizer.decode(output, skip_special_tokens=False),
                              reasoning_tokens=len(parts['reasoning_token_ids']), final_answer_tokens=len(parts['final_token_ids']))
                record['partial_tokens_note'] = 'Tokens observed by the processor before the runtime exception.'
        finally:
            torch.cuda.synchronize()
            record.update(latency_seconds=time.perf_counter() - start,
                          peak_allocated_bytes=torch.cuda.max_memory_allocated(), peak_reserved_bytes=torch.cuda.max_memory_reserved())
            if processor:
                record['constraint_processing'] = {'seconds': processor.seconds, 'calls': processor.calls,
                    'unconstrained_reasoning_steps': processor.reasoning_steps, 'constrained_final_steps': processor.final_steps,
                    'activation_offset': processor.activation_offset}
        return record
