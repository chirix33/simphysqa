"""Authorized central reconciliation, routing and prospective issuance, CPU only."""
import collections
import hashlib
import json
import shutil
import time
import zipfile
from datetime import datetime, timezone
from pathlib import Path, PurePosixPath

from simphysqa import execution_adapter as a, main_record_index as index, native_reconciliation as n

ROOT = Path(__file__).resolve().parent
REPO = Path('C:/Users/aashraf/.codex/worktrees/simphysqa/phi-jepa')
BASE = Path('C:/Users/aashraf/.codex/visualizations/2026/10/06/01a1131b-eac2-7a31-afb4-f219a8dd6471/spq06/2026-10-09')
SOURCE = Path('C:/Users/aashraf/Desktop/Work/phi-jepa/NAACL Paper/SimPhysQA-records-600_more_metadata.zip')
RAW = SOURCE.with_name('SimPhysQA-results-600.zip')
OUT = ROOT/'collaborator-issued-1.0.0'
PUBLIC = OUT/'public'
REMOTE = '/mnt/c/Users/mmujawar/VisualStudioCode/SimPhys/handoff/clarification-stage2-1.0.0'
HOST = '/mnt/c/Users/mmujawar/VisualStudioCode/SimPhys'
CUTOFF = '2026-10-13T02:00:00+00:00'
AUTH_TEXT = """I authorize a documented reconciliation of the verified independently executed first turns. Preserve their original local provenance and accounting; do not manufacture historical central tickets or approvals. Keep the existing budgets unchanged.
Finish preparing and issuing the two supported second-turn jobs, using the recorded replies, verbatim first responses and actual collaborator interpreter paths. Keep the frozen parser, prompts, settings and scoring unchanged. Arrange any required fresh metadata-only preflight on his workstation. Deliver one public runnable handoff with exact execution and complete-return export commands. Do not rerun first turns or launch answering on my workstation."""


def protect_snapshot(ledger):
    tables=['assignments','ownership','qualifications','processes','stages','routes','returns','transports','control_work','dispatcher_gaps',
            'executor_allocations','budget_revision_events','complement_stages','complement_returns','complement_routes',
            'restart_stages','restart_returns','restart_routes']
    snapshot={}
    for table in tables:
        if n.exists(ledger,table):
            snapshot[table]=set(tuple(r) for r in ledger.db.execute('SELECT * FROM '+table))
    return snapshot


def build():
    OUT.mkdir(exist_ok=False);PUBLIC.mkdir()
    ledger=index.Ledger(BASE/'central-main-1.0.0/main.sqlite')
    before=protect_snapshot(ledger);before_budget=n.budgets(ledger);before_summary=ledger.summary()
    a.put(OUT/'preserved-ledger-rows-before.json',{t:sorted(list(rows),key=str) for t,rows in before.items()})
    assert before_budget=={'allocations':{'Ashraf':126000.0,'Collaborator':100800.0},'shared':226800.0}
    control=None;started=time.monotonic()
    try:
        authorization={'version':n.VERSION,'explicit_human_native_reconciliation':True,'authorization_text':AUTH_TEXT,
                       'recorded_utc':datetime.now(timezone.utc).isoformat(),'native_archive_sha256':a.sha(SOURCE),
                       'original_raw_archive_sha256':a.sha(RAW),'unchanged_budgets':before_budget,
                       'ceiling_waiver_adopted':False,'historical_central_approval_synthesized':False}
        a.put(OUT/'actual-user-authorization.json',authorization)
        control=ledger.reserve_control('Collaborator','authorized native import/routing and public job preparation',1800)
        registry=n.reconcile(ledger,SOURCE,RAW,authorization,OUT/'immutable-native')['registry']
        a.put(OUT/'registry-receipt.json',{'native_archive_sha256':a.sha(SOURCE),'native_first_turns':registry['entries'],
                                        'original_authority':'independent_local','historical_tickets_created':False})
        shutil.copytree(BASE/'execution-public-1.1.1',PUBLIC/'execution-public-1.1.1')
        a.validate_package(PUBLIC/'execution-public-1.1.1')
        shutil.copyfile(REPO/'src/simphysqa/native_remote.py',PUBLIC/'native_remote.py')
        runner_hash=a.sha(PUBLIC/'native_remote.py')
        template=a.read(BASE/'gemma-gguf-metadata-1.0.0.json')['metadata']['tokenizer.chat_template']
        a.put(PUBLIC/'gemma-template.json',template)
        spec=json.loads(ledger.meta('spec'));routes=[]
        def route_all():
            for item in spec['items']:
                if item['family']!='clarification':continue
                for cid in n.CIDS:
                    first=a.stage_key(item['sample_id'],cid,'enriched',1)
                    routes.append(a.coordinate_reply(ledger,first,BASE/'main-preparation-1.0.0',
                                  OUT/'canonical-routes'/cid/(item['sample_id']+'-stage2.json')))
        ledger.transaction(route_all)
        assert len(routes)==120
        supported=[r for r in routes if r['status']=='supported']
        expected=a.read(ROOT/'collaborator-clarification-1.0.0/public/summary.json')['diagnostically_supported']
        assert set(r['key'] for r in supported)==set(expected),'verified raw responses changed eligibility'
        routing_summary={'version':n.VERSION,'native_archive_sha256':a.sha(SOURCE),'routes':len(routes),
                         'counts_by_condition':{cid:dict(collections.Counter(r['status'] for r in routes if r['key'].split('|')[1]==cid)) for cid in n.CIDS},
                         'supported_keys':[r['key'] for r in supported],'resolved_results':'pending',
                         'original_first_turn_authority':'independent_local_preserved','parser_semantic_gate_added':False}
        a.put(PUBLIC/'routing-summary.json',routing_summary)
        for r in routes:
            cid=r['key'].split('|')[1];sid=r['key'].split('|')[0]
            a.put(PUBLIC/'routing-provenance'/cid/(sid+'-stage2.json'),r)
        jobs=[]
        with zipfile.ZipFile(SOURCE) as archive:
            read=lambda name:json.loads(archive.read(name))
            for route in supported:
                cid=route['key'].split('|')[1];name='deepseek' if cid.startswith('deepseek') else 'gemma-cot'
                seed=registry['seed_metadata'][cid];c=seed['condition'];context=seed['context'];pin=spec['conditions'][cid]
                task_root='qualification/'+('deepseek' if cid.startswith('deepseek') else cid)+'-development-001'
                dev_paths=sorted(p for p in archive.namelist() if p.startswith(task_root+'/worker-output/results/') and p.endswith('.json'))
                if len(dev_paths)!=5:raise ValueError('exact five actual native development tasks required')
                dev=[]
                for p in dev_paths:
                    raw=read(p)
                    if raw['completion_status']!='completed' or raw['stage']!=1 or raw['worker_sha256']!=pin['worker_sha256']:
                        raise ValueError('reviewed native development evidence differs from frozen worker')
                    dev.append({'result_file_sha256':hashlib.sha256(archive.read(p)).hexdigest(),
                                'sample_id':raw['sample_id'],'termination':raw['termination'],'stage':1})
                task={'status':'passed','evidence_sha256':a.digest(dev),'initial_tasks':5,'live_continuation_tasks':0,
                      'missing_live_stage2':True,'authority':'central review of actual native initial/development evidence; historical local approvals remain false'}
                stop={'status':'passed','evidence_sha256':a.digest([d['termination'] for d in dev]),
                      'kind':'actual native development termination evidence from unchanged frozen worker; no inferred reasoning or stage2 claim'}
                env={k:v for k,v in seed['launch']['environment_overrides'].items() if k in
                     ('PYTHONDONTWRITEBYTECODE','HF_HUB_OFFLINE','TRANSFORMERS_OFFLINE','VLLM_NO_USAGE_STATS','TOKENIZERS_PARALLELISM','LD_LIBRARY_PATH')}
                env.update(PYTHONDONTWRITEBYTECODE='1',HF_HUB_OFFLINE='1',TRANSFORMERS_OFFLINE='1',VLLM_NO_USAGE_STATS='1')
                artifact=c.get('snapshot_path',c.get('gguf_path'))
                cache=artifact.split('/hub/')[0]
                bindings={'interpreter':c['local_python'],'environment':env,'artifact_cache':cache,
                          'device_uuid':context['device_uuid'],'cuda_visible_devices':seed['launch']['environment_overrides']['CUDA_VISIBLE_DEVICES'],
                          'nvidia_smi':context['nvidia_smi']}
                for field in a.LOCAL_FIELDS-{'local_python'}:
                    if field in c:bindings[field]=c[field]
                if c['backend']=='llama.cpp':bindings['llama_device']=context['llama_device']
                issue=n.issue(ledger,route['key'],OUT/'issued'/name/'issue.json',runner_hash,CUTOFF)
                entry=json.loads(ledger.db.execute('SELECT body FROM native_entries WHERE key=?',(route['initial_key'],)).fetchone()[0])
                job={'version':n.VERSION,'issue':issue,'condition':c,'bindings':bindings,'request':route['request'],
                     'actual_first_response':route['actual_raw'],'hardware_runtime':context['hardware_runtime'],
                     'worker_relative':pin['worker'],'worker_sha256':pin['worker_sha256'],'scientific_condition_sha256':pin['sha256'],
                     'support_sha256':a.sha(PUBLIC/'execution-public-1.1.1/workers/execution_support.py'),
                     'reviewed_task_evidence':task,'reviewed_stop_evidence':stop,
                     'render_example':{'request':read(entry['request']),'render':read(entry['prompt'])},
                     'original_native_archive_sha256':a.sha(SOURCE),
                     'device_lock_path':HOST+'/jobs/clarification-stage2-1.0.0/device.lock',
                     'attempt_guard_path':HOST+'/jobs/clarification-stage2-1.0.0/attempts/'+issue['process']+'.json',
                     'fresh_metadata_status':'required_on_collaborator_before_any_answering',
                     'first_turn_rerun_allowed':False,'meaning_of_task_pass':'execution/format evidence; no accuracy or wording gate'}
                assert a.digest(job['condition'])==context['resolved_condition_sha256']
                assert job['request']['messages'][-2]=={'role':'assistant','content':route['actual_raw']}
                assert job['request']['tools']==[]
                ledger.db.execute('INSERT INTO native_job_payloads VALUES(?,?)',(issue['process'],a.canonical(job).decode()))
                a.put(PUBLIC/'jobs'/name/'job.json',job);a.put(PUBLIC/'jobs'/name/'route.json',route)
                jobs.append({'name':name,'key':issue['key'],'assignment':issue['assignment']['id'],'process':issue['process'],
                             'bound_seconds':issue['bound_seconds'],'interpreter':bindings['interpreter'],'status':issue['status']})
        a.put(PUBLIC/'issued-jobs.json',{'version':n.VERSION,'jobs':jobs,'remote_metadata_complete':False,'answering_calls_here':0})
        for p in PUBLIC.rglob('*.json'):
            if 'execution-public-1.1.1' in p.parts:continue # independently sealed known public base
            def public_only(v):
                if isinstance(v,dict):
                    assert not {'private','private_record','initial_view','resolved_view','verification_record','structured_label','solution_trace','reference','gold_answer','witnesses'}.intersection(v),p
                    for child in v.values():public_only(child)
                elif isinstance(v,list):
                    for child in v:public_only(child)
            public_only(a.read(p))
        readme='''# Issued collaborator clarification jobs — run exactly once

This is the one runnable public handoff for two central prospective stage-2 jobs.
It contains frozen public workers,120 canonical routing receipts and the exact two
supported conversations. Original600 first turns were reconciled as independent
local execution; their approvals/local process identities were not rewritten.
The two NEW jobs are assigned to Collaborator and reserved centrally. They are
issued_pending_remote_metadata until actual on-machine verification permits a
single answer call. No first turns, other conditions or further continuations.

Extract this ZIP once into the new, exact directory below. Do not overwrite an old
folder, edit files, copy jobs to another attempt, reset run folders/host attempt
guards, rerun a completed/failed command or change model/settings/history.

```bash
mkdir /mnt/c/Users/mmujawar/VisualStudioCode/SimPhys/handoff/clarification-stage2-1.0.0
# Extract the received ZIP's contents into that directory; keep its manifest.
```

The pinned original model/artifact/runtime paths are in each jobs/*/job.json.
No model downloads or runtime upgrades are part of this handoff. Both jobs are
serial on the original GPU0/UUID. Fixed host locks/attempt guards survive copied
handoffs; failure retains the attempt and its complete return must be exported.
Do not remove guards or retry metadata/answering with the same issue.

Run DeepSeek once, then export its entire return even if the run reports failure:

```bash
/mnt/c/Users/mmujawar/VisualStudioCode/SimPhys/runtimes/deepseek/bin/python -B /mnt/c/Users/mmujawar/VisualStudioCode/SimPhys/handoff/clarification-stage2-1.0.0/native_remote.py run --handoff /mnt/c/Users/mmujawar/VisualStudioCode/SimPhys/handoff/clarification-stage2-1.0.0 --job deepseek --authorize-stage2
/mnt/c/Users/mmujawar/VisualStudioCode/SimPhys/runtimes/deepseek/bin/python -B /mnt/c/Users/mmujawar/VisualStudioCode/SimPhys/handoff/clarification-stage2-1.0.0/native_remote.py export --handoff /mnt/c/Users/mmujawar/VisualStudioCode/SimPhys/handoff/clarification-stage2-1.0.0 --job deepseek --output /mnt/c/Users/mmujawar/VisualStudioCode/SimPhys/handoff/clarification-stage2-1.0.0/deepseek-stage2-complete-return.zip
```

Run Gemma CoT once, then export its entire return even if it reports failure:

```bash
/mnt/c/Users/mmujawar/VisualStudioCode/SimPhys/runtimes/control/bin/python -B /mnt/c/Users/mmujawar/VisualStudioCode/SimPhys/handoff/clarification-stage2-1.0.0/native_remote.py run --handoff /mnt/c/Users/mmujawar/VisualStudioCode/SimPhys/handoff/clarification-stage2-1.0.0 --job gemma-cot --authorize-stage2
/mnt/c/Users/mmujawar/VisualStudioCode/SimPhys/runtimes/control/bin/python -B /mnt/c/Users/mmujawar/VisualStudioCode/SimPhys/handoff/clarification-stage2-1.0.0/native_remote.py export --handoff /mnt/c/Users/mmujawar/VisualStudioCode/SimPhys/handoff/clarification-stage2-1.0.0 --job gemma-cot --output /mnt/c/Users/mmujawar/VisualStudioCode/SimPhys/handoff/clarification-stage2-1.0.0/gemma-cot-stage2-complete-return.zip
```

The run command performs a fresh METADATA-ONLY phase before the answering worker:
hash pinned artifacts/template/worker/support; verify original hardware/OS/driver,
CUDA numeric-index/UUID and exact backend versions/configuration; reproduce an
actual original saved prompt/token sequence; render the FULL actual conversation
and check input+output capacity. DeepSeek uses frozen0.93 vLLM ModelConfig without
creating an LLM instance. Gemma uses pinned CUDA device listing and CPU GGUF
vocabulary tokenization, with the frozen template and no server/model load in the
metadata phase. Control Python needs jinja2 for that exact template rendering;
DeepSeek's pinned environment needs its existing Transformers/vLLM dependencies.
Missing dependencies or changed artifacts/hardware stop and are exported as failure;
do not install substitutions or alter the evaluated model to force completion.

Only a passed fresh proof (within300s) activates the issued worker. The metadata,
loading, one actual stage and teardown share the process bound:960s DeepSeek,
840s Gemma CoT (600s overhead plus frozen360s/240s answering limits). SIGALRM and
worker deadlines bound the lifecycle; no automatic retry or context truncation.
No changed parser, schema, prompts, selector rules, sampling, precision or scoring.

The actual first assistant response is verbatim, including reasoning. The supplied
user message contains the recorded missing selector and exact public updates;
it contains no answer. Keep those messages unchanged. Gemma CoT's unit-question
wording concern is separately recorded; its declared execution_condition routes
under the unchanged rule. There is no new semantic routing gate or human grade.

If a run exits nonzero but created a runs/<job>/process-receipt.json, export that
failure with the command above and send it. If no run folder/receipt exists (for
example a prior-attempt guard, invalid bundle or expired cutoff refused startup),
send the exact sanitized error and preserve all files; do not manufacture receipts.
If an item has incomplete request/render evidence, preserve the full run folder
and report that export failure rather than rerunning or inventing missing records.

Return BOTH complete-return ZIPs and their printed SHA256s. Each export includes
the issued job/routing, fresh metadata/qualification/activation, exact executed
request/rendered prompt/input IDs/raw output/output IDs/stop events, runtime,
memory/timing and process lifecycle logs/receipt plus the immutable return envelope
and every listed hash. Do not send only the two result JSONs. No credentials or
organizer-private records/gold/verification traces belong in this transfer.

The original budgets remain unchanged: collaborator100800s, Ashraf126000s,
shared226800s. Original native measurements plus explicitly unknown outer bounds
were recorded centrally once; they are not presented as new historical tickets.
The unchanged result-import cutoff is October12,21:00 America/Chicago / October13
02:00UTC. Each job must fit its bound PLUS600s export/central-import reserve before
that cutoff. Transfer promptly; the runner refuses a late start. No ceiling or
calendar extension is granted by this handoff.

Resolved clarification scoring is pending until both supported jobs' returns are
processed centrally. The organizer imports and scores genuine first/second turns
together with unchanged core200 denominators/scorers/bootstrap. No independent
ledger or grading/private-data access is needed on your machine.
'''
        for old,new in {'workers,120':'workers, 120','Original600':'Original 600','frozen0.93':'frozen 0.93',
                        'within300s':'within 300 s','bound:960s':'bound: 960 s','840s':'840 s','600s':'600 s',
                        'frozen360s/240s':'frozen 360 s / 240 s','collaborator100800s':'collaborator 100,800 s',
                        'Ashraf126000s':'Ashraf 126,000 s','shared226800s':'shared 226,800 s',
                        'October12,21:00':'October 12, 21:00','October13':'October 13','02:00UTC':'02:00 UTC',
                        'PLUS600s':'PLUS 600 s','core200':'core 200'}.items():readme=readme.replace(old,new)
        (PUBLIC/'README.md').write_text(readme,encoding='utf-8',newline='\n')
        a.put(PUBLIC/'manifest.json',{'version':n.VERSION,'files':a.files(PUBLIC),'issued_jobs':jobs,
                                   'private_evidence':False,'credentials':False,'answering_calls_here':0})
        destination=ROOT/'SimPhysQA-collaborator-stage2-issued-1.0.0.zip'
        with zipfile.ZipFile(destination,'x',compression=zipfile.ZIP_DEFLATED) as archive:
            for p in sorted(PUBLIC.rglob('*')):
                if p.is_file():archive.write(p,p.relative_to(PUBLIC).as_posix())
        with zipfile.ZipFile(destination) as archive:
            assert archive.testzip() is None
            for name,expected_hash in a.read(PUBLIC/'manifest.json')['files'].items():
                assert hashlib.sha256(archive.read(name)).hexdigest()==expected_hash
        after=protect_snapshot(ledger)
        for table,rows in before.items():assert rows<=after[table], 'historical ledger changed: '+table
        assert before_budget==n.budgets(ledger)
        ledger.settle_control(control,time.monotonic()-started);control=None
        report={'version':n.VERSION,'archive':str(destination),'sha256':a.sha(destination),'jobs':jobs,
                'native_first_turns_accepted':600,'original_first_turn_approvals_preserved_false':True,
                'canonical_routes':len(routes),'supported':len(supported),'unexecuted_conditional':len(routes)-len(supported),
                'before':before_summary,'after':ledger.summary(),'historical_ledger_rows_preserved':True,
                'budgets_unchanged':True,'metadata_validation':'required on collaborator; no fabricated proof',
                'resolved_scores':'pending','answering_calls_here':0,'historical_tickets_created':0}
        a.put(OUT/'completion-receipt.json',report)
        print(a.canonical(report).decode())
    except BaseException:
        if control is not None:ledger.settle_control(control,time.monotonic()-started,'failed')
        raise
    finally:ledger.db.close()


if __name__=='__main__':build()
