"""Bounded, measured batch-one/8/32/64 MJX-JAX device-step profile."""
import gc
import os
import time
os.environ.setdefault("XLA_PYTHON_CLIENT_PREALLOCATE","false")
import jax
import jax.numpy as jp
import mujoco
from mujoco import mjx
from phi_jepa.simulation.scenes import quadruped_model,gait
from phi_jepa.simulation.common import ROOT,read,write

def main():
    config=read(ROOT/"configs/dataset_quadruped_development.json")
    model=mujoco.MjModel.from_xml_string(quadruped_model(0,.8,.002))
    data=mujoco.MjData(model); data.qpos[7:]=gait(0,1)[0]; mujoco.mj_forward(model,data)
    mm=mjx.put_model(model,impl="jax"); dd=mjx.put_data(model,data,impl="jax")
    results=[]
    for batch in config["limits"]["mjx_batch_candidates"]:
        try:
            batched=jax.tree.map(lambda x:jp.broadcast_to(x,(batch,)+x.shape) if hasattr(x,"shape") else x,dd)
            step=jax.jit(jax.vmap(lambda d:mjx.step(mm,d)))
            start=time.perf_counter(); out=step(batched); jax.block_until_ready(out.qpos)
            compile_s=time.perf_counter()-start
            start=time.perf_counter()
            for _ in range(10): out=step(out)
            jax.block_until_ready(out.qpos)
            stats=jax.devices()[0].memory_stats() or {}
            results.append(dict(batch=batch,status="pass",compile_and_first_step_s=compile_s,ten_steps_s=time.perf_counter()-start,memory_stats=stats,dtype=str(out.qpos.dtype)))
            del out,step,batched; jax.clear_caches(); gc.collect()
        except Exception as exc:
            results.append(dict(batch=batch,status="fail",error=type(exc).__name__+": "+str(exc))); break
        write(ROOT/"dataset-runs/mjx-batch-profile.json",dict(implementation="jax",devices=[str(d) for d in jax.devices()],results=results,production_batch="unselected_pending_full_rollout_validation",memory_cap_fraction=config["limits"]["pilot_gpu_memory_fraction"]))
    print(results)

if __name__=="__main__": main()
