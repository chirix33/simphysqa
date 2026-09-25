"""Three bounded validation answer conditions; no reference reader in this process."""
import argparse
from copy import deepcopy
import json
from pathlib import Path
import sys
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'src'))
from phi_jepa.artifacts import canonical, digest, code_provenance
from phi_jepa.integration.contracts import PublicProblem, PhysicalRollout, FullAugmentedPrediction
from phi_jepa.integration.layout import StateLayout
from phi_jepa.inference.readout import named_forecast, read_targets, target_result, InvalidForecast
from phi_jepa.providers.openai_answer import OpenAIAnswer, AnswerParseFailure
from phi_jepa.providers.credentials import load_openai_key
from phi_jepa.providers.cache import FrozenOutputCache
from phi_jepa.providers.contracts import ProviderFailure


def save(path, obj):
    temporary = path.with_suffix(path.suffix+'.tmp')
    temporary.write_bytes(canonical(obj)); temporary.replace(path)


def main():
    parser=argparse.ArgumentParser()
    parser.add_argument('--profile',type=Path,required=True)
    parser.add_argument('--run',type=Path,required=True)
    parser.add_argument('--output',type=Path,required=True)
    parser.add_argument('--resume',action='store_true')
    args=parser.parse_args()
    root=Path(__file__).resolve().parents[1]
    config=json.loads((root/'configs/answer_p04a.json').read_text())
    asset=json.loads((root/'docs/assets/p04a_answer_v1.json').read_text())
    if not config['profile']['live_authorized'] or config['profile']['questions'] != 1 or config['max_total_attempts']>6:
        raise ValueError('profile budget')
    args.output.mkdir(parents=True,exist_ok=args.resume)
    selected=json.loads((args.profile/'selected-public.json').read_text())
    row=next(r for r in selected if r['domain']=='tethered_load' and r['split']=='validation')
    problem=PublicProblem.parse(row['public'])
    original=json.loads((args.run/'autonomous-trajectory.json').read_text())
    full=PhysicalRollout(original['sample_id'],tuple(FullAugmentedPrediction(**p) for p in original['predictions']),original['mode'])
    manifest=json.loads((root/'docs/reviews/artifacts/P02a/tethered_load.state_plus_fixed_conditioning.json').read_text())
    layout=StateLayout.from_manifest(manifest,digest(manifest))
    forecast=named_forecast(problem,layout,full)
    predicted=read_targets(problem,forecast)
    reversed_forecast=deepcopy(forecast)
    for row,other in zip(reversed_forecast['states'],reversed(forecast['states'])):
        row['measurements']=deepcopy(other['measurements'])
    reversed_readout=read_targets(problem,reversed_forecast)
    absent=[target_result(t,'unsupported',reason='no_forecast_in_public_only_control',source='control') for t in problem.input['answer_spec']]
    conditions={'public_only':(None,absent),'predicted':(forecast,predicted),'reversed_forecast':(reversed_forecast,reversed_readout)}
    identity={'config':config,'asset_sha256':digest(asset),'public_sha256':digest(problem.input),
        'raw_rollout_sha256':digest(original),'layout_sha256':layout.sha256,'sample_id':problem.sample_id}
    identity_path=args.output/'identity.json'
    if args.resume and json.loads(identity_path.read_text()) != identity: raise ValueError('resume identity mismatch')
    save(identity_path,identity)
    save(args.output/'source.json',code_provenance())
    save(args.output/'public.json',{'sample_id':problem.sample_id,'schema_version':problem.schema_version,'input':problem.input})
    save(args.output/'named-forecast.json',forecast)
    save(args.output/'numeric-readout.json',predicted)
    ledger_path=args.output/'ledger.json'
    ledger=json.loads(ledger_path.read_text()) if ledger_path.exists() else None
    provider=OpenAIAnswer(load_openai_key(root/'.env'),config,asset,FrozenOutputCache(args.output/'answer-cache'),
        ledger=ledger,event_sink=lambda value:save(ledger_path,value))
    results={}
    for condition in config['profile']['conditions']:
        supplied,outcomes=conditions[condition]
        path=args.output/(condition+'.json')
        if args.resume and path.exists():
            results[condition]=json.loads(path.read_text()); continue
        try:
            answer=provider.answer(problem,supplied,outcomes,condition=condition)
            result={'status':'success','answer':answer}
        except AnswerParseFailure as exc: result={'status':'parser_failure','reason':exc.reason}
        except ProviderFailure as exc: result={'status':'api_failure','reason':exc.code.value}
        results[condition]=result
        save(path,result)
        print(json.dumps({'condition':condition,'status':result['status'],'reason':result.get('reason')}),flush=True)
    save(args.output/'results.json',results)
    events=provider.runner.events
    summary={'sample_id':problem.sample_id,'split':'validation','questions':1,'conditions':list(results),
        'statuses':{k:v['status'] for k,v in results.items()},'attempts':len(events),
        'input_tokens':sum(e['usage']['input_tokens'] or 0 for e in events),
        'output_tokens':sum(e['usage']['output_tokens'] or 0 for e in events),
        'usage_priced_cost_usd':sum(e['usage']['cost_usd'] or 0 for e in events),
        'unpriced_attempts':sum(e['usage']['cost_usd'] is None for e in events),
        'api_wall_seconds':sum(e['wall_seconds'] for e in events),
        'encoder_calls':0,'ode_solves':0,'training_updates':0,
        'claim':'bounded answer-path diagnostic using an existing tiny correctness checkpoint; not a benchmark'}
    save(args.output/'summary.json',summary)
    print(json.dumps(summary))


if __name__=='__main__': main()
