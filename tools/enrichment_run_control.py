"""Durable supervisor for the explicitly approved P12 enrichment workload only."""
from p12_enrichment import *
from datetime import datetime, timezone
import os, subprocess, shutil

RUN = NATIVE/'p12-enrichment-full-01'
EXPORT = ROOT/'docs/reviews/artifacts/P12_enrichment_full'
APPROVED = PILOT/'approved-full-enrichment.json'

def now(): return datetime.now(timezone.utc).isoformat()

def prepare(verified_at):
    proposal=load(PILOT/'proposed-full-enrichment.json')
    if implementation_identity()!=proposal['implementation_sha256']:raise ValueError('reviewed implementation changed')
    if file_hash(PILOT/'inventory-after.json')!=proposal['inventory_sha256']:raise ValueError('reviewed inventory changed')
    if APPROVED.exists() or (RUN/'spend-ledger.json').exists():raise ValueError('approval/run already exists; use status or resume')
    config,asset=policy()
    if digest(config)!=proposal['provider_sha256'] or digest(asset)!=proposal['asset_sha256']:raise ValueError('provider identity changed')
    records=inventory();old={r['sample_id']:r for r in load(PILOT/'inventory-after.json')}
    if len(records)!=len(old) or any(r['request_sha256']!=old[r['sample_id']]['request_sha256'] for r in records):raise ValueError('public inventory changed')
    missing=dict(Counter(r['scope'] for r in records if not r['compatible_origin']))
    if missing!={'train_validation':7775,'confirmation':500}:raise ValueError('missing inventory changed; reconcile before dispatch')
    RUN.mkdir(exist_ok=True);EXPORT.mkdir(parents=True,exist_ok=True)
    proof={'verified_at_utc':verified_at,'pricing_sha256':digest(proposal['pricing']),
           'sources':proposal['pricing']['sources'],'verification':'Official pages fetched and checked in the approving session.'}
    age=(datetime.now(timezone.utc)-datetime.fromisoformat(verified_at)).total_seconds()
    if not 0<=age<3600:raise ValueError('fresh session pricing verification required')
    atomic_json(RUN/'pricing-verification.json',proof)
    approved={**proposal,'enabled':True,'full_enrichment_enabled':True,
              'authorization':'User explicitly approved: "$475 maximum for both scopes" in response to the additional $475 proposal; pilot charged separately.',
              'authorized_scopes':['train_validation','confirmation'],'authorized_at_utc':now(),
              'pricing_verification_path':str(RUN/'pricing-verification.json'),
              'supervisor_sha256':file_hash(__file__),'supervisor_wall_seconds_cap':72000}
    atomic_json(APPROVED,approved);atomic_json(RUN/'approved-config.json',approved)
    atomic_json(RUN/'launch-preflight.json',{'verified_at_utc':now(),'missing':missing,'compatible_records':sum(bool(r['compatible_origin']) for r in records),
                 'implementation_sha256':implementation_identity(),'inventory_sha256':proposal['inventory_sha256'],'public_requests_verified':len(records)})
    for name in ('approved-config.json','launch-preflight.json','pricing-verification.json'):shutil.copyfile(RUN/name,EXPORT/name)
    shutil.copyfile(__file__,RUN/'supervisor.py')
    print({'prepared':True,'missing':missing,'usd_cap':approved['usd_cap'],'attempt_cap':approved['attempt_cap']})

def summary():
    state=load(RUN/'spend-ledger.json') if (RUN/'spend-ledger.json').exists() else {'attempts':[],'stopped':None}
    results=[load(p) for p in (RUN/'results').glob('*.json')]
    scopes={}
    for scope,n in (('train_validation',7775),('confirmation',500)):
        rows=[r for r in results if r['scope']==scope];attempts=[a for a in state['attempts'] if a.get('scope')==scope]
        counts=dict(Counter(r['status'] for r in rows))
        scopes[scope]={'requested_unique':n,'results':counts,'remaining_unprocessed':n-len(rows),'attempts':len(attempts),
                      'charged_usd':sum(a['charged_nano_usd'] for a in attempts)/1e9,
                      'input_tokens':sum((a.get('usage') or {}).get('input_tokens',0) for a in attempts),
                      'output_tokens':sum((a.get('usage') or {}).get('output_tokens',0) for a in attempts),
                      'unknown_usage_attempts':sum(a.get('usage') is None for a in attempts)}
    value={'updated_at_utc':now(),'scopes':scopes,'attempts':len(state['attempts']),
           'charged_usd':sum(a['charged_nano_usd'] for a in state['attempts'])/1e9,'budget_stop':state['stopped'],
           'all_records_successful':all(s['results'].get('success',0)+s['results'].get('cache_reused',0)==s['requested_unique'] for s in scopes.values()),
           'supervisor':load(RUN/'supervisor-status.json') if (RUN/'supervisor-status.json').exists() else None}
    atomic_json(RUN/'status.json',value);atomic_json(EXPORT/'status.json',value)
    return value

def worker():
    import fcntl
    approved=load(APPROVED)
    if file_hash(__file__)!=approved['supervisor_sha256']:raise ValueError('approved supervisor changed')
    with (RUN/'supervisor.lock').open('a') as lock:
        fcntl.flock(lock,fcntl.LOCK_EX|fcntl.LOCK_NB)
        launch=RUN/'supervisor-budget.json'
        if not launch.exists():atomic_json(launch,{'deadline_unix':time.time()+approved['supervisor_wall_seconds_cap']})
        deadline=load(launch)['deadline_unix'];error=None;child=None
        try:
            for scope in approved['authorized_scopes']:
                if time.time()>=deadline:raise TimeoutError('supervisor wall cap')
                atomic_json(RUN/'supervisor-status.json',{'status':'running','pid':os.getpid(),'scope':scope,'updated_at_utc':now()})
                command=[sys.executable,str(ROOT/'tools/p12_enrichment_full.py'),'--config',str(APPROVED),'--scope',scope]
                with (RUN/(scope+'.log')).open('ab',buffering=0) as output:
                    child=subprocess.Popen(command,cwd=ROOT,stdin=subprocess.DEVNULL,stdout=output,stderr=subprocess.STDOUT)
                    while True:
                        try:code=child.wait(timeout=max(.1,min(30,deadline-time.time())));break
                        except subprocess.TimeoutExpired:
                            summary()
                            if time.time()>=deadline:raise TimeoutError('supervisor wall cap')
                    if code:raise RuntimeError('scope worker exited '+str(code))
                    result=summary()
                    if result['budget_stop']:raise RuntimeError('budget stopped: '+result['budget_stop'])
        except BaseException as exc:
            error=type(exc).__name__+': '+str(exc)
            if child is not None and child.poll() is None:
                child.terminate()
                try:child.wait(timeout=10)
                except subprocess.TimeoutExpired:child.kill();child.wait()
        finally:
            atomic_json(RUN/'supervisor-status.json',{'status':'stopped' if error else 'finished','failure':error,'updated_at_utc':now()})
            result=summary();atomic_json(RUN/'completion.json',result);atomic_json(EXPORT/'completion.json',result)
            if (RUN/'spend-ledger.json').exists():shutil.copyfile(RUN/'spend-ledger.json',EXPORT/'spend-ledger.json')

def start():
    approved=load(APPROVED)
    if not approved.get('enabled') or approved['authorized_scopes']!=['train_validation','confirmation']:raise ValueError('both-scope approval required')
    if file_hash(__file__)!=approved['supervisor_sha256']:raise ValueError('supervisor changed')
    if (RUN/'supervisor-status.json').exists():
        prior=load(RUN/'supervisor-status.json')
        if prior['status']=='running':
            try:os.kill(prior['pid'],0)
            except ProcessLookupError:pass
            else:raise ValueError('supervisor already running')
    with (RUN/'supervisor.log').open('ab',buffering=0) as output:
        proc=subprocess.Popen([sys.executable,str(Path(__file__).resolve()),'worker'],cwd=ROOT,
                stdin=subprocess.DEVNULL,stdout=output,stderr=subprocess.STDOUT,start_new_session=True)
    atomic_json(RUN/'launch.json',{'pid':proc.pid,'launched_at_utc':now(),'approved_config_sha256':file_hash(APPROVED)})
    print({'started_pid':proc.pid,'root':str(RUN)})

if __name__=='__main__':
    if sys.argv[1]=='prepare':prepare(sys.argv[2])
    elif sys.argv[1]=='start':start()
    elif sys.argv[1]=='worker':worker()
    elif sys.argv[1]=='status':print(json.dumps(summary(),indent=2))
    else:raise ValueError('unknown command')
