"""Bounded native-MuJoCo controller development; not MJX validation or training."""
import itertools
import math
from pathlib import Path
import time
import mujoco
import numpy as np
from phi_jepa.simulation.scenes import quadruped_model
from phi_jepa.simulation.common import write

def main():
    results=[]; start=time.perf_counter()
    for amplitude, knee_amp, offset, phase_shift in itertools.product((.15,.3),(.2,.4),(.5,.8),(-math.pi/2,math.pi/2)):
        xml=quadruped_model(0.,.8,.001)
        m=mujoco.MjModel.from_xml_string(xml); d=mujoco.MjData(m)
        d.qpos[2]=.4*math.cos(offset/2)+.03
        phases=np.array([0.,math.pi,math.pi,0.])
        def refs(t):
            a=2*math.pi*t+phases
            return np.stack([-offset/2+amplitude*np.sin(a),offset+knee_amp*np.sin(a+phase_shift)],axis=1).reshape(-1),np.stack([amplitude*2*math.pi*np.cos(a),knee_amp*2*math.pi*np.cos(a+phase_shift)],axis=1).reshape(-1)
        d.qpos[7:]=refs(0)[0]
        fallen=False; bad_for=0
        for _ in range(3000):
            desired,velocity=refs(d.time)
            d.qfrc_applied[6:]=np.clip(50*(desired-d.qpos[7:])+2*(velocity-d.qvel[6:]),-8,8)
            mujoco.mj_step(m,d)
            w,x,y,z=d.qpos[3:7]; roll=math.atan2(2*(w*x+y*z),1-2*(x*x+y*y)); pitch=math.asin(float(np.clip(2*(w*y-z*x),-1,1)))
            bad_for=bad_for+.001 if d.qpos[2]<.195 or max(abs(roll),abs(pitch))>math.pi/3 else 0
            fallen=fallen or bad_for>=.1
        results.append(dict(hip_amplitude=amplitude,knee_amplitude=knee_amp,knee_offset=offset,knee_phase=phase_shift,kp=50,kd=2,forward=float(d.qpos[0]),fell=fallen,qualified=bool(d.qpos[0]>=.2 and not fallen)))
    results.sort(key=lambda r:(r["qualified"],r["forward"]),reverse=True)
    write(Path("dataset-runs/gait-development.json"),dict(engine="native MuJoCo",version=mujoco.__version__,purpose="controller tuning only; no MJX qualification",runs=len(results),wall_seconds=time.perf_counter()-start,results=results))
    print(results[:4])

if __name__=="__main__": main()
