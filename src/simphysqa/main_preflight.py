"""Fresh public-only main metadata barrier /1.0.0. No model weights or inference.

Wraps the sealed /1.1.1 preflight. Adoption uses reviewed live development
evidence and identity checks, never imports development responses as main data.
"""
import argparse, json, os, platform, subprocess, sys, time
from pathlib import Path

def run(a):
    sys.path.insert(0,str(Path(a.package)/'procedures'))
    import execution_adapter as adapter
    import execution_preflight as preflight
    read,put,digest,sha = adapter.read,adapter.put,adapter.digest,adapter.sha
    started=time.monotonic(); output=Path(a.output); output.mkdir(parents=True,exist_ok=False)
    bindings=read(a.bindings); source=read(a.qualification); mapping=read(a.mapping)
    os.environ.update(bindings['environment']); os.environ['CUDA_VISIBLE_DEVICES']=bindings['cuda_visible_devices']
    os.environ['HF_HUB_OFFLINE']='1'; os.environ['TRANSFORMERS_OFFLINE']='1'
    adapter.validate_package(a.package)
    condition=adapter.resolved_condition(a.package,source['condition_id'],bindings,verify_artifacts=True)
    spec=read(Path(a.package)/'execution-spec.json'); pin=spec['conditions'][source['condition_id']]
    for field,actual in [('worker_sha256',pin['worker_sha256']),('support_sha256',sha(Path(a.package)/'workers/execution_support.py')),
                         ('scientific_condition_sha256',pin['sha256']),('bindings_sha256',digest(bindings)),('resolved_condition_sha256',digest(condition))]:
        if mapping[field]!=actual or source[field]!=actual: raise ValueError('reviewed mapping mismatch: '+field)
    import torch, importlib.metadata
    query=subprocess.run([bindings['nvidia_smi'],'-i',bindings['device_uuid'],'--query-gpu=name,uuid,memory.total,driver_version,index','--format=csv,noheader,nounits'],capture_output=True,text=True,check=True,timeout=5)
    name,device,memory,driver,index=[v.strip() for v in query.stdout.strip().split(',')]
    hw={'gpu_name':name,'device_uuid':device,'vram_mib':int(memory),'driver':driver,'os':platform.platform(),'wsl':platform.release(),
        'cuda_runtime':torch.version.cuda,'backend_versions':{k:importlib.metadata.version(k) for k in condition['runtime_versions']},'gpu_capability':list(torch.cuda.get_device_capability(0))}
    if hw!=source['hardware_runtime'] or digest(hw)!=mapping['hardware_runtime_sha256']: raise ValueError('fresh hardware/runtime differs from mapped task evidence')
    if mapping['model_files']!={name:v['sha256'] for name,v in condition['weight_files'].items()}: raise ValueError('mapped artifact identity')
    from transformers import AutoTokenizer
    tokenizer=AutoTokenizer.from_pretrained(condition['snapshot_path'],local_files_only=True,trust_remote_code=False)
    if digest(tokenizer.chat_template)!=condition['template_sha256']: raise ValueError('template identity')
    rendered=[]; settings=condition['settings']
    for key in read(a.keys):
        entry=spec['requests'].get(key)
        q=read(Path(a.package)/entry['path']) if entry else read(Path(a.routes)/((key.split('|')[0])+'.json'))['request']
        if entry and sha(Path(a.package)/entry['path'])!=entry['sha256']: raise ValueError('initial bytes')
        kwargs={'enable_thinking':settings['enable_thinking']} if settings.get('enable_thinking') is not None else {}
        text=tokenizer.apply_chat_template(q['messages'],tokenize=False,add_generation_prompt=True,**kwargs)
        ids=tokenizer(text,add_special_tokens=False)['input_ids']
        rendered.append({'key':key,'request_sha256':digest(q),'prompt':text,'token_ids':ids,'context_fits':len(ids)+settings['max_new_tokens']<=settings['max_input_and_output']})
    put(output/'render-verification.json',{'items':rendered,'template_sha256':condition['template_sha256'],'weights_loaded':False})
    if a.adopt:
        qualification={**source,'execution_scope':'main','status':'task_qualified','package_sha256':sha(Path(a.package)/'package-manifest.json'),
            'target_main_package_sha256':sha(Path(a.package)/'package-manifest.json'),
            'render_verification':{'status':'passed','evidence_sha256':sha(output/'render-verification.json')},
            'stop_verification':{'status':'passed','evidence_sha256':mapping['verification_file_sha256'],'kind':'reviewed actual development stop evidence; no inferred private reasoning'},
            'task_rehearsal':{'status':'passed','evidence_sha256':digest(mapping),'initial_tasks':5,'live_continuation_tasks':len(mapping['continuation_task_evidence']),'missing_live_stage2':not bool(mapping['continuation_task_evidence'])},
            'qualification_adoption':{'mapping_sha256':sha(a.mapping),'current_metadata_only':True,'development_outputs_are_not_main_results':True}}
    else: qualification=source
    put(output/'qualification.json',qualification)
    proof=preflight.preflight(a.package,bindings,qualification)
    proof.update(full_artifact_verification='all pinned files hashed; symlink targets constrained to cache',template_sha256=condition['template_sha256'],fresh_hardware_runtime=hw,
                 render_verification_sha256=sha(output/'render-verification.json'),wrapper_sha256=sha(__file__),metadata_total_seconds=time.monotonic()-started)
    put(output/'proof.json',proof)
    put(output/'manifest.json',{'files':adapter.files(output),'weights_loaded':False,'answering_calls':0})
    print(json.dumps({'passed':True,'items':len(rendered),'seconds':proof['metadata_total_seconds']}))

if __name__=='__main__':
    p=argparse.ArgumentParser()
    for key in ('package','bindings','qualification','mapping','keys','routes','output'):p.add_argument('--'+key,required=True)
    p.add_argument('--adopt',action='store_true');run(p.parse_args())
