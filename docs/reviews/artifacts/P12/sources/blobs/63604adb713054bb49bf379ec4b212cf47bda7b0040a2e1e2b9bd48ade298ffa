"""Fixed-clock experiment contract and synchronized refinement diagnostics.

This is simulator/development code, never an inference dependency.
"""
import math
import xml.etree.ElementTree as ET
import numpy as np
from phi_jepa.artifacts import digest
from .common import grid_index

DEFAULTS = dict(controller_period_s=.002, hip_amplitude_rad=.3,
                knee_amplitude_rad=.2, kp=50., kd=2., torque_limit_Nm=8.,
                solver="CG", iterations=20, solver_tolerance=1e-8,
                contact_time_constant_s=.02, contact_damping_ratio=1.)


def settings(overrides):
    if set(overrides)-DEFAULTS.keys():
        raise ValueError(f"unknown quadruped settings: {set(overrides)-DEFAULTS.keys()}")
    result = {**DEFAULTS, **overrides}
    for key, value in result.items():
        if key == "solver":
            if value not in ("CG", "Newton"): raise ValueError("unsupported solver")
        elif isinstance(value, bool) or not isinstance(value, (float, int)) or not math.isfinite(value) or value <= 0:
            raise ValueError(f"invalid quadruped setting: {key}")
    if int(result["iterations"]) != result["iterations"]: raise ValueError("iterations must be integer")
    result["iterations"] = int(result["iterations"])
    return result


def reference(t, frequency, cfg, xp=np):
    a = 2*xp.pi*frequency*t + xp.array([0., math.pi, math.pi, 0.])
    h, k = cfg["hip_amplitude_rad"], cfg["knee_amplitude_rad"]
    pos = xp.stack([-.25+h*xp.sin(a), .5+k*xp.sin(a-xp.pi/2)], axis=-1).reshape(-1)
    vel = xp.stack([h*2*xp.pi*frequency*xp.cos(a), k*2*xp.pi*frequency*xp.cos(a-xp.pi/2)], axis=-1).reshape(-1)
    return pos, vel


def schedule(dt, period, horizon, event_start, event_duration=.1):
    if not math.isfinite(dt) or dt <= 0: raise ValueError("positive timestep required")
    stride = grid_index(period, dt)
    if stride < 1: raise ValueError("integration timestep exceeds controller period")
    count = grid_index(horizon, dt)
    grid_index(horizon, period)
    return dict(control_stride=stride, steps=count,
                event_start_step=grid_index(event_start, dt),
                event_end_step=grid_index(event_start+event_duration, dt))


def experiment(xml, initial_qpos, initial_qvel, cfg, frequency, horizon, event_start, force):
    root = ET.fromstring(xml)
    root.find("option").attrib.pop("timestep")
    ticks = np.arange(grid_index(horizon, cfg["controller_period_s"]))*cfg["controller_period_s"]
    commands = [reference(t, frequency, cfg)[0].tolist()+reference(t, frequency, cfg)[1].tolist() for t in ticks]
    descriptor = dict(model_without_timestep=ET.tostring(root, encoding="unicode"),
                      initial_qpos=list(initial_qpos), initial_qvel=list(initial_qvel),
                      controller=cfg, frequency_hz=frequency, horizon_s=horizon,
                      control_ticks_s=ticks.tolist(), reference_commands=commands,
                      event=dict(start_s=event_start, duration_s=.1, force_world_y_N=force))
    return descriptor, digest(descriptor)


def synchronized_comparison(a, b):
    """Diagnostic limits retain label half-tolerances; torque/contact are extra diagnostics.

    Raw contact disagreement is reported, not used to silently change label gates.
    Quaternion distance is invariant to the q/-q representation.
    """
    if a["experiment_hash"] != b["experiment_hash"]: raise ValueError("refinement changed experiment")
    x, y = a["trace"], b["trace"]
    if x["times_s"] != y["times_s"]: raise ValueError("unsynchronized traces")
    errors = {}
    for key, tol in (("base_position", .005), ("base_velocity", .01),
                     ("base_angular_velocity", .01), ("joint_position", .005),
                     ("joint_velocity", .01), ("commanded_torque", .01)):
        delta = np.asarray(x[key])-np.asarray(y[key])
        # Position/velocity vectors use Euclidean label convention; joints each scalar.
        errors[key] = (np.linalg.norm(delta, axis=1) if key.startswith("base_") else np.max(np.abs(delta), axis=1), tol)
    qa, qb = np.asarray(x["base_orientation_wxyz"]), np.asarray(y["base_orientation_wxyz"])
    cos = np.abs(np.sum(qa*qb, axis=1))/(np.linalg.norm(qa, axis=1)*np.linalg.norm(qb, axis=1))
    errors["base_orientation"] = (2*np.arccos(np.clip(cos, 0, 1)), .005)
    errors["foot_contacts"] = (np.any(np.asarray(x["foot_contacts"]) != np.asarray(y["foot_contacts"]), axis=1).astype(float), 0.)
    result = {}
    times = np.asarray(x["times_s"])
    for key, (delta, tolerance) in errors.items():
        bad = np.flatnonzero(delta > tolerance)
        result[key] = dict(tolerance=tolerance, max_error=float(max(delta)),
                           rms_error=float(np.sqrt(np.mean(delta**2))),
                           terminal_error=float(delta[-1]),
                           first_material_divergence_s=float(times[bad[0]]) if len(bad) else None,
                           first_error=float(delta[bad[0]]) if len(bad) else None)
    first = [v["first_material_divergence_s"] for v in result.values() if v["first_material_divergence_s"] is not None]
    return dict(same_experiment=True, first_material_divergence_s=min(first) if first else None,
                channels=result, torque_tolerance_role="diagnostic only, N*m",
                contacts_role="geometric foot-ground overlap at stated state, raw mismatch diagnostic only")
