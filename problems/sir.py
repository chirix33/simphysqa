from __future__ import annotations

import numpy as np
import torch

from .base import PROBLEMS, Phase, Problem, clip_tensor
from schemas import IntegrationError


class SIRProblem(Problem):
    """Closed-population toy dynamics; no clinical interpretation is intended."""
    name,title="sir","SIR: population-conserving nonnegative coupled flows"
    description=("Simulate susceptible, infected and recovered population fractions in a "
        "closed population. Contact intensity changes after an intervention. Infer nonnegative "
        "infection and recovery fluxes from neural predictions, then rebuild S'=-u, I'=u-w, R'=w. "
        "Independent clipping is not allowed because it can break S+I+R=1.")
    state_names,state_units=["S","I","R"],["fraction","fraction","fraction"]
    context_names=["beta","gamma"]
    initial,dt=[0.98,0.02,0.0],0.1
    default_parameters={"total_population":1.0,"infection_coefficient_limit":1.0,"recovery_coefficient_limit":0.25}
    field_info={"total_population":("fraction","Conserved total population fraction."),
        "infection_coefficient_limit":("1/day","Upper infection coefficient multiplying S*I."),
        "recovery_coefficient_limit":("1/day","Upper recovery coefficient multiplying I.")}
    operators={"nonnegative_coupled_sir_flows":"S'=-u; I'=u-w; R'=w, conserving population structurally.",
        "state_dependent_flow_bounds":"0<=u<=bmax*S*I; 0<=w<=gmax*I; no infection when I=0."}
    assumptions=["SIR compartments are fractions of one closed population.",
        "No births, deaths, migration or loss of immunity.",
        "Parameters are arbitrary teaching values, not fitted to an epidemic or used for medical advice."]
    bad_operator="clip_each_compartment_independently"
    bad_explanation="Independent derivative/state clipping can destroy the shared population balance."
    phases=[Phase("high_contact",10.0,{"beta":0.7,"gamma":0.1},{},"Higher contact coefficient."),
            Phase("lower_contact",20.0,{"beta":0.2,"gamma":0.1},{"infection_coefficient_limit":0.3},
                  "Contact coefficient and its permitted upper bound decrease.")]

    def validate_parameters(self,p):
        self.positive_parameters(p,["total_population","infection_coefficient_limit","recovery_coefficient_limit"])

    def truth(self,y,c):
        s,i,r=y.unbind(); u=c["beta"]*s*i; w=c["gamma"]*i
        return torch.stack((-u,u-w,w))

    def sample_training(self,n,rng):
        compartments=rng.dirichlet([1.2,1.2,1.2],n)
        s,i,r=compartments.T; beta=rng.uniform(0.15,0.9,n); gamma=rng.uniform(0.05,0.2,n)
        u=beta*s*i; w=gamma*i
        return np.column_stack((compartments,beta,gamma)),np.column_stack((-u,u-w,w))

    def enforce(self,y,raw,p):
        s,i,r=y.unbind()
        u=clip_tensor(-raw[0],0.0,p["infection_coefficient_limit"]*s.clamp_min(0)*i.clamp_min(0))
        w=clip_tensor(raw[2],0.0,p["recovery_coefficient_limit"]*i.clamp_min(0))
        return torch.stack((-u,u-w,w))

    def state_guard(self,y,p):
        super().state_guard(y,p)
        if y.min()<-1e-9 or abs(y.sum().item()-p["total_population"])>1e-7:
            raise IntegrationError("SIR nonnegativity or population conservation violated")

    def probe_states(self,p):
        n=p["total_population"]
        return [[n,0.,0.],[0.,n,0.],[0.,0.,n],[0.5*n,0.5*n,0.],[0.2*n,0.3*n,0.5*n]]

    def derivative_checks(self,y,dy,p):
        s,i,r=y.tolist(); u=-dy[0].item(); w=dy[2].item()
        return {"population_balance":abs(dy.sum().item())<1e-9,
                "infection_bound":-1e-9<=u<=p["infection_coefficient_limit"]*s*i+1e-9,
                "recovery_bound":-1e-9<=w<=p["recovery_coefficient_limit"]*i+1e-9,
                "disease_free_absorbing":i>0 or dy.abs().max().item()<1e-12,
                "inward_at_boundaries":all(float(dy[j])>=-1e-9 for j,v in enumerate(y) if abs(float(v))<1e-12)}

    def state_summary(self,states,p):
        return super().state_summary(states,p)|{
            "maximum_population_error":float(np.abs(states.sum(1)-p["total_population"]).max()),
            "nonnegativity_violation":float(max(0,-states.min()))}

PROBLEMS["sir"] = SIRProblem()
