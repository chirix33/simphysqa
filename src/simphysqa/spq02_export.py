"""Export only qualified pairs, preserving accepted association baseline 1.1.1."""
from pathlib import Path
from hashlib import sha256
from collections import Counter
import argparse
from .io import ROOT,read,write,digest,canonical,manifest
from .spq01a import verify_manifest,retained
from .counterfactual import build
from .dataset import validate,public_record
from .associations import VERSION as ASSOCIATIONS,validate_view as validate_associations
from .audit import export_packets,import_ratings
from .evaluation import export_requests

def export(plan_path,runs,output):
    plan=read(plan_path);records=[];examples={};counts=Counter()
    for index,pair in enumerate(plan['pairs']):
        path=runs/'pairs'/(pair['pair_id']+'.json')
        if not path.exists():counts['pending']+=1;continue
        receipt=read(path);counts[receipt['status']]+=1
        if receipt['status']!='completed':continue
        alternative=read(runs/'alternative-records'/(pair['pair_id']+'.json'))
        if digest(alternative)!=receipt['alternative_sha256']:raise ValueError('qualified alternative record checksum mismatch')
        proofs={'pair_receipt':receipt,'replay':read(runs/'verification'/(pair['pair_id']+'-replay.json')),
                'original_admission':read(runs/'verification'/(pair['pair_id']+'-original-admission.json')),
                'alternative_admission':read(runs/'verification'/(pair['pair_id']+'-alternative-admission.json'))}
        artifacts={}
        for role in ('original-coarse','original-fine','alternative-coarse','alternative-fine'):
            folder=runs/'executions'/(pair['pair_id']+'-'+role)
            result=read(folder/'result.json');reservation=read(folder/'reservation.json')
            if result['status']!='completed' or reservation['scenario_sha256']!=digest(pair['scenario']) or reservation['config_sha256']!=digest(pair['config']) or reservation['omit_scheduled_intervention']!=role.startswith('alternative'):raise ValueError('execution reservation/result mismatched')
            artifacts[role]={'run_id':pair['pair_id']+'-'+role,'result_sha256':sha256((folder/'result.json').read_bytes()).hexdigest(),
                'reservation_sha256':sha256((folder/'reservation.json').read_bytes()).hexdigest(),'integration_timestep_s':reservation['dt'],'wall_seconds':result['wall_seconds']}
        specs=pair['source_wrapper']['public']['input']['answer_spec']
        # One numerical/vector target and one Boolean target per domain.
        target=next(t for t in specs if (t['answer_type']=='boolean')==(index>=4))
        record=build(pair['source_wrapper'],alternative,pair,proofs,artifacts,target)
        validate(record);records.append(record)
        retained(output/'organizer-private/items'/(record['sample_id']+'.json'),record)
        view=public_record(record,association_version=ASSOCIATIONS)
        validate_associations(public_record(record),view)
        retained(output/'public-items'/(record['sample_id']+'.json'),view)
        domain=record['public']['input']['domain']
        examples.setdefault(domain,{'sample_id':record['sample_id'],'pair_id':pair['pair_id'],'public_view':str(output/'public-items'/(record['sample_id']+'.json'))})
    retained(output/'public-qa.json',[public_record(r,association_version=ASSOCIATIONS) for r in records])
    # Private QA records stay separate from the model-visible list.
    path=output/'organizer-private/qa-records.jsonl';data=b''.join(canonical(r) for r in records)
    if path.exists():
        if path.read_bytes()!=data:raise ValueError('retained counterfactual QA changed')
    else:
        path.parent.mkdir(parents=True,exist_ok=True)
        with path.open('xb') as stream:stream.write(data)
    if records:
        packets=output/'audit-development'
        if packets.exists():pm=verify_manifest(packets)
        else:export_packets(records,packets,'development',association_version=ASSOCIATIONS);pm=read(packets/'manifest.json')
        if pm['record_hashes']!={r['sample_id']:digest(r) for r in records}:raise ValueError('audit counterfactual records mismatch')
        plan_eval=read(ROOT/'configs/simphysqa/evaluation.json')
        baseline=output/'public-requests'
        if baseline.exists():verify_manifest(baseline)
        else:export_requests(records,plan_eval,baseline,association_version=ASSOCIATIONS)
        for reviewer in ('R1','R2','R3'):
            result_path=output/'verification'/(reviewer+'-blank-import.json')
            rating=read(result_path) if result_path.exists() else import_ratings(packets,packets/'forms'/(reviewer+'.csv'),result_path)
            if rating['collected'] or rating['blank']!=len(records):raise ValueError('ratings must remain independent and blank')
        for entry in pm['assignments']:
            r=next(r for r in records if r['sample_id']==entry['sample_id'])
            packet=read(packets/'packets'/(entry['packet_id']+'.json'))
            if packet['structured_inputs']!=public_record(r,association_version=ASSOCIATIONS)['input'] or 'paired_counterfactual' not in packet['verification']:raise ValueError('public/private audit packet inconsistency')
            if 'gpt-5.6-sol' in canonical(packet).decode():raise ValueError('annotation identity not blinded')
            domain=r['public']['input']['domain']
            if examples[domain]['sample_id']==r['sample_id']:examples[domain]['audit_packet']=str(packets/'packets'/(entry['packet_id']+'.html'))
        expected={r['sample_id']:public_record(r,association_version=ASSOCIATIONS) for r in records}
        from .io import parse
        for condition in plan_eval['conditions']:
            for request in read(baseline/(condition['condition_id']+'.json')):
                if request['tools'] or parse(request['messages'][0]['content'].split('\n',1)[1])!=expected[request['sample_id']]:raise ValueError('baseline view leaked or changed counterfactual inputs')
    retained(output/'examples.json',examples)
    summary={'version':'spq02-export/1.0.0','association_export_version':ASSOCIATIONS,'qa_records':len(records),'completed_pairs':counts['completed'],'failed_pairs':counts['failed'],'pending_pairs':counts['pending'],
        'prepared_public_requests':len(records)*9,'answer_types':dict(Counter(r['public']['input']['answer_spec'][0]['answer_type'] for r in records)),
        'answering_model_evaluation':'pending_not_run','human_assessment':'pending','independent_ratings':0,'new_model_calls':0,
        'scoring':'existing typed numerical/vector/Boolean readout scorer with counterfactual family validation; answer tolerances preserved, distinct from replay/admission'}
    retained(output/'verification/checks.json',summary)
    if not (output/'manifest.json').exists():manifest(output,{'purpose':'SPQ02_qualified_counterfactual_development','plan_sha256':digest(plan),'run_summary_sha256':digest(read(runs/'run-summary.json')),'checks':summary})
    else:verify_manifest(output)
    print(summary);return summary
if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('--plan',type=Path,required=True);p.add_argument('--runs',type=Path,required=True);p.add_argument('--output',type=Path,required=True)
    a=p.parse_args();export(a.plan,a.runs,a.output)
