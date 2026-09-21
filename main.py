"""End-to-end driver: mirrors the original notebook's run-all-examples flow.

Run with ``python main.py``. Set ``OPENAI_API_KEY`` in the environment first
when ``config.MODE == "openai"``, or edit ``config.py`` to use ``"fixture"``
mode for an offline, no-credentials demonstration.
"""
from __future__ import annotations

from pprint import pprint

import numpy as np
import torch

import config
from agents import make_backend
from display import audit_rows, plot_result, print_summary
from pipeline import demonstrate_repair, run_example
from problems import get_problem
from schemas import Critique, make_evidence
from training import DTYPE
from verification import approval_gate


def build_backend():
    options = {}
    if config.MODE == "openai":
        options = {
            "model": config.MODEL,
            "max_calls": config.MAX_API_CALLS,
            "max_output_tokens": config.MAX_OUTPUT_TOKENS,
        }
    backend = make_backend(
        config.MODE,
        out_dir=config.RESULTS_ROOT / "provider_requests",
        **options,
    )
    print("Ready:", backend.origin)
    return backend


def run_all_examples(backend) -> dict:
    results = {}
    for name in ("driving", "rocket", "reactor", "oscillator", "sir"):
        result = run_example(
            name,
            backend=backend,
            seed=config.SEED,
            epochs=config.EPOCHS,
            results_dir=config.RESULTS_ROOT,
        )
        results[name] = result
        print_summary(result)
        plot_result(result)
        # These are this run's actual review records, not a sample transcript.
        pprint(audit_rows(result))
    return results


def show_example_contract(results: dict) -> None:
    contract = results["reactor"].contracts[0]
    print("Architect's blueprint:")
    pprint(contract.blueprint.model_dump())
    print("\nDynamic schema:")
    pprint(contract.instance.model_json_schema())
    print("\nExecutor's sourced values:")
    pprint(contract.instance.model_dump())


def run_repair_demonstrations(results: dict) -> dict:
    """Deliberately injects a bad design for each example, using offline fixtures."""
    repair_records = {}
    for name, result in results.items():
        records, approved_contract = demonstrate_repair(
            name,
            network=result.network,
            results_dir=config.RESULTS_ROOT / "repair_demonstrations",
        )
        repair_records[name] = records
        assert records[0]["runtime_gate_approved"] is False
        assert records[-1]["runtime_gate_approved"] is True
        print(f"\n{name}: rejected first design -> accepted repaired design")
        for record in records:
            pprint({
                "round": record["round"],
                "failed_checks": record["runtime_gate_failures"],
                "critic_verdict": record["critic_response"]["verdict"],
                "python_approved": record["runtime_gate_approved"],
            })
    return repair_records


def run_ordinary_python_checks(results: dict) -> None:
    """These checks use assert, not a separate test runner. They make no API calls."""
    assert set(results) == {"driving", "rocket", "reactor", "oscillator", "sir"}
    for name, result in results.items():
        assert result.summary["success"], f"{name}: experiment did not pass"
        assert len(result.contracts) == 2, f"{name}: a phase contract is missing"
        assert np.isfinite(result.trajectories["governed_neural"]).all()
        assert result.summary["full_rollout_step_refinement_max_scaled_error"] < 1e-3
        assert result.summary["training"]["split_sizes"] == {
            "train": 1024, "validation": 256, "test": 256,
        }
    print("All five runs: finite trajectories, two phase contracts, split sizes, and dt/2 checks passed.")

    # Driving: a proposal of +3 at v=11.9 is restricted by the speed barrier to +0.2.
    problem = get_problem("driving")
    params = problem.default_parameters | {"acceleration_limit": 1.0}
    change = problem.enforce(torch.tensor([11.9], dtype=DTYPE),
                             torch.tensor([3.0], dtype=DTYPE), params)
    assert abs(change.item() - 0.2) < 1e-10
    print("Driving: the speed barrier acts before the upper boundary is crossed.")

    # Fuel burn: no fuel means no fuel flow or thrust; gravity still acts.
    problem = get_problem("rocket")
    change = problem.enforce(torch.tensor([1., 0., 0.], dtype=DTYPE),
                             torch.tensor([1., 999., -999.], dtype=DTYPE),
                             problem.default_parameters)
    assert change[2].item() == 0.0
    assert change[1].item() == -problem.default_parameters["gravity"]
    print("Fuel burn: zero fuel means zero thrust, not zero gravity.")

    # Reactor: when reactant is gone, a hot reactor must be allowed to cool.
    problem = get_problem("reactor")
    change = problem.enforce(torch.tensor([0., 1., 305.], dtype=DTYPE),
                             torch.tensor([-99., 99., 99.], dtype=DTYPE),
                             problem.default_parameters)
    assert abs((change[0] + change[1]).item()) < 1e-12
    assert change[2].item() < 0.0
    print("Reactor: material balance holds and cooling is permitted.")

    # Oscillator: p=0 is valid, with no division-by-zero failure.
    problem = get_problem("oscillator")
    change = problem.enforce(torch.tensor([1., 0.], dtype=DTYPE),
                             torch.tensor([999., 999.], dtype=DTYPE),
                             problem.default_parameters)
    assert torch.isfinite(change).all() and change[0].item() == 0.0
    print("Oscillator: zero momentum is handled without a singularity.")

    # SIR: an infection-free closed population cannot create infection.
    problem = get_problem("sir")
    change = problem.enforce(torch.tensor([1., 0., 0.], dtype=DTYPE),
                             torch.tensor([-999., 999., 999.], dtype=DTYPE),
                             problem.default_parameters)
    assert torch.equal(change, torch.zeros(3, dtype=DTYPE))
    print("SIR: a disease-free population stays disease-free in this toy model.")

    # A Critic saying 'approve' cannot override a failed Python check.
    evidence = [make_evidence("deliberate_failure", False, "This check deliberately failed.")]
    critique = Critique(
        verdict="approve", issues=[], evidence_ids=["deliberate_failure"],
        suggested_changes=[], decision_summary="Deliberately incorrect approval for this test.",
    )
    accepted, failures = approval_gate(evidence, critique)
    assert accepted is False and "deliberate_failure" in failures
    print("Approval gate: a failed machine check cannot be overruled by the Critic.")


def compare_runs(results: dict, backend) -> None:
    for name, result in results.items():
        print(
            f"{name:12s} | "
            f"test derivative MSE = {result.summary['training']['test_normalized_mse']:.6g} | "
            f"dt/2 difference = {result.summary['full_rollout_step_refinement_max_scaled_error']:.6g} | "
            f"contract rounds = {[contract.rounds for contract in result.contracts]}"
        )
    print("\nActual selected-mode usage:")
    pprint(backend.usage)


def main() -> None:
    backend = build_backend()
    results = run_all_examples(backend)
    show_example_contract(results)
    run_repair_demonstrations(results)
    run_ordinary_python_checks(results)
    compare_runs(results, backend)


if __name__ == "__main__":
    main()
