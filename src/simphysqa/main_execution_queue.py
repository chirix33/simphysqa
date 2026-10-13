"""Central main queue wrapper /1.0.0; never grants inference authorization.

Allocate overhead before metadata. Scientific reservations still require a fresh
executor preflight and task qualification. Block a shared model startup failure
across its representations, with no automatic unblock, orphan release or retry.
"""
import argparse,json,uuid
from pathlib import Path
try:
    from . import execution_adapter as adapter
except ImportError:
    import execution_adapter as adapter
VERSION='SPQ06-main-queue/1.0.0'

def identity(ledger,executor,cid):
    spec=json.loads(ledger.meta('spec'));c=adapter.read(Path(ledger.meta('package'))/spec['conditions'][cid]['path'])
    return '|'.join((executor,c['model_id'],c['artifact_revision'],c['backend']))

def ensure_tables(ledger):
    if ledger.meta('fixture')!='True' and adapter.read(Path(ledger.meta('package'))/'execution-spec.json').get('execution_scope','main')!='main':raise ValueError('main ledger required')
    ledger.db.execute('CREATE TABLE IF NOT EXISTS startup_blocks(identity TEXT PRIMARY KEY,reason TEXT NOT NULL)')

def check_queue(ledger,executor,cid):
    ensure_tables(ledger)
    row=ledger.db.execute('SELECT reason FROM startup_blocks WHERE identity=?',(identity(ledger,executor,cid),)).fetchone()
    if row:raise ValueError('shared startup queue paused: '+row[0])

def reserve_overhead(ledger,assignment,executor,cid,label):
    check_queue(ledger,executor,cid);owned=ledger.assignment(assignment,executor)
    if not any(k.split('|')[1:3]==[cid,label] for k in owned['keys']):raise ValueError('explicit assigned preflight combination required')
    process=str(uuid.uuid4())
    def op():
        if ledger.used()+600>float(ledger.meta('ceiling')):raise ValueError('aggregate main overhead ceiling exhausted')
        ledger.db.execute('INSERT INTO processes VALUES(?,?,?,?,?)',(process,assignment,600,None,'reserved_unknown'))
    ledger.transaction(op)
    return {'version':VERSION,'id':process,'assignment':assignment,'executor':executor,'condition_id':cid,'representation':label,'bound_seconds':600,'stage_keys':[],'policy':'attach initial science stages only after metadata preflight; same lifecycle charged once; unknown work retains reservation'}

def prepare_job(ledger,assignment,executor,qualification,keys,bindings,output,preflight,process):
    check_queue(ledger,executor,keys[0].split('|')[1])
    preflight={**preflight,'accounted_preflight_seconds':preflight.get('accounted_preflight_seconds',preflight.get('elapsed_seconds',0))}
    return adapter.prepare_job(ledger,assignment,executor,qualification,keys,bindings,output,preflight,process)

def block_startup(ledger,assignment,executor,cid,process,reason,elapsed=None):
    ensure_tables(ledger);ledger.assignment(assignment,executor)
    row=ledger.db.execute('SELECT assignment FROM processes WHERE id=?',(process,)).fetchone()
    if not row or row[0]!=assignment:raise ValueError('known allocated process required')
    ledger.db.execute('INSERT OR IGNORE INTO startup_blocks VALUES(?,?)',(identity(ledger,executor,cid),adapter.canonical({'reason':reason,'process':process}).decode()))
    if elapsed is not None:ledger.settle(process,elapsed,'failed')
    # No automatic unblock and no stage/process reservation release.

def import_return(ledger,source,root):
    receipt=adapter.import_return(ledger,source,root)
    dest=Path(receipt['source_root'])
    if (dest/'ticket.json').is_file() and (dest/'process-receipt.json').is_file():
        t=adapter.read(dest/'ticket.json');p=adapter.read(dest/'process-receipt.json')
        if t.get('keys') and p.get('state') in ('failed','timed_out','interrupted','unknown') and not (dest/'worker-output/runtime.json').is_file():
            cid=t['keys'][0].split('|')[1];ensure_tables(ledger)
            # Only an authenticated known reservation may block this central queue.
            row=ledger.db.execute('SELECT assignment FROM processes WHERE id=?',(t.get('id'),)).fetchone()
            if row and row[0]==t.get('assignment'):
                ledger.db.execute('INSERT OR IGNORE INTO startup_blocks VALUES(?,?)',(identity(ledger,t['executor'],cid),adapter.canonical({'transport':receipt['transport'],'process':t['id'],'reason':'startup failed before runtime receipt; review shared configuration before any further issue'}).decode()))
    return receipt

def main():
    p=argparse.ArgumentParser();sub=p.add_subparsers(dest='command',required=True)
    a=sub.add_parser('reserve-overhead');a.add_argument('--authorize-main',action='store_true',required=True)
    for name in ('ledger','assignment','executor','condition','representation','output'):a.add_argument('--'+name,required=True)
    a=sub.add_parser('prepare-job')
    for name in ('ledger','assignment','executor','qualification','keys','bindings','output','preflight','process'):a.add_argument('--'+name,required=True)
    a=sub.add_parser('import')
    for name in ('ledger','source','output'):a.add_argument('--'+name,required=True)
    a=sub.add_parser('block-startup')
    for name in ('ledger','assignment','executor','condition','process','reason'):a.add_argument('--'+name,required=True)
    a.add_argument('--elapsed',type=float)
    a=p.parse_args();ledger=adapter.Ledger(a.ledger)
    try:
        if a.command=='reserve-overhead':r=reserve_overhead(ledger,a.assignment,a.executor,a.condition,a.representation);adapter.put(a.output,r)
        elif a.command=='prepare-job':r=prepare_job(ledger,a.assignment,a.executor,a.qualification,adapter.read(a.keys),adapter.read(a.bindings),a.output,adapter.read(a.preflight),a.process)
        elif a.command=='import':r=import_return(ledger,a.source,a.output)
        else:block_startup(ledger,a.assignment,a.executor,a.condition,a.process,a.reason,a.elapsed);r={'paused':True,'released_attempts':0}
        print(adapter.canonical(r).decode())
    finally:ledger.db.close()
if __name__=='__main__':main()
