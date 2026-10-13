"""Central main immutable importer wrapper /1.0.0.

Preserves sealed adapter policy and bytes. Handles its conflicting-lifecycle SQL
syntax defect conservatively: both transports remain, key conflicts block scoring,
and the process retains its full bound or actual overrun as unknown. Never selects
the successful/latest result. Other errors propagate without fabricated receipts.
"""
import sqlite3,uuid,math
from pathlib import Path
from . import execution_adapter as adapter,main_execution_queue as queue

def import_return(ledger,source,root):
    try:return queue.import_return(ledger,source,root)
    except sqlite3.OperationalError as exc:
        if 'near "IN": syntax error' not in str(exc):raise
        envelope=adapter.read(Path(source)/'return-envelope.json');ticket=adapter.read(Path(source)/'ticket.json');incoming=adapter.read(Path(source)/'process-receipt.json')
        process=ticket['id'];row=ledger.db.execute('SELECT actual,state,bound,assignment FROM processes WHERE id=?',(process,)).fetchone()
        seconds=incoming.get('elapsed_seconds')
        if not row or row[0] is None or row[3]!=ticket['assignment'] or not isinstance(seconds,(int,float)) or not math.isfinite(seconds) or seconds<0:raise
        hashes=adapter.files(Path(source));transport=adapter.digest(hashes)
        paths={r[0] for r in ledger.db.execute('SELECT source FROM returns') if Path(r[0]).parent.resolve()==Path(root).resolve() and adapter.digest(adapter.files(Path(r[0])))==transport}
        if len(paths)!=1:raise ValueError('conflicting-lifecycle immutable source unresolved') from exc
        dest=Path(next(iter(paths)));keys=[entry['key'] for entry in envelope['entries']]
        if not all(ledger.db.execute('SELECT 1 FROM returns WHERE key=? AND source=?',(key,str(dest))).fetchone() for key in keys):raise
        # This exact sealed branch is reached only after authenticated envelope,
        # known reservation and entry validation. Mark all relevant keys unresolved.
        ledger.db.execute('UPDATE processes SET actual=?,state=? WHERE id=?',(max(row[0],seconds),'unknown',process))
        receipt={'version':'SPQ06-central-import/1.0.0','transport':transport,'source_root':str(dest),'identical_duplicate_transport':False,
            'accepted_keys':[],'validation_failures':[{'process_reservation':process,'reason':'conflicting lifecycle receipts; sealed SQL defect handled conservatively; full bound/overrun retained; no preferred artifact','original_error':str(exc)}],
            'conflicts':adapter.conflicts(ledger),'aggregate_charged_seconds':ledger.used(),'disposition_required':True}
        ledger.db.execute('INSERT OR IGNORE INTO transports VALUES(?,?)',(transport,adapter.canonical(receipt).decode()))
        adapter.put(Path(root)/('import-conflict-'+str(uuid.uuid4())+'.json'),receipt)
        return receipt
