"""Replay all baseline answer caches with transport forbidden."""
import argparse
import json
from pathlib import Path
import sys
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'src'))
from phi_jepa.artifacts import canonical
from phi_jepa.integration.contracts import PublicProblem
from phi_jepa.providers.openai_answer import OpenAIAnswer
from phi_jepa.providers.cache import FrozenOutputCache

parser=argparse.ArgumentParser(); parser.add_argument('--run',type=Path,required=True); args=parser.parse_args()
root=Path(__file__).resolve().parents[1]; config=json.loads((args.run/'summary.json').read_text())['config']
p=PublicProblem.parse(json.loads((args.run/'validation-public.json').read_text()))
def forbidden(*args): raise AssertionError('network forbidden')
provider=OpenAIAnswer('cache-only',config['answer_profile'],json.loads((root/'docs/assets/p04a_answer_v1.json').read_text()),FrozenOutputCache(args.run/'answer-cache'),transport=forbidden)
for method in config['methods']:
    forecast=json.loads((args.run/method/'named-forecast.json').read_text()); rows=json.loads((args.run/method/'readout.json').read_text())
    expected=json.loads((args.run/method/'answer.json').read_text())['answer']
    if provider.answer(p,forecast,rows,condition=method)!=expected: raise ValueError('answer_cache_parity')
result={'replay':'exact','answer_cache_hits':provider.cache_hits,'api_attempts':len(provider.runner.events)}
(args.run/'answer-replay.json').write_bytes(canonical(result)); print(json.dumps(result))
