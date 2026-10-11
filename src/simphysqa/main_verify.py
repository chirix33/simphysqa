"""Public tokenizer-only verification of actual main return evidence /1.0.0."""
import argparse, os, sys
from pathlib import Path

def verify(a):
    sys.path.insert(0,str(Path(a.package)/'procedures'))
    from execution_adapter import read,put,sha,digest
    from transformers import AutoTokenizer
    os.environ['HF_HUB_OFFLINE']='1';os.environ['TRANSFORMERS_OFFLINE']='1'
    job=Path(a.job);condition=read(job/'condition.json');settings=condition['settings']
    tokenizer=AutoTokenizer.from_pretrained(condition['snapshot_path'],local_files_only=True,trust_remote_code=False)
    assert digest(tokenizer.chat_template)==condition['template_sha256']
    before=read(a.preflight)['items'];checks=[]
    for file in sorted((job/'worker-output/results').glob('*.json')):
        raw=read(file);qfile=job/'worker-output/executed-requests'/file.name;q=read(qfile)
        kw={'enable_thinking':settings['enable_thinking']} if settings.get('enable_thinking') is not None else {}
        text=tokenizer.apply_chat_template(q['messages'],tokenize=False,add_generation_prompt=True,**kw)
        ids=tokenizer(text,add_special_tokens=False)['input_ids'];prompt=read(job/'worker-output/tokenized-prompts'/file.name)
        assert prompt=={'prompt':text,'token_ids':ids},raw['stage_key']
        expected=next(item for item in before if item['key']==raw['stage_key'])
        assert expected['prompt']==text and expected['token_ids']==ids
        assert sha(qfile)==raw['request_sha256']
        assert tokenizer.decode(raw['output_token_ids'],skip_special_tokens=True)==raw['raw_output']
        assert raw['total_stage_seconds']>=raw['latency_seconds']>=0
        memory=raw['device_memory'];samples=memory['samples']
        assert memory['successful_sample_count']==len(samples)
        assert memory['sampled_peak_mib']==max((s['used_mib'] for s in samples),default=None)
        assert all(s['device_uuid']==read(job/'execution-context.json')['device_uuid'] for s in samples)
        assert raw['cpu_fallback'] is False and raw['execution_scope']=='main' and raw['response_origin']=='actual_local_model'
        if raw['stage']==2:
            route=read(job/'routing'/file.name)
            assert q['messages'][-2]=={'role':'assistant','content':route['actual_raw']}
        checks.append({'key':raw['stage_key'],'result_sha256':sha(file),'request_sha256':sha(qfile),'render_output_memory_timing_scope_history_verified':True,'termination':raw['termination']})
    put(a.output,{'version':'SPQ06-main-verification/1.0.0','actual_stages':checks,'weights_loaded':False,'answering_calls':0})
    print('actual evidence verified',len(checks))

if __name__=='__main__':
    p=argparse.ArgumentParser()
    for key in ('package','job','preflight','output'):p.add_argument('--'+key,required=True)
    verify(p.parse_args())
