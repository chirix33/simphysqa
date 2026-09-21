from __future__ import annotations

from dataclasses import dataclass

import numpy as np
import torch

from schemas import Blueprint, ContractError, IntegrationError


@dataclass(frozen=True)
class Phase:
    name: str
    duration: float
    context: dict[str, float]
    parameter_overrides: dict[str, float]
    description: str


def clip_tensor(x: torch.Tensor, lower, upper) -> torch.Tensor:
    """Device/dtype-safe clipping with possibly state-dependent bounds."""
    lo = torch.as_tensor(lower, dtype=x.dtype, device=x.device)
    hi = torch.as_tensor(upper, dtype=x.dtype, device=x.device)
    return torch.minimum(torch.maximum(x, lo), hi)


class Problem:
    """Interface shared by the five separate teaching examples."""
    name: str
    title: str
    description: str
    state_names: list[str]
    state_units: list[str]
    context_names: list[str]
    initial: list[float]
    dt: float
    default_parameters: dict[str, float]
    field_info: dict[str, tuple[str, str]]
    operators: dict[str, str]
    assumptions: list[str]
    phases: list[Phase]
    bad_operator: str
    bad_explanation: str

    @property
    def catalogue(self) -> dict[str, dict]:
        return {name: {"unit": info[0], "description": info[1]}
                for name, info in self.field_info.items()}

    def facts(self, phase: Phase) -> dict[str, dict]:
        values = self.default_parameters | phase.parameter_overrides
        return {name: {"value": value, "unit": self.field_info[name][0],
                       "source_id": f"toy_spec.{self.name}.{phase.name}.{name}"}
                for name, value in values.items()}

    def payload(self, phase: Phase) -> dict:
        """Everything the agents may use; no external manuals are implied."""
        return {
            "scenario_id": self.name, "problem": self.description,
            "state_order": self.state_names, "state_units": self.state_units,
            "phase": phase.name, "phase_description": phase.description,
            "context": phase.context, "facts": self.facts(phase),
            "field_catalogue": self.catalogue, "supported_operators": self.operators,
            "required_assumptions": self.assumptions,
            "known_invalid_design": {"operator": self.bad_operator,
                                     "why_invalid": self.bad_explanation},
            "scope": "synthetic teaching simulation; not deployment or universal proof",
        }

    def canonical_blueprint(self) -> Blueprint:
        """Authored fixture only. Live Architect responses are not replaced by this."""
        return Blueprint(
            scenario_id=self.name, state_order=self.state_names,
            operators=list(self.operators), parameter_fields=list(self.catalogue),
            assumptions=self.assumptions, missing_information=[],
            revision_summary="Compose the supported operators and source all parameters.",
        )

    def feature(self, y: torch.Tensor, context: dict) -> torch.Tensor:
        extra = y.new_tensor([context[name] for name in self.context_names])
        return torch.cat((y, extra))

    def raw_rhs(self, network, context: dict):
        return lambda t, y: network(self.feature(y, context))

    def semantic_errors(self, blueprint: Blueprint, parameters: dict) -> list[str]:
        errors = []
        if blueprint.scenario_id != self.name:
            errors.append("scenario_id differs from the trusted problem")
        if blueprint.state_order != self.state_names:
            errors.append(f"state_order must be {self.state_names}")
        if len(blueprint.operators) != len(set(blueprint.operators)):
            errors.append("duplicate operator names")
        missing = sorted(set(self.operators) - set(blueprint.operators))
        extra = sorted(set(blueprint.operators) - set(self.operators))
        if missing:
            errors.append(f"missing required operators: {missing}")
        if extra:
            errors.append(f"unsupported operators: {extra}; {self.bad_explanation}")
        if set(blueprint.parameter_fields) != set(self.catalogue):
            errors.append("parameter_fields must cover exactly the supported operator parameters")
        if blueprint.missing_information:
            errors.append("Architect reported missing information: " + "; ".join(blueprint.missing_information))
        if set(parameters) != set(self.catalogue):
            errors.append("The numerical contract is missing required parameters")
        return errors

    def positive_parameters(self, p: dict, names: list[str]) -> None:
        for name in names:
            if p[name] <= 0:
                raise ContractError(f"{name} must be strictly positive")

    def compile(self, raw_rhs, p: dict):
        """Return an enforced RHS; no model-written source is ever evaluated."""
        self.validate_parameters(p)
        return lambda t, y: self.enforce(y, raw_rhs(t, y), p)

    def state_guard(self, y: torch.Tensor, p: dict) -> None:
        if not torch.isfinite(y).all():
            raise IntegrationError("Nonfinite state")
        if y.numel() != len(self.state_names):
            raise IntegrationError("Unexpected state dimension")

    def transition_guard(self, before: torch.Tensor, after: torch.Tensor, p: dict) -> None:
        """Extra endpoint property; most problems rely on state_guard."""
        return None

    def state_summary(self, states: np.ndarray, p: dict) -> dict:
        return {"minimum": dict(zip(self.state_names, states.min(0).tolist())),
                "maximum": dict(zip(self.state_names, states.max(0).tolist()))}


# Each example registers its own problem when its module is imported.
PROBLEMS = {}


def get_problem(name: str) -> Problem:
    """Fail closed for unsupported domains; never silently substitute a problem."""
    if name not in PROBLEMS:
        raise ValueError(f"Unknown problem {name!r}. Choose from {list(PROBLEMS)}")
    return PROBLEMS[name]
