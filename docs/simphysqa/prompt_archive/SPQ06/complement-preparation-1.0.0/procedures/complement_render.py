"""Pinned tokenizer-only complement rendering. No model weights or inference."""
import argparse,hashlib,json,os
from pathlib import Path

def run(a):
 os.environ.update({'HF_HUB_OFFLINE':'1','TRANSFORMERS_OFFLINE':'1','CUDA_VISIBLE_DEVICES':'','TOKENIZERS_PARALLELISM':'false'})
 from simphysqa import execution_adapter as adapter
 from transformers import AutoTokenizer
 import importlib.metadata
 prepared=Path(a.prepared);package=Path(a.package);output=Path(a.output);output.mkdir(parents=True,exist_ok=False)
 public=adapter.read(prepared/'public/execution-inputs.json');bindings=adapter.read(a.bindings);cid=a.condition;label=a.representation
 condition=adapter.resolved_condition(package,cid,bindings,verify_artifacts=False)
 tokenizer=AutoTokenizer.from_pretrained(condition['snapshot_path'],local_files_only=True,trust_remote_code=False)
 if adapter.digest(tokenizer.chat_template)!=condition['template_sha256']:raise ValueError('pinned template differs')
 scientific=adapter.read(prepared/'public/conditions'/f'{cid}.json')
 if adapter.digest(scientific)!=public['conditions'][cid]['sha256']:raise ValueError('scientific condition identity')
 settings=condition['settings'];rows=[];pins={}
 for name in ('tokenizer.json','tokenizer_config.json','special_tokens_map.json','config.json','generation_config.json'):
  path=Path(condition['snapshot_path'])/name
  if path.exists():pins[name]=adapter.sha(path)
 for key,entry in public['requests'].items():
  if key.split('|')[1:3]!=[cid,label]:continue
  path=adapter.within(prepared/'public',entry['path']);q=adapter.read(path)
  if adapter.sha(path)!=entry['sha256']:raise ValueError('request bytes changed')
  options={'enable_thinking':settings['enable_thinking']} if settings.get('enable_thinking') is not None else {}
  prompt=tokenizer.apply_chat_template(q['messages'],tokenize=False,add_generation_prompt=True,**options)
  ids=tokenizer(prompt,add_special_tokens=False)['input_ids'];fits=len(ids)+settings['max_new_tokens']<=settings['max_input_and_output']
  if not fits:raise ValueError('unchanged context/output allowance fails; do not truncate or replace')
  file=output/'rendered'/(q['sample_id']+'.json');adapter.put(file,{'scope':'offline_complement_render_not_executed','worker_key':key,'request_sha256':entry['sha256'],'prompt':prompt,'token_ids':ids,'generation_prefix':True})
  rows.append({'key':key,'request_sha256':entry['sha256'],'render_file':file.relative_to(output).as_posix(),'render_sha256':adapter.sha(file),
   'input_tokens':len(ids),'max_output_tokens':settings['max_new_tokens'],'context_limit':settings['max_input_and_output'],'capacity_ok':fits})
 if len(rows)!=200:raise ValueError('same200 complement inputs per combination required')
 adapter.put(output/'verification.json',{'version':'SPQ06-complement-render/1.0.0','condition_id':cid,'representation':label,'items':rows,'template_sha256':condition['template_sha256'],
  'tokenizer_revision':condition['settings']['tokenizer_revision'],'tokenizer_files':pins,'versions':{k:importlib.metadata.version(k) for k in ('transformers','tokenizers')},
  'weights_loaded':False,'answering_calls':0,'gpu_execution':False,'existing_pinned_profile_used':True,'source_sha256':adapter.sha(__file__)})
 adapter.put(output/'manifest.json',{'files':adapter.files(output),'weights_loaded':False,'answering_calls':0})
 print(json.dumps({'condition':cid,'representation':label,'verified':len(rows),'answering_calls':0}),flush=True)
if __name__=='__main__':
 p=argparse.ArgumentParser()
 for key in ('prepared','package','bindings','condition','representation','output'):p.add_argument('--'+key,required=True)
 run(p.parse_args())
