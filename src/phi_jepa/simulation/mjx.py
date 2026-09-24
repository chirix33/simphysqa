"""MJX-JAX transparent periodic PD quadruped; qualification is measured."""
import math
import time
import numpy as np
from .common import Rollout, quantity as q, grid_index,opaque
from .engines import state,entity,public_description,compiled_model_properties
from .scenes import quadruped_model,gait

class MjxAdapter:
    def simulate(self,s,config,dt):
        import jax
        jax.config.update("jax_enable_x64",True)
        import jax.numpy as jp
        import mujoco
        from mujoco import mjx
        p=s.parameters; freq=p["joint_reference_frequency_hz"]
        xml=quadruped_model(p["body_payload_fraction"],p["contact_friction_coefficient"],dt)
        m=mujoco.MjModel.from_xml_string(xml); d=mujoco.MjData(m)
        d.qpos[7:]=gait(0,freq)[0]
        mujoco.mj_forward(m,d)
        start=time.perf_counter(); mm=mjx.put_model(m,impl="jax"); dd=mjx.put_data(m,d,impl="jax")
        phases=jp.array([0.,math.pi,math.pi,0.])
        total_mass=float(m.body_mass.sum()); magnitude=.05*total_mass*9.81
        def step(data):
            a=2*jp.pi*freq*data.time+phases
            desired=jp.stack([-.25+.3*jp.sin(a),.5+.2*jp.sin(a-jp.pi/2)],axis=1).reshape(-1)
            velocity=jp.stack([.3*2*jp.pi*freq*jp.cos(a),.2*2*jp.pi*freq*jp.cos(a-jp.pi/2)],axis=1).reshape(-1)
            torque=jp.clip(50*(desired-data.qpos[7:])+2*(velocity-data.qvel[6:]),-8,8)
            force=jp.zeros_like(data.qfrc_applied).at[6:].set(torque)
            index=jp.rint(data.time/dt).astype(jp.int32)
            force=force.at[1].set(jp.where((index>=grid_index(s.event_start,dt))&(index<grid_index(s.event_start+.1,dt)),magnitude,0.))
            new=mjx.step(mm,data.replace(qfrc_applied=force))
            # MJX 3.14 x64 emits int64 contact indices from int32 initial data.
            # Preserve administrative index dtypes for lax.scan; no physical
            # values or integration states are altered.
            return jax.tree.map(lambda out,before:out.astype(before.dtype) if hasattr(out,"dtype") and jp.issubdtype(out.dtype,jp.integer) else out,new,data)
        compiled=jax.jit(step)
        probe=compiled(dd); jax.block_until_ready(probe.qpos)
        compile_seconds=time.perf_counter()-start
        entities=[entity("base","quadruped_base")]+[entity(f"joint_{i}","hinge") for i in range(8)]
        parameters=[q("base","frequency",freq,"Hz"),q("base","kp",50.,"N*m/rad"),q("base","kd",2.,"N*m*s/rad"),q("base","torque_limit",8.,"N*m"),q("base","phase_order",[0.,math.pi,math.pi,0.],"rad")]
        pub=public_description(s,dt,xml,entities,parameters,["Joint order: fl_hip,fl_knee,fr_hip,fr_knee,rl_hip,rl_knee,rr_hip,rr_knee. a=2*pi*frequency*t+leg_phase.","hip_ref=-0.25+0.3*sin(a); knee_ref=0.5+0.2*sin(a-pi/2); ref_velocity is exact derivative.","tau=clip(50*(ref-q)+2*(ref_velocity-qdot),-8,8); no hidden controller state.","Scheduled force applied at base center of mass, +world-y, for 0.1s."],"base",magnitude,"N",.1)
        pub["entities"][0]["properties"].extend(compiled_model_properties(m,"base"))
        pub["global_context"] += " Numeric model_* arrays follow XML body/geom/joint order including world body; prior quaternion arrays are wxyz, measured orientation is xyzw."
        count=grid_index(max(config["time"]["quadruped_target_times_s"]),dt); stride=grid_index(config["time"]["default_saved_interval_s"],dt)
        def scan_step(data,_):
            new=step(data)
            return new,(new.qpos,new.qvel)
        rollout=jax.jit(lambda data:jax.lax.scan(scan_step,data,None,length=count))
        start=time.perf_counter(); final,history=rollout(dd); jax.block_until_ready(final.qpos)
        rollout_compile_and_execute=time.perf_counter()-start
        positions=np.concatenate([np.asarray(dd.qpos)[None,:],np.asarray(history[0])])
        velocities=np.concatenate([np.asarray(dd.qvel)[None,:],np.asarray(history[1])])
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
                for j in range(8): vals += [q(f"joint_{j}","angle",float(pos[j+7]),"rad","joint_local"),q(f"joint_{j}","angular_velocity",float(vel[j+6]),"rad/s","joint_local")]
                vals.append(q("base","fall_by_T",fell))
                states.append(state(s.group,index,dt,vals))
        devices=[str(x) for x in jax.devices()]
        diag=dict(steps=count,solve_calls=count+1,compile_probe_steps=1,compile_seconds=compile_seconds,rollout_compile_and_execute_s=rollout_compile_and_execute,wall_seconds=time.perf_counter()-start+rollout_compile_and_execute,devices=devices,backend=jax.default_backend(),implementation="jax",forward_displacement_m=float(pos[0]),fall_by_T=fell,nominal_locomotion_qualified=bool(pos[0]>=.2 and not fell),subfamily=s.subfamily)
        applied=__import__("copy").deepcopy(pub["known_events"][0]); applied["type"]="applied_intervention"; applied["description"]="Scheduled force applied at integration grid resolution."
        if applied["start_time"]<count*dt: events.insert(0,applied)
        return Rollout(states,events,pub,xml,"xml","mjx",mujoco.__version__,diag)
