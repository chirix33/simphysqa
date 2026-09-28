"""Export compact P03 evidence and checkpoint hashes; never model weights."""
import argparse
import json
from pathlib import Path
import sys
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'src'))
from phi_jepa.artifacts import canonical
from phi_jepa.integration.readers import file_hash

parser = argparse.ArgumentParser()
parser.add_argument('--run', type=Path, required=True)
args = parser.parse_args()
root = Path(__file__).resolve().parents[1]
out = root / 'docs/reviews/artifacts/P03'
out.mkdir(parents=True, exist_ok=True)
for name in ('summary.json', 'validation-metrics.json', 'training-history.json', 'checkpoint-diagnostics.json'):
    (out / name).write_bytes((args.run / name).read_bytes())
files = {p.relative_to(args.run).as_posix(): {'bytes':p.stat().st_size,'sha256':file_hash(p)}
         for p in sorted(args.run.rglob('*')) if p.is_file()}
(out / 'native-artifacts.json').write_bytes(canonical({'root': str(args.run), 'files': files}))
print(json.dumps({'artifacts': len(files), 'native_bytes': sum(x['bytes'] for x in files.values())}))
