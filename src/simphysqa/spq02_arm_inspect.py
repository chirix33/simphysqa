"""Compile/introspect declared model only: zero mj_step/trajectory executions."""
from pathlib import Path
from hashlib import sha256
import argparse,mujoco,inspect
from simphysqa.io import read,write,ROOT

def inspect_arm(plan_path,output):
    pair=next(p for p in read(plan_path)['pairs'] if p['scenario']['domain']=='robotic_arm')
    source=pair['source_records'][0]
    xml=source['metadata']['simulation']['solver_settings'][0]['value']
    model=mujoco.MjModel.from_xml_string(xml)
    joint=mujoco.mj_name2id(model,mujoco.mjtObj.mjOBJ_JOINT,'joint_1')
    header=Path(mujoco.__file__).parent/'include/mujoco/mjdata.h'
    lines=header.read_text(encoding='utf-8').splitlines()
    pointer=[{'line':i+1,'text':line.strip()} for i,line in enumerate(lines) if 'qfrc_applied' in line]
    assert int(model.jnt_dofadr[joint])==0 and int(model.jnt_type[joint])==int(mujoco.mjtJoint.mjJNT_HINGE)
    report={'version':'spq02-arm-interpretation/1.0.0','parent_group_id':pair['scenario']['group'],
        'engine_version':mujoco.__version__,'model_compilations':1,'simulation_executions':0,
        'raw_event_parameter':source['input']['known_events'][0]['parameters'][0],
        'raw_base_controls':source['input']['controller']['controls'],'joint_name':'joint_1','joint_type':'hinge',
        'generalized_velocity_coordinate':int(model.jnt_dofadr[joint]),'declared_local_joint_axis':model.jnt_axis[joint].tolist(),
        'interpretation':'Base torque and additional pulse are scalar generalized hinge torques in the same qfrc_applied coordinate. The world event frame is the generic quantity-constructor default, not an implemented Cartesian world-vector torque. Omit only the +0.5 increment on coordinate 0; retain both base controls. No frame conversion is inferred or performed; raw metadata remains unchanged.',
        'model_xml_sha256':sha256(xml.encode()).hexdigest(),
        'source_files':{p:sha256((ROOT/p).read_text(encoding='utf-8').encode()).hexdigest() for p in ('src/phi_jepa/simulation/engines.py','src/phi_jepa/simulation/common.py','src/phi_jepa/simulation/scenes.py')},
        'installed_header_evidence':pointer,'installed_header_sha256':sha256(header.read_bytes()).hexdigest(),
        'official_api_reference':'https://mujoco.readthedocs.io/en/3.14.0/APIreference/APItypes.html'}
    write(output,report);print(report['interpretation'])
if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('--plan',type=Path,required=True);p.add_argument('--output',type=Path,required=True)
    a=p.parse_args();inspect_arm(a.plan,a.output)
