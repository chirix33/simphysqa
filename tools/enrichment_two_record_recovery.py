"""Explicitly approved recovery of two public training records; no study execution."""
from enrichment_run_control import *
from phi_jepa.providers.enrichment_budget import EnrichmentBudget,EnrichmentBudgetStop,measured_cost

REC=NATIVE/'p12-enrichment-recovery-01'
DEST=ROOT/'docs/reviews/artifacts/P12_enrichment_recovery'

def validate_scope(config,rows):
    if not config.get('enabled') or not config.get('authorization'):raise ValueError('new recovery authorization required')
    if config['usd_cap']>2 or config['attempt_cap']>6 or config['wall_seconds_cap']>1800:raise ValueError('recovery cap exceeded')
    ids={r['sample_id'] for r in rows}
    if ids!={'b06de105f9948d5fb26f82e9194d2239','757d9982860c372fb1ac7fed9ddb8ffb'} or len(rows)!=2:raise ValueError('only two approved records')
    if any(r['domain']!='tethered_load' or r['split']!='train' for r in rows):raise ValueError('training scope changed')

def prepare(verified_at):
    proposal=load(RUN/'proposed-recovery.json');old=load(APPROVED)
    if (REC/'approved-config.json').exists():raise ValueError('already frozen; use run or verify')
    if implementation_identity()!=old['implementation_sha256']:raise ValueError('scientific implementation changed')
    if file_hash(RUN/'recovery-public-selection.json')!=proposal['selection_sha256']:raise ValueError('selection changed')
    rows=load(RUN/'recovery-public-selection.json');config,asset=policy()
    if digest(config)!=proposal['provider_sha256'] or digest(asset)!=proposal['asset_sha256']:raise ValueError('provider policy changed')
    prior=load(RUN/'spend-ledger.json');charged=sum(a['charged_nano_usd'] for a in prior['attempts'])/1e9
    if charged!=proposal['prior_charged_and_reserved_usd'] or charged+proposal['usd_cap']>475:raise ValueError('aggregate budget changed')
    train_charged=sum(a['charged_nano_usd'] for a in prior['attempts'] if a['scope']=='train_validation')/1e9
    if train_charged+proposal['usd_cap']>425:raise ValueError('original scope cap exceeded')
    age=(datetime.now(timezone.utc)-datetime.fromisoformat(verified_at)).total_seconds()
    if not 0<=age<3600:raise ValueError('fresh pricing verification required')
    approved={**proposal,'enabled':True,'authorization':'User answered yes to a new 30-minute recovery window, six attempts and $2 within the original unused $475 allowance.',
        'authorized_at_utc':now(),'pricing_verified_at_utc':verified_at,'implementation_sha256':implementation_identity(),
        'runner_sha256':file_hash(__file__),'prior_ledger_sha256':file_hash(RUN/'spend-ledger.json'),
        'prior_coverage_sha256':file_hash(RUN/'completion-cache-coverage.json')}
    validate_scope(approved,rows)
    REC.mkdir(exist_ok=True);atomic_json(REC/'approved-config.json',approved)
    atomic_json(REC/'selection.json',rows);shutil.copyfile(__file__,REC/'runner.py')
    print({'prepared':True,'records':len(rows),'usd_cap':2,'attempt_cap':6,'wall_seconds_cap':1800})

def run():
    import fcntl,signal
    from phi_jepa.providers.credentials import load_openai_key
    from phi_jepa.providers.openai_enrichment import OpenAIEnrichment
    from p10_common import guard_deployment_io
    approved=load(REC/'approved-config.json');rows=load(REC/'selection.json');validate_scope(approved,rows)
    if file_hash(__file__)!=approved['runner_sha256'] or implementation_identity()!=approved['implementation_sha256']:raise ValueError('approved source changed')
    if file_hash(REC/'selection.json')!=approved['selection_sha256']:raise ValueError('frozen public selection changed')
    if file_hash(RUN/'spend-ledger.json')!=approved['prior_ledger_sha256']:raise ValueError('prior spending changed')
    config,asset=policy()
    if digest(config)!=approved['provider_sha256'] or digest(asset)!=approved['asset_sha256']:raise ValueError('provider changed')
    with (REC/'worker.lock').open('a') as lock:
        fcntl.flock(lock,fcntl.LOCK_EX|fcntl.LOCK_NB)
        if all((REC/'results'/(r['sample_id']+'.json')).exists() for r in rows):
            print({'status':'already_processed','additional_requests':0});return
        timer=REC/'window.json'
        if not timer.exists():atomic_json(timer,{'deadline_unix':time.time()+approved['wall_seconds_cap'],'started_at_utc':now()})
        deadline=load(timer)['deadline_unix']
        def time_guard():
            if time.time()>=deadline:raise EnrichmentBudgetStop('recovery wall window expired')
            age=(datetime.now(timezone.utc)-datetime.fromisoformat(approved['pricing_verified_at_utc'])).total_seconds()
            if not 0<=age<86400:raise EnrichmentBudgetStop('price verification expired')
        time_guard()
        index=cache_index();prepared=[]
        for row in rows:
            p=PublicProblem.parse(row['public']);identity=request_identity(p,config,asset)
            if digest(identity)!=row['request_sha256']:raise ValueError('public request identity changed')
            notes,origin=compatible(p,config,asset,index);prepared.append((row,p,notes,origin))
        key=load_openai_key(ROOT/'.env') if any(notes is None and not (REC/'results'/(row['sample_id']+'.json')).exists() for row,p,notes,origin in prepared) else None
        guard_deployment_io();budget=EnrichmentBudget(REC,approved);cache=FrozenOutputCache(REC/'context_cache')
        def alarm(*_):raise EnrichmentBudgetStop('recovery wall window expired')
        signal.signal(signal.SIGALRM,alarm);signal.setitimer(signal.ITIMER_REAL,max(.001,deadline-time.time()))
        try:
            for row,p,notes,origin in prepared:
                path=REC/'results'/(p.sample_id+'.json')
                if path.exists():continue
                time_guard()
                if notes is not None:
                    atomic_json(REC/'enrichment'/(p.sample_id+'.json'),notes)
                    atomic_json(path,{'status':'cache_reused','sample_id':p.sample_id,'origin':origin});continue
                ledger=REC/'provider_ledgers'/(p.sample_id+'.json')
                provider=OpenAIEnrichment(key,config,asset,cache,event_sink=lambda v:atomic_json(ledger,v),ledger=load(ledger) if ledger.exists() else None)
                bounded=budget.transport(provider._http)
                def transport(payload,timeout):time_guard();return bounded(payload,min(timeout,max(.001,deadline-time.time())))
                provider.transport=transport;started=time.perf_counter()
                try:
                    notes=provider.enrich(p,p.input['observation_cutoff']);atomic_json(REC/'enrichment'/(p.sample_id+'.json'),notes)
                    result={'status':'success','failure':None}
                except Exception as exc:result={'status':'failure','failure':str(exc) if type(exc).__name__=='ProviderFailure' else type(exc).__name__}
                atomic_json(path,result|{'sample_id':p.sample_id,'request_sha256':row['request_sha256'],'latency_seconds':time.perf_counter()-started,
                    'provider_events':provider.runner.events})
                print({'sample_id':p.sample_id,**result,'attempts':len(budget.read()['attempts']),
                    'charged_usd':sum(a['charged_nano_usd'] for a in budget.read()['attempts'])/1e9},flush=True)
        finally:signal.setitimer(signal.ITIMER_REAL,0)

def verify():
    from p10_common import guard_deployment_io
    guard_deployment_io();approved=load(REC/'approved-config.json')
    if file_hash(RUN/'completion-cache-coverage.json')!=approved['prior_coverage_sha256'] or file_hash(RUN/'spend-ledger.json')!=approved['prior_ledger_sha256']:raise ValueError('historical audit changed')
    coverage=load(RUN/'completion-cache-coverage.json');selected={r['sample_id']:r for r in load(REC/'selection.json')};config,asset=policy();index=cache_index()
    for row in coverage:
        if row['sample_id'] in selected:
            p=PublicProblem.parse(selected[row['sample_id']]['public']);notes,origin=compatible(p,config,asset,index)
            if not origin:raise ValueError('recovery still missing')
            if notes!=load(REC/'enrichment'/(p.sample_id+'.json')):raise ValueError('recovered notes differ from cache')
            row['compatible_origin']=origin
        else:
            origin=row['compatible_origin']
            if not origin or file_hash(origin['cache_file'])!=origin['cache_sha256']:raise ValueError('prior cache changed')
    state=load(REC/'spend-ledger.json') if (REC/'spend-ledger.json').exists() else {'attempts':[]}
    for a in state['attempts']:
        body=load(REC/'responses'/f"{a['attempt_id']:04}.json")
        if measured_cost(body,approved['pricing'])!=a['usage']:raise ValueError('recovery usage mismatch')
    spent=sum(a['charged_nano_usd'] for a in state['attempts'])/1e9
    report={'verified_at_utc':now(),'recovered_records':2,'attempts':len(state['attempts']),'recovery_charged_usd':spent,
        'input_tokens':sum(a['usage']['input_tokens'] for a in state['attempts']),'output_tokens':sum(a['usage']['output_tokens'] for a in state['attempts']),
        'latency_seconds':sum(a['latency_seconds'] for a in state['attempts']),
        'combined_full_and_recovery_charged_or_reserved_usd':round(approved['prior_charged_and_reserved_usd']+spent,9),
        'combined_including_pilot_usd':round(approved['prior_charged_and_reserved_usd']+spent+1.284679,9),
        'coverage':dict(Counter(r['scope'] for r in coverage)),'missing':0,'historical_unknown_holds_preserved_usd':.61101,
        'historical_ledger_unchanged':True,'approved_config_sha256':file_hash(REC/'approved-config.json'),
        'recovery_ledger_sha256':file_hash(REC/'spend-ledger.json') if (REC/'spend-ledger.json').exists() else None}
    atomic_json(REC/'coverage-after-recovery.json',coverage);atomic_json(REC/'recovery-completion.json',report)
    DEST.mkdir(parents=True,exist_ok=True)
    for p in REC.rglob('*'):
        if not p.is_file() or p.name=='worker.lock' or p.name.startswith('.pending-'):continue
        destination=DEST/p.relative_to(REC);destination.parent.mkdir(parents=True,exist_ok=True);shutil.copyfile(p,destination)
    print(json.dumps(report,indent=2))

if __name__=='__main__':
    if sys.argv[1]=='prepare':prepare(sys.argv[2])
    elif sys.argv[1]=='run':run()
    elif sys.argv[1]=='verify':verify()
    else:raise ValueError('unknown command')
