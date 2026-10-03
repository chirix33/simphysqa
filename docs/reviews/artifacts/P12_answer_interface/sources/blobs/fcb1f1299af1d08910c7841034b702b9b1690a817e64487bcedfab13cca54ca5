"""Bounded validation-only compact interface run. Never launches the expanded study."""
from p12_common import ROOT, OUT, NATIVE, load, save, catalog
from phi_jepa.artifacts import digest, canonical
from phi_jepa.integration.readers import file_hash
from phi_jepa.integration.contracts import PublicProblem
from pathlib import Path
import argparse
import json
import time
import shutil
import subprocess
from collections import Counter
from dataclasses import asdict
from importlib.metadata import version

RUN = NATIVE / 'p12-answer-interface-01'
DEST = ROOT / 'docs/reviews/artifacts/P12_answer_interface'
ASSET = ROOT / 'docs/assets/p12_compact_answer_v1.json'
LOCK = ROOT / 'configs/local_answers_p12.lock.json'
CONDITIONS = ('qwen3_8b_direct', 'qwen3_8b_thinking', 'llama31_8b_direct')


def sources():
    paths = [*ROOT.glob('src/phi_jepa/**/*.py'), ROOT/'tools/p12_common.py',
             ROOT/'tools/p10_common.py', Path(__file__), ROOT/'tests/test_p12_answer_interface.py',
             ASSET, LOCK, ROOT/'configs/p12_answer_interface_dependencies.lock.txt']
    return {str(p.relative_to(ROOT)): file_hash(p) for p in paths}


def prepare():
    if (RUN/'config.json').exists():
        checked_config(); print('Existing preparation verified; no calls.'); return
    rows = load(OUT/'diagnostic-public.json')
    if len(rows) != 8 or len({r['sample_id'] for r in rows}) != 8 or any(r['split'] != 'validation' for r in rows):
        raise ValueError('exact eight validation cases required')
    if Counter(r['domain'] for r in rows) != {d: 2 for d in ('driving', 'object_pushing_stacking', 'robotic_arm', 'tethered_load')}:
        raise ValueError('two cases per domain required')
    files = sources()
    cfg = {'version': 'p12-answer-interface-debug-v1', 'authorization': 'User: two rounds, 48 total attempts, two-hour model-run window, validation only, no paid calls.',
           'maximum_attempts': 48, 'maximum_rounds': 2, 'model_window_seconds': 7200,
           'paid_api_calls': 0, 'full_study_enabled': False, 'conditions': list(CONDITIONS),
           'selection_sha256': file_hash(OUT/'diagnostic-public.json'), 'model_lock_sha256': file_hash(LOCK),
           'asset_sha256': file_hash(ASSET), 'commit': subprocess.check_output(['git','rev-parse','HEAD'],cwd=ROOT,text=True).strip(),
           'source_files': files, 'source_sha256': digest(files),
           'runtime': {k: version(k) for k in ('torch','transformers','tokenizers','safetensors','xgrammar')},
           'dependency_lock_sha256': file_hash(ROOT/'configs/p12_answer_interface_dependencies.lock.txt')}
    save(RUN/'config.json', cfg)
    shutil.copyfile(OUT/'diagnostic-public.json', RUN/'diagnostic-public.json')
    shutil.copyfile(LOCK, RUN/'historical-model.lock.json')
    shutil.copyfile(ASSET, RUN/'prompt.json')
    for rel, sha in files.items():
        dest = RUN/'sources/blobs'/sha; dest.parent.mkdir(parents=True, exist_ok=True)
        shutil.copyfile(ROOT/rel, dest)
    save(RUN/'sources/identity.json', {'commit': cfg['commit'], 'files': files, 'sha256': digest(files)})
    save(RUN/'budget.json', {'maximum_attempts': 48, 'started_unix': None, 'deadline_unix': None, 'attempts': []})
    print({'prepared': str(RUN), 'public_validation_questions': len(rows), 'source': cfg['source_sha256']})


def checked_config():
    cfg = load(RUN/'config.json')
    if file_hash(RUN/'diagnostic-public.json') != cfg['selection_sha256'] or file_hash(LOCK) != cfg['model_lock_sha256']:
        raise ValueError('frozen public cohort/model lock changed')
    active = load(RUN/'active-round.json') if (RUN/'active-round.json').exists() else {'round':1}
    if active['round'] == 2:
        correction = load(RUN/'round-2/config.json')
        cfg.update(source_files=correction['source_files'], source_sha256=correction['source_sha256'])
    cfg['round'] = active['round']
    if sources() != cfg['source_files']:
        raise ValueError('source changed: preserve this round and explicitly register a defect correction before another round')
    for k, v in cfg['runtime'].items():
        if version(k) != v: raise ValueError('runtime changed: ' + k)
    return cfg


def register_correction():
    """One explicit interface-defect correction; original clock/attempts remain intact."""
    if (RUN/'active-round.json').exists():
        checked_config(); print('Second round already registered; budget unchanged.'); return
    ledger = load(RUN/'budget.json')
    if time.time() >= ledger['deadline_unix']: raise ValueError('original model window expired')
    failures = list((RUN/'round-1/qwen3_8b_direct').glob('*.json'))
    evidence = {str(p.relative_to(RUN)):file_hash(p) for p in failures
                if load(p).get('failure_detail') == 'Failed to find C compiler. Please specify via CC environment variable.'}
    if not evidence: raise ValueError('specific decoder defect evidence required')
    files = sources()
    record = {'round':2,'defect':'XGrammar CUDA mask invokes Triton compilation; WSL lacks a C compiler.',
        'correction':'Use XGrammar CPU mask kernel; copy logits back to original device, include transfer overhead. Prompt/settings unchanged.',
        'evidence':evidence,'source_files':files,'source_sha256':digest(files),
        'registered_unix':time.time(),'budget_before':ledger,'prompt_unchanged':file_hash(ASSET)==load(RUN/'config.json')['asset_sha256']}
    if not record['prompt_unchanged']: raise ValueError('this correction may not change the prompt')
    save(RUN/'round-2/config.json',record)
    for rel,sha in files.items():
        path=RUN/'sources/blobs'/sha
        if not path.exists():shutil.copyfile(ROOT/rel,path)
    save(RUN/'active-round.json',{'round':2,'config_sha256':file_hash(RUN/'round-2/config.json')})
    print({'round':2,'prior_attempts_retained':len(ledger['attempts']),'deadline_unix':ledger['deadline_unix']})


def settings_and_tokenizer(condition):
    from transformers import AutoTokenizer
    from phi_jepa.providers.local_answer import LocalAnswerSettings
    entry = load(LOCK)[condition]
    data = dict(entry['qualified_settings']); data['runtime'] = tuple(tuple(x) for x in data['runtime'])
    settings = LocalAnswerSettings(**data)
    for package, expected in settings.runtime:
        if version(package) != expected: raise ValueError('pinned runtime mismatch ' + package)
    tokenizer = AutoTokenizer.from_pretrained(settings.model, revision=settings.tokenizer_revision,
        cache_dir=str(NATIVE/'model-cache'), local_files_only=True, trust_remote_code=False)
    return settings, tokenizer


def preflight():
    import xgrammar as xgr
    from transformers import AutoConfig
    from phi_jepa.providers.constrained_local import prepare_request
    from phi_jepa.providers.compact_answer import adapt_answer, value_schema
    from p10_common import guard_deployment_io
    guard_deployment_io(); cfg = checked_config(); rows = load(RUN/'diagnostic-public.json')
    report = {}
    for condition in CONDITIONS:
        settings, tokenizer = settings_and_tokenizer(condition)
        model_cfg = AutoConfig.from_pretrained(settings.model, revision=settings.revision,
            cache_dir=str(NATIVE/'model-cache'), local_files_only=True, trust_remote_code=False)
        info = xgr.TokenizerInfo.from_huggingface(tokenizer, vocab_size=model_cfg.vocab_size,
            stop_token_ids=tokenizer.eos_token_id)
        compiler = xgr.GrammarCompiler(info); records = []
        for row in rows:
            p = PublicProblem.parse(row['public'])
            request = prepare_request(tokenizer, p, load(ASSET)['prompt'], settings)
            compiled = compiler.compile_json_schema(request['schema'])
            # Dummy outputs test real tokenizer/grammar compatibility, never model performance.
            sample = {}
            for s in p.input['answer_spec']:
                schema = value_schema(p, s)
                value = False if s['answer_type'] == 'boolean' else ([0.]*schema['minItems'] if s['answer_type']=='vector' else 0.)
                sample[s['target_id']] = {'status':'supported','value':value,'reason':None}
            text = json.dumps(sample)
            matcher = xgr.GrammarMatcher(compiled)
            accepted = all(matcher.accept_token(t) for t in tokenizer.encode(text, add_special_tokens=False))
            if not accepted or not matcher.accept_token(tokenizer.eos_token_id):
                raise ValueError('real tokenizer cannot complete valid schema example')
            adapt_answer(p, text)
            path = RUN/f"round-{cfg['round']}"/condition/'requests'/(p.sample_id+'.json')
            save(path, request)
            records.append({'sample_id':p.sample_id,'input_tokens':len(request['input_token_ids']),
                            'request_sha256':digest(request),'real_tokenizer_grammar_check':True})
        report[condition] = {'settings':asdict(settings),'rows':records,'template':tokenizer.chat_template}
    save(RUN/f"round-{cfg['round']}"/'preflight.json', {'source_sha256':cfg['source_sha256'],'conditions':report,'model_calls':0})
    print({c: len(v['rows']) for c,v in report.items()})


def reserve_attempt(ledger, condition, sid, request_sha, now, max_seconds, round_number=1):
    if ledger['started_unix'] is None:
        raise ValueError('model window must start before loading')
    if round_number not in (1, 2): raise ValueError('two rounds maximum')
    if len(ledger['attempts']) >= 48: raise ValueError('attempt cap exhausted')
    if now + max_seconds > ledger['deadline_unix']: raise ValueError('model window exhausted')
    key = f'{round_number}:{condition}:{sid}'
    if any(a['key'] == key for a in ledger['attempts']):
        raise ValueError('attempt already counted; no automatic retry or reset')
    entry = {'key':key,'round':round_number,'condition':condition,'sample_id':sid,
             'request_sha256':request_sha,'started_unix':now,'status':'reserved'}
    ledger['attempts'].append(entry)
    return entry


def generate(condition):
    import fcntl
    import torch
    from transformers import AutoModelForCausalLM
    from phi_jepa.providers.constrained_local import ConstrainedLocalBackend
    from p10_common import guard_deployment_io
    guard_deployment_io(); cfg = checked_config()
    lock_handle = (RUN/'worker.lock').open('a')
    fcntl.flock(lock_handle, fcntl.LOCK_EX | fcntl.LOCK_NB)
    torch.set_num_threads(2)
    flight = load(RUN/f"round-{cfg['round']}"/'preflight.json')
    if flight['source_sha256'] != cfg['source_sha256']: raise ValueError('preflight stale')
    rows = load(RUN/'diagnostic-public.json'); folder = RUN/f"round-{cfg['round']}"/condition
    pending = []
    ledger = load(RUN/'budget.json')
    for row, pre in zip(rows, flight['conditions'][condition]['rows']):
        path = folder/(row['sample_id']+'.json')
        request = load(folder/'requests'/(row['sample_id']+'.json'))
        if digest(request) != pre['request_sha256']: raise ValueError('request changed')
        if path.exists():
            result = load(path)
            if result['request_sha256'] != pre['request_sha256']: raise ValueError('cache changed')
            continue
        key = f"{cfg['round']}:{condition}:{row['sample_id']}"
        if any(a['key'] == key for a in ledger['attempts']):
            print('Unresolved prior attempt retained, not retried: ' + key); continue
        pending.append((row, request))
    if not pending: print('No pending requests; zero model calls.'); return
    # Serialize with any independently active model/embedding worker.
    processes = subprocess.check_output(['nvidia-smi','--query-compute-apps=pid,process_name,used_memory','--format=csv,noheader'],text=True).strip()
    if processes: raise ValueError('GPU busy; serialize after existing worker: ' + processes)
    if ledger['started_unix'] is None:
        ledger.update(started_unix=time.time(), deadline_unix=time.time()+cfg['model_window_seconds'])
        save(RUN/'budget.json', ledger)
    if time.time()+120 > ledger['deadline_unix']: raise ValueError('original model window expired')
    settings, tokenizer = settings_and_tokenizer(condition)
    start = time.perf_counter()
    model = AutoModelForCausalLM.from_pretrained(settings.model, revision=settings.revision,
        cache_dir=str(NATIVE/'model-cache'),local_files_only=True,trust_remote_code=False,
        use_safetensors=True,torch_dtype=torch.bfloat16,attn_implementation='sdpa').to('cuda')
    backend = ConstrainedLocalBackend(model, tokenizer, settings, load(ASSET)['prompt'])
    save(folder/'runtime.json', {'settings':asdict(settings),'load_and_backend_seconds':time.perf_counter()-start,
        'compiler_setup_seconds':backend.compiler_setup_seconds,'source_sha256':cfg['source_sha256'],
        'gpu':torch.cuda.get_device_name(),'cuda':torch.version.cuda,'model_generation_config':model.generation_config.to_dict()})
    for row, request in pending:
        entry = reserve_attempt(ledger,condition,row['sample_id'],digest(request),time.time(),settings.max_seconds,cfg['round'])
        save(RUN/'budget.json',ledger)  # durable reservation BEFORE compilation/generate
        result = backend.answer(PublicProblem.parse(row['public']), request)
        result.update(condition=condition,domain=row['domain'],split='validation',scenario_id=row['scenario_id'],
                      source_sha256=cfg['source_sha256'],round=cfg['round'])
        save(folder/(row['sample_id']+'.json'),result)
        entry.update(status='finished',finished_unix=time.time(),result_status=result['status'],latency_seconds=result['latency_seconds'])
        save(RUN/'budget.json',ledger)
        print(json.dumps({k:result.get(k) for k in ('condition','sample_id','status','failure','latency_seconds','output_tokens','reasoning_tokens')}),flush=True)


def evaluate():
    """References are opened only in this independently invoked evaluator."""
    from phi_jepa.typed_evaluation import evaluate_targets
    from phi_jepa.inference.readout import BINDING
    from p12_evaluate import summarize
    round_number = load(RUN/'active-round.json')['round'] if (RUN/'active-round.json').exists() else 1
    rows = load(RUN/'diagnostic-public.json')
    if len(rows) != 8 or any(r['split'] != 'validation' for r in rows): raise ValueError('validation only')
    cat = catalog(); refs = {}; summary = {}
    for domain in sorted({r['domain'] for r in rows}):
        ids = {r['sample_id'] for r in rows if r['domain']==domain}
        refs.update({p.sample_id:ref for p,ref,_ in cat.records(domain,'validation') if p.sample_id in ids})
    for condition in (*CONDITIONS, 'hold_last'):
        records = []; costs = []; repetition = []; abstentions = 0
        for row in rows:
            p = PublicProblem.parse(row['public']); sid=p.sample_id; observed=p.input['states'][-1]['measurements']
            hold = []
            for s in p.input['answer_spec']:
                values=[m['value'] for m in observed if (m['entity_id'],m['name'],m['unit'],m['frame'])==(s['entity_id'],s['quantity'],s['unit'],s['frame'])]
                hold.append({**{k:s[k] for k in BINDING},'status':'supported' if len(values)==1 else 'unsupported',
                             'value':values[0] if len(values)==1 else None,'reason':None if len(values)==1 else 'no observed channel'})
            if condition=='hold_last':
                result={'answer':{'targets':hold},'status':'deterministic_control','full_contract_valid':True}
            else:
                path=RUN/f'round-{round_number}'/condition/(sid+'.json')
                result=load(path) if path.exists() else {'answer':None,'status':'not_completed','failure':'missing_or_interrupted_attempt'}
            answer=result['answer']; predictions=answer['targets'] if answer else []
            ev=evaluate_targets(p,refs[sid],predictions,method=condition,failure=None if answer else result.get('failure',result['status']))
            specs={s['target_id']:s for s in p.input['answer_spec']}
            for t in ev['targets']: t['quantity']=specs[t['target_id']]['quantity']
            ev.update(domain=row['domain'],distribution=row['distribution'],scenario_id=row['scenario_id'],
                      typed_output_valid=answer is not None,generation_failure=result.get('failure'))
            records.append(ev); costs.append({k:v for k,v in result.items() if k not in ('answer','identity','raw_completion','reasoning','final_text','generated_token_ids','reasoning_token_ids','final_token_ids')})
            for pred in predictions:
                if pred['status']=='unsupported': abstentions+=1; continue
                s=specs[pred['target_id']]
                matches=[]
                for state in p.input['states']:
                    for m in state['measurements']:
                        if (m['entity_id'],m['name'],m['unit'],m['frame'])==(s['entity_id'],s['quantity'],s['unit'],s['frame']) and m['value']==pred['value']:
                            matches.append(state['timestamp'])
                h=next(t for t in hold if t['target_id']==pred['target_id'])
                repetition.append({'sample_id':sid,'target_id':pred['target_id'],'answer_type':s['answer_type'],
                    'matches_any_observed':bool(matches),'matching_times':matches,
                    'matches_hold_last':h['status']=='supported' and h['value']==pred['value']})
        metrics=summarize(records); targets=[t for r in records for t in r['targets']]
        numeric=[t for t in targets if t['answer_type']!='boolean']; booleans=[t for t in targets if t['answer_type']=='boolean']
        ledger=load(RUN/'budget.json')
        requests=[a for a in ledger['attempts'] if a['condition']==condition and a['round']==round_number]
        latencies=[c['latency_seconds'] for c in costs if 'latency_seconds' in c]
        sr={'round':round_number,'requests_attempted':len(requests),
            'cumulative_attempts':sum(a['condition']==condition for a in ledger['attempts']),
            'requests_completed':sum(c.get('EOS_terminated',False) for c in costs),
            'syntax_valid':sum(c.get('syntax_valid',False) for c in costs),'full_contract_valid':sum(c.get('full_contract_valid',False) for c in costs),
            'complete_correct':sum(r['complete_success'] for r in records),'questions':len(rows),
            'supported_targets':metrics['supported_targets'],'eligible_targets':len(targets),'abstentions':abstentions,
            'abstention_rate_all_targets':abstentions/len(targets),
            'numeric_correct':sum(t['success'] for t in numeric),'numeric_eligible':len(numeric),'numeric_evaluated':sum(t['status']=='valid' for t in numeric),
            'boolean_correct':sum(t['success'] for t in booleans),'boolean_eligible':len(booleans),'boolean_evaluated':sum(t['status']=='valid' for t in booleans),
            'numeric_exact_any_observed':sum(t['matches_any_observed'] for t in repetition if t['answer_type']!='boolean'),
            'numeric_exact_hold_last':sum(t['matches_hold_last'] for t in repetition if t['answer_type']!='boolean'),
            'boolean_exact_hold_last':sum(t['matches_hold_last'] for t in repetition if t['answer_type']=='boolean'),
            'generation_seconds':sum(latencies),'latency_min':min(latencies) if latencies else None,'latency_max':max(latencies) if latencies else None,
            'peak_allocated_bytes':max((c.get('peak_allocated_bytes',0) for c in costs),default=0),
            'peak_reserved_bytes':max((c.get('peak_reserved_bytes',0) for c in costs),default=0),
            'constraint_compile_seconds':sum(c.get('constraint_compile_seconds',0) for c in costs),
            'constraint_processing_seconds':sum(c.get('constraint_processing',{}).get('seconds',0) for c in costs),
            'token_caps':sum(c.get('token_cap_termination',False) for c in costs),'time_caps':sum(c.get('time_cap_termination',False) for c in costs),
            'runtime_failures':sum(c.get('status')=='runtime_failure' for c in costs),
            'failures':dict(Counter(c.get('failure') for c in costs if c.get('failure'))),
            'reasoning_tokens':sum(c.get('reasoning_tokens',0) for c in costs),'final_tokens':sum(c.get('final_answer_tokens',0) for c in costs),
            'retries':0,'repairs':0}
        if latencies:
            import statistics
            sr['latency_median']=statistics.median(latencies)
        save(RUN/'evaluation'/f'{condition}.json',{'summary':sr,'metrics':metrics,'records':records,'cost':costs,'repetition':repetition})
        summary[condition]=sr
    save(RUN/'evaluation/summary.json',summary);print(json.dumps(summary,indent=2))


def export():
    DEST.mkdir(parents=True,exist_ok=True)
    for path in RUN.rglob('*'):
        if path.is_file() and path.name!='worker.lock':
            dest=DEST/path.relative_to(RUN);dest.parent.mkdir(parents=True,exist_ok=True);shutil.copyfile(path,dest)
    save(DEST/'artifact-index.json',{str(p.relative_to(DEST)):file_hash(p) for p in DEST.rglob('*') if p.is_file() and p.name!='artifact-index.json'})
    print('Exported to '+str(DEST))


if __name__=='__main__':
    parser=argparse.ArgumentParser();parser.add_argument('stage',choices=['prepare','preflight','generate','evaluate','export','register_correction'])
    parser.add_argument('--condition',choices=CONDITIONS);args=parser.parse_args()
    if args.stage=='generate':
        if not args.condition:parser.error('--condition is required')
        generate(args.condition)
    else: globals()[args.stage]()
