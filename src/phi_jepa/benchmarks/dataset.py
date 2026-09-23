"""Small, disclosed synthetic dataset. Labels/partitions never enter ScenarioInput."""
from dataclasses import asdict
from pathlib import Path
import random
from uuid import UUID
from ..artifacts import code_provenance, digest, environment, read_run, write_run
from ..contracts import ObservedFact, ObservableSpec, ScenarioInput
from ..data import EvaluationTruth, TrainingExample, fit_scaler
from ..validation import convert
from .config import DatasetConfig
from .stopping import FrictionEvent, StoppingCase, analytic, numerical, sample_grid

LAYOUT = (ObservableSpec("x", "position", "m", "fixed_1d_origin", 0, True, 1e-8),
          ObservableSpec("v", "forward_speed", "m/s", "fixed_1d_origin", 1, True, 1e-8))
ID_SPLITS = ("train", "selection", "calibration", "id_test")


def is_combination(v: float, mu: float, config: DatasetConfig) -> bool:
    return v >= config.combination_speed_min and mu <= config.combination_friction_max


def to_input(case: StoppingCase, scenario_id: str, family_id: str, wording: int) -> ScenarioInput:
    if wording not in (0, 1):
        raise ValueError("unsupported paraphrase")
    events = tuple(f"At t={e.time!r} s, friction coefficient changes to {e.mu!r} (dimensionless)." for e in case.events)
    description = (f"At t=0 s, x0={case.x0!r} m relative to fixed_1d_origin, forward speed v0={case.v0!r} m/s, "
                   f"friction coefficient mu={case.mu!r} (dimensionless), and gravity g={case.gravity!r} m/s^2. "
                   "A body slides on a horizontal surface; passive friction is the only horizontal force. "
                   "Once stopped it stays at rest. " + (" ".join(events) if events else "No friction changes occur.") +
                   f" Return position x in m and forward speed v in m/s at t={case.horizon!r} s.")
    question = ("Consider one-dimensional passive stopping. " if wording == 0 else "Determine the terminal motion of this sliding body. ") + description
    facts = tuple(ObservedFact(name, value, unit, "explicit_scenario") for name, value, unit in
                  (("x0", case.x0, "m"), ("v0", case.v0, "m/s"), ("mu", case.mu, "1"), ("g", case.gravity, "m/s^2")))
    return ScenarioInput(scenario_id, family_id, question, facts, LAYOUT, 0.0, case.horizon, events)


def source_registry() -> list[dict]:
    return [
        {"id": "passive_stopping_v1", "status": "implemented_local_analytic_benchmark", "license": None,
         "download_status": "not_required", "suitability": "P01 wiring and independently checked 1D motion",
         "conversion": "complete scenario templates; x/v SI terminal and trajectory labels", "rejection_reason": None},
        *[{"id": name, "status": "not_adopted", "license": None, "download_status": "not_verified",
           "suitability": suitability, "conversion": conversion, "rejection_reason": "deferred; license/revision/coverage review required"}
          for name, suitability, conversion in
          (("MuJoCo", "candidate articulated/contact benchmark", "author model and validate simulation; generate questions"),
           ("DeepMind Control Suite", "candidate robot trajectories, not a question corpus", "select environment and verify observable/answer mapping"),
           ("PDEBench", "candidate actual PDE/fluid fields", "field conditioning and target layout need a new interface"))],
        {"id": "professor_demo", "status": "historical_reference_only", "license": None,
         "download_status": "local_handoff", "suitability": "prompt/format reference", "conversion": None,
         "rejection_reason": "not a verified main-study benchmark; see supplied audit"}]


def generate(config: DatasetConfig) -> dict:
    rng = random.Random(config.seed)
    opaque = lambda: UUID(int=rng.getrandbits(128), version=4).hex
    draw = lambda interval: rng.uniform(interval.low, interval.high)
    high_v = (config.combination_speed_min + config.speed.high) / 2
    low_v = (config.speed.low + config.combination_speed_min) / 2
    low_mu = (config.friction.low + config.combination_friction_max) / 2
    high_mu = (config.combination_friction_max + config.friction.high) / 2
    families, inputs, truths, predictions = [], [], [], []
    partitions = {split: [] for split in vars(config.counts)}
    solves = 0
    for split, count in vars(config.counts).items():
        for index in range(count):
            # Assign the family to its partition before any correlated variant exists.
            family_id = opaque()
            v, mu = draw(config.speed), draw(config.friction)
            if split in ID_SPLITS:
                for _ in range(10000):
                    if not is_combination(v, mu, config):
                        break
                    v, mu = draw(config.speed), draw(config.friction)
                else:
                    raise ValueError("cannot sample ID outside reserved joint region")
            horizon = draw(config.horizon)
            if split == "train" and index < 2:
                # Exact marginal anchors demonstrate support of the combination fixture.
                v, mu = (high_v, high_mu) if index == 0 else (low_v, low_mu)
                horizon = config.horizon.low + 0.1 * (config.horizon.high - config.horizon.low) if index == 0 else config.horizon.high
            if split == "parameter_low":
                mu = draw(config.low_friction)
            elif split == "parameter_high":
                mu = draw(config.high_friction)
            elif split == "combination":
                v, mu = high_v, low_mu
            events = (FrictionEvent(config.horizon.low / 2, 0.0),) if split == "event" else ()
            base = StoppingCase(draw(config.position), v, mu, config.gravity, horizon, events)
            family = {"family_id": family_id, "split": split, "case": asdict(base), "scenario_ids": []}
            families.append(family)
            partitions[split].append(family_id)
            for fraction in config.time_fractions:
                query_time = config.horizon.low + fraction * (base.horizon - config.horizon.low)
                case = StoppingCase(base.x0, base.v0, base.mu, base.gravity, query_time, base.events)
                result = analytic(case, sample_grid(case, config.sample_intervals))
                solves += 1
                for wording in range(config.paraphrases):
                    scenario_id = opaque()
                    family["scenario_ids"].append(scenario_id)
                    scenario = to_input(case, scenario_id, family_id, wording)
                    truth = EvaluationTruth(scenario_id, family_id, split, "id" if split in ID_SPLITS else split,
                                            ("x", "v"), ("m", "m/s"), ("fixed_1d_origin",) * 2,
                                            result.times, result.states, result.states[-1])
                    inputs.append(asdict(scenario))
                    truths.append(asdict(truth))
                    predictions.append({"scenario_id": scenario_id, "observable_ids": ["x", "v"],
                                        "observable_names": ["position", "forward_speed"], "units": ["m", "m/s"],
                                        "frames": ["fixed_1d_origin"] * 2, "time": query_time,
                                        "values": list(truth.terminal), "times": list(truth.times),
                                        "trajectory": [list(row) for row in truth.trajectory]})
    typed_inputs = {x["scenario_id"]: ScenarioInput.from_dict(x) for x in inputs}
    typed_truths = tuple(convert(EvaluationTruth, t) for t in truths)
    scaler = fit_scaler(tuple(TrainingExample(typed_inputs[t.scenario_id], t) for t in typed_truths if t.split == "train"))
    # Deliberately impossible, one missing, one metadata-invalid. No altered oracle truth.
    corrupted = [dict(p) for p in predictions[1:]]
    if corrupted:
        first = typed_inputs[corrupted[0]["scenario_id"]]
        x0 = next(f.value for f in first.initial_facts if f.quantity_id == "x0")
        corrupted[0] = dict(corrupted[0], values=[x0 - 1.0, -1.0], times=None, trajectory=None)
    if len(corrupted) > 1:
        corrupted[1] = dict(corrupted[1], units=["cm", "m/s"])
    return {"config.json": asdict(config), "inputs.json": inputs, "truths.json": truths,
            "families.json": families, "partitions.json": partitions, "scaler.json": asdict(scaler),
            "source_registry.json": source_registry(),
            "oracle_predictions.json": {"producer": "oracle_fixture", "predictions": predictions},
            "corrupted_predictions.json": {"producer": "corrupted_oracle_fixture", "predictions": corrupted},
            "generation.json": {"fixture_only": True, "sealed_study": False, "analytic_solves": solves,
                                "model_calls": 0, "retries": 0, "numerical_solves": 0,
                                "annotation_status": "not_generated; no solution labels in inputs"}}


def generate_run(config: DatasetConfig, output: Path) -> Path:
    payloads = generate(config)
    return write_run(output, payloads, {"phase": "P01", "fixture_only": True, "generator": "passive_stopping_v1",
                                       "config_sha256": digest(asdict(config)), "seed": config.seed,
                                       "partition_sha256": digest(payloads["partitions.json"]),
                                       "code": code_provenance(), "environment": environment(),
                                       "usage": payloads["generation.json"]})


def training_scaler(inputs: dict[str, ScenarioInput], truths: tuple[EvaluationTruth, ...]):
    return fit_scaler(tuple(TrainingExample(inputs[t.scenario_id], t) for t in truths if t.split == "train"))


def validate_dataset(payloads: dict) -> dict:
    """Structural leakage audits plus independent numerical refinement of every unique query."""
    config = convert(DatasetConfig, payloads["config.json"])
    inputs_list = [ScenarioInput.from_dict(x) for x in payloads["inputs.json"]]
    truths = tuple(convert(EvaluationTruth, t) for t in payloads["truths.json"])
    inputs = {s.scenario_id: s for s in inputs_list}
    truth_map = {t.scenario_id: t for t in truths}
    if len(inputs) != len(inputs_list) or len(truth_map) != len(truths) or inputs.keys() != truth_map.keys():
        raise ValueError("duplicate or unmatched input/truth identity")
    families = payloads["families.json"]
    family_ids = [f["family_id"] for f in families]
    if len(set(family_ids)) != len(family_ids):
        raise ValueError("duplicate base family")
    partitions = payloads["partitions.json"]
    expected = {split: [f["family_id"] for f in families if f["split"] == split] for split in vars(config.counts)}
    if partitions != expected or any(len(partitions[s]) != count for s, count in vars(config.counts).items()):
        raise ValueError("partition allocation mismatch")
    seen_ids, seen_physics = set(), set()
    maximum_coarse, maximum_fine = [0.0, 0.0], [0.0, 0.0]
    numerical_steps = 0
    comparison_count = 0
    fine_bound_max = 0.0
    training_v, training_mu = set(), set()
    combination_cases = []
    stopped, moving = 0, 0
    for family in families:
        split = family["split"]
        base = convert(StoppingCase, family["case"])
        physics_hash = digest(family["case"])
        if physics_hash in seen_physics:
            raise ValueError("duplicate base physics across families")
        seen_physics.add(physics_hash)
        if not (config.position.low <= base.x0 <= config.position.high and config.speed.low <= base.v0 <= config.speed.high
                and config.horizon.low <= base.horizon <= config.horizon.high and base.gravity == config.gravity):
            raise ValueError("family outside configured ranges")
        if split in ID_SPLITS and (base.events or is_combination(base.v0, base.mu, config)):
            raise ValueError("reserved joint region/event leaked into ID")
        allowed_mu = config.low_friction if split == "parameter_low" else config.high_friction if split == "parameter_high" else config.friction
        if not allowed_mu.low <= base.mu <= allowed_mu.high:
            raise ValueError("friction does not belong to declared stratum")
        if split == "combination":
            if not is_combination(base.v0, base.mu, config) or base.events:
                raise ValueError("invalid combination OOD")
            combination_cases.append(base)
        if split == "event" and (not base.events or all(e.mu == base.mu for e in base.events)):
            raise ValueError("event OOD lacks a genuine stated change")
        if split != "event" and base.events:
            raise ValueError("events outside event stratum")
        if split == "train":
            training_v.add(base.v0)
            training_mu.add(base.mu)
        expected_variants = len(config.time_fractions) * config.paraphrases
        if len(family["scenario_ids"]) != expected_variants:
            raise ValueError("family variant count mismatch")
        offset = 0
        for fraction in config.time_fractions:
            query_time = config.horizon.low + fraction * (base.horizon - config.horizon.low)
            case = StoppingCase(base.x0, base.v0, base.mu, base.gravity, query_time, base.events)
            grid = sample_grid(case, config.sample_intervals)
            exact = analytic(case, grid)
            coarse, fine = numerical(case, grid, 0.02), numerical(case, grid, 0.01)
            numerical_steps += coarse.steps + fine.steps
            comparison_count += 1
            errors = [[max(abs(row[i] - ref[i]) for row, ref in zip(result.states, exact.states)) for i in (0, 1)] for result in (coarse, fine)]
            # Conservative forward-Euler bound in meters; speed is exact apart from roundoff.
            bound = case.gravity * max([case.mu, *(e.mu for e in case.events)]) * case.horizon * 0.01 + 1e-8
            fine_bound_max = max(fine_bound_max, bound)
            if errors[1][0] > bound or errors[1][1] > 1e-8 or errors[1][0] > errors[0][0] + 1e-8:
                raise ValueError("independent numerical agreement/refinement failed")
            for i in (0, 1):
                maximum_coarse[i] = max(maximum_coarse[i], errors[0][i])
                maximum_fine[i] = max(maximum_fine[i], errors[1][i])
            for wording in range(config.paraphrases):
                scenario_id = family["scenario_ids"][offset]
                offset += 1
                if scenario_id in seen_ids or scenario_id not in inputs:
                    raise ValueError("variant identity crosses families or is missing")
                seen_ids.add(scenario_id)
                scenario, truth = inputs[scenario_id], truth_map[scenario_id]
                if scenario != to_input(case, scenario_id, family["family_id"], wording):
                    raise ValueError("input differs from complete label-free scenario template")
                if truth.family_id != family["family_id"] or truth.split != split or truth.times != grid or truth.observable_ids != ("x", "v") or truth.units != ("m", "m/s") or truth.frames != ("fixed_1d_origin",) * 2:
                    raise ValueError("truth identity/layout/time mismatch")
                if any(abs(a - b) > 1e-10 for row, ref in zip(truth.trajectory, exact.states) for a, b in zip(row, ref)):
                    raise ValueError("truth disagrees with analytic oracle")
                stopped += truth.terminal[1] == 0
                moving += truth.terminal[1] > 0
    if seen_ids != set(inputs):
        raise ValueError("unassigned scenarios")
    if any(case.v0 not in training_v or case.mu not in training_mu for case in combination_cases):
        raise ValueError("combination OOD lacks exact individual marginal support in training")
    scaler = training_scaler(inputs, truths)
    if digest(asdict(scaler)) != digest(payloads["scaler.json"]):
        raise ValueError("persisted scaler differs from training-only fit")
    return {"status": "validated_fixture_only", "families": len(families), "samples": len(inputs),
            "partition_families": {s: len(v) for s, v in partitions.items()}, "moving_samples": moving, "stopped_samples": stopped,
            "combination_exact_marginal_support": True, "duplicate_base_families": 0,
            "near_duplicate_policy": "correlated time/text variants explicitly grouped; exact base-parameter duplicates rejected",
            "coarse_step_seconds": 0.02, "fine_step_seconds": 0.01,
            "max_coarse_errors_x_v": maximum_coarse, "max_fine_errors_x_v": maximum_fine,
            "fine_position_bound_policy": "g*max_mu*T*0.01 + 1e-8 m per case", "largest_position_bound_m": fine_bound_max,
            "speed_tolerance_m_per_s": 1e-8, "analytic_solves": comparison_count,
            "numerical_solves": comparison_count * 2, "numerical_steps": numerical_steps, "model_calls": 0,
            "scaler_sha256": digest(asdict(scaler))}


def validate_run(dataset: Path, output: Path) -> Path:
    payloads, manifest = read_run(dataset)
    report = validate_dataset(payloads)
    return write_run(output, {"validation.json": report}, {"phase": "P01", "dataset_manifest_sha256": dataset.name,
                     "generator_code": manifest["provenance"]["code"], "code": code_provenance(), "environment": environment(),
                     "usage": {k: report[k] for k in ("analytic_solves", "numerical_solves", "numerical_steps", "model_calls")}})
