"""Main power-loss recovery /1.0.0: preserve saved bytes, never release attempts.

The original process has no trustworthy end/lifecycle receipt. Import its exact
partial transport through the unchanged importer; missing entries remain invalid.
Mark unknown interrupted reservations without inventing timing or model output.
Call only after independent process inspection confirms the worker has stopped.
"""
import json
from pathlib import Path
from . import execution_adapter as adapter, main_import

VERSION = 'SPQ06-main-restart/1.0.0'

def recover(ledger, job, returned, immutable, stopped_evidence, route_root):
    job, returned, immutable, route_root = map(Path, (job, returned, immutable, route_root))
    ticket = adapter.read(job/'ticket.json')
    context = adapter.read(job/'execution-context.json')
    if context.get('execution_scope') != 'main':
        raise ValueError('main recovery only; development remains separate')
    if (job/'process-receipt.json').exists() or (job/'worker-output/completed.json').exists():
        raise ValueError('ended worker has its own receipt; do not infer interruption')
    if stopped_evidence.get('worker_stopped') is not True or not stopped_evidence.get('evidence_files'):
        raise ValueError('explicit stopped-worker evidence required')
    for name, expected in stopped_evidence['evidence_files'].items():
        if adapter.sha(name) != expected: raise ValueError('stopped-worker evidence changed')
    row = ledger.db.execute('SELECT assignment,bound,actual,state FROM processes WHERE id=?',(ticket['id'],)).fetchone()
    if not row or row[0] != ticket['assignment'] or row[2] is not None:
        raise ValueError('unknown unended allocated process required')
    if ledger.db.execute('SELECT COUNT(*) FROM stages WHERE process=?',(ticket['id'],)).fetchone()[0] != len(ticket['keys']):
        raise ValueError('original reservation coverage changed')
    original = adapter.files(job)
    adapter.export_return(job, returned)
    receipt = ledger.transaction(lambda: main_import.import_return(ledger, returned, immutable))
    if receipt['conflicts']:
        raise ValueError('conflict preserved; recovery cannot choose a preferred result')
    accepted = set(receipt['accepted_keys'])
    interrupted = [key for key in ticket['keys'] if key not in accepted]
    spec = json.loads(ledger.meta('spec'))
    families = {item['sample_id']: item['family'] for item in spec['items']}
    conditionals = []
    def mark():
        # Null actual duration retains the entire original bound. No synthetic zero.
        ledger.db.execute("UPDATE processes SET state='interrupted' WHERE id=? AND actual IS NULL",(ticket['id'],))
        for key in interrupted:
            ledger.db.execute("UPDATE stages SET state='interrupted' WHERE key=? AND process=?",(key,ticket['id']))
            sid,cid,label,stage = key.split('|')
            if stage == '1' and families.get(sid) == 'clarification':
                second = adapter.stage_key(sid,cid,label,2)
                route = {'version':adapter.VERSION,'key':second,'initial_key':key,'actual_raw':None,
                    'initial_result_sha256':None,'status':'unexecuted_conditional',
                    'reason':'interrupted process: no canonical actual first response; no authored substitute',
                    'request':None,'request_sha256':None,'recovery_version':VERSION}
                if ledger.db.execute('SELECT 1 FROM routes WHERE key=?',(second,)).fetchone():
                    raise ValueError('existing route must be preserved')
                ledger.db.execute('INSERT INTO routes VALUES(?,?)',(second,adapter.canonical(route).decode()))
                adapter.put(route_root/(sid+'.json'),route)
                conditionals.append(second)
    ledger.transaction(mark)
    if adapter.files(job) != original: raise ValueError('original interrupted job changed')
    return {'version':VERSION,'original_job':str(job),'original_files':original,'import_receipt':receipt,
        'accepted_saved_keys':sorted(accepted),'interrupted_missing_or_invalid_keys':interrupted,
        'unexecuted_conditional_keys':conditionals,'process_reservation':ticket['id'],
        'original_bound_seconds':row[1],'actual_lifecycle_seconds':None,
        'unavailable_reason':'power loss; trustworthy process-end/lifecycle timing unavailable',
        'reservation_releases':0,'scientific_retries':0,'invented_model_outputs':0,
        'stopped_worker_evidence':stopped_evidence}
