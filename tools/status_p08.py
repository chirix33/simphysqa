"""Compact read-only pilot progress, excluding payloads and credentials."""
from p08_common import *
state=budget().read()
value={'active':state['active']['name'] if state['active'] else None,'seconds':state['seconds'],'stopped':state['stopped'],
    'provider_attempts':len(state['provider']),'provider_usd_charged':sum(r['charged_usd'] for r in state['provider'])}
value['custom']={}
for method in ('coconut_inspired_t5_gru','codi_inspired_t5_distillation'):
    for phase in ('diagnostic','broad'):
        folder=RUN/'custom'/method/phase
        if (folder/'history.json').exists():
            rows=load(folder/'history.json'); value['custom'][method+'/'+phase]={'updates':len(rows),'last_preupdate_loss':rows[-1]['loss'] if rows else None,
                'fit_complete':(folder/'fit.json').exists(),'generated_examples':len(list((folder/'generations').glob('*.json')))}
print(json.dumps(value),flush=True)
