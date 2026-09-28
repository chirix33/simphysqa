import ast
from contextlib import redirect_stdout, redirect_stderr
from copy import deepcopy
from dataclasses import asdict, replace
import importlib
import io
import json
from pathlib import Path
import random
import socket
import tempfile
import unittest
from unittest.mock import patch

from phi_jepa.artifacts import canonical, code_provenance, digest, read_run
from phi_jepa.benchmarks.config import Counts, DatasetConfig
from phi_jepa.benchmarks.dataset import generate, generate_run, is_combination, to_input, validate_dataset
from phi_jepa.benchmarks.physical_checks import passive_checks
from phi_jepa.benchmarks.stopping import FrictionEvent, StoppingCase, analytic, numerical, sample_grid
from phi_jepa.cli import main
from phi_jepa.contracts import ScenarioInput
from phi_jepa.data import EvaluationTruth, TrainingExample, fit_scaler
from phi_jepa.evaluation import checked_dataset, evaluate
from phi_jepa.validation import convert

ROOT = Path(__file__).resolve().parents[1]


class OracleTests(unittest.TestCase):
    def check(self, case, expected):
        grid = sample_grid(case)
        exact = analytic(case, grid)
        self.assertEqual(exact.states[0], (case.x0, case.v0))
        self.assertEqual(exact.times[0], 0)
        self.assertEqual(exact.times[-1], case.horizon)
        for actual, target in zip(exact.states[-1], expected):
            self.assertAlmostEqual(actual, target, places=10)
        coarse = numerical(case, grid, 0.02)
        fine = numerical(case, grid, 0.01)
        coarse_error = max(abs(a[0] - b[0]) for a, b in zip(coarse.states, exact.states))
        fine_error = max(abs(a[0] - b[0]) for a, b in zip(fine.states, exact.states))
        self.assertLessEqual(fine_error, coarse_error + 1e-9)
        self.assertLessEqual(fine_error, case.gravity * max([case.mu, *(e.mu for e in case.events)]) * case.horizon * 0.01 + 1e-8)
        for state, target in zip(fine.states, exact.states):
            self.assertAlmostEqual(state[1], target[1], places=8)
            self.assertGreaterEqual(state[1], 0)

    def test_constant_closed_form_boundaries(self):
        for v, mu, horizon, expected in (
                (0, 1, 3, (-5, 0)), (2, 0, 3, (1, 2)),
                (2, 1, 1, (-3.5, 1)), (2, 1, 2, (-3, 0)), (2, 1, 3, (-3, 0))):
            with self.subTest(v=v, mu=mu, horizon=horizon):
                self.check(StoppingCase(-5, v, mu, 1, horizon), expected)

    def test_events_before_at_after_stop_and_terminal(self):
        for events, expected in (
                ((FrictionEvent(0.5, 0),), (4.625, 1.5)),
                ((FrictionEvent(2, 0),), (2, 0)),
                ((FrictionEvent(2.5, 0),), (2, 0)),
                ((FrictionEvent(3, 0),), (2, 0)),
                ((FrictionEvent(0.5, 0), FrictionEvent(1, 1)), (2.75, 0))):
            with self.subTest(events=events):
                case = StoppingCase(0, 2, 1, 1, 3, events)
                self.check(case, expected)
                result = analytic(case, sample_grid(case))
                for event in events:
                    self.assertIn(event.time, result.times)
        self.check(StoppingCase(0, 2, 0, 1, 4, (FrictionEvent(1, 1),)), (4, 0))

    def test_state_continuity_and_sample_grid_invariance(self):
        case = StoppingCase(0, 4, 1, 1, 4, (FrictionEvent(1, 0), FrictionEvent(2, 2)))
        result = analytic(case, (0, 1, 2, 4))
        self.assertEqual(result.states[1], (3.5, 3))
        self.assertEqual(result.states[2], (6.5, 3))
        self.assertEqual(result.states[-1], analytic(case, (0, 4)).states[-1])

    def test_numerical_is_independent_and_refines(self):
        case = StoppingCase(-1, 6, 0.5, 2, 2)
        grid = (0, 2)
        with patch("phi_jepa.benchmarks.stopping.constant_state", side_effect=AssertionError("analytic call")), patch("phi_jepa.benchmarks.stopping.analytic", side_effect=AssertionError("oracle call")):
            coarse = numerical(case, grid, 0.1)
            fine = numerical(case, grid, 0.05)
        exact_x = 9.0
        self.assertGreater(coarse.states[-1][0] - exact_x, 0)
        self.assertAlmostEqual((fine.states[-1][0] - exact_x) / (coarse.states[-1][0] - exact_x), 0.5, places=10)

    def test_random_event_agreement_without_dataset_selection(self):
        rng = random.Random(734)
        for _ in range(20):
            case = StoppingCase(rng.uniform(-10, 10), rng.uniform(0, 20), rng.uniform(0, 1), 9.81, 4,
                                (FrictionEvent(0.7, rng.uniform(0, 1)), FrictionEvent(2.3, 0)))
            self.check(case, analytic(case, (0, 4)).states[-1])

    def test_invalid_case_event_grid_and_step_budget(self):
        raw = asdict(StoppingCase(0, 2, 0.5, 9.81, 3))
        for change in ({"v0": -1}, {"mu": -1}, {"gravity": 0}, {"horizon": 0}, {"horizon": -1},
                       {"x0": float("nan")}, {"v0": float("inf")}, {"gravity": "9.81"}, {"v0": True},
                       {"mu": 1e308, "gravity": 1e308}, {"units": ["cm", "km/h"]},
                       {"events": [{"time": 0, "mu": 1}]}, {"events": [{"time": 4, "mu": 1}]},
                       {"events": [{"time": 1, "mu": 1}, {"time": 1, "mu": 0}]},
                       {"events": [{"time": 2, "mu": 1}, {"time": 1, "mu": 0}]}):
            with self.subTest(change=change), self.assertRaises(ValueError):
                convert(StoppingCase, raw | change)
        case = convert(StoppingCase, raw)
        for grid in ((0, 2), (1, 3), (0, 1, 1, 3), (0, float("nan"), 3)):
            with self.assertRaises(ValueError):
                analytic(case, grid)
        with self.assertRaises(ValueError):
            numerical(case, (0, 3), 0.001, max_steps=5)


class DatasetTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.data = generate(DatasetConfig())

    def test_deterministic_partitioning_support_and_outcomes(self):
        self.assertEqual(digest(self.data), digest(generate(DatasetConfig())))
        self.assertNotEqual(digest(self.data), digest(generate(DatasetConfig(seed=22))))
        report = validate_dataset(self.data)
        self.assertEqual((report["families"], report["samples"]), (32, 128))
        self.assertGreater(report["moving_samples"], 0)
        self.assertGreater(report["stopped_samples"], 0)
        ids = [family for group in self.data["partitions.json"].values() for family in group]
        self.assertEqual(len(ids), len(set(ids)))
        for scenario in self.data["inputs.json"]:
            self.assertRegex(scenario["scenario_id"], r"^[0-9a-f]{32}$")
            self.assertRegex(scenario["family_id"], r"^[0-9a-f]{32}$")
        train = [f["case"] for f in self.data["families.json"] if f["split"] == "train"]
        combo = next(f["case"] for f in self.data["families.json"] if f["split"] == "combination")
        self.assertIn(combo["v0"], [f["v0"] for f in train])
        self.assertIn(combo["mu"], [f["mu"] for f in train])
        for f in self.data["families.json"]:
            if f["split"] in ("train", "selection", "calibration", "id_test"):
                self.assertFalse(is_combination(f["case"]["v0"], f["case"]["mu"], DatasetConfig()))

    def test_correlated_views_and_complete_label_free_inputs(self):
        scenarios = {s["scenario_id"]: ScenarioInput.from_dict(s) for s in self.data["inputs.json"]}
        truths = {t["scenario_id"]: t for t in self.data["truths.json"]}
        forbidden = {"split", "ood_type", "terminal", "trajectory", "solution", "case"}
        for raw in self.data["inputs.json"]:
            self.assertFalse(forbidden & raw.keys())
            for key in forbidden:
                with self.assertRaises(ValueError):
                    ScenarioInput.from_dict(raw | {key: "label"})
        for family in self.data["families.json"]:
            views = [scenarios[key] for key in family["scenario_ids"]]
            self.assertEqual(len(views), 4)
            self.assertEqual(len({v.horizon for v in views}), 2)
            self.assertEqual({v.family_id for v in views}, {family["family_id"]})
            self.assertEqual({truths[v.scenario_id]["split"] for v in views}, {family["split"]})
            for view in views:
                for fact in view.initial_facts:
                    self.assertIn(repr(fact.value), view.question)
                for event in view.permitted_events:
                    self.assertIn(event, view.question)

    def test_train_only_scaling_and_constant_coordinates(self):
        _, _, original = checked_dataset(self.data)
        altered = deepcopy(self.data)
        for truth in altered["truths.json"]:
            if truth["split"] != "train":
                truth["terminal"] = (90000.0, 0.0)
                truth["trajectory"] = (*truth["trajectory"][:-1], truth["terminal"])
        self.assertEqual(checked_dataset(altered)[2], original)
        heldout = next(t for t in self.data["truths.json"] if t["split"] == "selection")
        scenario = next(s for s in self.data["inputs.json"] if s["scenario_id"] == heldout["scenario_id"])
        with self.assertRaises(ValueError):
            TrainingExample(ScenarioInput.from_dict(scenario), convert(EvaluationTruth, heldout))
        with self.assertRaises(ValueError):
            fit_scaler((convert(EvaluationTruth, heldout),))
        constant = deepcopy(self.data)
        for t in constant["truths.json"]:
            if t["split"] == "train":
                t["terminal"] = (2.0, 0.0)
                t["trajectory"] = (*t["trajectory"][:-1], t["terminal"])
        inputs = {s["scenario_id"]: ScenarioInput.from_dict(s) for s in constant["inputs.json"]}
        scaler = fit_scaler(tuple(TrainingExample(inputs[t["scenario_id"]], convert(EvaluationTruth, t)) for t in constant["truths.json"] if t["split"] == "train"))
        self.assertEqual(scaler.constant_coordinates, (True, True))
        self.assertEqual(scaler.scales, (1, 1))
        self.assertEqual(len(scaler.training_family_ids), 16)

    def test_validation_rejects_label_units_partition_and_truth_corruption(self):
        for modification in ("units", "partition", "truth", "label", "scaler"):
            bad = deepcopy(self.data)
            if modification == "units":
                bad["inputs.json"][0]["initial_facts"][0]["unit"] = "cm"
            elif modification == "partition":
                bad["partitions.json"]["selection"].append(bad["partitions.json"]["train"][0])
            elif modification == "truth":
                t = bad["truths.json"][0]
                t["terminal"] = (t["terminal"][0] + 1, t["terminal"][1])
                t["trajectory"] = (*t["trajectory"][:-1], t["terminal"])
            elif modification == "label":
                bad["inputs.json"][0]["terminal"] = [1, 2]
            else:
                bad["scaler.json"]["means"] = (999, 999)
            with self.subTest(modification=modification), self.assertRaises(ValueError):
                validate_dataset(bad)

    def test_config_limits_and_unknown_keys(self):
        for raw in ({"typo": 1}, {"counts": {"train": 1}}, {"counts": {"train": 1000}},
                    {"time_fractions": [1, 0.5]}, {"combination_speed_min": 50}, {"gravity": float("nan")},
                    {"paraphrases": 3}, {"horizon": {"low": 0, "high": 5}}):
            with self.subTest(raw=raw), self.assertRaises(ValueError):
                convert(DatasetConfig, raw)
        small = DatasetConfig(counts=Counts(2, 1, 1, 1, 1, 1, 1, 1), paraphrases=1, time_fractions=(1.0,))
        self.assertEqual(validate_dataset(generate(small))["samples"], 9)


class EvaluationTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.data = generate(DatasetConfig())

    def test_oracle_and_corrupted_predictions_have_explicit_denominators(self):
        report = evaluate(self.data, self.data["oracle_predictions.json"])
        exact = report["overall"]
        self.assertEqual(exact["expected_predictions"], 128)
        self.assertEqual(exact["train_normalized_macro_mse_valid_only"], 0)
        self.assertEqual(exact["pcvr"]["ratio"], 0)
        self.assertEqual(exact["pcvr"]["evaluated_denominator"], 512)
        self.assertEqual(exact["trajectory"]["valid"], 128)
        broken = evaluate(self.data, self.data["corrupted_predictions.json"])["overall"]
        self.assertEqual((broken["valid_predictions"], broken["missing_predictions"], broken["invalid_predictions"]), (126, 1, 1))
        self.assertEqual(broken["pcvr"]["violation_numerator"], 2)
        self.assertEqual(broken["pcvr"]["evaluated_denominator"], 504)
        self.assertEqual(broken["pcvr"]["eligible_checks"], 512)
        self.assertGreater(broken["train_normalized_macro_mse_valid_only"], 0)

    def test_missing_and_empty_physical_coverage_are_unavailable(self):
        missing = evaluate(self.data, {"producer": "missing_fixture", "predictions": []})["overall"]
        self.assertEqual(missing["failed_predictions"], 128)
        self.assertIsNone(missing["train_normalized_macro_mse_valid_only"])
        self.assertIsNone(missing["pcvr"]["ratio"])
        self.assertIsNone(missing["trajectory"]["rmse_physical_units"]["x"])
        unsupported = deepcopy(self.data)
        for s in unsupported["inputs.json"]:
            s["initial_facts"] = ()
        pcvr = evaluate(unsupported, unsupported["oracle_predictions.json"])["overall"]["pcvr"]
        self.assertEqual(pcvr["unsupported_checks"], 512)
        self.assertEqual(pcvr["eligible_checks"], 0)
        self.assertIsNone(pcvr["coverage"])
        self.assertIsNone(pcvr["ratio"])

    def test_wrong_but_weakly_compliant_is_not_correct_answer(self):
        envelope = deepcopy(self.data["oracle_predictions.json"])
        row = envelope["predictions"][0]
        scenario = ScenarioInput.from_dict(self.data["inputs.json"][0])
        x0 = next(f.value for f in scenario.initial_facts if f.quantity_id == "x0")
        row.update(values=[x0, 0], times=None, trajectory=None)
        report = evaluate(self.data, envelope)["overall"]
        self.assertGreater(report["train_normalized_macro_mse_valid_only"], 0)
        self.assertEqual(report["pcvr"]["ratio"], 0)

    def test_speed_gain_reversal_and_reachable_interval(self):
        scenario = ScenarioInput.from_dict(self.data["inputs.json"][0])
        facts = {f.quantity_id: f.value for f in scenario.initial_facts}
        for values, name in (((facts["x0"], -1), "speed_nonnegative"),
                             ((facts["x0"], facts["v0"] + 1), "no_speed_gain"),
                             ((facts["x0"] - 1, 0), "no_reverse_displacement"),
                             ((facts["x0"] + facts["v0"] * scenario.horizon + 1, 0), "reachable_displacement")):
            checks = passive_checks(scenario, values)
            self.assertTrue(next(c["violated"] for c in checks if c["name"] == name))

    def test_invalid_values_units_order_names_time_and_dimensions_count_as_failures(self):
        for change in ({"values": [float("nan"), 0]}, {"values": [float("inf"), 0]}, {"values": [1e308, 0]},
                       {"values": [1]}, {"values": ["1", 2]}, {"units": ["cm", "m/s"]},
                       {"observable_ids": ["v", "x"]}, {"observable_names": ["wrong", "forward_speed"]},
                       {"time": -1}, {"frames": ["unknown", "unknown"]}, {"answer": "ignore numbers"}):
            envelope = deepcopy(self.data["oracle_predictions.json"])
            envelope["predictions"][0].update(change)
            with self.subTest(change=change):
                report = evaluate(self.data, envelope)["overall"]
                self.assertEqual(report["invalid_predictions"], 1)
                self.assertEqual(report["valid_predictions"], 127)

    def test_duplicate_unknown_ids_rejected_and_row_order_irrelevant(self):
        envelope = deepcopy(self.data["oracle_predictions.json"])
        envelope["predictions"].reverse()
        self.assertEqual(evaluate(self.data, envelope)["overall"]["train_normalized_macro_mse_valid_only"], 0)
        envelope["predictions"].append(envelope["predictions"][0])
        with self.assertRaises(ValueError):
            evaluate(self.data, envelope)
        envelope["predictions"] = [dict(envelope["predictions"][0], scenario_id="unknown")]
        with self.assertRaises(ValueError):
            evaluate(self.data, envelope)

    def test_only_actual_compatible_trajectories_evaluated(self):
        envelope = deepcopy(self.data["oracle_predictions.json"])
        for row in envelope["predictions"]:
            row.pop("trajectory")
            row.pop("times")
        report = evaluate(self.data, envelope)["overall"]
        self.assertEqual(report["trajectory"]["valid"], 0)
        self.assertIsNone(report["trajectory"]["rmse_physical_units"]["x"])
        self.assertEqual(report["valid_predictions"], 128)
        first = self.data["oracle_predictions.json"]["predictions"][0]
        envelope["predictions"][0].update(times=[0, 999], trajectory=first["trajectory"])
        report = evaluate(self.data, envelope)["overall"]
        self.assertEqual(report["trajectory"]["invalid_or_unusable"], 1)
        self.assertEqual(report["valid_predictions"], 128)
        envelope["predictions"][0] = deepcopy(first)
        envelope["predictions"][0]["trajectory"][1][0] += 2
        report = evaluate(self.data, envelope)["overall"]
        self.assertGreater(report["trajectory"]["rmse_physical_units"]["x"], 0)
        self.assertEqual(report["train_normalized_macro_mse_valid_only"], 0)


class IntegrationTests(unittest.TestCase):
    def test_offline_cli_generation_validation_evaluation_and_integrity(self):
        with tempfile.TemporaryDirectory() as directory, patch.object(socket, "socket", side_effect=AssertionError("network")), patch.object(socket, "getaddrinfo", side_effect=AssertionError("DNS")):
            root = Path(directory)
            def command(*args):
                output = io.StringIO()
                with redirect_stdout(output):
                    self.assertEqual(main(list(args)), 0)
                return Path(output.getvalue().strip())
            dataset = command("generate-data", "--config", str(ROOT / "configs/p01_fixture.json"), "--output", str(root / "data"))
            repeated = command("generate-data", "--config", str(ROOT / "configs/p01_fixture.json"), "--output", str(root / "repeat"))
            self.assertEqual(dataset.name, repeated.name)
            for file in dataset.iterdir():
                self.assertEqual(file.read_bytes(), (repeated / file.name).read_bytes())
            validation = command("validate-data", "--dataset", str(dataset), "--output", str(root / "validation"))
            self.assertEqual(read_run(validation)[0]["validation.json"]["samples"], 128)
            for filename in ("oracle_predictions.json", "corrupted_predictions.json"):
                result = command("evaluate", "--dataset", str(dataset), "--predictions", str(dataset / filename), "--output", str(root / "eval"))
                report = read_run(result)[0]["metrics.json"]
                self.assertEqual(report["usage"]["model_calls"], 0)
            bad = root / "unknown.json"
            bad.write_text(json.dumps({"producer": "test", "predictions": [{"scenario_id": "unknown"}]}))
            with redirect_stderr(io.StringIO()), self.assertRaises(SystemExit) as caught:
                main(["evaluate", "--dataset", str(dataset), "--predictions", str(bad), "--output", str(root / "no_output")])
            self.assertEqual(caught.exception.code, 2)
            self.assertFalse((root / "no_output").exists())
            (dataset / "inputs.json").write_text("[]")
            with self.assertRaises(ValueError):
                read_run(dataset)

    def test_no_physics_imports_in_input_or_fixture_inference_and_recursive_hashes(self):
        for name in ("contracts", "fixture", "config", "validation"):
            module = importlib.import_module("phi_jepa." + name)
            tree = ast.parse(Path(module.__file__).read_text())
            for node in ast.walk(tree):
                if isinstance(node, ast.ImportFrom):
                    self.assertFalse(set((node.module or "").split(".")) & {"benchmarks", "evaluation", "data"})
        data = generate(DatasetConfig())
        with patch("phi_jepa.benchmarks.stopping.analytic", side_effect=AssertionError("oracle execution")):
            self.assertEqual(evaluate(data, data["oracle_predictions.json"])["usage"]["solves"], 0)
        self.assertIn("benchmarks/stopping.py", code_provenance()["source_files"])


if __name__ == "__main__":
    unittest.main()
