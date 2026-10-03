"""PyBullet DIRECT scenes; no GUI, downloaded models, or learned policies."""
import importlib.metadata
import math
import tempfile
import time
from pathlib import Path
import numpy as np
from .common import Rollout, quantity as q, grid_index, opaque,event_active
from .engines import state, entity, public_description
from .scenes import box_inertia

def link(name,mass,size,origin=(0,0,0),cylinder=False):
    inertia=box_inertia(mass,size)
    geometry=f'<cylinder radius="{size[0]}" length="{size[2]}"/>' if cylinder else f'<box size="{" ".join(map(str,size))}"/>'
    if cylinder:
        r,_,h=size; inertia=[mass*(3*r*r+h*h)/12]*2+[mass*r*r/2]
    pos=" ".join(map(str,origin))
    return f'''<link name="{name}"><inertial><origin xyz="{pos}"/><mass value="{mass}"/><inertia ixx="{inertia[0]}" ixy="0" ixz="0" iyy="{inertia[1]}" iyz="0" izz="{inertia[2]}"/></inertial><collision><origin xyz="{pos}"/><geometry>{geometry}</geometry></collision></link>'''

def joint(name,parent,child,pos,axis=(0,1,0),kind="continuous",rpy=(0,0,0),damping=0):
    limit='<limit lower="-2.8" upper="2.8" effort="100" velocity="100"/>' if kind=="revolute" else ''
    return f'''<joint name="{name}" type="{kind}"><parent link="{parent}"/><child link="{child}"/><origin xyz="{' '.join(map(str,pos))}" rpy="{' '.join(map(str,rpy))}"/><axis xyz="{' '.join(map(str,axis))}"/><dynamics damping="{damping}" friction="0"/>{limit}</joint>'''

def car_asset(mult):
    parts=[link("car",10*mult,(.6,.3,.12))]
    for i,(x,y) in enumerate(((.22,.2),(.22,-.2),(-.22,.2),(-.22,-.2))):
        parts += [link(f"wheel_{i}",.3*mult,(.1,.1,.04),cylinder=True),joint(f"axle_{i}","car",f"wheel_{i}",(x,y,-.07),axis=(0,0,1),rpy=(-math.pi/2,0,0))]
    return '<robot name="phi_car_v1">'+''.join(parts)+'</robot>'

def arm_asset(payload):
    # Uniform boxes plus rigid finite endpoint payload, matching MuJoCo geometry.
    parts=[link("base",0,(.02,.02,.02)),link("link1",1,(.4,.05,.05),(.2,0,0)),link("link2",.8,(.3,.05,.05),(.15,0,0))]
    # Sphere inertia and geometry explicitly, same 0.025 m radius.
    m=max(payload,1e-12); inertia=.4*m*.025**2
    parts += [f'<link name="payload"><inertial><mass value="{m}"/><inertia ixx="{inertia}" ixy="0" ixz="0" iyy="{inertia}" iyz="0" izz="{inertia}"/></inertial><collision><geometry><sphere radius="0.025"/></geometry></collision></link>',joint("joint_1","base","link1",(0,0,1),damping=.05),joint("joint_2","link1","link2",(.4,0,0),damping=.05),joint("fixed_payload","link2","payload",(.3,0,0),kind="fixed")]
    # Limits are engine-specific soft constraints; comparison isolates free motion
    # by reporting any limit-active pair as incompatible for this diagnostic.
    return ('<robot name="phi_arm_v1">'+''.join(parts)+'</robot>').replace('type="continuous"','type="revolute"').replace('<dynamics damping="0.05" friction="0"/>','<dynamics damping="0.05" friction="0"/><limit lower="-2.8" upper="2.8" effort="100" velocity="100"/>')

class BulletAdapter:
    def simulate(self,s,config,dt):
        import pybullet as b
        cid=b.connect(b.DIRECT)
        try: return self._run(b,cid,s,config,dt)
        finally: b.disconnect(cid)

    def _run(self,b,cid,s,config,dt):
        p=s.parameters; domain=s.domain
        b.setGravity(0,0,-9.81,physicsClientId=cid)
        b.setTimeStep(dt,physicsClientId=cid)
        b.setPhysicsEngineParameter(numSolverIterations=100,deterministicOverlappingPairs=1,physicsClientId=cid)
        ground=b.createCollisionShape(b.GEOM_PLANE,physicsClientId=cid) if domain=="driving" else b.createCollisionShape(b.GEOM_BOX,halfExtents=[2,2,.05],physicsClientId=cid)
        table=b.createMultiBody(0,ground,basePosition=[0,0,0] if domain=="driving" else [0,0,-.05],physicsClientId=cid)
        objects=[]
        if domain in ("driving","robotic_arm"):
            asset=car_asset(p["mass_multiplier"]) if domain=="driving" else arm_asset(p["payload_kg"])
            with tempfile.TemporaryDirectory(prefix="phi_scene_") as tmp:
                path=Path(tmp)/"model.urdf"; path.write_text(asset)
                body=b.loadURDF(str(path),basePosition=[0,0,.17] if domain=="driving" else [0,0,0],useFixedBase=domain=="robotic_arm",flags=b.URDF_USE_INERTIA_FROM_FILE,physicsClientId=cid)
            nj=b.getNumJoints(body,physicsClientId=cid)
            for j in range(nj):
                b.setJointMotorControl2(body,j,b.VELOCITY_CONTROL,force=0,physicsClientId=cid)
                b.changeDynamics(body,j,linearDamping=0,angularDamping=0,physicsClientId=cid)
            b.changeDynamics(body,-1,linearDamping=0,angularDamping=0,physicsClientId=cid)
            if domain=="driving":
                friction=p["lateral_friction_coefficient"]
                b.changeDynamics(table,-1,lateralFriction=1,physicsClientId=cid)
                for j in range(4):
                    b.changeDynamics(body,j,lateralFriction=friction,rollingFriction=0,spinningFriction=0,contactStiffness=10000,contactDamping=100,frictionAnchor=1,physicsClientId=cid)
                    b.resetJointState(body,j,0,p["initial_forward_speed_m_s"]/.1,physicsClientId=cid)
                b.resetBaseVelocity(body,[p["initial_forward_speed_m_s"],0,0],physicsClientId=cid)
                entities=[entity("car","four_wheel_vehicle")]+[entity(f"wheel_{j}","wheel") for j in range(4)]
                params=[q("car","friction",friction),q("car","brake_torque_limit",.25,"N*m"),q("car","wheel_contact_stiffness",10000.,"N/m"),q("car","wheel_contact_damping",100.,"N*s/m")]
                pub=public_description(s,dt,asset+" Infinite ground plane z=0, friction=1. No rolling/spinning friction or drag. Wheel contacts stiffness=10000 N/m, damping=100 N*s/m, frictionAnchor=1.",entities,params,["After onset, each axle uses a zero-velocity brake with maximum torque 0.25 N*m; PyBullet VELOCITY_CONTROL targetVelocity=0 opposes wheel motion. Braking remains engaged through T."],"car",.25,"N*m",max(config["time"]["default_target_times_s"])-s.event_start)
            else:
                for j in range(2): b.resetJointState(body,j,p["initial_joint_angles_rad"],p["initial_joint_velocity_rad_s"],physicsClientId=cid)
                entities=[entity("arm","two_link_arm"),entity("joint_1","hinge"),entity("joint_2","hinge"),entity("tip","endpoint")]
                pub=public_description(s,dt,asset,entities,[q("arm","torque",p["joint_torque_Nm"],"N*m")],["Apply constant torque to both joints plus +0.5 N*m pulse to joint 1; joint damping 0.05. Matched diagnostic requires no active joint limit."],"joint_1",.5,"N*m",.1)
        else:
            mass=p["block_mass_kg"]; friction=p["contact_friction_coefficient"]
            positions=[[-.15,0,.05],[.05,0,.05]] if s.subfamily=="pushing" else [[0,0,.05],[0,0,.15]]
            for pos in positions:
                shape=b.createCollisionShape(b.GEOM_BOX,halfExtents=[.05]*3,physicsClientId=cid)
                obj=b.createMultiBody(mass,shape,basePosition=pos,physicsClientId=cid)
                b.changeDynamics(obj,-1,lateralFriction=friction,linearDamping=0,angularDamping=0,restitution=0,physicsClientId=cid); objects.append(obj)
            b.changeDynamics(table,-1,lateralFriction=1,restitution=0,physicsClientId=cid)
            asset=__import__("json").dumps(dict(model="phi_two_blocks_v1",block_size=[.1]*3,mass_each=mass,inertia=box_inertia(mass,[.1]*3),positions=positions,table_half_extents=[2,2,.05],table_center=[0,0,-.05],friction=friction,table_friction=1,restitution=0,linear_damping=0,angular_damping=0,solver_iterations=100),sort_keys=True)
            entities=[entity("table","static_table"),entity("block_1","box"),entity("block_2","box")]
            pub=public_description(s,dt,asset,entities,[q("block_1","force",p["push_force_N"],"N")],["Apply +x force to block_1 at its instantaneous center of mass for 0.1 s; no force outside event."],"block_1",p["push_force_N"],"N",.1)
        bodies=[body] if domain in ("driving","robotic_arm") else objects
        owner=entities[0]["entity_id"]
        for bi,obj in enumerate(bodies):
            for ji in range(-1,b.getNumJoints(obj,physicsClientId=cid)):
                dyn=b.getDynamicsInfo(obj,ji,physicsClientId=cid)
                for name,value,unit in (("mass",dyn[0],"kg"),("friction",dyn[1],"engine_specific"),("inertia_diagonal",list(dyn[2]),"kg*m^2"),("inertial_position",list(dyn[3]),"m"),("inertial_quaternion_xyzw",list(dyn[4]),"1")):
                    pub["entities"][0]["properties"].append(q(owner,f"body_{bi}_link_{ji}_{name}",value,unit,"body_local"))
        states=[]; events=[]; active=set(); start=time.perf_counter()
        stride=grid_index(config["time"]["default_saved_interval_s"],dt); count=grid_index(max(config["time"]["default_target_times_s"]),dt)
        stop_start=None; stop_time=None; min_v=float("inf"); stable_start=None; stable=False; limit_seen=False; support_lost=False; supported=False
        for step in range(count+1):
            t=round(step*dt,10); relations=[]
            if domain=="robotic_arm":
                joints=[b.getJointState(body,j,physicsClientId=cid) for j in range(2)]
                limit_seen=limit_seen or any(abs(v[0])>=2.8 for v in joints)
                vals=[q(f"joint_{j+1}",name,float(joints[j][k]),unit,"joint_local") for j in range(2) for name,k,unit in (("angle",0,"rad"),("angular_velocity",1,"rad/s"))]
                vals.append(q("tip","position",list(b.getLinkState(body,2,computeForwardKinematics=True,physicsClientId=cid)[0]),"m"))
                vals.append(q("arm","joint_limit_by_T",limit_seen))
            elif domain=="driving":
                pos,ori=b.getBasePositionAndOrientation(body,physicsClientId=cid); vel,omega=b.getBaseVelocity(body,physicsClientId=cid)
                min_v=min(min_v,vel[0])
                vals=[q("car","position",list(pos),"m"),q("car","orientation",list(ori)),q("car","velocity",list(vel),"m/s"),q("car","angular_velocity",list(omega),"rad/s")]
                vals += [q("car","forward_position",float(pos[0]),"m"),q("car","forward_velocity",float(vel[0]),"m/s")]
                for j in range(4):
                    js=b.getJointState(body,j,physicsClientId=cid)
                    vals += [q(f"wheel_{j}","angle",js[0],"rad","joint_local"),q(f"wheel_{j}","angular_velocity",js[1],"rad/s","joint_local")]
                stopped=abs(vel[0])<.02 and math.hypot(vel[0],vel[1])<.03
                if stopped and stop_start is None: stop_start=t
                if not stopped: stop_start=None
                if stop_start is not None and t-stop_start>=.2-1e-10 and stop_time is None:
                    stop_time=t
                    events.append(dict(event_id=opaque(s.group,"stopped",step),start_time=t,end_time=t,type="stopped",parameters=[q("car","stop_time",t,"s")],description="Earliest end of qualifying continuous 0.2s stopped interval."))
                vals.append(q("car","stopped_by_T",stop_time is not None))
            else:
                vals=[]
                for j,obj in enumerate(objects):
                    pos,ori=b.getBasePositionAndOrientation(obj,physicsClientId=cid); vel,omega=b.getBaseVelocity(obj,physicsClientId=cid)
                    vals += [q(f"block_{j+1}",name,list(v),unit) for name,v,unit in (("position",pos,"m"),("orientation",ori,"1"),("velocity",vel,"m/s"),("angular_velocity",omega,"rad/s"))]
                contacts=b.getContactPoints(objects[0],objects[1],physicsClientId=cid)
                normal_force=sum(c[9] for c in contacts if c[7][2]<-.5)
                supported=normal_force>(.005 if supported else .01)
                if supported: relations.append(dict(subject_id="block_2",predicate="contact",object_id="block_1"))
                pp=[b.getBasePositionAndOrientation(o,physicsClientId=cid) for o in objects]
                tilt=b.getEulerFromQuaternion(pp[1][1]); vv=b.getBaseVelocity(objects[1],physicsClientId=cid)[0]
                rot=np.array(b.getMatrixFromQuaternion(pp[0][1])).reshape(3,3)
                local=rot.T@(np.array(pp[1][0])-np.array(pp[0][0]))
                good=supported and abs(tilt[0])<math.pi/18 and abs(tilt[1])<math.pi/18 and all(abs(local[k])<.05-.001 for k in (0,1)) and np.linalg.norm(vv)<.02
                if good and stable_start is None: stable_start=t
                if not good: stable_start=None
                stable=stable_start is not None and t-stable_start>=.2-1e-10
                support_lost=support_lost or (s.subfamily=="pre_stacked" and t>=config["time"]["default_cutoff_s"] and not supported)
                vals += [q("block_2","stable_stack",bool(stable)),q("block_2","support_lost",bool(support_lost)),q("block_2","left_table",any(abs(pp[1][0][k])>2 for k in (0,1)))]
                now={"support_contact"} if supported else set()
                for ev in now-active:
                    events.append(dict(event_id=opaque(s.group,ev,step),start_time=t,end_time=t,type=ev,parameters=[q("block_2","contact_normal_force",sum(c[9] for c in contacts),"N")],description="Contact onset above 0.01 N; aggregate across contact points."))
                active=now
            if step%stride==0: states.append(state(s.group,step,dt,vals,relations))
            if step==count: break
            if domain=="robotic_arm":
                for j in range(2): b.setJointMotorControl2(body,j,b.TORQUE_CONTROL,force=p["joint_torque_Nm"]+(.5 if j==0 and event_active(step,dt,s.event_start,s.event_start+.1) else 0),physicsClientId=cid)
            elif domain=="driving" and step>=grid_index(s.event_start,dt):
                for j in range(4): b.setJointMotorControl2(body,j,b.VELOCITY_CONTROL,targetVelocity=0,force=.25,physicsClientId=cid)
            elif domain=="object_pushing_stacking" and event_active(step,dt,s.event_start,s.event_start+.1):
                pos=b.getBasePositionAndOrientation(objects[0],physicsClientId=cid)[0]
                b.applyExternalForce(objects[0],-1,[p["push_force_N"],0,0],pos,b.WORLD_FRAME,physicsClientId=cid)
            b.stepSimulation(physicsClientId=cid)
        applied=__import__("copy").deepcopy(pub["known_events"][0]); applied["type"]="applied_intervention"; applied["description"]="Applied on integration grid using the public control law."
        events.insert(0,applied)
        diag=dict(steps=count,solve_calls=count,wall_seconds=time.perf_counter()-start,subfamily=s.subfamily,applied_intervention_start_s=applied["start_time"],applied_intervention_end_s=applied["end_time"])
        if domain=="driving": diag.update(min_forward_velocity=min_v,stopped_by_T=stop_time is not None,stop_time=stop_time)
        if domain=="object_pushing_stacking": diag.update(stable_stack_at_T=stable)
        return Rollout(states,events,pub,asset,"urdf" if domain!="object_pushing_stacking" else "json","pybullet",importlib.metadata.version("pybullet"),diag)
