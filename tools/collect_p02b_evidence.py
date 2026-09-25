"""Copy only compact measurement summaries, never keys/weights/provider text."""
import argparse
import json
from pathlib import Path
import sys
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'src'))
from phi_jepa.artifacts import canonical
from phi_jepa.integration.readers import file_hash
from phi_jepa.providers.qwen import REVISION

parser = argparse.ArgumentParser()
parser.add_argument('--profile', type=Path, required=True)
parser.add_argument('--cache-dir', type=Path, required=True)
args = parser.parse_args()
root = Path(__file__).resolve().parents[1]
destination = root / 'docs/reviews/artifacts/P02b'
names = ['coverage-summary.json', 'provider-summary.json', 'provider-ledger.json',
         'provider-outcomes.json', 'encode-base-summary.json', 'encode-enriched-summary.json', 'cache-resume.json']
for name in names:
    content = (args.profile / name).read_bytes()
    (destination / name).write_bytes(content)
snapshot = args.cache_dir / 'models--Qwen--Qwen3-Embedding-0.6B' / 'snapshots' / REVISION
inventory = {p.relative_to(snapshot).as_posix(): {'sha256': file_hash(p), 'bytes': p.stat().st_size}
             for p in sorted(snapshot.rglob('*')) if p.is_file()}
(destination / 'encoder-assets.json').write_bytes(canonical({'revision': REVISION, 'files': inventory}))
base = json.loads((args.profile / 'encode-base-summary.json').read_text())
enriched = json.loads((args.profile / 'encode-enriched-summary.json').read_text())
provider = json.loads((args.profile / 'provider-summary.json').read_text())
usages = [event['usage'] for event in provider['events']]
summary = {'encoder_asset_bytes': sum(x['bytes'] for x in inventory.values()),
    'live_attempts': len(usages), 'input_tokens': sum(x['input_tokens'] for x in usages),
    'output_tokens': sum(x['output_tokens'] for x in usages),
    'usage_priced_usd': sum(x['cost_usd'] for x in usages),
    'base_peak_allocated_bytes': base['cuda_peak_allocated_bytes'],
    'enriched_peak_allocated_bytes': enriched['cuda_peak_allocated_bytes'],
    'encoder_model_calls': base['coverage']['model_calls'] + enriched['coverage']['model_calls'],
    'embedding_cache_hits': base['coverage']['cache_hits'] + enriched['coverage']['cache_hits'],
    'enriched_min_tokens': min(x['token_count'] for x in enriched['outcomes']),
    'enriched_max_tokens': max(x['token_count'] for x in enriched['outcomes']),
    'projection_norm_range': [min(x['projection_l2_norm'] for x in enriched['outcomes']), max(x['projection_l2_norm'] for x in enriched['outcomes'])],
    'question_sensitivity_range': [min(x['question_perturbation_projection_l2'] for x in enriched['outcomes']), max(x['question_perturbation_projection_l2'] for x in enriched['outcomes'])],
    'provider_returned_models': sorted({x['returned_model'] for x in provider['responses']}),
    'provider_wall_seconds': provider['wall_seconds'], 'gpu': enriched['gpu']}
(destination / 'measured-summary.json').write_bytes(canonical(summary))
print(json.dumps(summary))
