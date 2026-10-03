"""Frozen local direct-answer backends. Public-only inputs; no tools or retrieval."""
from dataclasses import asdict, dataclass
import time
from phi_jepa.artifacts import canonical, digest
from phi_jepa.integration.contracts import PublicProblem
from .openai_answer import answer_schema, parse_answer, AnswerParseFailure


@dataclass(frozen=True)
class LocalAnswerSettings:
    model: str
    revision: str
    tokenizer_revision: str
    template_sha256: str
    runtime: tuple
    enable_thinking: bool | None
    max_input_and_output: int = 32768
    max_new_tokens: int = 1024
    max_seconds: float = 120.0
    temperature: float = 0.7
    top_p: float = 0.8
    top_k: int = 20
    seed: int = 11
    precision: str = 'bfloat16'
    quantization: str = 'none'
    attention: str = 'sdpa'

    def __post_init__(self):
        if self.model not in ('Qwen/Qwen3-8B','meta-llama/Llama-3.1-8B-Instruct'):
            raise ValueError('unapproved local checkpoint')
        if self.model.startswith('Qwen/') and type(self.enable_thinking) is not bool:
            raise ValueError('explicit Qwen thinking switch required')
        if self.model.startswith('meta-llama/') and self.enable_thinking is not None:
            raise ValueError('Llama has no native thinking switch')
        if any(len(v)!=40 or any(c not in '0123456789abcdef' for c in v) for v in (self.revision,self.tokenizer_revision)):
            raise ValueError('immutable checkpoint/tokenizer SHA required')
        if self.precision!='bfloat16' or self.quantization!='none' or self.attention!='sdpa':
            raise ValueError('unqualified runtime profile')
        if not 0<self.max_new_tokens<self.max_input_and_output or self.max_seconds<=0:
            raise ValueError('explicit generation limits required')


def messages(problem: PublicProblem, instruction: str):
    if type(problem) is not PublicProblem: raise ValueError('public-only input required')
    return [{'role':'system','content':instruction},
            {'role':'user','content':canonical({'public_problem':problem.input,'required_answer_schema':answer_schema(problem)}).decode()}]


class InputLengthFailure(ValueError):
    def __init__(self, input_tokens, output_reserve, context_limit):
        super().__init__('input_plus_output_overlength_no_truncation')
        self.input_tokens,self.output_reserve,self.context_limit=input_tokens,output_reserve,context_limit


def request_identity(settings, problem, instruction, ids):
    return {'version':'p12-local-public-answer-v1','settings':asdict(settings),'public_sha256':digest(problem.input),
            'instruction':instruction,'input_token_ids':ids,'tools':False,'retrieval':False}


def verify_cached_record(record, expected):
    if record.get('request_sha256')!=digest(expected) or digest(record.get('identity'))!=digest(expected):
        raise ValueError('incompatible local answer cache identity')


def prepare_tokens(tokenizer, problem, instruction, settings):
    if digest(tokenizer.chat_template)!=settings.template_sha256:raise ValueError('chat template identity mismatch')
    kwargs={'add_generation_prompt':True,'tokenize':True,'truncation':False}
    if settings.enable_thinking is not None:kwargs['enable_thinking']=settings.enable_thinking
    ids=tokenizer.apply_chat_template(messages(problem,instruction),**kwargs)
    if not ids or any(type(t) is not int or t<0 for t in ids):raise ValueError('invalid prompt token IDs')
    if len(ids)+settings.max_new_tokens>settings.max_input_and_output:
        raise InputLengthFailure(len(ids),settings.max_new_tokens,settings.max_input_and_output)
    return ids


def separate_output(ids, tokenizer, thinking):
    """Only bytes after Qwen's generated closing marker can be parsed as an answer."""
    if thinking:
        marker=tokenizer.convert_tokens_to_ids('</think>')
        if marker is None or marker==tokenizer.unk_token_id or marker not in ids:
            return {'reasoning_token_ids':list(ids),'final_token_ids':[], 'reasoning':tokenizer.decode(ids,skip_special_tokens=False),
                    'final_text':'','separation_failure':'missing_thinking_end'}
        index=ids.index(marker)+1
        reason,final=ids[:index],ids[index:]
    else:reason,final=[],ids
    return {'reasoning_token_ids':list(reason),'final_token_ids':list(final),
            'reasoning':tokenizer.decode(reason,skip_special_tokens=False),
            'final_text':tokenizer.decode(final,skip_special_tokens=True).strip(),'separation_failure':None}


class LocalAnswerBackend:
    def __init__(self,model,tokenizer,settings,instruction):
        self.model,self.tokenizer,self.settings,self.instruction=model,tokenizer,settings,instruction
        self.model.eval()
        for p in self.model.parameters():p.requires_grad_(False)

    def request_identity(self,problem,ids):
        return request_identity(self.settings,problem,self.instruction,ids)

    def answer(self,problem):
        import torch
        ids=prepare_tokens(self.tokenizer,problem,self.instruction,self.settings)
        identity=self.request_identity(problem,ids)
        record={'sample_id':problem.sample_id,'request_sha256':digest(identity),'identity':identity,
                'input_tokens':len(ids),'status':'runtime_failure','answer':None,'raw_completion':None,
                'generated_token_ids':[],'reasoning_tokens':0,'final_answer_tokens':0,'output_tokens':0,
                'EOS_terminated':False,'token_cap_termination':False,'time_cap_termination':False}
        torch.manual_seed(self.settings.seed);torch.cuda.manual_seed_all(self.settings.seed)
        torch.cuda.synchronize();torch.cuda.reset_peak_memory_stats();start=time.perf_counter()
        try:
            inputs=torch.tensor([ids],dtype=torch.long,device=self.model.device)
            eos=self.model.generation_config.eos_token_id
            eos_ids=eos if isinstance(eos,list) else [eos]
            with torch.inference_mode():
                generated=self.model.generate(input_ids=inputs,attention_mask=torch.ones_like(inputs),
                    do_sample=True,temperature=self.settings.temperature,top_p=self.settings.top_p,top_k=self.settings.top_k,
                    min_p=0.0,max_new_tokens=self.settings.max_new_tokens,max_time=self.settings.max_seconds,
                    eos_token_id=eos,pad_token_id=self.tokenizer.pad_token_id or self.tokenizer.eos_token_id,use_cache=True)
            output=generated[0,len(ids):].tolist();parts=separate_output(output,self.tokenizer,self.settings.enable_thinking is True)
            ended=bool(output and output[-1] in eos_ids)
            record.update(parts,generated_token_ids=output,raw_completion=self.tokenizer.decode(output,skip_special_tokens=False),
                          reasoning_tokens=len(parts['reasoning_token_ids']),final_answer_tokens=len(parts['final_token_ids']),
                          output_tokens=len(output),EOS_terminated=ended,token_cap_termination=len(output)>=self.settings.max_new_tokens and not ended,
                          time_cap_termination=not ended and len(output)<self.settings.max_new_tokens)
            if not ended:record.update(status='generation_incomplete',failure='token_cap' if record['token_cap_termination'] else 'time_cap')
            elif parts['separation_failure']:record.update(status='malformed_output',failure=parts['separation_failure'])
            else:
                try:record.update(answer=parse_answer(problem,parts['final_text'],[],boolean_policy='direct_prediction'),status='success',failure=None)
                except AnswerParseFailure as exc:record.update(status='malformed_output',failure=exc.reason)
        except Exception as exc:
            record.update(status='runtime_failure',failure=type(exc).__name__)
        finally:
            torch.cuda.synchronize()
            record.update(latency_seconds=time.perf_counter()-start,peak_allocated_bytes=torch.cuda.max_memory_allocated(),
                          peak_reserved_bytes=torch.cuda.max_memory_reserved())
        return record
