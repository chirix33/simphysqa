from __future__ import annotations

import math

import numpy as np
import torch

from schemas import Blueprint, make_evidence
from training import DTYPE, integrate


def verify_contract(problem, phase, blueprint: Blueprint, instance, network,
                    trusted_facts: dict | None = None, initial_state=None) -> tuple[list, dict]:
    """Verify a proposed dynamic contract, returning machine evidence and values.

    The same trusted facts are passed to generation and verification. Values
    must match exactly up to float serialisation tolerance, with matching units
    AND source identifiers. This is provenance validation against supplied facts,
    not a claim that source identifiers themselves prove real-world truth.
    """
    facts = problem.facts(phase) if trusted_facts is None else trusted_facts
    evidence = [make_evidence("pydantic_schema", True, "The instance passed its dynamic Pydantic schema.",
                              fields=list(type(instance).model_fields))]
    payload = instance.model_dump(mode="json")
    values, source_errors = {}, []
    for name, supplied in payload.items():
        expected = facts.get(name)
        value = supplied.get("value")
        if expected is None or expected.get("value") is None:
            source_errors.append(f"No trusted numeric source for {name}; execution must abstain")
            continue
        if value is None or not isinstance(value, (float, int)) or not math.isfinite(value):
            source_errors.append(f"{name} is missing or nonfinite")
            continue
        values[name] = float(value)
        for field in ("unit", "source_id"):
            if supplied[field] != expected[field]:
                source_errors.append(f"{name}.{field} does not match supplied evidence")
        if not math.isclose(value, expected["value"], rel_tol=1e-9, abs_tol=1e-12):
            source_errors.append(f"{name}={value} is not the supplied value {expected['value']}")
    evidence.append(make_evidence("parameter_provenance", not source_errors,
                                 "Match numeric values, units, and source IDs to the supplied toy specification.",
                                 errors=source_errors))
    semantics = problem.semantic_errors(blueprint, values)
    evidence.append(make_evidence("operator_semantics", not semantics,
                                 "Check operator coverage, state order, required fields and missing information.",
                                 errors=semantics))
    if source_errors or semantics:
        return evidence, values
    try:
        problem.validate_parameters(values)
        evidence.append(make_evidence("parameter_consistency", True, "Cross-parameter inequalities passed."))
    except Exception as error:
        evidence.append(make_evidence("parameter_consistency", False, str(error)))
        return evidence, values

    # Boundary and convex-combination states remain inside these toy domains.
    corners = np.asarray(problem.probe_states(values), dtype=float)
    rng = np.random.default_rng(314159)
    sampled = []
    for _ in range(32):
        first, second = corners[rng.integers(len(corners), size=2)]
        weight = rng.uniform()
        sampled.append(weight*first + (1-weight)*second)
    states = np.vstack((corners, sampled))
    failures, tests = [], 0
    with torch.no_grad():
        for state in states:
            y = torch.as_tensor(state, dtype=DTYPE)
            raw_candidates = [network(problem.feature(y, phase.context)), torch.zeros_like(y),
                              torch.full_like(y, 100.0), torch.full_like(y, -100.0),
                              torch.as_tensor(rng.normal(0, 30, len(y)), dtype=DTYPE)]
            for raw in raw_candidates:
                try:
                    problem.state_guard(y, values)
                    derivative = problem.enforce(y, raw, values)
                    checks = problem.derivative_checks(y, derivative, values)
                    checks["finite_derivative"] = bool(torch.isfinite(derivative).all())
                    tests += len(checks)
                    broken = [name for name, passed in checks.items() if not passed]
                    if broken and len(failures) < 6:
                        failures.append({"state": y.tolist(), "raw_derivative": raw.tolist(),
                                         "enforced_derivative": derivative.tolist(), "failed_checks": broken})
                except Exception as error:
                    tests += 1
                    if len(failures) < 6:
                        failures.append({"state": y.tolist(), "error": str(error)})
    evidence.append(make_evidence("adversarial_derivative_tests", not failures,
        "Boundary and interior checks using learned, zero, extreme, and random derivatives.",
        number_of_scalar_checks=tests, number_of_states=len(states), failure_witnesses=failures,
        scope="Finite test suite; not exhaustive verification of all real states."))
    if failures:
        return evidence, values

    # Integrate the actual learned RHS, then compare dt with dt/2.
    rhs = problem.compile(problem.raw_rhs(network, phase.context), values)
    guard = lambda y: problem.state_guard(y, values)
    transition = lambda y, z: problem.transition_guard(y, z, values)
    try:
        with torch.no_grad():
            initial = (torch.tensor(problem.initial, dtype=DTYPE) if initial_state is None
                       else torch.as_tensor(initial_state, dtype=DTYPE).clone())
            span = min(1.0, phase.duration)
            _, coarse, coarse_stats = integrate(rhs, initial, 0., span, problem.dt, guard, transition)
            _, fine, fine_stats = integrate(rhs, initial, 0., span, problem.dt/2, guard, transition)
        difference = ((coarse[-1]-fine[-1]).abs() / (1+fine[-1].abs())).max().item()
        evidence.append(make_evidence("short_guarded_rollout", True,
            "The actual trained network completed a guarded short rollout.",
            output_steps=len(coarse)-1, coarse_solver=coarse_stats,
            state_summary=problem.state_summary(coarse.numpy(), values)))
        evidence.append(make_evidence("step_refinement", difference < 1e-3,
            "Compare final states at dt and dt/2; threshold is a declared engineering test.",
            max_scaled_difference=difference, threshold=1e-3, fine_solver=fine_stats))
    except Exception as error:
        evidence.append(make_evidence("short_guarded_rollout", False, str(error)))
    return evidence, values


def approval_gate(evidence: list, critique) -> tuple[bool, list[str]]:
    """Python owns the final decision. A prose Critic cannot override failed tests."""
    failures = [item.evidence_id for item in evidence if not item.passed]
    if not evidence:
        failures.append("missing_machine_evidence")
    if critique.verdict != "approve":
        failures.append("critic_did_not_approve")
    valid_ids = {item.evidence_id for item in evidence}
    if not critique.evidence_ids or not set(critique.evidence_ids).issubset(valid_ids):
        failures.append("critic_cited_missing_or_unknown_evidence")
    return not failures, failures
