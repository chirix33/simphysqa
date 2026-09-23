import argparse
from pathlib import Path
from .config import RunConfig
from .contracts import ScenarioInput
from .fixture import run_fixture
from .validation import load_json


def main(argv=None) -> int:
    parser = argparse.ArgumentParser(prog="phi-jepa", description="Offline fixtures, benchmark data and numerical evaluation; no trained model or live execution.")
    commands = parser.add_subparsers(dest="command", required=True)
    validate = commands.add_parser("validate-config", help="validate offline/live JSON without calling providers")
    validate.add_argument("--config", type=Path, required=True)
    fixture = commands.add_parser("fixture", help="write an explicitly fixture-only input round trip")
    fixture.add_argument("--config", type=Path, required=True)
    fixture.add_argument("--input", type=Path, required=True)
    fixture.add_argument("--output", type=Path, required=True)
    generate = commands.add_parser("generate-data", help="generate a small passive-stopping wiring dataset")
    generate.add_argument("--config", type=Path, required=True)
    generate.add_argument("--output", type=Path, required=True)
    data_validate = commands.add_parser("validate-data", help="verify dataset integrity, partitions, oracle and numerical refinement")
    data_validate.add_argument("--dataset", type=Path, required=True)
    data_validate.add_argument("--output", type=Path, required=True)
    evaluate = commands.add_parser("evaluate", help="evaluate an external numerical prediction JSON file")
    evaluate.add_argument("--dataset", type=Path, required=True)
    evaluate.add_argument("--predictions", type=Path, required=True)
    evaluate.add_argument("--output", type=Path, required=True)
    args = parser.parse_args(argv)
    try:
        if args.command in ("validate-config", "fixture"):
            config = RunConfig.from_dict(load_json(args.config))
        if args.command == "validate-config":
            print("Configuration valid; no execution authorized or performed.")
        elif args.command == "fixture":
            scenario = ScenarioInput.from_dict(load_json(args.input))
            print(run_fixture(scenario, config, args.output))
        elif args.command == "generate-data":
            from .benchmarks.config import DatasetConfig
            from .benchmarks.dataset import generate_run
            from .validation import convert
            print(generate_run(convert(DatasetConfig, load_json(args.config)), args.output))
        elif args.command == "validate-data":
            from .benchmarks.dataset import validate_run
            print(validate_run(args.dataset, args.output))
        elif args.command == "evaluate":
            from .evaluation import evaluate_run
            print(evaluate_run(args.dataset, args.predictions, args.output))
    except (ValueError, OSError) as exc:
        parser.exit(2, f"phi-jepa: {exc}\n")
    return 0
