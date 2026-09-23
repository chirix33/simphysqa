"""Deterministic input round trip, explicitly without numerical prediction."""
from dataclasses import asdict
from pathlib import Path
from .artifacts import code_provenance, digest, environment, write_run
from .config import RunConfig
from .contracts import ScenarioInput


def run_fixture(scenario: ScenarioInput, config: RunConfig, output: Path) -> Path:
    if type(scenario) is not ScenarioInput or type(config) is not RunConfig:
        raise ValueError("typed ScenarioInput and RunConfig required")
    if config.mode != "offline":
        raise ValueError("P00 fixture requires offline mode; live execution is not implemented")
    input_data, settings = asdict(scenario), asdict(config)
    result = {"fixture_only": True, "status": "plumbing_only_no_prediction", "scenario_id": scenario.scenario_id,
              "physical_prediction": None, "empirical_metrics": None,
              "observable_ids": [o.quantity_id for o in scenario.observables]}
    provenance = {"fixture_only": True, "mode": config.mode, "seed": config.seed,
                  "input_sha256": digest(input_data), "config_sha256": digest(settings),
                  "code": code_provenance(), "environment": environment(), "cache_policy": config.cache_policy,
                  "dataset_sha256": None, "split_sha256": None, "model_sha256": None,
                  "prompt_sha256": None, "schema_sha256": None, "checkpoint_sha256": None,
                  "unused_hashes_reason": "P00 input round trip has no dataset, model, prompts or extracted schema",
                  "budgets": settings, "usage": {"model_calls": 0, "solves": 0, "retries": 0, "tokens": 0, "errors": 0}}
    return write_run(output, {"input.json": input_data, "config.json": settings, "result.json": result}, provenance)
