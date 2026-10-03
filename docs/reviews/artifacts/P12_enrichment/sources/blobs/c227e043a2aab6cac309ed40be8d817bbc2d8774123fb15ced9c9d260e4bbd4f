"""Evaluator-only four-domain physical/answer metrics; never imported by predict."""
from collections import Counter, defaultdict
import math
import random

from phi_jepa.inference.readout import BINDING, finite


def physical_error(value, truth, quantity):
    if type(truth) is bool:
        if type(value) is not bool: raise ValueError('boolean_type')
        return float(value != truth), 'boolean_mismatch'
    if isinstance(truth, list):
        if not isinstance(value,list) or len(value)!=len(truth) or not value or not all(map(finite,value+truth)):
            raise ValueError('vector_shape_or_value')
        if quantity=='orientation':
            if len(value)!=4: raise ValueError('quaternion_shape')
            a,b=math.hypot(*value),math.hypot(*truth)
            if not a or not b: raise ValueError('zero_quaternion')
            return 2*math.acos(min(1.,abs(sum((x/a)*(y/b) for x,y in zip(value,truth))))), 'rad_rotation'
        return math.dist(value,truth), 'native_euclidean'
    if not finite(value) or not finite(truth): raise ValueError('number_type')
    return abs(value-truth), 'native_absolute'


def evaluate_targets(problem, reference, rows, *, method, failure=None):
    """Every expected target contributes, including unsupported/failed answers."""
    specs=problem.input['answer_spec']
    truths={r['target_id']:r for r in reference['structured_label']}
    if len(truths)!=len(reference['structured_label']) or set(truths)!={s['target_id'] for s in specs}:
        raise ValueError('truth_target_identity')
    counts=Counter(r.get('target_id') for r in rows if isinstance(r,dict))
    found={r.get('target_id'):r for r in rows if isinstance(r,dict)}
    extra=set(found)-{s['target_id'] for s in specs}
    records=[]
    for spec in specs:
        ident=spec['target_id']; row=found.get(ident); truth=truths[ident]
        out={'target_id':ident,'answer_type':spec['answer_type'],'unit':spec['unit'],
             'status':'failure','reason':failure or 'missing_target','error':None,'success':False}
        try:
            if failure: raise ValueError(failure)
            if extra: raise ValueError('unknown_target')
            if row is None: raise ValueError('missing_target')
            if counts[ident]!=1: raise ValueError('duplicate_target')
            if any(row.get(k)!=spec[k] or type(row.get(k)) is bool for k in BINDING): raise ValueError('target_binding')
            if (truth['unit'],truth['frame'])!=(spec['unit'],spec['frame']): raise ValueError('truth_binding')
            if row.get('status')=='unsupported':
                if row.get('value') is not None or not row.get('reason'): raise ValueError('unsupported_format')
                out.update(status='unsupported',reason=row['reason'])
            elif row.get('status')=='supported':
                error,kind=physical_error(row['value'],truth['value'],spec['quantity'])
                if not math.isfinite(error): raise ValueError('nonfinite_error')
                magnitude=(math.hypot(*truth['value']) if isinstance(truth['value'],list) else abs(truth['value']))
                tolerance=spec['absolute_tolerance']+spec['relative_tolerance']*magnitude
                out.update(status='valid',reason=None,error=error,error_kind=kind,tolerance=tolerance,success=error<=tolerance)
            else: raise ValueError('status')
        except (ValueError,KeyError,TypeError,OverflowError) as exc:
            out['reason']=str(exc)
        records.append(out)
    boolean=[r for r in records if r['answer_type']=='boolean']
    valid_bool=[r for r in boolean if r['status']=='valid']
    return {'sample_id':problem.sample_id,'method':method,'targets':records,'eligible_questions':1,
        'eligible_targets':len(records),'valid_targets':sum(r['status']=='valid' for r in records),
        'complete_success':bool(records) and all(r['success'] for r in records),
        'boolean_eligible':len(boolean),'boolean_supported':len(valid_bool),
        'boolean_correct':sum(r['success'] for r in valid_bool),
        'boolean_coverage':len(valid_bool)/len(boolean) if boolean else None,
        'boolean_accuracy_supported':sum(r['success'] for r in valid_bool)/len(valid_bool) if valid_bool else None}


def trajectory_errors(predicted_states, reference_states, *, mode):
    """Named physical coordinates only, matched absolute times; no latent MSE."""
    if mode not in ('autonomous','recorded_input_one_step_diagnostic'):
        raise ValueError('explicit trajectory mode required')
    times=Counter(s['timestamp'] for s in predicted_states)
    by_time={s['timestamp']:s for s in predicted_states}
    errors=[]
    for ref in reference_states:
        t=ref['timestamp']; pred=by_time.get(t)
        for truth in ref['measurements']:
            if type(truth['value']) is bool: continue
            row={'time':t,'entity_id':truth['entity_id'],'quantity':truth['name'],'unit':truth['unit'],
                 'status':'failure','error':None}
            try:
                if pred is None or times[t]!=1: raise ValueError('missing_or_duplicate_time')
                matches=[m for m in pred['measurements'] if (m['entity_id'],m['name'])==(truth['entity_id'],truth['name'])]
                if len(matches)!=1: raise ValueError('missing_or_duplicate_channel')
                match=matches[0]
                if (match['unit'],match['frame'])!=(truth['unit'],truth['frame']): raise ValueError('unit_or_frame')
                error,kind=physical_error(match['value'],truth['value'],truth['name'])
                if not math.isfinite(error): raise ValueError('nonfinite_error')
                row.update(status='valid',error=error,error_kind=kind)
            except (ValueError,KeyError,TypeError,OverflowError) as exc: row['reason']=str(exc)
            errors.append(row)
    grouped=defaultdict(list)
    for row in errors: grouped[(row['entity_id'],row['quantity'],row['unit'])].append(row)
    metrics=[]
    for (entity,name,unit),rows in sorted(grouped.items()):
        valid=[r['error'] for r in rows if r['status']=='valid']
        metrics.append({'entity_id':entity,'quantity':name,'unit':unit,'eligible':len(rows),'valid':len(valid),
            'mae_valid_only':sum(valid)/len(valid) if valid else None,
            'rmse_valid_only':math.hypot(*valid)/math.sqrt(len(valid)) if valid else None})
    return {'mode':mode,'expected_timepoints':len(reference_states),'extra_predicted_times':sorted(set(by_time)-{s['timestamp'] for s in reference_states}),
            'metrics':metrics,'per_time_channel':errors}


def grouped_summary(records, *, resamples=1000, seed=11):
    """Cluster bootstrap of complete answers; resample scenarios, not questions."""
    def summary(rows):
        n=len(rows); groups=defaultdict(list)
        for r in rows: groups[r['scenario_id']].append(r)
        complete=sum(r['complete_success'] for r in rows)
        be=sum(r['boolean_eligible'] for r in rows); bs=sum(r['boolean_supported'] for r in rows); bc=sum(r['boolean_correct'] for r in rows)
        result={'questions':n,'scenarios':len(groups),'complete_successes':complete,'complete_success_rate':complete/n if n else None,
            'boolean_coverage':bs/be if be else None,'boolean_accuracy_supported':bc/bs if bs else None,
            'boolean_eligible':be,'boolean_supported':bs,'boolean_correct':bc,
            'scenario_macro_complete_success':sum(sum(x['complete_success'] for x in g)/len(g) for g in groups.values())/len(groups) if groups else None,
            'scenario_bootstrap_95_interval':None,'bootstrap_seed':seed,'bootstrap_resamples':resamples}
        if len(groups)>=2:
            rng=random.Random(seed); clusters=list(groups.values()); values=[]
            for _ in range(resamples):
                sample=[r for cluster in rng.choices(clusters,k=len(clusters)) for r in cluster]
                values.append(sum(r['complete_success'] for r in sample)/len(sample))
            values.sort(); result['scenario_bootstrap_95_interval']=[values[int(.025*(resamples-1))],values[math.ceil(.975*(resamples-1))]]
        return result
    by_domain={d:summary([r for r in records if r['domain']==d]) for d in sorted({r['domain'] for r in records})}
    return {'pooled':summary(records),'by_domain':by_domain,
        'domain_macro_complete_success':sum(r['complete_success_rate'] for r in by_domain.values())/len(by_domain) if by_domain else None,
        'by_domain_distribution':{d+':'+shift:summary([r for r in records if r['domain']==d and r['distribution']==shift]) for d,shift in sorted({(r['domain'],r['distribution']) for r in records})},
        'failure_categories':dict(Counter(t['reason'] for r in records for t in r['targets'] if t['status']!='valid'))}


def augmented_drift(layout, initial, predictions):
    """Diagnostics only: fixed-coordinate drift and p drift never modify output."""
    if len(initial)!=2*layout.d or not all(map(finite,initial)): raise ValueError('initial_augmented_shape')
    groups={'fixed_conditioning':[],'contextual':list(range(layout.d,2*layout.d)),
            'state_time_and_index':[]}
    for i,(path,_) in enumerate(layout.entries):
        if path[0]==('key','fixed_conditioning'): groups['fixed_conditioning'].append(i)
        elif path in ((('key','state'),('key','timestamp')),(('key','state'),('key','step_index'))): groups['state_time_and_index'].append(i)
    rows=[]
    for p in predictions:
        if p.layout_sha256!=layout.sha256 or len(p.values)!=2*layout.d or not all(map(finite,p.values)): raise ValueError('prediction_augmented_shape')
        rows.append({'time':p.physical_time,'blocks':{name:{'width':len(indices),
            'norm':math.hypot(*(p.values[i] for i in indices)),
            'delta_from_initial_l2':math.hypot(*(p.values[i]-initial[i] for i in indices))} for name,indices in groups.items()}})
    return {'meaning':'raw drift diagnostics; state time/index naturally advance, fixed coordinates need not remain constant under the learned ODE; no correction', 'rows':rows}
