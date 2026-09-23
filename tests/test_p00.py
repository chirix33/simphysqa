from dataclasses import FrozenInstanceError
from hashlib import sha256
import json
from pathlib import Path
import socket
import tempfile
import unittest
from unittest.mock import patch

from phi_jepa.artifacts import write_run
from phi_jepa.config import RunConfig
from phi_jepa.contracts import ScenarioInput
from phi_jepa.fixture import run_fixture
from phi_jepa.validation import load_json

ROOT = Path(__file__).resolve().parents[1]


class P00Tests(unittest.TestCase):
    def scenario(self):
        return load_json(ROOT / "tests/fixtures/scenario.json")

    def test_input_is_deeply_immutable_and_unknown_stays_unknown(self):
        raw = self.scenario()
        scenario = ScenarioInput.from_dict(raw)
        raw["initial_facts"][0]["value"] = 42
        self.assertIsNone(scenario.initial_facts[0].value)
        with self.assertRaises(FrozenInstanceError):
            scenario.initial_facts[0].value = 5

    def test_label_and_truth_rejected_at_boundary(self):
        for key in ("terminal_target", "ood_label", "trajectory", "evaluation_truth"):
            with self.subTest(key=key), self.assertRaises(ValueError):
                ScenarioInput.from_dict(self.scenario() | {key: [1]})
        raw = self.scenario()
        raw["initial_facts"][0]["terminal_target"] = 1
        with self.assertRaises(ValueError):
            ScenarioInput.from_dict(raw)
        with self.assertRaises(ValueError):
            run_fixture(self.scenario(), RunConfig(), Path("unused"))

    def test_invalid_config(self):
        for raw in ({"typo": 1}, {"mode": "fixture"}, {"seed": True}, {"seed": -1},
                    {"max_runtime_seconds": float("nan")}, {"mode": "live"},
                    {"max_calls": 1}, {"seed": "11"}, {"max_runtime_seconds": 0}):
            with self.subTest(raw=raw), self.assertRaises(ValueError):
                RunConfig.from_dict(raw)

    def test_live_validates_but_never_falls_back(self):
        config = RunConfig(mode="live", model_id="user-selected", model_revision="pinned-revision",
                           max_calls=1, max_output_tokens=10, max_cost_usd=0.01)
        with tempfile.TemporaryDirectory() as directory, self.assertRaises(ValueError):
            run_fixture(ScenarioInput.from_dict(self.scenario()), config, Path(directory))

    def test_numeric_layout_and_nested_types(self):
        for key, value in (("horizon", float("inf")), ("horizon", 0), ("observables", []), ("initial_time", True)):
            with self.subTest(key=key), self.assertRaises(ValueError):
                ScenarioInput.from_dict(self.scenario() | {key: value})
        raw = self.scenario()
        raw["observables"][0]["index"] = 2
        with self.assertRaises(ValueError):
            ScenarioInput.from_dict(raw)

    def test_deterministic_no_network_artifacts_and_exclusive_writes(self):
        scenario = ScenarioInput.from_dict(self.scenario())
        with tempfile.TemporaryDirectory() as directory, patch.object(socket, "socket", side_effect=AssertionError("offline socket")), patch.object(socket, "getaddrinfo", side_effect=AssertionError("offline DNS")):
            root = Path(directory)
            first = run_fixture(scenario, RunConfig(), root / "one")
            second = run_fixture(scenario, RunConfig(), root / "two")
            self.assertEqual(first.name, second.name)
            for path in first.iterdir():
                self.assertEqual(path.read_bytes(), (second / path.name).read_bytes())
            manifest = load_json(first / "manifest.json")
            for ref in manifest["artifacts"]:
                self.assertEqual(sha256((first / ref["path"]).read_bytes()).hexdigest(), ref["sha256"])
            self.assertTrue(load_json(first / "result.json")["fixture_only"])
            self.assertIsNone(load_json(first / "result.json")["physical_prediction"])
            before = (first / "manifest.json").read_bytes()
            with self.assertRaises(FileExistsError):
                run_fixture(scenario, RunConfig(), root / "one")
            self.assertEqual(before, (first / "manifest.json").read_bytes())
            changed = run_fixture(scenario, RunConfig(seed=22), root / "one")
            self.assertNotEqual(first.name, changed.name)

    def test_writer_rejects_traversal_and_nonfinite_before_writing(self):
        with tempfile.TemporaryDirectory() as directory:
            for name in ("../escape.json", "manifest.json", "C:escape", "a/b"):
                with self.assertRaises(ValueError):
                    write_run(Path(directory), {name: {}}, {})
            with self.assertRaises(ValueError):
                write_run(Path(directory), {"result.json": float("nan")}, {})
            self.assertEqual(list(Path(directory).iterdir()), [])

    def test_duplicate_json_rejected(self):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "bad.json"
            path.write_text('{"mode":"offline","mode":"live"}')
            with self.assertRaises(ValueError):
                load_json(path)


if __name__ == "__main__":
    unittest.main()
