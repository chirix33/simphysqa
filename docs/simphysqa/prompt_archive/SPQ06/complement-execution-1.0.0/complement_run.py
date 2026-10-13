"""Authorized Ashraf complement driver /1.0.0. GPU serial; never-reserved only.

Uses immutable execution-public-1.1.1 without changing scientific workers.
No collaborator execution entry point. Main and development ledgers are separate.
"""
import argparse,json,math,subprocess,time,traceback
from datetime import datetime,timezone
from simphysqa import complement_execution as complement
from pathlib import Path
from simphysqa import execution_adapter as adapter,main_execution_queue as queue,main_allocation,main_record_index,main_import
from simphysqa.execution_adapter import read,put,sha,digest,canonical

BASE=Path('C:/Users/aashraf/.codex/visualizations/2026/10/06/01a1131b-eac2-7a31-afb4-f219a8dd6471/spq06/2026-10-09')
RUN=BASE/'complement-execution-1.0.0';CENTRAL=BASE/'central-main-1.0.0';PACKAGE=BASE/'execution-public-1.1.1'
SOURCE=BASE/'complement-live-src-1.0.1';PREPARED=BASE/'complement-preparation-1.0.1';REPO=Path('C:/Users/aashraf/.codex/worktrees/simphysqa/phi-jepa')
adapter.canonical_records=main_record_index.canonical_records
SHARDS=['qwen3_8b_direct--enriched','qwen3_8b_thinking--enriched','llama31_8b_direct--enriched','llama31_8b_cot--enriched',
        'qwen3_32b_awq_off--enriched','qwen3_32b_awq_on--enriched','qwen3_8b_direct--structured_only','qwen3_32b_awq_on--structured_only']

def linux(path):
    value=str(path).replace('\\','/');return '/mnt/'+value[0].lower()+value[2:] if len(value)>1 and value[1]==':' else value

def command(args,log,timeout=None):
    start=time.monotonic();put(Path(str(log)+'.command.json'),{'args':args,'scope':complement.SCOPE,'unix_seconds':time.time()})
    try:
        with Path(log).open('xb') as output: result=subprocess.run(args,stdout=output,stderr=subprocess.STDOUT,timeout=timeout)
    except subprocess.TimeoutExpired:
        put(Path(str(log)+'.lifecycle.json'),{'elapsed_seconds':time.monotonic()-start,'returncode':None,'state':'unknown','reason':'outer command timeout; child termination not assumed; reservation retained'})
        raise
    elapsed=time.monotonic()-start
    put(Path(str(log)+'.lifecycle.json'),{'elapsed_seconds':elapsed,'returncode':result.returncode})
    if result.returncode:raise RuntimeError('command failed; preserved '+str(log))
    return elapsed

def wsl(bindings,script,args):
    return ['wsl.exe','-d','Ubuntu-24.04','--','env','PYTHONDONTWRITEBYTECODE=1','PYTHONUTF8=1',bindings['interpreter'],linux(script),*args]

def prepare():
    import shutil
    from simphysqa import complement_budget as budget,complement_preparation as preparation
    RUN.mkdir(exist_ok=False)
    approval=read(SOURCE/'user-authorization.json')
    before=preparation.ledger_snapshot(CENTRAL/'main.sqlite');put(RUN/'ledger-before.json',before)
    preparation.validate(PREPARED)
    preparation.forecast(BASE,PREPARED,RUN/'forecast-before.json',cutoff_utc=approval['result_import_cutoff_utc'])
    original=main_allocation.Ledger(CENTRAL/'main.sqlite')
    revision=budget.apply(original,approval);put(RUN/'budget-revision.json',revision)
    control=original.reserve_control('Ashraf','complement authorization, frozen identity and assignment preparation',600);started=time.monotonic()
    try:
        registration=complement.register(original,PREPARED,approval);put(RUN/'registration.json',registration)
    finally:original.db.close()
    ledger=complement.Ledger(CENTRAL/'main.sqlite')
    try:
        assignment=ledger.issue('Ashraf',[x['shard_id'] for x in ledger.registry['spec']['shards']]);put(RUN/'assignment.json',assignment)
        for shard in SHARDS:
            for folder in ('bindings','mappings','qualification'):
                source=BASE/'main-ashraf-1.0.0'/folder/(shard+'.json')
                target=RUN/folder/(shard+'.json');target.parent.mkdir(parents=True,exist_ok=True)
                with target.open('xb') as out:out.write(source.read_bytes())
            put(RUN/'assignments'/(shard+'.json'),assignment)
            mapping=read(RUN/'mappings'/(shard+'.json'))
            for e in mapping['initial_task_evidence']+mapping['continuation_task_evidence']:
                if sha(e['source'])!=e['sha256']:raise ValueError('mapped task evidence changed')
            qual=read(RUN/'qualification'/(shard+'.json'))
            if not ledger.db.execute('SELECT 1 FROM qualifications WHERE hash=?',(digest(qual),)).fetchone():raise ValueError('reviewed main qualification missing')
        identities={str(p):sha(p) for p in [PACKAGE/'package-manifest.json',PREPARED/'manifest.json',PREPARED/'complement-manifest.json',PREPARED/'public/execution-inputs.json',SOURCE/'complement_run.py',SOURCE/'complement_preflight.py',SOURCE/'main_verify.py',SOURCE/'user-authorization.json']}
        for p in (SOURCE/'src/simphysqa').rglob('*'):
            if p.is_file():identities[str(p)]=sha(p)
        analysis=ledger.reserve_control('Ashraf','separate core/complement/combined analyses and final audit export',3600)
        put(RUN/'execution-freeze.json',{'version':'SPQ06-complement-run/1.0.0','base_commit':'239cda56fff00785b4c3d63e971bec94cdc9bdda','scope':complement.SCOPE,'shards':SHARDS,'selected_items':200,'initial_calls':1600,'maximum_continuations':320,'maximum_calls':1920,'identities':identities,'cutoff_utc':approval['result_import_cutoff_utc'],'analysis_control':analysis,'accounting':'single central ledger; bounded processes include preflight/loading/stages/teardown once; central controls separate; measured dispatcher gaps once; unknown bounds retained','post_core_results_expansion':True,'collaborator_inference_authorized':False})
        ledger.settle_control(control,time.monotonic()-started)
        preparation.forecast(BASE,PREPARED,RUN/'forecast-after-budget.json',cutoff_utc=approval['result_import_cutoff_utc'])
        put(RUN/'preparation-accounting.json',ledger.summary());print('frozen approved complement',ledger.summary(),flush=True)
    except BaseException:
        if ledger.db.execute('SELECT actual FROM control_work WHERE id=?',(control,)).fetchone()[0] is None:ledger.settle_control(control,time.monotonic()-started,'unknown')
        raise
    finally:ledger.db.close()

def central_verify(ledger,keys,output):
    from simphysqa.spq06 import parse_answer
    from simphysqa.main_analysis import assess
    from simphysqa.heldout_scope import formal_scope
    plan=read(BASE/'main-run-preflight-1.0.0/main-run-plan.json');plan['items']=read(PREPARED/'complement-manifest.json')['items'];scope=plan['generation_candidate_scope'];actual=adapter.canonical_records(ledger);checks=[]
    with formal_scope(scope['candidates'],scope['excluded_groups']):
        for key in keys:
            raw=actual.get(key)
            if raw is None:raise ValueError('actual imported canonical key missing: '+key)
            sid,cid,label,stage=key.split('|');item=next(i for i in plan['items'] if i['sample_id']==sid);record=read(Path(plan['preparation'])/item['private_record'])
            if digest(record)!=item['record_sha256']:raise ValueError('private scoring join changed')
            condition=next(c for c in plan['conditions'] if c['condition_id']==cid)
            parsed=None;diag=None;error=None
            try:parsed,diag=parse_answer(raw['raw_output'])
            except (ValueError,TypeError) as exc:error=str(exc)
            first=actual.get(adapter.stage_key(sid,cid,label,1));second=actual.get(adapter.stage_key(sid,cid,label,2))
            scored=assess(record,condition,first,second)
            checks.append({'key':key,'raw_sha256':digest(raw),'private_record_sha256':item['record_sha256'],'parsed_response':parsed,'parser_diagnostics':diag,'parser_error':error,'score':scored})
    put(output,{'actual_main_stages':checks,'fixed_item_denominator_per_combination':200,'integrity_verified':True,'accuracy_used_for_gate':False,'parser_scoring_versions':{name:sha(REPO/'src/simphysqa'/(name+'.py')) for name in ('spq06','scoring','main_analysis','explanation_evaluation','clarification_evaluation')}})

def run(first_only=False):
    if (RUN/'QUEUE-PAUSED.json').exists() and not (RUN/'coordinator-repair-disposition-1.0.1.json').exists():raise ValueError('preserved queue pause; no automatic unblock')
    overlay=read(RUN/'orchestration-overlay-1.0.1.json')
    for file,expected in overlay['identities'].items():
        if sha(file)!=expected:raise ValueError('reviewed central repair snapshot changed '+file)
    freeze=read(RUN/'execution-freeze.json')
    for file,expected in freeze['identities'].items():
        if sha(file)!=expected:raise ValueError('execution freeze changed '+file)
    ledger=complement.Ledger(CENTRAL/'main.sqlite');spec=ledger.registry['spec']
    first_pass=(RUN/'first-main-batch-integrity.json').exists()
    try:
        for shard in SHARDS:
            cid,label=shard.split('--');assignment=read(RUN/'assignments'/(shard+'.json'));bindings=read(RUN/'bindings'/(shard+'.json'))
            condition=read(PACKAGE/spec['conditions'][cid]['path']);allowance=condition['settings']['max_seconds']
            for stage in (1,2):
                while True:
                    keys=[k for k in ledger.pending(assignment['id'],'Ashraf') if k.endswith('|'+str(stage)) and k.split('|')[1:3]==[cid,label]]
                    if not keys:break
                    # Hold central verification600 and preflight/loading600 in addition
                    # to unchanged stage bounds. Work already ended settles measured.
                    calendar=(datetime.fromisoformat(freeze['cutoff_utc'])-datetime.now(timezone.utc)).total_seconds()
                    count=min(50 if stage==1 else 40,len(keys),math.floor((ledger.remaining('Ashraf')-1200)/allowance),math.floor((calendar-1200-3600)/allowance))
                    if count<=0:
                        put(RUN/('bounded-stop-'+str(time.time_ns())+'.json'),{'shard':shard,'stage':stage,'remaining_never_reserved':len(keys),'calendar_seconds':calendar,'reason':'no conservative batch plus import and final analysis fits budget/calendar','accounting':ledger.summary()});print('BOUNDED STOP',shard,stage,flush=True);return
                    keys=keys[:count];sequence=ledger.db.execute('SELECT COUNT(*) FROM processes').fetchone()[0]+1
                    name=f'{sequence:03d}--{shard}--stage{stage}';keys_path=RUN/'key-batches'/(name+'.json');put(keys_path,keys)
                    process=None;prepared=False;metadata_start=time.monotonic()
                    try:
                        ticket=queue.reserve_overhead(ledger,assignment['id'],'Ashraf',cid,label);process=ticket['id'];put(RUN/'preflight-processes'/(name+'.json'),ticket)
                        qualification_path=RUN/'qualification'/(shard+'.json');adopt=not qualification_path.exists()
                        source=RUN/'source-qualification'/(shard+'.json') if adopt else qualification_path
                        out=RUN/'preflights'/name
                        args=['--package',linux(PACKAGE),'--bindings',linux(RUN/'bindings'/(shard+'.json')),'--qualification',linux(source),'--mapping',linux(RUN/'mappings'/(shard+'.json')),'--keys',linux(keys_path),'--routes',linux(RUN/'routes-1.0.1'/shard),'--output',linux(out)]
                        args.extend(['--registry',linux(PREPARED/'public/execution-inputs.json'),'--registry-sha256',sha(PREPARED/'public/execution-inputs.json')])
                        if adopt:args.append('--adopt')
                        command(wsl(bindings,SOURCE/'complement_preflight.py',args),RUN/(name+'-preflight.log'),timeout=600)
                        proof=read(out/'proof.json');qual=read(out/'qualification.json')
                        if adopt:
                            qh=ledger.approve_qualification(qual);put(qualification_path,qual);put(RUN/'qualification'/(shard+'-approved.json'),{'qualification_sha256':qh})
                        else:qh=digest(qual)
                        proof['accounted_preflight_seconds']=time.monotonic()-metadata_start;put(out/'accounted-proof.json',proof)
                        job=RUN/'jobs'/name
                        complement.prepare_job(ledger,assignment['id'],'Ashraf',qh,keys,bindings,job,proof,process);prepared=True
                        outer=command(wsl(bindings,PACKAGE/'procedures/public_executor.py',['launch','--package',linux(PACKAGE),'--job',linux(job),'--authorize-main']),RUN/(name+'-adapter.log'))
                        receipt=read(job/'process-receipt.json');preparation=read(job/'launch.json')['preparation_elapsed_seconds']
                        gap=max(0,outer-(receipt['elapsed_seconds']-preparation));ledger.add_dispatcher_gap(process,gap,{'outer_seconds':outer,'adapter_receipt_sha256':sha(job/'process-receipt.json'),'formula':'outer launch command minus adapter interval, excluding preparation already counted inside receipt'})
                        control=ledger.reserve_control('Ashraf','immutable return/import, actual token checks, central parse/score joins and routing: '+name,600);central_start=time.monotonic()
                        try:
                            returned=RUN/'returns'/name;adapter.export_return(job,returned)
                            imported=ledger.transaction(lambda:complement.import_return(ledger,returned,RUN/'immutable-imports'));put(RUN/'import-receipts'/(name+'.json'),imported)
                            if imported['validation_failures'] or len(imported['accepted_keys'])!=len(keys) or imported['conflicts']:raise RuntimeError('main import integrity failure; preserved return requires review')
                            command(wsl(bindings,SOURCE/'main_verify.py',['--package',linux(PACKAGE),'--job',linux(job),'--preflight',linux(out/'render-verification.json'),'--output',linux(RUN/'verification'/(name+'.json'))]),RUN/(name+'-verify.log'),timeout=600)
                            central_verify(ledger,keys,RUN/'central-stage-records'/(name+'.json'))
                            if stage==1:
                                def routes():
                                    for key in keys:
                                        item=next(i for i in spec['items'] if i['sample_id']==key.split('|')[0])
                                        if item['family']=='clarification':complement.route(ledger,key,BASE/'main-preparation-1.0.0',RUN/'routes-1.0.1'/shard/(item['sample_id']+'.json'))
                                ledger.transaction(routes)
                            if not first_pass:
                                put(RUN/'first-main-batch-integrity.json',{'complement_scope':complement.SCOPE,'passed':True,'name':name,'initials':len(keys),'import_receipt_sha256':sha(RUN/'import-receipts'/(name+'.json')),'actual_token_checks_sha256':sha(RUN/'verification'/(name+'.json')),'central_scoring_join_sha256':sha(RUN/'central-stage-records'/(name+'.json')),'main_scope':True,'accuracy_not_gate':True});first_pass=True
                            ledger.settle_control(control,time.monotonic()-central_start)
                        except BaseException:
                            ledger.settle_control(control,time.monotonic()-central_start,'unknown');raise
                        print(name,'imported',len(keys),'main accounted',round(ledger.used(),3),'Ashraf remaining',round(ledger.remaining('Ashraf'),3),flush=True)
                        put(RUN/'accounting-snapshots'/(name+'.json'),ledger.summary())
                        if first_only:return
                    except BaseException as exc:
                        if process and not prepared:
                            queue.block_startup(ledger,assignment['id'],'Ashraf',cid,process,str(exc),time.monotonic()-metadata_start if not isinstance(exc,(KeyboardInterrupt,subprocess.TimeoutExpired)) else None)
                        put(RUN/'QUEUE-PAUSED.json',{'scope':complement.SCOPE,'shard':shard,'process':process,'scientific_reserved':prepared,'reason':type(exc).__name__+': '+str(exc),'traceback':traceback.format_exc(),'accounting':ledger.summary(),'policy':'preserve failures; no automatic unblock/retry/orphan release'});raise
        put(RUN/'execution-completion.json',{'initial_reservations':ledger.db.execute("SELECT COUNT(*) FROM stages WHERE key LIKE '%|1'").fetchone()[0],'conditional_reservations':ledger.db.execute("SELECT COUNT(*) FROM stages WHERE key LIKE '%|2'").fetchone()[0],'routes':ledger.db.execute('SELECT COUNT(*) FROM routes').fetchone()[0],'accounting':ledger.summary(),'collaborator_runs':0})
    finally:ledger.db.close()

if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('command',choices=('prepare','first','run'));a=p.parse_args()
    if a.command=='prepare':prepare()
    else:run(a.command=='first')
