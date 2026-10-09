"""Freeze nested qualified manifests and public requests; never execute a model."""
from collections import Counter
from pathlib import Path
import argparse,subprocess
from .io import ROOT,DOMAINS,QUESTION_TYPES,read,write,external,canonical,digest,manifest
from .formal_sampling import file_hash,save_bytes
from .heldout_scope import formal_scope
from .heldout_live import annotation_ledger,simulation_wall,execution_plan
from .dataset import validate,restore
from .spq01a import retained,verify_manifest
from .spq06 import public_request,ABLATION
from .main_public import request_from
from .condition_revisions import resolved_condition

def export(run,pilot,output):
    run=external(run);pilot=external(pilot);output=external(output);plan=execution_plan(run)
    if (output/'manifest.json').exists():verify_manifest(output);return read(output/'manifest.json')
    counts=Counter();selected=[];ledger=[];records={};checks=[];indexes=[];history=annotation_ledger(run)
    retained(output/'private/generation-scope.json',{'candidates':plan['candidates'],'excluded_groups':plan['excluded_groups']})
    with formal_scope(plan['candidates'],plan['excluded_groups']):
        for c in plan['candidates']:
            case=run/'cases'/c['candidate_id'];path=case/'status.json';status=read(path) if path.exists() else None
            ledger.append({**c,'processing':status,'disposition':
                'qualified_selected' if status and status['status']=='completed' else 'retained_rejection' if status else
                'unused_reserve_cell_filled' if counts[c['cell']]>=20 else 'unprocessed_after_stop',
                'clarification_eligibility':read(case/'clarification-eligibility.json') if (case/'clarification-eligibility.json').exists() else None})
            if not status or status['status']!='completed':continue
            r=read(case/'record.json');validate(r)
            if digest(r)!=status['record_sha256'] or digest(restore(r))!=c['source']['source']['record_sha256']:raise ValueError('record/source changed')
            if counts[c['cell']]>=20:raise ValueError('extra completed cell item')
            counts[c['cell']]+=1;rank=counts[c['cell']]
            item={'sample_id':r['sample_id'],'group_id':c['source']['group_id'],'domain':c['domain'],'family':c['question_type'],
                'split':c['source']['split'],'candidate_id':c['candidate_id'],'candidate_rank':c['rank'],'qualified_cell_rank':rank,
                'nested_core':rank<=10,'record_sha256':digest(r),'original_source_sha256':c['source']['source']['record_sha256'],
                'private_record':'private/records/'+r['sample_id']+'.json','executed_case_path':str(case)}
            selected.append(item);records[r['sample_id']]=r;retained(output/item['private_record'],r)
            indexes.append({'path':item['private_record'],'sha256':digest(r),'kind':'reused_qualified_output',
                'source_case':str(case),'annotation_attempts':[x['attempt_number'] for x in history if x['candidate_id']==c['candidate_id']],
                'source_execution_procedures':['event_language.enrich','answer_annotations.enrich',
                    {'direct':'direct.build_direct','predictive':'original admitted source reused','counterfactual':'counterfactual.build',
                     'explanation':'counterfactual.build + explanation.build','clarification':'counterfactual.build + clarification.build'}[c['question_type']]],
                'export_procedure':'exact saved qualified record reuse; no new calls'})
        if len({i['sample_id'] for i in selected})!=len(selected) or len({i['group_id'] for i in selected})!=len(selected):raise ValueError('evaluation identity/group duplication')
        if {i['group_id'] for i in selected}&set(plan['excluded_groups']):raise ValueError('excluded group selected')
        if any(i['split']!='test_id' for i in selected):raise ValueError('split mixing')
        allcells=[d+'/'+f for d in DOMAINS for f in QUESTION_TYPES]
        core=[i for i in selected if i['nested_core']]
        core_ready=len(core)==200 and all(counts[c]>=10 for c in allcells)
        full_ready=len(selected)==400 and all(counts[c]==20 for c in allcells)
        identity={'version':'SPQ06-heldout-manifest/1.0.0','selection_protocol_sha256':plan['preparation_protocol_sha256'],
            'execution_plan_sha256':digest(plan),'producer_commit':subprocess.check_output(['git','rev-parse','HEAD'],cwd=ROOT,text=True).strip(),
            'exclusions':plan['excluded_groups'],'sampling_claim':'balanced qualified test_id benchmark; not natural release frequencies',
            'readiness':'generation_and_validation_ready' if full_ready else 'nested_core_ready_only' if core_ready else 'shortfall',
            'allocation':dict(counts),'qualified_items':len(selected),'missing_per_cell':{c:max(0,20-counts[c]) for c in allcells},
            'main_outputs':0,'human_acceptability':'not_established'}
        retained(output/'nested-200-manifest.json',{**identity,'target':200,'complete':core_ready,'items':core})
        retained(output/'nested-400-manifest.json',{**identity,'target':400,'complete':full_ready,'items':selected})
        condition_files=list((pilot/'conditions').glob('*.json'))
        if len(condition_files)!=9:raise ValueError('all nine conditions must have pinned configurations')
        for path in condition_files:
            cid=read(path)['condition_id'];condition,actual_path=resolved_condition(pilot,cid)
            retained(output/'conditions'/path.name,condition)
            candidates=[pilot.parent/'gemma_pilot_worker.py',*pilot.parent.glob('frozen-workers*/local_pilot_worker.py')]
            source=next((p for p in candidates if p.exists() and file_hash(p)==condition['worker_sha256']),None)
            if source is None:raise ValueError('no exact pinned worker source')
            if file_hash(source)!=condition['worker_sha256']:raise ValueError('qualified standalone worker changed')
            save_bytes(output/'workers'/(cid+'.py'),source.read_bytes())
            for size,items in ((200,core),(400,selected)):
                for ablation in (False,True):
                    if ablation and cid not in ABLATION:continue
                    label='structured_only' if ablation else 'enriched';requests=[]
                    for item in items:
                        r=records[item['sample_id']];q,check=request_from(public_request(r,condition),ablation)
                        retained(output/'public'/str(size)/label/cid/(r['sample_id']+'.json'),q);requests.append(q)
                        checks.append({'sample_id':r['sample_id'],'size':size,'condition_id':cid,**check})
                    retained(output/'request-lists'/str(size)/(cid+'-'+label+'-stage1.json'),requests)
        retained(output/'private/candidate-failure-ledger.json',ledger)
        accounting={'initial_requests':sum(h['initial_request'] for h in history),'attempts':len(history),'retries':sum(h['repair'] for h in history),
            'charged_usd':sum(h['charged_upper_bound_usd'] for h in history),'annotation_work_seconds':sum(h['wall_seconds'] for h in history),
            'reserved_input_tokens':sum(h['reservation']['input_token_upper_bound'] for h in history),
            'reserved_output_tokens':sum(h['reservation']['output_token_limit'] for h in history),
            'simulation_executions':len(list((run/'cases').glob('*/runs/executions/*/reservation.json'))),'simulation_worker_static_seconds':simulation_wall(run)}
        retained(output/'resource-accounting.json',accounting);retained(output/'public-projection-validation.json',checks)
        retained(output/'per-file-generation-index.json',indexes)
        prose=[i for i in core if i['family']=='explanation' and i['qualified_cell_rank']<=2]
        retained(output/'model-prose-assessment-subset.json',{'version':'SPQ06-model-prose-subset/1.0.0','items':prose,
            'conditions':[read(p)['condition_id'] for p in condition_files],'assessments':len(prose)*9,'judgments_collected':0,
            'purpose':'blinded human model-answer prose study; distinct from annotation audit'})
        lines=['# SPQ06 held-out preparation',f"\nQualified {len(selected)} distinct items; core complete: {core_ready}; 400 complete: {full_ready}.",
            '\nNo main answering outputs or human model-answer judgments exist. Original private evidence remains at each executed_case_path.']
        lines.extend('\n- '+i['domain']+' / '+i['family']+' / '+i['sample_id']+' — '+i['private_record'] for i in selected)
        save_bytes(output/'INDEX.md',('\n'.join(lines)+'\n').encode())
        return manifest(output,{'purpose':'SPQ06 frozen nested evaluation preparation','identities':identity,'accounting':accounting,'new_model_calls':0})

if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('--run',type=Path,required=True);p.add_argument('--pilot',type=Path,required=True);p.add_argument('--output',type=Path,required=True)
    a=p.parse_args();print(canonical(export(a.run,a.pilot,a.output)['identities']).decode())
