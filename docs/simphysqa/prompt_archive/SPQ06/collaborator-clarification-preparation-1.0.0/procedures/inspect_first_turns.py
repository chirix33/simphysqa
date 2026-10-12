"""Read-only organizer diagnostics. Does not import, reserve, score or launch.

Uses frozen central parser/router; drafts are explicitly NOT issued jobs.
"""
import argparse
import collections
import json
import sqlite3
import zipfile
from pathlib import Path

from simphysqa import execution_adapter as adapter
from simphysqa.clarification_evaluation import inspect_stage1, route_reply
from simphysqa.heldout_scope import formal_scope
from simphysqa.main_analysis import clarification_category
from simphysqa.main_public import continuation
from simphysqa.spq06 import parse_answer

CIDS = ('deepseek_r1_distill_qwen32b', 'gemma3_27b_qat_direct', 'gemma3_27b_qat_cot')


def run(a):
    output = Path(a.output)
    output.mkdir(parents=True, exist_ok=False)
    preparation, package = Path(a.base) / 'main-preparation-1.0.0', Path(a.base) / 'execution-public-1.1.1'
    adapter.validate_package(package)
    spec = adapter.read(package / 'execution-spec.json')
    selection = adapter.read(preparation / 'nested-200-manifest.json')
    assert adapter.sha(preparation / 'nested-200-manifest.json') == spec['selected_manifest_sha256']
    items = {i['sample_id']: i for i in selection['items']}
    expected = {k for k in spec['requests'] if k.split('|')[1] in CIDS}
    raw_index, raws, archive_files = [], {}, {}
    with zipfile.ZipFile(a.archive) as archive:
        names = [n for n in archive.namelist() if not n.endswith('/')]
        assert len(names) == len(set(names)) == 600
        for name in names:
            data = archive.read(name)
            raw = json.loads(data)
            key = raw['stage_key']
            assert key in expected and key not in raws
            sid, cid, label, stage = key.split('|')
            assert (sid, cid, label, int(stage)) == (raw['sample_id'], raw['condition_id'], raw['representation'], raw['stage'])
            assert name == cid + '/' + sid + '-stage1.json'
            pin = spec['conditions'][cid]
            assert raw['request_sha256'] == spec['requests'][key]['sha256']
            assert raw['worker_sha256'] == pin['worker_sha256']
            assert raw['scientific_condition_sha256'] == pin['sha256']
            assert raw['response_origin'] == 'actual_local_model' and raw['cpu_fallback'] is False
            assert raw['execution_scope'] == 'main' and raw['qualification_status'] == 'task_qualified'
            assert adapter.sha(package / spec['requests'][key]['path']) == raw['request_sha256']
            import hashlib
            byte_hash = hashlib.sha256(data).hexdigest()
            archive_files[name] = byte_hash
            raws[key] = raw
            raw_index.append({'key': key, 'archive_entry': name, 'result_file_sha256': byte_hash,
                              'process_reservation': raw['process_reservation'], 'assignment_sha256': raw['assignment_sha256'],
                              'qualification_sha256': raw['qualification_sha256']})
    assert set(raws) == expected
    db = sqlite3.connect(Path(a.ledger).as_uri() + '?mode=ro', uri=True)
    try:
        db.execute('BEGIN')
        assignments = [(identity, owner, adapter.digest(json.loads(body))) for identity, owner, body in db.execute('SELECT * FROM assignments')]
        known_processes = {r[0] for r in db.execute('SELECT id FROM processes')}
        known_qualifications = {r[0] for r in db.execute('SELECT hash FROM qualifications')}
        known_assignments = {r[2] for r in assignments}
        missing = {'process_reservations': sorted({r['process_reservation'] for r in raws.values()} - known_processes),
                   'qualification_sha256': sorted({r['qualification_sha256'] for r in raws.values()} - known_qualifications),
                   'assignment_sha256': sorted({r['assignment_sha256'] for r in raws.values()} - known_assignments)}
        ledger_state = {'collaborator_assignments': [r[0] for r in assignments if r[1] == 'Collaborator'],
                        'missing_original_authority': missing,
                        'allocation': dict(db.execute('SELECT owner,ceiling FROM executor_allocations')),
                        'shared_ceiling_seconds': float(db.execute("SELECT v FROM meta WHERE k='ceiling'").fetchone()[0]),
                        'note': 'Ledger read only. Remaining collaborator allocation cannot be verified until original process charges are reconciled.'}
    finally:
        db.close()
    scope = adapter.read(preparation / 'private/generation-scope.json')
    receipts = []
    for key, raw in sorted(raws.items()):
        sid, cid, label, _ = key.split('|')
        item = items[sid]
        if item['family'] != 'clarification':
            continue
        record = adapter.read(preparation / item['private_record'])
        assert adapter.digest(record) == item['record_sha256']
        condition = adapter.read(preparation / 'conditions' / (cid + '.json'))
        assert adapter.sha(preparation / 'conditions' / (cid + '.json')) == spec['conditions'][cid]['original_sha256']
        request, checks, diagnostics = None, None, None
        reason = raw['completion_status']
        category = 'first_turn_not_completed'
        with formal_scope(scope['candidates'], scope['excluded_groups']):
            if raw['completion_status'] == 'completed':
                try:
                    response, diagnostics = parse_answer(raw['raw_output'])
                    checks = inspect_stage1(record, response)
                    routed = route_reply(record, response)
                    category = clarification_category(checks)
                    request, routed_again = continuation(record, condition, raw['raw_output'], response, False)
                    assert routed_again == routed
                    reason = routed['status']
                except (ValueError, KeyError, TypeError) as exc:
                    reason = type(exc).__name__ + ': ' + str(exc)
                    category = 'frozen_parser_failure'
        if request:
            original = adapter.read(package / spec['requests'][key]['path'])
            assert request['messages'][:-2] == original['messages']
            assert request['messages'][-2] == {'role': 'assistant', 'content': raw['raw_output']}
            assert request['tools'] == []
            adapter.put(output / 'public/draft-requests' / cid / (sid + '-stage2.json'), request)
        receipt = {'version': 'SPQ06-collaborator-raw-diagnostic/1.0.0', 'key': key[:-1] + '2', 'initial_key': key,
                   'provenance_status': 'original_complete_return_and_authority_missing', 'issued': False,
                   'diagnostic_routing_status': 'supported' if request else 'unexecuted_conditional',
                   'category': category, 'reason': reason, 'checks': checks, 'parser_diagnostics': diagnostics,
                   'initial_result_sha256': adapter.digest(raw), 'actual_raw': raw['raw_output'],
                   'request_sha256': adapter.digest(request) if request else None,
                   'resolved_result_status': 'pending', 'semantic_routing_gate_added': False}
        adapter.put(output / 'public/diagnostic-receipts' / cid / (sid + '-stage2.json'), receipt)
        receipts.append(receipt)
    assert len(receipts) == 120
    counts = {cid: {'clarification_first_turns': sum(r['initial_key'].split('|')[1] == cid for r in receipts),
                    'categories': dict(collections.Counter(r['category'] for r in receipts if r['initial_key'].split('|')[1] == cid)),
                    'completion_status_all_200': dict(collections.Counter(r['completion_status'] for k, r in raws.items() if k.split('|')[1] == cid))}
              for cid in CIDS}
    source = {'archive_sha256': adapter.sha(a.archive), 'files': archive_files, 'results': raw_index}
    adapter.put(output / 'public/expected-results-index.json', source)
    versions = {n: adapter.sha(Path(adapter.__file__).parent / (n + '.py')) for n in
                ('spq06', 'clarification_evaluation', 'clarification', 'main_public', 'public_updates', 'scoring', 'main_analysis', 'execution_adapter')}
    summary = {'version': 'SPQ06-collaborator-preparation/1.0.0', 'status': 'blocked_original_provenance',
               'raw_results': 600, 'exact_core_coverage_per_condition': 200, 'clarification_diagnostics': counts,
               'diagnostically_supported': [r['key'] for r in receipts if r['diagnostic_routing_status'] == 'supported'],
               'unexecuted_conditional_diagnostics': sum(r['diagnostic_routing_status'] == 'unexecuted_conditional' for r in receipts),
               'issued_jobs': [], 'canonical_imports': 0, 'answering_calls': 0, 'ledger_mutations': 0,
               'ledger_snapshot': ledger_state, 'frozen_sources_sha256': versions,
               'archive_sha256': source['archive_sha256'], 'resolved_clarification_results': 'pending',
               'warning': 'Raw-file fields match sealed pins but do not authenticate missing execution evidence or original authority.'}
    adapter.put(output / 'public/summary.json', summary)
    print(json.dumps({k: summary[k] for k in ('status', 'raw_results', 'clarification_diagnostics', 'diagnostically_supported', 'unexecuted_conditional_diagnostics', 'canonical_imports', 'issued_jobs')}))


if __name__ == '__main__':
    p = argparse.ArgumentParser()
    for name in ('base', 'archive', 'ledger', 'output'):
        p.add_argument('--' + name, required=True)
    run(p.parse_args())
