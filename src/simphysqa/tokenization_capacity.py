"""CPU-only tokenization, including conservative dialogue capacity; no inference."""
import argparse,hashlib,json,os,subprocess,ast
from pathlib import Path
from collections import Counter
from transformers import AutoTokenizer
from jinja2 import Environment,StrictUndefined

def read(path):return json.loads(Path(path).read_bytes())
def canonical(x):return (json.dumps(x,sort_keys=True,separators=(',',':'),ensure_ascii=False,allow_nan=False)+'\n').encode()
def write(path,x):
    path.parent.mkdir(parents=True,exist_ok=True)
    with path.open('xb') as f:f.write(canonical(x))
def sha(path):
    with Path(path).open('rb') as f:return hashlib.file_digest(f,'sha256').hexdigest()

class GemmaTokenizer:
    def __init__(self,condition,base,pilot,output):
        self.c=condition;self.output=output;self.template=read(base/'gemma-gguf-metadata-1.0.0.json')['metadata']['tokenizer.chat_template']
        if hashlib.sha256(canonical(self.template)).hexdigest()!=condition['template_sha256']:raise ValueError('embedded GGUF template changed')
        self.env={**os.environ,'LD_LIBRARY_PATH':':'.join(condition['library_paths']),'CUDA_VISIBLE_DEVICES':''}
        self.tool=Path(condition['server_path']).with_name('llama-tokenize')
        def fail(message):raise ValueError(message)
        self.renderer=Environment(undefined=StrictUndefined).from_string(self.template)
        self.renderer.environment.globals['raise_exception']=fail
        self.renderer.environment.globals['strftime_now']=lambda fmt:'2026-10-09' # Actual Gemma template has no date call.
        checks=[]
        for p in pilot.glob('executions/gemma3_27b_qat_*-stage*/tokenized-prompts/*.json'):
            request=p.parent.parent/'executed-requests'/p.name
            if not request.exists():continue
            actual=read(p);rendered=self.render(read(request)['messages'])
            if rendered!=actual['prompt']:raise ValueError('offline GGUF render differs from actual pinned llama.cpp prompt')
            if not checks:
                ids=self.tokens(rendered)
                if ids!=actual['token_ids']:raise ValueError('offline GGUF tokenizer differs from actual server token IDs')
            checks.append({'request_sha256':sha(request),'prompt_file_sha256':sha(p),'render_exact':True})
        if not checks:raise ValueError('no actual Gemma prompt evidence for renderer qualification')
        write(output/'gemma-renderer-qualification.json',{'checks':checks,'binary_sha256':sha(self.tool),'inference_calls':0})
    def render(self,messages):
        # Pinned llama.cpp /apply-template omits BOS. Qualify exact text against
        # every saved actual prompt and exact token IDs against its tokenizer.
        return self.renderer.render(messages=messages,add_generation_prompt=True,bos_token='',eos_token='')
    def tokens(self,prompt):
        r=subprocess.run([str(self.tool),'-m',self.c['gguf_path'],'--stdin','--ids','--no-bos','--no-escape','--offline'],
            input=prompt,env=self.env,capture_output=True,text=True,timeout=60)
        if r.returncode:raise RuntimeError('pinned CPU GGUF tokenizer failed: '+r.stderr[-240:])
        ids=ast.literal_eval(r.stdout.strip())
        if not isinstance(ids,list) or any(type(i) is not int for i in ids):raise ValueError('invalid tokenizer IDs')
        return ids
    def count(self,messages):return len(self.tokens(self.render(messages)))

def run(preparation,pilot,base,output,dry):
    output.mkdir(parents=True,exist_ok=False);rows=[];tokenizers={};gemma=None
    configs=sorted((pilot/'conditions').glob('*.json')) if dry else sorted((preparation/'conditions').glob('*.json'))
    for path in configs:
        cid=read(path)['condition_id'];c=read(path)
        if dry:
            revisions=sorted((pilot/'condition-revisions'/cid).glob('*.json'))
            if revisions:c=read(revisions[-1])
        s=c['settings']
        if 'gguf_path' in c:
            if gemma is None:gemma=GemmaTokenizer(c,base,pilot,output)
            count=gemma.count
        else:
            snapshot=c['snapshot_path']
            if snapshot not in tokenizers:tokenizers[snapshot]=AutoTokenizer.from_pretrained(snapshot,local_files_only=True,trust_remote_code=False)
            tokenizer=tokenizers[snapshot]
            if hashlib.sha256(canonical(tokenizer.chat_template)).hexdigest()!=c['template_sha256']:raise ValueError('pinned template changed')
            kwargs={'enable_thinking':s['enable_thinking']} if s.get('enable_thinking') is not None else {}
            def count(messages):
                text=tokenizer.apply_chat_template(messages,tokenize=False,add_generation_prompt=True,**kwargs)
                return len(tokenizer(text,add_special_tokens=False)['input_ids'])
        paths=[preparation/(cid+'-stage1.json')] if dry else list((preparation/'request-lists/400').glob(cid+'-*-stage1.json'))
        for requests_path in paths:
            for q in read(requests_path):
                n=count(q['messages']);maxout=s['max_new_tokens'];limit=s['max_input_and_output']
                row={'condition_id':cid,'sample_id':q['sample_id'],'input_condition':q.get('input_condition','enriched'),
                    'request_file_sha256':sha(requests_path),'request_sha256':hashlib.sha256(canonical(q)).hexdigest(),
                    'initial_input_tokens':n,'initial_max_output_tokens':maxout,'context_limit':limit,'initial_capacity_ok':n+maxout<=limit}
                if not dry:
                    reply=preparation/'private/conditional-public-replies'/q['input_condition']/(q['sample_id']+'.json')
                    if reply.exists():
                        content=read(reply)['stage2_user_content'];empty=q['messages']+[{'role':'assistant','content':''},{'role':'user','content':content}]
                        # Future actual assistant text is unknown. Reserve its full
                        # output allowance and additional boundary slack; never truncate.
                        overhead=count(empty)-n;bound=n+overhead+maxout+64+maxout
                        row.update({'conditional_reply_file_sha256':sha(reply),'continuation_additional_template_and_reply_tokens':overhead,
                            'continuation_full_allowances_upper_bound_tokens':bound,'continuation_capacity_ok':bound<=limit,
                            'continuation_bound_policy':'initial+exact empty-assistant template/reply delta+full first output allowance+64boundary slack+full second output allowance; actual continuation rechecked before inference'})
                rows.append(row)
        print(json.dumps({'condition_id':cid,'checked':sum(r['condition_id']==cid for r in rows),'inference_calls':0}),flush=True)
    write(output/'capacity-checks.json',{'version':'SPQ06-tokenization-capacity/1.0.0','items':rows,
        'initial_failures':sum(not r['initial_capacity_ok'] for r in rows),
        'conservative_continuation_failures':sum(not r.get('continuation_capacity_ok',True) for r in rows),
        'new_model_calls':0,'gpu_execution':False,'tokenizer_procedure_sha256':sha(__file__)})

if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('--preparation',type=Path,required=True);p.add_argument('--pilot',type=Path,required=True)
    p.add_argument('--base',type=Path,required=True);p.add_argument('--output',type=Path,required=True);p.add_argument('--dry',action='store_true')
    a=p.parse_args();run(a.preparation,a.pilot,a.base,a.output,a.dry)
