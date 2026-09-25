"""Offline bank/assessment and V1 response replay; no model solve or API call."""
import argparse
import json
from pathlib import Path
import sys
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'src'))
from phi_jepa.artifacts import canonical,digest
from phi_jepa.integration.contracts import PublicProblem
from phi_jepa.integration.layout import StateLayout
from phi_jepa.assessment.reference import ReferenceBank
from phi_jepa.providers.openai_judge import OpenAIJudge
from phi_jepa.providers.cache import FrozenOutputCache
from phi_jepa.assessment.fixed import deterministic_answer,bounded_fallback

parser=argparse.ArgumentParser(); parser.add_argument('--run',type=Path,required=True); parser.add_argument('--answer-run',type=Path,required=True); args=parser.parse_args()
root=Path(__file__).resolve().parents[1]
summary=json.loads((args.run/'summary.json').read_text())
p=PublicProblem.parse(json.loads((args.answer_run/'public.json').read_text()))
prompts=json.loads((root/'docs/assets/prompts.json').read_text())
asset={'prompt':prompts['JUDGE_PROMPT'],'schema':json.loads((root/'docs/assets/judge_schema.json').read_text())}
def forbidden(*args): raise AssertionError('network forbidden')
provider=OpenAIJudge('cache-only',summary['provider_config'],asset,FrozenOutputCache(args.run/'judge-cache'),transport=forbidden)
if provider.judge(p)!=summary['judge']: raise ValueError('judge_replay')
bank_path=next((args.run/'bank').glob('*.json')); data=json.loads(bank_path.read_text())
bank=ReferenceBank.load(bank_path,identity=data['identity'])
if bank.sha256!=summary['familiarity']['bank_sha256']: raise ValueError('bank_identity')
forecast=json.loads((args.run/'named-forecast.json').read_text())
fallback=bounded_fallback(forecast,failure='answer_failure',numeric_formatter=lambda value:deterministic_answer(p,value))
result={'judge_replay':'exact','judge_cache_hits':provider.cache_hits,'judge_calls':len(provider.runner.events),
    'bank_integrity':'verified','fallback_original_preserved':fallback['returned_prediction']==forecast,
    'fallback_formatter':fallback['replacement']}
(args.run/'offline-replay.json').write_bytes(canonical(result))
print(json.dumps({k:v for k,v in result.items() if k!='fallback_formatter'}))
