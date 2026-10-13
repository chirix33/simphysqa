"""SPQ06 frozen development pilot and held-out design; no provider calls."""
import argparse
from collections import Counter, defaultdict
from copy import deepcopy
import csv
from pathlib import Path
import random
import subprocess

from .io import ROOT, DOMAINS, QUESTION_TYPES, canonical, digest, read, write, external
from .spq01a import retained, verify_manifest
from .formal_sampling import file_hash, source_record

VERSION = 'simphysqa-SPQ06/1.0.0'
SEED = 20261009
ABLATION = ('qwen3_8b_direct', 'qwen3_32b_awq_on')


def conditions():
    plan = read(ROOT/'configs/simphysqa/evaluation.json')
    if len(plan['conditions']) != 9 or len({c['condition_id'] for c in plan['conditions']}) != 9:
        raise ValueError('authoritative nine-condition identity changed')
    result = deepcopy(plan['conditions'])
    for c in result:
        s = c['settings']; native = c['reasoning'] == 'native'; cot = c['reasoning'] == 'prompted_cot'
        for k, v in {'max_input_and_output':32768, 'max_new_tokens':8192 if native else 4096 if cot else 1024,
                     'max_seconds':360 if native else 240 if cot else 120, 'seed':11,
                     'temperature':0.6, 'top_p':0.95 if native else 0.9, 'top_k':20 if 'qwen' in c['condition_id'] else 50}.items():
            if s.get(k) is None: s[k] = v
    return result


def parse_answer(raw):
    """Extract one final JSON object; no repair, completion, coercion or guess."""
    from .io import parse
    text = raw.strip()
    reasoning = '</think>' in text
    if reasoning: text = text.rsplit('</think>', 1)[1].strip()
    if text.startswith('```json\n') and text.endswith('```'): text = text[8:-3].strip()
    elif text.startswith('```\n') and text.endswith('```'): text = text[4:-3].strip()
    # Prompted CoT may precede the final object; a unique complete JSON suffix is allowed.
    possibilities = []
    for i, char in enumerate(text):
        if char != '{': continue
        try:
            value = parse(text[i:])
            if isinstance(value, dict): possibilities.append((i,value))
        except ValueError: pass
    if len(possibilities) != 1: raise ValueError('missing_or_ambiguous_final_JSON_object')
    return possibilities[0][1], {'explicit_think_closure':reasoning, 'prose_prefix_present':bool(text[:possibilities[0][0]].strip()),
                                 'reasoning_compliance':'separate_format_diagnostic_not_correctness'}


def public_request(record, condition, structured_only=False):
    from .evaluation import request
    value = request(record, condition, association_version='simphysqa-associations/1.1.1')
    family = record['question_type']
    if family in ('direct','predictive','counterfactual'):
        value['messages'][0]['content'] += ('\nReturn a final JSON object: {"targets":[{"target_id":"declared ID","value":"typed number, Boolean or vector",'
            '"unit":"declared unit","frame":"declared frame"}]}. Values must have their actual JSON types, not strings. '
            'Include every requested target. If abstaining, return {"abstained":true}. Do not invent missing information.')
    if structured_only:
        value = structured_request(value, family)
    if value['tools'] != []: raise ValueError('answering tools forbidden')
    return value


def structured_request(value, family):
    """Remove only derived language; preserve structured task facts and ambiguity."""
    from .io import parse
    from .dataset import public_record
    result = deepcopy(value)
    content = result['messages'][0]['content']; start = content.find('\n{')
    if start < 0: raise ValueError('missing public JSON view')
    body = content[start+1:]; decoder = __import__('json').JSONDecoder()
    view, end = decoder.raw_decode(body)
    annotations = view.get('annotations')
    if annotations is None: raise ValueError('missing annotations in public projection')
    # Generated measurement/event text has bound structured sources. Unique physical
    # context and question/control/predicate strings are retained as underlying facts.
    view.pop('annotations')
    result['messages'][0]['content'] = content[:start] + '\n' + canonical(view).decode() + body[end:]
    result['input_variant'] = 'structured_only'
    return result


def freeze_pilot(artifacts, output, development_index):
    output=external(output); index=read(development_index); rng=random.Random(SEED)
    selected=[]; used=set(); all_items=index['items']
    for domain in DOMAINS:
        # Prioritize the three smaller pools; reuse is unavoidable with only 16 groups.
        for family in ('clarification','explanation','counterfactual','direct','predictive'):
            pool=sorted([i for i in all_items if i['domain']==domain and i['family']==family],key=lambda x:x['sample_id'])
            rng.shuffle(pool); item=next((i for i in pool if i['group_id'] not in used),pool[0])
            selected.append(item);used.add(item['group_id'])
    if len(selected)!=20 or len({x['sample_id'] for x in selected})!=20:raise ValueError('pilot selection')
    plan=conditions(); refs=[]
    for item in selected:
        root=Path(artifacts)/index['roots'][item['artifact_root']]
        record=read(root/item['paths']['organizer_record'])
        if digest(record)!=item['record_sha256']:raise ValueError('accepted development record changed')
        retained(output/'private-records'/(item['sample_id']+'.json'),record)
        ref={k:item[k] for k in ('sample_id','family','domain','group_id','split','record_sha256')}; refs.append(ref)
        for c in plan:retained(output/'public-requests'/c['condition_id']/(item['sample_id']+'.json'),public_request(record,c))
    frozen={'version':VERSION,'purpose':'local execution qualification and timing; not quality estimate','seed':SEED,
        'producer_commit':subprocess.check_output(['git','rev-parse','HEAD'],cwd=ROOT,text=True).strip(),
        'source_development_index_sha256':file_hash(development_index),'selected':refs,'conditions':plan,
        'initial_request_ceiling':180,'continuation_ceiling':36,'pilot_gpu_work_seconds_ceiling':64800,
        'loading_seconds_per_process_ceiling':600,'sequential_gpu':True,'tools':[],
        'failure_policy':'one attempt/stage; raw outputs retained; no answer repair or retry; interrupted reservations remain failures; no replacement items',
        'continuation_policy':'actual first-turn raw assistant text only; supported structured slot routed by accepted CPU route_reply; no authored gold assistant turn',
        'reasoning_policy':'separate raw-reasoning/closure/prose format diagnostics from validity and correctness',
        'ablation_conditions':list(ABLATION),'unique_groups':len(used),'main_experiment_enabled':False}
    retained(output/'pilot-plan.json',frozen)
    print(canonical({'pilot_items':20,'groups':len(used),'initial_requests':180,'max_continuations':36,'new_calls':0}).decode())
    return frozen


def audit_status(audit):
    delivery=Path(audit)/'delivery-1.0.0'; verify_manifest(delivery)
    final=read(delivery/'final-140-manifest.json'); groups=set()
    for item in final['assignments']:groups.add(item['group_id'])
    forms={}
    for rid in ('R1','R2','R3'):
        with (delivery/'forms'/(rid+'.csv')).open(newline='',encoding='utf-8') as f: rows=list(csv.DictReader(f))
        forms[rid]={'rows':len(rows),'collected_in_frozen_form':sum(bool(r['judgment']) for r in rows),'sha256':file_hash(delivery/'forms'/(rid+'.csv'))}
    return {'source':'actual frozen SPQ05 delivery','manifest_sha256':file_hash(delivery/'manifest.json'),'items':len(final['assignments']),
            'groups':sorted(groups),'forms':forms,'feedback_status':'user reports processing; independent feedback is not imported or inferred',
            'calibration_items':0}


def freeze_heldout(inventory, historical, audit, output):
    output=external(output); verify_manifest(inventory)
    rows=[__import__('json').loads(x) for x in (Path(inventory)/'records.jsonl').read_text().splitlines()]
    summary=read(Path(inventory)/'summary.json')
    for path,h in read(Path(inventory)/'source-files.json').items():
        if file_hash(path)!=h:raise ValueError('original release changed')
    if file_hash(Path(summary['data_root'])/'release-manifest.json')!=summary['release_manifest_sha256']:raise ValueError('release manifest changed')
    status=audit_status(audit); old=read(historical)
    development=set(read(ROOT/'configs/simphysqa/development_exclusions.json')['excluded_groups'])
    prompt_groups={i.get('split_group') or i.get('scenario_id') for i in old['items']}
    prompt_samples={i['sample_id'] for i in old['items']}
    excluded=development|set(status['groups'])|prompt_groups
    eligible=defaultdict(lambda:defaultdict(list)); rejected=[]
    for r in rows:
        reason='not_original_test_id' if r['split']!='test_id' else 'development_or_audit_or_prompt_use' if r['group_id'] in excluded or r['sample_id'] in prompt_samples else None
        if reason:rejected.append({'sample_id':r['sample_id'],'group_id':r['group_id'],'domain':r['domain'],'split':r['split'],'reason':reason})
        else:eligible[r['domain']][r['group_id']].append(r)
    rng=random.Random(SEED); candidates=[]; pools={}
    for domain in DOMAINS:
        groups=sorted(eligible[domain]);rng.shuffle(groups);cells={f:[] for f in QUESTION_TYPES}
        for i,g in enumerate(groups):cells[QUESTION_TYPES[i%5]].append(rng.choice(sorted(eligible[domain][g],key=lambda x:x['sample_id'])))
        for family in QUESTION_TYPES:
            cell=domain+'/'+family;pools[cell]=len(cells[family])
            for rank,r in enumerate(cells[family][:40],1):
                candidates.append({'candidate_id':'SPQ06-C-'+digest({'cell':cell,'rank':rank,'source':r['sample_id'],'seed':SEED})[:20],
                    'cell':cell,'domain':domain,'question_type':family,'rank':rank,'source':r})
    from .annotation import payload,reservation
    provider=read(ROOT/'configs/simphysqa/annotation_spq01.json'); bounds=[]; prechecks=[]
    for c in candidates:
        try:
            parent=source_record(c['source']); body=payload(parent,provider); bound=reservation(body,provider)
            retained(output/'prepared-annotation-requests'/(c['candidate_id']+'.json'),body)
            bounds.append({'candidate_id':c['candidate_id'],'cell':c['cell'],'rank':c['rank'],**bound})
            prechecks.append({'candidate_id':c['candidate_id'],'status':'source_admitted_payload_valid'})
        except Exception as e:prechecks.append({'candidate_id':c['candidate_id'],'status':'failed','exception_type':type(e).__name__,'reason':str(e)[:160]})
    estimates={}
    for n in (200,400,'all_candidates'):
        subset=bounds if isinstance(n,str) else [b for b in bounds if b['rank']<=n//20]
        estimates[str(n)]={'annotation_initials':len(subset),'two_attempt_maximum':len(subset)*2,
            'reserved_input_tokens_two_attempts':sum(b['input_token_upper_bound'] for b in subset)*2,
            'reserved_output_tokens_two_attempts':sum(b['output_token_limit'] for b in subset)*2,
            'reservation_usd_initials':sum(b['usd'] for b in subset),'reservation_usd_two_attempts':sum(b['usd'] for b in subset)*2,
            'maximum_simulator_executions':sum(4 for c in candidates if (isinstance(n,str) or c['rank']<=n//20) and c['question_type'] in ('counterfactual','explanation','clarification'))}
    pins={p.relative_to(ROOT).as_posix():file_hash(p) for folder in ('src/simphysqa','src/phi_jepa/simulation') for p in (ROOT/folder).rglob('*') if p.suffix in ('.py','.json')}
    for p in [ROOT/'dataset.schema.json',ROOT/'configs/simphysqa/evaluation.json',ROOT/'configs/simphysqa/annotation_spq01.json']:pins[p.relative_to(ROOT).as_posix()]=file_hash(p)
    frozen={'version':VERSION,'seed':SEED,'target_items':400,'nested_core_items':200,'per_cell':20,'core_per_cell':10,
        'canonical_families':list(QUESTION_TYPES),'paper_label_explanatory_maps_to':'explanation','candidate_order':candidates,
        'candidate_order_sha256':digest(candidates),'eligible_pool_counts':pools,'eligible_groups':sum(len(g) for g in eligible.values()),
        'split_policy':'original test_id only; original split labels preserved; no train/validation/test_ood mixing',
        'source_inventory_manifest_sha256':file_hash(Path(inventory)/'manifest.json'),'source_release_manifest_sha256':summary['release_manifest_sha256'],
        'source_records':summary['records'],'source_groups':summary['groups'],'excluded_groups':sorted(excluded),
        'historical_prompt_use_sha256':file_hash(historical),'spq05_actual_status':status,'source_code_schema_pins':pins,
        'sampling':'sorted test_id groups shuffled per domain; round-robin disjoint five-family pools; one random original QA per group; first 40 candidates or full smaller pool',
        'qualification':'first 20 scientifically qualified in each frozen cell order; first 10 form core, next 10 extension; same-cell reserves only; no effect-size filter for CF/explanation; keep every rejection/retry/failure',
        'clarification':'actual scorer-disjoint acceptance regions and whole-visible-input-compatible witnesses; eligibility attrition recorded separately',
        'outcome_evidence':'original admitted data preserved; new matched outcomes require canonical exact factual replay plus separate coarse/fine original and alternative admission',
        'cutoff':'preserve source observation cutoff; selected explanation comparison explicitly supplied, never observations',
        'annotation_settings':{k:v for k,v in provider.items() if k not in ('budget','credential_reference_file')},
        'spending_authorization':'none for SPQ06 paid annotation/new simulation generation; SPQ05 budgets are not reused',
        'estimates':estimates,'initial_source_prechecks':Counter(p['status'] for p in prechecks),
        'ablation_conditions':list(ABLATION),'ablation_reason':'same Qwen architecture family, unquantized small direct and larger AWQ native reasoning; prespecified before main scores',
        'decision_rule':'400 only if 20/cell qualified and measured all-nine-condition main+two-condition ablation forecast plus 25% runtime reserve <=48 GPU hours and preparation finishes leaving >=12 hours for analysis/writing before 2026-10-12 23:59 AoE; else qualified nested200; never use main scores',
        'main_answering_enabled':False,'human_model_prose_subset':'first 2 explanation items/cell in core, every condition; blinded independent claim-level rubric; not annotation audit'}
    retained(output/'protocol.json',frozen);retained(output/'candidate-order.json',candidates);retained(output/'eligibility-rejections.json',rejected)
    retained(output/'source-prechecks.json',prechecks);retained(output/'annotation-estimates.json',estimates)
    print(canonical({'eligible_groups':frozen['eligible_groups'],'cell_pool_counts':pools,'candidates':len(candidates),'prechecks':frozen['initial_source_prechecks'],'estimates':estimates,'new_calls':0}).decode())
    return frozen


def main():
    p=argparse.ArgumentParser();s=p.add_subparsers(dest='command',required=True)
    a=s.add_parser('pilot-freeze');a.add_argument('--artifacts',type=Path,required=True);a.add_argument('--index',type=Path,required=True);a.add_argument('--output',type=Path,required=True)
    b=s.add_parser('heldout-freeze');b.add_argument('--inventory',type=Path,required=True);b.add_argument('--historical',type=Path,required=True);b.add_argument('--audit',type=Path,required=True);b.add_argument('--output',type=Path,required=True)
    a=p.parse_args()
    if a.command=='pilot-freeze':freeze_pilot(a.artifacts,a.output,a.index)
    else:freeze_heldout(a.inventory,a.historical,a.audit,a.output)


if __name__=='__main__':main()
