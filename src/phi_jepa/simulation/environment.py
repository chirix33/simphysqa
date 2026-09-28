"""Read-only host measurements; no assumption that reported hardware is local."""
import importlib.metadata
import os
import platform
import shutil
import subprocess
import time
from pathlib import Path

def inspect_environment(path=Path.cwd(), device_step=False):
    import psutil
    data=dict(os=platform.platform(),python=platform.python_version(),cpu=platform.processor(),logical_cpus=os.cpu_count(),ram_bytes=psutil.virtual_memory().total,available_ram_bytes=psutil.virtual_memory().available,disk_free_bytes=shutil.disk_usage(path).free,packages={},workers=1,worker_policy="serial until measured profiling",device_step="not_run")
    for name in ("mujoco","mujoco-mjx","pybullet","jax","jaxlib","numpy","jsonschema","psutil"):
        try: data["packages"][name]=importlib.metadata.version(name)
        except importlib.metadata.PackageNotFoundError: data["packages"][name]=None
    try: data["nvidia_smi"]=subprocess.check_output(["nvidia-smi","--query-gpu=name,driver_version,memory.total,memory.free","--format=csv,noheader"],text=True,timeout=15).strip()
    except (OSError,subprocess.SubprocessError) as exc: data["nvidia_smi_error"]=str(exc)
    if device_step:
        try:
            import jax
            import mujoco
            from mujoco import mjx
            data["jax_devices"]=[str(d) for d in jax.devices()]
            model=mujoco.MjModel.from_xml_string('<mujoco><worldbody><body pos="0 0 1"><freejoint/><geom size="0.1" mass="1"/></body></worldbody></mujoco>')
            mm=mjx.put_model(model,impl="jax"); dd=mjx.make_data(mm)
            start=time.perf_counter(); step=jax.jit(mjx.step); out=step(mm,dd); jax.block_until_ready(out.qpos)
            data["device_step"]=dict(status="pass",implementation="jax",backend=jax.default_backend(),compile_and_step_s=time.perf_counter()-start,z_before=float(dd.qpos[2]),z_after=float(out.qpos[2]))
        except Exception as exc: data["device_step"]=dict(status="fail",error=type(exc).__name__+": "+str(exc))
    return data
