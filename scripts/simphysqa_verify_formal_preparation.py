import argparse
from collections import Counter
from pathlib import Path
from simphysqa.io import read, canonical, digest
from simphysqa.formal_sampling import file_hash
from simphysqa.spq01a import retained, verify_manifest
from simphysqa.focused_audit import extract, validate_form

p=argparse.ArgumentParser()
p.add_argument('--root',type=Path,required=True)
p.add_argument('--prior',type=Path,required=True)
a=p.parse_args()
root=a.root
prep=root/'preparation-1.0.1'; check=root/'development-extraction-check-1.0.0'
pm=verify_manifest(prep); cm=verify_manifest(check)
candidates=read(prep/'candidate-order.json')
excluded=set(read(prep/'source-frame-summary.json')['excluded_groups'])
assert len(candidates)==280
assert len({c['source']['sample_id'] for c in candidates})==280
assert len({c['source']['group_id'] for c in candidates})==280
assert not excluded & {c['source']['group_id'] for c in candidates}
assert set(Counter(c['cell'] for c in candidates).values())=={14}
assert set(Counter(c['cell'] for c in candidates if c['role']=='primary').values())=={7}
assert canonical(candidates)==canonical(read(root/'preparation-1.0.0/candidate-order.json'))
focused=read(check/'focused.json')
assert len(focused)==56
states=events=0
for item in focused:
    packet=read(check/item['source_packet'])
    actual=extract(packet,file_hash(check/item['source_packet']),item['source_packet'])
    actual['usage']='excluded_development_extraction_validation_not_formal_sample'
    assert canonical(actual)==canonical(item)
    for state in item['states']:
        source=next(s for s in packet['structured_inputs']['states'] if s['state_id']==state['state_id'])
        for key in ('state_id','timestamp','context','measurements','relations','linked_events'):
            assert canonical(state[key])==canonical(source[key])
        sentence=next(t for t in packet['language_annotations']['timestamps'] if t['state_id']==state['state_id'])
        assert canonical(state['timestamp_language'])==canonical(sentence)
        states+=1; events+=len(state['linked_events'])
    assert 'qa' in item and set(item['qa'])=={'question'}
    assert b'gpt-5.6-sol' not in canonical(item)
    assert 'private' not in item and 'verification' not in item
blanks={}
for reviewer in ('R1','R2','R3'):
    result=validate_form((check/'forms'/f'{reviewer}.csv').read_bytes(),cm['assignments'],reviewer,'development_extraction_check')
    assert result['collected']==0 and result['blank']==56
    blanks[reviewer]=result['blank']
prior_manifests=0; prior_files=0
for stage in ('spq01','spq01a','spq02','spq02b','spq03','spq04'):
    for path in sorted((a.prior/stage).rglob('manifest.json')):
        info=read(path)
        if 'files' in info:
            verify_manifest(path.parent)
            prior_manifests+=1; prior_files+=len(info['files'])
source=read(prep/'source-file-hashes.json')
for name, expected in source.items():assert file_hash(name)==expected
report={'version':'SPQ05-verification/1.0.0','preparation_files':len(pm['files']),
    'source_shards_preserved':len(source),'candidate_groups':280,'primary_groups':140,
    'excluded_groups':len(excluded),'primary_cells':20,'primary_per_cell':7,
    'distinct_same_cell_reserves':140,'candidate_order_preserved_across_resume_fix':True,
    'development_extractions':56,'formal_packets':0,'complete_extraction_states':states,
    'complete_extraction_state_event_links':events,'bindings_resolved':sum(len(x['evidence_resolution']) for x in focused),
    'forms_blank':blanks,'ratings_collected':0,'prior_manifests_preserved':prior_manifests,
    'prior_indexed_file_checks':prior_files,'new_annotation_calls':0,'new_simulations':0,'spend_usd':0,
    'shortfall':140,'protocol_sha256':file_hash(prep/'protocol.json'),
    'preparation_manifest_sha256':file_hash(prep/'manifest.json'),
    'focused_manifest_sha256':file_hash(check/'manifest.json')}
retained(root/'verification.json',report)
print(canonical(report).decode(),end='')
