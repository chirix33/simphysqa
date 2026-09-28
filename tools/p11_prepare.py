"""Outcome-blind candidate inventory; no held-out references are opened."""
from p11_common import *
from collections import defaultdict,Counter
from phi_jepa.integration.readers import PublicInputReader,json_lines
from phi_jepa.integration.contracts import validate_enrichment

def inventory():
    bootstrap();cat=catalog();domains={};all_rows=[]
    cached={p.stem:p for root in ('p02b-profile','p08-learning-01','p10-qualification-01') for p in (NATIVE/root/'enrichment').glob('*.json')}
    for domain in sorted({d for d,s in cat.partitions}):
        pools={};summary={}
        for split,limit in [('train',80),('validation',8),('test_id',20)]:
            meta={r['sample_id']:r['metadata'] for r in json_lines(cat.verified_file(domain,split,'evaluator.jsonl'))};groups=defaultdict(list)
            path=cat.verified_file(domain,split,'inputs.jsonl')
            for p in PublicInputReader(path,file_hash(path)):
                m=meta[p.sample_id];groups[m['base_scenario_id']].append((p,m))
            # Cache availability is public infrastructure information, never a
            # score. Preserve existing P10 selection scenarios for main selection.
            old=load(NATIVE/'p10-qualification-01/selected-public.json') if domain=='tethered_load' else []
            preferred={r['scenario_id'] for r in old if r['split']==split}
            ordered=sorted(groups,key=lambda scenario:(scenario not in preferred,digest(f'p11|11|{domain}|{split}|{scenario}')))[:limit]
            rows=[]
            for scenario in ordered:
                p,m=min(groups[scenario],key=lambda pm:(max(s['end_time'] for s in pm[0].input['answer_spec']),pm[0].sample_id))
                cache=cached.get(p.sample_id)
                if cache:
                    try: validate_enrichment(p,load(cache))
                    except ValueError: cache=None
                rows.append({'sample_id':p.sample_id,'scenario_id':scenario,'split_group':m['split_group_id'],'split':split,'domain':domain,
                    'public':{'sample_id':p.sample_id,'schema_version':p.schema_version,'input':p.input},'enrichment_cache':str(cache) if cache else None})
            pools[split]=rows;all_rows.extend(rows)
            summary[split]={'trajectories':len(rows),'cached_enrichment':sum(r['enrichment_cache'] is not None for r in rows),'question_types':dict(Counter(r['public']['input']['task_type'] for r in rows))}
        if any({r['scenario_id'] for r in pools[a]}&{r['scenario_id'] for r in pools[b]} for a,b in [('train','validation'),('train','test_id'),('validation','test_id')]):raise ValueError('scenario_split_overlap')
        domains[domain]={'pools':pools,'summary':summary}
    save(OUT/'candidate_inventory.json',{'domains':domains,'release_identity':cat.identity,'reference_outcomes_opened':False,'seed':11,
        'rule':'Within original partitions: existing P10 train/selection scenarios first for tethered-load, then fixed SHA256 order; one earliest-horizon question then sample_id; no score access.'})
    print(json.dumps({d:v['summary'] for d,v in domains.items()}))

def freeze():
    if (OUT/'plan.json').exists(): raise ValueError('plan_already_frozen')
    inv=load(OUT/'candidate_inventory.json'); rows=[]; cohorts={}; coverage=[]
    for domain,item in inv['domains'].items():
        pools=item['pools']; chosen=pools['train'][:48]+pools['validation'][:8]+pools['test_id'][:12]
        cohorts[domain]={'main_train':[r['sample_id'] for r in pools['train'][:48]],'main_selection':[r['sample_id'] for r in pools['validation'][:8]],
            'main_test':[r['sample_id'] for r in pools['test_id'][:12]],'appendix_train':[r['sample_id'] for r in pools['train'][:16]],'appendix_test':[r['sample_id'] for r in pools['test_id'][:4]]}
        for r in chosen:
            r={**r,'appendix':r['sample_id'] in cohorts[domain]['appendix_train']+cohorts[domain]['appendix_test']};rows.append(r)
            for s in r['public']['input']['answer_spec']: coverage.append({'domain':domain,'split':r['split'],'sample_id':r['sample_id'],'quantity':s['quantity'],'answer_type':s['answer_type'],'horizon':s['end_time'],'appendix':r['appendix']})
    rows.sort(key=lambda r:(not r['appendix'],r['split']!='train',r['domain'],r['sample_id']))
    timings={short:load(OUT/'timing'/f'{short}.json') for short in ('coconut','codi')}
    estimate=sum(sum(r['step_seconds'])/len(r['step_seconds'])*32 for values in timings.values() for r in values)
    plan={'version':'p11-deadline-study-v1','frozen_utc':time.time(),'seed':11,'main_trajectories_per_domain':60,'main_train':48,'main_test':12,'main_separate_selection':8,
        'appendix_trajectories_per_domain':20,'appendix_train':16,'appendix_test':4,'cohorts':cohorts,'selection_rule':inv['rule'],
        'main_models':['Phi-JEPA independent per-domain layout','gpt-5.6-sol direct public all components'],
        'appendix_models':['Phi-JEPA independently trained per-domain on appendix train only','custom Coconut shared across four domains','custom CODI student shared across four domains'],
        'custom_policy':{'passes':2,'examples':64,'updates':128,'checkpoint':'final completed second pass; no held-out selection','generation_milestones':'one fixed training example after each complete pass; held-out only after final checkpoint','initialization':'fresh pinned flan-t5-small, seed 11; never timing checkpoint'},
        'numerical_policy':{'updates':20000,'batch_pairs':20,'milestones':[5000,10000,20000],'main_checkpoint':'minimum separate validation numeric tolerance-normalized error; earliest on ties','appendix_checkpoint':'final update 20000; no test access for selection','parameterization':'unchanged P10 biasinit_conditioned_full, equal pair sampler, full interval'},
        'custom_training_estimated_seconds':estimate,'provider_probe_seconds':[4.372,4.866,4.128],
        'estimates_seconds':{'preparation_enrichment_encoding':1800,'custom_training':estimate,'custom_generation':700,'numerical_cpu_parallel':2400,'answer_api':1800,'report_recovery':1200},
        'estimated_expensive_finish_utc':'2026-09-26T04:15:00Z','deadline_utc':DEADLINE,'expensive_stop_utc':EXPENSIVE_STOP,
        'assumptions':'Domain-specific two-update mean; +~25 minutes GPU scheduling/generation allowance. Provider work sequential remote, overlaps local compute with separate accounting. No competing GPU workers. Main numerical CPU runs separately. Long-input variation remains uncertain.',
        'deferred':['new ablation retraining','CODI hybrid/teacher evaluation','calibrated OOD detection','human clarification evaluation','larger custom cohort'],
        'heldout_outcomes_opened_before_freeze':False,'inventory_sha256':file_hash(OUT/'candidate_inventory.json'),'execution_sha256':file_hash(OUT/'execution.json')}
    save(OUT/'selected-public.json',rows);save(OUT/'question_coverage.json',coverage);save(OUT/'plan.json',plan)
    save(OUT/'selection.json',{'release_identity':inv['release_identity'],'plan_sha256':digest(plan),'rows':[{k:v for k,v in r.items() if k!='public'} for r in rows]})
    save(ROOT/'configs/study_p11_frozen.json',plan)
    print(json.dumps({'frozen_questions':len(rows),'custom_training_estimated_seconds':estimate,'main_test':48,'appendix_test':16}))

if __name__=='__main__':
    if len(sys.argv)>1 and sys.argv[1]=='freeze': freeze()
    else: inventory()
