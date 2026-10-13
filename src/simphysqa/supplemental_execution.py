"""Development-only SPQ06 issuer/adapter/importer. Never accepts main scope.

Adapted from sealed execution_readiness/1.0.0 with explicit scope and ceilings.
Worker generation and instrumentation remain the exact transferred 1.0.0 versions.
Runtime qualification bootstraps fresh task evidence; it is not task qualification.
"""
import argparse
from collections import Counter
import json,math,os,shutil,sqlite3,subprocess,time,uuid
from pathlib import Path
try:
    from .execution_adapter import canonical,read,sha,digest,put,within,stage_key,files,assert_public,resolved_condition,LOCAL_FIELDS,VERSION
except ImportError:  # Standalone public package launcher, no organizer imports.
    from execution_adapter import canonical,read,sha,digest,put,within,stage_key,files,assert_public,resolved_condition,LOCAL_FIELDS,VERSION
SCOPE='development_rehearsal'
COORDINATOR_VERSION='SPQ06-awq-supplement/1.0.0'
CEILING=8640
COMBINED_CEILING=20400
INITIAL_LIMIT=15
CONTINUATION_LIMIT=3
PROCESS_LIMIT=6
CONDITIONS=('qwen3_32b_awq_off','qwen3_32b_awq_on')
ABLATIONS=('qwen3_32b_awq_on',)


try:
    from .execution_preflight import verify_preflight, live_device_check
except ImportError:
    from execution_preflight import verify_preflight, live_device_check

def device_binding_valid(bindings,qualification):
    visible=bindings['cuda_visible_devices'];uid=bindings['device_uuid']
    if visible==uid:return 'vllm' not in qualification.get('hardware_runtime',{}).get('backend_versions',{})
    proof=qualification.get('device_binding',{})
    return bool(proof.get('status')=='passed' and visible==str(proof.get('physical_index')) and proof.get('device_uuid')==uid and proof.get('torch_device_uuid')==uid)

def resolved_condition(package,cid,bindings,verify_artifacts=True):
    # HF snapshots legitimately symlink to the cache's adjacent blobs directory.
    # Package paths remain confined by within(); cache paths have their own root.
    try:
        from .execution_adapter import resolved_condition as original_resolve
    except ImportError:
        from execution_adapter import resolved_condition as original_resolve
    c=original_resolve(package,cid,bindings,verify_artifacts=False)
    if verify_artifacts:
        if 'weight_files' not in c:raise ValueError('development HF backends only')
        cache=Path(bindings['artifact_cache']).resolve();snapshot=Path(bindings['snapshot_path'])
        for name,info in c['weight_files'].items():
            rel=Path(name)
            if rel.is_absolute() or '..' in rel.parts:raise ValueError('unsafe model artifact path')
            target=(snapshot/rel).resolve()
            if cache not in target.parents:raise ValueError('model artifact outside explicit cache')
            if sha(target)!=info['sha256']:raise ValueError('pinned artifact mismatch: '+name)
    return c

def validate_package(root):
    root=Path(root);manifest=read(root/'package-manifest.json');actual=files(root);actual.pop('package-manifest.json')
    if actual!=manifest['files'] or manifest['scope']!=SCOPE: raise ValueError('development package hashes/scope')
    spec=read(root/'execution-spec.json');items=spec['items']
    if spec['execution_scope']!=SCOPE or spec['aggregate_seconds']!=CEILING or len(items)!=5 or len({x['sample_id'] for x in items})!=5 or {x['split'] for x in items}!={'train'}: raise ValueError('development selection/scope/ceiling')
    if {x['family'] for x in items}!={'direct','predictive','counterfactual','explanation','clarification'} or len({x['domain'] for x in items})!=4: raise ValueError('frozen development cells')
    expected={stage_key(i['sample_id'],cid,label,s) for cid in CONDITIONS for label in ('enriched','structured_only') if label=='enriched' or cid in ABLATIONS for i in items for s in ((1,2) if i['family']=='clarification' else (1,))}
    keys=[k for shard in spec['shards'] for k in shard['keys']]
    if len(keys)!=18 or len(set(keys))!=18 or set(keys)!=expected or len(spec['requests'])!=15 or any(s['owner'] is not None for s in spec['shards']): raise ValueError('development 40+8 coverage')
    if spec['limits']!={'initials':15,'continuations':3,'calls':18,'processes':6,'seconds':8640,'loading_per_process':600}: raise ValueError('development authorized limits changed')
    if len({x['group_id'] for x in items})!=5 or set(x['sample_id'] for x in items)&set(spec['original_sample_ids']): raise ValueError('supplemental distinct development selection')
    if spec.get('diagnostic_id')!='awq-supplement-1.0.0' or spec['prior_accounting']['combined_ceiling']!=COMBINED_CEILING: raise ValueError('supplemental budget provenance')
    for key,r in spec['requests'].items():
        p=within(root,r['path']);q=read(p)
        if sha(p)!=r['sha256'] or q['tools']!=[] or stage_key(q['sample_id'],q['condition_id'],q['input_condition'],1)!=key: raise ValueError('exact development request identity')
        assert_public(q)
    return manifest

def prepare_package(*args):
    raise ValueError('use the frozen supplemental selection exporter; original rehearsal proposals are rejected')

class Ledger:
    """One organizer database, transactional unique keys across all executor roots."""
    def __init__(self, path):
        self.path = Path(path)
        self.db = sqlite3.connect(self.path, timeout=30, isolation_level=None)
        self.db.execute('PRAGMA foreign_keys=ON')

    @classmethod
    def create(cls, path, package, fixture=False, ceiling=CEILING):
        if not fixture:
            validate_package(package)
            if ceiling != CEILING: raise ValueError('fixed development ceiling')
        path = Path(path); path.parent.mkdir(parents=True, exist_ok=True)
        with path.open('xb'): pass
        obj = cls(path)
        obj.db.executescript('''
          CREATE TABLE meta(k TEXT PRIMARY KEY,v TEXT NOT NULL);
          CREATE TABLE assignments(id TEXT PRIMARY KEY,owner TEXT NOT NULL,body TEXT NOT NULL);
          CREATE TABLE ownership(key TEXT PRIMARY KEY,assignment TEXT NOT NULL REFERENCES assignments(id));
          CREATE TABLE qualifications(hash TEXT PRIMARY KEY,body TEXT NOT NULL);
          CREATE TABLE processes(id TEXT PRIMARY KEY,assignment TEXT NOT NULL,bound REAL NOT NULL,actual REAL,state TEXT NOT NULL);
          CREATE TABLE stages(key TEXT PRIMARY KEY,process TEXT NOT NULL REFERENCES processes(id),request_hash TEXT NOT NULL,state TEXT NOT NULL);
          CREATE TABLE routes(key TEXT PRIMARY KEY,body TEXT NOT NULL);
          CREATE TABLE transports(id TEXT PRIMARY KEY,body TEXT NOT NULL);
          CREATE TABLE returns(key TEXT NOT NULL,artifact TEXT NOT NULL,source TEXT NOT NULL,valid INTEGER NOT NULL,reason TEXT,PRIMARY KEY(key,artifact));
        ''')
        spec = read(Path(package) / 'execution-spec.json')
        for k, v in {'version': VERSION, 'package': str(Path(package).resolve()), 'package_hash': sha(Path(package) / 'package-manifest.json'),
                     'spec': canonical(spec).decode(), 'fixture': str(fixture), 'ceiling': str(ceiling), 'scope': SCOPE}.items():
            obj.db.execute('INSERT INTO meta VALUES(?,?)', (k, v))
        if not fixture and ceiling != CEILING: raise ValueError('fixed development ceiling')
        return obj

    def meta(self, key):
        return self.db.execute('SELECT v FROM meta WHERE k=?', (key,)).fetchone()[0]

    def transaction(self, operation):
        self.db.execute('BEGIN IMMEDIATE')
        try:
            result = operation(); self.db.execute('COMMIT'); return result
        except BaseException:
            self.db.execute('ROLLBACK'); raise

    def issue(self, owner, shards):
        if not owner or not shards: raise ValueError('explicit executor and shards required')
        spec = json.loads(self.meta('spec')); found = [s for s in spec['shards'] if s['shard_id'] in shards]
        if {s['shard_id'] for s in found} != set(shards): raise ValueError('unknown shard')
        body = {'version': VERSION, 'id': str(uuid.uuid4()), 'owner': owner, 'package_sha256': self.meta('package_hash'),
                'shards': shards, 'keys': [k for s in found for k in s['keys']]}
        def op():
            self.db.execute('INSERT INTO assignments VALUES(?,?,?)', (body['id'], owner, canonical(body).decode()))
            for key in body['keys']: self.db.execute('INSERT INTO ownership VALUES(?,?)', (key, body['id']))
        self.transaction(op)
        return body

    def assignment(self, identity, executor):
        row = self.db.execute('SELECT owner,body FROM assignments WHERE id=?', (identity,)).fetchone()
        if row is None or row[0] != executor: raise ValueError('unknown assignment/executor')
        return json.loads(row[1])

    def approve_qualification(self, receipt):
        required = ('executor_id', 'condition_id', 'representation', 'package_sha256', 'worker_sha256', 'support_sha256',
                    'scientific_condition_sha256', 'hardware_runtime', 'model_files', 'tokenizer_files', 'quantization',
                    'precision', 'bindings_sha256', 'resolved_condition_sha256', 'render_verification', 'stop_verification', 'status')
        if any(k not in receipt or receipt[k] is None for k in required) or receipt['status'] != 'runtime_qualified' or receipt.get('execution_scope') != SCOPE:
            raise ValueError('incomplete/unqualified receipt')
        hw = receipt['hardware_runtime']
        if any(k not in hw or not hw[k] for k in ('gpu_name', 'device_uuid', 'vram_mib', 'os', 'wsl', 'driver', 'cuda_runtime', 'backend_versions')):
            raise ValueError('hardware/runtime qualification incomplete')
        for evidence in ('render_verification', 'stop_verification'):
            if receipt[evidence].get('status') != 'passed' or not receipt[evidence].get('evidence_sha256'):
                raise ValueError('qualification evidence required: ' + evidence)
        spec = json.loads(self.meta('spec')); c = spec['conditions'][receipt['condition_id']]
        package = Path(self.meta('package')); condition = read(package / c['path'])
        if receipt['package_sha256'] != self.meta('package_hash') or receipt['worker_sha256'] != c['worker_sha256'] or receipt['scientific_condition_sha256'] != c['sha256'] or receipt['support_sha256'] != sha(package / 'workers/execution_support.py'):
            raise ValueError('qualification pin mismatch')
        if receipt['quantization'] != condition['settings']['quantization'] or receipt['precision'] != condition['settings']['precision']:
            raise ValueError('model precision/quantization substitution')
        if 'weight_files' in condition:
            expected = {k: v['sha256'] for k, v in condition['weight_files'].items()}
            if receipt['model_files'] != expected: raise ValueError('model digest mismatch')
        elif receipt['model_files'].get('gguf') != condition['gguf_sha256']:
            raise ValueError('GGUF digest mismatch')
        runtime_pin = condition['runtime_versions'] if condition.get('runtime_versions') else {'llama.cpp': condition['runtime_revision'], 'server_sha256': condition['server_sha256']}
        if condition['backend']=='vllm' and (receipt.get('device_binding',{}).get('status')!='passed' or receipt.get('backend_config_verification',{}).get('status')!='passed'): raise ValueError('vLLM device/config preflight required before stage reservation')
        if receipt['tokenizer_files'].get('template_sha256') != condition['template_sha256'] or hw['backend_versions'] != runtime_pin:
            raise ValueError('tokenizer/runtime mismatch')
        if receipt.get('target_main_package_sha256')!=spec['main_package_sha256']: raise ValueError('supplemental evidence must bind corrected main package')
        h = digest(receipt)
        self.db.execute('INSERT INTO qualifications VALUES(?,?)', (h, canonical(receipt).decode()))
        return h

    def used(self):
        return self.db.execute("SELECT COALESCE(SUM(CASE WHEN actual IS NULL OR state IN ('unknown','interrupted') THEN MAX(bound,COALESCE(actual,0)) ELSE actual END),0) FROM processes").fetchone()[0]

    def check_combined(self,bound):
        spec=json.loads(self.meta('spec'))
        prior=spec['prior_accounting']
        if self.meta('fixture')!='True' and sha(prior['receipt_path'])!=prior['receipt_sha256']: raise ValueError('prior accounting identity changed')
        if prior['charged_seconds']+self.used()+bound>COMBINED_CEILING: raise ValueError('combined development ceiling exhausted')

    def pending(self, assignment, executor):
        body = self.assignment(assignment, executor)
        reserved = {r[0] for r in self.db.execute('SELECT key FROM stages')}
        routed = {r[0] for r in self.db.execute('SELECT key FROM routes')}
        # Unsupported receipts count as considered conditional stages, never become attempts.
        return [k for k in body['keys'] if k not in reserved and (k.endswith('|1') or k in routed and json.loads(self.db.execute('SELECT body FROM routes WHERE key=?', (k,)).fetchone()[0])['status'] == 'supported')]

    def reserve(self, assignment, executor, keys, request_hashes, qualification, loading=600, preflight=None, process=None):
        body = self.assignment(assignment, executor); keys = list(keys)
        if not keys or len(set(keys)) != len(keys) or not set(keys) <= set(body['keys']): raise ValueError('assignment filter required')
        qrow = self.db.execute('SELECT body FROM qualifications WHERE hash=?', (qualification,)).fetchone()
        if qrow is None: raise ValueError('unqualified runtime')
        qual = json.loads(qrow[0]); spec = json.loads(self.meta('spec'))
        if self.meta('fixture')!='True': verify_preflight(preflight,qual)
        if any(k.split('|')[1:3] != [qual['condition_id'], qual['representation']] for k in keys) or qual['executor_id'] != executor:
            raise ValueError('qualification condition/executor scope')
        if loading != 600: raise ValueError('frozen per-process overhead allowance')
        bound = loading + sum(read(Path(self.meta('package')) / spec['conditions'][k.split('|')[1]]['path'])['settings']['max_seconds'] for k in keys)
        reuse=process is not None
        process = process or str(uuid.uuid4())
        def op():
            if self.meta('scope') != SCOPE: raise ValueError('development ledger required')
            if not reuse and self.db.execute('SELECT COUNT(*) FROM processes').fetchone()[0] >= PROCESS_LIMIT: raise ValueError('worker-process ceiling exhausted')
            counts = dict(self.db.execute('SELECT substr(key,-1),COUNT(*) FROM stages GROUP BY substr(key,-1)'))
            if counts.get('1',0)+sum(k.endswith('|1') for k in keys)>INITIAL_LIMIT or counts.get('2',0)+sum(k.endswith('|2') for k in keys)>CONTINUATION_LIMIT: raise ValueError('development call ceiling exhausted')
            self.check_combined(bound-600 if reuse else bound)
            if self.used() + (bound-600 if reuse else bound) > float(self.meta('ceiling')): raise ValueError('aggregate ceiling exhausted including unknown reservations')
            for k in keys:
                if k.endswith('|1'):
                    expected = spec['requests'][k]['sha256']
                else:
                    row = self.db.execute('SELECT body FROM routes WHERE key=?', (k,)).fetchone()
                    if row is None: raise ValueError('actual supported route required')
                    route = json.loads(row[0])
                    if route['status'] != 'supported': raise ValueError('unexecuted conditional stage')
                    first = canonical_records(self).get(route['initial_key'])
                    if first is None or digest(first) != route['initial_result_sha256']:
                        raise ValueError('initial history missing or conflicted after routing')
                    expected = route['request_sha256']
                if request_hashes.get(k) != expected: raise ValueError('exact request required')
            if reuse:
                row=self.db.execute('SELECT assignment,bound,actual,state FROM processes WHERE id=?',(process,)).fetchone()
                if row!=(assignment,600.0,None,'reserved_unknown') or self.db.execute('SELECT 1 FROM stages WHERE process=?',(process,)).fetchone(): raise ValueError('preflight process already consumed or changed')
                self.db.execute('UPDATE processes SET bound=? WHERE id=?',(bound,process))
            else:
                self.db.execute('INSERT INTO processes VALUES(?,?,?,?,?)', (process, assignment, bound, None, 'reserved_unknown'))
            for k in keys: self.db.execute('INSERT INTO stages VALUES(?,?,?,?)', (k, process, request_hashes[k], 'reserved_unknown'))
        self.transaction(op)
        return {'id': process, 'assignment': assignment, 'executor': executor, 'qualification_sha256': qualification,
                'fixture': self.meta('fixture') == 'True',
                'bound_seconds': bound, 'loading_seconds': loading, 'keys': keys, 'request_hashes': request_hashes,
                'policy': 'known ended process charged full measured lifecycle once; unknown/orphan retains full bound; no stage attempt released'}

    def settle(self, process, elapsed, state):
        if not math.isfinite(elapsed) or elapsed < 0 or state not in ('complete', 'failed', 'timed_out', 'interrupted', 'unknown'):
            raise ValueError('invalid process accounting')
        changed = self.db.execute('UPDATE processes SET actual=?,state=? WHERE id=? AND actual IS NULL', (elapsed, state, process)).rowcount
        if changed != 1: raise ValueError('unknown or already settled process')

def prepare_job(ledger, assignment, executor, qualification, keys, bindings, output, preflight=None, process=None):
    """Later authorized coordinator operation. No inference; reservations persist first."""
    prepared_start = time.monotonic()
    package = Path(ledger.meta('package')); spec = read(package / 'execution-spec.json')
    if sha(package / 'package-manifest.json') != ledger.meta('package_hash'): raise ValueError('package identity changed')
    if ledger.meta('fixture') != 'True': validate_package(package)
    if not keys: raise ValueError('explicit assignment stage filter required')
    if len(keys) > 5: raise ValueError('development five-stage batching ceiling')
    cid, label = keys[0].split('|')[1:3]
    if any(k.split('|')[1:3] != [cid, label] for k in keys): raise ValueError('single condition/representation per process')
    if any(k not in ledger.pending(assignment, executor) for k in keys): raise ValueError('resume only never-reserved eligible keys')
    qual = json.loads(ledger.db.execute('SELECT body FROM qualifications WHERE hash=?', (qualification,)).fetchone()[0])
    if bindings['device_uuid'] != qual['hardware_runtime']['device_uuid']: raise ValueError('device qualification mismatch')
    if not device_binding_valid(bindings,qual) or digest(bindings) != qual['bindings_sha256']:
        raise ValueError('qualified portable environment/device binding required')
    requests = []
    for k in keys:
        requests.append(read(package / spec['requests'][k]['path']) if k.endswith('|1') else json.loads(ledger.db.execute('SELECT body FROM routes WHERE key=?', (k,)).fetchone()[0])['request'])
    ticket = ledger.reserve(assignment, executor, keys, dict(zip(keys, map(digest, requests))), qualification, preflight=preflight, process=process)
    output = Path(output); output.mkdir(parents=True, exist_ok=False)
    put(output / 'pre-reservation-preflight.json', preflight); put(output / 'ticket.json', ticket); put(output / 'assignment.json', ledger.assignment(assignment, executor)); put(output / 'qualification.json', qual)
    # All preparation after reservation is charged to this process allocation.
    # Coordinator can issue a ticket for a remote cache without reading its files.
    # The public executor verifies every pinned local file before loading weights.
    condition = resolved_condition(package, cid, bindings, verify_artifacts=False)
    if digest(condition) != qual['resolved_condition_sha256']: raise ValueError('qualified resolved configuration changed')
    put(output / 'condition.json', condition); put(output / 'requests.json', requests); put(output / 'bindings.json', bindings)
    for key in keys:
        if key.endswith('|2'):
            route = json.loads(ledger.db.execute('SELECT body FROM routes WHERE key=?', (key,)).fetchone()[0])
            put(output / 'routing' / (key.split('|')[0] + '-stage2.json'), route)
    worker = package / spec['conditions'][cid]['worker']
    context = {'version': VERSION, 'worker_sha256': sha(worker), 'resolved_condition_sha256': sha(output / 'condition.json'),
        'execution_scope': SCOPE,
        'development_manifest_sha256': spec['proposal_sha256'],
        'development_sample_ids': [i['sample_id'] for i in spec['items']],
        'scientific_condition_sha256': spec['conditions'][cid]['sha256'], 'qualification_status': qual['status'],
        'qualification_sha256': qualification, 'assignment_sha256': digest(ledger.assignment(assignment, executor)),
        'adapter_sha256': sha(Path(__file__)), 'preflight_sha256':digest(preflight), 'hardware_runtime_sha256': digest(qual['hardware_runtime']), 'gpu_name': qual['hardware_runtime']['gpu_name'],
        'hardware_runtime': qual['hardware_runtime'],
        'device_uuid': bindings['device_uuid'], 'llama_device': bindings.get('llama_device'), 'nvidia_smi': bindings['nvidia_smi'],
        'memory_interval_seconds': .5, 'representation': label, 'process_reservation': ticket['id'],
        'stage_reservations': {k: ticket['id'] + ':' + k for k in keys}}
    put(output / 'execution-context.json', context)
    command = [bindings['interpreter'], str(worker), '--condition', str(output / 'condition.json'), '--requests', str(output / 'requests.json'),
               '--output', str(output / 'worker-output'), '--execution-context', str(output / 'execution-context.json')]
    put(output / 'launch.json', {'command': command, 'worker_relative': spec['conditions'][cid]['worker'], 'package_sha256': ledger.meta('package_hash'),
        'environment': {**bindings['environment'], 'CUDA_VISIBLE_DEVICES': bindings['cuda_visible_devices'],
        'HF_HUB_OFFLINE': '1', 'TRANSFORMERS_OFFLINE': '1', 'VLLM_NO_USAGE_STATS': '1'}, 'deadline_seconds': ticket['bound_seconds'],
        'prepared_unix_seconds': time.time(), 'preparation_elapsed_seconds': time.monotonic() - prepared_start + (preflight or {}).get('accounted_preflight_seconds',0)})
    return ticket

def launch_job(job, package=None):
    """Explicit later launch; one-shot exclusive marker, no inferred permission."""
    job = Path(job); launch = read(job / 'launch.json'); started = time.monotonic()
    # Time waiting for transfer/assignment is not workstation execution time.
    elapsed_preparation = launch['preparation_elapsed_seconds']
    put(job / 'launch-reserved.json', {'unix_seconds': time.time(), 'attempt': 1})
    state = 'unknown'; code = None
    proc = None
    def terminate_tree():
        if proc is None or proc.poll() is not None: return
        if os.name == 'nt':
            subprocess.run(['taskkill', '/PID', str(proc.pid), '/T', '/F'], capture_output=True, timeout=10)
        else:
            import signal
            os.killpg(proc.pid, signal.SIGKILL)
        proc.wait(timeout=10)
    try:
        if package is not None:
            package = Path(package); validate_package(package)
            if sha(package / 'package-manifest.json') != launch['package_sha256']: raise ValueError('executor package changed')
            worker = within(package, launch['worker_relative']); context = read(job / 'execution-context.json'); qual = read(job / 'qualification.json')
            if sha(worker) != context['worker_sha256'] or sha(package / 'workers/execution_support.py') != qual['support_sha256']:
                raise ValueError('executor worker/support pin')
            if digest(read(job / 'bindings.json')) != qual['bindings_sha256'] or digest(read(job / 'assignment.json')) != context['assignment_sha256']:
                raise ValueError('executor binding/assignment pin')
            if digest(qual) != context['qualification_sha256'] or qual['status'] != 'runtime_qualified' or context.get('execution_scope') != SCOPE: raise ValueError('executor qualification gate')
            condition = read(job / 'condition.json'); verified = resolved_condition(package, condition['condition_id'], read(job / 'bindings.json'))
            if verified != condition or digest(verified) != qual['resolved_condition_sha256']: raise ValueError('executor resolved config pin')
            if not device_binding_valid(read(job/'bindings.json'),qual): raise ValueError('qualified device binding required')
            binding=read(job/'bindings.json')
            if binding['cuda_visible_devices']!=binding['device_uuid']:
                observed=subprocess.run([binding['nvidia_smi'],'--query-gpu=index,uuid','--format=csv,noheader,nounits'],capture_output=True,text=True,timeout=5,check=True)
                mapping={i.strip():u.strip() for line in observed.stdout.strip().splitlines() for i,u in [line.split(',')]}
                if mapping.get(binding['cuda_visible_devices'])!=binding['device_uuid']:raise ValueError('physical index/UUID mapping changed')
            requests = read(job / 'requests.json'); ticket = read(job / 'ticket.json')
            expected = {stage_key(q['sample_id'], q['condition_id'], q['input_condition'], q.get('stage', 1)): digest(q) for q in requests}
            if expected != ticket['request_hashes']: raise ValueError('executor exact issued request pin')
            launch['command'] = [read(job / 'bindings.json')['interpreter'], str(worker), '--condition', str(job / 'condition.json'),
                '--requests', str(job / 'requests.json'), '--output', str(job / 'worker-output'), '--execution-context', str(job / 'execution-context.json')]
        else:
            raise ValueError('explicit verified portable package required')
        if time.monotonic() - started + elapsed_preparation >= launch['deadline_seconds']:
            raise TimeoutError('process allowance exhausted during executor preflight; no inference started')
        with (job / 'process.log').open('xb') as log:
            proc = subprocess.Popen(launch['command'], env={**os.environ, **launch['environment']}, stdout=log, stderr=subprocess.STDOUT,
                                    start_new_session=os.name != 'nt')
            code = proc.wait(timeout=max(.001, launch['deadline_seconds'] - elapsed_preparation - (time.monotonic() - started)))
        state = 'complete' if code == 0 else 'failed'
    except subprocess.TimeoutExpired: state = 'timed_out'; terminate_tree()
    except TimeoutError as exc:
        state = 'timed_out'; put(job / 'launch-failure.json', {'reason': str(exc), 'inference_started': proc is not None})
    except KeyboardInterrupt: state = 'interrupted'; terminate_tree()
    except Exception as exc:
        state = 'failed'; put(job / 'launch-failure.json', {'reason': type(exc).__name__ + ': ' + str(exc), 'inference_started': proc is not None})
    finally:
        put(job / 'process-receipt.json', {'state': state, 'returncode': code, 'elapsed_seconds': elapsed_preparation + time.monotonic() - started,
            'boundaries': 'coordinator job preparation plus executor preflight/hash verification through process exit; loading, all stages, teardown counted once; transfer/queue wait excluded',
            'process_reservation': read(job / 'ticket.json')['id']})

def export_return(job, output):
    job, output = Path(job), Path(output); output.mkdir(parents=True, exist_ok=False)
    for p in sorted(job.rglob('*')):
        if p.is_file():
            dest = within(output, p.relative_to(job)); dest.parent.mkdir(parents=True, exist_ok=True)
            with dest.open('xb') as stream: stream.write(p.read_bytes())
    ticket = read(job / 'ticket.json'); entries = []
    for key in ticket['keys']:
        sid, cid, label, stage = key.split('|'); stem = sid + '-stage' + stage + '.json'
        entry = {'key': key, 'request': 'worker-output/executed-requests/' + stem,
                 'result': 'worker-output/results/' + stem, 'prompt': 'worker-output/tokenized-prompts/' + stem}
        if stage == '2': entry['routing'] = 'routing/' + stem
        entries.append(entry)
    put(output / 'return-envelope.json', {'version': VERSION, 'kind': 'fixture' if ticket.get('fixture') else SCOPE,
        'assignment': ticket['assignment'], 'executor': ticket['executor'], 'process_reservation': ticket['id'],
        'qualification_sha256': ticket['qualification_sha256'], 'entries': entries, 'files': files(output)})
    return sha(output / 'return-envelope.json')

def import_return(ledger, source, root):
    """Preserve bytes BEFORE validation, including invalid/incomplete transports."""
    source, root = Path(source), Path(root); source_hashes = files(source); transport = digest(source_hashes)
    if source.resolve() == root.resolve() or source.resolve() in root.resolve().parents:
        raise ValueError('import root must be outside returned source')
    root.mkdir(parents=True, exist_ok=True)
    dest = root / (transport + '-' + str(uuid.uuid4()))
    shutil.copytree(source, dest)
    envelope = None; reasons = []; accepted = []; lifecycle_verified = False
    try:
        envelope = read(dest / 'return-envelope.json')
        from jsonschema import validate
        from jsonschema.exceptions import ValidationError
        try: validate(envelope, read(Path(__file__).parent / 'development-return.schema.json'))
        except ValidationError as exc: raise ValueError('return envelope schema: ' + exc.message) from exc
        if envelope['version'] != VERSION or envelope['kind'] != ('fixture' if ledger.meta('fixture') == 'True' else SCOPE):
            raise ValueError('main/fixture/pilot namespace boundary')
        actual = files(dest); actual.pop('return-envelope.json')
        if envelope['files'] != actual: raise ValueError('returned file/hash mismatch')
        assignment = ledger.assignment(envelope['assignment'], envelope['executor'])
        ticket = read(dest / 'ticket.json'); qual = read(dest / 'qualification.json'); context = read(dest / 'execution-context.json')
        if digest(qual) != envelope['qualification_sha256'] or not ledger.db.execute('SELECT 1 FROM qualifications WHERE hash=?', (digest(qual),)).fetchone():
            raise ValueError('unqualified return')
        if digest(read(dest / 'assignment.json')) != digest(assignment) or context['assignment_sha256'] != digest(assignment): raise ValueError('assignment provenance')
        process = ledger.db.execute('SELECT assignment,bound FROM processes WHERE id=?', (envelope['process_reservation'],)).fetchone()
        if not process or process[0] != envelope['assignment'] or ticket['id'] != envelope['process_reservation']: raise ValueError('unknown process reservation')
        if context['qualification_sha256'] != digest(qual) or context['worker_sha256'] != qual['worker_sha256'] or context['resolved_condition_sha256'] != sha(dest / 'condition.json') or context['resolved_condition_sha256'] != qual['resolved_condition_sha256']:
            raise ValueError('worker/config qualification identity')
        if ledger.meta('fixture')!='True':
            if context.get('adapter_sha256')!=sha(Path(__file__)): raise ValueError('versioned adapter return identity')
            verify_preflight(read(dest/'pre-reservation-preflight.json'),qual,check_fresh=False)
        spec = json.loads(ledger.meta('spec')); public_c = read(Path(ledger.meta('package')) / spec['conditions'][qual['condition_id']]['path'])
        returned_c = {k: v for k, v in read(dest / 'condition.json').items() if k not in LOCAL_FIELDS}
        if returned_c != public_c: raise ValueError('scientific condition changed')
        if context.get('execution_scope') != SCOPE or qual['status'] != 'runtime_qualified': raise ValueError('development runtime scope required')
        if any(ledger.db.execute('SELECT process,request_hash FROM stages WHERE key=?',(k,)).fetchone() != (ticket['id'],h) for k,h in ticket['request_hashes'].items()): raise ValueError('lifecycle stage reservation identity')
        lifecycle_verified = True
        runtime_path = dest / 'worker-output/runtime.json'
        if not runtime_path.exists(): raise ValueError('runtime receipt absent; reserved work remains unknown')
        runtime = read(runtime_path)
        if runtime.get('qualification_sha256') != digest(qual) or runtime.get('worker_sha256') != qual['worker_sha256'] or runtime.get('process_reservation') != ticket['id']:
            raise ValueError('runtime receipt identity')
        if runtime.get('gpu_name', qual['hardware_runtime']['gpu_name']) != qual['hardware_runtime']['gpu_name']:
            raise ValueError('GPU identity changed')
        if runtime.get('runtime_versions', qual['hardware_runtime']['backend_versions']) != qual['hardware_runtime']['backend_versions']:
            raise ValueError('actual backend versions changed')
        if public_c['backend'] == 'llama.cpp':
            launch_evidence = read(dest / 'worker-output/server-launch.json')
            device_evidence = read(dest / 'worker-output/cuda-device-preflight.json')
            args = launch_evidence['args']
            if runtime.get('runtime_revision') != public_c['runtime_revision'] or args[args.index('--device') + 1] != context['llama_device'] or device_evidence['returncode'] != 0 or context['llama_device'] not in device_evidence['stdout']:
                raise ValueError('GGUF runtime/offload evidence')
        expected_hardware = {k: qual['hardware_runtime'][k] for k in ('driver', 'os', 'vram_mib')}
        if runtime.get('hardware_runtime_observed') != expected_hardware or runtime.get('device_uuid') != qual['hardware_runtime']['device_uuid']:
            raise ValueError('actual hardware preflight evidence missing/changed')
        if {e['key'] for e in envelope['entries']} != set(ticket['keys']) or len(envelope['entries']) != len(ticket['keys']): raise ValueError('return entry coverage')
        for entry in envelope['entries']:
            key = entry['key']; artifact = entry_identity(entry, actual); reason = None
            try:
                if key not in assignment['keys']: raise ValueError('unassigned/unknown selected key')
                reservation = ledger.db.execute('SELECT process,request_hash FROM stages WHERE key=?', (key,)).fetchone()
                if not reservation or reservation[0] != ticket['id']: raise ValueError('unique central reservation required')
                q = read(within(dest, entry['request'])); raw = read(within(dest, entry['result'])); prompt = read(within(dest, entry['prompt']))
                if sha(within(dest, entry['request'])) != reservation[1] or raw['request_sha256'] != reservation[1] or q['tools'] != []: raise ValueError('request provenance')
                if stage_key(raw['sample_id'], raw['condition_id'], raw['representation'], raw['stage']) != key: raise ValueError('result identity')
                if raw.get('response_origin') != 'actual_local_model' and ledger.meta('fixture') != 'True': raise ValueError('pilot/non-main response')
                for field in ('qualification_sha256', 'assignment_sha256', 'hardware_runtime_sha256', 'worker_sha256', 'scientific_condition_sha256', 'process_reservation'):
                    if raw.get(field) != context[field]: raise ValueError('returned provenance: ' + field)
                if raw.get('stage_key') != key or raw.get('stage_reservation') != context['stage_reservations'][key]:
                    raise ValueError('stage reservation provenance')
                if raw.get('cpu_fallback') is not False or raw.get('execution_version') != VERSION or raw.get('execution_scope') != SCOPE or raw.get('qualification_status') != 'runtime_qualified': raise ValueError('unqualified runtime/fallback/rehearsal scope')
                if not isinstance(prompt['prompt'], str) or not isinstance(prompt['token_ids'], list): raise ValueError('render/token evidence absent')
                if raw['completion_status'] not in ('completed', 'failed', 'length_limited', 'timeout', 'interrupted', 'unknown'): raise ValueError('completion state')
                if not isinstance(raw['raw_output'], str) or 'termination' not in raw or 'device_memory' not in raw or 'total_stage_seconds' not in raw: raise ValueError('essential record absent')
                if key.endswith('|2'):
                    route = json.loads(ledger.db.execute('SELECT body FROM routes WHERE key=?', (key,)).fetchone()[0])
                    if read(within(dest, entry['routing'])) != route: raise ValueError('coordinator routing receipt changed')
                    if route['status'] != 'supported' or digest(q) != route['request_sha256'] or q['messages'][-2] != {'role': 'assistant', 'content': route['actual_raw']}:
                        raise ValueError('supported actual dialogue history required')
                accepted.append(key)
                ledger.db.execute('UPDATE stages SET state=? WHERE key=?', (raw['completion_status'], key))
            except (ValueError, KeyError, TypeError, OSError) as exc:
                reason = str(exc); reasons.append({'key': key, 'reason': reason})
            ledger.db.execute('INSERT OR IGNORE INTO returns VALUES(?,?,?,?,?)', (key, artifact, str(dest), int(reason is None), reason))
        if (dest / 'process-receipt.json').exists():
            receipt = read(dest / 'process-receipt.json')
            row = ledger.db.execute('SELECT actual,state FROM processes WHERE id=?', (ticket['id'],)).fetchone()
            if row[0] is None: ledger.settle(ticket['id'], receipt['elapsed_seconds'], receipt['state'])
            elif row != (receipt['elapsed_seconds'], receipt['state']):
                elapsed = receipt['elapsed_seconds']
                if not math.isfinite(elapsed) or elapsed < 0: raise ValueError('invalid conflicting process timing')
                ledger.db.execute("UPDATE processes SET actual=?,state='unknown' WHERE id=?", (max(row[0], elapsed), ticket['id']))
                reasons.append({'process_reservation': ticket['id'], 'reason': 'conflicting lifecycle receipts; full bound/overrun charged, no preferred receipt'})
    except (ValueError, KeyError, TypeError, OSError) as exc:
        reasons.append({'transport': transport, 'reason': str(exc)})
        # A differing invalid transport for a known key also blocks canonicalization.
        if envelope:
            spec = json.loads(ledger.meta('spec')); known = {k for s in spec['shards'] for k in s['keys']}
            for entry in envelope.get('entries', []):
                if entry.get('key') in known:
                    artifact = entry_identity(entry, source_hashes)
                    ledger.db.execute('INSERT OR IGNORE INTO returns VALUES(?,?,?,?,?)', (entry['key'], artifact, str(dest), 0, str(exc)))
    if lifecycle_verified and (dest / 'process-receipt.json').exists() and (dest / 'ticket.json').exists():
        lifecycle = read(dest / 'process-receipt.json'); returned_ticket = read(dest / 'ticket.json')
        row = ledger.db.execute('SELECT actual FROM processes WHERE id=?', (returned_ticket.get('id'),)).fetchone()
        if row and row[0] is None and lifecycle.get('process_reservation') == returned_ticket['id']:
            try: ledger.settle(returned_ticket['id'], lifecycle['elapsed_seconds'], lifecycle['state'])
            except (ValueError,KeyError,TypeError): pass  # Unknown reservation retained.
    previous = ledger.db.execute('SELECT 1 FROM transports WHERE id=?', (transport,)).fetchone()
    receipt = {'version': VERSION, 'transport': transport, 'source_root': str(dest), 'identical_duplicate_transport': bool(previous),
               'accepted_keys': accepted, 'validation_failures': reasons,
               'conflicts': conflicts(ledger), 'aggregate_charged_seconds': ledger.used()}
    ledger.db.execute('INSERT OR IGNORE INTO transports VALUES(?,?)', (transport, canonical(receipt).decode()))
    put(root / ('import-' + str(uuid.uuid4()) + '.json'), receipt)
    return receipt

def conflicts(ledger):
    return [r[0] for r in ledger.db.execute('SELECT key FROM returns GROUP BY key HAVING COUNT(DISTINCT artifact)>1')]

def entry_identity(entry, hashes):
    """Transport aggregation must not make a changed OTHER item conflict this key."""
    shared = {'assignment.json', 'qualification.json', 'bindings.json', 'ticket.json', 'condition.json', 'execution-context.json',
              'process-receipt.json', 'worker-output/runtime.json', 'worker-output/server-launch.json', 'worker-output/server-properties.json',
              'worker-output/cuda-device-preflight.json'}
    stem = Path(entry['result']).name
    selected = {name: h for name, h in hashes.items() if name in shared or name in (entry['request'], entry['result'], entry['prompt'], entry.get('routing')) or
                name.startswith('worker-output/') and Path(name).name == stem}
    return digest({'entry': entry, 'artifacts': selected})

def canonical_records(ledger):
    blocked = set(conflicts(ledger)); result = {}
    # A continuation cannot be canonical while its actual initial history conflicts.
    for key in list(blocked):
        if key.endswith('|1'): blocked.add(key[:-1] + '2')
    for key, source in ledger.db.execute('SELECT key,source FROM returns WHERE valid=1'):
        if key in blocked: continue
        envelope = read(Path(source) / 'return-envelope.json'); entry = next(e for e in envelope['entries'] if e['key'] == key)
        actual = files(Path(source)); actual.pop('return-envelope.json')
        if actual != envelope['files']: raise ValueError('immutable imported source changed')
        if not ledger.db.execute('SELECT 1 FROM transports WHERE id=?', (digest(files(Path(source))),)).fetchone():
            raise ValueError('immutable transport envelope changed')
        result[key] = read(within(source, entry['result']))
    return result

def coordinate_reply(ledger,key,pilot,output):
    from .spq06 import parse_answer
    from .main_public import continuation
    if ledger.meta('scope')!=SCOPE or not key.endswith('|1'):raise ValueError('development initial required')
    raw=canonical_records(ledger).get(key)
    if raw is None:raise ValueError('canonical actual first result required')
    sid,cid,label,_=key.split('|');spec=json.loads(ledger.meta('spec'));item=next(i for i in spec['items'] if i['sample_id']==sid)
    if item['family']!='clarification':raise ValueError('clarification development item required')
    record=read(Path(pilot)/'private-records'/(sid+'.json'))
    if digest(record)!=item['record_sha256']:raise ValueError('development scoring record changed')
    condition=read(Path(ledger.meta('package'))/spec['conditions'][cid]['path'])
    request=None;reason=raw['completion_status']
    try:
        if raw['completion_status']=='completed':
            response,diagnostics=parse_answer(raw['raw_output']);request,route=continuation(record,condition,raw['raw_output'],response,label=='structured_only');reason=route['status']
            if request and request['messages'][:-2]!=read(Path(ledger.meta('package'))/spec['requests'][key]['path'])['messages']:raise ValueError('continuation original request history differs')
    except (ValueError,KeyError,TypeError) as exc:reason=type(exc).__name__+': '+str(exc)
    second=stage_key(sid,cid,label,2)
    receipt={'version':VERSION,'execution_scope':SCOPE,'key':second,'initial_key':key,'actual_raw':raw['raw_output'],
        'initial_result_sha256':digest(raw),'status':'supported' if request else 'unexecuted_conditional','reason':reason,'request':request,'request_sha256':digest(request) if request else None}
    ledger.db.execute('INSERT INTO routes VALUES(?,?)',(second,canonical(receipt).decode()));put(output,receipt);return receipt

def analyse_development(ledger,pilot,output):
    from .main_analysis import assess
    from .spq06 import parse_answer
    if ledger.meta('scope')!=SCOPE:raise ValueError('development ledger required')
    output=Path(output);output.mkdir(parents=True,exist_ok=False);records=canonical_records(ledger);spec=json.loads(ledger.meta('spec'));rows=[];parsed=[]
    for key,raw in records.items():
        value=diagnostics=failure=None
        try:value,diagnostics=parse_answer(raw['raw_output'])
        except (ValueError,TypeError) as exc:failure=type(exc).__name__+': '+str(exc)
        parsed.append({'stage_key':key,'raw_result_sha256':digest(raw),'parsed_response':value,'parser_diagnostics':diagnostics,'parser_failure':failure,'execution_status':raw['completion_status']})
    for shard in spec['shards']:
        cid,label=shard['condition_id'],shard['representation'];c=read(Path(ledger.meta('package'))/spec['conditions'][cid]['path'])
        for item in spec['items']:
            sid=item['sample_id'];r=read(Path(pilot)/'private-records'/(sid+'.json'))
            if digest(r)!=item['record_sha256']:raise ValueError('development private record changed')
            first=records.get(stage_key(sid,cid,label,1));second=records.get(stage_key(sid,cid,label,2))
            rows.append({**item,'condition_id':cid,'input_condition':label,**assess(r,c,first,second),'actual_initial_sha256':digest(first) if first else None,'actual_continuation_sha256':digest(second) if second else None})
    versions={n:sha(Path(__file__).parent/(n+'.py')) for n in ('spq06','scoring','explanation_evaluation','clarification_evaluation','main_analysis','main_public')}
    result={'version':COORDINATOR_VERSION,'execution_scope':SCOPE,'items':rows,'parsed_stages':parsed,'scorer_parser_sha256':versions,'fixed_item_denominator':15,'unique_development_items':5,
      'claims':'Execution rehearsal only; no benchmark uncertainty or empirical performance claim. Automatic explanation facts do not establish prose adequacy.',
      'conflicts':conflicts(ledger),'invalid_returns':list(ledger.db.execute('SELECT key,reason FROM returns WHERE valid=0')),
      'processes':[dict(zip(('id','assignment','bound_seconds','measured_seconds','state'),r)) for r in ledger.db.execute('SELECT * FROM processes')],
      'reserved_stages':[dict(zip(('key','process','request_hash','state'),r)) for r in ledger.db.execute('SELECT * FROM stages')],
      'routes':[json.loads(r[0]) for r in ledger.db.execute('SELECT body FROM routes')],'aggregate_charged_seconds':ledger.used()}
    put(output/'development-analysis.json',result);return result

def reserve_startup(ledger,assignment,executor,cid,label,provenance):
    if ledger.meta('scope')!=SCOPE:raise ValueError('development startup ledger required')
    owned=ledger.assignment(assignment,executor)
    if not any(k.split('|')[1:3]==[cid,label] for k in owned['keys']):raise ValueError('assigned startup condition required')
    identity=str(uuid.uuid4())
    def op():
        if ledger.db.execute('SELECT COUNT(*) FROM processes').fetchone()[0]>=PROCESS_LIMIT:raise ValueError('worker-process ceiling exhausted')
        ledger.check_combined(600)
        if ledger.used()+600>float(ledger.meta('ceiling')):raise ValueError('aggregate startup ceiling exhausted')
        ledger.db.execute('INSERT INTO processes VALUES(?,?,?,?,?)',(identity,assignment,600,None,'reserved_unknown'))
    ledger.transaction(op)
    return {'version':COORDINATOR_VERSION,'scope':SCOPE,'purpose':'startup_only_no_answering','id':identity,'assignment':assignment,'executor':executor,
      'condition_id':cid,'representation':label,'bound_seconds':600,'stage_keys':[],'answering_call_ceiling':0,'provenance':provenance,
      'policy':'counts as a worker-process launch; known lifecycle once, unknown/interrupted retains600; no scientific stage attempts or releases'}

def main():
    p=argparse.ArgumentParser();sub=p.add_subparsers(dest='command',required=True)
    a=sub.add_parser('prepare-package');a.add_argument('--proposal',required=True);a.add_argument('--main-package',required=True);a.add_argument('--output',required=True)
    a=sub.add_parser('validate');a.add_argument('--package',required=True)
    a=sub.add_parser('launch');a.add_argument('--job',required=True);a.add_argument('--package',required=True);a.add_argument('--authorize-development',action='store_true',required=True)
    a=sub.add_parser('export-return');a.add_argument('--job',required=True);a.add_argument('--output',required=True)
    for name in ('init','issue','approve','pending','prepare-job','import','route','analyse'):
        a=sub.add_parser(name);a.add_argument('--ledger',required=True)
        if name=='init':a.add_argument('--package',required=True)
        if name in ('issue','pending','prepare-job'):a.add_argument('--executor',required=True)
        if name=='issue':a.add_argument('--shard',action='append',required=True);a.add_argument('--output',required=True)
        if name=='approve':a.add_argument('--receipt',required=True)
        if name in ('pending','prepare-job'):a.add_argument('--assignment',required=True)
        if name=='prepare-job':
            a.add_argument('--process')
            for flag in ('qualification','keys','bindings','output','preflight'):a.add_argument('--'+flag,required=True)
        if name=='import':a.add_argument('--source',required=True);a.add_argument('--output',required=True)
        if name=='route':a.add_argument('--key',required=True);a.add_argument('--pilot',required=True);a.add_argument('--output',required=True)
        if name=='analyse':a.add_argument('--pilot',required=True);a.add_argument('--output',required=True)
    a=p.parse_args()
    if a.command=='prepare-package':result=prepare_package(a.proposal,a.main_package,a.output);result={'verified_files':len(result['files'])}
    elif a.command=='validate':result={'verified_files':len(validate_package(a.package)['files'])}
    elif a.command=='launch':launch_job(a.job,a.package);result=read(Path(a.job)/'process-receipt.json')
    elif a.command=='export-return':result={'sha256':export_return(a.job,a.output)}
    elif a.command=='init':Ledger.create(a.ledger,a.package).db.close();result={'scope':SCOPE,'ledger':a.ledger}
    else:
        ledger=Ledger(a.ledger)
        if ledger.meta('scope')!=SCOPE:raise ValueError('development ledger required')
        if a.command=='issue':result=ledger.issue(a.executor,a.shard);put(a.output,result)
        elif a.command=='approve':result={'qualification_sha256':ledger.approve_qualification(read(a.receipt))}
        elif a.command=='pending':result={'never_reserved_keys':ledger.pending(a.assignment,a.executor)}
        elif a.command=='prepare-job':result=prepare_job(ledger,a.assignment,a.executor,a.qualification,read(a.keys),read(a.bindings),a.output,read(a.preflight),a.process)
        elif a.command=='import':result=import_return(ledger,a.source,a.output)
        elif a.command=='route':result=coordinate_reply(ledger,a.key,a.pilot,a.output)
        elif a.command=='analyse':result={'rows':len(analyse_development(ledger,a.pilot,a.output)['items'])}
        ledger.db.close()
    print(canonical(result).decode())
if __name__=='__main__':main()
