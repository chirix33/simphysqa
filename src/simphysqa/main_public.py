"""Main task projection, preserving physical inputs while separating derived language."""
from copy import deepcopy
from .io import canonical,parse,digest

# These fields locate/identify annotation production, rather than task facts.
LINEAGE={'bindings','description_bindings','event_description_bindings','matching_bindings',
    'cache_identity','controller_registry_sha256','matching_rules_sha256','point_registry_sha256',
    'source_public_input_sha256','source_state_sha256','source_event_sha256'}
DERIVED={'event_description'}

def strip_lineage(value):
    if isinstance(value,list):return [strip_lineage(x) for x in value]
    if isinstance(value,dict):return {k:strip_lineage(v) for k,v in value.items() if k not in LINEAGE}
    return deepcopy(value)

def structured_input(value):
    if isinstance(value,list):return [structured_input(x) for x in value]
    if isinstance(value,dict):return {k:structured_input(v) for k,v in value.items() if k not in LINEAGE|DERIVED}
    return deepcopy(value)

def project(view,structured=False):
    result={k:deepcopy(view[k]) for k in ('sample_id','question_type','schema_version','export_version')}
    result['input']=structured_input(view['input'])
    events=view.get('annotations',{}).get('event_context',{}).get('links',{}).get('events',[])
    if events:
        result['input']['declared_event_semantics']=[
            {k:strip_lineage(v) for k,v in event.items() if k not in ('bindings','context_note','controller')}
            | {'controller':{k:strip_lineage(v) for k,v in event.get('controller',{}).items() if k not in ('bindings','claims')}}
            for event in events]
    if not structured:
        # Each shared event description occurs once, while state links retain IDs
        # and actual temporal relationships. No observed state or fact is removed.
        annotation=view.get('annotations',{})
        result['language_annotations']={
            'trajectory':{k:deepcopy(v) for k,v in annotation.get('trajectory',{}).items() if k in ('text','status')},
            'timestamps':[{k:deepcopy(v) for k,v in t.items() if k in ('state_id','timestamp','text','status')} for t in annotation.get('timestamps',[])],
            'declared_event_descriptions':[{k:deepcopy(v) for k,v in e.items() if k in ('event_id','event_description','event_description_status')} for e in view['input'].get('known_events',[])]}
        # Event-context structured identities/controller phases are duplicate
        # derivations of retained declared controls; full originals stay in evidence.
    result['public_task_projection_version']='SPQ06-main-public/1.0.0'
    # The matched ablation differs only by this derived-language field. Original
    # context, question, comparison, units, frames, facts and query gaps are exact.
    physical={k:v for k,v in result['input'].items() if k!='declared_event_semantics'}
    if canonical(physical)!=canonical(structured_input(view['input'])):raise ValueError('physical projection mismatch')
    return result

def request_from(original,structured=False):
    request=deepcopy(original);prefix,text=request['messages'][0]['content'].split('\n',1)
    # Numeric requests append a response contract after the canonical view.
    decoder=__import__('json').JSONDecoder();view,end=decoder.raw_decode(text)
    suffix=text[end:]
    projected=project(view,structured)
    request['messages'][0]['content']=prefix+'\n'+canonical(projected).decode()+suffix
    request['public_projection_version']='SPQ06-main-public/1.0.0'
    request['input_condition']='structured_only' if structured else 'enriched'
    request['source_public_view_sha256']=digest(view)
    return request,{'source_sha256':digest(view),'projected_sha256':digest(projected),
        'physical_input_sha256':digest(projected['input']),'original_bytes':len(canonical(view)),
        'projected_bytes':len(canonical(projected)),'structured':structured,
        'unique_physical_facts':'all original physical input fields retained; only explicit generated event language and annotation lineage removed from input',
        'language':'exact original trajectory/timestamp/event text; one event description per event identity'}

def continuation(record,condition,actual_raw,response,structured=False):
    from .clarification_evaluation import route_reply
    from .public_updates import difference,apply
    from .spq06 import public_request
    route=route_reply(record,response)
    if route['status']!='recorded_reply_routed':return None,route
    initial=project(record['private']['initial_view'],structured)
    resolved=project(route['resolved_view'],structured)
    changes=difference(initial,resolved)
    if canonical(apply(initial,changes))!=canonical(resolved):raise ValueError('main public continuation differs')
    request,_=request_from(public_request(record,condition),structured)
    request['stage']=2
    request['messages'].extend([{'role':'assistant','content':actual_raw},{'role':'user','content':
        'Recorded clarification reply: '+canonical(route['reply']).decode()+'\nApply these exact updates to the original public task; unchanged facts remain supplied. Return the typed resolved answer.\n'+canonical({'public_task_updates':changes}).decode()}])
    return request,route
