"""Offline runtime/artifact/tokenizer qualification; never loads answering weights.

Run with the pinned condition interpreter on the executor. This receipt allows
development task evidence collection, never main execution or a task-qualified claim.
"""
import argparse
import importlib.metadata
import os
import platform
from pathlib import Path
import subprocess
import time
try:
    from .execution_adapter import read,put,sha,digest,canonical
    from .supplemental_execution import resolved_condition
except ImportError:
    from execution_adapter import read,put,sha,digest,canonical
    from supplemental_execution import resolved_condition


def qualify(package,cid,label,bindings,executor,output):
    started=time.monotonic();package=Path(package);output=Path(output);output.mkdir(parents=True,exist_ok=False)
    os.environ.update(bindings['environment']);os.environ['CUDA_VISIBLE_DEVICES']=bindings['cuda_visible_devices']
    os.environ['HF_HUB_OFFLINE']='1';os.environ['TRANSFORMERS_OFFLINE']='1'
    spec=read(package/'execution-spec.json');pin=spec['conditions'][cid]
    condition=resolved_condition(package,cid,bindings)
    import torch
    if not torch.cuda.is_available():raise RuntimeError('CUDA unavailable; no CPU fallback')
    versions={k:importlib.metadata.version(k) for k in condition['runtime_versions']}
    if versions!=condition['runtime_versions']:raise RuntimeError('backend revision mismatch')
    query=subprocess.run([bindings['nvidia_smi'],'-i',bindings['device_uuid'],'--query-gpu=name,uuid,memory.total,driver_version,index','--format=csv,noheader,nounits'],capture_output=True,text=True,timeout=5,check=True)
    name,device,memory,driver,index=[x.strip() for x in query.stdout.strip().split(',')]
    if device!=bindings['device_uuid'] or torch.cuda.get_device_name(0)!=name:raise RuntimeError('device identity mismatch')
    actual_uuid='GPU-'+str(torch.cuda.get_device_properties(0).uuid).removeprefix('GPU-')
    if actual_uuid!=device or bindings['cuda_visible_devices'] not in (device,index):raise RuntimeError('CUDA selected UUID mismatch')
    device_proof={'status':'passed','physical_index':int(index),'device_uuid':device,'torch_device_uuid':actual_uuid,'cuda_visible_devices':bindings['cuda_visible_devices']}
    backend_config={'status':'passed','kind':'not_applicable_transformers'}
    if condition['backend']=='vllm':
        if bindings['cuda_visible_devices']!=index:raise RuntimeError('pinned vLLM requires verified physical numeric CUDA visibility')
        from vllm.engine.arg_utils import EngineArgs
        config=EngineArgs(model=condition['snapshot_path'],tokenizer=condition['snapshot_path'],dtype=condition['settings']['precision'],
            max_model_len=condition['settings']['max_input_and_output'],gpu_memory_utilization=.89,trust_remote_code=False,seed=condition['settings']['seed'],
            enforce_eager=True,enable_prefix_caching=False,max_num_seqs=1,**condition.get('backend_options',{})).create_engine_config()
        backend_config={'status':'passed','kind':'ModelConfig construction only; no model weights or answering','config_repr':str(config)}
    put(output/'device-backend-preflight.json',{'device_binding':device_proof,'backend_config_verification':backend_config})
    from transformers import AutoTokenizer
    tok=AutoTokenizer.from_pretrained(condition['snapshot_path'],local_files_only=True,trust_remote_code=False)
    if digest(tok.chat_template)!=condition['template_sha256']:raise RuntimeError('template digest mismatch')
    rendered=[]
    for key,r in spec['requests'].items():
        if key.split('|')[1:3]!=[cid,label]:continue
        q=read(package/r['path']);settings=condition['settings']
        kw={'enable_thinking':settings['enable_thinking']} if settings.get('enable_thinking') is not None else {}
        text=tok.apply_chat_template(q['messages'],tokenize=False,add_generation_prompt=True,**kw)
        ids=tok(text,add_special_tokens=False)['input_ids']
        rendered.append({'stage_key':key,'request_sha256':sha(package/r['path']),'prompt':text,'token_ids':ids,
            'context_fits':len(ids)+settings['max_new_tokens']<=settings['max_input_and_output'],
            'input_tokens':len(ids),'allowance':settings['max_new_tokens'],'context_limit':settings['max_input_and_output']})
    if len(rendered)!=5:raise ValueError('five frozen development renders required')
    put(output/'render-verification.json',{'status':'passed','method':'exact worker chat-template/tokenizer calls; no generation','items':rendered})
    gen=read(Path(condition['snapshot_path'])/'generation_config.json')
    put(output/'stop-metadata.json',{'status':'passed','verification_kind':'offline_metadata_only','generation_config':gen,
        'worker_sha256':sha(package/pin['worker']),'runtime_versions':versions,
        'limitation':'Live stop behavior and actual task evidence are collected by rehearsal; metadata is not task qualification.'})
    hw={'gpu_name':name,'device_uuid':device,'vram_mib':int(memory),'driver':driver,'os':platform.platform(),'wsl':platform.release(),
        'cuda_runtime':torch.version.cuda,'backend_versions':versions,'gpu_capability':list(torch.cuda.get_device_capability(0))}
    models={name:v['sha256'] for name,v in condition['weight_files'].items()}
    receipt={'status':'runtime_qualified','execution_scope':'development_rehearsal','executor_id':executor,'condition_id':cid,'representation':label,
        'target_main_package_sha256':spec['main_package_sha256'],'package_sha256':sha(package/'package-manifest.json'),'worker_sha256':pin['worker_sha256'],'support_sha256':sha(package/'workers/execution_support.py'),
        'scientific_condition_sha256':pin['sha256'],'bindings_sha256':digest(bindings),'resolved_condition_sha256':digest(condition),
        'hardware_runtime':hw,'model_files':models,'tokenizer_files':{'template_sha256':condition['template_sha256']},
        'device_binding':device_proof,'backend_config_verification':{'status':'passed','evidence_sha256':sha(output/'device-backend-preflight.json'),'kind':backend_config['kind']},
        'quantization':condition['settings']['quantization'],'precision':condition['settings']['precision'],
        'render_verification':{'status':'passed','evidence_sha256':sha(output/'render-verification.json')},
        'stop_verification':{'status':'passed','evidence_sha256':sha(output/'stop-metadata.json'),'kind':'offline_metadata_only'},
        'task_rehearsal':{'status':'not_yet_collected'},'metadata_verification_seconds':time.monotonic()-started}
    put(output/'qualification.json',receipt);put(output/'manifest.json',{'files':{p.name:sha(p) for p in output.iterdir() if p.is_file()},'answering_weights_loaded':False,'answering_calls':0})
    return receipt


if __name__=='__main__':
    p=argparse.ArgumentParser()
    for flag in ('package','condition','representation','bindings','executor','output'):p.add_argument('--'+flag,required=True)
    a=p.parse_args();r=qualify(a.package,a.condition,a.representation,read(a.bindings),a.executor,a.output)
    print(canonical({'qualification_sha256':digest(r),'seconds':r['metadata_verification_seconds'],'status':r['status']}).decode())
