"""Disclosed output capabilities, not simulator dynamics or missing evidence."""
from phi_jepa.inference.readout import RULES,SAMPLING
from collections import Counter

TARGETS={
    'robotic_arm':[('joint_1','angle'),('joint_1','angular_velocity'),('joint_2','angle'),('joint_2','angular_velocity'),('tip','position'),('arm','joint_limit_by_T')],
    'driving':[('car','forward_position'),('car','forward_velocity'),('car','stopped_by_T')],
    'object_pushing_stacking':[('block_1','position'),('block_1','orientation'),('block_2','position'),('block_2','orientation'),('block_2','stable_stack'),('block_2','support_lost'),('block_2','left_table')],
    'tethered_load':[('load','position'),('load','swing_angle'),('load','angular_velocity'),('load','boundary_crossed')],
}
CONTACT={
    'stable_stack':'Supporting normal contact force/on-off latch and vertical normal, both poses, lower local footprint, upper speed and uninterrupted 0.2 s endpoint dwell. Future force/normal/latch are absent from predicted n.',
    'support_lost':'Qualified initial support and supporting contact-force/normal latch history after cutoff. Future contact history is absent; proximity is insufficient.',
}
HISTORY={
    'joint_limit_by_T':'Both joint angles (rad/joint_local), initialized at t=0 through T, trigger >=2.8 rad, rearm <2.795 rad.',
    'boundary_crossed':'World load COM x from cutoff to T; qualified initial x<0.095 m, trigger x>0.105 m, rearm x<0.095 m.',
    'left_table':'World upper-block COM at T; outside [-2,2] m on x or y. Endpoint only, not ever-left event.',
    'stopped_by_T':'Forward and planar speed (m/s), complete history, abs(forward)<0.02 and planar<0.03 for 0.2 s; accumulate earliest qualifying interval.',
}


def capability(domain,entity,quantity):
    supported=(entity,quantity) in TARGETS.get(domain,[]) and quantity not in CONTACT
    return {'domain':domain,'entity_id':entity,'quantity':quantity,'implemented':supported,
        'required_evidence':CONTACT.get(quantity,HISTORY.get(quantity,'Registered finite named numerical channel with exact unit/frame/type at requested physical time; quaternion rotation error uses xyzw.')),
        'missing_mechanism':CONTACT.get(quantity,None if supported else 'unregistered_output_binding'),
        'qualification':'Per-target readout checks still required; invalid forecasts are failures, not unsupported capabilities.',
        'sampling':SAMPLING if quantity in RULES else None,
        'scientific_decision_required':quantity in CONTACT}


def matrix():
    return [capability(d,e,q) for d,targets in TARGETS.items() for e,q in targets]


def target_coverage(problem,rows,*,forecast_failure=None):
    found={r['target_id']:r for r in rows}
    counts=Counter(r['target_id'] for r in rows)
    return [{**capability(problem.input['domain'],s['entity_id'],s['quantity']),
        'target_id':s['target_id'],'status':'failure' if forecast_failure or counts[s['target_id']]!=1 else found.get(s['target_id'],{}).get('status','failure'),
        'reason':forecast_failure or ('duplicate_prediction' if counts[s['target_id']]>1 else found.get(s['target_id'],{}).get('reason','missing_prediction')),
        'eligible':1} for s in problem.input['answer_spec']]
