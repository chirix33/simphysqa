"""SPQ06 execution readiness 1.0.0. Offline export and central coordination.

SQLite is CENTRAL and must never be copied to executors as an independent ledger.
The coordinator issues disjoint tickets before transfer. No network service needed.
Neither creating the public package nor validating it reserves any main stages.
"""
import argparse
from collections import Counter
from copy import deepcopy
import hashlib
import json
import math
import os
from pathlib import Path
import shutil
import sqlite3
import subprocess
import time
import uuid
import zipfile

VERSION = 'SPQ06-execution/1.0.0'
CEILING = 172800
ABLATIONS = ('qwen3_8b_direct', 'qwen3_32b_awq_on')
LOCAL_FIELDS = {'local_python', 'snapshot_path', 'gguf_path', 'server_path', 'library_paths'}


def canonical(value):
    return (json.dumps(value, sort_keys=True, separators=(',', ':'), ensure_ascii=False, allow_nan=False) + '\n').encode()


def read(path):
    return json.loads(Path(path).read_bytes())


def sha(path):
    with Path(path).open('rb') as stream:
        return hashlib.file_digest(stream, 'sha256').hexdigest()


def digest(value):
    return hashlib.sha256(canonical(value)).hexdigest()


def put(path, value):
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open('xb') as stream:
        stream.write(canonical(value))


def within(root, relative):
    root = Path(root).resolve()
    path = (root / relative).resolve()
    if Path(relative).is_absolute() or path == root or root not in path.parents or '..' in Path(relative).parts:
        raise ValueError('unsafe relative path: ' + str(relative))
    return path


def stage_key(sid, cid, representation, stage):
    parts = (sid, cid, representation, str(stage))
    if any('|' in p for p in parts) or representation not in ('enriched', 'structured_only') or stage not in (1, 2):
        raise ValueError('invalid stage identity')
    return '|'.join(parts)


def files(root):
    return {p.relative_to(root).as_posix(): sha(p) for p in sorted(Path(root).rglob('*')) if p.is_file()}


def validate_package(root):
    root = Path(root)
    manifest = read(root / 'package-manifest.json')
    actual = files(root)
    actual.pop('package-manifest.json')
    if actual != manifest['files']:
        raise ValueError('package file/hash mismatch')
    if any('actual-pilot' in name or '-observed-stop-events' in name or '-actual-server-launch' in name for name in actual):
        raise ValueError('historical execution evidence stays outside public transfer')
    spec = read(root / 'execution-spec.json')
    if spec['selected_size'] != 200 or spec['aggregate_seconds'] != CEILING:
        raise ValueError('scientific size/budget changed')
    keys = [k for shard in spec['shards'] for k in shard['keys']]
    if len(keys) != 2640 or len(set(keys)) != 2640 or any(s['owner'] is not None for s in spec['shards']):
        raise ValueError('ownership template coverage')
    items = spec['items']
    if len(items) != 200 or len({i['sample_id'] for i in items}) != 200 or len({i['group_id'] for i in items}) != 200 or {i['split'] for i in items} != {'test_id'}:
        raise ValueError('selected unique groups/splits')
    allocation = Counter((i['domain'], i['family']) for i in items)
    if len(allocation) != 20 or set(allocation.values()) != {10}:
        raise ValueError('frozen balanced core allocation')
    expected = {stage_key(i['sample_id'], cid, label, stage) for cid in spec['conditions'] for label in ('enriched', 'structured_only')
        if label == 'enriched' or cid in ABLATIONS for i in items for stage in ((1, 2) if i['family'] == 'clarification' else (1,))}
    if set(keys) != expected: raise ValueError('exhaustive item/condition/representation/stage coverage')
    if len(spec['requests']) != 2200:
        raise ValueError('initial collection incomplete')
    for key, request in spec['requests'].items():
        path = within(root, request['path'])
        q = read(path)
        if sha(path) != request['sha256'] or q['tools'] != [] or stage_key(q['sample_id'], q['condition_id'], q['input_condition'], 1) != key:
            raise ValueError('request identity/hash/tools')
        assert_public(q)
    return manifest


def assert_public(value):
    forbidden = {'private', 'gold', 'gold_answer', 'gold_explanation', 'reference', 'reference_rollout',
                 'solution_trace', 'witnesses', 'credential', 'api_key'}
    def scan(x):
        if isinstance(x, dict):
            if forbidden & x.keys():
                raise ValueError('private public-input field')
            for v in x.values(): scan(v)
        elif isinstance(x, list):
            for v in x: scan(v)
    scan(value)
    for message in value.get('messages', []):
        if message['role'] == 'user' and '\n' in message['content']:
            text = message['content'].split('\n', 1)[1].lstrip()
            if text.startswith('{'):
                scan(json.JSONDecoder().raw_decode(text)[0])


def export_package(preparation, confirmation, output):
    preparation, confirmation, output = map(Path, (preparation, confirmation, output))
    from .spq01a import verify_manifest
    verify_manifest(preparation)
    output.mkdir(parents=True, exist_ok=False)
    mappings = []
    def copy(source, relative):
        dest = within(output, relative); dest.parent.mkdir(parents=True, exist_ok=True)
        with dest.open('xb') as stream: stream.write(source.read_bytes())
        mappings.append({'path': relative, 'source_relative': str(source.relative_to(preparation)) if preparation in source.parents else str(source.relative_to(confirmation)) if confirmation in source.parents else source.name,
                         'source_sha256': sha(source), 'kind': 'exact_copy'})
    selected = read(preparation / 'nested-200-manifest.json')
    items = selected['items']
    identity_fields = ('sample_id', 'group_id', 'domain', 'family', 'split', 'candidate_rank', 'qualified_cell_rank', 'nested_core', 'record_sha256', 'original_source_sha256')
    public_items = [{k: v for k, v in item.items() if k in identity_fields} for item in items]
    put(output / 'selected-items.json', {'items': public_items, 'original_manifest_sha256': sha(preparation / 'nested-200-manifest.json')})
    put(output / 'inventory-400.json', {'items': [{k: v for k, v in item.items() if k in identity_fields} for item in read(preparation / 'nested-400-manifest.json')['items']],
        'original_manifest_sha256': sha(preparation / 'nested-400-manifest.json'), 'executable': False})
    # Original identity manifest contains private path pointers, retained organizer-side.
    spec = {'version': VERSION, 'selected_size': 200, 'aggregate_seconds': CEILING, 'requests': {}, 'conditions': {}, 'shards': [],
            'selected_manifest_sha256': sha(preparation / 'nested-200-manifest.json'),
            'pool_inventory': {'selected_size': 400, 'manifest_sha256': sha(preparation / 'nested-400-manifest.json'), 'executable': False},
            'items': public_items}
    for path in sorted((preparation / 'conditions').glob('*.json')):
        c = read(path); cid = c['condition_id']; public_c = {k: v for k, v in c.items() if k not in LOCAL_FIELDS}
        put(output / 'conditions' / path.name, public_c)
        source_worker = preparation / 'workers' / (cid + '.py')
        copy(source_worker, 'historical-workers/' + cid + '.py')
        worker = Path(__file__).parent / 'execution_workers' / (cid + '.py')
        copy(worker, 'workers/' + cid + '.py')
        spec['conditions'][cid] = {'path': 'conditions/' + path.name, 'sha256': digest(public_c),
                                   'original_sha256': sha(path), 'worker': 'workers/' + cid + '.py', 'worker_sha256': sha(worker)}
        for label in ('enriched', 'structured_only'):
            if label == 'structured_only' and cid not in ABLATIONS: continue
            keys = []
            for item in items:
                sid = item['sample_id']; relative = f'requests/{label}/{cid}/{sid}.json'
                source = preparation / 'public' / '200' / label / cid / (sid + '.json')
                copy(source, relative); key = stage_key(sid, cid, label, 1)
                spec['requests'][key] = {'path': relative, 'sha256': sha(source)}; keys.append(key)
                if item['family'] == 'clarification': keys.append(stage_key(sid, cid, label, 2))
            spec['shards'].append({'shard_id': cid + '--' + label, 'condition_id': cid, 'representation': label, 'owner': None, 'keys': keys})
    copy(Path(__file__).parent / 'execution_support.py', 'workers/execution_support.py')
    copy(Path(__file__).parent / 'execution_workers' / 'transformations.json', 'workers/transformations.json')
    # Include ONLY whitelisted inspection files, never historical pilot outputs/replies.
    for p in sorted((confirmation / 'examples').rglob('*')):
        if p.is_file() and p.name in ('request.json', 'rendered-prompt.txt', 'tokenized-prompt.json', 'complete-example.md', 'message-contract.json', 'rendering-summary.json'):
            copy(p, 'inspection/' + p.relative_to(confirmation / 'examples').as_posix())
    for folder in ('templates', 'runtime-stop-evidence'):
        for p in sorted((confirmation / folder).rglob('*')):
            if p.is_file() and not any(marker in p.name for marker in ('actual-pilot', '-observed-stop-events', '-actual-server-launch')):
                copy(p, folder + '/' + p.relative_to(confirmation / folder).as_posix())
    copy(Path(__file__).parent / 'main_public.py', 'procedures/main_public.py')
    copy(Path(__file__), 'procedures/execution_readiness.py')
    copy(Path(__file__).parent / 'public_executor.py', 'procedures/public_executor.py')
    for name in ('return-envelope.schema.json', 'qualification-template.json'):
        copy(Path(__file__).parent / name, name)
    put(output / 'conditional-specification.json', {'version': VERSION, 'stage': 2, 'coordinator_required': True,
        'rules': 'Only coordinator route_reply on parsed ACTUAL first response. Retain original messages and raw assistant verbatim. Exact main_public.continuation assembles recorded reply and public_task_updates. No authored assistant replacement. Context check unchanged; unsupported/absent/premature/invalid first response: unexecuted conditional receipt.',
        'assembly_source': 'procedures/main_public.py', 'conditional_templates': 'uninstantiated; no synthetic assistant output',
        'private_resources': 'not transferred; organizer keeps records and reply evidence'})
    put(output / 'portable-config-template.json', {'version': VERSION, 'executor_id': None, 'bindings': {},
        'binding_fields': ['interpreter', 'environment', 'artifact_cache', 'snapshot_path OR gguf_path/server_path/library_paths', 'device_uuid', 'cuda_visible_devices', 'llama_device', 'nvidia_smi'],
        'qualification': 'central approved fresh receipt required for every assigned condition/representation; no old pilot receipt suffices'})
    put(output / 'execution-spec.json', spec)
    put(output / 'ownership-template.json', {'version': VERSION, 'shards': spec['shards'], 'assigned_owners': 0})
    put(output / 'file-generation-index.json', {'mappings': mappings, 'new_files': 'deterministic public metadata/procedures; no generation/inference'})
    documentation = Path(__file__).parent / 'execution_instructions.md'
    copy(documentation, 'README.md')
    put(output / 'package-manifest.json', {'version': VERSION, 'files': files(output), 'preparation_manifest_sha256': sha(preparation / 'manifest.json'),
         'confirmation_manifest_sha256': sha(confirmation / 'manifest.json'), 'initial_requests': 2200, 'possible_keys': 2640,
         'private_evidence': False, 'credentials': False, 'owners_assigned': 0, 'inference_executed': False})
    return validate_package(output)


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
            if ceiling != CEILING: raise ValueError('fixed aggregate 48-hour ceiling')
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
                     'spec': canonical(spec).decode(), 'fixture': str(fixture), 'ceiling': str(ceiling)}.items():
            obj.db.execute('INSERT INTO meta VALUES(?,?)', (k, v))
        if not fixture and ceiling != CEILING: raise ValueError('fixed aggregate 48-hour ceiling')
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
                    'precision', 'bindings_sha256', 'resolved_condition_sha256', 'render_verification', 'stop_verification', 'task_rehearsal', 'status')
        if any(k not in receipt or receipt[k] is None for k in required) or receipt['status'] != 'task_qualified':
            raise ValueError('incomplete/unqualified receipt')
        hw = receipt['hardware_runtime']
        if any(k not in hw or not hw[k] for k in ('gpu_name', 'device_uuid', 'vram_mib', 'os', 'wsl', 'driver', 'cuda_runtime', 'backend_versions')):
            raise ValueError('hardware/runtime qualification incomplete')
        for evidence in ('render_verification', 'stop_verification', 'task_rehearsal'):
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
        if receipt['tokenizer_files'].get('template_sha256') != condition['template_sha256'] or hw['backend_versions'] != runtime_pin:
            raise ValueError('tokenizer/runtime mismatch')
        h = digest(receipt)
        self.db.execute('INSERT INTO qualifications VALUES(?,?)', (h, canonical(receipt).decode()))
        return h

    def used(self):
        return self.db.execute("SELECT COALESCE(SUM(CASE WHEN actual IS NULL OR state='unknown' THEN MAX(bound,COALESCE(actual,0)) ELSE actual END),0) FROM processes").fetchone()[0]

    def pending(self, assignment, executor):
        body = self.assignment(assignment, executor)
        reserved = {r[0] for r in self.db.execute('SELECT key FROM stages')}
        routed = {r[0] for r in self.db.execute('SELECT key FROM routes')}
        # Unsupported receipts count as considered conditional stages, never become attempts.
        return [k for k in body['keys'] if k not in reserved and (k.endswith('|1') or k in routed and json.loads(self.db.execute('SELECT body FROM routes WHERE key=?', (k,)).fetchone()[0])['status'] == 'supported')]

    def reserve(self, assignment, executor, keys, request_hashes, qualification, loading=600):
        body = self.assignment(assignment, executor); keys = list(keys)
        if not keys or len(set(keys)) != len(keys) or not set(keys) <= set(body['keys']): raise ValueError('assignment filter required')
        qrow = self.db.execute('SELECT body FROM qualifications WHERE hash=?', (qualification,)).fetchone()
        if qrow is None: raise ValueError('unqualified runtime')
        qual = json.loads(qrow[0]); spec = json.loads(self.meta('spec'))
        if any(k.split('|')[1:3] != [qual['condition_id'], qual['representation']] for k in keys) or qual['executor_id'] != executor:
            raise ValueError('qualification condition/executor scope')
        if loading != 600: raise ValueError('frozen per-process overhead allowance')
        bound = loading + sum(read(Path(self.meta('package')) / spec['conditions'][k.split('|')[1]]['path'])['settings']['max_seconds'] for k in keys)
        process = str(uuid.uuid4())
        def op():
            if self.used() + bound > float(self.meta('ceiling')): raise ValueError('aggregate ceiling exhausted including unknown reservations')
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


def resolved_condition(package, cid, bindings, verify_artifacts=True):
    spec = read(Path(package) / 'execution-spec.json'); c = read(Path(package) / spec['conditions'][cid]['path'])
    allowed = LOCAL_FIELDS | {'environment', 'artifact_cache', 'device_uuid', 'cuda_visible_devices', 'llama_device', 'nvidia_smi', 'interpreter'}
    if set(bindings) - allowed: raise ValueError('scientific settings cannot be overridden')
    for name in ('interpreter', 'environment', 'artifact_cache', 'device_uuid', 'cuda_visible_devices', 'nvidia_smi'):
        if name not in bindings or bindings[name] is None: raise ValueError('explicit portable binding required: ' + name)
    result = deepcopy(c)
    for field in LOCAL_FIELDS:
        if field in bindings: result[field] = bindings[field]
    result['local_python'] = bindings['interpreter']
    if 'weight_files' in c:
        root = Path(bindings['snapshot_path'])
        if root.name != c['artifact_revision']: raise ValueError('snapshot revision path')
        if verify_artifacts:
            for name, info in c['weight_files'].items():
                if sha(within(root, name)) != info['sha256']: raise ValueError('pinned artifact mismatch: ' + name)
    else:
        if verify_artifacts and (sha(bindings['gguf_path']) != c['gguf_sha256'] or sha(bindings['server_path']) != c['server_sha256']):
            raise ValueError('pinned GGUF/server mismatch')
        if not bindings.get('llama_device'): raise ValueError('qualified llama CUDA device required')
    return result


def prepare_job(ledger, assignment, executor, qualification, keys, bindings, output):
    """Later authorized coordinator operation. No inference; reservations persist first."""
    prepared_start = time.monotonic()
    package = Path(ledger.meta('package')); spec = read(package / 'execution-spec.json')
    if sha(package / 'package-manifest.json') != ledger.meta('package_hash'): raise ValueError('package identity changed')
    if ledger.meta('fixture') != 'True': validate_package(package)
    if not keys: raise ValueError('explicit assignment stage filter required')
    if len(keys) > 50: raise ValueError('frozen 50-stage process batching ceiling')
    cid, label = keys[0].split('|')[1:3]
    if any(k.split('|')[1:3] != [cid, label] for k in keys): raise ValueError('single condition/representation per process')
    if any(k not in ledger.pending(assignment, executor) for k in keys): raise ValueError('resume only never-reserved eligible keys')
    qual = json.loads(ledger.db.execute('SELECT body FROM qualifications WHERE hash=?', (qualification,)).fetchone()[0])
    if bindings['device_uuid'] != qual['hardware_runtime']['device_uuid']: raise ValueError('device qualification mismatch')
    if bindings['cuda_visible_devices'] != bindings['device_uuid'] or digest(bindings) != qual['bindings_sha256']:
        raise ValueError('qualified portable environment/device binding required')
    requests = []
    for k in keys:
        requests.append(read(package / spec['requests'][k]['path']) if k.endswith('|1') else json.loads(ledger.db.execute('SELECT body FROM routes WHERE key=?', (k,)).fetchone()[0])['request'])
    ticket = ledger.reserve(assignment, executor, keys, dict(zip(keys, map(digest, requests))), qualification)
    output = Path(output); output.mkdir(parents=True, exist_ok=False)
    put(output / 'ticket.json', ticket); put(output / 'assignment.json', ledger.assignment(assignment, executor)); put(output / 'qualification.json', qual)
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
        'execution_scope': 'main',
        'scientific_condition_sha256': spec['conditions'][cid]['sha256'], 'qualification_status': qual['status'],
        'qualification_sha256': qualification, 'assignment_sha256': digest(ledger.assignment(assignment, executor)),
        'hardware_runtime_sha256': digest(qual['hardware_runtime']), 'gpu_name': qual['hardware_runtime']['gpu_name'],
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
        'prepared_unix_seconds': time.time(), 'preparation_elapsed_seconds': time.monotonic() - prepared_start})
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
            if digest(qual) != context['qualification_sha256'] or qual['status'] != 'task_qualified': raise ValueError('executor qualification gate')
            condition = read(job / 'condition.json'); verified = resolved_condition(package, condition['condition_id'], read(job / 'bindings.json'))
            if verified != condition or digest(verified) != qual['resolved_condition_sha256']: raise ValueError('executor resolved config pin')
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
    put(output / 'return-envelope.json', {'version': VERSION, 'kind': 'fixture' if ticket.get('fixture') else 'main',
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
    envelope = None; reasons = []; accepted = []
    try:
        envelope = read(dest / 'return-envelope.json')
        from jsonschema import validate
        from jsonschema.exceptions import ValidationError
        try: validate(envelope, read(Path(__file__).parent / 'return-envelope.schema.json'))
        except ValidationError as exc: raise ValueError('return envelope schema: ' + exc.message) from exc
        if envelope['version'] != VERSION or envelope['kind'] != ('fixture' if ledger.meta('fixture') == 'True' else 'main'):
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
        spec = json.loads(ledger.meta('spec')); public_c = read(Path(ledger.meta('package')) / spec['conditions'][qual['condition_id']]['path'])
        returned_c = {k: v for k, v in read(dest / 'condition.json').items() if k not in LOCAL_FIELDS}
        if returned_c != public_c: raise ValueError('scientific condition changed')
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
                if raw.get('cpu_fallback') is not False or raw.get('execution_version') != VERSION or raw.get('execution_scope') != 'main' or raw.get('qualification_status') != 'task_qualified': raise ValueError('unqualified runtime/fallback/rehearsal scope')
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


def coordinate_reply(ledger, key, preparation, output):
    from .spq06 import parse_answer
    from .main_public import continuation
    if not key.endswith('|1'): raise ValueError('initial clarification stage required')
    raw = canonical_records(ledger).get(key)
    if raw is None: raise ValueError('canonical nonconflicted first result required')
    spec = json.loads(ledger.meta('spec')); sid, cid, label, _ = key.split('|')
    selected = read(Path(preparation) / 'nested-200-manifest.json')
    item = next(x for x in selected['items'] if x['sample_id'] == sid)
    if item['family'] != 'clarification' or sha(Path(preparation) / 'nested-200-manifest.json') != spec['selected_manifest_sha256']:
        raise ValueError('frozen clarification record required')
    record = read(Path(preparation) / item['private_record']); condition = read(Path(preparation) / 'conditions' / (cid + '.json'))
    if digest(record) != item['record_sha256'] or sha(Path(preparation) / 'conditions' / (cid + '.json')) != spec['conditions'][cid]['original_sha256']:
        raise ValueError('frozen organizer evidence/config changed')
    request = None; route_reason = raw['completion_status']
    try:
        if raw['completion_status'] == 'completed':
            from .heldout_scope import formal_scope
            scope = read(Path(preparation) / 'private/generation-scope.json')
            with formal_scope(scope['candidates'], scope['excluded_groups']):
                response, diagnostics = parse_answer(raw['raw_output'])
                request, route = continuation(record, condition, raw['raw_output'], response, label == 'structured_only')
                route_reason = route['status']
    except (ValueError, KeyError, TypeError) as exc: route_reason = type(exc).__name__ + ': ' + str(exc)
    second_key = stage_key(sid, cid, label, 2)
    receipt = {'version': VERSION, 'key': second_key, 'initial_key': key, 'actual_raw': raw['raw_output'],
        'initial_result_sha256': digest(raw), 'status': 'supported' if request else 'unexecuted_conditional', 'reason': route_reason,
        'request': request, 'request_sha256': digest(request) if request else None}
    ledger.db.execute('INSERT INTO routes VALUES(?,?)', (second_key, canonical(receipt).decode()))
    # Only public message update leaves organizer. No private record/gold is exported.
    put(Path(output), receipt)
    return receipt


def analysis_bridge(ledger, original_plan, output):
    """Organizer only. Fixed denominators/endpoints/bootstrap delegated unchanged."""
    from .main_analysis import analyse
    from .spq06 import parse_answer
    output = Path(output); output.mkdir(parents=True, exist_ok=False)
    plan = read(original_plan)
    if sha(Path(plan['preparation']) / 'nested-200-manifest.json') != json.loads(ledger.meta('spec'))['selected_manifest_sha256']:
        raise ValueError('analysis selection mismatch')
    put(output / 'main-run-plan.json', plan)
    parsed = []; records = canonical_records(ledger)
    for key, raw in records.items():
        sid, cid, label, stage = key.split('|'); job = output / 'jobs' / f'{cid}--{label}--stage{stage}--canonical'
        put(job / 'results' / f'{sid}-stage{stage}.json', raw)
        put(job / 'reservations' / f'{sid}-stage{stage}.json', {'central_stage_key': key, 'process': raw['process_reservation']})
        value = None; diagnostics = None; failure = None
        try: value, diagnostics = parse_answer(raw['raw_output'])
        except (ValueError, TypeError) as exc: failure = type(exc).__name__ + ': ' + str(exc)
        parsed.append({'stage_key': key, 'parsed_response': value, 'parser_diagnostics': diagnostics, 'parser_failure': failure,
                       'execution_status': raw['completion_status'], 'scientific_scoring_eligibility': raw['completion_status'] == 'completed'})
    versions = {name: sha(Path(__file__).parent / (name + '.py')) for name in ('spq06', 'scoring', 'explanation_evaluation', 'clarification_evaluation', 'main_analysis')}
    put(output / 'central-parsed-records.json', {'version': VERSION, 'versions_sha256': versions, 'stages': parsed,
        'conflicted_keys': conflicts(ledger), 'invalid_returns': list(ledger.db.execute('SELECT key,reason FROM returns WHERE valid=0')),
        'reservation_states': [{'stage_key': k, 'process': p, 'request_sha256': h, 'state': s} for k, p, h, s in ledger.db.execute('SELECT key,process,request_hash,state FROM stages')],
        'process_accounting': [{'id': i, 'assignment': a, 'bound_seconds': b, 'measured_seconds': t, 'state': s} for i, a, b, t, s in ledger.db.execute('SELECT id,assignment,bound,actual,state FROM processes')],
        'conditional_receipts': [{'stage_key': k, 'status': readout['status'], 'reason': readout['reason']} for k, body in ledger.db.execute('SELECT key,body FROM routes') for readout in [json.loads(body)]]})
    if not records:
        raise ValueError('no canonical main records; no results fabricated')
    return analyse(output, output / 'analysis')


def zip_export(root, output):
    root, output = Path(root), Path(output)
    with zipfile.ZipFile(output, 'x', compression=zipfile.ZIP_DEFLATED) as archive:
        for p in sorted(root.rglob('*')):
            if p.is_file(): archive.write(p, p.relative_to(root).as_posix())
    return sha(output)


def main():
    p = argparse.ArgumentParser(); sub = p.add_subparsers(dest='command', required=True)
    e = sub.add_parser('prepare-package'); e.add_argument('--preparation', required=True); e.add_argument('--confirmation', required=True); e.add_argument('--output', required=True)
    v = sub.add_parser('validate-package'); v.add_argument('--package', required=True)
    z = sub.add_parser('export'); z.add_argument('--package', required=True); z.add_argument('--output', required=True)
    r = sub.add_parser('export-return'); r.add_argument('--job', required=True); r.add_argument('--output', required=True)
    for name in ('init-ledger', 'issue', 'approve-qualification', 'pending', 'prepare-job', 'import', 'route', 'analyse'):
        a = sub.add_parser(name); a.add_argument('--ledger', required=True)
        if name == 'init-ledger': a.add_argument('--package', required=True)
        if name in ('issue', 'pending', 'prepare-job'): a.add_argument('--executor', required=True)
        if name == 'issue': a.add_argument('--shard', action='append', required=True); a.add_argument('--output', required=True)
        if name == 'approve-qualification': a.add_argument('--receipt', required=True)
        if name in ('pending', 'prepare-job'): a.add_argument('--assignment', required=True)
        if name == 'prepare-job':
            a.add_argument('--qualification', required=True); a.add_argument('--keys', required=True); a.add_argument('--bindings', required=True); a.add_argument('--output', required=True)
        if name == 'import': a.add_argument('--source', required=True); a.add_argument('--output', required=True)
        if name == 'route': a.add_argument('--key', required=True); a.add_argument('--preparation', required=True); a.add_argument('--output', required=True)
        if name == 'analyse': a.add_argument('--plan', required=True); a.add_argument('--output', required=True)
    l = sub.add_parser('launch'); l.add_argument('--job', required=True); l.add_argument('--package', required=True); l.add_argument('--authorize-main', action='store_true', required=True)
    a = p.parse_args()
    if a.command == 'prepare-package': result = export_package(a.preparation, a.confirmation, a.output)
    elif a.command == 'validate-package': result = validate_package(a.package)
    elif a.command == 'export': validate_package(a.package); result = {'zip_sha256': zip_export(a.package, a.output)}
    elif a.command == 'export-return': result = {'return_sha256': export_return(a.job, a.output)}
    elif a.command == 'launch': launch_job(a.job, a.package); result = {'job': a.job}
    elif a.command == 'init-ledger': Ledger.create(a.ledger, a.package).db.close(); result = {'ledger': a.ledger}
    else:
        ledger = Ledger(a.ledger)
        if a.command == 'issue': result = ledger.issue(a.executor, a.shard); put(a.output, result)
        elif a.command == 'approve-qualification': result = {'qualification_sha256': ledger.approve_qualification(read(a.receipt))}
        elif a.command == 'pending': result = {'never_reserved_keys': ledger.pending(a.assignment, a.executor)}
        elif a.command == 'prepare-job': result = prepare_job(ledger, a.assignment, a.executor, a.qualification, read(a.keys), read(a.bindings), a.output)
        elif a.command == 'import': result = import_return(ledger, a.source, a.output)
        elif a.command == 'route': result = coordinate_reply(ledger, a.key, a.preparation, a.output)
        elif a.command == 'analyse': result = analysis_bridge(ledger, a.plan, a.output); result = {'scored_rows': len(result['items'])}
        ledger.db.close()
    print(canonical(result if a.command != 'prepare-package' and a.command != 'validate-package' else {'verified_files': len(result['files']), 'initial_requests': result['initial_requests']}).decode())


if __name__ == '__main__': main()
