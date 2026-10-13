"""Central immutable-return index /1.1.0; same canonicalization, fewer reads.

Hash each unique imported source once per lookup, instead of once per item.
Never caches across calls/transactions. A conflict blocks the item and its
conditional stage exactly as in the sealed adapter. No parser/scorer changes.
"""
from collections import defaultdict
from contextlib import contextmanager
from pathlib import Path
import sqlite3
from . import execution_adapter as adapter
from . import main_allocation

VERSION='SPQ06-main-record-index/1.1.0'

def canonical_records(ledger):
    blocked=set(adapter.conflicts(ledger))
    blocked.update(key[:-1]+'2' for key in list(blocked) if key.endswith('|1'))
    sources=defaultdict(list)
    for key,source in ledger.db.execute('SELECT key,source FROM returns WHERE valid=1'):
        if key not in blocked:sources[source].append(key)
    result={}
    for source,keys in sources.items():
        path=Path(source);envelope=adapter.read(path/'return-envelope.json');actual=adapter.files(path)
        manifest_hash=actual.pop('return-envelope.json')
        if actual!=envelope['files']:raise ValueError('immutable imported source changed')
        transport=adapter.digest({**actual,'return-envelope.json':manifest_hash})
        if not ledger.db.execute('SELECT 1 FROM transports WHERE id=?',(transport,)).fetchone():raise ValueError('immutable transport envelope changed')
        entries={entry['key']:entry for entry in envelope['entries']}
        for key in keys:result[key]=adapter.read(adapter.within(path,entries[key]['result']))
    # Native history applies only to the original core connection. Scoped restart/
    # complement connections retain their own namespace; their core joins happen later.
    if isinstance(ledger.db, sqlite3.Connection):
        from .native_reconciliation import canonical_native, exists
        native = canonical_native(ledger)
        if exists(ledger, 'native_entries'):
            for (key,) in ledger.db.execute('SELECT key FROM native_entries'):
                if key not in native:
                    blocked.update((key, key[:-1] + '2'))
        result.update(native)
        result = {k: v for k, v in result.items() if k not in blocked}
    return result

@contextmanager
def transaction_snapshot(ledger):
    """Verified immutable snapshot, only while holding central BEGIN IMMEDIATE."""
    if not ledger.db.in_transaction:raise ValueError('central write transaction required for snapshot')
    original=adapter.canonical_records;snapshot=None
    def lookup(requested):
        nonlocal snapshot
        if requested is not ledger:return original(requested)
        if snapshot is None:snapshot=canonical_records(ledger)
        return snapshot
    adapter.canonical_records=lookup
    try:yield
    finally:adapter.canonical_records=original

class Ledger(main_allocation.Ledger):
    def transaction(self,operation):
        def guarded():
            with transaction_snapshot(self):return operation()
        return super().transaction(guarded)
