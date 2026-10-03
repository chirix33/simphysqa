"""User-requested selected-checkpoint validation replay; no training or providers."""
import sys, json, time, hashlib, math, signal
from pathlib import Path
from dataclasses import asdict

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[3]
sys.path.insert(0, str(ROOT / 'src'))
from phi_jepa.artifacts import canonical, digest
from phi_jepa.integration.readers import ReleaseCatalog, PublicInputReader, file_hash

def load(p): return json.loads(Path(p).read_text())
def write(p, value):
    p = Path(p); p.parent.mkdir(parents=True, exist_ok=True)
    with p.open('xb') as f: f.write(canonical(value))

def budget():
    p = HERE / 'window.json'
    if not p.exists():
        write(p, dict(started_unix=time.time(), deadline_unix=time.time()+1200,
                      wall_seconds_cap=1200, request_cap=1336, paid_calls=0,
                      scope='selected checkpoints; original validation only',
                      script_sha256=file_hash(__file__)))
    w = load(p)
    if w['script_sha256'] != file_hash(__file__): raise ValueError('replay source changed')
    remaining = w['deadline_unix']-time.time()
    if remaining <= 0: raise TimeoutError('replay window expired')
    signal.signal(signal.SIGALRM, lambda *_: (_ for _ in ()).throw(TimeoutError('replay deadline')))
    signal.alarm(math.ceil(remaining))
    return w

def inputs():
    cfg = load(ROOT/'configs/model_training_p02a.json')
    return ReleaseCatalog(ROOT/cfg['export_root'], cfg['export_index_sha256'], cfg['release_manifest_sha256'])

def infer():
    budget()
    def guard(event, args):
        if event.startswith('socket.'): raise RuntimeError('network forbidden')
        if event == 'open' and isinstance(args[0], (str, bytes)):
            s = str(args[0]).replace('\\','/').lower()
            if any(x in s for x in ('references.jsonl','evaluator.jsonl','confirmation','credentials','.env')):
                raise RuntimeError('inference private/network boundary')
    sys.addaudithook(guard)
    import torch
    from phi_jepa.integration.layout import StateLayout
    from phi_jepa.integration.contracts import enriched_context
    from phi_jepa.training.checkpoint import load_checkpoint
    from phi_jepa.inference.rollout import rollout
    from phi_jepa.inference.readout import named_forecast, read_targets
    from phi_jepa.solvers.rk4 import SolveStats
    torch.set_num_threads(2)
    base = ROOT/'docs/reviews/artifacts/P12_training_run'
    proposal = load(base/'execution/approved-plan.json')
    native = Path('/home/aashraf/phi-jepa/p12-expanded-study-seed11')
    covpath = Path(proposal['inputs']['cache_coverage']['path'])
    assert file_hash(covpath) == proposal['inputs']['cache_coverage']['sha256']
    coverage = {r['sample_id']:r for r in load(covpath)}
    cat = inputs(); count=0; started=time.monotonic()
    for domain, settings in proposal['domains'].items():
        src = load(base/'domains'/domain/'execution-source.json')
        for name, sha in src['files'].items():
            if name.startswith('src/') and file_hash(ROOT/name) != sha:
                raise ValueError('frozen source mismatch: '+name)
        selected = load(base/'domains'/domain/'selected.json')
        directory = native/domain/'checkpoints'/str(selected['update'])
        assert load(directory/'latest.json') == selected['checkpoint']
        m = load(ROOT/f'docs/reviews/artifacts/P02a/{domain}.state_plus_fixed_conditioning.json')
        layout = StateLayout.from_manifest(m,digest(m))
        ctx = dict(encoder=proposal['encoder_settings'], mode='enriched', run='p12-expanded-seed11')
        model, solver = load_checkpoint(directory,layout=layout,context_identity=ctx,training=False)
        pubfile = cat.verified_file(domain,'validation','inputs.jsonl')
        expected = {r['sample_id'] for r in load(base/'domains'/domain/'validation'/f"{selected['update']}.json")['records']}
        seen=set()
        for p in PublicInputReader(pubfile,file_hash(pubfile)):
            seen.add(p.sample_id); count+=1
            assert count<=1336 and p.sample_id in expected
            entry=coverage[p.sample_id]
            for kind in ('embedding','enrichment'):
                assert file_hash(entry[kind+'_path'])==entry[kind+'_file_sha256']
            e=load(entry['embedding_path']); notes=load(entry['enrichment_path'])
            assert e['request_sha256']==entry['embedding_request_sha256']
            assert e['context_sha256']==digest(enriched_context(p,notes,p.input['observation_cutoff']))
            identity=dict(sample_id=p.sample_id,public_sha256=digest(p.input),checkpoint=selected['checkpoint'],
                          update=selected['update'],embedding_sha256=entry['embedding_file_sha256'],solver=asdict(solver))
            dest=HERE/'predictions'/domain/(p.sample_id+'.json')
            if dest.exists():
                assert load(dest)['identity']==identity
                continue
            attempt=HERE/'attempts'/domain/(p.sample_id+'.json')
            if attempt.exists(): raise RuntimeError('interrupted request; no automatic retry')
            write(attempt,dict(identity=identity,started_unix=time.time()))
            t0=time.monotonic(); stats=SolveStats()
            record=dict(sample_id=p.sample_id,domain=domain,identity=identity,public=dict(sample_id=p.sample_id,schema_version=p.schema_version,input=p.input))
            try:
                a=p.input['observation_cutoff']; b=max(s['end_time'] for s in p.input['answer_spec'])
                times=[round(a+.02*i,8) for i in range(round((b-a)/.02)+1)]
                trajectory=rollout(model,p,torch.tensor([e['values']],dtype=torch.float32),times,solver,stats)
                named=named_forecast(p,layout,trajectory)
                record.update(status='success',failure=None,answer=read_targets(p,named),trajectory=asdict(trajectory))
            except (ValueError, RuntimeError, OverflowError) as exc:
                record.update(status='failure',failure=type(exc).__name__,answer=[])
            record.update(seconds=time.monotonic()-t0,stats=stats.manifest())
            write(dest,record)
            if count%100==0: print('completed',count,'elapsed',round(time.monotonic()-started,1),flush=True)
        assert seen==expected and len(seen)==settings['validation_questions']
        print(domain,'complete',len(seen),flush=True)
    assert count==1336
    write(HERE/'inference-complete.json',dict(questions=count,seconds=time.monotonic()-started,torch=torch.__version__,threads=2,paid_calls=0))

def report():
    from phi_jepa.integration.contracts import PublicProblem
    from phi_jepa.typed_evaluation import evaluate_targets
    cat=inputs(); data=[]; summaries={}; mismatches=[]; stats={}; predictions=0
    base=ROOT/'docs/reviews/artifacts/P12_training_run/domains'
    for domain in ('driving','robotic_arm','object_pushing_stacking','tethered_load'):
        selected=load(base/domain/'selected.json')
        old={r['sample_id']:r['result'] for r in load(base/domain/'validation'/f"{selected['update']}.json")['records']}
        refs={r['sample_id']:r['reference'] for r in map(json.loads,cat.verified_file(domain,'validation','references.jsonl').read_text().splitlines())}
        domainrows=[]
        for path in sorted((HERE/'predictions'/domain).glob('*.json')):
            pred=load(path); p=PublicProblem.parse(pred['public']); ref=refs[p.sample_id]
            result=evaluate_targets(p,ref,pred['answer'],method='Phi-JEPA numerical/readout',failure=pred['failure'])
            if digest(result)!=digest(old[p.sample_id]): mismatches.append(p.sample_id)
            for k,v in pred['stats'].items(): stats[k]=stats.get(k,0)+v
            predictions+=1
            truths={r['target_id']:r for r in ref['structured_label']}
            answers={r['target_id']:r for r in pred['answer']}
            targets=[]
            for spec,metric in zip(p.input['answer_spec'],result['targets']):
                assert spec['target_id']==metric['target_id']
                targets.append(dict(specification=spec,prediction=answers.get(spec['target_id']),reference=truths[spec['target_id']],evaluation=metric))
            row=dict(sample_id=p.sample_id,domain=domain,checkpoint_update=selected['update'],question=p.input['question'],
                     observation_cutoff=p.input['observation_cutoff'],complete_success=result['complete_success'],
                     targets=targets,public_problem=p.input,prediction_file=str(path.relative_to(HERE)),failure=pred['failure'])
            data.append(row);domainrows.append(row)
        assert len(domainrows)==len(old)
        summaries[domain]=dict(questions=len(domainrows),complete_correct=sum(r['complete_success'] for r in domainrows),selected_update=selected['update'])
    assert predictions==1336
    with (HERE/'questions-predictions-references.jsonl').open('xb') as f:
        for row in data:f.write(canonical(row))
    summary=dict(domains=summaries,questions=predictions,exact_historical_result_matches=predictions-len(mismatches),mismatches=mismatches,
                 solve_stats=stats,inference=load(HERE/'inference-complete.json'),meaning='Validation-only selected models; numerical predictions, not LLM prose; original tolerances unchanged')
    write(HERE/'summary.json',summary)
    page='''<!doctype html><meta charset="utf-8"><title>Today's Phi-JEPA validation answers</title>
<style>body{font:16px system-ui;margin:30px;max-width:1400px}input,select{padding:8px;margin:6px}table{border-collapse:collapse;width:100%}td,th{border:1px solid #ccc;padding:8px;text-align:left;vertical-align:top}pre{white-space:pre-wrap} .bad{color:#a00}.good{color:#075}details{margin:16px 0}small{color:#555}</style>
<h1>Phi-JEPA validation: questions, predictions and reference answers</h1>
<p>Selected checkpoints from the 29 September 2026 training run. Numerical/readout answers; no LLM prose. All original validation questions. Original tolerances. Unsupported answers are retained.</p>
<input id="search" placeholder="Search question or sample ID" size="45"><select id="domain"><option value="">All domains</option></select><select id="status"><option value="">All results</option><option value="pass">Complete correct</option><option value="fail">Incomplete / incorrect</option></select><p id="count"></p><div id="rows"></div>
<script>const data=DATA;
const esc=x=>String(x??'').replace(/[&<>"']/g,c=>({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[c]));
const val=x=>x===undefined?'missing':JSON.stringify(x);
const dom=document.getElementById('domain');[...new Set(data.map(r=>r.domain))].forEach(x=>dom.add(new Option(x,x)));
function render(){const q=document.getElementById('search').value.toLowerCase(),s=document.getElementById('status').value;const found=data.filter(r=>(!dom.value||r.domain===dom.value)&&(!s||(s==='pass')===r.complete_success)&&(r.question+' '+r.sample_id).toLowerCase().includes(q));document.getElementById('count').textContent=found.length+' matching questions; showing first 100. Search by sample ID to locate any record.';
document.getElementById('rows').innerHTML=found.slice(0,100).map(r=>`<details><summary><b>${esc(r.domain)}</b> · ${esc(r.sample_id)} · ${r.complete_success?'PASS':'FAIL'}<br>${esc(r.question)}</summary><p>Checkpoint update ${r.checkpoint_update}; observed through ${r.observation_cutoff}s.</p><table><tr><th>Target / time / unit</th><th>Model prediction</th><th>Reference answer</th><th>Error / tolerance</th><th>Result</th></tr>${r.targets.map(t=>`<tr><td>${esc(t.specification.target_id)}<br>${t.specification.end_time}s · ${esc(t.specification.unit)}</td><td>${esc(val(t.prediction?.value))}</td><td>${esc(val(t.reference.value))}</td><td>${esc(val(t.evaluation.error))} / ${esc(val(t.evaluation.tolerance))}<br>${esc(t.evaluation.error_kind)}</td><td class="${t.evaluation.success?'good':'bad'}">${t.evaluation.success?'PASS':esc(t.evaluation.status)}<br>${esc(t.evaluation.reason)}</td></tr>`).join('')}</table><details><summary>Full public input and target specifications</summary><pre>${esc(JSON.stringify(r.public_problem,null,2))}</pre></details></details>`).join('');}
document.querySelectorAll('input,select').forEach(x=>x.addEventListener('input',render));render();</script>'''
    with (HERE/'answers.html').open('x',encoding='utf-8') as f:f.write(page.replace('DATA',json.dumps(data,ensure_ascii=False).replace('<','\\u003c')))
    print(json.dumps(summary,indent=2))
    if mismatches: raise ValueError('historical results differ; inspect summary')

if __name__=='__main__':
    if sys.argv[1]=='infer':infer()
    elif sys.argv[1]=='report':report()
    else:raise ValueError('infer or report required')
