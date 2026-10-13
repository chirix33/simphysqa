"""Explicit post-result external-restart exception /1.0.0.

Additive attempt tables in the SAME authoritative database. Original stages,
returns, routes and interrupted process are never changed. The sealed adapter is
reused with table-scoped SQL; every recovery process is charged by original
allocation triggers. This layer is not a generic retry facility.
"""
import json,re,uuid
from pathlib import Path
from . import execution_adapter as adapter,main_allocation,main_record_index

VERSION='SPQ06-authorized-restart-execution/1.0.0'
TABLES=('stages','routes','returns','transports')

class AttemptConnection:
    def __init__(self,db):self.original=db
    def execute(self,sql,args=()):
        for name in TABLES:sql=re.sub(r'\b'+name+r'\b','restart_'+name,sql)
        return self.original.execute(sql,args)
    def __getattr__(self,name):return getattr(self.original,name)

def original_records(ledger):
    base=main_allocation.Ledger(ledger.path)
    try:return main_record_index.canonical_records(base)
    finally:base.db.close()

def install(ledger,freeze):
    if not freeze.get('explicit_post_result_authorization') or not freeze.get('authorization_text'):
        raise ValueError('dated explicit post-result authorization required')
    if freeze['remaining_at_freeze_seconds']>ledger.remaining(freeze['executor'])+1e-6:
        raise ValueError('remaining allocation changed')
    eligible=freeze['eligible'];keys=[r['key'] for r in eligible]
    if not keys or len(set(keys))!=len(keys):raise ValueError('unique exact missing keys required')
    original=original_records(ledger)
    for r in eligible:
        row=ledger.db.execute('SELECT process,request_hash,state FROM stages WHERE key=?',(r['key'],)).fetchone()
        process=ledger.db.execute('SELECT bound,actual,state FROM processes WHERE id=?',(r['original_process'],)).fetchone()
        if row!=(r['original_process'],r['request_sha256'],'interrupted') or not process or process[1] is not None or process[2]!='interrupted':
            raise ValueError('only documented original interrupted missing stages')
        if r['key'] in original:raise ValueError('saved original result must be imported, never regenerated')
    if ledger.meta('fixture')!='True':
        if len(keys)!=35 or any(k.split('|')[1:]!=['qwen3_8b_direct','structured_only','1'] for k in keys):
            raise ValueError('authorization is exactly 35 Qwen structured-only restart initials')
    db=ledger.db
    db.executescript("""
      CREATE TABLE restart_freeze(hash TEXT PRIMARY KEY,body TEXT NOT NULL);
      CREATE TABLE restart_eligible(key TEXT PRIMARY KEY,original_process TEXT NOT NULL,request_hash TEXT NOT NULL);
      CREATE TABLE restart_stages(key TEXT PRIMARY KEY,process TEXT NOT NULL REFERENCES processes(id),request_hash TEXT NOT NULL,state TEXT NOT NULL);
      CREATE TABLE restart_routes(key TEXT PRIMARY KEY,body TEXT NOT NULL);
      CREATE TABLE restart_returns(key TEXT NOT NULL,artifact TEXT NOT NULL,source TEXT NOT NULL,valid INTEGER NOT NULL,reason TEXT,PRIMARY KEY(key,artifact));
      CREATE TABLE restart_transports(id TEXT PRIMARY KEY,body TEXT NOT NULL);
      CREATE TABLE restart_processes(id TEXT PRIMARY KEY,authorization_hash TEXT NOT NULL REFERENCES restart_freeze(hash));
      CREATE TRIGGER restart_scope BEFORE INSERT ON restart_stages BEGIN
        SELECT CASE WHEN NOT EXISTS(SELECT 1 FROM restart_processes WHERE id=NEW.process) THEN RAISE(ABORT,'recovery process authorization required') END;
        SELECT CASE WHEN NOT EXISTS(SELECT 1 FROM restart_eligible WHERE key=NEW.key OR key=substr(NEW.key,1,length(NEW.key)-1)||'1' AND NEW.key LIKE '%|2') THEN RAISE(ABORT,'outside restart eligibility') END;
        SELECT CASE WHEN EXISTS(SELECT 1 FROM stages WHERE key=NEW.key AND state!='interrupted') THEN RAISE(ABORT,'existing noninterrupted reservation excluded') END;
      END;
      CREATE TRIGGER restart_eligible_no_update BEFORE UPDATE ON restart_eligible BEGIN SELECT RAISE(ABORT,'frozen eligibility'); END;
      CREATE TRIGGER restart_eligible_no_delete BEFORE DELETE ON restart_eligible BEGIN SELECT RAISE(ABORT,'frozen eligibility'); END;
    """)
    def add():
        db.execute('INSERT INTO restart_freeze VALUES(?,?)',(adapter.digest(freeze),adapter.canonical(freeze).decode()))
        db.executemany('INSERT INTO restart_eligible VALUES(?,?,?)',[(r['key'],r['original_process'],r['request_sha256']) for r in eligible])
    ledger.transaction(add)

class Ledger(main_allocation.Ledger):
    def __init__(self,path):
        super().__init__(path);self.db=AttemptConnection(self.db)
        row=self.db.execute('SELECT hash,body FROM restart_freeze').fetchone()
        if not row:raise ValueError('frozen restart authorization required')
        self.authorization_hash,self.freeze=row[0],json.loads(row[1])
    def pending(self,assignment,executor):
        keys=super().pending(assignment,executor)
        allowed={r[0] for r in self.db.execute('SELECT key FROM restart_eligible')}
        return [k for k in keys if k in allowed or k.endswith('|2') and k[:-1]+'1' in allowed]
    def reserve(self,assignment,executor,keys,*args,**kwargs):
        if not keys or any(k not in self.pending(assignment,executor) for k in keys):raise ValueError('never-reserved recovery keys only')
        original=original_records(self)
        if any(k.endswith('|1') and k in original for k in keys):raise ValueError('genuine saved original found; no regeneration')
        return super().reserve(assignment,executor,keys,*args,**kwargs)
    def reserve_overhead(self,assignment,executor):
        if executor!=self.freeze['executor']:raise ValueError('authorized recovery executor only')
        self.assignment(assignment,executor)
        identity=str(uuid.uuid4())
        def op():
            count=self.db.execute('SELECT COUNT(*) FROM restart_processes').fetchone()[0]
            if count>=self.freeze['maximum_processes']:raise ValueError('recovery process ceiling')
            self.db.execute('INSERT INTO restart_processes VALUES(?,?)',(identity,self.authorization_hash))
            self.db.execute('INSERT INTO processes VALUES(?,?,?,?,?)',(identity,assignment,600,None,'reserved_unknown'))
        self.transaction(op);return identity

def combined_records(ledger):
    original=original_records(ledger)
    attempts=ledger if isinstance(ledger,Ledger) else Ledger(ledger.path)
    try:
        recovered=main_record_index.canonical_records(attempts)
        blocked=set(adapter.conflicts(attempts))
        blocked.update(k[:-1]+'2' for k in list(blocked) if k.endswith('|1'))
        for key,raw in recovered.items():
            if key in original and adapter.digest(original[key])!=adapter.digest(raw):
                raise ValueError('conflicting genuine original and recovery; explicit disposition required')
            original[key]=raw
        return {k:r for k,r in original.items() if k not in blocked}
    finally:
        if attempts is not ledger:attempts.db.close()

def route(ledger,key,preparation,output):
    if key not in {r['key'] for r in ledger.freeze['eligible']} or not key.endswith('|1'):
        raise ValueError('only recovered eligible first turns may route')
    old=ledger.db.original.execute('SELECT body FROM routes WHERE key=?',(key[:-1]+'2',)).fetchone()
    if not old or json.loads(old[0]).get('actual_raw') is not None:raise ValueError('original null-response history required')
    receipt=adapter.coordinate_reply(ledger,key,preparation,output)
    # Preserve the sealed route bytes used by workers/importer. History linkage is
    # a separate receipt, not a change to the actual continuation request.
    adapter.put(Path(str(output)+'.history.json'),{'version':VERSION,'authorization_hash':ledger.authorization_hash,
       'original_null_response_receipt':json.loads(old[0]),'original_receipt_sha256':adapter.digest(json.loads(old[0])),
       'new_route_sha256':adapter.digest(receipt),'recovered_initial_sha256':receipt['initial_result_sha256']})
    return receipt
