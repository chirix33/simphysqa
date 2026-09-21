from __future__ import annotations

import numpy as np
import torch

from schemas import ContractError, IntegrationError
from .base import PROBLEMS, Phase, Problem, clip_tensor


class DrivingProblem(Problem):
    """Idealised one-dimensional acceleration control, not a vehicle safety case."""
    name, title = "driving", "Driving: changing grip and a two-sided speed barrier"
    description = (
        "Simulate speed v with a trained neural acceleration model. A dry-to-wet "
        "regime change increases drag and decreases available acceleration. Keep "
        "speed in [0,12] m/s using a two-sided continuous-time barrier and symmetric "
        "acceleration authority. The speed ceiling does NOT jump below current speed."
    )
    state_names, state_units = ["speed"], ["m/s"]
    context_names = ["command", "drag"]
    initial, dt = [2.0], 0.05
    default_parameters = {"speed_floor": 0.0, "speed_limit": 12.0,
                          "acceleration_limit": 3.0, "barrier_gain": 2.0}
    field_info = {
        "speed_floor": ("m/s", "Lower admissible speed."),
        "speed_limit": ("m/s", "Upper admissible speed."),
        "acceleration_limit": ("m/s^2", "Symmetric achievable net acceleration magnitude."),
        "barrier_gain": ("1/s", "Barrier convergence gain; not a speed or acceleration."),
    }
    operators = {"two_sided_speed_barrier": "Intersect -k(v-vmin)<=a<=k(vmax-v).",
                 "bounded_acceleration": "Also intersect -amax<=a<=amax; reject infeasibility."}
    assumptions = ["1D ideal actuator realises commanded net acceleration.",
                   "The initial state is inside the speed interval.",
                   "No unmodelled disturbance or actuator delay is included."]
    bad_operator = "upper_speed_boundary_only"
    bad_explanation = "A boundary-only upper clamp misses negative speeds and finite-step overshoot."
    phases = [Phase("dry", 5.0, {"command": 4.0, "drag": 0.03}, {}, "Dry road."),
              Phase("wet", 5.0, {"command": 4.0, "drag": 0.10},
                    {"acceleration_limit": 1.0}, "Wet road: lower acceleration authority; higher drag.")]

    def validate_parameters(self, p):
        self.positive_parameters(p, ["acceleration_limit", "barrier_gain"])
        if p["speed_floor"] >= p["speed_limit"]:
            raise ContractError("speed_floor must be below speed_limit")

    def truth(self, y, c):
        return torch.stack((c["command"] - c["drag"] * y[0],))

    def sample_training(self, n, rng):
        v, u, d = rng.uniform(0, 20, n), rng.uniform(-4, 4, n), rng.uniform(0.01, 0.2, n)
        return np.column_stack((v, u, d)), (u - d * v)[:, None]

    def enforce(self, y, raw, p):
        v = y[0]
        lower = torch.maximum(v.new_tensor(-p["acceleration_limit"]),
                              -p["barrier_gain"] * (v - p["speed_floor"]))
        upper = torch.minimum(v.new_tensor(p["acceleration_limit"]),
                              p["barrier_gain"] * (p["speed_limit"] - v))
        if lower > upper + 1e-10:
            raise IntegrationError("Speed and actuator constraints are infeasible")
        return clip_tensor(raw[0], lower, upper).reshape(1)

    def state_guard(self, y, p):
        super().state_guard(y, p)
        if y[0] < p["speed_floor"] - 1e-9 or y[0] > p["speed_limit"] + 1e-9:
            raise IntegrationError("Speed outside the admissible interval")

    def probe_states(self, p):
        return [[p["speed_floor"]], [p["speed_limit"]], [(p["speed_floor"] + p["speed_limit"]) / 2]]

    def derivative_checks(self, y, dy, p):
        v, a, k = y[0].item(), dy[0].item(), p["barrier_gain"]
        return {"actuator": abs(a) <= p["acceleration_limit"] + 1e-9,
                "lower_barrier": a >= -k * (v - p["speed_floor"]) - 1e-9,
                "upper_barrier": a <= k * (p["speed_limit"] - v) + 1e-9}

    def state_summary(self, states, p):
        return super().state_summary(states, p) | {
            "max_speed_violation": float(max(0, states[:, 0].max()-p["speed_limit"],
                                               p["speed_floor"]-states[:, 0].min()))}

PROBLEMS["driving"] = DrivingProblem()
