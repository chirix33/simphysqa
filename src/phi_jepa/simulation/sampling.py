"""Group assignment precedes rendering; no held-out truth enters sampling."""
import random
from .common import Scenario, opaque, grid_index,read,ROOT

PAIRS = {
    "robotic_arm": ("payload_kg", "joint_torque_Nm"),
    "driving": ("initial_forward_speed_m_s", "mass_multiplier"),
    "object_pushing_stacking": ("block_mass_kg", "push_force_N"),
    "quadruped_locomotion": ("body_payload_fraction", "joint_reference_frequency_hz"),
    "tethered_load": ("cable_length_m", "support_acceleration_m_s2"),
}

def rules(config):
    return config.get("sampling",read(ROOT/"configs/dataset_sampling.json"))

def allocation(count, mode,config=None):
    policy=rules(config or {})
    weights = policy["smoke_shift_weights" if mode == "smoke" else "calibration_shift_weights"]
    sizes = [int(count*w) for w in weights]
    for i in range(count-sum(sizes)):
        sizes[i % 4] += 1
    return [s for s, n in zip(policy["shift_order"], sizes) for _ in range(n)]

def sample(config, domain, index, mode="smoke", shift="id", split="development"):
    if shift == "structural" or config["counts"]["structural_ood_enabled"]:
        raise ValueError("structural OOD is unsupported")
    spec = config["domains"][domain]
    seed = int(opaque(config["master_seed"], domain, mode, split, shift, index)[:12], 16)
    rng = random.Random(seed)
    p = {k: rng.uniform(*spec["id"][k]) for k in sorted(spec["id"])}
    policy=rules(config)
    if policy["grouping_granularity"]!="base_parameter_draw_and_control_schedule": raise ValueError("unsupported grouping granularity")
    a, b = policy["combination_pairs"][domain]
    # Equal cycling over admitted quadrants; torque magnitude and sign separate.
    quadrant = policy["combination_ood_quadrant"] if shift == "unseen_combination" else policy["id_quadrants"][index % len(policy["id_quadrants"])]
    for key, high in zip((a, b), quadrant):
        lo, hi = spec["id"][key]
        if key == "joint_torque_Nm": lo = 0
        mid = lo+(hi-lo)*policy["midpoint_fraction"]
        p[key] = rng.uniform(mid, hi) if high else rng.uniform(lo, mid)
        if key == "joint_torque_Nm": p[key] *= (-1 if index % 2 else 1)
    if shift == "parameter_extrapolation":
        for k, bounds in spec["parameter_ood"].items(): p[k] = rng.uniform(*bounds)
    dt = config["time"]["default_timestep_s"]
    bounds = spec["event_ood_time_s" if shift == "timed_event" else "event_id_time_s"]
    start = rng.randint(grid_index(bounds[0], dt), grid_index(bounds[1], dt))*dt
    subfamily = policy["object_subfamilies"][index % len(policy["object_subfamilies"])] if domain == "object_pushing_stacking" else "default"
    return Scenario(domain, seed, opaque("group", domain, mode, split, shift, index, config["master_seed"]), split, shift, subfamily, p, start)
