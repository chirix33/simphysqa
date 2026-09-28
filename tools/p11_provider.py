"""One provider worker owns the paid ledger; local jobs have separate records."""
from p11_common import *
from phi_jepa.integration.contracts import PublicProblem
from phi_jepa.providers.openai_enrichment import OpenAIEnrichment
from phi_jepa.providers.credentials import load_openai_key
from phi_jepa.providers.cache import FrozenOutputCache

def enrich_rows(rows):
    c=load(ROOT/'configs/model_context_p02b.json'); asset=load(ROOT/c['enrichment_asset']); b=budget()
    for row in rows:
        time_guard(); p=PublicProblem.parse(row['public']); path=OUT/'enrichment'/f'{p.sample_id}.json'
        if path.exists(): continue
        if row.get('enrichment_cache'):
            save(path,load(row['enrichment_cache'])); continue
        failure=OUT/'failures/enrichment'/f'{p.sample_id}.json'
        if failure.exists(): continue
        pc={**c['enrichment_provider'],'max_attempts_per_request':1}; ledger=OUT/'provider_ledgers'/f'enrich-{p.sample_id}.json'
        obj=OpenAIEnrichment(load_openai_key(ROOT/'.env'),pc,asset,FrozenOutputCache(OUT/'context_cache'),event_sink=lambda v:save(ledger,v),ledger=load(ledger) if ledger.exists() else None)
        obj.transport=b.transport(obj._http); start=time.time()
        try: save(path,obj.enrich(p,p.input['observation_cutoff'])); status='success'
        except Exception as exc: save(failure,{'status':'failure','reason':str(exc),'type':type(exc).__name__}); status='failure'
        print(json.dumps({'enrichment':p.sample_id,'domain':row['domain'],'status':status,'seconds':time.time()-start}),flush=True)
        b.check()

def answers():
    from phi_jepa.providers.openai_answer import OpenAIAnswer
    rows=load(OUT/'selected-public.json');pc={**load(ROOT/'configs/baselines_p05b.json')['answer_profile'],'max_attempts_per_request':1};b=budget()
    pending=[(row,method) for row in rows if row['split']=='test_id' for method in (['main_phi','direct_llm','appendix_phi'] if row['appendix'] else ['main_phi','direct_llm'])]
    while pending:
        time_guard();progress=False
        for row,method in list(pending):
            sid=row['sample_id'];path=OUT/'answers'/method/f'{sid}.json'
            if path.exists():pending.remove((row,method));continue
            # Wait for legitimate local main learning/forecast before API answers.
            main=StudyRun(row['domain'],'main').root/'numerical/phi_jepa/forecasts'/f'{sid}.json'
            if not main.exists():continue
            forecast=None;outcomes=[]
            if method!='direct_llm':
                cohort='main' if method=='main_phi' else 'appendix';fp=StudyRun(row['domain'],cohort).root/'numerical/phi_jepa/forecasts'/f'{sid}.json'
                if not fp.exists():continue
                saved=load(fp)
                if saved['status']!='success':save(path,{'status':'forecast_failure','answer':None,'reason':saved['reason']});pending.remove((row,method));continue
                forecast=saved['named'];outcomes=saved['readout']
            asset=load(ROOT/('docs/assets/p11_direct_answer_v1.json' if method=='direct_llm' else 'docs/assets/p04a_answer_v1.json'))
            ledger=OUT/'provider_ledgers'/f'{method}-{sid}.json';obj=OpenAIAnswer(load_openai_key(ROOT/'.env'),pc,asset,FrozenOutputCache(OUT/'answer_cache'),event_sink=lambda v:save(ledger,v),ledger=load(ledger) if ledger.exists() else None)
            bounded=b.transport(obj._http)
            def transport(payload,timeout):
                time_guard();return bounded(payload,min(timeout,max(1,EXPENSIVE_STOP-time.time())))
            obj.transport=transport;start=time.time();p=PublicProblem.parse(row['public'])
            try:answer=obj.answer(p,forecast,outcomes,condition=method,boolean_policy='direct_prediction' if method=='direct_llm' else 'readout');result={'status':'success','answer':answer}
            except Exception as exc:result={'status':'api_or_parse_failure','answer':None,'reason':str(exc),'type':type(exc).__name__}
            save(path,{**result,'sample_id':sid,'method':method,'domain':row['domain'],'seconds':time.time()-start,'public_sha256':digest(row['public']),'forecast_sha256':digest(forecast),'asset_sha256':digest(asset),'provider_profile':pc,'boolean_policy':'direct_prediction' if method=='direct_llm' else 'readout','response_metadata':obj.response_metadata})
            print(json.dumps({'method':method,'sample_id':sid,'status':result['status'],'seconds':time.time()-start}),flush=True);pending.remove((row,method));progress=True;b.check()
        if not progress:
            if (OUT/'cpu_done.json').exists():break
            time.sleep(3)
    save(OUT/'answer_completion.json',{'unfinished':[{'sample_id':r['sample_id'],'method':m} for r,m in pending],'time':time.time()})

if __name__=='__main__':
    if sys.argv[1]=='probe':
        inventory=load(OUT/'candidate_inventory.json');enrich_rows([v['pools']['train'][0] for v in inventory['domains'].values()])
    elif sys.argv[1] in ('answers','wait_answers'):
        if sys.argv[1]=='wait_answers':
            rows=load(OUT/'selected-public.json')
            while any(not (OUT/'enrichment'/f"{r['sample_id']}.json").exists() and not (OUT/'failures/enrichment'/f"{r['sample_id']}.json").exists() for r in rows):time_guard();time.sleep(3)
        archive_sources('answers');answers()
    else: enrich_rows(load(OUT/'selected-public.json'))
