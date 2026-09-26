"""Fail-closed cross-run aggregation of separately evaluated cohort artifacts."""
from collections import defaultdict
from p10_common import *
from phi_jepa.typed_evaluation import grouped_summary


def aggregate_records(inputs,*,seed=11):
    groups=defaultdict(list); seen=set(); sets=defaultdict(dict)
    for identity,records in inputs:
        for row in records:
            key=(identity['domain'],identity['seed'],row['role'],row['condition'],row['method'],row['sample_id'])
            if key in seen: raise ValueError('duplicate_aggregate_question_condition')
            seen.add(key)
            group=(row['role'],row['condition'],row['method'])
            sets[(identity['domain'],identity['seed'],row['role'])].setdefault((row['condition'],row['method']),set()).add(row['sample_id'])
            # Same scenario across seeds remains one resampling cluster.
            groups[group].append({**row,'domain':identity['domain'],'distribution':row['role'],
                'scenario_id':identity['domain']+':'+row['scenario_id'],'seed':identity['seed']})
    for conditions in sets.values():
        if len({frozenset(ids) for ids in conditions.values()})!=1:
            raise ValueError('unmatched_questions_across_conditions')
    return [{'role':role,'condition':condition,'method':method,
        'seeds':sorted({r['seed'] for r in rows}),'summary':grouped_summary(rows,resamples=1000,seed=seed),
        'numeric_correct':sum(t['success'] for r in rows for t in r['targets'] if t['answer_type']!='boolean'),
        'numeric_eligible':sum(t['answer_type']!='boolean' for r in rows for t in r['targets']),
        'denominator':'question-seed attempts; bootstrap clusters the same scenario jointly across seeds'}
        for (role,condition,method),rows in sorted(groups.items())]


def aggregate(run,job):
    if not job.replace('_','').isalnum(): raise ValueError('aggregate_manifest_name_required')
    spec=load(ROOT/'configs/proposed_full_study'/f'{job}.json'); inputs=[]; missing=[]; identities=[]; cohort_sets={}
    for file in spec['profiles']:
        config=load(ROOT/file); root=Path(config['run_root'])
        if not (root/'config.json').exists() or load(root/'config.json')!=config:
            missing.append({'profile':file,'reason':'missing_or_changed_executed_config'}); continue
        for role in spec['roles']:
            path=root/'evaluation/cohorts'/f'{role}.json'
            if not path.exists(): missing.append({'profile':file,'role':role,'reason':'cohort_not_evaluated'}); continue
            data=load(path); records=data['answer_results']; expected={r['sample_id'] for r in load(root/'cohorts'/config['domain']/f'{role}.json')['public_rows']}
            cohort_key=(config['domain'],role)
            if cohort_key in cohort_sets and cohort_sets[cohort_key]!=expected: raise ValueError('unmatched_questions_across_seeds')
            cohort_sets[cohort_key]=expected
            conditions=defaultdict(set)
            for row in records: conditions[(row['condition'],row['method'])].add(row['sample_id'])
            methods=load(root/'active_methods.json')['methods']
            wanted={('numerical_readout',m) for m in methods}|{('frozen_answer_llm',m) for m in [*methods,'public_only']}|{('custom_answer',m) for m in ('coconut_coconut','codi_student','codi_teacher','codi_hybrid')}
            if set(conditions)!=wanted or any(ids!=expected for ids in conditions.values()):
                raise ValueError('cohort_conditions_or_question_denominators_incomplete')
            ident={'domain':config['domain'],'seed':config['seed'],'profile':file,'cohort_sha256':file_hash(path)}
            inputs.append((ident,records)); identities.append(ident)
    destination=run.root/'report/full_study_aggregate.json'
    if missing:
        save(destination,{'status':'incomplete','missing':missing,'summaries':[],
            'reason':'No pooled performance summary until every declared cohort is evaluated; ungenerated methods must be explicit failed records.'})
        raise ValueError('full_study_aggregation_missing_required_cohorts')
    save(destination,{'status':'complete','identities':identities,'spec_sha256':digest(spec),
        'summaries':aggregate_records(inputs),'calibrated_OOD_claim':False,
        'qualification':'Scenario-clustered uncertainty does not replace independent seeds or detector calibration.'})
