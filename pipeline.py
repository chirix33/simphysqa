from __future__ import annotations

import csv
import importlib.metadata
import json
import platform
import uuid
from dataclasses import dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import numpy as np
import torch
from pydantic import ValidationError

from agents import Backend, FixtureBackend, make_backend
from schemas import (
    Blueprint,
    ContractError,
    Critique,
    IntegrationError,
    build_contract_model,
    content_hash,
    make_evidence,
)
from training import DTYPE, integrate, train_network
from problems import get_problem
from verification import approval_gate, verify_contract


def write_json(path: str | Path, data: Any) -> None:
    path = Path(path); path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, indent=2, allow_nan=False))


def append_jsonl(path: str | Path, data: dict) -> None:
    with Path(path).open("a", encoding="utf-8") as stream:
        stream.write(json.dumps(data, allow_nan=False) + "\n")


def environment_manifest() -> dict:
    versions = {}
    for name in ["torch", "numpy", "pydantic", "openai", "matplotlib"]:
        try:
            versions[name] = importlib.metadata.version(name)
        except importlib.metadata.PackageNotFoundError:
            versions[name] = "not_installed"
    return {"python": platform.python_version(), "platform": platform.platform(), "versions": versions,
            "device": "CPU", "torch_dtype": "float64"}


@dataclass
class ApprovedContract:
    blueprint: Blueprint
    instance: Any
    parameters: dict[str, float]
    evidence: list
    critique: Critique
    rounds: int
    contract_hash: str
    audit_path: Path


def design_contract(problem, phase, network, backend: Backend, out_dir: str | Path,
                    max_rounds: int = 3, inject_bad_first_design: bool = False,
                    initial_state=None, verbose: bool = True) -> ApprovedContract:
    """Fail closed unless BOTH independent tests and the Critic approve.

    ``inject_bad_first_design`` is a labelled fixture-only educational fault.
    It demonstrates repair-loop plumbing; it is NOT an observed OpenAI mistake.
    API errors propagate rather than turning into fake offline successes.
    """
    if not 1 <= max_rounds <= 10:
        raise ValueError("max_rounds must be 1..10")
    if inject_bad_first_design and not isinstance(backend, FixtureBackend):
        raise ValueError("Fault injection here is fixture-only; never attribute it to OpenAI")
    directory = Path(out_dir); directory.mkdir(parents=True, exist_ok=True)
    audit_path = directory / "audit.jsonl"
    if audit_path.exists():
        raise FileExistsError(f"Refusing to overwrite an existing audit: {audit_path}")
    specification = problem.payload(phase)
    if initial_state is not None:
        specification["current_state_at_phase_entry"] = torch.as_tensor(initial_state).tolist()
    feedback = []
    for round_number in range(1, max_rounds + 1):
        common = {"problem": specification, "previous_feedback": feedback,
                  "round": round_number, "maximum_rounds": max_rounds}
        # Role 1: generate the STRUCTURE. All subsequent changes are recorded.
        blueprint = backend.ask("architect", Blueprint, common)
        original_blueprint = blueprint.model_dump(mode="json")
        injected = bool(inject_bad_first_design and round_number == 1)
        if injected:
            blueprint = blueprint.model_copy(deep=True)
            blueprint.operators = [problem.bad_operator]
            blueprint.revision_summary = "DELIBERATELY INJECTED TEST FAULT, NOT AN LLM ERROR: " + problem.bad_explanation
        instance, parameters, evidence, json_schema = None, {}, [], None
        try:
            dynamic_model = build_contract_model(blueprint, problem.catalogue)
            json_schema = dynamic_model.model_json_schema()
            # Role 2: populate the newly constructed Pydantic schema.
            instance = backend.ask("executor", dynamic_model,
                                   common | {"blueprint": blueprint.model_dump(mode="json")})
            # Python executes real checks before the Critic sees their results.
            evidence, parameters = verify_contract(problem, phase, blueprint, instance, network,
                                                    trusted_facts=specification["facts"], initial_state=initial_state)
        except (ContractError, ValidationError) as error:
            evidence = [make_evidence("schema_compilation", False,
                                      "The candidate schema/instance was rejected before execution.", error=str(error))]
        # Role 3: evaluate the actual artifacts and numerical evidence.
        critique = backend.ask("critic", Critique, common | {
            "blueprint": blueprint.model_dump(mode="json"),
            "contract_values": instance.model_dump(mode="json") if instance else None,
            "machine_evidence": [item.model_dump(mode="json") for item in evidence],
        })
        approved, gate_failures = approval_gate(evidence, critique)
        record = {
            "scenario": problem.name, "phase": phase.name, "round": round_number,
            "backend_origin": backend.origin, "injected_test_fault": injected,
            "original_architect_response": original_blueprint,
            "blueprint_used": blueprint.model_dump(mode="json"), "dynamic_json_schema": json_schema,
            "executor_response": instance.model_dump(mode="json") if instance else None,
            "machine_evidence": [item.model_dump(mode="json") for item in evidence],
            "critic_response": critique.model_dump(mode="json"),
            "runtime_gate_approved": approved, "runtime_gate_failures": gate_failures,
        }
        append_jsonl(audit_path, record)
        write_json(directory / f"round_{round_number:02d}.json", record)
        if verbose:
            state = "APPROVED" if approved else "REJECTED"
            print(f"  {problem.name}/{phase.name}: round {round_number} {state} [{backend.origin}]", flush=True)
            if gate_failures:
                print("    Gate: " + ", ".join(gate_failures), flush=True)
        if approved:
            contract_hash = content_hash({
                "blueprint": blueprint.model_dump(mode="json"), "values": instance.model_dump(mode="json")})
            write_json(directory / "approved_contract.json", {
                "hash": contract_hash, "blueprint": blueprint.model_dump(mode="json"),
                "values": instance.model_dump(mode="json"), "backend_origin": backend.origin,
                "verification_scope": "supplied toy model + finite machine checks; not universal safety"})
            return ApprovedContract(blueprint, instance, parameters, evidence, critique,
                                    round_number, contract_hash, audit_path)
        feedback = [{"round": round_number, "gate_failures": gate_failures,
                     "machine_evidence": [item.model_dump(mode="json") for item in evidence if not item.passed],
                     "critic": critique.model_dump(mode="json")}]
        if critique.verdict == "abstain":
            raise ContractError(f"Critic abstained; obtain missing facts. Audit: {audit_path}")
    raise ContractError(f"No approved contract after {max_rounds} rounds. Audit: {audit_path}")


@dataclass
class ExperimentResult:
    name: str
    path: Path
    times: np.ndarray
    trajectories: dict[str, np.ndarray]
    summary: dict
    contracts: list[ApprovedContract]
    network: Any = field(repr=False)
    training_history: list = field(repr=False)


def _write_trajectory_csv(path: Path, times: np.ndarray, trajectories: dict, names: list[str]) -> None:
    with path.open("w", newline="") as stream:
        writer = csv.writer(stream)
        writer.writerow(["time", "variant"] + names)
        for variant, states in trajectories.items():
            for t, state in zip(times, states):
                writer.writerow([float(t), variant] + state.tolist())


def run_example(name: str, mode: str = "openai", backend: Backend | None = None,
                model: str = "gpt-4.1-mini-2025-04-14", seed: int = 7, epochs: int = 400,
                results_dir: str | Path = "results", max_rounds: int = 3,
                inject_bad_first_design: bool = False, verbose: bool = True) -> ExperimentResult:
    """Run ONE complete example: train, metacognitive contracts, compare, save.

    Four genuinely computed trajectories are generated:
      ungoverned_neural: trained network, no policy guard;
      governed_neural: SAME trained network + approved runtime constraints;
      governed_reference: specified synthetic equations + SAME approved policy;
      governed_neural_half_step: numerical refinement of the governed network.

    Reference errors are controlled toy comparisons, not evidence that an LLM
    improves prediction accuracy. Constraints can trade fidelity for compliance.
    """
    problem = get_problem(name)
    timestamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%S")
    directory = Path(results_dir) / f"{name}_seed{seed}_{timestamp}_{uuid.uuid4().hex[:6]}"
    directory.mkdir(parents=True, exist_ok=False)
    if backend is None:
        options = {"model": model} if mode == "openai" else {}
        backend = make_backend(mode, out_dir=directory / "provider_requests", **options)
    if verbose:
        print(f"\n{name.upper()} | {backend.origin} | seed={seed} | CPU derivative training", flush=True)
    write_json(directory / "run_started.json", {"name": name, "origin": backend.origin,
               "seed": seed, "epochs": epochs, "environment": environment_manifest(),
               "contains_deliberate_test_fault": inject_bad_first_design})
    try:
        network, training, history = train_network(problem, seed, epochs, directory / "training")
        if verbose:
            print(f"  Held-out derivative normalized MSE: {training['test_normalized_mse']:.6g}", flush=True)
        variants = ["ungoverned_neural", "governed_neural", "governed_reference", "governed_neural_half_step"]
        current = {variant: torch.tensor(problem.initial, dtype=DTYPE) for variant in variants}
        pieces = {variant: [] for variant in variants}
        time_pieces, contract_records, phase_reports, boundaries = [], [], [], []
        clock = 0.0
        with torch.no_grad():
            for phase_index, phase in enumerate(problem.phases):
                contract = design_contract(problem, phase, network, backend,
                    directory / "contracts" / phase.name, max_rounds,
                    inject_bad_first_design=inject_bad_first_design and phase_index == 0,
                    initial_state=current["governed_neural"], verbose=verbose)
                contract_records.append(contract)
                p = contract.parameters
                raw_rhs = problem.raw_rhs(network, phase.context)
                governed_rhs = problem.compile(raw_rhs, p)
                reference_rhs = problem.compile(lambda t,y,c=phase.context: problem.truth(y,c), p)
                guard = lambda y: problem.state_guard(y, p)
                transition = lambda y,z: problem.transition_guard(y,z,p)
                trajectories, statistics, grids = {}, {}, {}
                for variant in variants:
                    rhs = raw_rhs if variant == "ungoverned_neural" else (
                        reference_rhs if variant == "governed_reference" else governed_rhs)
                    step = problem.dt/2 if variant == "governed_neural_half_step" else problem.dt
                    guarded = variant != "ungoverned_neural"
                    t, states, stats = integrate(rhs, current[variant], clock, clock+phase.duration, step,
                                                guard if guarded else None, transition if guarded else None)
                    current[variant] = states[-1].clone()
                    trajectories[variant], statistics[variant], grids[variant] = states.numpy(), stats, t
                coarse_times = grids["governed_neural"]
                # Align the half-step trajectory to the coarse observation grid.
                fine = trajectories["governed_neural_half_step"]
                trajectories["governed_neural_half_step"] = np.column_stack([
                    np.interp(coarse_times, grids["governed_neural_half_step"], fine[:,j])
                    for j in range(fine.shape[1])])
                start_index = 0 if phase_index == 0 else 1
                time_pieces.append(coarse_times[start_index:])
                for variant in variants:
                    pieces[variant].append(trajectories[variant][start_index:])
                phase_reports.append({"phase": phase.name, "start": clock, "end": clock+phase.duration,
                    "context": phase.context, "parameters": p, "contract_hash": contract.contract_hash,
                    "rounds": contract.rounds, "solver_statistics": statistics,
                    "state_checks": {variant: problem.state_summary(states,p) for variant,states in trajectories.items()}})
                clock += phase.duration
                if phase_index + 1 < len(problem.phases):
                    boundaries.append(clock)
        times = np.concatenate(time_pieces)
        arrays = {variant: np.vstack(parts) for variant,parts in pieces.items()}
        reference = arrays["governed_reference"]
        state_scale = 1 + np.max(np.abs(reference), axis=0)
        errors = {variant: {
                    "rmse_per_state_component": np.sqrt(np.mean((states-reference)**2,axis=0)).tolist(),
                    "state_order": problem.state_names,
                    "dimensionless_scaled_rmse": float(np.sqrt(np.mean(((states-reference)/state_scale)**2)))
                  } for variant,states in arrays.items() if variant != "governed_reference"}
        refinement = float(np.max(np.abs(arrays["governed_neural"]-arrays["governed_neural_half_step"])/state_scale))
        summary = {"scenario": name, "backend_origin": backend.origin, "seed": seed,
                   "success": refinement < 1e-3, "training": training,
                   "phase_reports": phase_reports, "phase_boundaries": boundaries,
                   "errors_against_same_policy_toy_reference": errors,
                   "full_rollout_step_refinement_max_scaled_error": refinement,
                   "step_refinement_threshold": 1e-3,
                   "provider_usage_snapshot": backend.usage,
                   "deliberate_design_fault_injected": inject_bad_first_design,
                   "scope": "Controlled synthetic toy experiment; no live API call is implied by fixture results.",
                   "neural_weight_update_at_context_change": False}
        write_json(directory / "summary.json", summary)
        np.savez_compressed(directory / "trajectories.npz", time=times, **arrays)
        _write_trajectory_csv(directory / "trajectories.csv", times, arrays, problem.state_names)
        if not summary["success"]:
            raise IntegrationError(f"Full rollout failed dt/2 convergence threshold. See {directory/'summary.json'}")
        if verbose:
            print(f"  dt versus dt/2 scaled discrepancy: {refinement:.3g}", flush=True)
            print(f"  Saved: {directory}", flush=True)
        return ExperimentResult(name, directory, times, arrays, summary, contract_records, network, history)
    except Exception as error:
        write_json(directory / "failure.json", {"scenario": name, "origin": backend.origin,
                   "error_type": type(error).__name__, "message": str(error), "provider_usage": backend.usage})
        raise


def demonstrate_repair(name: str = "reactor", network=None, seed: int = 7, epochs: int = 60,
                       results_dir: str | Path = "results/repair_demonstration"):
    """A transparent, deliberately faulty FIRST schema followed by a fixture repair.

    Reuse result.network to avoid retraining. This verifies double-loop wiring,
    not a language model's capacity to notice the fault without machine evidence.
    """
    problem = get_problem(name)
    if network is None:
        network, _, _ = train_network(problem, seed, epochs)
    directory = Path(results_dir)/f"{name}_{uuid.uuid4().hex[:8]}"
    approved = design_contract(problem, problem.phases[0], network, FixtureBackend(), directory,
                               inject_bad_first_design=True, verbose=True)
    records = [json.loads(line) for line in approved.audit_path.read_text().splitlines()]
    assert len(records) == 2 and not records[0]["runtime_gate_approved"] and records[1]["runtime_gate_approved"]
    return records, approved
