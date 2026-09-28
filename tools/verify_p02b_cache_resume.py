"""Verify real enrichment-cache replay with a transport that forbids dispatch."""
import argparse
import json
from pathlib import Path
import sys
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'src'))
from phi_jepa.artifacts import canonical
from phi_jepa.integration.contracts import PublicProblem
from phi_jepa.providers.cache import FrozenOutputCache
from phi_jepa.providers.openai_enrichment import OpenAIEnrichment

parser = argparse.ArgumentParser()
parser.add_argument('--profile', type=Path, required=True)
args = parser.parse_args()
root = Path(__file__).resolve().parents[1]
config = json.loads((root / 'configs/model_context_p02b.json').read_text())
asset = json.loads((root / config['enrichment_asset']).read_text())
ledger = json.loads((args.profile / 'provider-ledger.json').read_text())
original_attempts = len(ledger['events'])

def forbid(*_):
    raise AssertionError('cache-only verification attempted transport')

provider = OpenAIEnrichment('unused-no-credential-loaded', config['enrichment_provider'], asset,
    FrozenOutputCache(args.profile / 'enrichment-cache'), transport=forbid, ledger=ledger)
for row in json.loads((args.profile / 'selected-public.json').read_text()):
    problem = PublicProblem.parse(row['public'])
    actual = provider.enrich(problem, problem.input['observation_cutoff'])
    expected = json.loads((args.profile / 'enrichment' / (problem.sample_id + '.json')).read_text())
    if actual != expected:
        raise ValueError('enrichment cache mismatch')
result = {'cache_hits': provider.cache_hits, 'original_attempts_retained': original_attempts,
          'new_attempts': len(provider.runner.events) - original_attempts,
          'credentials_loaded': False, 'network_allowed': False}
if result['new_attempts'] != 0 or result['cache_hits'] != 8:
    raise ValueError('cache resume accounting mismatch')
(args.profile / 'cache-resume.json').write_bytes(canonical(result))
print(json.dumps(result))
