"""Verified omission QA: original public world, private matched alternative truth."""
from copy import deepcopy
from .io import canonical,digest
from .event_language import render,measurement_base,validate_view
from .dataset import restore
from phi_jepa.simulation.validation import validate as validate_source
from phi_jepa.simulation.records import answer_text

VERSION='matched-omission-qa/1.0.0'

OMISSION_SEMANTICS={
    'robotic_arm':'Skip only the additional +0.5 N m increment to qfrc_applied[0] on joint_1 during the scheduled half-open pulse. Retain both base generalized joint torques. The scalar pulse and base torque use the same hinge DOF; the raw world event tag is a source-constructor default, with no Cartesian frame conversion implemented.',
    'driving':'Skip the scheduled wheel velocity-control brake command (zero target wheel velocity, maximum motor torque 0.25 N m per wheel). This is a motor torque limit, not a measured realized braking torque; retain initial wheel/car motion, friction, other controls and numerical settings.',
    'object_pushing_stacking':'Skip only the scheduled world-x external force on block_1, applied at its base position during the declared half-open interval. Retain gravity, collisions, initial conditions and all other physical parameters.',
    'tethered_load':'Disable the complete scheduled support-motion program by using zero motion amplitude at every evaluation, including the positive and negative acceleration phases and subsequent prescribed support displacement. Retain the pendulum dynamics, cable length, mass, initial state and numerical settings.'}

def public_input(source,pair_id,target):
    inp=deepcopy(source['input'])
    if len(inp['known_events'])!=1:raise ValueError('omission QA needs exactly one identified scheduled intervention')
    event=inp['known_events'][0]
    if event['type']!='scheduled_intervention' or event['start_time']<=inp['observation_cutoff'] or target['end_time']<=event['start_time'] or target not in inp['answer_spec']:
        raise ValueError('omission QA needs one post-observation intervention and an existing later target')
    inp['answer_spec']=[deepcopy(target)]
    inp['task_type']='counterfactual_state_prediction'
    inp['question']=f"If scheduled intervention {event['event_id']} were omitted while all initial conditions, physical parameters, other controls and execution settings stayed fixed, what would {target['entity_id']} {target['quantity']} be at {target['end_time']:g} s ({target['unit']}, frame {target['frame']})?"
    inp['counterfactual']={'version':VERSION,'pair_id':pair_id,'parent_sample_id':source['sample_id'],
        'operation':'omit_scheduled_intervention','omitted_event_ids':[event['event_id']],
        'public_world':'Original observed scenario and declared schedule; disable only the identified intervention for this question. Event annotations describe the original schedule, not an alternative outcome.'}
    return inp

def build(parent,alternative,pair,verification,artifacts,target):
    source=restore(parent)
    validate_source(alternative,admission=True)
    record=deepcopy(parent)
    record.update(schema_version='simphysqa/0.3.0',question_type='counterfactual')
    record['sample_id']='spq-counterfactual-'+digest({'version':VERSION,'pair_id':pair['pair_id'],'target':target})[:24]
    record['public']['input']=public_input(source,pair['pair_id'],target)
    record['public']['annotations']=render(record['public']['input'],measurement_base(parent['public']['annotations']))
    evidence={'version':VERSION,'pair_id':pair['pair_id'],'source_annotations':deepcopy(parent['public']['annotations']),
        'alternative_run_id':pair['pair_id']+'-alternative-coarse','original_run_id':pair['pair_id']+'-original-coarse',
        'alternative_record':deepcopy(alternative),'verification':deepcopy(verification),'simulation_artifacts':artifacts,
        'intervention_change':{'changed_execution_field':'omit_scheduled_intervention','original':False,'alternative':True,
            'scenario_sha256':digest(pair['scenario']),'config_sha256':digest(pair['config']),
            'original_scenario':deepcopy(pair['scenario']),'original_config':deepcopy(pair['config']),
            'execution_semantics':OMISSION_SEMANTICS[source['input']['domain']],
            'omitted_event_id':source['input']['known_events'][0]['event_id'],'other_scenario_and_execution_settings':'identical at each matched timestep'}}
    record['private']['source_record']=deepcopy(source)
    record['private']['counterfactual_evidence']=evidence
    ref=deepcopy(alternative['reference'])
    ref['structured_label']=[v for v in ref['structured_label'] if v['target_id']==target['target_id']]
    ref['label']=answer_text([target],ref['structured_label'])
    record['private']['reference']=ref
    record['private']['metadata']=deepcopy(alternative['metadata'])
    terminal=next(s for s in ref['states'] if s['timestamp']==target['end_time'])
    record['private']['evidence_bindings']=[{'target_id':target['target_id'],'kind':'matched_alternative_readout',
        'state_ids':[terminal['state_id']],'event_ids':[],'evidence_ids':[e['evidence_id'] for e in ref['evidence'] if terminal['state_id'] in e['state_ids']],
        'alternative_run_id':evidence['alternative_run_id']}]
    record['completion']['counterfactual_qa']='verified_matched_omission'
    validate_counterfactual(record)
    return record

def validate_counterfactual(record):
    if record['question_type']!='counterfactual' or record['schema_version']!='simphysqa/0.3.0':raise ValueError('counterfactual family/version mismatch')
    private=record['private'];source=private['source_record'];proof=private['counterfactual_evidence'];alternative=proof['alternative_record']
    validate_source(source,admission=True);validate_source(alternative,admission=True)
    if record['source']['record_sha256']!=digest(source) or record['trajectory_id']!=source['metadata']['base_scenario_id'] or record['trajectory_id']!=alternative['metadata']['base_scenario_id']:raise ValueError('counterfactual parent/group lineage changed')
    if proof['version']!=VERSION or not proof['verification']['replay']['passed'] or not proof['verification']['original_admission']['refinement']['passed'] or not proof['verification']['original_admission']['domain_physics'] or not proof['verification']['alternative_admission']['refinement']['passed'] or not proof['verification']['alternative_admission']['domain_physics']:raise ValueError('counterfactual replay/admission not qualified')
    criterion=proof['verification']['replay']['criterion']
    if criterion['status']!='approved' or criterion['version']!='canonical-exact-replay/1.0.0' or criterion['numeric_tolerance']!=0:raise ValueError('unresolved or altered original replay criterion')
    receipt=proof['verification']['pair_receipt']
    if receipt['status']!='completed' or not receipt['qualified'] or receipt['pair_id']!=proof['pair_id'] or receipt['alternative_sha256']!=digest(alternative):raise ValueError('counterfactual alternative differs from qualified run receipt')
    original_sim=source['metadata']['simulation'];alt_sim=alternative['metadata']['simulation']
    for key in ('seed','integration_timestep_s','saved_state_interval_s','duration_s','solver_settings','assets','dtype','engine','engine_version'):
        if canonical(original_sim[key])!=canonical(alt_sim[key]):raise ValueError('counterfactual execution settings changed: '+key)
    if canonical(source['input']['states'])!=canonical(alternative['input']['states']) or alternative['input']['known_events'] or any(e['type']=='applied_intervention' for e in alternative['reference']['events']):raise ValueError('alternative prefix/omission mismatch')
    for key in ('controls','parameters','equations','mode','initial_internal_state','update_interval_s'):
        if canonical(alternative['input']['controller'][key])!=canonical(source['input']['controller'][key]):raise ValueError('alternative remaining physical controls changed')
    for key in ('entities','global_context','coordinate_convention','answer_spec','observation_cutoff'):
        if canonical(alternative['input'][key])!=canonical(source['input'][key]):raise ValueError('alternative physical prior or target/cutoff changed')
    if len(record['public']['input']['answer_spec'])!=1:raise ValueError('one supported counterfactual target per pair required')
    target=record['public']['input']['answer_spec'][0]
    if target not in source['input']['answer_spec']:raise ValueError('counterfactual target/time not in original source specification')
    inp=public_input(source,proof['pair_id'],target)
    if canonical(inp)!=canonical(record['public']['input']):raise ValueError('counterfactual public projection changed or leaked private outcomes')
    expected_id='spq-counterfactual-'+digest({'version':VERSION,'pair_id':proof['pair_id'],'target':target})[:24]
    if record['sample_id']!=expected_id:raise ValueError('counterfactual QA identity changed')
    if proof['original_run_id']!=proof['pair_id']+'-original-coarse' or proof['alternative_run_id']!=proof['pair_id']+'-alternative-coarse':raise ValueError('counterfactual run identity changed')
    change=proof['intervention_change']
    if change['changed_execution_field']!='omit_scheduled_intervention' or change['original'] is not False or change['alternative'] is not True or change['omitted_event_id']!=source['input']['known_events'][0]['event_id']:raise ValueError('invalid intervention difference')
    if change['execution_semantics']!=OMISSION_SEMANTICS[source['input']['domain']]:raise ValueError('omission controller semantics changed')
    if digest(change['original_scenario'])!=change['scenario_sha256'] or digest(change['original_config'])!=change['config_sha256'] or change['config_sha256']!=original_sim['config_sha256'] or change['original_scenario']['group']!=record['trajectory_id']:raise ValueError('matched scenario/configuration provenance differs')
    artifacts=proof['simulation_artifacts']
    roles=('original-coarse','original-fine','alternative-coarse','alternative-fine')
    if set(artifacts)!=set(roles):raise ValueError('all four real replay/refinement execution artifacts required')
    for role,item in artifacts.items():
        expected_dt=original_sim['integration_timestep_s']/(2 if role.endswith('fine') else 1)
        if item['run_id']!=proof['pair_id']+'-'+role or item['integration_timestep_s']!=expected_dt or item['wall_seconds']<0:raise ValueError('execution artifact identity/timestep differs')
    expected=deepcopy(alternative['reference']);expected['structured_label']=[v for v in expected['structured_label'] if v['target_id']==target['target_id']]
    expected['label']=answer_text([target],expected['structured_label'])
    if canonical(expected)!=canonical(private['reference']) or canonical(private['metadata'])!=canonical(alternative['metadata']):raise ValueError('counterfactual answer/reference not exact alternative readout')
    terminal=next(s for s in expected['states'] if s['timestamp']==target['end_time'])
    binding={'target_id':target['target_id'],'kind':'matched_alternative_readout','state_ids':[terminal['state_id']],'event_ids':[],
        'evidence_ids':[e['evidence_id'] for e in expected['evidence'] if terminal['state_id'] in e['state_ids']], 'alternative_run_id':proof['alternative_run_id']}
    if not binding['evidence_ids'] or private['evidence_bindings']!=[binding]:raise ValueError('counterfactual evidence world/target/timestamp mismatch')
    expected_language=render(inp,measurement_base(proof['source_annotations']))
    if canonical(record['public']['annotations'])!=canonical(expected_language):raise ValueError('counterfactual public language differs from grounded observed source')
    validate_view(inp,record['public']['annotations'],record['annotation_version'])
    return True
