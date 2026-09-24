"""MJX-JAX transparent periodic PD quadruped; qualification is measured."""
import math
import time
import numpy as np
from .common import Rollout, quantity as q, grid_index,opaque
from .engines import state,entity,public_description,compiled_model_properties
from .scenes import quadruped_model,gait
from .quadruped import settings, reference, schedule, experiment

class MjxAdapter:
    def simulate(self,s,config,dt):
        started=time.perf_counter()
        import jax
        jax.config.update("jax_enable_x64",True)
        import jax.numpy as jp
        import mujoco
        from mujoco import mjx
        p=s.parameters; freq=p["joint_reference_frequency_hz"]
        cfg=settings(config.get("quadruped_settings",{}))
        horizon=max(config["time"]["quadruped_target_times_s"])
        clock=schedule(dt,cfg["controller_period_s"],horizon,s.event_start)
        xml=quadruped_model(p["body_payload_fraction"],p["contact_friction_coefficient"],dt,cfg)
        m=mujoco.MjModel.from_xml_string(xml); d=mujoco.MjData(m)
        d.qpos[7:]=gait(0,freq)[0]
        mujoco.mj_forward(m,d)
        start=time.perf_counter(); mm=mjx.put_model(m,impl="jax"); dd=mjx.put_data(m,d,impl="jax")
        total_mass=float(m.body_mass.sum()); magnitude=.05*total_mass*9.81
        descriptor, experiment_hash=experiment(xml,d.qpos.tolist(),d.qvel.tolist(),cfg,freq,horizon,s.event_start,magnitude)
        def command(data,index):
            # Integer control ticks, not accumulated integration time. Between
            # ticks qfrc_applied stores the held command, including feedback.
            def update(_):
                tick=index//clock["control_stride"]
                desired,velocity=reference(tick*cfg["controller_period_s"],freq,cfg,jp)
                return jp.clip(cfg["kp"]*(desired-data.qpos[7:])+cfg["kd"]*(velocity-data.qvel[6:]),-cfg["torque_limit_Nm"],cfg["torque_limit_Nm"])
            return jax.lax.cond(index%clock["control_stride"]==0,update,lambda _:data.qfrc_applied[6:],None)
        def step(data,index):
            torque=command(data,index)
            force=jp.zeros_like(data.qfrc_applied).at[6:].set(torque)
            force=force.at[1].set(jp.where((index>=clock["event_start_step"])&(index<clock["event_end_step"]),magnitude,0.))
            new=mjx.step(mm,data.replace(qfrc_applied=force))
            # MJX 3.14 x64 emits int64 contact indices from int32 initial data.
            # Preserve administrative index dtypes for lax.scan; no physical
            # values or integration states are altered.
            return jax.tree.map(lambda out,before:out.astype(before.dtype) if hasattr(out,"dtype") and jp.issubdtype(out.dtype,jp.integer) else out,new,data)
        compiled=jax.jit(step)
        probe=compiled(dd,jp.array(0)); jax.block_until_ready(probe.qpos)
        compile_seconds=time.perf_counter()-start
        entities=[entity("base","quadruped_base")]+[entity(f"joint_{i}","hinge") for i in range(8)]
        parameters=[q("base","frequency",freq,"Hz"),q("base","kp",cfg["kp"],"N*m/rad"),q("base","kd",cfg["kd"],"N*m*s/rad"),q("base","torque_limit",cfg["torque_limit_Nm"],"N*m"),q("base","hip_amplitude",cfg["hip_amplitude_rad"],"rad"),q("base","knee_amplitude",cfg["knee_amplitude_rad"],"rad"),q("base","phase_order",[0.,math.pi,math.pi,0.],"rad")]
        pub=public_description(s,cfg["controller_period_s"],xml,entities,parameters,["Joint order: fl_hip,fl_knee,fr_hip,fr_knee,rl_hip,rl_knee,rr_hip,rr_knee. a=2*pi*frequency*t+leg_phase.","hip_ref=-0.25+hip_amplitude*sin(a); knee_ref=0.5+knee_amplitude*sin(a-pi/2); ref_velocity is exact derivative.","At control times n*update_interval_s: tau=clip(kp*(ref-q)+kd*(ref_velocity-qdot),-torque_limit,torque_limit); hold tau constant until the next control tick, starting at t=0.","Scheduled force applied at base center of mass, +world-y, for 0.1s."],"base",magnitude,"N",.1)
        pub["controller"]["description"]="Sampled feedback on a fixed physical clock with zero-order hold; events use [start,end)."
        pub["controller"]["initial_internal_state"]=[q(f"joint_{j}","held_torque_before_first_update",0.,"N*m","joint_local") for j in range(8)]
        pub["entities"][0]["properties"].extend(compiled_model_properties(m,"base"))
        pub["global_context"] += " Numeric model_* arrays follow XML body/geom/joint order including world body; prior quaternion arrays are wxyz, measured orientation is xyzw."
        count=grid_index(max(config["time"]["quadruped_target_times_s"]),dt); stride=grid_index(config["time"]["default_saved_interval_s"],dt)
        def scan_step(data,index):
            new=step(data,index)
            return new,(new.qpos,new.qvel,new.qfrc_applied[6:])
        rollout=jax.jit(lambda data:jax.lax.scan(scan_step,data,jp.arange(count)))
        start=time.perf_counter(); final,history=rollout(dd); jax.block_until_ready(final.qpos)
        rollout_compile_and_execute=time.perf_counter()-start
        positions=np.concatenate([np.asarray(dd.qpos)[None,:],np.asarray(history[0])])
        velocities=np.concatenate([np.asarray(dd.qvel)[None,:],np.asarray(history[1])])
        torques=np.asarray(history[2])
        # Torque history t_i is the command actually applied over [t_i,t_i+dt).
        # Terminal has no new controller update: retain the final applied torque.
        torques=np.concatenate([torques,torques[-1:]])
        states=[]; events=[]; fall_since=None; fell=False; start=time.perf_counter()
        for index in range(count+1):
            pos=positions[index]; vel=velocities[index]
            if not np.all(np.isfinite(pos)) or not np.all(np.isfinite(vel)): raise ValueError("MJX nonfinite state")
            w,x,y,z=pos[3:7]
            roll=math.atan2(2*(w*x+y*z),1-2*(x*x+y*y)); pitch=math.asin(float(np.clip(2*(w*y-z*x),-1,1)))
            bad=pos[2]<.5*(.4*math.cos(.25)+.03) or max(abs(roll),abs(pitch))>math.pi/3
            if bad and fall_since is None: fall_since=index*dt
            if not bad: fall_since=None
            if fall_since is not None and index*dt-fall_since>=.1-1e-10 and not fell:
                fell=True
                events.append(dict(event_id=opaque(s.group,"fall",index),start_time=round(index*dt,10),end_time=round(index*dt,10),type="fall",parameters=[q("base","fall",True)],description="First qualifying fall interval end, measured each integration step."))
            if index%stride==0:
                vals=[q("base","position",pos[:3].tolist(),"m"),q("base","orientation",[float(x),float(y),float(z),float(w)]),q("base","velocity",vel[:3].tolist(),"m/s"),q("base","angular_velocity",vel[3:6].tolist(),"rad/s","body"),q("base","roll",roll,"rad"),q("base","pitch",pitch,"rad")]
                for j in range(8): vals += [q(f"joint_{j}","angle",float(pos[j+7]),"rad","joint_local"),q(f"joint_{j}","angular_velocity",float(vel[j+6]),"rad/s","joint_local"),q(f"joint_{j}","commanded_torque",float(torques[index,j]),"N*m","joint_local")]
                vals.append(q("base","fall_by_T",fell))
                states.append(state(s.group,index,dt,vals))
        devices=[str(x) for x in jax.devices()]
        diag=dict(steps=count,solve_calls=count+1,compile_probe_steps=1,compile_seconds=compile_seconds,rollout_compile_and_execute_s=rollout_compile_and_execute,wall_seconds=time.perf_counter()-start+rollout_compile_and_execute,devices=devices,backend=jax.default_backend(),implementation="jax",forward_displacement_m=float(pos[0]),fall_by_T=fell,nominal_locomotion_qualified=bool(pos[0]>=.2 and not fell),subfamily=s.subfamily)
        diag.update(experiment_hash=experiment_hash,controller_updates=grid_index(horizon,cfg["controller_period_s"]),controller_probe_updates=1,controller_period_s=cfg["controller_period_s"],integration_timestep_s=dt)
        if config.get("quadruped_trace_interval_s") is not None:
            trace_stride=grid_index(config["quadruped_trace_interval_s"],dt)
            if trace_stride<1: raise ValueError("positive trace stride required")
            indices=np.arange(0,count+1,trace_stride)
            if indices[-1]!=count: raise ValueError("trace must include terminal state")
            foot_ids=jp.array([m.geom(name+"_foot").id for name in ("fl","fr","rl","rr")])
            ground=m.geom("ground").id
            def contacts_at(qpos):
                # step() contacts belong to its PRE-integration state. Recompute
                # only kinematics/collision on a separate data value at qpos.
                contact=mjx.collision(mm,mjx.kinematics(mm,dd.replace(qpos=qpos)))._impl.contact
                pair=contact.geom
                mask=((pair[:,0,None]==ground)&(pair[:,1,None]==foot_ids))|((pair[:,1,None]==ground)&(pair[:,0,None]==foot_ids))
                return jp.any(mask&(contact.dist[:,None]<=0),axis=0)
            contacts=jax.jit(jax.vmap(contacts_at))(jp.asarray(positions[indices]))
            contacts=np.asarray(contacts)
            diag["diagnostic_collision_calls"]=len(indices)
            diag["experiment"]=descriptor
            diag["trace"]=dict(times_s=np.round(indices*dt,10).tolist(),base_position=positions[indices,:3].tolist(),base_orientation_wxyz=positions[indices,3:7].tolist(),base_velocity=velocities[indices,:3].tolist(),base_angular_velocity=velocities[indices,3:6].tolist(),joint_position=positions[indices,7:].tolist(),joint_velocity=velocities[indices,6:].tolist(),commanded_torque=torques[indices].tolist(),foot_contacts=contacts.tolist(),torque_semantics="Right-continuous held command; terminal retains last interval command. Contacts recomputed at the stated qpos without altering dynamics.")
        diag["wall_seconds"]=time.perf_counter()-started
        applied=__import__("copy").deepcopy(pub["known_events"][0]); applied["type"]="applied_intervention"; applied["description"]="Scheduled force applied at integration grid resolution."
        if applied["start_time"]<count*dt: events.insert(0,applied)
        return Rollout(states,events,pub,xml,"xml","mjx",mujoco.__version__,diag)
