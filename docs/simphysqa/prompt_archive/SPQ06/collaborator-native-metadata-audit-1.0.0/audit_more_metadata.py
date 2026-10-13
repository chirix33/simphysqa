"""Read-only audit of native collaborator records, without authority conversion."""
import collections
import json
import math
import sqlite3
import zipfile
from pathlib import Path
from simphysqa import execution_adapter as adapter

ROOT = Path(__file__).resolve().parent
BASE = Path('C:/Users/aashraf/.codex/visualizations/2026/10/06/01a1131b-eac2-7a31-afb4-f219a8dd6471/spq06/2026-10-09')
INPUT = Path('C:/Users/aashraf/Desktop/Work/phi-jepa/NAACL Paper/SimPhysQA-records-600_more_metadata.zip')
OLD = INPUT.with_name('SimPhysQA-results-600.zip')
OUT = ROOT / 'metadata-audit-1.0.1'


def audit():
    import hashlib
    OUT.mkdir(exist_ok=False)
    issues, batches, results, counts, main_keys = [], [], [], collections.Counter(), set()
    spec = adapter.read(BASE / 'execution-public-1.1.1/execution-spec.json')
    with zipfile.ZipFile(OLD) as old:
        originals = {json.loads(old.read(n))['stage_key']: (n, old.read(n)) for n in old.namelist() if not n.endswith('/')}
    with zipfile.ZipFile(INPUT) as archive:
        names = {n for n in archive.namelist() if not n.endswith('/')}
        assert len(names) == len([n for n in archive.namelist() if not n.endswith('/')])
        assert archive.testzip() is None
        assert not any(Path(n).is_absolute() or '..' in Path(n).parts or '\\' in n for n in names)

        def read(name):
            return json.loads(archive.read(name))

        def h(name):
            return hashlib.sha256(archive.read(name)).hexdigest()

        def check(test, label, where):
            if not test:
                issues.append({'check': label, 'file': where})
            else:
                counts[label] += 1

        roots = sorted(n.rsplit('/condition.json', 1)[0] for n in names if n.startswith('jobs/') and n.endswith('/condition.json'))
        for batch in roots:
            c = read(batch + '/condition.json')
            cid = c['condition_id']
            pin = spec['conditions'][cid]
            ctx = read(batch + '/execution-context.json')
            reservation = read(batch + '/local-reservation.json')
            outcome = read(batch + '/process-outcome.json')
            runtime = read(batch + '/worker-output/runtime.json')
            launch = read(batch + '/launch.json')
            prefix = batch.rsplit('/batch-', 1)[0]
            assignment_path = (prefix + '/local-assignment.json') if cid.startswith('deepseek') else (batch + '/local-assignment.json')
            qual_path = (prefix + '/local-qualification.json') if cid.startswith('deepseek') else (batch + '/local-qualification.json')
            assignment, qual = read(assignment_path), read(qual_path)
            public = adapter.read(BASE / 'execution-public-1.1.1' / pin['path'])
            check({k: v for k, v in c.items() if k not in adapter.LOCAL_FIELDS} == public, 'scientific_condition_exact', batch + '/condition.json')
            check(adapter.digest(c) == ctx['resolved_condition_sha256'], 'resolved_condition_hash', batch)
            check(adapter.digest(assignment) == ctx['assignment_sha256'], 'local_assignment_hash', assignment_path)
            check(adapter.digest(qual) == ctx['qualification_sha256'], 'local_qualification_hash', qual_path)
            check(adapter.digest(ctx['hardware_runtime']) == ctx['hardware_runtime_sha256'], 'hardware_hash', batch)
            check(reservation['process'] == ctx['process_reservation'] == runtime['process_reservation'], 'process_identity', batch)
            check(runtime['worker_sha256'] == ctx['worker_sha256'] == pin['worker_sha256'], 'worker_pin_link', batch)
            check(runtime['qualification_sha256'] == ctx['qualification_sha256'], 'runtime_qualification_link', batch)
            check(outcome['exit_code'] == 0 and math.isfinite(outcome['elapsed_seconds']) and outcome['elapsed_seconds'] >= 0, 'native_process_completed_with_finite_time', batch)
            check(launch['command'][0] == c['local_python'], 'original_interpreter_link', batch)
            check(launch['command'][2].endswith('/workers/' + Path(pin['worker']).name), 'original_worker_path_link', batch)
            requests = read(batch + '/requests.json')
            check(len(requests) == len(reservation['keys']) == 50, 'native_batch_50_coverage', batch)
            requests_by_key = {adapter.stage_key(q['sample_id'], q['condition_id'], q['input_condition'], q.get('stage', 1)): q for q in requests}
            batch_keys = set()
            for n in sorted(names):
                if not n.startswith(batch + '/worker-output/results/'):
                    continue
                raw = read(n)
                key = raw['stage_key']
                stem = n.rsplit('/', 1)[1]
                main_keys.add(key)
                batch_keys.add(key)
                qpath = batch + '/worker-output/executed-requests/' + stem
                ppath = batch + '/worker-output/tokenized-prompts/' + stem
                rpath = batch + '/worker-output/reservations/' + stem
                required = (qpath, ppath, rpath)
                check(all(p in names for p in required), 'complete_per_item_evidence', n)
                if not all(p in names for p in required):
                    continue
                q, prompt = read(qpath), read(ppath)
                check(key in originals and archive.read(n) == originals[key][1], 'raw_bytes_match_original_archive', n)
                check(key in spec['requests'] and adapter.digest(q) == raw['request_sha256'] == spec['requests'][key]['sha256'], 'executed_request_exact', qpath)
                check(key in requests_by_key and q == requests_by_key[key], 'job_request_list_link', qpath)
                check(q['tools'] == [] and raw['stage'] == 1 and raw['representation'] == 'enriched', 'public_tool_free_initial_stage', qpath)
                check(isinstance(prompt.get('prompt'), str) and isinstance(prompt.get('token_ids'), list) and all(type(t) is int and t >= 0 for t in prompt['token_ids']), 'saved_render_structure', ppath)
                check(len(prompt['token_ids']) == raw['input_tokens'], 'input_token_count', ppath)
                check(len(prompt['token_ids']) + c['settings']['max_new_tokens'] <= c['settings']['max_input_and_output'], 'saved_actual_context_fits', ppath)
                check(len(raw['output_token_ids']) == raw['output_tokens'], 'output_token_count', n)
                check(raw['process_reservation'] == ctx['process_reservation'] and raw['stage_reservation'] == ctx['stage_reservations'][key], 'original_stage_identity', n)
                for field in ('assignment_sha256', 'qualification_sha256', 'hardware_runtime_sha256', 'worker_sha256', 'scientific_condition_sha256'):
                    check(raw[field] == ctx[field], 'raw_context_' + field, n)
                check(math.isfinite(raw['total_stage_seconds']) and raw['total_stage_seconds'] >= 0, 'finite_stage_time', n)
                results.append({'key': key, 'metadata_path': n, 'sha256': h(n), 'process': ctx['process_reservation'], 'completion_status': raw['completion_status']})
            check(batch_keys == set(reservation['keys']) == set(requests_by_key), 'original_key_coverage', batch)
            if c['backend'] == 'llama.cpp':
                server = read(batch + '/worker-output/server-launch.json')
                device = read(batch + '/worker-output/cuda-device-preflight.json')
                args = server['args']
                check(args[args.index('--device') + 1] == ctx['llama_device'] and device['returncode'] == 0 and ctx['llama_device'] in device['stdout'], 'gemma_original_device_receipt', batch)
                check(runtime['runtime_revision'] == c['runtime_revision'], 'gemma_runtime_pin', batch)
            batches.append({'archive_root': batch, 'condition_id': cid, 'process': ctx['process_reservation'],
                            'original_interpreter': launch['command'][0], 'original_worker': launch['command'][2],
                            'original_job_root': str(Path(launch['command'][launch['command'].index('--condition') + 1]).parent),
                            'native_elapsed_seconds': outcome['elapsed_seconds'], 'native_bound_seconds': reservation['bound_seconds'],
                            'native_exit_code': outcome['exit_code'], 'organizer_approved': ctx.get('organizer_approved'),
                            'shared_ledger': reservation['shared_ledger'], 'qualification_authority': ctx.get('qualification_authority', qual.get('scope')),
                            'assignment_archive_path': assignment_path, 'qualification_archive_path': qual_path,
                            'runtime_elapsed_at_receipt': runtime.get('process_elapsed_seconds_at_receipt')})
        check(main_keys == set(originals) and len(results) == len(main_keys) == 600, 'exact_600_original_coverage', 'jobs/')
        dev = [n for n in names if n.startswith('qualification/') and '/results/' in n and n.endswith('.json')]
        development = [{'path': n, 'completion_status': read(n)['completion_status'], 'key': read(n).get('stage_key'), 'stage': read(n)['stage']} for n in sorted(dev)]
        file_index = {n: h(n) for n in sorted(names)}
        missing = {name: sum(n.rsplit('/', 1)[1] == name for n in names) for name in
                   ('return-envelope.json', 'ticket.json', 'assignment.json', 'bindings.json', 'qualification.json', 'pre-reservation-preflight.json', 'process-receipt.json')}
        # Preserve self-reported local authorization without accepting it as this user's approval.
        auth = {'deepseek_local_assignment_user_instruction': read('jobs/deepseek-main-001/local-assignment.json').get('user_instruction'),
                'deepseek_shared_ceiling_applied': read('jobs/deepseek-main-001/local-assignment.json').get('shared_ceiling_applied'),
                'development_authorization_claim': read('qualification/deepseek-development-001/manifest.json').get('authorization'),
                'trusted_current_user_budget_change': False}
    db = sqlite3.connect((BASE / 'central-main-1.0.0/main.sqlite').as_uri() + '?mode=ro', uri=True)
    try:
        known = {r[0] for r in db.execute('SELECT id FROM processes')}
        ledger = {'unregistered_original_processes': sorted(b['process'] for b in batches if b['process'] not in known),
                  'collaborator_assignments': [r[0] for r in db.execute("SELECT id FROM assignments WHERE owner='Collaborator'")],
                  'collaborator_ceiling_seconds': db.execute("SELECT ceiling FROM executor_allocations WHERE owner='Collaborator'").fetchone()[0]}
    finally:
        db.close()
    report = {'status': 'native_execution_evidence_received_central_acceptance_pending', 'archive_sha256': adapter.sha(INPUT),
              'zip_crc_passed': True, 'archive_files': len(file_index), 'checks_passed': dict(counts), 'issues': issues,
              'main_results': len(results), 'development_results': development, 'batches': batches,
              'main_native_elapsed_seconds_sum': sum(b['native_elapsed_seconds'] for b in batches),
              'main_native_elapsed_by_condition': {cid: sum(b['native_elapsed_seconds'] for b in batches if b['condition_id'] == cid) for cid in {b['condition_id'] for b in batches}},
              'sealed_return_file_counts': missing, 'local_authorization_claims': auth, 'central_ledger_read_only_snapshot': ledger,
              'canonical_imports': 0, 'ledger_mutations': 0, 'issued_jobs': 0, 'answering_calls': 0,
              'limitation': 'Measured native subprocess outcomes are not centrally settled total lifecycle charges. No retrospective tickets or qualifications created.'}
    adapter.put(OUT / 'archive-file-index.json', {'archive_sha256': report['archive_sha256'], 'files': file_index})
    adapter.put(OUT / 'raw-result-join.json', {'results': results})
    adapter.put(OUT / 'audit.json', report)
    print(json.dumps({k: report[k] for k in ('status', 'archive_files', 'main_results', 'checks_passed', 'issues', 'main_native_elapsed_seconds_sum', 'sealed_return_file_counts', 'canonical_imports')}))


if __name__ == '__main__':
    audit()
