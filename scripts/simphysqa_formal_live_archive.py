"""Archive exact SPQ05 requests and index every executed/reused/deterministic file."""
import argparse
from pathlib import Path
from simphysqa.io import ROOT,canonical,digest,read,external
from simphysqa.formal_sampling import file_hash,save_bytes
from simphysqa.spq01a import retained,verify_manifest
from simphysqa.formal_live import execution_plan


def archive(run,delivery,preparation,previous,review_bundle,output):
    output=external(output);pm=verify_manifest(previous);dm=verify_manifest(delivery);prep=verify_manifest(preparation)
    plan=execution_plan(run);mappings=[]
    statuses={c['candidate_id']:read(run/'cases'/c['candidate_id']/'status.json') for c in plan['candidates'] if (run/'cases'/c['candidate_id']/'status.json').exists()}
    attempts={p.name:read(p) for p in (run/'annotation/attempts').glob('*.json')}
    by_candidate={}
    for name,a in attempts.items():
        response=run/'annotation/responses'/name
        by_candidate.setdefault(a['candidate_id'],[]).append({'attempt_file':name,'attempt_number':a['attempt_number'],
            'request_sha256':a['request_sha256'],'provider_completion':'recorded_response' if response.exists() else 'unknown_reserved',
            'validation_failure':read(response)['failure'] if response.exists() else 'interrupted_unknown_reserved'})
    selected={a['sample_id']:a for a in dm['assignments']}
    paths={a['packet_id']:a for a in dm['assignments']}
    verify_manifest(review_bundle)
    for alias,root in (('executed_run',run),('delivery',delivery),('review_distribution',review_bundle)):
        for p in sorted(root.rglob('*')):
            if not p.is_file() or p.name.startswith('.'):continue
            relative=p.relative_to(root).as_posix();mode='deterministic_saved_evidence_procedure';candidate=None;executed=False
            if alias=='executed_run' and relative.startswith('annotation/requests/'):
                a=attempts[p.name];candidate=a['candidate_id'];executed=True;mode='actual_executed_annotation_request'
                response=run/'annotation/responses'/p.name
                if not response.exists() or read(response)['raw_response'] is None:
                    executed=False;mode='attempted_annotation_request_unknown_provider_completion'
                save_bytes(output/'actual-requests'/p.name,p.read_bytes())
            elif alias=='executed_run' and relative.startswith('annotation/responses/'):
                candidate=attempts[p.name]['candidate_id'];mode='actual_provider_response_accounting';executed=True
                save_bytes(output/'actual-responses'/p.name,p.read_bytes())
            elif alias=='executed_run' and relative.startswith('annotation/attempts/'):
                candidate=attempts[p.name]['candidate_id'];mode='provider_attempt_reservation'
            elif alias=='executed_run' and relative.startswith('annotation/items/'):
                candidate=p.stem;mode='validated_executed_annotation'
            elif alias=='executed_run' and relative.startswith('simulation-work-completed/'):
                candidate=read(p)['candidate_id'];mode='actual_worker_or_static_compilation_resource_receipt'
            elif alias=='executed_run' and relative.startswith('simulation-work/'):
                candidate=read(p)['candidate_id'];mode='bounded_worker_admission_reservation'
            elif alias=='executed_run' and relative.startswith('cases/'):
                candidate=relative.split('/')[1]
                if '/executions/' in relative:mode='real_simulator_execution_evidence'
                elif '/source-snapshot/' in relative:mode='reused_exact_committed_simulator_source'
                elif p.name=='simulation-worker.log':mode='actual_simulator_worker_log'
                elif p.name=='runtime.json':mode='actual_saved_simulator_runtime_provenance'
                elif p.name=='record.json':mode='deterministic_family_qa_with_executed_public_language'
                elif p.name=='public-view.json':mode='deterministic_public_only_projection'
                elif p.name=='arm-interpretation.json':mode='actual_static_model_interpretation_zero_trajectory_steps'
                elif p.name=='simulation-plan.json':mode='reused_admitted_source_configuration_for_matched_verification'
                else:mode='deterministic_candidate_verification_or_failure'
            elif alias in ('delivery','review_distribution'):
                if relative.startswith('forms/'):mode='deterministic_identical_blank_reviewer_form_uncollected'
                if p.stem in paths:candidate=paths[p.stem]['candidate_id']
                if p.stem in selected:candidate=selected[p.stem]['candidate_id']
                if relative.startswith('focused'):mode='deterministic_exact_public_packet_extraction'
                if relative.startswith('auditor-only/'):mode='deterministic_blinded_private_packet_with_saved_evidence'
                if relative.startswith('public-items/'):mode='deterministic_public_only_projection'
                if relative.startswith('review-pages/'):mode='deterministic_readable_focused_scope_from_exact_packet_keys'
                if alias=='review_distribution':mode='reused_exact_blinded_distribution_of_same140_items'
            aggregate=(alias in ('delivery','review_distribution') and candidate is None and
                       (relative in ('focused.json','focused.jsonl','organizer-private/qa-records.jsonl','organizer-private/identity-key.json')
                        or relative.startswith('organizer-private/candidate')))
            source_candidates=([x['candidate_id'] for x in dm['assignments']] if aggregate else [candidate] if candidate else [])
            if relative.startswith('organizer-private/candidate'):source_candidates=[c['candidate_id'] for c in plan['candidates']]
            lineage=[v for c in source_candidates for v in by_candidate.get(c,[])]
            entry={'path':str(p),'sha256':file_hash(p),'root_scope':alias,'mode':mode,
                   'candidate_id':candidate,'actual_provider_request_or_response':executed,
                   'source_candidate_ids':source_candidates,
                   'language_request_lineage':sorted(lineage,key=lambda x:x['attempt_number']),
                   'generation_procedure_pins_sha256':digest(plan['scientific_source_pins'])}
            mappings.append(entry)
    for relative in plan['scientific_source_pins']:
        path=ROOT/relative
        if file_hash(path)!=plan['scientific_source_pins'][relative]:raise ValueError('executed source modified')
        save_bytes(output/'procedures'/relative,path.read_bytes())
    for relative in ('scripts/simphysqa_formal_live_archive.py','scripts/simphysqa_verify_formal_delivery.py','scripts/simphysqa_formal_dryrun.py',
                     'scripts/simphysqa_formal_readable.py','docs/decisions/SPQ05_authorized_execution.md'):
        save_bytes(output/'procedures'/relative,(ROOT/relative).read_bytes())
    save_bytes(output/'procedures/scripts/simphysqa_formal_blinded_bundle.py',(ROOT/'scripts/simphysqa_formal_blinded_bundle.py').read_bytes())
    index={'version':'SPQ05-executed-provenance/1.0.0','producer_commit':plan['producer_commit'],
           'inherits':{'path':str(previous),'manifest_sha256':file_hash(previous/'manifest.json'),'historical_executed_requests':16},
           'preparation':{'path':str(preparation),'manifest_sha256':file_hash(preparation/'manifest.json'),'prepared_requests':280,'execution_status':'unexecuted_preparations_separate_from_actual_requests'},
           'execution_plan_sha256':digest(plan),'generation_procedure_pins':plan['scientific_source_pins'],
           'delivery_manifest_sha256':file_hash(delivery/'manifest.json'),
           'review_distribution':{'path':str(review_bundle),'manifest_sha256':file_hash(review_bundle/'manifest.json'),
                                  'same140_assignments':True,'new_audit_items':0},
           'actual_annotation_attempts':len(attempts),'actual_annotation_initials':sum(a['initial_request'] for a in attempts.values()),
           'known_returned_provider_requests':sum((run/'annotation/responses'/name).exists() and read(run/'annotation/responses'/name)['raw_response'] is not None for name in attempts),
           'unknown_completion_attempts':sum(not (run/'annotation/responses'/name).exists() for name in attempts),
           'formal_items':len(dm['assignments']),'ratings_collected':0,'answering_model_calls':0,
           'per_file_generation_index':mappings}
    retained(output/'file-generation-index.json',index)
    save_bytes(output/'README.md',('# SPQ05 executed provenance archive\n\nExact actual provider requests/responses are distinct from the280 prepared requests. Every run/delivery file has its saved hash, generation mode, candidate and executed public-language lineage. Deterministic family construction, event wording, answer annotations and focused extraction are not new model calls. Original source releases and sealed SPQ04 archive remain read-only. Generator identity/accounting and private evidence are organizer-only; this archive is not an answering input or blinded reviewer entry point.\n').encode())
    retained(output/'manifest.json',{'version':index['version'],'files':{p.relative_to(output).as_posix():file_hash(p) for p in sorted(output.rglob('*')) if p.is_file() and p.name!='manifest.json'},'index_sha256':digest(index)})
    print(canonical({'indexed_files':len(mappings),'actual_annotation_attempts':len(attempts),'formal_items':len(dm['assignments'])}).decode())

if __name__=='__main__':
    p=argparse.ArgumentParser()
    for key in ('run','delivery','preparation','previous','review-bundle','output'):p.add_argument('--'+key,type=Path,required=True)
    a=p.parse_args();archive(a.run,a.delivery,a.preparation,a.previous,a.review_bundle,a.output)
