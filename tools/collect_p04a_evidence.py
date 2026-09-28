"""Copy compact evidence, hash native artifacts, preserve original assets."""
import argparse
from hashlib import sha256
import json
from pathlib import Path
import sys
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'src'))
from phi_jepa.artifacts import canonical

parser=argparse.ArgumentParser(); parser.add_argument('--run',type=Path,required=True); args=parser.parse_args()
root=Path(__file__).resolve().parents[1]; output=root/'docs/reviews/artifacts/P04a'; output.mkdir(parents=True,exist_ok=True)
for name in ('identity.json','summary.json','paired-metrics.json','public-bindings.json','cache-replay.json'):
    (output/name).write_bytes((args.run/name).read_bytes())
native={p.relative_to(args.run).as_posix():{'sha256':sha256(p.read_bytes()).hexdigest(),'bytes':p.stat().st_size} for p in sorted(args.run.rglob('*')) if p.is_file()}
(output/'native-artifacts.json').write_bytes(canonical(native))
paths=[*root.glob('src/phi_jepa/inference/*.py'),root/'src/phi_jepa/providers/openai_answer.py',*root.glob('tools/*p04a*.py'),root/'tests/test_p04a.py',root/'configs/answer_p04a.json',root/'docs/assets/p04a_answer_v1.json']
(output/'source-inventory.json').write_bytes(canonical({p.relative_to(root).as_posix():sha256(p.read_bytes()).hexdigest() for p in sorted(paths)}))
print(json.dumps({'native_files':len(native),'output':str(output)}))
