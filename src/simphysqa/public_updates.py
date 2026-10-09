"""Lossless public-view changes for real clarification continuations."""
from copy import deepcopy
from .io import canonical


def difference(initial, resolved, path=''):
    if type(initial) is type(resolved) and canonical(initial)==canonical(resolved):return []
    if isinstance(initial,dict) and isinstance(resolved,dict):
        result=[]
        def esc(k):return k.replace('~','~0').replace('/','~1')
        for k in sorted(initial.keys()-resolved.keys()):result.append({'op':'remove','path':path+'/'+esc(k)})
        for k in sorted(resolved):
            p=path+'/'+esc(k)
            if k not in initial:result.append({'op':'add','path':p,'value':deepcopy(resolved[k])})
            else:result.extend(difference(initial[k],resolved[k],p))
        return result
    return [{'op':'replace','path':path,'value':deepcopy(resolved)}]


def apply(initial, changes):
    result=deepcopy(initial)
    for c in changes:
        if c['path']=='':result=deepcopy(c['value']);continue
        parts=[p.replace('~1','/').replace('~0','~') for p in c['path'][1:].split('/')]
        parent=result
        for p in parts[:-1]:parent=parent[p]
        if c['op']=='remove':del parent[parts[-1]]
        else:parent[parts[-1]]=deepcopy(c['value'])
    return result


def continuation_request(record, condition, actual_raw_response, parsed_response):
    from .clarification_evaluation import route_reply, initial_request
    route=route_reply(record,parsed_response)
    if route['status']!='recorded_reply_routed':return None,route
    initial=record['private']['initial_view'];resolved=route['resolved_view'];changes=difference(initial,resolved)
    if canonical(apply(initial,changes))!=canonical(resolved):raise ValueError('public update lost resolved task facts')
    first=initial_request(record,condition)
    first['stage']=2
    first['messages'].extend([{'role':'assistant','content':actual_raw_response},
        {'role':'user','content':'Recorded clarification reply: '+canonical(route['reply']).decode()+
          '\nResolve the original public task by applying these public JSON updates to the initial view. '
          'All unchanged physical observations, language, controls and declarations remain as previously supplied. '
          'Return the typed final answer using the resolved interaction.response_schema. No gold answer is supplied.\n'+
          canonical({'public_update_version':'public-task-update/1.0.0','changes':changes}).decode()}])
    return first,{**route,'public_update_roundtrip_verified':True,'public_update_version':'public-task-update/1.0.0'}
