"""Authorized Ashraf main driver /1.0.0. GPU serial; never-reserved only.

Uses immutable execution-public-1.1.1 without changing scientific workers.
No collaborator execution entry point. Main and development ledgers are separate.
"""
import argparse,json,math,subprocess,time,traceback
from pathlib import Path
from simphysqa import execution_adapter as adapter,main_execution_queue as queue,main_allocation
from simphysqa.execution_adapter import read,put,sha,digest,canonical

BASE=Path('C:/Users/aashraf/.codex/visualizations/2026/10/06/01a1131b-eac2-7a31-afb4-f219a8dd6471/spq06/2026-10-09')
RUN=BASE/'main-ashraf-1.0.0';CENTRAL=BASE/'central-main-1.0.0';PACKAGE=BASE/'execution-public-1.1.1'
SOURCE=BASE/'main-src-1.0.0';REPO=Path('C:/Users/aashraf/.codex/worktrees/simphysqa/phi-jepa')
SHARDS=['qwen3_8b_direct--enriched','qwen3_8b_thinking--enriched','llama31_8b_direct--enriched','llama31_8b_cot--enriched',
        'qwen3_32b_awq_off--enriched','qwen3_32b_awq_on--enriched','qwen3_8b_direct--structured_only','qwen3_32b_awq_on--structured_only']

def linux(path):
    value=str(path).replace('\\','/');return '/mnt/'+value[0].lower()+value[2:] if len(value)>1 and value[1]==':' else value

def command(args,log):
    start=time.monotonic();put(Path(str(log)+'.command.json'),{'args':args,'scope':'main','unix_seconds':time.time()})
    with Path(log).open('xb') as output: result=subprocess.run(args,stdout=output,stderr=subprocess.STDOUT)
    elapsed=time.monotonic()-start
    put(Path(str(log)+'.lifecycle.json'),{'elapsed_seconds':elapsed,'returncode':result.returncode})
    if result.returncode:raise RuntimeError('command failed; preserved '+str(log))
    return elapsed

def wsl(bindings,script,args):
    return ['wsl.exe','-d','Ubuntu-24.04','--','env','PYTHONDONTWRITEBYTECODE=1','PYTHONUTF8=1',bindings['interpreter'],linux(script),*args]

def prepare():
    RUN.mkdir(exist_ok=False);CENTRAL.mkdir(exist_ok=False)
    ledger=main_allocation.Ledger.create(CENTRAL/'main.sqlite',PACKAGE)
    main_allocation.install(ledger,{'Ashraf':72000,'Collaborator':100800})
    control=ledger.reserve_control('Ashraf','frozen main identity, evidence adoption and assignment preparation',600);started=time.monotonic()
    try:
        tests=BASE/'main-allocation-offline-1.0.2.log';log=tests.read_text(encoding='utf8')
        if 'Ran 108 tests' not in log or '\nOK' not in log:raise ValueError('offline verification required')
        adapter.validate_package(PACKAGE)
        evidence_path=BASE/'awq-supplement-1.0.0/delivery-1.0.0/qualification-evidence-mapping.json';evidence=read(evidence_path)
        if evidence['target_main_package_sha256']!=sha(PACKAGE/'package-manifest.json'):raise ValueError('reviewed package changed')
        spec=read(PACKAGE/'execution-spec.json')
        identities={str(p):sha(p) for p in [PACKAGE/'package-manifest.json',BASE/'main-preparation-1.0.0/nested-200-manifest.json',BASE/'main-preparation-1.0.0/nested-400-manifest.json',evidence_path,REPO/'src/simphysqa/main_allocation.py',SOURCE/'main_run.py',SOURCE/'main_preflight.py',SOURCE/'main_verify.py',tests]}
        for shard in SHARDS:
            cid,label=shard.split('--');mapping=next(m for m in evidence['conditions'] if m['condition_id']==cid and m['representation']==label)
            for e in mapping['initial_task_evidence']+mapping['continuation_task_evidence']:
                if sha(e['source'])!=e['sha256']:raise ValueError('mapped actual evidence changed')
            verification=Path(mapping['render_stop_verification'])
            mapping={**mapping,'verification_file_sha256':sha(verification),'reviewed_mapping_sha256':sha(evidence_path)}
            root=Path(mapping['source_root']);bindings=read(root/'bindings'/(shard+'.json'));source=read(root/'qualification'/shard/'qualification.json')
            if digest(bindings)!=mapping['bindings_sha256']:raise ValueError('binding changed')
            put(RUN/'bindings'/(shard+'.json'),bindings);put(RUN/'mappings'/(shard+'.json'),mapping);put(RUN/'source-qualification'/(shard+'.json'),source)
            assignment=ledger.issue('Ashraf',[shard]);put(RUN/'assignments'/(shard+'.json'),assignment)
        # Preserve all scientific package/preparation/development bytes. New ledger
        # is the sole central authority; no model outputs are copied into it.
        preserved={}
        for name in ('execution-public-1.1.1','main-preparation-1.0.0','development-rehearsal-1.0.3','awq-supplement-1.0.0'):
            for p in (BASE/name).rglob('*'):
                if p.is_file():preserved[str(p)]=sha(p)
        put(RUN/'preservation-before.json',preserved)
        put(RUN/'execution-freeze.json',{'version':'SPQ06-Ashraf-main/1.0.0','base_commit':'8c901ee7fb10fd589ef14dae52fcdfb535dc017f','scope':'main','shards':SHARDS,'selected_items':200,'initial_calls':1600,'maximum_continuations':320,'maximum_calls':1920,
            'central_ledger':str(ledger.path),'allocations_seconds':{'Ashraf':72000,'Collaborator':100800},'shared_ceiling_seconds':172800,'identities':identities,
            'batch_rule':'explicit shard order; preserved assignment key order; initial batches <=50, conditional batches <=40; shrink to fit remaining reservation budget without changing stage allowances; no retry of any reserved key',
            'first_batch':'first <=50 qwen3_8b_direct enriched initials; actual immutable import/token/render/measurement/private central scoring join verified before further scientific issue; accuracy is not a gate',
            'accounting':'main preparation/control work, outer metadata, job preparation, adapter preflight/loading/stages/teardown, outer dispatcher gap and central processing counted once; queue/transfer wait and implementation engineering excluded; unknown bound retained',
            'unchanged_science':True,'collaborator_inference_authorized':False,'source_files':adapter.files(SOURCE)})
        put(CENTRAL/'allocation-freeze.json',ledger.summary())
        ledger.settle_control(control,time.monotonic()-started)
        put(RUN/'preparation-accounting.json',{'id':control,'seconds':time.monotonic()-started,'summary':ledger.summary()})
        print('frozen',ledger.summary(),flush=True)
    except BaseException:
        ledger.settle_control(control,time.monotonic()-started,'unknown');raise
    finally:ledger.db.close()

def central_verify(ledger,keys,output):
    from simphysqa.spq06 import parse_answer
    from simphysqa.main_analysis import assess
    from simphysqa.heldout_scope import formal_scope
    plan=read(BASE/'main-run-preflight-1.0.0/main-run-plan.json');scope=plan['generation_candidate_scope'];actual=adapter.canonical_records(ledger);checks=[]
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
    if (RUN/'QUEUE-PAUSED.json').exists():raise ValueError('preserved queue pause; no automatic unblock')
    freeze=read(RUN/'execution-freeze.json')
    for file,expected in freeze['identities'].items():
        if sha(file)!=expected:raise ValueError('execution freeze changed '+file)
    ledger=main_allocation.Ledger(CENTRAL/'main.sqlite');spec=read(PACKAGE/'execution-spec.json')
    first_pass=(RUN/'first-main-batch-integrity.json').exists()
    try:
        for shard in SHARDS:
            cid,label=shard.split('--');assignment=read(RUN/'assignments'/(shard+'.json'));bindings=read(RUN/'bindings'/(shard+'.json'))
            condition=read(PACKAGE/spec['conditions'][cid]['path']);allowance=condition['settings']['max_seconds']
            for stage in (1,2):
                while True:
                    keys=[k for k in ledger.pending(assignment['id'],'Ashraf') if k.endswith('|'+str(stage))]
                    if not keys:break
                    # Hold central verification600 and preflight/loading600 in addition
                    # to unchanged stage bounds. Work already ended settles measured.
                    count=min(50 if stage==1 else 40,len(keys),math.floor((ledger.remaining('Ashraf')-1200)/allowance))
                    if count<=0:raise RuntimeError('allocation prevents another bounded process; no allowance increase')
                    keys=keys[:count];sequence=ledger.db.execute('SELECT COUNT(*) FROM processes').fetchone()[0]+1
                    name=f'{sequence:03d}--{shard}--stage{stage}';keys_path=RUN/'key-batches'/(name+'.json');put(keys_path,keys)
                    process=None;prepared=False;metadata_start=time.monotonic()
                    try:
                        ticket=queue.reserve_overhead(ledger,assignment['id'],'Ashraf',cid,label);process=ticket['id'];put(RUN/'preflight-processes'/(name+'.json'),ticket)
                        qualification_path=RUN/'qualification'/(shard+'.json');adopt=not qualification_path.exists()
                        source=RUN/'source-qualification'/(shard+'.json') if adopt else qualification_path
                        out=RUN/'preflights'/name
                        args=['--package',linux(PACKAGE),'--bindings',linux(RUN/'bindings'/(shard+'.json')),'--qualification',linux(source),'--mapping',linux(RUN/'mappings'/(shard+'.json')),'--keys',linux(keys_path),'--routes',linux(RUN/'routes'/shard),'--output',linux(out)]
                        if adopt:args.append('--adopt')
                        command(wsl(bindings,SOURCE/'main_preflight.py',args),RUN/(name+'-preflight.log'))
                        proof=read(out/'proof.json');qual=read(out/'qualification.json')
                        if adopt:
                            qh=ledger.approve_qualification(qual);put(qualification_path,qual);put(RUN/'qualification'/(shard+'-approved.json'),{'qualification_sha256':qh})
                        else:qh=digest(qual)
                        proof['accounted_preflight_seconds']=time.monotonic()-metadata_start;put(out/'accounted-proof.json',proof)
                        job=RUN/'jobs'/name
                        queue.prepare_job(ledger,assignment['id'],'Ashraf',qh,keys,bindings,job,proof,process);prepared=True
                        outer=command(wsl(bindings,PACKAGE/'procedures/public_executor.py',['launch','--package',linux(PACKAGE),'--job',linux(job),'--authorize-main']),RUN/(name+'-adapter.log'))
                        receipt=read(job/'process-receipt.json');preparation=read(job/'launch.json')['preparation_elapsed_seconds']
                        gap=max(0,outer-(receipt['elapsed_seconds']-preparation));ledger.add_dispatcher_gap(process,gap,{'outer_seconds':outer,'adapter_receipt_sha256':sha(job/'process-receipt.json'),'formula':'outer launch command minus adapter interval, excluding preparation already counted inside receipt'})
                        control=ledger.reserve_control('Ashraf','immutable return/import, actual token checks, central parse/score joins and routing: '+name,600);central_start=time.monotonic()
                        try:
                            returned=RUN/'returns'/name;adapter.export_return(job,returned)
                            imported=queue.import_return(ledger,returned,RUN/'immutable-imports');put(RUN/'import-receipts'/(name+'.json'),imported)
                            if imported['validation_failures'] or len(imported['accepted_keys'])!=len(keys) or imported['conflicts']:raise RuntimeError('main import integrity failure; preserved return requires review')
                            command(wsl(bindings,SOURCE/'main_verify.py',['--package',linux(PACKAGE),'--job',linux(job),'--preflight',linux(out/'render-verification.json'),'--output',linux(RUN/'verification'/(name+'.json'))]),RUN/(name+'-verify.log'))
                            central_verify(ledger,keys,RUN/'central-stage-records'/(name+'.json'))
                            if stage==1:
                                for key in keys:
                                    item=next(i for i in spec['items'] if i['sample_id']==key.split('|')[0])
                                    if item['family']=='clarification':adapter.coordinate_reply(ledger,key,BASE/'main-preparation-1.0.0',RUN/'routes'/shard/(item['sample_id']+'.json'))
                            if not first_pass:
                                put(RUN/'first-main-batch-integrity.json',{'passed':True,'name':name,'initials':len(keys),'import_receipt_sha256':sha(RUN/'import-receipts'/(name+'.json')),'actual_token_checks_sha256':sha(RUN/'verification'/(name+'.json')),'central_scoring_join_sha256':sha(RUN/'central-stage-records'/(name+'.json')),'main_scope':True,'accuracy_not_gate':True});first_pass=True
                            ledger.settle_control(control,time.monotonic()-central_start)
                        except BaseException:
                            ledger.settle_control(control,time.monotonic()-central_start,'unknown');raise
                        print(name,'imported',len(keys),'main accounted',round(ledger.used(),3),'Ashraf remaining',round(ledger.remaining('Ashraf'),3),flush=True)
                        put(RUN/'accounting-snapshots'/(name+'.json'),ledger.summary())
                        if first_only:return
                    except BaseException as exc:
                        if process and not prepared:
                            queue.block_startup(ledger,assignment['id'],'Ashraf',cid,process,str(exc),time.monotonic()-metadata_start if not isinstance(exc,KeyboardInterrupt) else None)
                        put(RUN/'QUEUE-PAUSED.json',{'scope':'main','shard':shard,'process':process,'scientific_reserved':prepared,'reason':type(exc).__name__+': '+str(exc),'traceback':traceback.format_exc(),'accounting':ledger.summary(),'policy':'preserve failures; no automatic unblock/retry/orphan release'});raise
        put(RUN/'execution-completion.json',{'initial_reservations':ledger.db.execute("SELECT COUNT(*) FROM stages WHERE key LIKE '%|1'").fetchone()[0],'conditional_reservations':ledger.db.execute("SELECT COUNT(*) FROM stages WHERE key LIKE '%|2'").fetchone()[0],'routes':ledger.db.execute('SELECT COUNT(*) FROM routes').fetchone()[0],'accounting':ledger.summary(),'collaborator_runs':0})
    finally:ledger.db.close()

if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('command',choices=('prepare','first','run'));a=p.parse_args()
    if a.command=='prepare':prepare()
    else:run(a.command=='first')
