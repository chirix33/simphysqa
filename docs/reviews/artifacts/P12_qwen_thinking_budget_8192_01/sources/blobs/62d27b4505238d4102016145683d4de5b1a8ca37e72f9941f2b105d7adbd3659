"""Label extraction and question rendering deliberately implemented separately."""
import copy
from hashlib import sha256
from .common import opaque, quantity as q
from phi_jepa.artifacts import digest

CHANNELS={
 "robotic_arm": [("joint_1","angle","rad"),("joint_1","angular_velocity","rad/s"),("joint_2","angle","rad"),("joint_2","angular_velocity","rad/s"),("tip","position","m"),("arm","joint_limit_by_T","1")],
 "driving": [("car","forward_position","m"),("car","forward_velocity","m/s"),("car","stopped_by_T","1")],
 "object_pushing_stacking": [("block_1","position","m"),("block_1","orientation","1"),("block_2","position","m"),("block_2","orientation","1"),("block_2","stable_stack","1"),("block_2","support_lost","1"),("block_2","left_table","1")],
 "quadruped_locomotion": [("base","position","m"),("base","velocity","m/s"),("base","roll","rad"),("base","pitch","rad"),("base","fall_by_T","1")],
 "tethered_load": [("load","position","m"),("load","swing_angle","rad"),("load","angular_velocity","rad/s"),("load","boundary_crossed","1")],
}

def target_specs(domain, time, measurements):
    targets=[]
    for entity,name,unit in CHANNELS[domain]:
        m=next(v for v in measurements if (v["entity_id"],v["name"])==(entity,name))
        rules={"stopped_by_T":"Absolute forward speed <0.02 m/s and planar speed <0.03 m/s for 0.2s; earliest qualifying interval end <=T.","stable_stack":"Supporting normal contact onset >0.01 N/off <=0.005 N with normal vertical component >0.5, tilt <10 degrees, COM inside lower local footprint with 0.001m margin, upper speed <0.02 m/s continuously for 0.2s.","support_lost":"Initially stacked upper block has lost supporting contact after cutoff.","left_table":"Upper block COM outside table footprint [-2,2] x [-2,2].","fall_by_T":"Base height <0.5*(0.4*cos(0.25)+0.03)m or abs(roll/pitch)>60 degrees for 0.1s.","boundary_crossed":"Load COM crosses x=0.1m with 0.005m hysteresis after cutoff.","joint_limit_by_T":"Either joint reaches magnitude 2.8rad; contact onset rearmed below 2.795rad."}
        kind="boolean" if type(m["value"]) is bool else "vector" if isinstance(m["value"],list) else "number"
        targets.append(dict(target_id=entity+":"+name,entity_id=entity,quantity=name,answer_type=kind,unit=unit,frame=m["frame"],query_kind="at_time",start_time=time,end_time=time,rule_id="terminal_readout_v1",rule_definition=rules.get(name,"Read the named channel at the requested absolute time. Unwrapped angles; quaternion xyzw compared by sign-invariant rotation angle; other vectors by Euclidean norm."),absolute_tolerance=0. if kind=="boolean" else .02 if unit in ("m/s","rad/s") else .01,relative_tolerance=0.))
    return targets

def question(targets):
    names=", ".join(t["entity_id"]+" "+t["quantity"]+" ("+t["unit"]+")" for t in targets)
    return f"At {targets[0]['end_time']:.6g} seconds from the initialized state, what are {names}, under the public model, control law and scheduled intervention?"

def labels(states, targets):
    result=[]
    for t in targets:
        s=next(s for s in states if s["timestamp"]==t["end_time"])
        v=next(v for v in s["measurements"] if (v["entity_id"],v["name"])==(t["entity_id"],t["quantity"]))
        result.append(dict(target_id=t["target_id"],value=copy.deepcopy(v["value"]),unit=v["unit"],frame=v["frame"]))
    return result

def answer_text(targets, answers):
    def display(v):
        if type(v) is bool: return "true" if v else "false"
        return "["+", ".join(format(x,".8g") for x in v)+"]" if isinstance(v,list) else format(v,".8g")
    return "; ".join(f"{a['target_id']} at {t['end_time']:.6g} s = {display(a['value'])} {a['unit']}" for t,a in zip(targets,answers))+"."

def build_records(s, rollout, config, provenance, checks):
    cutoff=config["time"]["default_cutoff_s"]
    times=config["time"]["quadruped_target_times_s" if s.domain=="quadruped_locomotion" else "default_target_times_s"]
    # Event-conditioned questions always use a target after the complete event.
    times=[t for t in times if t>=rollout.public["known_events"][0]["end_time"]-1e-10][-2:]
    if s.shift=="timed_event": times=[times[-1]]
    result=[]
    for t in times:
        terminal=next(st for st in rollout.states if st["timestamp"]==t)
        targets=target_specs(s.domain,t,terminal["measurements"])
        answers=labels(rollout.states,targets)
        inp={**copy.deepcopy(rollout.public),"domain":s.domain,"task_type":"future_state_prediction","question":question(targets),"observation_cutoff":cutoff,"states":copy.deepcopy([st for st in rollout.states if st["timestamp"]<=cutoff]),"answer_spec":targets}
        ref=dict(states=copy.deepcopy([st for st in rollout.states if cutoff<st["timestamp"]<=t]),events=[e for e in rollout.events if e["start_time"]<=t],structured_label=answers,label=answer_text(targets,answers),explanation="Named readouts in the recorded reference state support the answer; no causal derivation is asserted.",explanation_kind="descriptive",evidence=[dict(evidence_id=opaque(s.group,"evidence",t),state_ids=[terminal["state_id"]],event_ids=[],description="Simulator terminal readout.")],solution_trace=dict(status="unavailable",steps=[],verification_record=None))
        asset_hash=sha256(rollout.asset.encode()).hexdigest()
        sim=dict(engine=rollout.engine,implementation="jax" if rollout.engine=="mjx" else "native",engine_version=rollout.version,model_id=s.domain+"_v1",assets=[dict(role="complete_model",path="assets/"+asset_hash+"."+rollout.asset_format,sha256=asset_hash,license=config.get("asset_license","Authored in this repository; redistribution license not yet granted"))],generator_commit=provenance["git_commit"],config_sha256=digest(config),seed=s.seed,integration_timestep_s=config["time"]["default_timestep_s"],saved_state_interval_s=config["time"]["default_saved_interval_s"],duration_s=rollout.states[-1]["timestamp"],solver_settings=[q("runtime","settings",rollout.asset,"text","not_applicable")],dtype="float64",runtime_environment=[q("runtime",k,str(v),"text","not_applicable") for k,v in provenance.items() if k!="source_files"])
        shifts=[] if s.shift=="id" else [dict(parameter=k,unit="SI; see public model",training_support=str(config["domains"][s.domain]["id"].get(k,"configured event window")),test_support=s.shift,actual_value=v) for k,v in s.parameters.items()]
        meta=dict(record_origin="simulation",base_scenario_id=s.group,split_group_id=s.group,split=s.split,distribution=s.shift,shifts=shifts,simulation=sim,validation=dict(status="accepted" if all(c["status"]=="pass" for c in checks) else "pending",checks=copy.deepcopy(checks)))
        result.append(dict(schema_version="1.0.0",sample_id=opaque(s.group,"question",t,rollout.engine),input=inp,reference=ref,metadata=meta))
    return result
