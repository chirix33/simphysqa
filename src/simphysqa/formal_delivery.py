"""SPQ05 blinded packets, focused primary entry and immutable final identities."""
import argparse
from collections import Counter
from copy import deepcopy
from html import escape
from pathlib import Path
import subprocess

from .io import ROOT, DOMAINS, QUESTION_TYPES, canonical, digest, read, external
from .formal_sampling import file_hash, save_bytes
from .formal_scope import formal_scope
from .formal_live import annotation_ledger, simulation_wall, LIMITS, SIM_LIMITS
from .spq01a import retained, verify_manifest
from .focused_audit import extract, blank_forms, validate_form, CRITERIA

VERSION='SPQ05-formal-delivery/1.0.0'


def packet_for(record):
    from .dataset import validate, public_record
    from .answer_annotations import enriched_reference, roots
    validate(record)
    view=public_record(record,association_version='simphysqa-associations/1.1.1')
    packet_id='SPQ-'+digest({'phase':'formal','record_sha256':digest(record),
                             'export_version':view['export_version'],'delivery_version':VERSION})[:16]
    packet={'packet_id':packet_id,'phase':'formal','sample_id':record['sample_id'],
            'annotation_version':record['annotation_version'],'question_type':record['question_type'],
            'structured_inputs':view['input'],'language_annotations':view['annotations'],
            'qa':{'question':record['public']['input']['question'],'reference':enriched_reference(record)},
            'verification':{'metadata':record['private']['metadata'],'bindings':record['private']['evidence_bindings']},
            'annotation_completion':record['completion'],'rubric_version':'SPQ05-focused-rubric/1.0.0',
            'export_version':view['export_version'],'association_provenance':view['association_provenance']}
    if 'answer_annotation' in record['private']:
        annotation=record['private']['answer_annotation']
        packet['answer_annotation']=annotation
        packet['verification']['answer_evidence_roots']=roots(record,annotation['evidence_context'])
    if record['question_type']=='counterfactual':
        proof=record['private']['counterfactual_evidence']
        packet['verification']['paired_counterfactual']=deepcopy(proof)
    if record['question_type']=='explanation':
        from .explanation import evidence_roots
        packet['explanation_annotation']=record['private']['explanation_annotation']
        packet['verification']['answer_evidence_roots']=evidence_roots(record)
    if record['question_type']=='clarification':
        from .clarification import roots as clarification_roots
        packet['clarification_annotation']=record['private']['clarification_annotation']
        packet['two_stage_task']={'initial_view':record['private']['initial_view'],
            'reference_clarification_question':record['private']['reference']['reference_clarification_question'],
            'reference_question_origin':'authored_reference_not_actual_model_response',
            'recorded_reply':record['private']['resolved_view']['input']['recorded_reply'],
            'resolved_view':record['private']['resolved_view']}
        packet['verification']['answer_evidence_roots']=clarification_roots(record)
        packet['verification']['private_gap_witnesses']=record['private']['reference']['witnesses']
    # Organizer-only model identity and execution request lineage never enter packets.
    if b'gpt-5.6-sol' in canonical(packet) or b'annotation_provenance' in canonical(packet):
        raise ValueError('generator identity leaked into blinded packet')
    return packet,view


def render_item(out):
    body='<h1>'+escape(out['packet_id'])+'</h1><p>'+escape(out['domain']+' / '+out['question_type'])+'</p>'
    body+='<h2>Question</h2><p>'+escape(out['qa']['question'])+'</p>'
    for title,key in (('Physical/global context','structured_inputs'),('Observed trajectory language','language_annotations'),
                       ('States, generated timestamp language and linked events','states'),('Declared schedule/controller evidence','evidence')):
        body+='<h2>'+title+'</h2><pre>'+escape(canonical(out[key]).decode())+'</pre>'
    if 'clarification' in out:
        body+='<h2>Initial view, authored clarification, recorded reply and resolved view</h2><p>Authored reference turns; no answering-model conversation was executed.</p><pre>'+escape(canonical(out['clarification']).decode())+'</pre>'
    body+='<p><a href="../'+escape(out['source_packet'])+'">Auditor-only gold and extra verification (outside primary rating scope)</a></p>'
    return ('<!doctype html><meta charset="utf-8"><title>'+out['packet_id']+'</title><style>body{max-width:1100px;margin:2em auto;font:16px system-ui}pre{white-space:pre-wrap;overflow-wrap:anywhere}</style>'+body).encode()


def export(run, output):
    run=external(run);output=external(output);plan=read(run/'execution-plan.json')
    if output==run or run in output.parents:raise ValueError('delivery root must be separate from mutable execution root')
    assignments=[];focused=[];records=[];keys=[];ledger=[];links=[];counts=Counter();examples={}
    with formal_scope(plan['candidates'],plan['excluded_groups']):
        for candidate in plan['candidates']:
            case=run/'cases'/candidate['candidate_id']; status_path=case/'status.json'
            status=read(status_path) if status_path.exists() else None
            attempts=[a for a in annotation_ledger(run) if a['candidate_id']==candidate['candidate_id']]
            entry={**deepcopy(candidate),'processing':status,
                   'annotation_attempt_numbers':[a['attempt_number'] for a in attempts],
                   'annotation_accounting':attempts,
                   'simulation_executions':[{'path':str(p),'reservation':read(p),'result':read(p.with_name('result.json')) if p.with_name('result.json').exists() else None}
                       for p in sorted((case/'runs/executions').glob('*/reservation.json'))],
                   'clarification_eligibility':read(case/'clarification-eligibility.json') if (case/'clarification-eligibility.json').exists() else None}
            if status is None:
                entry['disposition']='unused_reserve_cell_filled' if counts[candidate['cell']]==7 else 'unprocessed_after_stop'
            elif status['status']!='completed':entry['disposition']='retained_rejection'
            else:
                entry['disposition']='qualified_selected'
                counts[candidate['cell']]+=1
                record=read(case/'record.json')
                if digest(record)!=status['record_sha256']:raise ValueError('saved status/record mismatch')
                from .dataset import restore
                if digest(restore(record))!=candidate['source']['source']['record_sha256']:raise ValueError('source restoration differs')
                packet,view=packet_for(record)
                ph=digest(packet);pid=packet['packet_id']
                out=extract(packet,ph,'auditor-only/'+pid+'.json')
                if out['missing_required_fields'] or out['validation_errors']:raise ValueError('focused extraction incomplete:'+pid)
                save_bytes(output/'auditor-only'/(pid+'.json'),canonical(packet))
                save_bytes(output/'auditor-only'/(pid+'.html'),('<!doctype html><meta charset="utf-8"><h1>Auditor-only extra evidence</h1><p>Outside primary rating scope. Human unreviewed. Generator blinded.</p><pre style="white-space:pre-wrap;overflow-wrap:anywhere">'+escape(canonical(packet).decode())+'</pre>').encode())
                save_bytes(output/'public-items'/(record['sample_id']+'.json'),canonical(view))
                retained(output/'focused-items'/(pid+'.json'),out)
                save_bytes(output/'focused-items'/(pid+'.html'),render_item(out))
                assignments.append({'packet_id':pid,'sample_id':record['sample_id'],'packet_sha256':ph,
                                    'domain':candidate['domain'],'question_type':candidate['question_type'],
                                    'group_id':candidate['source']['group_id'],'split':candidate['source']['split'],
                                    'candidate_id':candidate['candidate_id'],'source_sample_id':candidate['source']['sample_id'],
                                    'source_record_sha256':candidate['source']['source']['record_sha256'],
                                    'record_sha256':digest(record),'public_view_sha256':digest(view),'phase':'formal'})
                focused.append(out);records.append(record)
                keys.append({'packet_id':pid,'source':record['source'],'candidate_id':candidate['candidate_id'],
                             'annotation_provenance':record['private']['annotation_provenance']})
                links.append('<li><a href="focused-items/'+pid+'.html">'+escape(candidate['cell']+' / '+pid)+'</a></li>')
                examples.setdefault(candidate['cell'],{'packet_id':pid,'focused':str(output/'focused-items'/(pid+'.html')),
                                                      'private_packet':str(output/'auditor-only'/(pid+'.json'))})
            ledger.append(entry)
        # Explicit failed-primary -> selected-reserve links, never replacing ledger records.
        replacements=[]
        for domain in DOMAINS:
            for family in QUESTION_TYPES:
                cell=domain+'/'+family
                failed=[e['candidate_id'] for e in ledger if e['cell']==cell and e['role']=='primary' and e['disposition']=='retained_rejection']
                selected=[e['candidate_id'] for e in ledger if e['cell']==cell and e['role']=='reserve' and e['disposition']=='qualified_selected']
                replacements.extend({'cell':cell,'rejected_primary':a,'selected_reserve':b,'rule':'next qualified same-stratum candidate in frozen order'} for a,b in zip(failed,selected))
    complete=len(assignments)==140 and all(counts[d+'/'+q]==7 for d in DOMAINS for q in QUESTION_TYPES)
    if len({a['sample_id'] for a in assignments})!=len(assignments) or len({a['group_id'] for a in assignments})!=len(assignments):raise ValueError('sample/group duplication')
    if set(plan['excluded_groups']) & {a['group_id'] for a in assignments}:raise ValueError('excluded group selected')
    retained(output/'focused.json',focused);save_bytes(output/'focused.jsonl',b''.join(canonical(r) for r in focused))
    retained(output/'organizer-private/identity-key.json',keys)
    save_bytes(output/'organizer-private/qa-records.jsonl',b''.join(canonical(r) for r in records))
    retained(output/'organizer-private/candidate-eligibility-failure-ledger.json',ledger)
    save_bytes(output/'organizer-private/candidate-ledger.jsonl',b''.join(canonical(e) for e in ledger))
    retained(output/'organizer-private/replacements.json',replacements)
    clarification=[e for e in ledger if e['question_type']=='clarification']
    retained(output/'organizer-private/clarification-attrition.json',{'candidates':56,'processed':sum(e['processing'] is not None for e in clarification),
             'qualified':sum(e['disposition']=='qualified_selected' for e in clarification),
             'rejected_by_stage':dict(Counter(e['processing']['stage'] for e in clarification if e['disposition']=='retained_rejection')),
             'entries':[{'candidate_id':e['candidate_id'],'disposition':e['disposition'],'processing':e['processing'],'selection':e['clarification_eligibility']} for e in clarification]})
    for relative,name in (('docs/simphysqa/formal_reviewer_guide.md','reviewer-guide.md'),('docs/simphysqa/formal_analysis.md','analysis-specification.md'),
                           ('docs/simphysqa/formal_protocol.md','protocol.md'),('docs/simphysqa/formal_execution.md','authorized-execution.md')):
        save_bytes(output/name,(ROOT/relative).read_bytes())
    retained(output/'execution-plan.json',plan)
    if complete:
        for reviewer,data in blank_forms(assignments,'formal').items():
            save_bytes(output/'forms'/(reviewer+'.csv'),data)
            checked=validate_form(data,assignments,reviewer,'formal')
            if checked['collected'] or checked['blank']!=140:raise ValueError('form not blank/identical140')
    history=annotation_ledger(run)
    summary={'version':VERSION,'status':'ready_for_independent_human_review' if complete else 'honest_shortfall_do_not_begin_formal_review',
             'target_items':140,'qualified_items':len(assignments),'shortfall':140-len(assignments),'allocation':dict(counts),
             'final_identity_frozen':complete,'ratings_collected':0,'expected_individual_ratings':420 if complete else None,
             'initial_requests':sum(a['initial_request'] for a in history),'annotation_attempts':len(history),
             'repairs':sum(a['repair'] for a in history),'charged_usd':sum(a['charged_upper_bound_usd'] for a in history),
             'known_usage_usd':sum(a['recorded_cost_usd'] or 0 for a in history),
             'reserved_input_tokens':sum(a['reservation']['input_token_upper_bound'] for a in history),
             'reserved_output_tokens':sum(a['reservation']['output_token_limit'] for a in history),
             'actual_input_tokens':sum(a.get('usage',{}).get('input_tokens',0) for a in history),
             'actual_output_tokens':sum(a.get('usage',{}).get('output_tokens',0) for a in history),
             'annotation_work_seconds':sum(a['wall_seconds'] for a in history),'simulation_work_seconds':simulation_wall(run),
             'simulation_executions':len(list((run/'cases').glob('*/runs/executions/*/reservation.json'))),
             'static_model_compilations':sum(read(p).get('model_compilations',0) for p in (run/'simulation-work').glob('*.json')),
             'answering_model_requests':0,'annotation_limits':LIMITS,'simulation_limits':SIM_LIMITS,'examples':examples,
             'processing_summaries':[read(p) for p in sorted((run/'summaries').glob('*.json'))]}
    retained(output/'completion.json',summary)
    retained(output/'final-140-manifest.json' if complete else output/'shortfall.json',{'version':VERSION,**summary,'assignments':assignments})
    save_bytes(output/'rating-import-commands.txt',('Use the CPU environment with PYTHONPATH=src from the worktree. After independent submission, validate/import each original separately:\n'+
        '\n'.join('python -m simphysqa.focused_audit import-ratings --packets "'+str(output)+'" --form "<submitted-'+r+'.csv>" --reviewer '+r+' --output "<new-external-submissions-root>"' for r in ('R1','R2','R3'))+
        '\nNo output argument validates only. Blank forms are uncollected and cannot be imported as submissions. Discussion, adjudication and corrections go into separate new tables/versions; do not edit these files.\n').encode())
    intro='140 frozen distinct QA; identical blank R1/R2/R3 forms; 420 uncollected ratings.' if complete else str(len(assignments))+'/140 qualified QA. Shortfall: formal review cannot begin; no final forms claimed.'
    save_bytes(output/'index.html',('<!doctype html><meta charset="utf-8"><title>SPQ05 focused audit</title><h1>SPQ05 focused human audit</h1><p>'+intro+'</p><p>Rate global physical context, observed trajectory language, question/type, generated timestamp language and state-event descriptions. Gold/trace/private outcomes are separate optional corroboration. Generator identity blinded. Pooled results concern this balanced design, not the natural record-weighted release; seven per cell do not power subgroup claims.</p><p><a href="reviewer-guide.md">Reviewer guide</a> · <a href="analysis-specification.md">Analysis specification</a> · <a href="protocol.md">Protocol</a> · <a href="completion.json">Accounting/status</a></p>'+('<p><a href="forms/R1.csv">R1 form</a> · <a href="forms/R2.csv">R2 form</a> · <a href="forms/R3.csv">R3 form</a></p>' if complete else '')+'<ul>'+''.join(links)+'</ul>').encode())
    producer=(read(output/'manifest.json')['producer_commit'] if (output/'manifest.json').exists() else subprocess.check_output(['git','rev-parse','HEAD'],cwd=ROOT,text=True).strip())
    files={p.relative_to(output).as_posix():file_hash(p) for p in sorted(output.rglob('*')) if p.is_file() and p.name!='manifest.json'}
    retained(output/'manifest.json',{'version':VERSION,'producer_commit':producer,'phase':'formal' if complete else 'shortfall',
             'final_identity_frozen':complete,'assignments':assignments,'files':files,'execution_plan_sha256':digest(plan),
             'ratings_status':'blank_not_collected','reviewer_slots':['R1','R2','R3']})
    verify_manifest(output)
    print(canonical({k:v for k,v in summary.items() if k not in ('examples','processing_summaries')}).decode(),flush=True)
    return summary


def main():
    p=argparse.ArgumentParser();p.add_argument('--run',type=Path,required=True);p.add_argument('--output',type=Path,required=True)
    a=p.parse_args();export(a.run,a.output)

if __name__=='__main__':main()
