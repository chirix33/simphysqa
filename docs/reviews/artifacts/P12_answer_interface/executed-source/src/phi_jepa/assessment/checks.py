"""Disclosed independent physical checks and evidence-bound contract operators.

No authored force law is imported into the learned predictor. Driven/dissipative
systems receive no conservation-of-energy or momentum check.
"""
import math
from phi_jepa.artifacts import digest
from phi_jepa.inference.readout import channel, Unsupported, CONVENTION, finite


def physical_checks(problem, forecast, config):
    inp=problem.input; checks=[]
    for state in forecast['states']:
        t=state['timestamp']
        def check(name, unit, compute, tolerance):
            row={'name':name,'time':t,'unit':unit,'tolerance':tolerance,'status':'unsupported','violated':None,'excess':None}
            try:
                if inp['coordinate_convention']!=CONVENTION: raise Unsupported('coordinate_convention')
                error=compute()
                if not finite(error): raise Unsupported('nonfinite_check')
                row.update(status='evaluated',violated=error>tolerance,excess=max(0.,error-tolerance),error=error)
            except (Unsupported,ValueError,KeyError) as exc: row['reason']=str(exc)
            checks.append(row)
        for entity in sorted({m['entity_id'] for m in inp['states'][-1]['measurements'] if m['name']=='orientation'}):
            check(entity+':unit_quaternion','1',lambda entity=entity:abs(math.hypot(*channel(state,entity,'orientation','1','world',4))-1),config['quaternion_norm_tolerance'])
        if inp['domain']=='tethered_load':
            def length_error():
                params=inp['controller']['parameters']
                values=[m for m in params if (m['entity_id'],m['name'],m['unit'],m['frame'])==('load','length','m','world')]
                if len(values)!=1 or not finite(values[0]['value']) or values[0]['value']<=0: raise Unsupported('public_cable_length')
                return abs(math.dist(channel(state,'load','position','m','world',3),channel(state,'support','position','m','world',3))-values[0]['value'])
            check('taut_tether_length','m',length_error,config['tether_length_tolerance_m'])
        if inp['domain']=='driving':
            for name,vector,unit in [('forward_position','position','m'),('forward_velocity','velocity','m/s')]:
                check('car:'+name+'_consistency',unit,
                    lambda name=name,vector=vector,unit=unit:abs(channel(state,'car',name,unit,'world')-channel(state,'car',vector,unit,'world',3)[0]),
                    config['redundant_channel_tolerance'])
    evaluated=[c for c in checks if c['status']=='evaluated']
    return {'checks':checks,'eligible':len(checks),'evaluated':len(evaluated),
        'unsupported':len(checks)-len(evaluated),'violations':sum(c['violated'] for c in evaluated),
        'pcvr':sum(c['violated'] for c in evaluated)/len(evaluated) if evaluated else None,
        'coverage':len(evaluated)/len(checks) if checks else None,
        'meaning':'independent limited physical consistency checks; separate from truth error, provenance and LLM agreement',
        'policy_sha256':digest(config)}


def contract_score(problem, forecast, contracts):
    """Only structured public constraints, never convert an observed fact to bound.

    The frozen release currently supplies no typed constraint operators. Explicit
    caller proposals must exactly match public controller constraints and carry
    an evidence substring. Empty support remains unavailable, never severity 0.
    """
    inp=problem.input
    declared=inp['controller'].get('constraints',[])
    if contracts!=declared: raise ValueError('constraints_must_be_immutable_public_metadata')
    rows=[]
    for c in contracts:
        row={'constraint_id':c.get('constraint_id'),'status':'unsupported','severity':None}
        try:
            if not c['evidence'] or c['evidence'] not in inp['global_context']: raise Unsupported('missing_public_evidence')
            if c['operator'] not in ('eq','le','ge','between'): raise Unsupported('operator')
            scale=c['scale']; tolerance=c['tolerance']
            if not finite(scale) or scale<=0 or not finite(tolerance) or tolerance<0: raise Unsupported('scale_or_tolerance')
            bounds=c['bounds']
            if not isinstance(bounds,list) or len(bounds)!=(2 if c['operator']=='between' else 1) or not all(map(finite,bounds)): raise Unsupported('bounds')
            if len(bounds)==2 and bounds[0]>bounds[1]: raise Unsupported('bounds_order')
            values=[channel(s,c['entity_id'],c['quantity'],c['unit'],c['frame']) for s in forecast['states']]
            if not values: raise Unsupported('empty_forecast')
            def excess(v):
                if c['operator']=='le': return max(0.,v-bounds[0]-tolerance)/scale
                if c['operator']=='ge': return max(0.,bounds[0]-v-tolerance)/scale
                if c['operator']=='eq': return max(0.,abs(v-bounds[0])-tolerance)/scale
                return max(0.,bounds[0]-v-tolerance,v-bounds[1]-tolerance)/scale
            row.update(status='evaluated',severity=sum(map(excess,values))/len(values))
        except (Unsupported,KeyError,TypeError) as exc: row['reason']=str(exc)
        rows.append(row)
    valid=[r['severity'] for r in rows if r['status']=='evaluated']
    complete=bool(rows) and len(valid)==len(rows)
    return {'status':'available' if complete else 'unavailable','reason':None if complete else 'empty_or_incomplete_contract_coverage',
        'score':sum(valid)/len(valid) if complete else None,'checks':rows,'eligible':len(rows),'evaluated':len(valid)}
