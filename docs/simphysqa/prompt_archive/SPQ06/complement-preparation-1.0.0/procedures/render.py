"""Offline exact complement tokenizer verification; never answering inference."""
import json,subprocess,time
from pathlib import Path
from simphysqa import execution_adapter as a
from simphysqa.complement_preparation import COMBINATIONS
BASE=Path('C:/Users/aashraf/.codex/visualizations/2026/10/06/01a1131b-eac2-7a31-afb4-f219a8dd6471/spq06/2026-10-09');REPO=Path('C:/Users/aashraf/.codex/worktrees/simphysqa/phi-jepa');PREP=BASE/'complement-preparation-1.0.1';OUTPUT=BASE/'complement-render-1.0.0'
def linux(p):
 s=str(p).replace('\\','/');return '/mnt/'+s[0].lower()+s[2:] if len(s)>1 and s[1]==':' else s
OUTPUT.mkdir(exist_ok=False);results=[]
for cid,label in COMBINATIONS:
 name=cid+'--'+label;bindings=BASE/'main-ashraf-1.0.0/bindings'/(name+'.json');b=a.read(bindings)
 args=['wsl.exe','-d','Ubuntu-24.04','--','env','PYTHONDONTWRITEBYTECODE=1','PYTHONUTF8=1','HF_HUB_OFFLINE=1','TRANSFORMERS_OFFLINE=1','CUDA_VISIBLE_DEVICES=',
  'PYTHONPATH='+linux(REPO/'src'),b['interpreter'],'-m','simphysqa.complement_render','--prepared',linux(PREP),'--package',linux(BASE/'execution-public-1.1.1'),
  '--bindings',linux(bindings),'--condition',cid,'--representation',label,'--output',linux(OUTPUT/name)]
 a.put(OUTPUT/(name+'-command.json'),{'args':args,'scope':'offline_render_only','weights_loaded':False,'answering_calls':0});start=time.monotonic()
 with (OUTPUT/(name+'.log')).open('xb') as log:r=subprocess.run(args,stdout=log,stderr=subprocess.STDOUT,timeout=900)
 a.put(OUTPUT/(name+'-lifecycle.json'),{'elapsed_seconds':time.monotonic()-start,'returncode':r.returncode,'scope':'offline_render_only'})
 if r.returncode:raise RuntimeError('offline render failed; preserve '+name+' log')
 v=a.read(OUTPUT/name/'verification.json');cap=a.read(PREP/'organizer/reused-capacity-evidence.json');lookup={(r['sample_id'],r['condition_id'],r['input_condition']):r for r in cap['items']}
 for row in v['items']:
  sid=row['key'].split('|')[0];saved=lookup[(sid,cid,label)]
  if row['input_tokens']!=saved['initial_input_tokens'] or row['request_sha256']!=saved['request_sha256']:raise ValueError('fresh pinned tokenizer differs from saved400-pool capacity evidence')
 results.append({'condition_id':cid,'representation':label,'requests':len(v['items']),'verification_sha256':a.sha(OUTPUT/name/'verification.json'),'initial_token_counts_match_saved400_evidence':True})
 print(name,'verified',len(v['items']),flush=True)
a.put(OUTPUT/'completion.json',{'combinations':results,'initial_requests_verified':1600,'answering_calls':0,'weights_loaded':False,'gpu_execution':False});a.put(OUTPUT/'file-manifest.json',{'files':a.files(OUTPUT),'excludes_self':True})
