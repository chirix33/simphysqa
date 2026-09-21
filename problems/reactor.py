from __future__ import annotations

import numpy as np
import torch

from schemas import ContractError, IntegrationError
from .base import PROBLEMS, Phase, Problem, clip_tensor


class ReactorProblem(Problem):
    """Closed, constant-volume A->B reaction with explicit controllable heat removal."""
    name, title = "reactor", "Reactor: coupled material balance and physically explicit cooling"
    description = (
        "A transforms to B in a closed, constant-volume toy reactor with 1:1 "
        "stoichiometry, so A+B=1. Heat generation is proportional to reaction flux. "
        "Newton cooling and a bounded active heat-removal actuator may make the "
        "temperature DECREASE even while reactant remains. Temperature is capped "
        "at 308 K only when the specified cooling authority is feasible."
    )
    state_names, state_units = ["A", "B", "temperature"], ["mol/L", "mol/L", "K"]
    context_names = ["reaction_constant", "cooling_constant", "ambient_temperature"]
    initial, dt = [1.0, 0.0, 300.0], 0.04
    default_parameters = {"total_concentration": 1.0, "depletion_gain": 2.0,
        "maximum_reaction_flux": 1.0, "heat_yield": 25.0, "cooling_constant": 0.10,
        "ambient_temperature": 295.0, "temperature_limit": 308.0,
        "temperature_barrier_gain": 2.0, "maximum_active_cooling": 30.0}
    field_info = {
        "total_concentration": ("mol/L", "Closed-system conserved A+B concentration."),
        "depletion_gain": ("1/s", "Upper proportional depletion rate."),
        "maximum_reaction_flux": ("mol/(L*s)", "Upper material conversion flux."),
        "heat_yield": ("K*L/mol", "Temperature rise per concentration converted; fixed heat capacity."),
        "cooling_constant": ("1/s", "Newton-cooling heat-transfer coefficient divided by heat capacity."),
        "ambient_temperature": ("K", "Coolant/environment temperature."),
        "temperature_limit": ("K", "Toy maximum permitted temperature."),
        "temperature_barrier_gain": ("1/s", "Gain in T'<=gain*(Tlimit-T)."),
        "maximum_active_cooling": ("K/s", "Maximum additional temperature-rate removal by actuator."),
    }
    operators = {"coupled_reaction_flux": "A'=-r; B'=r; 0<=r<=min(rmax,kA*A).",
                 "heat_balance_with_feasible_cooling": "T'=heat_yield*r-h*(T-Ta)-u; 0<=u<=umax, enforce barrier."}
    assumptions = ["Closed, well-mixed, constant-volume 1:1 A->B toy reaction.",
                   "Fixed heat capacity is absorbed into heat_yield and cooling parameters.",
                   "Explicit active cooling, not unexplained temperature clipping, enforces the thermal limit.",
                   "This is not a pressure-vessel or chemical-process safety model."]
    bad_operator = "temperature_must_never_decrease"
    bad_explanation = "At A=0, T>ambient, heat generation vanishes and Newton cooling requires T'<0. Cooling can also dominate while A>0."
    phases = [Phase("initial_cooling", 3.0,
                    {"reaction_constant":0.4,"cooling_constant":0.1,"ambient_temperature":295.0}, {},
                    "Initial cooling and reaction rate."),
              Phase("coolant_change", 5.0,
                    {"reaction_constant":0.9,"cooling_constant":0.35,"ambient_temperature":290.0},
                    {"cooling_constant":0.35,"ambient_temperature":290.0},
                    "Coolant gets colder; heat transfer and reaction rate change.")]

    def validate_parameters(self,p):
        self.positive_parameters(p,["total_concentration","depletion_gain","maximum_reaction_flux",
            "heat_yield","cooling_constant","temperature_barrier_gain"])
        if p["maximum_active_cooling"]<0 or p["temperature_limit"]<=p["ambient_temperature"]:
            raise ContractError("Invalid cooling capacity or thermal bounds")

    def truth(self,y,c):
        a,b,temp=y.unbind()
        r=c["reaction_constant"]*a
        return torch.stack((-r,r,25*r-c["cooling_constant"]*(temp-c["ambient_temperature"])))

    def sample_training(self,n,rng):
        a=rng.uniform(0.01,1,n); b=1-a; temp=rng.uniform(289,312,n)
        k=rng.uniform(0.2,1.0,n); h=rng.uniform(0.08,0.4,n); ambient=rng.uniform(289,296,n)
        r=k*a
        return np.column_stack((a,b,temp,k,h,ambient)), np.column_stack((-r,r,25*r-h*(temp-ambient)))

    def enforce(self,y,raw,p):
        a,b,temp=y.unbind()
        rmax=torch.minimum(a.new_tensor(p["maximum_reaction_flux"]),p["depletion_gain"]*a.clamp_min(0))
        # Average two independently learned estimates of the SAME material flux.
        r=clip_tensor((-raw[0]+raw[1])/2,0.0,rmax)
        passive=p["heat_yield"]*r-p["cooling_constant"]*(temp-p["ambient_temperature"])
        allowed=p["temperature_barrier_gain"]*(p["temperature_limit"]-temp)
        active=torch.clamp(passive-allowed,min=0.0)
        if active>p["maximum_active_cooling"]+1e-9:
            raise IntegrationError("Thermal barrier infeasible: required active cooling exceeds authority")
        return torch.stack((-r,r,passive-active))

    def state_guard(self,y,p):
        super().state_guard(y,p)
        if y[0]<-1e-9 or y[1]<-1e-9 or abs((y[0]+y[1]).item()-p["total_concentration"])>1e-7:
            raise IntegrationError("Material nonnegativity or conservation violated")
        if y[2]>p["temperature_limit"]+1e-8:
            raise IntegrationError("Temperature limit exceeded")

    def probe_states(self,p):
        total=p["total_concentration"]; lim=p["temperature_limit"]
        return [[total,0.,lim],[0.,total,lim],[total/2,total/2,lim],
                [0.,total,p["ambient_temperature"]+2]]

    def derivative_checks(self,y,dy,p):
        a,b,temp=y.tolist(); r=dy[1].item()
        passive=p["heat_yield"]*r-p["cooling_constant"]*(temp-p["ambient_temperature"])
        active=passive-dy[2].item()
        return {"material_balance": abs((dy[0]+dy[1]).item())<1e-9,
                "reaction_bounds": -1e-9<=r<=min(p["maximum_reaction_flux"],p["depletion_gain"]*a)+1e-9,
                "thermal_barrier": dy[2].item()<=p["temperature_barrier_gain"]*(p["temperature_limit"]-temp)+1e-8,
                "explicit_cooling_authority": -1e-8<=active<=p["maximum_active_cooling"]+1e-8,
                "empty_reactor_cools": a>0 or temp<=p["ambient_temperature"] or dy[2].item()<0}

    def state_summary(self,states,p):
        return super().state_summary(states,p)|{
            "max_material_balance_error":float(np.abs(states[:,0]+states[:,1]-p["total_concentration"]).max()),
            "max_temperature_violation":float(max(0,states[:,2].max()-p["temperature_limit"])),
            "material_nonnegativity_violation":float(max(0,-states[:,:2].min()))}

PROBLEMS["reactor"] = ReactorProblem()
