"""Bounded real-MJX audit of actual held torques and applied force intervals.

An ordered diagnostic callback observes each step's input force without changing
the model/data. This audit is separate from performance/qualification runs.
"""
import argparse
from dataclasses import replace
from pathlib import Path
from unittest.mock import patch
import jax
import numpy as np
from mujoco import mjx
from phi_jepa.artifacts import code_provenance
from phi_jepa.simulation.common import ROOT, read, write
from phi_jepa.simulation.sampling import sample
from phi_jepa.simulation.mjx import MjxAdapter
from phi_jepa.simulation.quadruped import schedule


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output",type=Path,required=True)
    args=parser.parse_args()
    if args.output.exists(): raise ValueError("audit output already exists")
    cfg=read(ROOT/"configs/dataset_quadruped_development.json")
    cfg["quadruped_settings"]={"controller_period_s":.001}
    cfg["time"]["quadruped_target_times_s"]=[.12]
    s=replace(sample(cfg,"quadruped_locomotion",0,"clock_audit"),event_start=.01)
    original=mjx.step
    reports=[]
    for dt in (.0005,.00025):
        captured=[]
        def observe(t,force): captured.append((float(t),np.array(force)))
        def step(model,data):
            jax.debug.callback(observe,data.time,data.qfrc_applied,ordered=True)
            return original(model,data)
        with patch.object(mjx,"step",step):
            rollout=MjxAdapter().simulate(s,cfg,dt)
        jax.effects_barrier()
        clock=schedule(dt,.001,.12,.01)
        if len(captured)!=clock["steps"]+1: raise AssertionError("solve/probe count mismatch")
        # The separately counted compile probe is first; rollout restarts at t0.
        times=np.array([x[0] for x in captured[1:]])
        forces=np.array([x[1] for x in captured[1:]])
        np.testing.assert_allclose(times,np.arange(clock["steps"])*dt,atol=1e-12,rtol=0)
        for i in range(clock["steps"]):
            if i%clock["control_stride"]:
                np.testing.assert_array_equal(forces[i,6:],forces[i-1,6:])
        expected=np.zeros(clock["steps"])
        magnitude=rollout.public["known_events"][0]["parameters"][0]["value"]
        expected[clock["event_start_step"]:clock["event_end_step"]]=magnitude
        np.testing.assert_array_equal(forces[:,1],expected)
        np.testing.assert_array_equal(forces[:,[0,2,3,4,5]],0.)
        reports.append(dict(dt_s=dt,controller_updates=rollout.diagnostics["controller_updates"],steps=clock["steps"],probe_steps=1,event_start_s=.01,event_end_s=.11,force_duration_s=float(np.count_nonzero(forces[:,1])*dt),applied_impulse_Ns=float(np.sum(forces[:,1])*dt),forces=forces.tolist(),times_s=times.tolist(),experiment_hash=rollout.diagnostics["experiment_hash"],passed=True,devices=rollout.diagnostics["devices"]))
        jax.clear_caches()
    if reports[0]["experiment_hash"]!=reports[1]["experiment_hash"]: raise AssertionError("experiment changed")
    np.testing.assert_allclose(reports[0]["applied_impulse_Ns"],reports[1]["applied_impulse_Ns"],atol=1e-12,rtol=0)
    write(args.output,dict(passed=True,runs=reports,source=code_provenance(),role="Instrumented scheduler audit, not nominal locomotion qualification"))
    print("Actual MJX held-torque and event-force audits passed at both timesteps",flush=True)


if __name__=="__main__": main()
