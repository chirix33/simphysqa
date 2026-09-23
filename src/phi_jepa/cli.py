import argparse
from pathlib import Path
from .config import RunConfig
from .contracts import ScenarioInput
from .fixture import run_fixture
from .validation import load_json


def main(argv=None) -> int:
    parser = argparse.ArgumentParser(prog="phi-jepa", description="P00 fixture plumbing; no trained model or live execution.")
    commands = parser.add_subparsers(dest="command", required=True)
    validate = commands.add_parser("validate-config", help="validate offline/live JSON without calling providers")
    validate.add_argument("--config", type=Path, required=True)
    fixture = commands.add_parser("fixture", help="write an explicitly fixture-only input round trip")
    fixture.add_argument("--config", type=Path, required=True)
    fixture.add_argument("--input", type=Path, required=True)
    fixture.add_argument("--output", type=Path, required=True)
    args = parser.parse_args(argv)
    try:
        config = RunConfig.from_dict(load_json(args.config))
        if args.command == "validate-config":
            print("Configuration valid; no execution authorized or performed.")
        else:
            scenario = ScenarioInput.from_dict(load_json(args.input))
            print(run_fixture(scenario, config, args.output))
    except (ValueError, OSError) as exc:
        parser.exit(2, f"phi-jepa: {exc}\n")
    return 0
