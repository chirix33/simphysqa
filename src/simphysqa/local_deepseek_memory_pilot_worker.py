"""Standalone local GPU worker. Reads only public requests and model settings.

No SimPhysQA/simulator imports, private references, tools or network. Model files
must already exist at the exact pinned snapshot. Each reserved request is attempted
once; incomplete/orphaned reservations are never automatically retried.
"""
import argparse
import hashlib
import importlib.metadata
import json
import os
from pathlib import Path
import time


def canonical(x):return (json.dumps(x,sort_keys=True,separators=(',',':'),ensure_ascii=False,allow_nan=False)+'\n').encode()
def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def put(p,x):
    p.parent.mkdir(parents=True,exist_ok=True)
    with p.open('xb') as f:f.write(canonical(x))


def main():
    p=argparse.ArgumentParser();p.add_argument('--condition',type=Path,required=True);p.add_argument('--requests',type=Path,required=True);p.add_argument('--output',type=Path,required=True)
    a=p.parse_args(); condition=json.loads(a.condition.read_bytes()); requests=json.loads(a.requests.read_bytes());s=condition['settings']
    if any(q['tools']!=[] or q['condition_id']!=condition['condition_id'] for q in requests):raise ValueError('tool/condition boundary')
    os.environ['HF_HUB_OFFLINE']='1';os.environ['TRANSFORMERS_OFFLINE']='1';os.environ['VLLM_NO_USAGE_STATS']='1'
    import torch
    if not torch.cuda.is_available():raise RuntimeError('workstation CUDA unavailable')
    if torch.cuda.get_device_name(0)!='NVIDIA GeForce RTX 5090':raise RuntimeError('GPU identity changed')
    versions={k:importlib.metadata.version(k) for k in ('torch','transformers','tokenizers','safetensors')}
    for k,v in condition['runtime_versions'].items():
        if importlib.metadata.version(k)!=v:raise RuntimeError('runtime revision mismatch: '+k)
    snapshot=Path(condition['snapshot_path'])
    if not snapshot.is_dir() or snapshot.name!=condition['artifact_revision']:raise ValueError('exact local snapshot missing')
    from transformers import AutoTokenizer
    tokenizer=AutoTokenizer.from_pretrained(snapshot,local_files_only=True,trust_remote_code=False)
    if hashlib.sha256(canonical(tokenizer.chat_template)).hexdigest()!=condition['template_sha256']:raise ValueError('template pin mismatch')
    torch.cuda.reset_peak_memory_stats();loaded=time.monotonic()
    backend=condition['backend']
    if backend=='transformers':
        from transformers import AutoModelForCausalLM,StoppingCriteria,StoppingCriteriaList
        model=AutoModelForCausalLM.from_pretrained(snapshot,torch_dtype=torch.bfloat16,attn_implementation='sdpa',local_files_only=True,trust_remote_code=False).to('cuda').eval()
    elif backend=='vllm':
        from vllm import LLM,SamplingParams
        model=LLM(model=str(snapshot),tokenizer=str(snapshot),dtype='bfloat16',max_model_len=s['max_input_and_output'],gpu_memory_utilization=.93,
                  trust_remote_code=False,seed=s['seed'],enforce_eager=True,enable_prefix_caching=False,max_num_seqs=1,**condition.get('backend_options',{}))
    else:raise ValueError('unqualified backend')
    load_seconds=time.monotonic()-loaded
    metadata={'condition_id':condition['condition_id'],'worker_sha256':sha(__file__),'condition_sha256':sha(a.condition),
        'request_list_sha256':sha(a.requests),'runtime_versions':versions,'gpu_name':torch.cuda.get_device_name(0),'gpu_capability':list(torch.cuda.get_device_capability(0)),
        'load_seconds':load_seconds,'peak_loading_allocated_bytes':torch.cuda.max_memory_allocated(),'peak_loading_reserved_bytes':torch.cuda.max_memory_reserved(),
        'snapshot_path':str(snapshot),'artifact_revision':condition['artifact_revision'],'tools':[],'hosted_answering_calls':0}
    put(a.output/'runtime.json',metadata)
    for number,q in enumerate(requests,1):
        sid=q['sample_id']; stage=q.get('stage',1);stem=sid+'-stage'+str(stage); reservation=a.output/'reservations'/(stem+'.json');result=a.output/'results'/(stem+'.json')
        if reservation.exists():
            # Existing reservations retain their outcomes or unknown failure; no retry.
            continue
        torch.manual_seed(s['seed']);torch.cuda.manual_seed_all(s['seed']);torch.cuda.reset_peak_memory_stats()
        template_kwargs={'enable_thinking':s['enable_thinking']} if s.get('enable_thinking') is not None else {}
        text=tokenizer.apply_chat_template(q['messages'],tokenize=False,add_generation_prompt=True,**template_kwargs)
        ids=tokenizer(text,return_tensors='pt',add_special_tokens=False);n=ids['input_ids'].shape[-1]
        prompt_tokens=ids['input_ids'][0].tolist()
        put(reservation,{'sample_id':sid,'stage':stage,'condition_id':condition['condition_id'],'request_sha256':hashlib.sha256(canonical(q)).hexdigest(),
            'prompt_sha256':hashlib.sha256(text.encode()).hexdigest(),'prompt_tokens':n,'max_output_tokens':s['max_new_tokens'],'maximum_seconds':s['max_seconds'],
            'reserved_unix_seconds':time.time(),'attempt':1,'seed':s['seed']})
        put(a.output/'executed-requests'/(stem+'.json'),q)
        put(a.output/'tokenized-prompts'/(stem+'.json'),{'prompt':text,'token_ids':prompt_tokens})
        started=time.monotonic();status='completed';reason=None;output=[];raw=''
        try:
            if n+s['max_new_tokens']>s['max_input_and_output']:raise ValueError('context_capacity_exceeded_no_truncation')
            if backend=='transformers':
                class Deadline(StoppingCriteria):
                    def __call__(self,input_ids,scores,**kwargs):return time.monotonic()-started>=s['max_seconds']
                with torch.inference_mode():
                    generated=model.generate(**{k:v.to('cuda') for k,v in ids.items()},max_new_tokens=s['max_new_tokens'],do_sample=True,
                        temperature=s['temperature'],top_p=s['top_p'],top_k=s['top_k'],pad_token_id=tokenizer.pad_token_id or tokenizer.eos_token_id,
                        stopping_criteria=StoppingCriteriaList([Deadline()]))
                output=generated[0,n:].tolist()
                eos=model.generation_config.eos_token_id
                eos=[eos] if isinstance(eos,int) else eos or []
                if not output or output[-1] not in eos:
                    status='timeout' if time.monotonic()-started>=s['max_seconds'] else 'length_limited';reason=status
            else:
                params=SamplingParams(max_tokens=s['max_new_tokens'],temperature=s['temperature'],top_p=s['top_p'],top_k=s['top_k'],seed=s['seed'])
                key=stem;engine=model.llm_engine;engine.add_request(key,{'prompt_token_ids':prompt_tokens},params)
                last=None
                while engine.has_unfinished_requests():
                    batch=engine.step()
                    if batch:last=batch[-1]
                    if time.monotonic()-started>=s['max_seconds']:
                        engine.abort_request(key);status='timeout';reason=status;break
                if last and last.outputs:
                    output=list(last.outputs[0].token_ids)
                    if last.outputs[0].finish_reason=='length' and status=='completed':status='length_limited';reason=status
            raw=tokenizer.decode(output,skip_special_tokens=True)
        except Exception as e:status='failed';reason=type(e).__name__+': '+str(e)[:220]
        torch.cuda.synchronize()
        value={'sample_id':sid,'condition_id':condition['condition_id'],'stage':stage,'completion_status':status,'failure_reason':reason,
            'raw_output':raw,'output_token_ids':output,'input_tokens':n,'output_tokens':len(output),'latency_seconds':time.monotonic()-started,
            'peak_allocated_bytes':torch.cuda.max_memory_allocated(),'peak_reserved_bytes':torch.cuda.max_memory_reserved(),'request_sha256':hashlib.sha256(canonical(q)).hexdigest(),
            'response_origin':'actual_local_model','reasoning_format_diagnostics':{'explicit_think_closure':'</think>' in raw,'contains_think_open':'<think>' in raw},
            'model_id':condition['model_id'],'artifact_revision':condition['artifact_revision'],'template_sha256':condition['template_sha256']}
        put(result,value);print(json.dumps({k:value[k] for k in ('condition_id','sample_id','stage','completion_status','input_tokens','output_tokens','latency_seconds')}),flush=True)
    put(a.output/'completed.json',{'reserved_requests':len(list((a.output/'reservations').glob('*.json'))),'returned_results':len(list((a.output/'results').glob('*.json'))),'load_seconds':load_seconds})


if __name__=='__main__':main()
