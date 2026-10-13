"""Authorized native-first-turn reconciliation and prospective continuation issuance.

No historical central tickets/qualifications are synthesized. Native bytes live in
an immutable transport registry; charges use the existing executor budget guards.
New stage-2 tickets are conditional on real remote metadata before any model call.
"""
import argparse
import hashlib
import json
import math
import shutil
import time
import uuid
import zipfile
from datetime import datetime, timezone
from pathlib import Path

from . import execution_adapter as a, main_allocation, main_record_index

VERSION = 'SPQ06-native-reconciliation/1.0.0'
CIDS = ('deepseek_r1_distill_qwen32b', 'gemma3_27b_qat_direct', 'gemma3_27b_qat_cot')


def install(ledger):
    ledger.db.executescript('''
      CREATE TABLE IF NOT EXISTS native_registry(id TEXT PRIMARY KEY,body TEXT NOT NULL);
      CREATE TABLE IF NOT EXISTS native_entries(key TEXT PRIMARY KEY,registry TEXT NOT NULL,body TEXT NOT NULL);
      CREATE TABLE IF NOT EXISTS native_charges(id TEXT PRIMARY KEY,registry TEXT NOT NULL,body TEXT NOT NULL);
      CREATE TABLE IF NOT EXISTS native_jobs(key TEXT PRIMARY KEY,process TEXT UNIQUE NOT NULL,body TEXT NOT NULL);
      CREATE TABLE IF NOT EXISTS native_job_payloads(process TEXT PRIMARY KEY,body TEXT NOT NULL);
      CREATE TRIGGER IF NOT EXISTS native_initial_no_rerun BEFORE INSERT ON stages
        WHEN EXISTS(SELECT 1 FROM native_entries WHERE key=NEW.key)
        BEGIN SELECT RAISE(ABORT,'reconciled native first turn cannot be rerun'); END;
      CREATE TRIGGER IF NOT EXISTS native_registry_immutable BEFORE UPDATE ON native_registry
        BEGIN SELECT RAISE(ABORT,'native registry immutable'); END;
      CREATE TRIGGER IF NOT EXISTS native_entries_immutable BEFORE UPDATE ON native_entries
        BEGIN SELECT RAISE(ABORT,'native provenance immutable'); END;
      CREATE TRIGGER IF NOT EXISTS native_registry_no_delete BEFORE DELETE ON native_registry
        BEGIN SELECT RAISE(ABORT,'native registry immutable'); END;
      CREATE TRIGGER IF NOT EXISTS native_entries_no_delete BEFORE DELETE ON native_entries
        BEGIN SELECT RAISE(ABORT,'native provenance immutable'); END;
    ''')


def budgets(ledger):
    return {'allocations': dict(ledger.db.execute('SELECT owner,ceiling FROM executor_allocations')),
            'shared': float(ledger.meta('ceiling'))}


def exists(ledger, name):
    return bool(ledger.db.execute("SELECT 1 FROM sqlite_master WHERE type='table' AND name=?", (name,)).fetchone())


def canonical_native(ledger):
    if not exists(ledger, 'native_entries'):
        return {}
    records = {}
    # A transport hash is checked once per registry per lookup, never cached across calls.
    for identity, body in ledger.db.execute('SELECT id,body FROM native_registry'):
        registry = json.loads(body)
        source = Path(registry['source'])
        if a.sha(source) != identity:
            raise ValueError('immutable native archive changed')
        with zipfile.ZipFile(source) as archive:
            for key, entry_body in ledger.db.execute('SELECT key,body FROM native_entries WHERE registry=?', (identity,)):
                entry = json.loads(entry_body)
                data = archive.read(entry['result'])
                if hashlib.sha256(data).hexdigest() != entry['raw_file_sha256']:
                    raise ValueError('immutable native result changed')
                if ledger.db.execute('SELECT 1 FROM returns WHERE key=?', (key,)).fetchone():
                    # Do not prefer native or newly received conflicting first-turn transports.
                    continue
                records[key] = json.loads(data)
    return records


def inspect_native(source, original_raw, spec, package, fixture=False):
    """Validate actual source links; return immutable entries and explicit charges."""
    if not fixture:
        a.validate_package(package)
    expected = {k for k in spec['requests'] if k.split('|')[1] in CIDS}
    with zipfile.ZipFile(original_raw) as old:
        old_results = {json.loads(old.read(n))['stage_key']: old.read(n) for n in old.namelist() if n.endswith('.json')}
    entries, processes, development, seeds = [], [], [], {}
    with zipfile.ZipFile(source) as archive:
        names = [n for n in archive.namelist() if not n.endswith('/')]
        if len(names) != len(set(names)) or archive.testzip() is not None or any(n.startswith(('/', '\\')) or '..' in n.split('/') or '\\' in n for n in names):
            raise ValueError('unsafe or corrupt native archive')
        read = lambda n: json.loads(archive.read(n))
        roots = sorted(n[:-len('/condition.json')] for n in names if n.startswith('jobs/') and n.endswith('/condition.json'))
        for root in roots:
            condition = read(root + '/condition.json'); cid = condition['condition_id']; pin = spec['conditions'][cid]
            if cid not in CIDS:
                raise ValueError('outside authorized native conditions')
            if {k: v for k, v in condition.items() if k not in a.LOCAL_FIELDS} != a.read(Path(package) / pin['path']):
                raise ValueError('native scientific condition changed')
            context = read(root + '/execution-context.json'); reservation = read(root + '/local-reservation.json')
            outcome = read(root + '/process-outcome.json'); runtime = read(root + '/worker-output/runtime.json')
            launch = read(root + '/launch.json'); parent = root.rsplit('/batch-', 1)[0]
            qual_path = parent + '/local-qualification.json' if cid.startswith('deepseek') else root + '/local-qualification.json'
            assignment_path = parent + '/local-assignment.json' if cid.startswith('deepseek') else root + '/local-assignment.json'
            qual, assignment = read(qual_path), read(assignment_path)
            if a.digest(qual) != context['qualification_sha256'] or a.digest(assignment) != context['assignment_sha256'] or a.digest(condition) != context['resolved_condition_sha256']:
                raise ValueError('native qualification/assignment/condition hash mismatch')
            if reservation['process'] != context['process_reservation'] or runtime['process_reservation'] != reservation['process'] or runtime['qualification_sha256'] != context['qualification_sha256']:
                raise ValueError('native process identity mismatch')
            if context.get('organizer_approved') is not False or reservation.get('shared_ledger') is not False:
                raise ValueError('preserve actual independent provenance; no assumed central authority')
            if context['worker_sha256'] != pin['worker_sha256'] or a.digest(context['hardware_runtime']) != context['hardware_runtime_sha256']:
                raise ValueError('native worker/hardware pin mismatch')
            elapsed = outcome['elapsed_seconds']
            if outcome['exit_code'] != 0 or not math.isfinite(elapsed) or elapsed < 0:
                raise ValueError('native process not known completed')
            batch_keys = set()
            request_list = read(root + '/requests.json')
            requests = {a.stage_key(q['sample_id'], q['condition_id'], q['input_condition'], q.get('stage', 1)): q for q in request_list}
            for path in sorted(n for n in names if n.startswith(root + '/worker-output/results/')):
                data = archive.read(path); raw = json.loads(data); key = raw['stage_key']; stem = path.rsplit('/', 1)[1]
                request_path = root + '/worker-output/executed-requests/' + stem
                prompt_path = root + '/worker-output/tokenized-prompts/' + stem
                request, prompt = read(request_path), read(prompt_path)
                if key not in expected or key not in old_results or data != old_results[key] or not key.endswith('|1'):
                    raise ValueError('native results differ from authorized original first turns')
                if a.digest(request) != raw['request_sha256'] or raw['request_sha256'] != spec['requests'][key]['sha256'] or requests.get(key) != request or request['tools'] != []:
                    raise ValueError('native exact public request mismatch')
                for field in ('assignment_sha256', 'qualification_sha256', 'hardware_runtime_sha256', 'worker_sha256', 'scientific_condition_sha256'):
                    if raw[field] != context[field]: raise ValueError('native context link mismatch: ' + field)
                if raw['process_reservation'] != context['process_reservation'] or raw['stage_reservation'] != context['stage_reservations'][key]:
                    raise ValueError('native stage identity mismatch')
                if not isinstance(prompt['prompt'], str) or not isinstance(prompt['token_ids'], list) or len(prompt['token_ids']) != raw['input_tokens'] or len(raw['output_token_ids']) != raw['output_tokens']:
                    raise ValueError('native token/render evidence mismatch')
                if len(prompt['token_ids']) + condition['settings']['max_new_tokens'] > condition['settings']['max_input_and_output']:
                    raise ValueError('native actual initial context overflow')
                batch_keys.add(key)
                entries.append({'key': key, 'result': path, 'request': request_path, 'prompt': prompt_path,
                                'raw_file_sha256': hashlib.sha256(data).hexdigest(), 'result_sha256': a.digest(raw),
                                'original_local_process': context['process_reservation'], 'original_context': root + '/execution-context.json',
                                'original_organizer_approved': False, 'original_shared_ledger': False,
                                'original_assignment_sha256': raw['assignment_sha256'], 'original_qualification_sha256': raw['qualification_sha256'],
                                'owner': 'Collaborator', 'original_authority': 'independent_local'})
            if batch_keys != set(reservation['keys']) or batch_keys != set(requests):
                raise ValueError('native batch coverage mismatch')
            if condition['backend'] == 'llama.cpp':
                server = read(root + '/worker-output/server-launch.json'); device = read(root + '/worker-output/cuda-device-preflight.json')
                args = server['args']
                if args[args.index('--device') + 1] != context['llama_device'] or device['returncode'] != 0 or context['llama_device'] not in device['stdout'] or runtime['runtime_revision'] != condition['runtime_revision']:
                    raise ValueError('native GGUF device/runtime mismatch')
            process = {'original_process': reservation['process'], 'scope': 'main_initials', 'original_bound_seconds': reservation['bound_seconds'],
                       'measured_subprocess_seconds': elapsed, 'receipt': root + '/process-outcome.json',
                       'unknown_outer_allowance_seconds': 600,
                       'outer_allowance_policy': 'declared per-process 600s retained conservatively for missing outside-subprocess boundaries; not a measured duration or extra loading measurement'}
            processes.append(process)
            seeds.setdefault(cid, {'condition': condition, 'context': context, 'qualification': qual, 'launch': launch, 'archive_root': root})
        keys = [entry['key'] for entry in entries]
        if set(keys) != expected or len(keys) != len(set(keys)) or (not fixture and len(keys) != 600):
            raise ValueError('exact original 600-item native coverage required')
        for path in sorted(n for n in names if n.startswith('qualification/') and n.endswith('/process-outcome.json')):
            root = path.rsplit('/', 1)[0]; outcome = read(path); reservation = read(root + '/local-reservation.json')
            elapsed = outcome['elapsed_seconds']
            if outcome['exit_code'] != 0 or not math.isfinite(elapsed) or elapsed < 0:
                raise ValueError('native development process not known completed')
            development.append({'original_process': reservation['process'], 'scope': 'development_only',
                                'original_bound_seconds': reservation.get('bound_seconds', reservation.get('maximum_seconds')),
                                'measured_subprocess_seconds': elapsed, 'receipt': path, 'unknown_outer_allowance_seconds': 600,
                                'outer_allowance_policy': 'conservative original per-process outer allowance; development not main scientific results'})
        if not fixture and (len(processes) != 12 or len(development) != 3):
            raise ValueError('original 12 main / 3 development process coverage required')
    return entries, processes + development, seeds


def reconcile(ledger, source, original_raw, authorization, output):
    if not authorization.get('explicit_human_native_reconciliation') or not authorization.get('authorization_text'):
        raise ValueError('explicit human reconciliation authorization required')
    archive_hash = a.sha(source)
    if archive_hash != authorization['native_archive_sha256'] or a.sha(original_raw) != authorization['original_raw_archive_sha256']:
        raise ValueError('authorization binds exact original archives')
    before = budgets(ledger)
    if before != authorization['unchanged_budgets']:
        raise ValueError('budget identity changed; no implicit revision')
    if exists(ledger, 'native_registry'):
        row = ledger.db.execute('SELECT body FROM native_registry WHERE id=?', (archive_hash,)).fetchone()
        if row:
            registry = json.loads(row[0])
            if a.sha(registry['source']) != archive_hash: raise ValueError('immutable reconciled archive changed')
            return {'identical_duplicate': True, 'registry': registry, 'new_charges': 0}
    package = Path(ledger.meta('package')); spec = json.loads(ledger.meta('spec'))
    entries, charges, seeds = inspect_native(source, original_raw, spec, package, ledger.meta('fixture') == 'True')
    output = Path(output); output.mkdir(parents=True, exist_ok=False)
    dest = output / ('native-' + archive_hash + '.zip'); shutil.copyfile(source, dest)
    if a.sha(dest) != archive_hash: raise ValueError('native immutable copy failed')
    registry = {'version': VERSION, 'source': str(dest.resolve()), 'original_source_sha256': archive_hash,
                'original_raw_archive_sha256': a.sha(original_raw), 'authorization': authorization,
                'accepted_utc': datetime.now(timezone.utc).isoformat(), 'original_authority': 'independent_local',
                'historical_central_tickets_created': False, 'original_local_approvals_changed': False,
                'entries': len(entries), 'charges': charges, 'seed_metadata': seeds}
    install(ledger)
    def commit():
        ledger.db.execute('INSERT INTO native_registry VALUES(?,?)', (archive_hash, a.canonical(registry).decode()))
        for entry in entries:
            if ledger.db.execute('SELECT 1 FROM stages WHERE key=?', (entry['key'],)).fetchone() or ledger.db.execute('SELECT 1 FROM returns WHERE key=?', (entry['key'],)).fetchone():
                raise ValueError('existing first-turn reservation/return conflicts with native reconciliation')
            ledger.db.execute('INSERT INTO native_entries VALUES(?,?,?)', (entry['key'], archive_hash, a.canonical(entry).decode()))
        for charge in charges:
            identity = 'native-known:' + archive_hash + ':' + charge['original_process']
            seconds = charge['measured_subprocess_seconds']
            ledger.db.execute('INSERT INTO control_work VALUES(?,?,?,?,?,?)', (identity, 'Collaborator', 'reconciled native ' + charge['scope'] + ' subprocess', max(seconds, .001), seconds, 'complete'))
            unknown = 'native-outer:' + archive_hash + ':' + charge['original_process']
            ledger.db.execute('INSERT INTO control_work VALUES(?,?,?,?,?,?)', (unknown, 'Collaborator', charge['outer_allowance_policy'], 600, None, 'unknown'))
            ledger.db.execute('INSERT INTO native_charges VALUES(?,?,?)', (charge['original_process'], archive_hash,
                              a.canonical({**charge, 'known_charge_id': identity, 'unknown_charge_id': unknown}).decode()))
        if budgets(ledger) != before: raise ValueError('budgets changed during native reconciliation')
    ledger.transaction(commit)
    a.put(output / 'reconciliation-receipt.json', {'version': VERSION, 'registry_sha256': archive_hash, 'original_local_records_preserved': True,
          'accepted_first_turns': len(entries), 'measured_main_and_development_subprocess_seconds': sum(c['measured_subprocess_seconds'] for c in charges),
          'conservative_unknown_outer_seconds': 600 * len(charges), 'new_historical_tickets': 0, 'summary': ledger.summary()})
    return {'identical_duplicate': False, 'registry': registry, 'entries': len(entries)}


def issue(ledger, key, output, remote_executor_sha256, cutoff_utc):
    """Real future assignment/process, conditional on remote metadata activation."""
    if datetime.now(timezone.utc) >= datetime.fromisoformat(cutoff_utc):
        raise ValueError('existing result-import cutoff passed')
    route_row = ledger.db.execute('SELECT body FROM routes WHERE key=?', (key,)).fetchone()
    if not route_row or json.loads(route_row[0])['status'] != 'supported' or not key.endswith('|2'):
        raise ValueError('supported canonical second turn required')
    route = json.loads(route_row[0]); original = canonical_native(ledger).get(route['initial_key'])
    if original is None or a.digest(original) != route['initial_result_sha256']:
        raise ValueError('native canonical history missing/changed')
    if route['request']['messages'][-2] != {'role': 'assistant', 'content': original['raw_output']}:
        raise ValueError('verbatim first-turn history required')
    cid = key.split('|')[1]
    spec = json.loads(ledger.meta('spec')); condition = a.read(Path(ledger.meta('package')) / spec['conditions'][cid]['path'])
    process, assignment = str(uuid.uuid4()), str(uuid.uuid4())
    body = {'version': VERSION, 'id': assignment, 'owner': 'Collaborator', 'keys': [key], 'shards': [],
            'package_sha256': ledger.meta('package_hash'), 'purpose': 'prospective supported second turn only',
            'issued_utc': datetime.now(timezone.utc).isoformat(), 'metadata_activation_delegated': True}
    bound = 600 + condition['settings']['max_seconds']
    receipt = {'version': VERSION, 'key': key, 'process': process, 'assignment': body, 'bound_seconds': bound,
               'status': 'issued_pending_remote_metadata', 'metadata_overhead_seconds': 600,
               'request_sha256': route['request_sha256'], 'route_sha256': a.digest(route),
               'initial_result_sha256': route['initial_result_sha256'], 'remote_executor_sha256': remote_executor_sha256,
               'cutoff_utc': cutoff_utc, 'original_first_turn_authority': 'independent_local',
               'gate': 'new metadata-only proof on qualified collaborator machine before activation/model call; no fabricated pre-reservation proof'}
    def commit():
        ledger.db.execute('INSERT INTO assignments VALUES(?,?,?)', (assignment, 'Collaborator', a.canonical(body).decode()))
        ledger.db.execute('INSERT INTO ownership VALUES(?,?)', (key, assignment))
        ledger.db.execute('INSERT INTO processes VALUES(?,?,?,?,?)', (process, assignment, bound, None, 'reserved_unknown'))
        ledger.db.execute('INSERT INTO stages VALUES(?,?,?,?)', (key, process, route['request_sha256'], 'issued_pending_remote_metadata'))
        ledger.db.execute('INSERT INTO native_jobs VALUES(?,?,?)', (key, process, a.canonical(receipt).decode()))
    ledger.transaction(commit)
    a.put(output, receipt)
    return receipt


def import_continuation(ledger, source, output):
    """Validate future conditional activation and complete transport, then canonicalize."""
    source, output = Path(source), Path(output)
    incoming = a.files(source); transport = a.digest(incoming)
    output.mkdir(parents=True, exist_ok=True)
    previous = ledger.db.execute('SELECT body FROM transports WHERE id=?', (transport,)).fetchone()
    if previous: return {**json.loads(previous[0]), 'identical_duplicate_transport': True}
    dest = output / (transport + '-' + str(uuid.uuid4())); shutil.copytree(source, dest)
    envelope = a.read(dest / 'return-envelope.json'); actual = a.files(dest); actual.pop('return-envelope.json')
    if envelope.get('version') != VERSION or envelope.get('kind') != 'prospective_central_stage2' or envelope.get('files') != actual:
        raise ValueError('native continuation envelope/file hashes changed')
    descriptor = a.read(dest / 'job.json'); key = descriptor['issue']['key']
    row = ledger.db.execute('SELECT body FROM native_jobs WHERE key=?', (key,)).fetchone()
    payload = ledger.db.execute('SELECT body FROM native_job_payloads WHERE process=?', (descriptor['issue']['process'],)).fetchone()
    if not row or json.loads(row[0]) != descriptor['issue'] or not payload or json.loads(payload[0]) != descriptor:
        raise ValueError('unknown/changed prospective native continuation issue')
    issue = descriptor['issue']; route = json.loads(ledger.db.execute('SELECT body FROM routes WHERE key=?', (key,)).fetchone()[0])
    if (envelope.get('assignment'), envelope.get('executor'), envelope.get('process_reservation')) != (issue['assignment']['id'], 'Collaborator', issue['process']):
        raise ValueError('return envelope assignment/executor/process changed')
    state = ledger.db.execute('SELECT assignment,bound FROM processes WHERE id=?', (issue['process'],)).fetchone()
    stage = ledger.db.execute('SELECT process,request_hash FROM stages WHERE key=?', (key,)).fetchone()
    if state != (issue['assignment']['id'], issue['bound_seconds']) or stage != (issue['process'], issue['request_sha256']):
        raise ValueError('prospective central reservation changed')
    original = canonical_native(ledger).get(route['initial_key'])
    if original is None or a.digest(original) != route['initial_result_sha256']:
        raise ValueError('first-turn native provenance changed/conflicted')
    if a.digest(descriptor['request']) != issue['request_sha256'] or descriptor['request'] != route['request']:
        raise ValueError('issued conversation changed')
    process = a.read(dest / 'process-receipt.json')
    if process['process_reservation'] != issue['process'] or not math.isfinite(process['elapsed_seconds']) or process['elapsed_seconds'] < 0:
        raise ValueError('prospective process receipt mismatch')
    if process.get('state') not in ('complete','failed','timed_out','interrupted','unknown') or type(process.get('inference_started')) is not bool:
        raise ValueError('invalid prospective lifecycle status')
    activation = a.read(dest / 'activation.json') if (dest / 'activation.json').exists() else None
    raw = None
    if activation:
        from .native_remote import validate_proof
        proof = a.read(dest / 'metadata-proof.json')
        validate_proof(descriptor, proof, activation['activated_unix_seconds'])
        if activation['remote_executor_sha256'] != issue['remote_executor_sha256'] or a.digest(proof) != activation['metadata_proof_sha256']:
            raise ValueError('metadata activation identity changed')
        if activation.get('central_issue_process') != issue['process']:
            raise ValueError('metadata activation/process lifecycle differs')
        context, qual = a.read(dest / 'execution-context.json'), a.read(dest / 'qualification.json')
        if a.digest(qual) != context['qualification_sha256'] or qual != proof['qualification']:
            raise ValueError('fresh activation qualification changed')
        from .native_remote import execution_context
        if context != execution_context(descriptor, qual):
            raise ValueError('issued prospective worker context changed')
    if activation and envelope['entries']:
        if process['inference_started'] is not True:
            raise ValueError('raw result without an actual worker attempt')
        runtime = a.read(dest / 'worker-output/runtime.json')
        if runtime['process_reservation'] != issue['process'] or runtime['qualification_sha256'] != context['qualification_sha256'] or runtime['worker_sha256'] != context['worker_sha256']:
            raise ValueError('worker/runtime activation mismatch')
        expected_hw = {k: qual['hardware_runtime'][k] for k in ('driver','os','vram_mib')}
        if runtime.get('hardware_runtime_observed') != expected_hw or runtime.get('device_uuid') != qual['hardware_runtime']['device_uuid']:
            raise ValueError('actual worker hardware differs from fresh metadata')
        c = descriptor['condition']
        if c['backend'] == 'llama.cpp':
            server = a.read(dest/'worker-output/server-launch.json'); device = a.read(dest/'worker-output/cuda-device-preflight.json')
            args = server['args']
            if runtime.get('runtime_revision') != c['runtime_revision'] or args[args.index('--device')+1] != context['llama_device'] or device['returncode'] != 0 or context['llama_device'] not in device['stdout']:
                raise ValueError('actual GGUF offload/backend differs from issued metadata')
        elif runtime.get('runtime_versions') != qual['hardware_runtime']['backend_versions']:
            raise ValueError('actual answering runtime versions changed')
        entries = envelope['entries']
        if len(entries) != 1 or entries[0]['key'] != key:
            raise ValueError('one exact issued continuation return required')
        entry = entries[0]
        q, prompt = a.read(a.within(dest, entry['request'])), a.read(a.within(dest, entry['prompt']))
        raw = a.read(a.within(dest, entry['result']))
        if q != route['request'] or raw['request_sha256'] != issue['request_sha256'] or raw['stage_key'] != key or raw['stage'] != 2:
            raise ValueError('returned continuation request/stage changed')
        if raw['response_origin'] != 'actual_local_model' or raw['cpu_fallback'] is not False or raw['qualification_status'] != 'task_qualified' or raw['execution_version'] != a.VERSION or raw['execution_scope'] != 'main':
            raise ValueError('unqualified continuation/fallback')
        for field in ('assignment_sha256', 'qualification_sha256', 'hardware_runtime_sha256', 'worker_sha256', 'scientific_condition_sha256', 'process_reservation'):
            if raw[field] != context[field]: raise ValueError('continuation context provenance changed: ' + field)
        if len(prompt['token_ids']) != raw['input_tokens'] or prompt != proof['stage2_render'] or len(raw['output_token_ids']) != raw['output_tokens']:
            raise ValueError('actual continuation render/token evidence changed')
        if raw['stage_reservation'] != issue['process'] + ':' + key or a.read(dest / 'route.json') != route:
            raise ValueError('continuation route/reservation changed')
        if raw.get('completion_status') not in ('completed','failed','length_limited','timeout','interrupted','unknown') or not isinstance(raw.get('raw_output'), str):
            raise ValueError('invalid returned completion/raw text')
        if 'termination' not in raw or 'device_memory' not in raw or not math.isfinite(raw.get('total_stage_seconds', float('nan'))) or raw['total_stage_seconds'] < 0:
            raise ValueError('essential continuation measurement evidence missing')
    elif envelope['entries'] or (process.get('inference_started') is not False and not activation):
        raise ValueError('missing real metadata activation before inference')
    def commit():
        existing = ledger.db.execute('SELECT actual,state FROM processes WHERE id=?', (issue['process'],)).fetchone()
        if existing[0] is None:
            ledger.settle(issue['process'], process['elapsed_seconds'], process['state'])
        elif existing != (process['elapsed_seconds'], process['state']):
            ledger.db.execute("UPDATE processes SET actual=?,state='unknown' WHERE id=?", (max(existing[0], process['elapsed_seconds']), issue['process']))
        if raw:
            entry = envelope['entries'][0]
            ledger.db.execute('INSERT OR IGNORE INTO qualifications VALUES(?,?)', (a.digest(qual), a.canonical(qual).decode()))
            ledger.db.execute('INSERT OR IGNORE INTO returns VALUES(?,?,?,?,?)', (key, a.entry_identity(entry, actual), str(dest), 1, None))
            ledger.db.execute('UPDATE stages SET state=? WHERE key=?', (raw['completion_status'], key))
        else:
            terminal = 'worker_failed_no_result' if process.get('inference_started') else 'activated_worker_unexecuted' if activation else 'metadata_failed_unexecuted'
            ledger.db.execute('UPDATE stages SET state=? WHERE key=?', (terminal, key))
        receipt = {'version': VERSION, 'transport': transport, 'source_root': str(dest), 'accepted_keys': [key] if raw else [],
                   'metadata_failed_unexecuted_keys': [] if raw else [key], 'identical_duplicate_transport': False,
                   'original_first_turn_provenance': 'independent_local_preserved', 'resolved_scoring': 'unchanged_scorer_required',
                   'conflicts': a.conflicts(ledger), 'summary': ledger.summary()}
        ledger.db.execute('INSERT INTO transports VALUES(?,?)', (transport, a.canonical(receipt).decode()))
        return receipt
    receipt = ledger.transaction(commit); a.put(output / ('import-' + transport + '.json'), receipt)
    return receipt


def unpack_return(source, output):
    """Preserve exact ZIP bytes, then safely extract a complete returned payload."""
    source, output = Path(source), Path(output)
    output.mkdir(parents=True, exist_ok=False)
    archive_hash = a.sha(source)
    shutil.copyfile(source, output / ('original-' + archive_hash + '.zip'))
    dest = output / 'payload'; dest.mkdir()
    with zipfile.ZipFile(source) as archive:
        names = [n for n in archive.namelist() if not n.endswith('/')]
        if len(names) != len(set(names)) or archive.testzip() is not None:
            raise ValueError('corrupt or duplicate return ZIP entries')
        for name in names:
            if '\\' in name or name.startswith('/'):
                raise ValueError('unsafe returned ZIP path')
            target = a.within(dest, name); target.parent.mkdir(parents=True, exist_ok=True)
            with target.open('xb') as stream: stream.write(archive.read(name))
    return dest


def analyse_core(ledger, plan, output):
    """After the two issued continuations are processed, delegate unchanged analysis."""
    from . import restart_execution
    from unittest.mock import patch
    pending = ledger.db.execute("SELECT n.key FROM native_jobs n JOIN stages s ON s.key=n.key WHERE s.state IN ('issued_pending_remote_metadata','issued_pending_metadata','reserved_unknown')").fetchall()
    families = {i['sample_id']: i['family'] for i in json.loads(ledger.meta('spec'))['items']}
    for first_key, in ledger.db.execute('SELECT key FROM native_entries'):
        if families[first_key.split('|')[0]] == 'clarification' and not ledger.db.execute('SELECT 1 FROM routes WHERE key=?', (first_key[:-1]+'2',)).fetchone():
            pending.append((first_key[:-1]+'2',))
    for key, body in ledger.db.execute('SELECT key,body FROM routes'):
        route = json.loads(body)
        if route['status'] == 'supported' and ledger.db.execute('SELECT 1 FROM native_entries WHERE key=?', (route['initial_key'],)).fetchone():
            if not ledger.db.execute('SELECT 1 FROM native_jobs WHERE key=?', (key,)).fetchone():
                pending.append((key,))
    if pending: raise ValueError('resolved clarification results still pending; process both supported continuations first')
    records = restart_execution.combined_records(ledger) if exists(ledger, 'restart_freeze') else main_record_index.canonical_records(ledger)
    if a.conflicts(ledger): raise ValueError('conflicting returns require disposition before analysis')
    # Existing frozen bridge/scorers/bootstrap see this verified combined core snapshot.
    with patch.object(a, 'canonical_records', lambda requested: records if requested is ledger else main_record_index.canonical_records(requested)):
        result = a.analysis_bridge(ledger, plan, output)
    a.put(Path(output)/'native-provenance-and-accounting.json', {
        'version': VERSION, 'original_first_turn_authority': 'independent_local_preserved',
        'historical_central_tickets_created': False,
        'native_entries': [json.loads(body) for body, in ledger.db.execute('SELECT body FROM native_entries')],
        'native_charge_receipts': [json.loads(body) for body, in ledger.db.execute('SELECT body FROM native_charges')],
        'new_prospective_jobs': [json.loads(body) for body, in ledger.db.execute('SELECT body FROM native_jobs')],
        'settled_processes': list(ledger.db.execute('SELECT id,assignment,bound,actual,state FROM processes WHERE id IN (SELECT process FROM native_jobs)')),
        'current_accounting': ledger.summary(), 'unchanged_scorers_and_fixed_denominators': True})
    return result


def main():
    p = argparse.ArgumentParser(); sub = p.add_subparsers(dest='command', required=True)
    c = sub.add_parser('import-continuation')
    for name in ('ledger', 'source', 'output'): c.add_argument('--' + name, required=True)
    c = sub.add_parser('analyse-core')
    for name in ('ledger', 'plan', 'output'): c.add_argument('--' + name, required=True)
    args = p.parse_args(); ledger = main_allocation.Ledger(args.ledger)
    control = None; started = time.monotonic()
    try:
        bound = 1800 if args.command == 'analyse-core' else 600
        control = ledger.reserve_control('Collaborator', 'native continuation ' + args.command, bound)
        if args.command == 'analyse-core':
            result = analyse_core(ledger, args.plan, args.output)
        else:
            source = Path(args.source)
            if source.is_file():
                source = unpack_return(source, Path(args.output)/('transport-'+a.sha(source)+'-'+str(uuid.uuid4())))
            result = import_continuation(ledger, source, args.output)
        ledger.settle_control(control, time.monotonic() - started)
        print(a.canonical(result).decode())
    except BaseException:
        if control is not None: ledger.settle_control(control, time.monotonic() - started, 'failed')
        raise
    finally: ledger.db.close()


if __name__ == '__main__': main()
