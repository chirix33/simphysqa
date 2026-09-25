"""Compact Stage 6 results, independent checkpoint hashes and source inventory."""
import argparse
from hashlib import sha256
import json
from pathlib import Path
import sys
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'src'))
from phi_jepa.artifacts import canonical

parser=argparse.ArgumentParser(); parser.add_argument('--run',type=Path,required=True); parser.add_argument('--ablations',action='store_true'); args=parser.parse_args()
root=Path(__file__).resolve().parents[1]; out=root/'docs/reviews/artifacts/P05b'
if args.ablations: out=out/'ablations'
out.mkdir(parents=True,exist_ok=True)
summary=json.loads((args.run/'summary.json').read_text())
compact={k:v for k,v in summary.items() if k!='provenance'}
compact['provenance']={k:v for k,v in summary['provenance'].items() if k!='source'}
if 'fixed_projection_lr' in compact['methods']:
    lr=compact['methods']['fixed_projection_lr']
    lr_width=len(json.loads((args.run/'fixed_projection_lr/trajectory.json').read_text())['predictions'][0]['values'])
    lr['fitted_coefficient_count']=lr['fit']['design_columns']*lr_width
(out/'summary.json').write_bytes(canonical(compact))
for name in ('answer-summary.json','evaluation.json','deployment-replay.json'):
    (out/name).write_bytes((args.run/name).read_bytes())
native={p.relative_to(args.run).as_posix():{'sha256':sha256(p.read_bytes()).hexdigest(),'bytes':p.stat().st_size} for p in sorted(args.run.rglob('*')) if p.is_file()}
(out/'native-artifacts.json').write_bytes(canonical(native))
paths=[*root.glob('src/phi_jepa/baselines/*.py'),root/'src/phi_jepa/inference/readout.py',root/'src/phi_jepa/training/pairs.py',*root.glob('tools/*p05b*.py'),root/'tests/test_p05b.py',root/'configs/baselines_p05b.json',root/'configs/ablations_p05b.json']
(out/'source-inventory.json').write_bytes(canonical({p.relative_to(root).as_posix():sha256(p.read_bytes()).hexdigest() for p in sorted(paths)}))
print(json.dumps({'native_files':len(native),'output':str(out)}))
