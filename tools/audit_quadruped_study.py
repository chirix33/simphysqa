"""Independently audit saved controller traces and contact timestamp alignment."""
import argparse
from pathlib import Path
import numpy as np
import mujoco
from phi_jepa.simulation.common import read, write
from phi_jepa.simulation.quadruped import reference


def audit(path):
    rollout=read(path)
    diag=rollout["diagnostics"]; trace=diag["trace"]; exp=diag["experiment"]
    cfg=exp["controller"]; times=np.asarray(trace["times_s"])
    torque=np.asarray(trace["commanded_torque"])
    angles=np.asarray(trace["joint_position"]); velocity=np.asarray(trace["joint_velocity"])
    expected=[]
    for i,t in enumerate(times[:-1]):
        desired,speed=reference(t,exp["frequency_hz"],cfg)
        expected.append(np.clip(cfg["kp"]*(desired-angles[i])+cfg["kd"]*(speed-velocity[i]),-cfg["torque_limit_Nm"],cfg["torque_limit_Nm"]))
    # Study traces are exactly on controller ticks (terminal has no update).
    if not np.allclose(np.diff(times),cfg["controller_period_s"],atol=1e-12,rtol=0): raise ValueError("audit requires one sample per control period")
    error=float(np.max(np.abs(np.asarray(expected)-torque[:-1])))
    if error>1e-10: raise ValueError(f"controller law mismatch: {error}")
    model=mujoco.MjModel.from_xml_string(rollout["asset"])
    data=mujoco.MjData(model)
    ground=model.geom("ground").id
    feet=[model.geom(name+"_foot").id for name in ("fl","fr","rl","rr")]
    # Native collision is used only as an independent geometric check on the
    # recorded MJX qpos. It never advances or replaces the dynamics trajectory.
    checked=0
    for i in range(0,len(times),10):
        data.qpos[:]=trace["base_position"][i]+trace["base_orientation_wxyz"][i]+trace["joint_position"][i]
        mujoco.mj_kinematics(model,data)
        mujoco.mj_collision(model,data)
        present=[]
        for foot in feet:
            present.append(any(set(map(int,c.geom))=={ground,foot} and c.dist<=0 for c in data.contact[:data.ncon]))
        if present!=trace["foot_contacts"][i]: raise ValueError(f"contact timestamp/geometry mismatch at {times[i]}")
        checked+=1
    return dict(artifact=path.name,controller_ticks_checked=len(expected),max_torque_law_error_Nm=error,independent_geometry_timestamps_checked=checked,passed=True)


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument("path",type=Path)
    args=parser.parse_args()
    results=[]
    for candidate in read(args.path/"summary.json")["candidates"]:
        for run in candidate["runs"]:
            if "diagnostics" in run: results.append(audit(args.path/run["artifact"]))
    write(args.path/"independent-trace-audit.json",dict(results=results,passed=all(x["passed"] for x in results),role="Offline algebra and geometry audit only; no native dynamics substitution."))
    print(f"{len(results)} saved runs passed controller and contact-timestamp audits")


if __name__=="__main__": main()
