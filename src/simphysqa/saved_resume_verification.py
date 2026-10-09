"""Exercise completed saved-output resume with all live boundaries disabled."""
import argparse
from collections import Counter
from pathlib import Path
from unittest.mock import patch
from .io import read, write, external, canonical
from .formal_sampling import file_hash
from . import heldout_live, main_preparation

def snapshot(root):
    return {p.relative_to(root).as_posix():file_hash(p) for p in root.rglob('*') if p.is_file()}

def verify(run, pilot, preparation, output):
    run=external(run);pilot=external(pilot);preparation=external(preparation);output=external(output)
    completed=[read(p) for p in run.glob('cases/*/status.json') if read(p)['status']=='completed']
    counts=Counter(s['cell'] for s in completed)
    if len(completed)!=400 or len(counts)!=20 or set(counts.values())!={20}:
        raise ValueError('only a completed 400-item export can exercise this zero-work resume proof')
    before=snapshot(run);export_before=snapshot(preparation);calls=[]
    def forbidden(*args, **kwargs):
        calls.append('unexpected_live_boundary')
        raise heldout_live.CeilingReached('resume proof forbids new annotation/simulation/derivation work')
    with patch.object(heldout_live,'annotate',forbidden),patch.object(heldout_live,'simulate',forbidden),patch.object(heldout_live,'derive',forbidden):
        result=heldout_live.process(run)
        main_preparation.export(run,pilot,preparation)
    after=snapshot(run);export_after=snapshot(preparation)
    if calls or result['shortfall'] or result['stop_reason']:
        raise ValueError('saved resume attempted new work or lost qualification')
    if any(after.get(p)!=h for p,h in before.items()) or export_before!=export_after:
        raise ValueError('saved resume changed a prior file')
    added=sorted(set(after)-set(before))
    if len(added)!=1 or not added[0].startswith('summaries/'):
        raise ValueError('resume added files other than its immutable summary snapshot')
    report={'version':'SPQ06-actual-saved-resume/1.0.0','qualified_items':400,
        'existing_run_files_preserved':len(before),'existing_export_files_preserved':len(export_before),
        'added_summary':added[0],'new_annotation_requests':0,'new_simulator_executions':0,
        'new_static_compilations':0,'new_answering_calls':0,'existing_hashes_unchanged':True,
        'run_before_file_hashes':before,'export_before_file_hashes':export_before}
    write(output/'saved-resume-verification.json',report)
    return {k:v for k,v in report.items() if not k.endswith('file_hashes')}

if __name__=='__main__':
    p=argparse.ArgumentParser()
    for name in ('run','pilot','preparation','output'):p.add_argument('--'+name,type=Path,required=True)
    a=p.parse_args();print(canonical(verify(a.run,a.pilot,a.preparation,a.output)).decode())
