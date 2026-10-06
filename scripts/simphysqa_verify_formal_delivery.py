"""Independent saved-output checks for SPQ05; no provider or solves."""
import argparse
from collections import Counter
from pathlib import Path
from simphysqa.io import canonical,digest,read
from simphysqa.formal_live import execution_plan,annotation_ledger,LIMITS,SIM_LIMITS,simulation_wall
from simphysqa.formal_scope import formal_scope
from simphysqa.formal_delivery import packet_for
from simphysqa.formal_sampling import source_record,file_hash
from simphysqa.focused_audit import extract,validate_form
from simphysqa.spq01a import verify_manifest,retained
from simphysqa.dataset import validate,restore,public_record,pointer

p=argparse.ArgumentParser()
for key in ('run','delivery','preparation','prior','output'):p.add_argument('--'+key,type=Path,required=True)
a=p.parse_args();dm=verify_manifest(a.delivery);prep=verify_manifest(a.preparation);plan=execution_plan(a.run)
assert digest(plan['candidates'])==plan['candidate_order_sha256']
assert canonical(plan['candidates'])==canonical(read(a.preparation/'candidate-order.json'))
assert plan['simulation_limits']==SIM_LIMITS and plan['provider_config']['budget']==LIMITS
excluded=set(read(a.preparation/'source-frame-summary.json')['excluded_groups'])
assert set(plan['excluded_groups'])==excluded
assert len(plan['candidates'])==280 and len({c['source']['group_id'] for c in plan['candidates']})==280
assert not excluded & {c['source']['group_id'] for c in plan['candidates']}
assignments=dm['assignments'];focused=read(a.delivery/'focused.json');assert len(focused)==len(assignments)
assert len({x['sample_id'] for x in assignments})==len(assignments)
assert len({x['group_id'] for x in assignments})==len(assignments)
assert not excluded & {x['group_id'] for x in assignments}
index={c['candidate_id']:c for c in plan['candidates']};states=events=resolved=0;privatebindings=0;pairs=0
relationships=Counter();description_statuses=Counter();zero_event_states=0
with formal_scope(plan['candidates'],plan['excluded_groups']):
    for assignment,out in zip(assignments,focused):
        candidate=index[assignment['candidate_id']];case=a.run/'cases'/candidate['candidate_id']
        record=read(case/'record.json');validate(record)
        source=source_record(candidate['source'])
        assert canonical(restore(record))==canonical(restore(source))
        assert assignment['record_sha256']==digest(record)
        view=public_record(record,association_version='simphysqa-associations/1.1.1')
        assert canonical(view)==canonical(read(a.delivery/'public-items'/(record['sample_id']+'.json')))
        packet,regenerated_view=packet_for(record)
        saved=a.delivery/'auditor-only'/(assignment['packet_id']+'.json')
        assert canonical(packet)==saved.read_bytes() and file_hash(saved)==assignment['packet_sha256']
        actual=extract(packet,file_hash(saved),'auditor-only/'+saved.name)
        assert canonical(actual)==canonical(out)
        assert actual['missing_required_fields']==[] and actual['validation_errors']==[]
        for s in out['states']:
            original=next(v for v in packet['structured_inputs']['states'] if v['state_id']==s['state_id'])
            for key in ('state_id','timestamp','context','measurements','relations','linked_events'):assert canonical(s[key])==canonical(original[key])
            timestamp=next(t for t in packet['language_annotations']['timestamps'] if t['state_id']==s['state_id'])
            assert canonical(s['timestamp_language'])==canonical(timestamp)
            assert s['timestamp']<=out['evidence']['observation_cutoff']
            states+=1;events+=len(s['linked_events'])
            zero_event_states+=not s['linked_events']
            relationships.update(e['temporal_relationship'] for e in s['linked_events'])
            description_statuses.update(e['event_description_status'] for e in s['linked_events'])
        resolved+=len(out['evidence_resolution'])
        assert set(out['qa'])=={'question'} and 'verification' not in out and 'private' not in out
        assert b'gpt-5.6-sol' not in canonical(packet) and b'annotation_provenance' not in canonical(packet)
        # Public views are exactly the validated projection; gold, witnesses and accounting stay private.
        def forbidden(value):
            if isinstance(value,dict):
                assert not {'private','reference','solution_trace','witnesses','annotation_provenance','recorded_cost_usd','OPENAI_API_KEY'} & set(value)
                for v in value.values():forbidden(v)
            elif isinstance(value,list):
                for v in value:forbidden(v)
        forbidden(view)
        root=packet['verification'].get('answer_evidence_roots',{})
        def bindings(obj):
            global privatebindings
            if isinstance(obj,dict):
                if set(('namespace','pointer','value_sha256'))<=set(obj):
                    assert digest(pointer(root[obj['namespace']],obj['pointer']))==obj['value_sha256'];privatebindings+=1
                else:
                    for v in obj.values():bindings(v)
            elif isinstance(obj,list):
                for v in obj:bindings(v)
        for key in ('qa','answer_annotation','explanation_annotation','clarification_annotation'):
            if key in packet:bindings(packet[key])
        if (case/'runs/manifest.json').exists():verify_manifest(case/'runs');pairs+=1
# Every source shard and every historical manifest remains unchanged.
sourcehashes=read(a.preparation/'source-file-hashes.json')
for name,value in sourcehashes.items():assert file_hash(name)==value
prior_count=prior_files=0
for phase in ('spq01','spq01a','spq02','spq02b','spq03','spq04'):
    for manifest in sorted((a.prior/phase).rglob('manifest.json')):
        if 'files' in read(manifest):info=verify_manifest(manifest.parent);prior_count+=1;prior_files+=len(info['files'])
forms={}
if dm.get('final_identity_frozen'):
    assert len(assignments)==140
    assert set(Counter(x['domain']+'/'+x['question_type'] for x in assignments).values())=={7}
    for r in ('R1','R2','R3'):
        checked=validate_form((a.delivery/'forms'/(r+'.csv')).read_bytes(),assignments,r,'formal')
        assert checked['collected']==0 and checked['blank']==140;forms[r]=checked['blank']
history=annotation_ledger(a.run)
assert len(history)<=560 and sum(h['initial_request'] for h in history)<=280
assert max(Counter(h['candidate_id'] for h in history).values(),default=0)<=2
assert sum(h['charged_upper_bound_usd'] for h in history)<=125
assert sum(h['reservation']['input_token_upper_bound'] for h in history)<=7000000
assert sum(h['reservation']['output_token_limit'] for h in history)<=1146880
assert sum(h['wall_seconds'] for h in history)<=7200
assert simulation_wall(a.run)<=3600
solves=len(list((a.run/'cases').glob('*/runs/executions/*/reservation.json')));assert solves<=672
# Order and reserve discipline: every cell keeps the first seven qualifying saved statuses.
for cell in {c['cell'] for c in plan['candidates']}:
    selected=[x['candidate_id'] for x in assignments if x['domain']+'/'+x['question_type']==cell]
    qualified=[c['candidate_id'] for c in plan['candidates'] if c['cell']==cell and (a.run/'cases'/c['candidate_id']/'status.json').exists() and read(a.run/'cases'/c['candidate_id']/'status.json')['status']=='completed']
    assert selected==qualified[:7]
report={'version':'SPQ05-saved-delivery-verification/1.0.0','formal_items':len(assignments),'final_identity_frozen':dm.get('final_identity_frozen'),
        'unique_sample_and_groups':True,'exclusions_verified':len(excluded),'candidate_order_unchanged':True,
        'extraction_states':states,'extraction_state_event_links':events,'public_bindings_resolved':resolved,
        'temporal_relationship_counts':dict(relationships),'description_status_counts':dict(description_statuses),
        'states_without_linked_events_retained':zero_event_states,
        'private_answer_trace_bindings_resolved':privatebindings,'qualified_paired_receipts':pairs,
        'source_shards_preserved':len(sourcehashes),'prior_manifests_preserved':prior_count,'prior_indexed_file_checks':prior_files,
        'blank_per_reviewer':forms,'ratings_collected':0,'within_all_authorized_ceilings':True,
        'annotation_attempts_including_unknown':len(history),'unknown_attempts':sum(h['status']=='interrupted_unknown_reserved' for h in history),
        'simulation_executions':solves,'delivery_manifest_sha256':file_hash(a.delivery/'manifest.json')}
retained(a.output,report);print(canonical(report).decode())
