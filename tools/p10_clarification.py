"""Explicitly enabled human condition, separate from unattended benchmarking."""
from p10_common import *
from phi_jepa.integration.contracts import PublicProblem
from phi_jepa.inference.clarification import AttemptStore,ClarificationService,ReplyReview
from phi_jepa.providers.clarification import FrozenClarificationAnswer
from phi_jepa.providers.openai_enrichment import OpenAIEnrichment
from phi_jepa.providers.credentials import load_openai_key
from phi_jepa.providers.cache import FrozenOutputCache


def clarify(run,job):
    if not job or any(x not in 'abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789_-' for x in job):
        raise ValueError('clarification_request_id_required')
    request=load(run.root/'clarification_requests'/f'{job}.json')
    if request.get('enable_human_condition') is not True or not run.c['provider_enabled']:
        raise ValueError('explicit_human_condition_enable_required')
    config={**load(ROOT/'configs/baselines_p05b.json')['answer_profile'],'max_attempts_per_request':1}
    asset=load(ROOT/'docs/assets/clarification_v1.json')
    http=OpenAIEnrichment(load_openai_key(ROOT/'.env'),config,{},FrozenOutputCache(run.root/'clarification_transport'))
    provider=FrozenClarificationAnswer(config=config,asset=asset,transport=run.b.transport(http._http),
        authorize_and_reserve=lambda stage,payload:run.b.check())
    store=AttemptStore(run.root/'clarification'); service=ClarificationService(store,provider)
    attempt=request['attempt_id']
    if request['action']=='start':
        row=next(r for r in run.rows() if r['sample_id']==request['sample_id'])
        method=request.get('method',run.methods()[0])
        if method not in run.methods(): raise ValueError('unknown_selected_method')
        prediction=load(run.root/'numerical'/method/'forecasts'/f"{row['sample_id']}.json")
        if prediction['status']!='success': raise ValueError('valid_existing_forecast_required')
        result=service.start(attempt,PublicProblem.parse(row['public']),prediction['named'],prediction['readout'],mode='actual_interactive')
    elif request['action']=='review_and_refine':
        result=service.review_and_refine(attempt,ReplyReview(**request['human_review']))
    else: raise ValueError('unknown_clarification_action')
    # No reference interface here; separate evaluator must retain original task.
    save(run.root/'clarification_results'/f'{job}.json',result)
    print(json.dumps({'attempt':attempt,'status':result['status'],'condition':'actual_interactive'}))
