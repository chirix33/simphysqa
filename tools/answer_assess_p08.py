"""Approved answer/judge calls; no evaluator truths enter provider payloads."""
import argparse
from copy import deepcopy
from hashlib import sha256
import torch
from p08_common import *
from phi_jepa.integration.contracts import PublicProblem
from phi_jepa.inference.readout import read_targets,target_result
from phi_jepa.providers.openai_answer import OpenAIAnswer
from phi_jepa.providers.openai_judge import OpenAIJudge
from phi_jepa.providers.credentials import load_openai_key
from phi_jepa.providers.cache import FrozenOutputCache
from phi_jepa.assessment.reference import ReferenceBank
from phi_jepa.assessment.checks import physical_checks,contract_score
from phi_jepa.assessment.fixed import combine,calibrate,apply_threshold


def provider(cls,config,asset,name):
    b=budget(); ledger=RUN/'provider-ledgers'/f'{name}.json'
    obj=cls(load_openai_key(ROOT/'.env'),config,asset,FrozenOutputCache(RUN/'provider-cache'/name),event_sink=lambda value:save(ledger,value),ledger=load(ledger) if ledger.exists() else None)
    obj.transport=b.transport(obj._http); return obj


def answers():
    b=budget(); provenance('answers'); config=load(ROOT/'configs/baselines_p05b.json')['answer_profile']; asset=load(ROOT/'docs/assets/p04a_answer_v1.json')
    for row in public_records():
        if row['split']!='validation': continue
        p=PublicProblem.parse(row['public']); sid=p.sample_id
        for method in [*CONFIG['numerical_methods'],'public_only','reversed_forecast']:
            out=RUN/'answers'/method/f'{sid}.json'
            if out.exists(): continue
            b.check(); saved=load(RUN/'numerical'/('phi_jepa' if method in ('public_only','reversed_forecast') else method)/'forecasts'/f'{sid}.json')
            if method=='public_only':
                forecast=None; outcomes=[target_result(t,'unsupported',reason='no_forecast_in_public_only_control',source='control') for t in p.input['answer_spec']]
            elif saved['status']!='success':
                save(out,{'status':'forecast_failure','reason':saved['reason'],'answer':None}); continue
            else:
                forecast=deepcopy(saved['named'])
                if method=='reversed_forecast':
                    for a,z in zip(forecast['states'],reversed(saved['named']['states'])): a['measurements']=deepcopy(z['measurements'])
                outcomes=read_targets(p,forecast)
            obj=provider(OpenAIAnswer,config,asset,'answer-'+method+'-'+sid)
            try: answer=obj.answer(p,forecast,outcomes,condition=method); result={'status':'success','answer':answer}
            except Exception as exc: result={'status':'api_or_parse_failure','reason':str(exc),'type':type(exc).__name__,'answer':None}
            save(out,{**result,'sample_id':sid,'method':method,'outcomes':outcomes,'forecast_sha256':digest(forecast) if forecast else None})
            print(json.dumps({'answer':sid,'method':method,'status':result['status'],'attempts':len(b.read()['provider'])}),flush=True)
            b.check()


def assessment():
    b=budget(); provenance('assessment'); l=layout(); config=load(ROOT/'configs/assessment_p04b.json'); fit=load(RUN/'numerical/phi_jepa/fit.json')
    folder=RUN/'numerical/phi_jepa/deployment'; pointer=load(folder/'latest.json'); bundle=torch.load(folder/pointer['file'],weights_only=True,map_location='cpu')
    projection={k:sha256(v.numpy().tobytes()).hexdigest() for k,v in bundle['state'].items() if k.startswith('projection.')}
    identity={'checkpoint_sha256':pointer['sha256'],'projection_sha256':digest(projection),'encoder_sha256':digest(fit['context_identity']),
        'solver_sha256':digest(CONFIG['solver']),'layout_sha256':l.sha256,'profile_sha256':digest(config)}
    bankrows=[]; queries={}
    for row in public_records():
        saved=load(RUN/'numerical/phi_jepa/forecasts'/f"{row['sample_id']}.json")
        if saved['status']!='success': continue
        e=load(RUN/'embeddings/enriched'/f"{row['sample_id']}.json")
        value={'sample_id':row['sample_id'],'scenario_id':row['scenario_id'],'split':row['split'],'domain':CONFIG['domain'],'origin':'autonomous_prediction',
            'layout_sha256':l.sha256,'cutoff':row['public']['input']['observation_cutoff'],'times':[r['physical_time'] for r in saved['trajectory']['predictions']],
            'trajectory':[r['values'] for r in saved['trajectory']['predictions']],'embedding':e['values'],'public_sha256':digest(row['public']['input']),'embedding_request_sha256':e['request_sha256']}
        if row['split']=='train': bankrows.append(value)
        else: queries[row['sample_id']]=value
    bank=ReferenceBank.build(identity,bankrows); bank.write(RUN/'assessment/bank')
    prompts=load(ROOT/'docs/assets/prompts.json'); asset={'prompt':prompts['JUDGE_PROMPT'],'schema':load(ROOT/'docs/assets/judge_schema.json')}
    pc={'model':'gpt-5.6-sol','reasoning_effort':'medium','max_attempts_per_request':2,'max_total_attempts':2,'max_output_tokens':2048,'timeout_seconds':120}
    for row in public_records():
        if row['split']!='validation': continue
        b.check(); sid=row['sample_id']; p=PublicProblem.parse(row['public']); out=RUN/'assessment'/f'{sid}.json'
        if out.exists(): continue
        saved=load(RUN/'numerical/phi_jepa/forecasts'/f'{sid}.json')
        if saved['status']!='success': save(out,{'status':'unavailable','reason':'forecast_failure'}); continue
        obj=provider(OpenAIJudge,pc,asset,'judge-'+sid)
        try: judged=obj.judge(p)
        except Exception as exc: judged={'status':'unavailable','score':None,'reason':str(exc)}
        fullid={**identity,'bank_sha256':bank.sha256,'judge_asset_sha256':digest(asset),'judge_config_sha256':digest(pc)}
        result=combine(bank.assess(queries[sid],l,identity=identity),contract_score(p,saved['named'],p.input['controller'].get('constraints',[])),judged,profile=config,identity=fullid)
        calibration=calibrate([],assessment_identity=fullid,profile_sha256=digest(config),policy=config['calibration'],selection_scenarios=[r['scenario_id'] for r in public_records() if r['split']=='validation'])
        save(out,{'assessment':apply_threshold(result,calibration),'calibration':calibration,'physical_checks':physical_checks(p,saved['named'],config['physical_checks'])})
        print(json.dumps({'assessed':sid,'status':result['status']}),flush=True)
        b.check()


if __name__=='__main__':
    p=argparse.ArgumentParser(); p.add_argument('stage',choices=('answers','assessment')); a=p.parse_args(); globals()[a.stage]()
