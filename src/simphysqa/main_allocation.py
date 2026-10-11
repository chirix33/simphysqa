"""Central main executor sublimits /1.0.0; sealed public adapter stays unchanged.

SQLite guards apply to every connection, including historical adapter clients.
Known overruns are retained; only new reservations/bound extensions are rejected.
Engineering implementation time is excluded. Run preparation, verification,
preflight, full launcher lifecycle and central processing are charged once.
"""
import math
import uuid
from . import execution_adapter as adapter

VERSION = 'SPQ06-main-allocation/1.0.0'
CHARGE = "CASE WHEN p.actual IS NULL OR p.state IN ('unknown','interrupted') THEN MAX(p.bound,COALESCE(p.actual,0)) ELSE p.actual END"

def install(ledger, allocations):
    if not allocations or any(not owner or not math.isfinite(limit) or limit <= 0 for owner, limit in allocations.items()):
        raise ValueError('explicit positive executor allocations required')
    if sum(allocations.values()) != float(ledger.meta('ceiling')):
        raise ValueError('allocations must partition the fixed shared ceiling')
    ledger.db.executescript('''
      CREATE TABLE executor_allocations(owner TEXT PRIMARY KEY,ceiling REAL NOT NULL);
      CREATE TABLE control_work(id TEXT PRIMARY KEY,owner TEXT NOT NULL REFERENCES executor_allocations(owner),purpose TEXT NOT NULL,bound REAL NOT NULL,actual REAL,state TEXT NOT NULL);
      CREATE TABLE dispatcher_gaps(process TEXT PRIMARY KEY REFERENCES processes(id),seconds REAL NOT NULL,evidence TEXT NOT NULL);
      CREATE TRIGGER allocations_no_update BEFORE UPDATE ON executor_allocations BEGIN SELECT RAISE(ABORT,'frozen executor allocation'); END;
      CREATE TRIGGER allocations_no_delete BEFORE DELETE ON executor_allocations BEGIN SELECT RAISE(ABORT,'frozen executor allocation'); END;
    ''')
    ledger.db.executemany('INSERT INTO executor_allocations VALUES(?,?)', allocations.items())
    # Include controls and outer dispatcher gaps in both guards. A bare adapter
    # connection cannot bypass the split by ignoring the derived Python totals.
    process_sum = f'(SELECT COALESCE(SUM({CHARGE}),0) FROM processes p JOIN assignments a ON a.id=p.assignment WHERE a.owner=NEWOWNER)'
    control_sum = "(SELECT COALESCE(SUM(CASE WHEN actual IS NULL OR state IN ('unknown','interrupted') THEN MAX(bound,COALESCE(actual,0)) ELSE actual END),0) FROM control_work WHERE owner=NEWOWNER)"
    gap_sum = '(SELECT COALESCE(SUM(g.seconds),0) FROM dispatcher_gaps g JOIN processes p ON p.id=g.process JOIN assignments a ON a.id=p.assignment WHERE a.owner=NEWOWNER)'
    owner_total = process_sum + '+' + control_sum + '+' + gap_sum
    shared_total = f'(SELECT COALESCE(SUM({CHARGE}),0) FROM processes p)'+ '+' + control_sum.replace(' WHERE owner=NEWOWNER','') + '+' + '(SELECT COALESCE(SUM(seconds),0) FROM dispatcher_gaps)'
    for table, event, owner, when in (
        ('processes','INSERT', '(SELECT owner FROM assignments WHERE id=NEW.assignment)', ''),
        ('processes','UPDATE', '(SELECT owner FROM assignments WHERE id=NEW.assignment)', 'WHEN NEW.bound != OLD.bound'),
        ('control_work','INSERT', 'NEW.owner', ''),
    ):
        total = owner_total.replace('NEWOWNER', owner)
        ledger.db.executescript(f'''CREATE TRIGGER guard_{table}_{event.lower()} AFTER {event} ON {table} {when}
          BEGIN
            SELECT CASE WHEN NOT EXISTS(SELECT 1 FROM executor_allocations WHERE owner={owner}) THEN RAISE(ABORT,'unallocated executor') END;
            SELECT CASE WHEN {total} > (SELECT ceiling FROM executor_allocations WHERE owner={owner}) THEN RAISE(ABORT,'executor reservation ceiling exhausted') END;
            SELECT CASE WHEN {shared_total} > CAST((SELECT v FROM meta WHERE k='ceiling') AS REAL) THEN RAISE(ABORT,'shared reservation ceiling exhausted') END;
          END;''')

class Ledger(adapter.Ledger):
    def executor_used(self, owner):
        if not self.db.execute('SELECT 1 FROM executor_allocations WHERE owner=?',(owner,)).fetchone():
            raise ValueError('unallocated executor')
        process = self.db.execute(f'SELECT COALESCE(SUM({CHARGE}),0) FROM processes p JOIN assignments a ON a.id=p.assignment WHERE a.owner=?',(owner,)).fetchone()[0]
        control = self.db.execute("SELECT COALESCE(SUM(CASE WHEN actual IS NULL OR state IN ('unknown','interrupted') THEN MAX(bound,COALESCE(actual,0)) ELSE actual END),0) FROM control_work WHERE owner=?",(owner,)).fetchone()[0]
        gaps = self.db.execute('SELECT COALESCE(SUM(g.seconds),0) FROM dispatcher_gaps g JOIN processes p ON p.id=g.process JOIN assignments a ON a.id=p.assignment WHERE a.owner=?',(owner,)).fetchone()[0]
        return process + control + gaps

    def used(self):
        return sum(self.executor_used(row[0]) for row in self.db.execute('SELECT owner FROM executor_allocations').fetchall())

    def remaining(self, owner):
        ceiling = self.db.execute('SELECT ceiling FROM executor_allocations WHERE owner=?',(owner,)).fetchone()
        if ceiling is None: raise ValueError('unallocated executor')
        return min(ceiling[0]-self.executor_used(owner),float(self.meta('ceiling'))-self.used())

    def reserve_control(self, owner, purpose, bound=600):
        if not math.isfinite(bound) or bound <= 0: raise ValueError('positive control reservation')
        self.remaining(owner)
        identity = str(uuid.uuid4())
        def operation():
            if self.used()+bound > float(self.meta('ceiling')): raise ValueError('shared control ceiling exhausted')
            self.db.execute('INSERT INTO control_work VALUES(?,?,?,?,?,?)',(identity,owner,purpose,bound,None,'reserved_unknown'))
        self.transaction(operation)
        return identity

    def settle_control(self, identity, elapsed, state='complete'):
        if not math.isfinite(elapsed) or elapsed < 0 or state not in ('complete','failed','unknown','interrupted'): raise ValueError('invalid control accounting')
        if self.db.execute('UPDATE control_work SET actual=?,state=? WHERE id=? AND actual IS NULL',(elapsed,state,identity)).rowcount != 1:
            raise ValueError('control already settled or unknown')

    def add_dispatcher_gap(self, process, seconds, evidence):
        if not math.isfinite(seconds) or seconds < 0: raise ValueError('invalid dispatcher gap')
        # A known actual overrun is evidence, not permission to issue more work.
        self.db.execute('INSERT INTO dispatcher_gaps VALUES(?,?,?)',(process,seconds,adapter.canonical(evidence).decode()))

    def summary(self):
        allocations = [{'executor':owner,'ceiling_seconds':limit,'accounted_seconds':self.executor_used(owner),'remaining_seconds':limit-self.executor_used(owner)} for owner,limit in self.db.execute('SELECT owner,ceiling FROM executor_allocations')]
        return {'version':VERSION,'shared_ceiling_seconds':float(self.meta('ceiling')),'accounted_seconds':self.used(),'remaining_seconds':float(self.meta('ceiling'))-self.used(),'allocations':allocations,'unknown_processes':self.db.execute("SELECT COUNT(*) FROM processes WHERE actual IS NULL OR state IN ('unknown','interrupted')").fetchone()[0]}
