"""Pinned public runtime startup only: no requests, decoding or scientific stages."""
import argparse
import hashlib
import importlib.metadata
import os
from pathlib import Path
import sys
import time
try:
    from .execution_readiness import read,put,sha,digest
    from .development_execution import resolved_condition,device_binding_valid
    from .execution_support import MemoryMonitor
except ImportError:
    from execution_readiness import read,put,sha,digest
    from development_execution import resolved_condition,device_binding_valid
    sys.path.insert(0,str(Path(__file__).parent.parent/'workers'))
    from execution_support import MemoryMonitor


def startup(package,bindings,qualification,ticket,output):
    started=time.monotonic();output=Path(output);output.mkdir(parents=True,exist_ok=False)
    if ticket['scope']!='development_rehearsal' or ticket['purpose']!='startup_only_no_answering' or ticket['stage_keys'] or ticket['answering_call_ceiling']!=0:raise ValueError('startup-only bounded reservation required')
    if ticket['provenance']['probe_sha256']!=sha(__file__) or ticket['provenance']['qualification_sha256']!=digest(qualification):raise ValueError('startup code/qualification identity')
    if not device_binding_valid(bindings,qualification):raise ValueError('fresh verified device binding required')
    os.environ.update(bindings['environment']);os.environ['CUDA_VISIBLE_DEVICES']=bindings['cuda_visible_devices'];os.environ['HF_HUB_OFFLINE']='1';os.environ['TRANSFORMERS_OFFLINE']='1';os.environ['VLLM_NO_USAGE_STATS']='1'
    monitor=MemoryMonitor(bindings['nvidia_smi'],bindings['device_uuid'],.5);monitor.start();state='failed';error=None;metadata={};loaded=False
    try:
        condition=resolved_condition(package,ticket['condition_id'],bindings)
        if condition['backend']!='vllm':raise ValueError('this diagnostic covers the AWQ vLLM startup blocker only')
        if digest(condition)!=qualification['resolved_condition_sha256']:raise ValueError('resolved configuration changed')
        import torch
        versions={k:importlib.metadata.version(k) for k in condition['runtime_versions']}
        if versions!=condition['runtime_versions'] or not torch.cuda.is_available():raise ValueError('runtime/GPU mismatch')
        actual_uuid='GPU-'+str(torch.cuda.get_device_properties(0).uuid).removeprefix('GPU-')
        if actual_uuid!=bindings['device_uuid'] or torch.cuda.get_device_name(0)!=qualification['hardware_runtime']['gpu_name']:raise ValueError('selected CUDA device mismatch')
        from transformers import AutoTokenizer
        snapshot=Path(condition['snapshot_path']);s=condition['settings']
        tokenizer=AutoTokenizer.from_pretrained(snapshot,local_files_only=True,trust_remote_code=False)
        if digest(tokenizer.chat_template)!=condition['template_sha256']:raise ValueError('template digest mismatch')
        from vllm import LLM
        loading=time.monotonic()
        model=LLM(model=str(snapshot),tokenizer=str(snapshot),dtype=s['precision'],max_model_len=s['max_input_and_output'],gpu_memory_utilization=.89,
                  trust_remote_code=False,seed=s['seed'],enforce_eager=True,enable_prefix_caching=False,max_num_seqs=1,**condition.get('backend_options',{}))
        loaded=True;state='complete';metadata={'model_loading_seconds':time.monotonic()-loading,'actual_device_uuid':actual_uuid,
          'gpu_name':torch.cuda.get_device_name(0),'runtime_versions':versions,'artifact_revision':condition['artifact_revision'],'template_sha256':condition['template_sha256'],
          'quantization':s['quantization'],'precision':s['precision'],'model_constructor':'identical LLM call to the sealed AWQ worker; no generate/add_request/step invoked'}
    except BaseException as exc:
        state='interrupted' if isinstance(exc,KeyboardInterrupt) else 'failed';error=type(exc).__name__+': '+str(exc)
    finally:
        monitor.close();put(output/'startup-result.json',{'scope':'development_rehearsal','purpose':'startup_only_no_answering','process_reservation':ticket['id'],
          'state':state,'error':error,'weights_loaded':loaded,'answering_calls':0,'scientific_stage_keys':[],'elapsed_seconds_at_receipt':time.monotonic()-started,
          'device_memory':monitor.report(started),'metadata':metadata,'probe_sha256':sha(__file__),'qualification_sha256':digest(qualification)})
    print('Startup-only result:',state,'weights_loaded:',loaded,'answering_calls: 0',flush=True)

if __name__=='__main__':
    p=argparse.ArgumentParser()
    for flag in ('package','bindings','qualification','ticket','output'):p.add_argument('--'+flag,required=True)
    a=p.parse_args();startup(a.package,read(a.bindings),read(a.qualification),read(a.ticket),a.output)
