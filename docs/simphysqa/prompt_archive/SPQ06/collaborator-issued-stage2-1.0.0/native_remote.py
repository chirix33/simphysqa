"""Public metadata-first runner for two genuinely issued prospective stage-2 jobs.

Uses only public issued inputs and frozen answering workers. No organizer database,
private record, scoring, first-turn retry or model-setting override is available.
"""
import argparse
import ast
import hashlib
import importlib.metadata
import json
import math
import os
import platform
import signal
import subprocess
import sys
import time
import zipfile
from datetime import datetime, timezone
from pathlib import Path

VERSION = 'SPQ06-native-reconciliation/1.0.0'


def canonical(v):
    return (json.dumps(v, sort_keys=True, separators=(',', ':'), ensure_ascii=False, allow_nan=False) + '\n').encode()


def digest(v): return hashlib.sha256(canonical(v)).hexdigest()
def read(p): return json.loads(Path(p).read_bytes())


def sha(p):
    with Path(p).open('rb') as stream: return hashlib.file_digest(stream, 'sha256').hexdigest()


def put(p, v):
    p = Path(p); p.parent.mkdir(parents=True, exist_ok=True)
    with p.open('xb') as stream: stream.write(canonical(v))


def within(root, rel):
    root = Path(root).resolve(); target = (root / rel).resolve()
    if Path(rel).is_absolute() or '..' in Path(rel).parts or root not in target.parents:
        raise ValueError('unsafe issued relative path')
    return target


def validate_bundle(root):
    manifest = read(root / 'manifest.json')
    for name, expected in manifest['files'].items():
        if sha(within(root, name)) != expected: raise ValueError('issued public bundle changed: ' + name)
    return manifest


def validate_proof(job, proof, when=None):
    """Pure validation used independently by the central importer and remote runner."""
    when = time.time() if when is None else when
    c, issue = job['condition'], job['issue']
    q = proof.get('qualification', {})
    if proof.get('status') != 'passed' or proof.get('answering_calls') != 0 or proof.get('weights_loaded') is not False:
        raise ValueError('real metadata-only proof required')
    if not 0 <= when - proof.get('verified_unix_seconds', 0) <= 300:
        raise ValueError('fresh metadata proof required within 300 seconds before activation')
    for field, expected in (('request_sha256', issue['request_sha256']), ('job_sha256', digest(job)),
                            ('remote_executor_sha256', issue['remote_executor_sha256']),
                            ('condition_sha256', digest(c)), ('bindings_sha256', digest(job['bindings']))):
        if proof.get(field) != expected: raise ValueError('metadata identity mismatch: ' + field)
    if q.get('status') != 'task_qualified' or q.get('worker_sha256') != job['worker_sha256'] or q.get('scientific_condition_sha256') != job['scientific_condition_sha256'] or q.get('support_sha256') != job['support_sha256']:
        raise ValueError('fresh task-adoption worker/condition/support mismatch')
    if q.get('hardware_runtime') != job['hardware_runtime'] or q.get('resolved_condition_sha256') != digest(c) or q.get('bindings_sha256') != digest(job['bindings']):
        raise ValueError('fresh hardware/binding/condition mismatch')
    if q.get('quantization') != c['settings']['quantization'] or q.get('precision') != c['settings']['precision']:
        raise ValueError('scientific precision/quantization changed')
    if q.get('tokenizer_files', {}).get('template_sha256') != c['template_sha256']:
        raise ValueError('fresh tokenizer template mismatch')
    expected_files = {n: info['sha256'] for n, info in c['weight_files'].items()} if 'weight_files' in c else {'gguf': c['gguf_sha256'], 'server': c['server_sha256']}
    if q.get('model_files') != expected_files:
        raise ValueError('fresh actual artifact digest mismatch')
    if q.get('task_rehearsal') != job['reviewed_task_evidence'] or q.get('stop_verification') != job['reviewed_stop_evidence']:
        raise ValueError('reviewed original native task/stop evidence changed')
    if q.get('executor_id') != 'Collaborator' or q.get('condition_id') != c['condition_id'] or q.get('representation') != 'enriched' or q.get('execution_scope') != 'main' or q.get('package_sha256') != issue['assignment']['package_sha256']:
        raise ValueError('prospective qualification scope changed')
    device = proof.get('device_binding', {})
    if device.get('status') != 'passed' or device.get('device_uuid') != job['hardware_runtime']['device_uuid'] or str(device.get('physical_index')) != job['bindings']['cuda_visible_devices']:
        raise ValueError('fresh physical device mapping mismatch')
    if c['backend'] == 'vllm':
        if device.get('torch_device_uuid') != device['device_uuid'] or proof.get('backend_config_verification', {}).get('status') != 'passed' or proof['backend_config_verification'].get('gpu_memory_utilization') != .93:
            raise ValueError('exact frozen DeepSeek device/ModelConfig proof required')
    elif proof.get('gguf_device_verification', {}).get('status') != 'passed':
        raise ValueError('fresh pinned GGUF device/backend proof required')
    rendered = proof.get('stage2_render', {})
    ids = rendered.get('token_ids')
    if not isinstance(rendered.get('prompt'), str) or not isinstance(ids, list) or any(type(n) is not int or n < 0 for n in ids):
        raise ValueError('fresh actual-history render evidence required')
    if len(ids) + c['settings']['max_new_tokens'] > c['settings']['max_input_and_output']:
        raise ValueError('actual dialogue overflow; no truncation')
    if job['request']['messages'][-2] != {'role': 'assistant', 'content': job['actual_first_response']} or digest(job['request']) != issue['request_sha256']:
        raise ValueError('verbatim actual-history request mismatch')
    return True


def execution_context(job, qual):
    issue, c = job['issue'], job['condition']
    return {'version': 'SPQ06-execution/1.0.0', 'execution_scope': 'main', 'qualification_status': 'task_qualified',
            'worker_sha256': job['worker_sha256'], 'resolved_condition_sha256': digest(c),
            'scientific_condition_sha256': job['scientific_condition_sha256'], 'qualification_sha256': digest(qual),
            'assignment_sha256': digest(issue['assignment']), 'adapter_sha256': issue['remote_executor_sha256'],
            'hardware_runtime_sha256': digest(job['hardware_runtime']), 'hardware_runtime': job['hardware_runtime'],
            'gpu_name': job['hardware_runtime']['gpu_name'], 'device_uuid': job['hardware_runtime']['device_uuid'],
            'llama_device': job['bindings'].get('llama_device'), 'nvidia_smi': job['bindings']['nvidia_smi'],
            'memory_interval_seconds': .5, 'representation': 'enriched', 'process_reservation': issue['process'],
            'stage_reservations': {issue['key']: issue['process'] + ':' + issue['key']}}


def perform_preflight(root, job):
    """No LLM/server loading. Hash pinned artifacts; tokenize actual full history."""
    started = time.monotonic(); c, bindings = job['condition'], job['bindings']
    if sys.executable != bindings['interpreter'] and Path(sys.executable).resolve() != Path(bindings['interpreter']).resolve():
        raise ValueError('use the original condition-specific pinned interpreter')
    os.environ.update(bindings['environment']); os.environ['CUDA_VISIBLE_DEVICES'] = bindings['cuda_visible_devices']
    os.environ['HF_HUB_OFFLINE'] = '1'; os.environ['TRANSFORMERS_OFFLINE'] = '1'; os.environ['VLLM_NO_USAGE_STATS'] = '1'
    package = root / 'execution-public-1.1.1'
    if sha(package / 'package-manifest.json') != job['issue']['assignment']['package_sha256']:
        raise ValueError('sealed base package changed')
    for file, expected in ((job['worker_relative'], job['worker_sha256']), ('workers/execution_support.py', job['support_sha256'])):
        if sha(package / file) != expected: raise ValueError('frozen worker/support changed')
    query = subprocess.run([bindings['nvidia_smi'], '-i', bindings['device_uuid'], '--query-gpu=index,uuid,name,memory.total,driver_version', '--format=csv,noheader,nounits'], capture_output=True, text=True, check=True, timeout=10)
    index, uid, name, memory, driver = [v.strip() for v in query.stdout.strip().split(',')]
    hw = job['hardware_runtime']
    if (index, uid, name, int(memory), driver) != (bindings['cuda_visible_devices'], hw['device_uuid'], hw['gpu_name'], hw['vram_mib'], hw['driver']) or platform.platform() != hw['os']:
        raise ValueError('fresh hardware/driver/OS differs; no automatic substitution')
    proof = {'status': 'passed', 'answering_calls': 0, 'weights_loaded': False, 'request_sha256': job['issue']['request_sha256'],
             'job_sha256': digest(job), 'remote_executor_sha256': sha(__file__), 'condition_sha256': digest(c),
             'bindings_sha256': digest(bindings), 'device_binding': {'status': 'passed', 'physical_index': int(index), 'device_uuid': uid}}
    initial = job['render_example']
    if 'weight_files' in c:
        cache = Path(bindings['artifact_cache']).resolve(); snapshot = Path(c['snapshot_path'])
        for file, info in c['weight_files'].items():
            target = (snapshot / file).resolve()
            if cache not in target.parents or sha(target) != info['sha256']:
                raise ValueError('pinned artifact/symlink cache mismatch: ' + file)
        import torch
        if not torch.cuda.is_available() or torch.version.cuda != hw['cuda_runtime']:
            raise ValueError('qualified CUDA unavailable')
        versions = {k: importlib.metadata.version(k) for k in c['runtime_versions']}
        if versions != hw['backend_versions']:
            raise ValueError('pinned backend/runtime versions changed')
        torch_uid = 'GPU-' + str(torch.cuda.get_device_properties(0).uuid).removeprefix('GPU-')
        if torch_uid != uid: raise ValueError('Torch/physical CUDA index-to-UUID differs')
        proof['device_binding']['torch_device_uuid'] = torch_uid
        from vllm.engine.arg_utils import EngineArgs
        config = EngineArgs(model=c['snapshot_path'], tokenizer=c['snapshot_path'], dtype='bfloat16', max_model_len=c['settings']['max_input_and_output'],
                            gpu_memory_utilization=.93, trust_remote_code=False, seed=c['settings']['seed'], enforce_eager=True,
                            enable_prefix_caching=False, max_num_seqs=1, **c.get('backend_options', {})).create_engine_config()
        proof['backend_config_verification'] = {'status': 'passed', 'gpu_memory_utilization': .93, 'config_repr': str(config),
                                                 'kind': 'exact frozen DeepSeek EngineArgs/ModelConfig; no LLM instance or weights loaded'}
        from transformers import AutoTokenizer
        tokenizer = AutoTokenizer.from_pretrained(snapshot, local_files_only=True, trust_remote_code=False)
        if digest(tokenizer.chat_template) != c['template_sha256']:
            raise ValueError('pinned tokenizer/chat template changed')
        def render(messages):
            text = tokenizer.apply_chat_template(messages, tokenize=False, add_generation_prompt=True)
            return {'prompt': text, 'token_ids': tokenizer(text, add_special_tokens=False)['input_ids']}
        model_files = {n: info['sha256'] for n, info in c['weight_files'].items()}
    else:
        if sha(c['gguf_path']) != c['gguf_sha256'] or sha(c['server_path']) != c['server_sha256']:
            raise ValueError('actual pinned GGUF/server digest changed')
        environment = {**os.environ, 'LD_LIBRARY_PATH': ':'.join(c['library_paths'])}
        devices = subprocess.run([c['server_path'], '--list-devices'], env=environment, capture_output=True, text=True, check=True, timeout=30)
        if bindings['llama_device'] not in devices.stdout or hw['gpu_name'] not in devices.stdout:
            raise ValueError('GGUF CUDA device/backend differs')
        proof['gguf_device_verification'] = {'status': 'passed', 'argv': [c['server_path'], '--list-devices'], 'stdout': devices.stdout,
                                               'binary_sha256': c['server_sha256'], 'kind': 'pinned CUDA binary/device metadata only; no server/model loaded'}
        template = read(root / 'gemma-template.json')
        if digest(template) != c['template_sha256']: raise ValueError('GGUF embedded-template pin mismatch')
        from jinja2 import Environment, StrictUndefined
        env = Environment(undefined=StrictUndefined)
        def fail(message): raise ValueError(message)
        env.globals['raise_exception'] = fail; env.globals['strftime_now'] = lambda fmt: '2026-10-09'
        renderer = env.from_string(template); tool = str(Path(c['server_path']).with_name('llama-tokenize'))
        def render(messages):
            text = renderer.render(messages=messages, add_generation_prompt=True, bos_token='', eos_token='')
            tokens = subprocess.run([tool, '-m', c['gguf_path'], '--stdin', '--ids', '--no-bos', '--no-escape', '--offline'],
                                    input=text, env={**environment, 'CUDA_VISIBLE_DEVICES': ''}, capture_output=True, text=True, check=True, timeout=60)
            return {'prompt': text, 'token_ids': ast.literal_eval(tokens.stdout.strip())}
        model_files = {'gguf': c['gguf_sha256'], 'server': c['server_sha256']}
    if render(initial['request']['messages']) != initial['render']:
        raise ValueError('fresh initial renderer/tokenizer differs from original actual saved evidence')
    proof['stage2_render'] = render(job['request']['messages'])
    q = {'version': VERSION, 'executor_id': 'Collaborator', 'condition_id': c['condition_id'], 'representation': 'enriched',
         'status': 'task_qualified', 'execution_scope': 'main', 'package_sha256': job['issue']['assignment']['package_sha256'],
         'worker_sha256': job['worker_sha256'], 'support_sha256': job['support_sha256'],
         'scientific_condition_sha256': job['scientific_condition_sha256'], 'hardware_runtime': hw,
         'model_files': model_files, 'tokenizer_files': {'template_sha256': c['template_sha256']},
         'quantization': c['settings']['quantization'], 'precision': c['settings']['precision'],
         'bindings_sha256': digest(bindings), 'resolved_condition_sha256': digest(c),
         'render_verification': {'status': 'passed', 'evidence_sha256': digest(proof['stage2_render']), 'actual_history': True},
         'task_rehearsal': job['reviewed_task_evidence'], 'stop_verification': job['reviewed_stop_evidence'],
         'device_binding': proof['device_binding'], 'qualification_authority': 'new central conditional issuance activated by real remote metadata',
         'original_first_turn_authority': 'independent_local_preserved', 'historical_organizer_approval_changed': False}
    proof['qualification'] = q; proof['metadata_elapsed_seconds'] = time.monotonic() - started
    proof['verified_unix_seconds'] = time.time()
    validate_proof(job, proof)
    return proof


def run(root, name):
    import fcntl
    entry_started = time.monotonic()
    root = Path(root).resolve(); validate_bundle(root)
    job_path = within(root, 'jobs/' + name + '/job.json'); job = read(job_path)
    issue, c = job['issue'], job['condition']
    if sha(__file__) != issue['remote_executor_sha256']: raise ValueError('issued executor changed')
    if datetime.now(timezone.utc).timestamp() + issue['bound_seconds'] + 600 >= datetime.fromisoformat(issue['cutoff_utc']).timestamp():
        raise ValueError('job plus export/central-import reserve no longer fits the unchanged cutoff')
    # One device serially across both jobs. Locks are local coordination, never a ledger.
    lock_path = Path(job['device_lock_path'])
    guard_path = Path(job['attempt_guard_path'])
    if not lock_path.is_absolute() or not guard_path.is_absolute():
        raise ValueError('centrally issued fixed workstation attempt/lock paths required')
    lock_path.parent.mkdir(parents=True, exist_ok=True)
    with lock_path.open('a') as lock:
        fcntl.flock(lock.fileno(), fcntl.LOCK_EX | fcntl.LOCK_NB)
        # Fixed host path survives copying/re-extracting the handoff. Never release it.
        put(guard_path, {'attempt': 1, 'process_reservation': issue['process'],
                         'stage_key': issue['key'], 'issued_job_sha256': digest(job), 'unix_seconds': time.time()})
        output = within(root, 'runs/' + name); output.mkdir(parents=True, exist_ok=False)
        put(output / 'job.json', job); put(output / 'route.json', read(job_path.parent / 'route.json'))
        put(output / 'launch-reserved.json', {'attempt': 1, 'process_reservation': issue['process'], 'unix_seconds': time.time(), 'science_stage': 2})
        started = entry_started; proc = None; state = 'failed'; code = None; failure = None
        def expire(signum, frame):
            raise TimeoutError('issued process deadline exhausted')
        previous_alarm = signal.signal(signal.SIGALRM, expire)
        signal.setitimer(signal.ITIMER_REAL, max(.001, issue['bound_seconds'] - (time.monotonic() - started)))
        try:
            with (output / 'metadata.log').open('x') as log:
                import contextlib
                with contextlib.redirect_stdout(log), contextlib.redirect_stderr(log):
                    proof = perform_preflight(root, job)
            put(output / 'metadata-proof.json', proof)
            validate_proof(job, proof)
            if time.monotonic() - started + c['settings']['max_seconds'] >= issue['bound_seconds']:
                raise TimeoutError('metadata exhausted loading/overhead allowance; no answering started')
            qual = proof['qualification']; put(output / 'qualification.json', qual)
            put(output / 'condition.json', c); put(output / 'requests.json', [job['request']]); put(output / 'bindings.json', job['bindings'])
            context = execution_context(job, qual)
            put(output / 'execution-context.json', context)
            put(output / 'activation.json', {'activated_unix_seconds': time.time(), 'remote_executor_sha256': sha(__file__),
                 'metadata_proof_sha256': digest(proof), 'central_issue_process': issue['process'], 'activation_kind': 'prospective_remote_metadata_gate'})
            command = [job['bindings']['interpreter'], '-B', str(root / 'execution-public-1.1.1' / job['worker_relative']),
                       '--condition', str(output / 'condition.json'), '--requests', str(output / 'requests.json'),
                       '--output', str(output / 'worker-output'), '--execution-context', str(output / 'execution-context.json')]
            put(output / 'executed-command.json', {'argv': command, 'environment_overrides': job['bindings']['environment'],
                 'cuda_visible_devices': job['bindings']['cuda_visible_devices'], 'first_turn_rerun': False})
            with (output / 'process.log').open('xb') as log:
                proc = subprocess.Popen(command, stdout=log, stderr=subprocess.STDOUT,
                                        env={**os.environ, **job['bindings']['environment'], 'CUDA_VISIBLE_DEVICES': job['bindings']['cuda_visible_devices']},
                                        start_new_session=True)
                code = proc.wait(timeout=max(.001, issue['bound_seconds'] - (time.monotonic() - started)))
            state = 'complete' if code == 0 else 'failed'
        except (subprocess.TimeoutExpired, TimeoutError) as exc:
            state = 'timed_out'; failure = type(exc).__name__
        except KeyboardInterrupt:
            state = 'interrupted'; failure = 'KeyboardInterrupt'
        except Exception as exc:
            state = 'failed'; failure = type(exc).__name__ + ': ' + str(exc)
        finally:
            signal.setitimer(signal.ITIMER_REAL, 0)
            signal.signal(signal.SIGALRM, previous_alarm)
            if proc is not None and proc.poll() is None:
                os.killpg(proc.pid, signal.SIGKILL); proc.wait(timeout=10)
            put(output / 'process-receipt.json', {'state': state, 'returncode': code, 'failure': failure,
                'elapsed_seconds': time.monotonic() - started, 'process_reservation': issue['process'],
                'inference_started': proc is not None,
                'boundaries': 'entire remote metadata/hashing/rendering, activation, worker/model loading, stage and teardown once; transfer/queue excluded; central preparation charged separately'})
        print(json.dumps({'job': name, 'state': state, 'inference_started': proc is not None, 'return_required': True}))
        return 0 if state == 'complete' else 2


def export(root, name, output):
    root = Path(root).resolve(); validate_bundle(root)
    source = within(root, 'runs/' + name); output = Path(output)
    if source in output.resolve().parents:
        raise ValueError('export ZIP must be outside the original run folder')
    issue = read(source / 'job.json')['issue']; sid, cid, label, stage = issue['key'].split('|')
    stem = sid + '-stage2.json'
    entries = []
    result = 'worker-output/results/' + stem
    if (source / result).is_file():
        entry = {'key': issue['key'], 'request': 'worker-output/executed-requests/' + stem,
                 'prompt': 'worker-output/tokenized-prompts/' + stem, 'result': result, 'routing': 'route.json'}
        if not all((source / entry[k]).is_file() for k in ('request', 'prompt', 'result')):
            raise ValueError('partial item evidence; preserve original files and report incomplete export')
        entries.append(entry)
    files = {p.relative_to(source).as_posix(): sha(p) for p in sorted(source.rglob('*')) if p.is_file()}
    if 'process-receipt.json' not in files: raise ValueError('process receipt absent; do not fabricate one')
    envelope = {'version': VERSION, 'kind': 'prospective_central_stage2', 'process_reservation': issue['process'],
                'executor': 'Collaborator', 'assignment': issue['assignment']['id'], 'entries': entries, 'files': files}
    with zipfile.ZipFile(output, 'x', compression=zipfile.ZIP_DEFLATED) as archive:
        for name, h in files.items():
            p = within(source, name)
            if sha(p) != h: raise ValueError('source changed during export')
            archive.write(p, name)
        archive.writestr('return-envelope.json', canonical(envelope))
    print(json.dumps({'complete_return_zip': str(output), 'sha256': sha(output), 'entries': len(entries)}))


def main():
    p = argparse.ArgumentParser(); sub = p.add_subparsers(dest='command', required=True)
    r = sub.add_parser('run'); r.add_argument('--handoff', type=Path, required=True); r.add_argument('--job', required=True)
    r.add_argument('--authorize-stage2', action='store_true', required=True)
    e = sub.add_parser('export'); e.add_argument('--handoff', type=Path, required=True); e.add_argument('--job', required=True); e.add_argument('--output', type=Path, required=True)
    args = p.parse_args()
    if args.command == 'run': sys.exit(run(args.handoff, args.job))
    else: export(args.handoff, args.job, args.output)


if __name__ == '__main__': main()
