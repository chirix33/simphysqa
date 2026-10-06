"""Saved SPQ02 checks: integrity, world evidence, typed scoring probes and resume."""
from copy import deepcopy
from hashlib import sha256
from pathlib import Path
from collections import Counter
import argparse
from .io import read,digest,canonical
from .dataset import load,restore,public_record
from .spq01a import verify_manifest,retained
from .spq02_export import export
from .associations import strip_associations
from .scoring import score

def hashes(root):
    return {p.relative_to(root).as_posix():sha256(p.read_bytes()).hexdigest() for p in root.rglob('*') if p.is_file()}

def verify(plan_path,runs,exported,baseline,source,original,output):
    plan=read(plan_path);runtime=verify_manifest(runs);old=verify_manifest(original)
    prior={root:hashes(root) for root in (baseline,source)}
    for root in prior:verify_manifest(root)
    saved_runs=hashes(runs);saved_export=hashes(exported)
    records=list(load(exported/'organizer-private/qa-records.jsonl'))
    checks=[];counts=Counter()
    for r in records:
        p=next(p for p in plan['pairs'] if p['source_wrapper']['sample_id']==r['private']['source_record']['sample_id'])
        if restore(r)!=restore(p['source_wrapper']):raise ValueError('original source was revised')
        view=public_record(r,association_version='simphysqa-associations/1.1.1')
        parent=p['baseline_public_view']
        for key in ('states','known_events','between_state_associations','observation_cutoff','controller','entities','global_context','coordinate_convention'):
            if canonical(view['input'][key])!=canonical(parent['input'][key]):raise ValueError('accepted physical/association baseline changed: '+key)
        if strip_associations(view['input'])!=r['public']['input']:raise ValueError('counterfactual source recovery failed')
        proof=r['private']['counterfactual_evidence'];target=r['public']['input']['answer_spec'][0]
        original_truth=next(t for t in restore(r)['reference']['structured_label'] if t['target_id']==target['target_id'])
        alternative_truth=r['private']['reference']['structured_label'][0]
        changed=canonical(original_truth['value'])!=canonical(alternative_truth['value'])
        counts['readout_changed' if changed else 'readout_unchanged']+=1
        checks.append({'sample_id':r['sample_id'],'pair_id':p['pair_id'],'domain':r['public']['input']['domain'],
            'target':target,'original_value':original_truth['value'],'alternative_value':alternative_truth['value'],
            'target_value_changed':changed,'source_exact':True,'accepted_public_physical_associations_exact':True,
            'alternative_run_id':proof['alternative_run_id'],'binding':r['private']['evidence_bindings'][0],
            'factual_replay':proof['verification']['replay']['passed'],
            'factual_admission':proof['verification']['original_admission'],
            'alternative_admission':proof['verification']['alternative_admission']})
    # Supplied reference values deliberately exercise the scorer, not a model experiment.
    probes=[{'sample_id':r['sample_id'],'condition_id':'SOFTWARE_TEST_ONLY','annotation_version':r['annotation_version'],
             'status':'completed','targets':deepcopy(r['private']['reference']['structured_label'])} for r in records]
    exact=score(records,probes,['SOFTWARE_TEST_ONLY'])
    if not all(i['whole_question_correct'] for i in exact['items']):raise ValueError('typed scorer exact-readout software probe failed')
    missing=score(records,[],['SOFTWARE_TEST_ONLY'])
    if not all(i['status']=='missing' and not i['whole_question_correct'] for i in missing['items']):raise ValueError('missing answers dropped from counterfactual scoring')
    export(plan_path,runs,exported)
    if hashes(exported)!=saved_export or hashes(runs)!=saved_runs:raise ValueError('saved export/resume overwrote completed evidence')
    for root,before in prior.items():
        if hashes(root)!=before:raise ValueError('prior outputs changed')
    if verify_manifest(original)!=old:raise ValueError('original SPQ01 files changed')
    for pair in plan['pairs']:
        for file,expected in pair['source_files'].items():
            if sha256(Path(file).read_bytes()).hexdigest()!=expected:raise ValueError('release source/configuration/partition file changed')
    result={'version':'spq02-saved-verification/1.0.0','kind':'automatic_verification_not_human_assessment',
        'records':len(records),'case_checks':checks,'target_readout_contrasts':dict(counts),
        'saved_run_files':len(saved_runs),'saved_export_files':len(saved_export),
        'resume_all_hashes_unchanged':True,'prior_outputs_preserved':{str(root):len(before) for root,before in prior.items()},
        'SPQ01_indexed_files_verified':len(old['files']),'frozen_plan_sha256':digest(plan),
        'execution_accounting':read(runs/'run-summary.json'),
        'scoring_test_probes_only':{'exact_readout_supported':True,'missing_retained_as_failure':True,'model_calls':0},
        'human_quality':'pending','human_independent_ratings':0,'answering_benchmark':'not_run'}
    retained(output,result)
    print({k:v for k,v in result.items() if k not in ('case_checks','prior_outputs_preserved')})
    return result

if __name__=='__main__':
    p=argparse.ArgumentParser()
    for key in ('plan','runs','export','baseline','source','original','output'):p.add_argument('--'+key,type=Path,required=True)
    a=p.parse_args();verify(a.plan,a.runs,a.export,a.baseline,a.source,a.original,a.output)
