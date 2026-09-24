"""Lazy simulator adapters. No dependency fallback or truth substitution."""
import importlib.metadata
import math
import time
import numpy as np
from .common import Rollout, quantity as q, opaque, grid_index,event_active
from .scenes import arm_model, tether_model, quadruped_model, support_motion, gait

def state(group, step, dt, measurements, relations=None):
    return dict(state_id=opaque(group, "state", round(step*dt, 10)), step_index=step, timestamp=round(step*dt, 10), measurements=measurements, relations=relations or [], context="Measured simulator state at the stated timestamp.")

def entity(name, kind, properties=()):
    return dict(entity_id=name, type=kind, properties=list(properties))

def compiled_model_properties(model, owner):
    """Numeric shared prior, with packed channel mapping explicitly named."""
    return [q(owner,"model_"+name,np.asarray(getattr(model,name)).reshape(-1).tolist(),unit,"model_local") for name,unit in (("body_mass","kg"),("body_inertia","kg*m^2"),("body_pos","m"),("body_quat","1"),("body_ipos","m"),("body_iquat","1"),("geom_size","m"),("geom_pos","m"),("geom_quat","1"),("geom_friction","engine_specific"),("jnt_axis","1"),("jnt_pos","m"),("jnt_range","rad_or_m"),("dof_damping","generalized_SI")) if np.asarray(getattr(model,name)).size]

def public_description(s, dt, asset, entities, parameters, equations, event_entity, event_magnitude, event_unit, duration):
    # Full authored model text is a shared public prior, not a private path.
    controller = dict(mode="fully_specified_feedback" if equations else "explicit_schedule", description="Memoryless law evaluated before each integration step; events use [start,end).", equations=equations, parameters=parameters, initial_internal_state=[], update_interval_s=dt, controls=[])
    event = dict(event_id=opaque(s.group, "intervention"), start_time=s.event_start, end_time=round(s.event_start+duration, 10), type="scheduled_intervention", parameters=[q(event_entity, "magnitude", event_magnitude, event_unit)], description="Known scheduled intervention; the controller definition specifies direction and application point.")
    return dict(global_context="Deterministic SI simulation. Full public model prior: "+asset, entities=entities, controller=controller, known_events=[event], coordinate_convention="Right-handed world x-forward/y-left/z-up; quaternion xyzw; unwrapped right-hand joint angles; all channels SI.")

class MujocoAdapter:
    def simulate(self, s, config, dt):
        import mujoco as mj
        p = s.parameters
        is_arm = s.domain == "robotic_arm"
        if not is_arm and s.domain != "tethered_load": raise ValueError("wrong native domain")
        xml = arm_model(p["payload_kg"], dt) if is_arm else tether_model(p["cable_length_m"], p["load_mass_kg"], dt)
        model = mj.MjModel.from_xml_string(xml)
        data = mj.MjData(model)
        if is_arm:
            data.qpos[:] = p["initial_joint_angles_rad"]
            data.qvel[:] = p["initial_joint_velocity_rad_s"]
            entities = [entity("arm", "two_link_arm"), entity("joint_1", "hinge"), entity("joint_2", "hinge"), entity("tip", "endpoint")]
            params = [q("arm", k, float(v), "kg" if k == "payload_kg" else "rad" if "angles" in k else "rad/s" if "velocity" in k else "N*m") for k,v in p.items()]
            pub = public_description(s, dt, xml, entities, params, ["tau_1=tau_2=joint_torque_Nm; add +0.5 N*m to joint_1 during the scheduled pulse; viscous damping=0.05 N*m*s/rad."], "joint_1", .5, "N*m", .1)
            pub["controller"]["mode"]="explicit_schedule"
            pub["controller"]["controls"]=[dict(entity_id=f"joint_{j+1}",channel="applied_torque",start_time=0.,end_time=max(config["time"]["default_target_times_s"]),value=p["joint_torque_Nm"],unit="N*m",frame="joint_local",interpolation="constant") for j in range(2)]
        else:
            data.qpos[1] = p["initial_swing_angle_rad"]
            entities = [entity("support", "prescribed_translation"), entity("load", "point_load")]
            params = [q("load", "length", p["cable_length_m"], "m"), q("load", "mass", p["load_mass_kg"], "kg"), q("support", "acceleration", p["support_acceleration_m_s2"], "m/s^2")]
            pub = public_description(s, dt, xml, entities, params, ["support x=0,v=0 until event onset; +a for 0.1s then -a for 0.1s, then stationary; continuous analytic position and velocity.", "theta_ddot=-(g*sin(theta)+support_acceleration*cos(theta))/length; positive theta displaces load toward +x; motion imposed at integration substeps."], "support", p["support_acceleration_m_s2"], "m/s^2", .2)
        pub["entities"][0]["properties"].extend(compiled_model_properties(model,pub["entities"][0]["entity_id"]))
        pub["global_context"] += " Numeric model_* arrays follow the XML body/geom/joint order including world body; body_quat and geom_quat use MuJoCo wxyz internally. Observed orientations use xyzw. Model numbers are prior parameters, not observed future states."
        mj.mj_forward(model, data)
        states, events = [], []
        stride = grid_index(config["time"]["default_saved_interval_s"], dt)
        horizon = max(config["time"]["default_target_times_s"])
        count = grid_index(horizon, dt)
        min_tension, max_length_error = float("inf"), 0.
        contact_active = False
        limit_seen = False
        boundary_seen = False
        boundary_armed = True
        started = time.perf_counter()
        for step in range(count+1):
            t = step*dt
            if not np.all(np.isfinite(data.qpos)) or not np.all(np.isfinite(data.qvel)): raise ValueError("nonfinite simulation")
            mj.mj_forward(model, data)
            if is_arm:
                values = [q(f"joint_{j+1}", name, float(arr[j]), unit, "joint_local") for j in range(2) for name,arr,unit in (("angle",data.qpos,"rad"),("angular_velocity",data.qvel,"rad/s"))]
                values.append(q("tip", "position", data.site("tip").xpos.tolist(), "m"))
                limit = bool(np.any(np.abs(data.qpos) >= 2.8))
                if limit and not contact_active:
                    events.append(dict(event_id=opaque(s.group,"limit",step), start_time=round(t,10), end_time=round(t,10), type="joint_limit_contact", parameters=[q("arm","contact",True)], description="Joint limit onset; rearmed below 2.795 rad."))
                if limit: contact_active=True
                elif np.all(np.abs(data.qpos)<2.795): contact_active=False
                limit_seen = limit_seen or limit
                values.append(q("arm","joint_limit_by_T",limit_seen))
            else:
                x,v,a = support_motion(t,s.event_start,p["support_acceleration_m_s2"])
                theta,omega = data.qpos[1],data.qvel[1]
                length = p["cable_length_m"]
                tension = p["load_mass_kg"]*(9.81*math.cos(theta)-a*math.sin(theta)+length*omega*omega)
                min_tension=min(min_tension,tension)
                pos=data.site("load").xpos.copy()
                max_length_error=max(max_length_error, abs(np.linalg.norm(pos-np.array([x,0,2]))-length))
                values=[q("load","position",pos.tolist(),"m"),q("load","swing_angle",float(theta),"rad"),q("load","angular_velocity",float(omega),"rad/s"),q("support","position",[x,0.,2.],"m"),q("support","velocity",[v,0.,0.],"m/s")]
                if t>=config["time"]["default_cutoff_s"] and pos[0]>.105 and boundary_armed:
                    boundary_seen=True; boundary_armed=False
                    events.append(dict(event_id=opaque(s.group,"crossing",step),start_time=round(t,10),end_time=round(t,10),type="boundary_crossing",parameters=[q("load","boundary",.1,"m")],description="Positive x crossing with 0.005 m hysteresis."))
                if pos[0]<.095: boundary_armed=True
                values.append(q("load","boundary_crossed",boundary_seen))
            if step % stride == 0: states.append(state(s.group,step,dt,values))
            if step == count: break
            if is_arm:
                data.qfrc_applied[:]=p["joint_torque_Nm"]
                if event_active(step,dt,s.event_start,s.event_start+.1): data.qfrc_applied[0]+=.5
                mj.mj_step(model,data)
            else:
                # Reduced-coordinate constrained pendulum: integrate using RK4 with
                # MuJoCo mass/bias dynamics and prescribed support acceleration.
                # Both generalized accelerations solved together via inverse dynamics.
                def deriv(ti, yi):
                    xx,vv,aa=support_motion(ti,s.event_start,p["support_acceleration_m_s2"])
                    data.qpos[:]=[xx,yi[0]]; data.qvel[:]=[vv,yi[1]]
                    mj.mj_forward(model,data)
                    mass=np.zeros((2,2)); mj.mj_fullM(model,data,mass)
                    acc=(-data.qfrc_bias[1]-mass[1,0]*aa)/mass[1,1]
                    return np.array([yi[1],acc])
                y=np.array([data.qpos[1],data.qvel[1]])
                k1=deriv(t,y); k2=deriv(t+dt/2,y+dt*k1/2); k3=deriv(t+dt/2,y+dt*k2/2); k4=deriv(t+dt-1e-12,y+dt*k3)
                y=y+dt*(k1+2*k2+2*k3+k4)/6
                xx,vv,_=support_motion(t+dt,s.event_start,p["support_acceleration_m_s2"])
                data.qpos[:]=[xx,y[0]]; data.qvel[:]=[vv,y[1]]; data.time=t+dt
        applied=__import__("copy").deepcopy(pub["known_events"][0]); applied["type"]="applied_intervention"; applied["description"]="Applied on the declared integration grid using [start,end) control semantics."
        events.insert(0,applied)
        diagnostics=dict(steps=count, solve_calls=count if is_arm else count*4, wall_seconds=time.perf_counter()-started, subfamily=s.subfamily,applied_intervention_start_s=applied["start_time"],applied_intervention_end_s=applied["end_time"])
        if not is_arm:
            diagnostics.update(min_tension_N=min_tension, max_length_error_m=max_length_error)
            if min_tension <= 0: raise ValueError("outside taut suspension validity: nonpositive tension")
        return Rollout(states,events,pub,xml,"xml","mujoco",mj.__version__,diagnostics)
