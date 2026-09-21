from __future__ import annotations

import numpy as np
import torch

from schemas import ContractError, IntegrationError
from .base import PROBLEMS, Phase, Problem, clip_tensor


class RocketProblem(Problem):
    """Toy 1D variable-mass motion with bounded fuel flux and a burnout test."""
    name, title = "rocket", "Rocket: fuel depletion and coupled variable-mass dynamics"
    description = (
        "Simulate altitude, signed vertical velocity, and remaining fuel. Onboard "
        "mass is dry_mass+fuel, not a conserved constant. Rebuild acceleration "
        "from exhaust momentum flux, gravity and drag. At exactly zero fuel, "
        "burn rate and thrust are zero. Negative velocity is allowed during descent."
    )
    state_names, state_units = ["height", "velocity", "fuel"], ["m", "m/s", "kg"]
    context_names = ["throttle"]
    initial, dt = [0.0, 0.0, 0.8], 0.04
    default_parameters = {"dry_mass": 1.0, "exhaust_speed": 12.0, "gravity": 1.0,
                          "drag_coefficient": 0.03, "maximum_burn_rate": 0.3, "fuel_gain": 2.0}
    field_info = {
        "dry_mass": ("kg", "Positive inert dry mass; not consumed."),
        "exhaust_speed": ("m/s", "Effective exhaust speed relative to the vehicle."),
        "gravity": ("m/s^2", "Chosen toy gravitational acceleration, not Earth gravity."),
        "drag_coefficient": ("kg/m", "Coefficient in drag force c*v*abs(v)."),
        "maximum_burn_rate": ("kg/s", "Upper bound on fuel consumption flux."),
        "fuel_gain": ("1/s", "Enforce burn<=fuel_gain*fuel near depletion."),
    }
    operators = {"nonnegative_bounded_fuel_flux": "0<=q<=min(qmax,kf*fuel); no thrust at zero fuel.",
                 "variable_mass_momentum_balance": "h'=v; f'=-q; v'=(ve*q-c*v*abs(v))/(mdry+f)-g."}
    assumptions = ["1D toy ascent/descent without ground collision handling.",
                   "Exhaust relative speed and gravitational acceleration are specified constants.",
                   "Near depletion the flux tapers continuously; exact finite-time burnout is not claimed."]
    bad_operator = "onboard_mass_is_constant"
    bad_explanation = "Onboard mass decreases with fuel loss; at fuel=0, thrust must be zero."
    phases = [Phase("burn", 4.0, {"throttle": 0.22}, {}, "Initial burn."),
              Phase("reduced_throttle", 5.0, {"throttle": 0.12},
                    {"maximum_burn_rate": 0.15}, "Reduced throttle and lower burn-rate limit.")]

    def validate_parameters(self, p):
        self.positive_parameters(p, ["dry_mass", "exhaust_speed", "gravity", "maximum_burn_rate", "fuel_gain"])
        if p["drag_coefficient"] < 0:
            raise ContractError("drag_coefficient must be nonnegative")

    def truth(self, y, c):
        h, v, fuel = y.unbind()
        q = c["throttle"] * (1 + 0.05 * torch.tanh(v / 5))
        mass = 1.0 + fuel
        return torch.stack((v, (12*q - 0.03*v*v.abs())/mass - 1.0, -q))

    def sample_training(self, n, rng):
        h, v, f = rng.uniform(-5, 35, n), rng.uniform(-6, 10, n), rng.uniform(0.05, 1, n)
        throttle = rng.uniform(0.05, 0.30, n)
        q = throttle * (1 + 0.05*np.tanh(v/5))
        dy = np.column_stack((v, (12*q - 0.03*v*np.abs(v))/(1+f)-1, -q))
        return np.column_stack((h, v, f, throttle)), dy

    def enforce(self, y, raw, p):
        _, v, fuel = y.unbind()
        maximum = torch.minimum(fuel.new_tensor(p["maximum_burn_rate"]),
                                p["fuel_gain"]*fuel.clamp_min(0))
        q = clip_tensor(-raw[2], 0.0, maximum)
        mass = p["dry_mass"] + fuel
        if mass <= 0:
            raise IntegrationError("Nonpositive total mass")
        acceleration = (p["exhaust_speed"]*q - p["drag_coefficient"]*v*v.abs())/mass - p["gravity"]
        return torch.stack((v, acceleration, -q))

    def state_guard(self, y, p):
        super().state_guard(y, p)
        if y[2] < -1e-9 or p["dry_mass"] + y[2] <= 0:
            raise IntegrationError("Negative fuel or nonpositive total mass")

    def transition_guard(self, before, after, p):
        if after[2] > before[2] + 1e-9:
            raise IntegrationError("Fuel increased")

    def probe_states(self, p):
        return [[0., 0., 0.8], [0., -2., 0.], [5., 4., 0.001], [0., 0., 0.]]

    def derivative_checks(self, y, dy, p):
        v, fuel, q = y[1].item(), y[2].item(), -dy[2].item()
        expected_a = (p["exhaust_speed"]*q-p["drag_coefficient"]*v*abs(v))/(p["dry_mass"]+fuel)-p["gravity"]
        return {"kinematics": abs(dy[0].item()-v)<1e-9,
                "fuel_flux_bounds": -1e-9<=q<=min(p["maximum_burn_rate"],p["fuel_gain"]*fuel)+1e-9,
                "momentum_balance": abs(dy[1].item()-expected_a)<1e-8,
                "no_thrust_at_empty": fuel>0 or abs(q)<1e-12}

    def state_summary(self, states, p):
        return super().state_summary(states,p) | {
            "minimum_total_mass": float((p["dry_mass"]+states[:,2]).min()),
            "max_fuel_increase_per_output_step": float(max(0,np.diff(states[:,2]).max())),
            "fuel_nonnegativity_violation": float(max(0,-states[:,2].min()))}

PROBLEMS["rocket"] = RocketProblem()
