"""Compact Stage 5 evidence and exact native/source hashes."""
import argparse
from hashlib import sha256
import json
from pathlib import Path
import sys
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'src'))
from phi_jepa.artifacts import canonical

parser=argparse.ArgumentParser(); parser.add_argument('--run',type=Path,required=True); args=parser.parse_args()
root=Path(__file__).resolve().parents[1]; output=root/'docs/reviews/artifacts/P04b'; output.mkdir(parents=True,exist_ok=True)
for name in ('summary.json','assessment.json','calibration.json'):
    (output/name).write_bytes((args.run/name).read_bytes())
evaluation=json.loads((args.run/'evaluation.json').read_text())
compact={k:v for k,v in evaluation.items() if k not in ('autonomous','recorded_input_one_step_diagnostic','deterministic_answer_fallback')}
for mode in ('autonomous','recorded_input_one_step_diagnostic'):
    compact[mode]={k:v for k,v in evaluation[mode].items() if k!='per_time_channel'}
(output/'evaluation-summary.json').write_bytes(canonical(compact))
drift=json.loads((args.run/'drift.json').read_text())
(output/'terminal-drift.json').write_bytes(canonical({'meaning':drift['meaning'],'terminal':drift['rows'][-1]}))
replay=json.loads((args.run/'offline-replay.json').read_text())
(output/'offline-replay.json').write_bytes(canonical({k:v for k,v in replay.items() if k!='fallback_formatter'}))
native={p.relative_to(args.run).as_posix():{'sha256':sha256(p.read_bytes()).hexdigest(),'bytes':p.stat().st_size} for p in sorted(args.run.rglob('*')) if p.is_file()}
(output/'native-artifacts.json').write_bytes(canonical(native))
paths=[*root.glob('src/phi_jepa/assessment/*.py'),root/'src/phi_jepa/typed_evaluation.py',root/'src/phi_jepa/providers/openai_judge.py',root/'src/phi_jepa/inference/readout.py',*root.glob('tools/*p04b*.py'),root/'tests/test_p04b.py',root/'configs/assessment_p04b.json']
(output/'source-inventory.json').write_bytes(canonical({p.relative_to(root).as_posix():sha256(p.read_bytes()).hexdigest() for p in sorted(paths)}))
print(json.dumps({'native_files':len(native),'output':str(output)}))
