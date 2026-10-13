"""Isolated local GGUF answering worker; public files only, loopback HTTP only."""
import argparse,hashlib,json,os,socket,subprocess,time,threading
from pathlib import Path
from urllib.request import Request,urlopen

def canonical(x):return (json.dumps(x,sort_keys=True,separators=(',',':'),ensure_ascii=False,allow_nan=False)+'\n').encode()
def put(p,x):
    p.parent.mkdir(parents=True,exist_ok=True)
    with p.open('xb') as f:f.write(canonical(x))
def sha(p):
    with Path(p).open('rb') as f:return hashlib.file_digest(f,'sha256').hexdigest()

def main():
    p=argparse.ArgumentParser();p.add_argument('--condition',type=Path,required=True);p.add_argument('--requests',type=Path,required=True);p.add_argument('--output',type=Path,required=True)
    a=p.parse_args();c=json.loads(a.condition.read_bytes());requests=json.loads(a.requests.read_bytes());s=c['settings']
    if any(q['tools']!=[] or q['condition_id']!=c['condition_id'] for q in requests):raise ValueError('public tool-free boundary')
    if sha(__file__)!=c['worker_sha256'] or sha(c['gguf_path'])!=c['gguf_sha256']:raise ValueError('worker/model hash mismatch')
    server=Path(c['server_path'])
    if sha(server)!=c['server_sha256']:raise ValueError('runtime hash mismatch')
    env={**os.environ,'LD_LIBRARY_PATH':':'.join(c['library_paths'])}
    endpoint='http://127.0.0.1:18086'
    devices=subprocess.run([str(server),'--list-devices'],env=env,capture_output=True,text=True,timeout=30)
    if devices.returncode or 'CUDA0' not in devices.stdout or 'NVIDIA GeForce RTX 5090' not in devices.stdout:raise RuntimeError('required pinned workstation CUDA0 unavailable; CPU fallback forbidden')
    put(a.output/'cuda-device-preflight.json',{'stdout':devices.stdout,'stderr':devices.stderr,'returncode':devices.returncode})
    def call(path,body=None,timeout=10):
        req=Request(endpoint+path,data=canonical(body) if body is not None else None,headers={'Content-Type':'application/json'})
        with urlopen(req,timeout=timeout) as response:return json.load(response)
    peak=[0];stop=threading.Event()
    def monitor():
        while not stop.is_set():
            try:
                result=subprocess.run(['/usr/lib/wsl/lib/nvidia-smi','--query-gpu=memory.used','--format=csv,noheader,nounits'],capture_output=True,text=True,timeout=3)
                peak[0]=max(peak[0],int(result.stdout.strip()))
            except Exception:pass
            stop.wait(.5)
    threading.Thread(target=monitor,daemon=True).start()
    args=[str(server),'-m',c['gguf_path'],'--host','127.0.0.1','--port','18086','-c',str(s['max_input_and_output']),
        '-ngl','all','--device','CUDA0','--fit','off','-np','1','-fa','on','--no-context-shift','--no-warmup','--jinja','--no-webui',
        '--cache-type-k','f16','--cache-type-v','f16','--threads','8','--threads-batch','8']
    put(a.output/'server-launch.json',{'args':args,'worker_sha256':sha(__file__),'condition_sha256':sha(a.condition),'requests_sha256':sha(a.requests),'tools':[]})
    started=time.monotonic();a.output.mkdir(parents=True,exist_ok=True)
    log=(a.output/'server.log').open('xb');proc=subprocess.Popen(args,env=env,stdout=log,stderr=subprocess.STDOUT)
    try:
        while True:
            if proc.poll() is not None:raise RuntimeError('pinned local server failed to load; inspect saved log')
            try:
                health=call('/health')
                if health.get('status')=='ok':break
            except Exception:pass
            if time.monotonic()-started>=600:raise TimeoutError('600-second model loading ceiling')
            time.sleep(.5)
        props=call('/props');put(a.output/'server-properties.json',props)
        template=props.get('chat_template')
        if hashlib.sha256(canonical(template)).hexdigest()!=c['template_sha256']:raise ValueError('GGUF runtime chat template changed')
        put(a.output/'runtime.json',{'load_seconds':time.monotonic()-started,'worker_sha256':sha(__file__),'model_id':c['model_id'],
            'artifact_revision':c['artifact_revision'],'runtime_revision':c['runtime_revision'],'peak_loading_device_memory_mib':peak[0],
            'tools':[],'hosted_answering_calls':0})
        for q in requests:
            sid=q['sample_id'];stage=q.get('stage',1);stem=sid+'-stage'+str(stage);reservation=a.output/'reservations'/(stem+'.json')
            if reservation.exists():continue
            prompt=call('/apply-template',{'messages':q['messages']})['prompt']
            ids=call('/tokenize',{'content':prompt,'add_special':False,'parse_special':True})['tokens']
            body={'prompt':ids,'stream':True,'return_tokens':True,'n_predict':s['max_new_tokens'],'seed':s['seed'],
                'temperature':s['temperature'],'top_p':s['top_p'],'top_k':s['top_k'],'min_p':0,'typical_p':1,
                'repeat_penalty':1,'presence_penalty':0,'frequency_penalty':0,'cache_prompt':False,
                'samplers':['top_k','top_p','temperature'],'t_max_predict_ms':int(s['max_seconds']*1000)}
            put(reservation,{'sample_id':sid,'stage':stage,'condition_id':c['condition_id'],'request_sha256':hashlib.sha256(canonical(q)).hexdigest(),
                'prompt_tokens':len(ids),'max_output_tokens':s['max_new_tokens'],'maximum_seconds':s['max_seconds'],'attempt':1,'reserved_unix_seconds':time.time()})
            put(a.output/'executed-requests'/(stem+'.json'),q);put(a.output/'executed-http-requests'/(stem+'.json'),body)
            put(a.output/'tokenized-prompts'/(stem+'.json'),{'prompt':prompt,'token_ids':ids})
            begun=time.monotonic();timer=None;peak[0]=0;events=[];raw='';output=[];status='completed';reason=None
            try:
                if len(ids)+s['max_new_tokens']>s['max_input_and_output']:raise ValueError('context_capacity_exceeded_no_truncation')
                with urlopen(Request(endpoint+'/completion',data=canonical(body),headers={'Content-Type':'application/json'}),timeout=s['max_seconds']) as response:
                    deadline_socket=response.fp.raw._sock
                    remaining=max(.001,s['max_seconds']-(time.monotonic()-begun))
                    def shutdown_at_deadline():
                        try:deadline_socket.shutdown(socket.SHUT_RDWR)
                        except OSError:pass
                    timer=threading.Timer(remaining,shutdown_at_deadline);timer.daemon=True;timer.start()
                    for line in response:
                        if time.monotonic()-begun>=s['max_seconds']:raise TimeoutError('per-request wall ceiling')
                        if not line.startswith(b'data: '):continue
                        event=json.loads(line[6:]);events.append(event);raw+=event.get('content','');output.extend(event.get('tokens',[]))
                        if event.get('stop'):
                            if event.get('truncated'):status='failed';reason='unexpected_context_truncation'
                            elif event.get('stop_type')=='limit':status='length_limited';reason=status
                            break
                if not events or not events[-1].get('stop'):
                    status='timeout' if time.monotonic()-begun>=s['max_seconds'] else 'failed';reason=status if status=='timeout' else 'incomplete_stream'
            except (TimeoutError,socket.timeout):status='timeout';reason='per-request wall ceiling'
            except Exception as exc:status='failed';reason=type(exc).__name__+': '+str(exc)[:220]
            if timer is not None:timer.cancel()
            value={'sample_id':sid,'condition_id':c['condition_id'],'stage':stage,'completion_status':status,'failure_reason':reason,
                'raw_output':raw,'output_token_ids':output,'raw_stream_events':events,'input_tokens':len(ids),'output_tokens':len(output),
                'latency_seconds':time.monotonic()-begun,'peak_device_memory_mib':peak[0],'response_origin':'actual_local_model',
                'request_sha256':hashlib.sha256(canonical(q)).hexdigest(),'model_id':c['model_id'],'artifact_revision':c['artifact_revision'],
                'template_sha256':c['template_sha256'],'reasoning_format_diagnostics':{'contains_think_open':'<think>' in raw,'explicit_think_closure':'</think>' in raw}}
            put(a.output/'results'/(stem+'.json'),value);print(json.dumps({k:value[k] for k in ('condition_id','sample_id','stage','completion_status','input_tokens','output_tokens','latency_seconds')}),flush=True)
        put(a.output/'completed.json',{'returned_results':len(list((a.output/'results').glob('*.json')))})
    finally:
        stop.set();proc.terminate()
        try:proc.wait(timeout=10)
        except subprocess.TimeoutExpired:proc.kill();proc.wait()
        log.close()

if __name__=='__main__':main()
