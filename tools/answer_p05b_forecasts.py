"""Same frozen Stage 4 answer interface for each independently trained comparison."""
import argparse
import json
from pathlib import Path
import sys
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'src'))
from phi_jepa.artifacts import canonical
from phi_jepa.integration.contracts import PublicProblem
from phi_jepa.providers.cache import FrozenOutputCache
from phi_jepa.providers.credentials import load_openai_key
from phi_jepa.providers.openai_answer import OpenAIAnswer,AnswerParseFailure
from phi_jepa.providers.contracts import ProviderFailure

parser=argparse.ArgumentParser(); parser.add_argument('--run',type=Path,required=True); args=parser.parse_args()
root=Path(__file__).resolve().parents[1]; config=json.loads((args.run/'summary.json').read_text())['config']
p=PublicProblem.parse(json.loads((args.run/'validation-public.json').read_text()))
def save(path,value):
    temp=path.with_suffix(path.suffix+'.tmp'); temp.write_bytes(canonical(value)); temp.replace(path)
ledger_path=args.run/'answer-ledger.json'; ledger=json.loads(ledger_path.read_text()) if ledger_path.exists() else None
provider=OpenAIAnswer(load_openai_key(root/'.env'),config['answer_profile'],json.loads((root/'docs/assets/p04a_answer_v1.json').read_text()),
    FrozenOutputCache(args.run/'answer-cache'),ledger=ledger,event_sink=lambda value:save(ledger_path,value))
results={}
for method in config['methods']:
    path=args.run/method/'answer.json'
    if path.exists(): results[method]=json.loads(path.read_text()); continue
    forecast=json.loads((args.run/method/'named-forecast.json').read_text()); outcomes=json.loads((args.run/method/'readout.json').read_text())
    try: result={'status':'success','answer':provider.answer(p,forecast,outcomes,condition=method)}
    except AnswerParseFailure as exc: result={'status':'parser_failure','reason':exc.reason}
    except ProviderFailure as exc: result={'status':'api_failure','reason':exc.code.value}
    save(path,result); results[method]=result; print(json.dumps({'method':method,'status':result['status']}),flush=True)
events=provider.runner.events
summary={'results':{k:v['status'] for k,v in results.items()},'attempts':len(events),
    'input_tokens':sum(e['usage']['input_tokens'] or 0 for e in events),'output_tokens':sum(e['usage']['output_tokens'] or 0 for e in events),
    'usage_priced_cost_usd':sum(e['usage']['cost_usd'] or 0 for e in events),'unpriced_attempts':sum(e['usage']['cost_usd'] is None for e in events)}
save(args.run/'answer-summary.json',summary); print(json.dumps(summary))
