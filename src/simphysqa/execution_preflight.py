"""Metadata-only execution barrier. No weights, generation or private resources.

Fresh executor attestation precedes a central scientific reservation. The launcher
rechecks physical visibility again. This is runtime evidence, not task qualification.
"""
import argparse,json,os,subprocess,time,uuid
from pathlib import Path
try:
    from .execution_readiness import read,put,digest,sha
except ImportError:
    from execution_readiness import read,put,digest,sha

def live_device_check(bindings):
    result=subprocess.run([bindings['nvidia_smi'],'--query-gpu=index,uuid','--format=csv,noheader,nounits'],capture_output=True,text=True,check=True,timeout=5)
    mapping={i.strip():u.strip() for line in result.stdout.strip().splitlines() for i,u in [line.split(',')]}
    visible=bindings['cuda_visible_devices'];device=bindings['device_uuid']
    if visible not in (device,*mapping) or (visible!=device and mapping.get(visible)!=device) or device not in mapping.values():
        raise ValueError('physical index/UUID mapping changed')
    return mapping

def verify_preflight(proof,qualification,check_fresh=True):
    if not isinstance(proof,dict) or proof.get('status')!='passed':raise ValueError('fresh execution preflight required before reservation')
    for field in ('bindings_sha256','resolved_condition_sha256','worker_sha256','support_sha256','scientific_condition_sha256'):
        if proof.get(field)!=qualification.get(field):raise ValueError('preflight identity mismatch: '+field)
    if proof.get('qualification_sha256')!=digest(qualification):raise ValueError('preflight qualification identity')
    if proof.get('hardware_runtime_sha256')!=digest(qualification['hardware_runtime']):raise ValueError('preflight hardware identity')
    if check_fresh and not 0<=time.time()-proof.get('verified_unix_seconds',0)<=300:raise ValueError('stale pre-reservation preflight')
    p=proof.get('device_binding',{});q=qualification.get('device_binding',{})
    if p.get('status')!='passed' or p.get('device_uuid')!=qualification['hardware_runtime']['device_uuid'] or ('torch' in qualification['hardware_runtime']['backend_versions'] and p.get('torch_device_uuid')!=p.get('device_uuid')):raise ValueError('preflight physical GPU mismatch')
    if 'vllm' in qualification['hardware_runtime']['backend_versions'] and (p.get('physical_index')!=q.get('physical_index') or proof.get('backend_config_verification',{}).get('status')!='passed'):
        raise ValueError('exact vLLM ModelConfig preflight required')

def preflight(package,bindings,qualification):
    started=time.monotonic()
    try:
        from .execution_adapter import resolved_condition
    except ImportError:
        from execution_adapter import resolved_condition
    os.environ.update(bindings['environment']);os.environ['CUDA_VISIBLE_DEVICES']=bindings['cuda_visible_devices']
    os.environ['HF_HUB_OFFLINE']='1';os.environ['TRANSFORMERS_OFFLINE']='1'
    mapping=live_device_check(bindings)
    cid=qualification['condition_id'];c=resolved_condition(package,cid,bindings,verify_artifacts=False)
    backend={'status':'passed','kind':'not_applicable_transformers_or_gguf'}
    if 'weight_files' in c:
        import torch,importlib.metadata
        versions={k:importlib.metadata.version(k) for k in c['runtime_versions']}
        if versions!=qualification['hardware_runtime']['backend_versions'] or not torch.cuda.is_available():raise ValueError('qualified CUDA/runtime unavailable')
        selected='GPU-'+str(torch.cuda.get_device_properties(0).uuid).removeprefix('GPU-');torch_uuid=selected
        if selected!=bindings['device_uuid']:raise ValueError('Torch selected GPU identity mismatch')
        if c['backend']=='vllm':
            if mapping.get(bindings['cuda_visible_devices'])!=selected:raise ValueError('vLLM requires verified physical numeric visibility')
            from vllm.engine.arg_utils import EngineArgs
            config=EngineArgs(model=c['snapshot_path'],tokenizer=c['snapshot_path'],dtype=c['settings']['precision'],max_model_len=c['settings']['max_input_and_output'],gpu_memory_utilization=.89,trust_remote_code=False,seed=c['settings']['seed'],enforce_eager=True,enable_prefix_caching=False,max_num_seqs=1,**c.get('backend_options',{})).create_engine_config()
            backend={'status':'passed','kind':'exact EngineArgs/ModelConfig; no model weights or generation','config_repr':str(config)}
    else:
        # GGUF identity is confirmed by its independently qualified CUDA device;
        # no server launch is performed by this metadata-only barrier.
        selected=bindings['device_uuid'];torch_uuid=None
        if not bindings.get('llama_device'):raise ValueError('qualified llama device missing')
    index=next(int(i) for i,u in mapping.items() if u==selected)
    proof={k:qualification[k] for k in ('bindings_sha256','resolved_condition_sha256','worker_sha256','support_sha256','scientific_condition_sha256')}
    proof.update(status='passed',qualification_sha256=digest(qualification),hardware_runtime_sha256=digest(qualification['hardware_runtime']),verified_unix_seconds=time.time(),attestation_id=str(uuid.uuid4()),device_binding={'status':'passed','physical_index':index,'device_uuid':selected,'torch_device_uuid':torch_uuid,'gpu_identity_source':'nvidia-smi plus Torch CUDA UUID' if torch_uuid else 'nvidia-smi only; Torch unavailable/not applicable'},backend_config_verification=backend,elapsed_seconds=time.monotonic()-started,answering_calls=0,weights_loaded=False)
    verify_preflight(proof,qualification);return proof

if __name__=='__main__':
    p=argparse.ArgumentParser()
    for name in ('package','bindings','qualification','output'):p.add_argument('--'+name,required=True)
    a=p.parse_args();put(a.output,preflight(a.package,read(a.bindings),read(a.qualification)))
    print(json.dumps({'status':'passed','weights_loaded':False,'answering_calls':0}))
