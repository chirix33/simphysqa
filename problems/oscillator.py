from __future__ import annotations

import numpy as np
import torch

from schemas import ContractError, IntegrationError
from .base import PROBLEMS, Phase, Problem, clip_tensor


class OscillatorProblem(Problem):
    """Enforce dissipation of a specified physical energy, not an arbitrary learned H."""
    name,title="oscillator","Oscillator: reject energy conservation when damping is present"
    description=("Simulate a spring-mass oscillator with momentum p and changing damping. "
        "The correct statement is energy NONINCREASE, not energy conservation: "
        "H=k*q^2/2+p^2/(2*m), H'=(p/m)*F_damping<=0. Reconstruct the spring and "
        "kinematic terms and constrain the learned residual damping force. No division by p.")
    state_names,state_units=["position","momentum"],["m","kg*m/s"]
    context_names=["damping"]
    initial,dt=[1.5,0.0],0.04
    default_parameters={"mass":1.0,"spring_constant":1.0,"minimum_damping":0.05,"maximum_damping":1.5}
    field_info={"mass":("kg","Known inertial mass."),
        "spring_constant":("N/m","Known linear spring constant."),
        "minimum_damping":("kg/s","Lower allowed dissipative coefficient."),
        "maximum_damping":("kg/s","Upper allowed dissipative coefficient.")}
    operators={"spring_kinematics":"q'=p/m; split momentum derivative into spring and residual forces.",
               "dissipative_residual_force":"Damping opposes velocity with coefficient between supplied limits."}
    assumptions=["No external forcing or actuator supplies energy.",
                 "The specified H is the physical energy of this toy model.",
                 "Numerical H drift is monitored separately from the continuous-time inequality."]
    bad_operator="conserve_energy_exactly"
    bad_explanation="A damped oscillator loses energy when velocity is nonzero; conservation is the wrong contract."
    phases=[Phase("light_damping",6.0,{"damping":0.2},{},"Light damping."),
            Phase("heavy_damping",6.0,{"damping":0.8},{"minimum_damping":0.1},"Damping increases.")]

    def validate_parameters(self,p):
        self.positive_parameters(p,["mass","spring_constant","maximum_damping"])
        if not 0<=p["minimum_damping"]<=p["maximum_damping"]:
            raise ContractError("Inconsistent damping interval")

    def truth(self,y,c):
        q,momentum=y.unbind()
        return torch.stack((momentum,-q-c["damping"]*(1+0.1*q*q)*momentum))

    def sample_training(self,n,rng):
        q,p=rng.uniform(-2,2,n),rng.uniform(-2,2,n); c=rng.uniform(0.1,1.0,n)
        return np.column_stack((q,p,c)),np.column_stack((p,-q-c*(1+0.1*q*q)*p))

    def enforce(self,y,raw,p):
        q,momentum=y.unbind(); velocity=momentum/p["mass"]
        residual=raw[1]+p["spring_constant"]*q
        direction=torch.sign(velocity)
        magnitude=clip_tensor(-direction*residual,p["minimum_damping"]*velocity.abs(),
                              p["maximum_damping"]*velocity.abs())
        force=-direction*magnitude
        return torch.stack((velocity,-p["spring_constant"]*q+force))

    def energy(self,y,p):
        return 0.5*p["spring_constant"]*y[...,0]**2+0.5*y[...,1]**2/p["mass"]

    def transition_guard(self,before,after,p):
        if self.energy(after,p)>self.energy(before,p)+1e-9:
            raise IntegrationError("Numerical energy increased; reduce step")

    def probe_states(self,p):
        return [[1.,0.],[0.,1.],[0.,-1.],[0.,0.],[1.,1.],[-1.,-1.]]

    def derivative_checks(self,y,dy,p):
        q,mom=y.tolist(); vel=mom/p["mass"]
        hdot=p["spring_constant"]*q*dy[0].item()+vel*dy[1].item()
        force=dy[1].item()+p["spring_constant"]*q
        return {"kinematics":abs(dy[0].item()-vel)<1e-9,
                "energy_dissipation":hdot<=1e-9,
                "bounded_damping":p["minimum_damping"]*abs(vel)-1e-9<=abs(force)<=p["maximum_damping"]*abs(vel)+1e-9,
                "finite_at_zero_momentum":bool(torch.isfinite(dy).all())}

    def state_summary(self,states,p):
        e=self.energy(states,p)
        return super().state_summary(states,p)|{"initial_energy":float(e[0]),"final_energy":float(e[-1]),
            "maximum_energy_increase_per_output_step":float(max(0,np.diff(e).max()))}

PROBLEMS["oscillator"] = OscillatorProblem()
