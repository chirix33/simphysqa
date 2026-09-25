"""Fixed combination, validation-only calibration, transparent bounded fallback."""
from copy import deepcopy
import math
from phi_jepa.artifacts import digest


def combine(familiarity, contract, judge, *, profile, identity):
    if not 0<=profile['alpha_contract']<=1 or not math.isfinite(profile['lambda_json']) or profile['lambda_json']<0 or profile.get('high_score_numerical_replacement') is not False:
        raise ValueError('invalid_or_unapproved_score_policy')
    components={'familiarity':familiarity,'contract':contract,'semantic_v1':judge}
    available=all(c.get('status')=='available' and type(c.get('score')) in (int,float) and math.isfinite(c['score']) for c in components.values())
    result={'profile':'development_r1_v1_full_2d','identity':identity,'profile_sha256':digest(profile),
        'components':components,'status':'complete' if available else 'partial','score':None,'threshold_decision':None,
        'meaning':'development familiarity assessment; not physical correctness or calibrated uncertainty'}
    if available:
        if not 0<=familiarity['score']<=2 or contract['score']<0 or not 0<=judge['score']<=1: raise ValueError('invalid_component_score')
        result['score']=familiarity['score']+profile['lambda_json']*(profile['alpha_contract']*contract['score']+(1-profile['alpha_contract'])*judge['score'])
    return result


def calibrate(records, *, assessment_identity, profile_sha256, policy, selection_scenarios=()):
    """Freeze higher empirical quantile of per-scenario maxima on ID calibration.

    This is a detector policy, not conformal validity. One aggregate per scenario
    prevents duplicate question contexts from being independent calibration units.
    """
    if (policy['split'],policy['distribution'],policy['role'],policy['algorithm'],policy['trigger'],policy['unit']) != ('validation','id','calibration','higher','strict_greater','scenario_maximum'):
        raise ValueError('unsupported_calibration_policy')
    if type(policy['quantile']) not in (float,int) or not 0<policy['quantile']<1 or type(policy['minimum_scenarios']) is not int or policy['minimum_scenarios']<2:
        raise ValueError('invalid_calibration_policy')
    grouped={}
    ids=set()
    for row in records:
        if row['split']!='validation' or row['distribution']!='id' or row['role']!='calibration': raise ValueError('validation_calibration_only')
        if row['scenario_id'] in selection_scenarios: raise ValueError('selection_calibration_overlap')
        if row['sample_id'] in ids: raise ValueError('duplicate_calibration_sample')
        ids.add(row['sample_id'])
        assessment=row['assessment']
        if assessment['identity']!=assessment_identity or assessment['profile_sha256']!=profile_sha256: raise ValueError('calibration_identity')
        if assessment['status']!='complete' or not math.isfinite(assessment['score']): raise ValueError('complete_calibration_required')
        grouped[row['scenario_id']]=max(grouped.get(row['scenario_id'],-math.inf),assessment['score'])
    result={'status':'uncalibrated','threshold':None,'identity':assessment_identity,'profile_sha256':profile_sha256,
        'policy':deepcopy(policy),'scenario_ids':sorted(grouped),'sample_ids':sorted(ids),'source_sha256':digest(records)}
    values=sorted(grouped.values())
    if len(values)<policy['minimum_scenarios']: result['reason']='insufficient_calibration_scenarios'
    elif values[0]==values[-1]: result['reason']='degenerate_calibration_scores'
    else:
        threshold=values[math.ceil(policy['quantile']*(len(values)-1))]
        result.update(status='calibrated',threshold=threshold,reason=None,
            observed_calibration_scenario_alarm_rate=sum(v>threshold for v in values)/len(values))
    result['sha256']=digest(result)
    return result


def apply_threshold(assessment, calibration):
    result=deepcopy(assessment)
    supplied={k:v for k,v in calibration.items() if k!='sha256'}
    if calibration.get('sha256')!=digest(supplied): raise ValueError('calibration_integrity')
    if calibration['identity']!=assessment['identity'] or calibration['profile_sha256']!=assessment['profile_sha256']: raise ValueError('stale_calibration')
    result['calibration_sha256']=calibration['sha256']
    if assessment['status']=='complete' and calibration['status']=='calibrated':
        result['threshold_decision']=assessment['score']>calibration['threshold']
    return result


def bounded_fallback(original, *, failure=None, text_answer=None, numeric_formatter=None):
    """No numerical replacement without an independently trained fallback.

    This output-only reliability path calls at most one supplied public-text
    callback for a technical forecast failure. It never responds to high scores.
    Callback owns provider retry/usage accounting; those records are retained.
    """
    result={'original_prediction':deepcopy(original),'returned_prediction':deepcopy(original),
        'trigger':failure,'replacement':None,'fallback_calls':0,'fallback_status':'not_needed',
        'high_score_numerical_replacement':False}
    if failure=='answer_failure' and original is not None and numeric_formatter is not None:
        result.update(fallback_status='deterministic_numeric_format',replacement=numeric_formatter(original))
    elif failure in ('extraction_failure','forecast_failure'):
        if text_answer is None: result['fallback_status']='unavailable_no_independent_fallback'
        else:
            result['fallback_calls']=1
            try:
                result['replacement']=text_answer(); result['fallback_status']='public_text_answer_only'
            except Exception:
                result['fallback_status']='fallback_failed'
    return result


def deterministic_answer(problem, forecast):
    from phi_jepa.inference.readout import read_targets,BINDING
    rows=read_targets(problem,forecast)
    text=[]
    for row in rows:
        if row['status']=='supported': text.append(f"{row['entity_id']} {row['quantity']} at {row['end_time']} s: {row['value']} {row['unit']} ({row['frame']}).")
        else: text.append(f"{row['entity_id']} {row['quantity']}: unsupported ({row['reason']}).")
    return {'source':'deterministic_numeric_and_rule_formatter','plain_text_answer':' '.join(text),
        'targets':[{k:r[k] for k in (*BINDING,'status','value','reason')} for r in rows],
        'llm_narrative_available':False,'forecast_sha256':digest(forecast)}
