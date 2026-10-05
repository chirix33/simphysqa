"""Prepare eight admitted matched source scenarios, no simulator executions."""
from copy import deepcopy
from pathlib import Path
from hashlib import sha256
import argparse,random
from simphysqa.io import read,write,digest,ROOT,DOMAINS,external
from simphysqa.dataset import load,restore,validate
from simphysqa.spq01a import verify_manifest,retained
from simphysqa.associations import VERSION

def prepare(source,baseline,output,exclusions=None):
    output=external(output)
    verify_manifest(source);verify_manifest(baseline)
    assert read(baseline/'manifest.json')['export_version']==VERSION=='simphysqa-associations/1.1.1'
    records=[r for r in load(source/'qa-records.jsonl') if r['question_type']=='predictive']
    pairs=[];rng=random.Random(20261004)
    for domain in DOMAINS:
        candidates=sorted([r for r in records if r['public']['input']['domain']==domain],key=lambda r:r['trajectory_id'])
        if domain=='object_pushing_stacking':
            buckets={}
            for r in candidates:
                folder=Path(r['source']['path']).parent.parent
                family=next(x['subfamily'] for x in read(folder/'partitions.json') if x['group']==r['trajectory_id'])
                buckets.setdefault(family,[]).append(r)
            chosen=[rng.choice(buckets[k]) for k in sorted(buckets)]
        else:chosen=rng.sample(candidates,2)
        for r in chosen:
            validate(r)
            folder=Path(r['source']['path']).parent.parent
            config=read(folder/'config.json')
            scenario=next(x for x in read(folder/'partitions.json') if x['group']==r['trajectory_id'])
            originals=[read_source for read_source in [__import__('json').loads(line) for line in Path(r['source']['path']).read_text(encoding='utf-8').splitlines()] if read_source['metadata']['base_scenario_id']==r['trajectory_id']]
            sim=r['private']['metadata']['simulation']
            assert digest(config)==sim['config_sha256']
            assert scenario['event_start']>r['public']['input']['observation_cutoff']
            assert restore(r) in originals
            pair_id='spq-cf-'+digest({'version':'omission-pair/1.0.0','group':r['trajectory_id'],'source':r['sample_id']})[:24]
            pairs.append({'pair_id':pair_id,'source_wrapper':r,'source_records':originals,'scenario':scenario,
                'config':config,'original_environment':read(folder/'environment.json'),
                'source_files':{str(p):sha256(p.read_bytes()).hexdigest() for p in (Path(r['source']['path']),folder/'config.json',folder/'partitions.json')},
                'baseline_public_view':read(baseline/'public-items'/(r['sample_id']+'.json'))})
    # One first selected case per domain, then all remaining selected cases.
    pairs=pairs[::2]+pairs[1::2]
    plan={'version':'spq02-plan/1.0.0','base_commit':'e379013b7e80fe28172682cd39e42f4066fde841',
        'selection_rule':'Python Random(20261004), domain order fixed, candidates sorted by trajectory ID; sample two without replacement, object domain one random choice per sorted subfamily; engineering sample, not quality estimation',
        'sampling_seed':20261004,'random_sampling':True,'pairs':pairs,
        'limits':{'maximum_simulation_executions':32,'total_wall_seconds':1800,'per_execution_seconds':180},
        'replay_criterion':{'version':'canonical-exact-replay/1.0.0','status':'proposed_pending_user_confirmation','numeric_tolerance':0,'require_exact_saved_states_events_public_definitions':True,'answer_scoring_not_replay':True},
        'baseline_manifest_sha256':sha256((baseline/'manifest.json').read_bytes()).hexdigest(),
        'baseline_version':VERSION,'model_calls':0}
    retained(output/'plan.json',plan)
    if exclusions is not None:
        selection=read(exclusions)
        excluded=selection['future_formal_excluded_groups']
        if not {p['scenario']['group'] for p in pairs}<=set(excluded):raise ValueError('counterfactual development groups missing from existing fresh-formal exclusions')
        retained(output/'selection-manifest.json',{
            'version':'spq02-frozen-selection/1.0.0','plan_sha256':digest(plan),'selection_seed':plan['sampling_seed'],
            'selection_rule':plan['selection_rule'],'frozen_before_simulator_execution':True,
            'population':'existing sixteen admitted SPQ01 engineering-development train trajectories; not a quality-estimation sample',
            'existing_formal_exclusions_file_sha256':sha256(exclusions.read_bytes()).hexdigest(),
            'future_formal_excluded_groups':excluded,'formal_sample_exported':False,
            'selected':[{'pair_id':p['pair_id'],'domain':p['scenario']['domain'],'group_id':p['scenario']['group'],
                'parent_sample_id':p['source_wrapper']['sample_id'],'split':p['scenario']['split'],'subfamily':p['scenario']['subfamily'],
                'source_record_sha256':p['source_wrapper']['source']['record_sha256'],
                'observation_cutoff':p['source_wrapper']['public']['input']['observation_cutoff'],
                'scheduled_event_id':p['source_wrapper']['public']['input']['known_events'][0]['event_id'],
                'execution_order':i+1,'qualification_order':'one per domain first, then remaining cases'} for i,p in enumerate(pairs)]})
    print({'pairs':len(pairs),'expected_simulations':32,'limits':plan['limits'],'baseline':VERSION})
if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('--source',type=Path,required=True);p.add_argument('--baseline',type=Path,required=True);p.add_argument('--output',type=Path,required=True);p.add_argument('--exclusions',type=Path)
    a=p.parse_args();prepare(a.source,a.baseline,a.output,a.exclusions)
