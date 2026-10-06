"""No-call SPQ05 payload and source-family eligibility dry run."""
from collections import Counter
from pathlib import Path
from html import escape
import argparse
from simphysqa.io import read, canonical, digest
from simphysqa.formal_live import pair_for,settings
from simphysqa.formal_sampling import source_record,file_hash,save_bytes
from simphysqa.annotation import payload,project,reservation
from simphysqa.counterfactual import public_input
from simphysqa.spq01a import retained

p=argparse.ArgumentParser();p.add_argument('--run',type=Path,required=True);p.add_argument('--output',type=Path,required=True)
a=p.parse_args();plan=read(a.run/'execution-plan.json');results=[];links=[]
for c in plan['candidates']:
    wrapper=source_record(c['source']);body=payload(wrapper,settings());view=project(wrapper)
    assert set(view)=={'domain','focal_entity','focal_quantity','observation_cutoff','observed','facts'}
    assert set(view['facts'])=={'/controller','/known_events','/coordinate_convention'}|{x[k] for x in view['observed'] for k in ('time_binding','value_binding')}
    assert all(x['timestamp']<=view['observation_cutoff'] for x in view['observed'])
    assert body['tools']==[] and body['store'] is False and body['model']=='gpt-5.6-sol'
    reason=None
    if c['question_type'] in ('counterfactual','explanation','clarification'):
        try:
            pair=pair_for(c)
            target=next(t for t in sorted(wrapper['public']['input']['answer_spec'],key=lambda t:t['target_id']) if t['answer_type'] in ('number','integer','vector','boolean'))
            source=next(s for s in pair['source_records'] if s['sample_id']==wrapper['sample_id'])
            public_input(source,pair['pair_id'],target)
        except Exception as exc:reason=type(exc).__name__+': '+str(exc)
    results.append({'candidate_id':c['candidate_id'],'cell':c['cell'],'rank':c['rank'],'source_precheck_reason':reason,'request_sha256':digest(body),'reservation':reservation(body,settings())})
    save_bytes(a.output/'payloads'/(c['candidate_id']+'.json'),canonical(body))
    links.append('<li>'+escape(c['cell']+' rank'+str(c['rank']))+' <a href="payloads/'+c['candidate_id']+'.json">'+c['candidate_id']+'</a></li>')
retained(a.output/'results.json',results)
report={'version':'SPQ05-payload-dryrun/1.0.0','requests_prepared':len(results),'private_future_or_gold_fields_in_payload':0,
        'destination':'https://api.openai.com/v1/responses','live_calls':0,'simulations':0,
        'source_precheck_eligible':sum(x['source_precheck_reason'] is None for x in results),
        'source_precheck_reasons':dict(Counter(x['source_precheck_reason'] for x in results if x['source_precheck_reason'])),
        'execution_plan_sha256':file_hash(a.run/'execution-plan.json')}
retained(a.output/'report.json',report)
save_bytes(a.output/'index.html',('<!doctype html><meta charset="utf-8"><h1>SPQ05 concrete annotation payloads</h1><p>Destination: https://api.openai.com/v1/responses. Observed-prefix focal measurements/timestamps/units/frames and declared controls/events only. No private future states, gold answers, explanation traces, or verification. Fixed established prompt/schema. Zero executed calls. Budgets in execution-plan.json remain unchanged.</p><ul>'+''.join(links)+'</ul>').encode())
retained(a.output/'manifest.json',{'version':report['version'],'files':{f.relative_to(a.output).as_posix():file_hash(f) for f in sorted(a.output.rglob('*')) if f.is_file() and f.name!='manifest.json'}})
print(canonical(report).decode())
