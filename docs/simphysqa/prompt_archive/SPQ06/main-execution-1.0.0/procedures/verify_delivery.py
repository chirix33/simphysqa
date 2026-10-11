"""Offline checks of actual saved main evidence. No weights or answering calls."""
from collections import Counter
from pathlib import Path
from simphysqa.execution_adapter import read, sha, put


def verify(run, package, preparation, output):
    run, package, preparation = map(Path, (run, package, preparation))
    core = read(preparation / 'nested-200-manifest.json')['items']
    pool = read(preparation / 'nested-400-manifest.json')['items']
    assert len(core) == len({r['sample_id'] for r in core}) == len({r['group_id'] for r in core}) == 200
    assert len(pool) == len({r['sample_id'] for r in pool}) == len({r['group_id'] for r in pool}) == 400
    assert {r['sample_id'] for r in core} <= {r['sample_id'] for r in pool}
    assert set(Counter((r['domain'], r['family']) for r in core).values()) == {10}
    assert set(Counter((r['domain'], r['family']) for r in pool).values()) == {20}
    assert {r['split'] for r in core + pool} == {'test_id'}
    spec = read(package / 'execution-spec.json')
    assignments = [read(p) for p in (run / 'assignments').glob('*.json')]
    assigned = [k for a in assignments for k in a['keys']]
    assert len(assignments) == 8 and all(a['owner'] == 'Ashraf' for a in assignments)
    assert len(assigned) == len(set(assigned)) == 1920
    assert sum(k.endswith('|1') for k in assigned) == 1600
    assert sum(k.endswith('|2') for k in assigned) == 320
    checks, seen, reserved, missing_receipts = [], set(), set(), []
    for job in sorted((run / 'jobs').iterdir()):
        if not job.is_dir():
            continue
        ticket = read(job/'ticket.json')
        assert not reserved.intersection(ticket['keys'])
        reserved.update(ticket['keys'])
        receipt_path=job/'process-receipt.json'
        if not receipt_path.exists():
            recovery=read(run/'restart-recovery-1.0.0/recovery-receipt.json')
            assert Path(recovery['original_job']).resolve()==job.resolve()
            assert recovery['actual_lifecycle_seconds'] is None and recovery['reservation_releases']==0
            assert recovery['original_files']==__import__('simphysqa.execution_adapter',fromlist=['files']).files(job)
            missing_receipts.append({'job':str(job),'bound_seconds':ticket['bound_seconds'],'actual_seconds':None,'reason':'power loss; full original bound retained'})
        context = read(job / 'execution-context.json')
        assert context['execution_scope'] == 'main'
        for file in sorted((job / 'worker-output/results').glob('*.json')):
            raw = read(file)
            key = raw['stage_key']
            assert key not in seen and key in assigned
            seen.add(key)
            assert raw['execution_scope'] == 'main' and raw['response_origin'] == 'actual_local_model'
            assert raw['cpu_fallback'] is False
            prompt = read(job / 'worker-output/tokenized-prompts' / file.name)
            assert raw['input_tokens'] == len(prompt['token_ids'])
            assert raw['output_tokens'] == len(raw['output_token_ids'])
            request = job / 'worker-output/executed-requests' / file.name
            assert sha(request) == raw['request_sha256']
            if raw['stage'] == 1:
                assert sha(package / spec['requests'][key]['path']) == spec['requests'][key]['sha256']
            else:
                route = read(job / 'routing' / file.name)
                actual = read(request)
                assert actual['messages'][-2] == {'role': 'assistant', 'content': route['actual_raw']}
            checks.append({'key': key, 'result_sha256': sha(file), 'token_counts_match_saved_ids': True,
                           'process_receipt_sha256': sha(receipt_path) if receipt_path.exists() else None})
    assert sum(k.endswith('|1') for k in reserved) == 1600
    missing_initials=sorted(k for k in reserved-seen if k.endswith('|1'))
    recovery=read(run/'restart-recovery-1.0.0/recovery-receipt.json')
    assert missing_initials==sorted(recovery['interrupted_missing_or_invalid_keys'])
    assert len(missing_initials)==35 and sum(k.endswith('|1') for k in seen)==1565
    import sqlite3
    connection=sqlite3.connect('file:'+str((preparation.parent/'central-main-1.0.0/main.sqlite').as_posix())+'?mode=ro',uri=True)
    try:
        for key in missing_initials:
            assert connection.execute('SELECT state FROM stages WHERE key=?',(key,)).fetchone()==('interrupted',)
        actual,state,bound=connection.execute('SELECT actual,state,bound FROM processes WHERE id=?',(recovery['process_reservation'],)).fetchone()
        assert actual is None and state=='interrupted' and bound==6600
    finally:connection.close()
    assert sum(k.endswith('|2') for k in seen) <= 320
    before = read(run / 'preservation-before.json')
    legacy = read(preparation.parent / 'awq-supplement-1.0.0/historical-package-preservation-before.json')['hashes']
    combined = {}
    for group in (before, legacy):
        for p, h in group.items():
            name = str(Path(p).resolve())
            assert name not in combined or combined[name] == h, name
            combined[name] = h
    changed = [p for p, h in combined.items() if sha(p) != h]
    assert not changed, changed
    put(output, {'version': 'SPQ06-main-final-offline/1.0.0', 'actual_stage_checks': checks,'missing_reserved_initial_keys':missing_initials,'missing_lifecycle_receipts':missing_receipts,'initial_primary_denominators':1600,
                 'core_unique_items_groups': 200, 'pool_unique_items_groups': 400,
                 'preserved_file_count': len(combined), 'main_freeze_file_count': len(before),
                 'historical_package_file_count': len(legacy), 'preservation_changed': changed,
                 'answering_calls': 0, 'weights_loaded': False})
    return len(checks)
