"""Reconstruct and replay the three exact answer requests with transport forbidden."""
import argparse
from copy import deepcopy
import json
from pathlib import Path
import sys
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'src'))
from phi_jepa.artifacts import canonical
from phi_jepa.integration.contracts import PublicProblem
from phi_jepa.inference.readout import read_targets,target_result
from phi_jepa.providers.openai_answer import OpenAIAnswer
from phi_jepa.providers.cache import FrozenOutputCache

parser=argparse.ArgumentParser(); parser.add_argument('--run',type=Path,required=True); args=parser.parse_args()
root=Path(__file__).resolve().parents[1]
p=PublicProblem.parse(json.loads((args.run/'public.json').read_text()))
forecast=json.loads((args.run/'named-forecast.json').read_text())
rev=deepcopy(forecast)
for row,other in zip(rev['states'],reversed(forecast['states'])): row['measurements']=deepcopy(other['measurements'])
absent=[target_result(t,'unsupported',reason='no_forecast_in_public_only_control',source='control') for t in p.input['answer_spec']]
conditions={'public_only':(None,absent),'predicted':(forecast,read_targets(p,forecast)),'reversed_forecast':(rev,read_targets(p,rev))}
def forbidden(*args): raise AssertionError('No network permitted in replay')
provider=OpenAIAnswer('cache-only',json.loads((root/'configs/answer_p04a.json').read_text()),
    json.loads((root/'docs/assets/p04a_answer_v1.json').read_text()),FrozenOutputCache(args.run/'answer-cache'),transport=forbidden)
for name,(supplied,outcomes) in conditions.items():
    actual=provider.answer(p,supplied,outcomes,condition=name)
    expected=json.loads((args.run/(name+'.json')).read_text())['answer']
    if actual!=expected: raise ValueError('replay mismatch')
result={'replay':'exact','cache_hits':provider.cache_hits,'api_attempts':len(provider.runner.events)}
(args.run/'cache-replay.json').write_bytes(canonical(result)); print(json.dumps(result))
