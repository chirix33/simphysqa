"""Bounded nominal MJX qualification and native/backend comparison."""
from dataclasses import replace
import time
import numpy as np
import mujoco
from phi_jepa.simulation.common import ROOT,read,write
from phi_jepa.simulation.sampling import sample
from phi_jepa.simulation.mjx import MjxAdapter
from phi_jepa.simulation.scenes import quadruped_model,gait
from phi_jepa.simulation.pipeline import comparison

def main():
    c=read(ROOT/"pilot_config.json")
    s=sample(c,"quadruped_locomotion",0,"nominal_qualification")
    s=replace(s,event_start=4.,parameters=dict(body_payload_fraction=0.,contact_friction_coefficient=.8,joint_reference_frequency_hz=1.))
    start=time.perf_counter()
    a=MjxAdapter().simulate(s,c,.001); b=MjxAdapter().simulate(s,c,.0005)
    agreement=comparison(a,b,s.domain)
    m=mujoco.MjModel.from_xml_string(quadruped_model(0.,.8,.001)); d=mujoco.MjData(m); d.qpos[7:]=gait(0,1)[0]
    for _ in range(3000):
        desired,velocity=gait(d.time,1.)
        d.qfrc_applied[6:]=np.clip(50*(np.array(desired)-d.qpos[7:])+2*(np.array(velocity)-d.qvel[6:]),-8,8)
        mujoco.mj_step(m,d)
    report=dict(protocol="fixed nominal unperturbed controller qualification; separate native/MJX backend check",mjx_coarse=a.diagnostics,mjx_refined=b.diagnostics,refinement=agreement,native_terminal_qpos=d.qpos.tolist(),mjx_terminal_states=[a.states[-1],b.states[-1]],wall_seconds=time.perf_counter()-start,qualified=bool(a.diagnostics["nominal_locomotion_qualified"] and b.diagnostics["nominal_locomotion_qualified"] and agreement["passed"]))
    write(ROOT/"dataset-runs/quadruped-nominal-check.json",report)
    print(report)

if __name__=="__main__": main()
