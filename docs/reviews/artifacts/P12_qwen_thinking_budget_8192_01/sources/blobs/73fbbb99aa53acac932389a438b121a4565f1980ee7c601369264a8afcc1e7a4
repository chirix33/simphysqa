"""Explicit runtime controls, distinct from independent retraining ablations."""
from copy import deepcopy
from phi_jepa.artifacts import digest
from phi_jepa.inference.readout import read_targets,target_result
from phi_jepa.assessment.fixed import deterministic_answer


CONTROLS={
    'without_fixed_assessment':{'assessment':False,'fallback':True,'forecast':True},
    'without_fallback':{'assessment':True,'fallback':False,'forecast':True},
    'public_only_answer':{'assessment':False,'fallback':False,'forecast':False},
}


def runtime_control(name,problem,forecast,*,checkpoint_sha256,assess,answer,assessment_active=True,fallback_active=True):
    if name not in CONTROLS: raise ValueError('unknown_runtime_control')
    policy=CONTROLS[name]
    supplied=deepcopy(forecast) if policy['forecast'] else None
    outcomes=(read_targets(problem,supplied) if supplied is not None else
        [target_result(t,'unsupported',reason='no_forecast_in_public_only_control',source='control') for t in problem.input['answer_spec']])
    result={'control':name,'kind':'runtime_intervention_not_retraining','policy':policy.copy(),
        'checkpoint_sha256':checkpoint_sha256,'original_forecast_sha256':digest(forecast),
        'assessment':None,'answer':None,'failure':None,'fallback_used':False}
    result['no_op']=((name=='without_fixed_assessment' and not assessment_active) or
                     (name=='without_fallback' and not fallback_active))
    result['run_identity']=digest({k:v for k,v in result.items() if k not in ('answer','assessment')})
    if policy['assessment'] and assessment_active: result['assessment']=assess()
    try: result['answer']=answer(supplied,outcomes)
    except Exception as exc:
        result['failure']='answer_failure'
        from phi_jepa.providers.openai_answer import AnswerParseFailure
        from phi_jepa.providers.contracts import ProviderFailure
        result['failure_detail']=({'stage':'parser','reason':exc.reason} if isinstance(exc,AnswerParseFailure) else
            {'stage':'api','reason':exc.code.value} if isinstance(exc,ProviderFailure) else {'stage':'answer','reason':'callback_exception'})
        if policy['fallback'] and fallback_active and supplied is not None:
            result['answer']=deterministic_answer(problem,supplied); result['fallback_used']=True
    return result
