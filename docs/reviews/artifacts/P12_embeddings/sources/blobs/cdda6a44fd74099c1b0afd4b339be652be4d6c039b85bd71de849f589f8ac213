"""Bounded, public-only frozen embedding preparation; no training or providers."""
from p12_common import *
from collections import Counter
from dataclasses import asdict
from datetime import datetime, timezone
import math
import os
import shutil
import time

from phi_jepa.integration.contracts import enriched_context
from phi_jepa.providers.cache import FrozenOutputCache
from phi_jepa.providers.context import ContextEncoder, parse_notes
from phi_jepa.providers.enrichment_budget import atomic_json

RUN = NATIVE/'p12-embedding-preparation-01'
EXPORT = ROOT/'docs/reviews/artifacts/P12_embeddings'
RECOVERY = NATIVE/'p12-enrichment-recovery-01/coverage-after-recovery.json'


def now():
    return datetime.now(timezone.utc).isoformat()


def source_files():
    # Independent of local-answer code: the user is diagnosing Llama concurrently.
    paths = [Path(__file__), ROOT/'tools/p12_common.py', ROOT/'tools/p12_enrichment.py',
             ROOT/'tools/p10_common.py', ROOT/'src/phi_jepa/artifacts.py']
    paths += [ROOT/f'src/phi_jepa/{p}.py' for p in (
        'providers/qwen', 'providers/context', 'providers/contracts', 'providers/cache',
        'providers/enrichment_budget', 'integration/contracts', 'integration/readers',
        'models/context_projection')]
    return {str(p.relative_to(ROOT)): file_hash(p) for p in paths}


def identity(settings, text, tokens):
    return {'kind': 'frozen_E', 'version': 1, 'settings': settings,
            'serialization': 'P02a-Q-C-enrichment-v1', 'context_mode': 'enriched',
            'text': text, 'tokens_sha256': digest(tuple(tokens))}


def validate_vector(value, row):
    if (value.get('request_sha256') != row['embedding_request_sha256'] or
            value.get('context_sha256') != row['context_sha256'] or
            value.get('token_count') != row['token_count']):
        raise ValueError('embedding identity mismatch')
    values = value.get('values', [])
    if len(values) != 1024 or any(type(v) not in (int, float) or not math.isfinite(v) for v in values):
        raise ValueError('invalid embedding vector')
    if not math.isclose(sum(v*v for v in values), 1., rel_tol=1e-5, abs_tol=1e-5):
        raise ValueError('embedding normalization mismatch')


def validate_population(rows):
    if len({r['sample_id'] for r in rows}) != len(rows):
        raise ValueError('duplicate selected question')
    counts = Counter(r['scope'] for r in rows)
    if counts != {'train_validation': 8038, 'confirmation': 500}:
        raise ValueError('frozen population changed')
    groups = {}
    for r in rows:
        if (r['split'] in ('train', 'validation')) != (r['scope'] == 'train_validation'):
            raise ValueError('scope/split mismatch')
        for key in ((r['domain'], r['scenario_id']), ('group', r['split_group'])):
            partition = (r['domain'], r['split'])
            if key in groups and groups[key] != partition:
                raise ValueError('scenario-group split leakage')
            groups[key] = partition


def verified_notes(problem, origin, config, asset):
    from p12_enrichment import request_identity
    path = Path(origin['cache_file'])
    if file_hash(path) != origin['cache_sha256']:
        raise ValueError('enrichment origin changed')
    for attempts in (config['max_attempts_per_request'], 1):
        request = request_identity(problem, {**config, 'max_attempts_per_request': attempts}, asset)
        if digest(request) != origin['request_sha256']:
            continue
        output = FrozenOutputCache(path.parent).read(request)
        if not output or output.get('metadata', {}).get('returned_model') != config['model']:
            raise ValueError('enrichment model binding failed')
        return parse_notes(problem, output['text'])
    raise ValueError('enrichment public request binding failed')


def frozen_config():
    cfg = load(RUN/'config.json')
    if source_files() != cfg['source_files']:
        raise ValueError('embedding implementation changed')
    for path, expected in cfg['input_files'].items():
        if file_hash(path) != expected:
            raise ValueError('frozen preparation input changed')
    for path, expected in cfg['encoder_snapshot_files'].items():
        if file_hash(path) != expected:
            raise ValueError('frozen encoder snapshot changed')
    if file_hash(RUN/'inventory.json') != cfg['inventory_sha256']:
        raise ValueError('frozen embedding inventory changed')
    return cfg


def prepare():
    from p10_common import guard_deployment_io
    from p12_enrichment import public_population, policy
    from phi_jepa.providers.qwen import QwenEncoder
    guard_deployment_io()
    if (RUN/'config.json').exists():
        frozen_config();print('Preparation already frozen.');return
    started = time.perf_counter()
    prior = load(RECOVERY);validate_population(prior)
    origins = {r['sample_id']: r for r in prior}
    config, asset = policy()
    backend = QwenEncoder(str(NATIVE/'model-cache'), runtime_versions=load(ROOT/'configs/model_context_p02b.json')['encoder']['runtime_versions'], load_model=False)
    settings = asdict(backend.settings)
    roots = sorted(p.parent for p in NATIVE.glob('**/encoding-report.json') if load(p).get('settings') == settings and p.parent != RUN)
    inventory = []
    for meta, problem in public_population():
        original = origins[problem.sample_id]
        if any(meta[k] != original[k] for k in ('domain', 'split', 'scenario_id', 'split_group', 'public_sha256')):
            raise ValueError('original selection identity changed')
        if digest(problem.input) != original['public_sha256']:
            raise ValueError('public input changed')
        notes = verified_notes(problem, original['compatible_origin'], config, asset)
        candidate_note = Path(original['compatible_origin']['cache_file']).parent.parent/'enrichment'/f'{problem.sample_id}.json'
        if not candidate_note.exists() or load(candidate_note) != notes:
            candidate_note = RUN/'enrichment'/f'{problem.sample_id}.json'
            atomic_json(candidate_note, notes)
        text = enriched_context(problem, notes, problem.input['observation_cutoff'])
        tokens = backend.tokenize(text)
        if not tokens or len(tokens) > settings['max_length']:
            raise ValueError(f'overlength: {problem.sample_id}, {len(tokens)}')
        row = {**original, 'enrichment_path': str(candidate_note), 'enrichment_file_sha256': file_hash(candidate_note),
               'embedding_request_sha256': digest(identity(settings, text, tokens)),
               'context_sha256': digest(text), 'token_count': len(tokens), 'embedding_path': None, 'embedding_file_sha256': None}
        for root in roots:
            path = root/'embeddings/enriched'/f'{problem.sample_id}.json'
            if not path.exists():
                continue
            try:
                validate_vector(load(path), row)
            except ValueError:
                continue
            row.update(embedding_path=str(path), embedding_file_sha256=file_hash(path));break
        inventory.append(row)
        if len(inventory) % 500 == 0:
            print({'preflight_records': len(inventory), 'reused': sum(bool(r['embedding_path']) for r in inventory)}, flush=True)
    validate_population(inventory)
    if {r['sample_id'] for r in inventory} != set(origins):
        raise ValueError('missing selected questions')
    atomic_json(RUN/'inventory.json', inventory)
    inputs = [RECOVERY, OUT/'selection.json', OUT/'confirmation-public.json', OUT/'confirmation-cohort.json',
              ROOT/'configs/model_context_p02b.json', ROOT/'configs/model_training_p02a.json', ROOT/'docs/assets/p02b_enrichment_v1.json']
    files = source_files()
    for path, sha in files.items():
        target = RUN/'sources/blobs'/sha;target.parent.mkdir(parents=True, exist_ok=True)
        if not target.exists():shutil.copyfile(ROOT/path, target)
    cfg = {'authorization': 'User: Embedding preparation can continue alongside my diagnostics of the Llama output failures. Proceed.',
           'created_at_utc': now(), 'settings': settings, 'source_files': files,
           'commit': subprocess.check_output(['git', 'rev-parse', 'HEAD'], cwd=ROOT, text=True).strip(),
           'input_files': {str(p): file_hash(p) for p in inputs}, 'inventory_sha256': file_hash(RUN/'inventory.json'),
           'encoder_snapshot_files': {str(p): file_hash(p) for p in (NATIVE/'model-cache/models--Qwen--Qwen3-Embedding-0.6B/snapshots'/settings['model_revision']).glob('*') if p.is_file()},
           'maximum_model_calls': sum(not r['embedding_path'] for r in inventory),
           'encoding_seconds_cap': 3600, 'per_call_seconds_cap': 120, 'execution_wall_seconds_cap': 5400,
           'artifact_bytes_cap': 2000000000, 'retries': 0, 'paid_calls': 0, 'training_enabled': False,
           'preflight_seconds': time.perf_counter()-started, 'reuse_counts': dict(Counter(r['scope'] for r in inventory if r['embedding_path'])),
           'missing_counts': dict(Counter(r['scope'] for r in inventory if not r['embedding_path'])),
           'token_length_min': min(r['token_count'] for r in inventory), 'token_length_max': max(r['token_count'] for r in inventory)}
    atomic_json(RUN/'config.json', cfg)
    print({k: cfg[k] for k in ('maximum_model_calls', 'reuse_counts', 'missing_counts', 'token_length_min', 'token_length_max', 'preflight_seconds')}, flush=True)


def check_budget(cfg, attempts, seconds, deadline):
    if time.time() >= deadline:raise TimeoutError('embedding execution wall window expired')
    if attempts >= cfg['maximum_model_calls']:raise ValueError('embedding call cap reached')
    if seconds + cfg['per_call_seconds_cap'] > cfg['encoding_seconds_cap']:raise TimeoutError('embedding time reservation exceeds cap')


def run():
    import fcntl
    import signal
    import torch
    from p10_common import guard_deployment_io
    from p12_enrichment import public_population
    from phi_jepa.providers.qwen import QwenEncoder
    guard_deployment_io();torch.set_num_threads(2)
    cfg = frozen_config();rows = load(RUN/'inventory.json');by_id = {r['sample_id']: r for r in rows}
    with (RUN/'worker.lock').open('a') as lock:
        fcntl.flock(lock, fcntl.LOCK_EX | fcntl.LOCK_NB)
        if (RUN/'completion.json').exists():
            print('Embedding run already complete; no model calls.');return
        attempts = {p.stem: load(p) for p in (RUN/'attempts').glob('*.json')}
        for sid, value in attempts.items():
            if value['status'] != 'success':raise ValueError('unresolved/failed embedding attempt; no automatic retry')
            validate_vector(load(RUN/'embeddings/enriched'/f'{sid}.json'), by_id[sid])
        seconds = sum(a['seconds'] for a in attempts.values());calls = len(attempts)
        window = RUN/'window.json'
        if not window.exists():atomic_json(window, {'deadline_unix': time.time()+cfg['execution_wall_seconds_cap'], 'started_at_utc': now()})
        deadline = load(window)['deadline_unix']
        check_budget(cfg, calls, seconds, deadline)
        def expired(*_):raise TimeoutError('embedding per-call/wall deadline reached')
        signal.signal(signal.SIGALRM, expired)
        started = time.perf_counter();backend = None;load_seconds = 0.;completed = sum(bool(r['embedding_path']) for r in rows) + calls
        def status(state):
            atomic_json(RUN/'status.json', {'status': state, 'updated_at_utc': now(), 'pid': os.getpid(),
                'completed': completed, 'total': len(rows), 'new_model_calls': calls, 'encoding_seconds': seconds,
                'model_load_seconds': load_seconds, 'remaining': len(rows)-completed, 'paid_calls': 0})
        try:
            status('running')
            for meta, problem in public_population():
                row = by_id[problem.sample_id];sid = problem.sample_id
                if row['embedding_path']:
                    if file_hash(row['embedding_path']) != row['embedding_file_sha256']:raise ValueError('reused vector changed')
                    continue
                if sid in attempts:continue
                check_budget(cfg, calls, seconds, deadline)
                # Do not overlap an active local answer-model process. Keep the
                # small encoder loaded while waiting, without encoding calls.
                active = subprocess.check_output(['nvidia-smi', '--query-compute-apps=pid,process_name', '--format=csv,noheader,nounits'], text=True) if backend is None or calls % 25 == 0 else ''
                others = [line for line in active.splitlines() if line.strip() and line.split(',')[0].strip() != str(os.getpid())]
                if others:
                    status('waiting_for_gpu')
                    while others:
                        if time.time() >= deadline:raise TimeoutError('GPU wait exhausted wall cap')
                        time.sleep(5)
                        active = subprocess.check_output(['nvidia-smi', '--query-compute-apps=pid,process_name', '--format=csv,noheader,nounits'], text=True)
                        others = [line for line in active.splitlines() if line.strip() and line.split(',')[0].strip() != str(os.getpid())]
                    status('running')
                if backend is None:
                    load_start = time.perf_counter()
                    backend = QwenEncoder(str(NATIVE/'model-cache'), runtime_versions=load(ROOT/'configs/model_context_p02b.json')['encoder']['runtime_versions'])
                    load_seconds = time.perf_counter()-load_start
                    if asdict(backend.settings) != cfg['settings']:raise ValueError('encoder settings changed')
                if file_hash(row['enrichment_path']) != row['enrichment_file_sha256']:raise ValueError('notes changed')
                notes = load(row['enrichment_path'])
                torch.cuda.synchronize();torch.cuda.reset_peak_memory_stats()
                attempt_path = RUN/'attempts'/f'{sid}.json';call_start = time.perf_counter()
                atomic_json(attempt_path, {'status': 'reserved', 'seconds': cfg['per_call_seconds_cap'], 'request_sha256': row['embedding_request_sha256'], 'started_at_utc': now()})
                calls += 1
                signal.setitimer(signal.ITIMER_REAL, min(cfg['per_call_seconds_cap'], deadline-time.time()))
                try:
                    value = asdict(ContextEncoder(backend).encode(problem, problem.input['observation_cutoff'], mode='enriched', enrichment=notes))
                    torch.cuda.synchronize();validate_vector(value, row)
                    atomic_json(RUN/'embeddings/enriched'/f'{sid}.json', value)
                    elapsed = time.perf_counter()-call_start
                    record = {'status': 'success', 'seconds': elapsed, 'domain': row['domain'], 'scope': row['scope'],
                              'token_count': value['token_count'], 'request_sha256': value['request_sha256'],
                              'peak_allocated_bytes': torch.cuda.max_memory_allocated(), 'peak_reserved_bytes': torch.cuda.max_memory_reserved()}
                    atomic_json(attempt_path, record);seconds += elapsed;completed += 1
                except BaseException as exc:
                    atomic_json(attempt_path, {'status': 'failed', 'failure': type(exc).__name__, 'seconds': max(time.perf_counter()-call_start, cfg['per_call_seconds_cap'])})
                    raise
                finally:signal.setitimer(signal.ITIMER_REAL, 0)
                if calls % 25 == 0:
                    status('running');print({'completed': completed, 'total': len(rows), 'calls': calls, 'encoding_seconds': round(seconds, 2)}, flush=True)
                if calls % 500 == 0 and sum(p.stat().st_size for p in RUN.rglob('*') if p.is_file()) > cfg['artifact_bytes_cap']:
                    raise ValueError('embedding artifact cap exceeded')
            atomic_json(RUN/'encoding-report.json', {'settings': cfg['settings'], 'calls': calls, 'encoding_seconds': seconds, 'paid_calls': 0})
            atomic_json(RUN/'completion.json', {'status': 'complete', 'new_model_calls': calls, 'encoding_seconds': seconds,
                'model_load_seconds': load_seconds, 'execution_wall_seconds': time.perf_counter()-started, 'completed_at_utc': now(), 'paid_calls': 0})
            status('complete')
        except BaseException:
            status('stopped');raise


def audit():
    from p10_common import guard_deployment_io
    from p12_enrichment import public_population, policy
    from phi_jepa.providers.qwen import QwenEncoder
    guard_deployment_io();cfg = frozen_config();rows = load(RUN/'inventory.json');by_id = {r['sample_id']: r for r in rows}
    config, asset = policy()
    encoder = QwenEncoder(str(NATIVE/'model-cache'), runtime_versions=load(ROOT/'configs/model_context_p02b.json')['encoder']['runtime_versions'], load_model=False)
    if asdict(encoder.settings) != cfg['settings']:raise ValueError('audit encoder settings changed')
    verified = [];origins = []
    for meta, problem in public_population():
        row = by_id[problem.sample_id]
        notes = verified_notes(problem, row['compatible_origin'], config, asset)
        if file_hash(row['enrichment_path']) != row['enrichment_file_sha256'] or load(row['enrichment_path']) != notes:raise ValueError('notes mismatch')
        text = enriched_context(problem, notes, problem.input['observation_cutoff']);tokens = encoder.tokenize(text)
        if (len(tokens), digest(text), digest(identity(cfg['settings'], text, tokens))) != (row['token_count'], row['context_sha256'], row['embedding_request_sha256']):raise ValueError('fresh context/token audit mismatch')
        path = Path(row['embedding_path']) if row['embedding_path'] else RUN/'embeddings/enriched'/f'{problem.sample_id}.json'
        validate_vector(load(path), row)
        if row['embedding_path'] and file_hash(path) != row['embedding_file_sha256']:raise ValueError('historical vector changed')
        verified.append({**row, 'embedding_path': str(path), 'embedding_file_sha256': file_hash(path)})
        origins.append({'sample_id': problem.sample_id, 'domain': row['domain'], 'split': row['split'], 'scope': row['scope'], 'status': 'verified', **row['compatible_origin']})
    validate_population(verified)
    for scope, prefix in (('train_validation', ''), ('confirmation', 'confirmation-')):
        atomic_json(RUN/f'{prefix}cache-coverage.json', [r for r in verified if r['scope'] == scope])
        selected = [r for r in origins if r['scope'] == scope]
        atomic_json(RUN/f'{prefix}enrichment-origin-audit.json', {'records': selected, 'counts': {'verified': len(selected)}})
    attempts = [load(p) for p in (RUN/'attempts').glob('*.json')]
    report = {'status': 'complete', 'verified_at_utc': now(), 'coverage': dict(Counter(r['scope'] for r in verified)),
              'by_partition': dict(Counter(r['domain']+'/'+r['split'] for r in verified)), 'missing': 0,
              'reused_vectors': sum(bool(r['embedding_path']) for r in rows), 'new_vectors': len(attempts),
              'all_attempts_successful': all(r['status'] == 'success' for r in attempts),
              'encoding_seconds': sum(r['seconds'] for r in attempts),
              'input_tokens_new': sum(r['token_count'] for r in attempts),
              'peak_allocated_bytes': max(r['peak_allocated_bytes'] for r in attempts),
              'peak_reserved_bytes': max(r['peak_reserved_bytes'] for r in attempts),
              'token_length_min': cfg['token_length_min'], 'token_length_max': cfg['token_length_max'],
              'historical_embeddings_unchanged': True, 'test_outcomes_opened': False, 'paid_calls': 0, 'training_started': False,
              'config_sha256': file_hash(RUN/'config.json'), 'per_scope': {}}
    for scope in ('train_validation', 'confirmation'):
        items = [r for r in attempts if r['scope'] == scope]
        report['per_scope'][scope] = {'new_vectors': len(items), 'encoding_seconds': sum(r['seconds'] for r in items), 'input_tokens': sum(r['token_count'] for r in items)}
    atomic_json(RUN/'audit.json', report)
    EXPORT.mkdir(parents=True, exist_ok=True)
    for p in RUN.glob('*.json'):
        shutil.copyfile(p, EXPORT/p.name)
    for p in RUN.glob('*.log'):
        shutil.copyfile(p, EXPORT/p.name)
    shutil.copytree(RUN/'sources', EXPORT/'sources', dirs_exist_ok=True)
    atomic_json(EXPORT/'artifact-index.json', {'native_root': str(RUN), 'files': {str(p.relative_to(EXPORT)): file_hash(p) for p in EXPORT.rglob('*') if p.is_file() and p.name != 'artifact-index.json'}})
    print(json.dumps(report, indent=2))


if __name__ == '__main__':
    {'prepare': prepare, 'run': run, 'audit': audit}[sys.argv[1]]()
