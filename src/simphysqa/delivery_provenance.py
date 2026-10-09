"""Immutable pilot accounting and per-file execution lineage; no scientific calls."""
from collections import Counter
from pathlib import Path
import argparse
from .io import read,write,external,canonical,digest
from .formal_sampling import file_hash

def pilot_accounting(pilot,output):
    stages=[(p,read(p)) for p in pilot.glob('executions/*/reservations/*.json')]
    keys=[(r['condition_id'],r['sample_id'],r['stage']) for p,r in stages]
    if len(set(keys))!=len(keys):raise ValueError('duplicate scientific stage reservation')
    initial=sum(r['stage']==1 for _,r in stages);continued=len(stages)-initial
    if initial>180 or continued>36:raise ValueError('pilot call ceiling exceeded')
    processes=[];measured=unknown=0
    for p in sorted((pilot/'process-reservations').glob('*.json')):
        if p.stem.endswith('-result'):continue
        result=p.with_name(p.stem+'-result.json');r=read(p)
        if result.exists():wall=read(result)['wall_seconds'];measured+=wall;status='measured_process_work'
        else:wall=r['reserved_seconds'];unknown+=wall;status='unknown_full_reservation'
        processes.append({'path':str(p),'file_sha256':file_hash(p),'accounted_seconds':wall,'accounting_status':status})
    # First two manual runs had item receipts but no process reservation.
    # Preserve the prespecified retrospective bounds, not invented timing.
    bound=6000
    total=measured+unknown+bound
    if total>64800:raise ValueError('pilot GPU-work ceiling exceeded')
    results=[read(p) for p in pilot.glob('executions/*/results/*.json')]
    result={'version':'SPQ06-pilot-accounting/1.0.0','initial_stage_reservations':initial,'continuation_stage_reservations':continued,
        'raw_results_returned':len(results),'unknown_item_stages':len(stages)-len(results),
        'process_measured_seconds':measured,'unknown_process_reservation_seconds':unknown,'manual_process_upper_bound_seconds':bound,
        'total_accounted_work_seconds':total,'gpu_work_cap_seconds':64800,'processes':processes,
        'input_tokens_all_returned_stages':sum(r['input_tokens'] for r in results),
        'output_tokens_all_returned_stages':sum(r['output_tokens'] for r in results),
        'api_answering_spend_usd':0,'independent_pilot_items':20,'pilot_trajectory_groups':len({r['group_id'] for r in read(pilot/'pilot-plan.json')['selected']}),
        'method':'failed CPU setup and unknown processes conservatively charged; zero-time capacity rejection is not inference; no scientific item/stage retry'}
    write(output/'pilot-resource-accounting.json',result);return result

def index(run,pilot,output):
    output=external(output);rows=[];counts=Counter()
    for label,root in (('heldout',run),('pilot',pilot)):
        for p in sorted(root.rglob('*')):
            if not p.is_file():continue
            rel=p.relative_to(root).as_posix();kind='execution_metadata_or_deterministic_procedure';extra={}
            if label=='heldout':
                if rel.startswith('annotation/requests/'):
                    attempt=read(root/'annotation/attempts'/p.name);kind='actual_annotation_payload_reserved_and_dispatched'
                    extra={'candidate_id':attempt['candidate_id'],'attempt_number':attempt['attempt_number'],'repair':attempt['repair'],
                        'payload_canonical_sha256':attempt['request_sha256'],'response_path':str(root/'annotation/responses'/p.name)}
                elif rel.startswith('annotation/responses/'):kind='actual_provider_response_and_failure_usage_accounting'
                elif '/runs/executions/' in rel:kind='actual_matched_simulation_execution_reservation_or_result'
                elif '/source-snapshot/' in rel:kind='reused_frozen_scientific_code'
                elif rel.endswith('/record.json'):kind='deterministic_qualified_qa_with_reused_source_and_generated_language'
                elif rel.endswith('/status.json'):kind='qualification_or_retained_rejection'
                elif rel.startswith(('simulation-work/','simulation-work-completed/')):kind='actual_simulator_or_static_compile_work_accounting'
            elif '/executed-requests/' in rel or '/executed-http-requests/' in rel:
                result=p.parent.parent/'results'/p.name;raw=read(result) if result.exists() else None
                invalid=(pilot/'invalid-runtime-receipts'/(p.parents[1].name+'.json')).exists()
                kind='reserved_public_answering_stage'
                extra={'dispatch':'not_dispatched_context_capacity' if raw and 'context_capacity' in str(raw.get('failure_reason')) else
                    'invalid_cpu_runtime' if invalid else 'actual_local_model_attempt' if raw else 'unknown_reserved_attempt',
                    'result_path':str(result),'actual_result_sha256':file_hash(result) if result.exists() else None}
            elif '/results/' in rel:kind='actual_local_execution_result_including_failures'
            elif rel.startswith(('public-requests/','request-lists/')):kind='prepared_public_request_not_itself_execution_evidence'
            elif rel.startswith('private-records/'):kind='reused_accepted_development_record'
            elif rel.startswith(('conditions/','condition-revisions/')):kind='pinned_condition_or_immutable_startup_revision'
            elif '/tokenized-prompts/' in rel:kind='deterministic_tokenization_of_reserved_public_request'
            counts[kind]+=1;rows.append({'root':label,'relative_path':rel,'source_path':str(p),'file_sha256':file_hash(p),'kind':kind,**extra})
    result={'version':'SPQ06-execution-per-file-provenance/1.0.0','files':rows,'kind_counts':dict(counts),
        'annotation_procedure':'adopted annotation.PROMPT and payload; requests are exact saved HTTP bodies, repairs retain validation feedback',
        'qa_procedures':'event_language.enrich, answer_annotations.enrich, direct.build_direct, matched counterfactual.build, explanation.build, clarification.build; saved status records identify actual qualification/rejections',
        'answering_procedure':'pinned standalone public-only workers; raw outputs and tokenized prompts retained; no gold/reference/model conversations substituted',
        'main_answering_calls':0,'human_judgments_collected':0}
    write(output/'execution-per-file-index.json',result);return {'files':len(rows),'kind_counts':dict(counts)}

if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('command',choices=('pilot','index'));p.add_argument('--run',type=Path);p.add_argument('--pilot',type=Path,required=True);p.add_argument('--output',type=Path,required=True)
    a=p.parse_args();result=pilot_accounting(external(a.pilot),external(a.output)) if a.command=='pilot' else index(external(a.run),external(a.pilot),external(a.output))
    print(canonical(result if a.command=='index' else {k:v for k,v in result.items() if k!='processes'}).decode())
