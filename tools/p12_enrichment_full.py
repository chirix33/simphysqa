"""Disabled-by-default full preparation executor. Requires a separately approved cap."""
from p12_enrichment import *

def run_full(config_path,scope):
    import fcntl
    from phi_jepa.providers.credentials import load_openai_key
    from phi_jepa.providers.openai_enrichment import OpenAIEnrichment
    from p10_common import guard_deployment_io
    approved=load(config_path)
    if not approved.get('enabled') or not approved.get('authorization') or scope not in approved.get('authorized_scopes',[]):
        raise ValueError('separate full-enrichment spending and scope authorization required')
    if approved['mode']!='full_enrichment':raise ValueError('pilot authorization cannot launch full preparation')
    if implementation_identity()!=approved['implementation_sha256']:raise ValueError('approved implementation changed')
    config,asset=policy()
    if digest(config)!=approved['provider_sha256'] or digest(asset)!=approved['asset_sha256']:raise ValueError('approved provider or prompt changed')
    if file_hash(PILOT/'inventory-after.json')!=approved['inventory_sha256']:raise ValueError('approved remaining inventory changed')
    def price_guard():
        from datetime import datetime,timezone
        proof=load(approved['pricing_verification_path'])
        age=(datetime.now(timezone.utc)-datetime.fromisoformat(proof['verified_at_utc'])).total_seconds()
        if not 0<=age<86400 or proof['pricing_sha256']!=digest(approved['pricing']):raise ValueError('current price verification required before dispatch')
    price_guard()
    root=Path(approved['run_root'])
    if root.parent.resolve()!=NATIVE.resolve() or not root.name.startswith('p12-enrichment-full-'):raise ValueError('new separate full-preparation directory required')
    root.mkdir(exist_ok=True)
    source=snapshot('full-enrichment-'+scope,output=root)
    atomic_json(root/'executions'/f'{source}.json',{'source':source,'config':approved,'scope':scope})
    key=load_openai_key(ROOT/'.env');guard_deployment_io()
    with (root/'worker.lock').open('a') as lock:
        fcntl.flock(lock,fcntl.LOCK_EX|fcntl.LOCK_NB)
        budget=EnrichmentBudget(root,approved,scope=scope);cache=FrozenOutputCache(root/'context_cache');index=cache_index()
        required={r['sample_id']:r for r in load(PILOT/'inventory-after.json') if r['scope']==scope and not r['compatible_origin']}
        for meta,p in public_population():
            if p.sample_id not in required:continue
            state=budget.read()
            if state['stopped'] or len(state['attempts'])>=approved['attempt_cap']:break
            result_path=root/'results'/f'{p.sample_id}.json'
            if result_path.exists():continue
            ident=request_identity(p,config,asset)
            if digest(ident)!=required[p.sample_id]['request_sha256']:raise ValueError('public request changed since approval')
            notes,origin=compatible(p,config,asset,index)
            if notes is not None:
                atomic_json(root/'enrichment'/f'{p.sample_id}.json',notes)
                atomic_json(result_path,{'status':'cache_reused','sample_id':p.sample_id,'scope':scope,'origin':origin});continue
            ledger=root/'provider_ledgers'/f'{p.sample_id}.json';started=time.perf_counter()
            provider=OpenAIEnrichment(key,config,asset,cache,event_sink=lambda v:atomic_json(ledger,v),ledger=load(ledger) if ledger.exists() else None)
            bounded=budget.transport(provider._http)
            def transport(payload,timeout):price_guard();return bounded(payload,timeout)
            provider.transport=transport
            try:
                notes=provider.enrich(p,p.input['observation_cutoff']);atomic_json(root/'enrichment'/f'{p.sample_id}.json',notes)
                result={'status':'success','failure':None}
            except Exception as exc:result={'status':'failure','failure':str(exc) if type(exc).__name__=='ProviderFailure' else type(exc).__name__}
            atomic_json(result_path,result|{'sample_id':p.sample_id,'scope':scope,'domain':meta['domain'],'split':meta['split'],
                         'latency_seconds':time.perf_counter()-started,'provider_events':provider.runner.events,'request_sha256':digest(ident)})
            print({'sample_id':p.sample_id,'scope':scope,**result,'attempts':len(budget.read()['attempts']),
                   'charged_usd':sum(r['charged_nano_usd'] for r in budget.read()['attempts'])/1e9},flush=True)

if __name__=='__main__':
    import argparse
    parser=argparse.ArgumentParser();parser.add_argument('--config',type=Path,required=True);parser.add_argument('--scope',choices=['train_validation','confirmation'],required=True)
    args=parser.parse_args();run_full(args.config,args.scope)
