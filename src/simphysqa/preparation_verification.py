"""Independent saved-output verification; no model, provider or simulator calls."""
import argparse,json
from collections import Counter
from pathlib import Path
from .io import canonical,digest,read,write,external,DOMAINS,QUESTION_TYPES
from .formal_sampling import source_record,file_hash
from .spq01a import verify_manifest
from .heldout_live import execution_plan,annotation_ledger,simulation_wall
from .heldout_scope import formal_scope
from .dataset import validate,restore,public_record,pointer
from .main_public import project,structured_input

def forbidden(value):
    if isinstance(value,dict):
        if {'private','reference','solution_trace','witnesses','annotation_provenance','recorded_cost_usd','OPENAI_API_KEY'}&set(value):raise ValueError('private evidence in public task')
        for v in value.values():forbidden(v)
    elif isinstance(value,list):
        for v in value:forbidden(v)

def preserved(inventory,prior,audit,protocol,output):
    if file_hash(inventory/'manifest.json')!=protocol['source_inventory_manifest_sha256']:raise ValueError('source inventory differs')
    verify_manifest(inventory);source=read(inventory/'source-files.json');summary=read(inventory/'summary.json')
    for name,h in source.items():
        if file_hash(name)!=h:raise ValueError('original release file changed')
    if file_hash(Path(summary['data_root'])/'release-manifest.json')!=protocol['source_release_manifest_sha256']:raise ValueError('release manifest changed')
    manifests=files=0
    for phase in ('spq01','spq01a','spq02','spq02b','spq03','spq04'):
        for path in (prior/phase).rglob('manifest.json'):
            if 'files' in read(path):info=verify_manifest(path.parent);manifests+=1;files+=len(info['files'])
    forms={};audit_manifests=0
    from .focused_audit import validate_form
    for path in audit.rglob('manifest.json'):
        if 'files' in read(path):verify_manifest(path.parent);audit_manifests+=1
    delivery=read(audit/'delivery-1.0.0/manifest.json');assignments=delivery['assignments']
    if len(assignments)!=140 or len({i['group_id'] for i in assignments})!=140:raise ValueError('SPQ05 identity changed')
    for rid in ('R1','R2','R3'):
        checked=validate_form((audit/'delivery-1.0.0/forms'/(rid+'.csv')).read_bytes(),assignments,rid,'formal')
        if checked['collected']!=0 or checked['blank']!=140:raise ValueError('stored blank audit forms changed')
        forms[rid]=140
    report={'version':'SPQ06-source-preservation/1.0.0','source_files':len(source),'source_qa':summary['records'],
        'source_groups':summary['groups'],'source_release_manifest_sha256':protocol['source_release_manifest_sha256'],
        'prior_manifests':manifests,'prior_indexed_files':files,'spq05_manifests':audit_manifests,
        'stored_spq05_blank_forms':forms,'external_human_feedback':'processing per user; no imported judgments inferred',
        'new_calls':0,'preserved':True}
    write(output/'source-preservation.json',report);return report

def verify(run,preparation,output):
    run=external(run);preparation=external(preparation);output=external(output)
    dm=verify_manifest(preparation);plan=execution_plan(run);full=read(preparation/'nested-400-manifest.json');core=read(preparation/'nested-200-manifest.json')
    if len({i['group_id'] for i in full['items']})!=len(full['items']) or len({i['sample_id'] for i in full['items']})!=len(full['items']):raise ValueError('duplicate QA/group')
    if set(plan['excluded_groups'])&{i['group_id'] for i in full['items']}:raise ValueError('excluded group evaluated')
    candidates={c['candidate_id']:c for c in plan['candidates']};records={};states=private_bindings=pair_count=0
    with formal_scope(plan['candidates'],plan['excluded_groups']):
        for item in full['items']:
            r=read(preparation/item['private_record']);validate(r);sid=r['sample_id'];records[sid]=r;c=candidates[item['candidate_id']]
            if digest(r)!=item['record_sha256'] or canonical(restore(r))!=canonical(restore(source_record(c['source']))):raise ValueError('record/source changed')
            if item['split']!='test_id':raise ValueError('original split not held out')
            view=public_record(r,association_version='simphysqa-associations/1.1.1');forbidden(view)
            if any(s['timestamp']>view['input']['observation_cutoff'] for s in view['input']['states']):raise ValueError('future public observation')
            states+=len(view['input']['states'])
            from .answer_annotations import roots
            if r['question_type']=='explanation':
                from .explanation import evidence_roots
                root=evidence_roots(r);annotation=r['private']['explanation_annotation']
            elif r['question_type']=='clarification':
                from .clarification import roots as gap_roots
                root=gap_roots(r);annotation=r['private']['clarification_annotation']
            else:annotation=r['private']['answer_annotation'];root=roots(r,annotation['evidence_context'])
            def bindings(obj):
                nonlocal private_bindings
                if isinstance(obj,dict):
                    if {'namespace','pointer','value_sha256'}<=set(obj):
                        if digest(pointer(root[obj['namespace']],obj['pointer']))!=obj['value_sha256']:raise ValueError('unresolved private binding')
                        private_bindings+=1
                    else:
                        for v in obj.values():bindings(v)
                elif isinstance(obj,list):
                    for v in obj:bindings(v)
            bindings(annotation)
            runs=Path(item['executed_case_path'])/'runs'
            if (runs/'manifest.json').exists():verify_manifest(runs);pair_count+=1
        for cell in [d+'/'+f for d in DOMAINS for f in QUESTION_TYPES]:
            statuses=[c for c in plan['candidates'] if c['cell']==cell and (run/'cases'/c['candidate_id']/'status.json').exists() and read(run/'cases'/c['candidate_id']/'status.json')['status']=='completed']
            selected=[i for i in full['items'] if i['domain']+'/'+i['family']==cell]
            if [i['candidate_id'] for i in selected]!=[c['candidate_id'] for c in statuses[:20]]:raise ValueError('qualified randomized order changed')
            if [i['sample_id'] for i in core['items'] if i['domain']+'/'+i['family']==cell]!=[i['sample_id'] for i in selected[:10]]:raise ValueError('nested core changed')
        checks=0;public_hashes={};projected_views={}
        for path in preparation.glob('public/*/*/*/*.json'):
            q=read(path);sid=q['sample_id'];structured=q['input_condition']=='structured_only'
            if q['tools']!=[] or len(q['messages'])!=1:raise ValueError('initial request boundary')
            text=q['messages'][0]['content'].split('\n',1)[1];view,end=json.JSONDecoder().raw_decode(text);forbidden(view)
            if (sid,structured) not in projected_views:projected_views[(sid,structured)]=project(public_record(records[sid],association_version='simphysqa-associations/1.1.1'),structured)
            expected=projected_views[(sid,structured)]
            if canonical(view)!=canonical(expected):raise ValueError('projected task differs from exact accepted public input')
            key=(path.parents[2].name,sid)
            physical=digest(view['input'])
            if key in public_hashes and public_hashes[key]!=physical:raise ValueError('models/ablation got different physical facts')
            public_hashes[key]=physical;checks+=1
    history=annotation_ledger(run);budget=plan['provider_config']['budget']
    used={'initial_requests':sum(h['initial_request'] for h in history),'total_attempts':len(history),
        'usd_cap':sum(h['charged_upper_bound_usd'] for h in history),'total_input_tokens':sum(h['reservation']['input_token_upper_bound'] for h in history),
        'total_output_tokens':sum(h['reservation']['output_token_limit'] for h in history),'wall_seconds':sum(h['wall_seconds'] for h in history)}
    if any(used[k]>budget[k] for k in used) or max(Counter(h['candidate_id'] for h in history).values(),default=0)>2:raise ValueError('annotation ceiling exceeded')
    solves=len(list((run/'cases').glob('*/runs/executions/*/reservation.json')))
    if solves>plan['simulation_limits']['maximum_simulation_executions'] or simulation_wall(run)>plan['simulation_limits']['total_wall_seconds']:raise ValueError('simulation ceiling exceeded')
    report={'version':'SPQ06-preparation-verification/1.0.0','qualified_items':len(full['items']),'core_items':len(core['items']),
        'allocation':dict(Counter(i['domain']+'/'+i['family'] for i in full['items'])),'unique_qa_and_groups':True,
        'exclusions':len(plan['excluded_groups']),'states_with_original_cutoffs':states,'private_evidence_bindings_resolved':private_bindings,
        'qualified_saved_pair_manifests':pair_count,'exact_public_requests_checked':checks,'matched_ablation_physical_facts':True,
        'candidate_order_and_nested_core':True,'annotation_budget_used':used,'simulation_executions':solves,
        'simulation_worker_static_seconds':simulation_wall(run),'main_outputs':0,'human_model_answer_judgments':0,
        'preparation_manifest_sha256':file_hash(preparation/'manifest.json')}
    write(output/'preparation-verification.json',report);return report

if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('command',choices=('preservation','main'))
    for name in ('run','preparation','inventory','prior','audit','protocol'):p.add_argument('--'+name,type=Path)
    p.add_argument('--output',type=Path,required=True);a=p.parse_args()
    result=preserved(a.inventory,a.prior,a.audit,read(a.protocol),external(a.output)) if a.command=='preservation' else verify(a.run,a.preparation,a.output)
    print(canonical(result).decode())
