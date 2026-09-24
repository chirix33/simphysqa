"""Prepare licensing inventory and a disabled freeze; never run a simulator."""
import argparse
import copy
from dataclasses import asdict
from hashlib import sha256
import importlib.metadata as metadata
from pathlib import Path
import shutil
import subprocess
from phi_jepa.artifacts import code_provenance, digest
from phi_jepa.simulation.common import ROOT, read, write
from phi_jepa.simulation.freeze import contract, verify_freeze
from phi_jepa.simulation.sampling import sample
from phi_jepa.simulation.scope import RELEASE_ENGINES

DEST = ROOT / "docs/reviews/artifacts/PDS_release_preparation"


def model_text(domain, parameters, subfamily, dt):
    """Render authored descriptions only; no engine initialization or stepping."""
    import json
    from phi_jepa.simulation.scenes import arm_model, tether_model, box_inertia
    from phi_jepa.simulation.bullet import car_asset
    if domain == "robotic_arm":
        return arm_model(parameters["payload_kg"], dt)
    if domain == "driving":
        return car_asset(parameters["mass_multiplier"])
    if domain == "tethered_load":
        return tether_model(parameters["cable_length_m"], parameters["load_mass_kg"], dt)
    mass = parameters["block_mass_kg"]
    positions = [[-.15, 0, .05], [.05, 0, .05]] if subfamily == "pushing" else [[0, 0, .05], [0, 0, .15]]
    return json.dumps(dict(model="phi_two_blocks_v1", block_size=[.1]*3, mass_each=mass,
        inertia=box_inertia(mass, [.1]*3), positions=positions, table_half_extents=[2, 2, .05],
        table_center=[0, 0, -.05], friction=parameters["contact_friction_coefficient"], table_friction=1,
        restitution=0, linear_damping=0, angular_damping=0, solver_iterations=100), sort_keys=True)


def hashed(path):
    return sha256(path.read_bytes()).hexdigest()


def inventory():
    entries = []; measurements = []; families = []
    descriptions = {
        "robotic_arm": ("src/phi_jepa/simulation/scenes.py:arm_model", "MJCF: two box links, hinge joints, finite spherical payload, tip site; authored inertias and control law"),
        "driving": ("src/phi_jepa/simulation/bullet.py:car_asset,link,joint,BulletAdapter._run", "URDF box chassis, four cylinder wheels and axles; procedural infinite plane at z=0; braking/contact law"),
        "object_pushing_stacking": ("src/phi_jepa/simulation/bullet.py:BulletAdapter._run; scenes.py:box_inertia", "JSON model: two primitive box bodies and static box table, pushing and pre-stacked placements, inertias and push schedule"),
        "tethered_load": ("src/phi_jepa/simulation/scenes.py:tether_model,support_motion", "MJCF: prescribed support, slider/pivot, pendulum joint, spherical payload, site and fixed-length taut constraint; no external cable mesh"),
    }
    for domain in RELEASE_ENGINES:
        source, description = descriptions[domain]
        families.append(dict(domain=domain, origin="project_authored_procedural", source=source,
            description=description, ownership="unconfirmed; Git provenance is not an ownership grant",
            existing_project_license="none found", proposed_license="CC-BY-4.0", grant_status="not_granted",
            redistribution="intended: model files and descriptions embedded in public records; not published yet"))
        for mode in ("smoke", "calibrate"):
            folder = "corrected-" + mode if domain == "tethered_load" else mode
            run = ROOT / "dataset-runs/final" / domain / folder
            manifest = read(run / "manifest.json")
            dt = read(run / "config.json")["time"]["default_timestep_s"]
            expected_assets = {sha256(model_text(domain, s["parameters"], s["subfamily"], dt).encode()).hexdigest()
                               for s in read(run / "partitions.json")}
            assert expected_assets == {p.stem for p in (run / "assets").iterdir()}, (domain, mode)
            for asset in sorted((run / "assets").iterdir()):
                actual = hashed(asset)
                assert actual == asset.stem
                assert actual == manifest["files"][asset.relative_to(run).as_posix()]
                entries.append(dict(domain=domain, path=asset.relative_to(ROOT).as_posix(), sha256=actual,
                                    bytes=asset.stat().st_size, origin="project_authored_procedural"))
            if mode == "calibrate":
                measurements.append(dict(domain=domain, path=run.relative_to(ROOT).as_posix(),
                    manifest_sha256=hashed(run / "manifest.json"), attempted=manifest["counts"]["attempted"],
                    admitted=manifest["counts"]["accepted"], wall_seconds=manifest["wall_seconds"],
                    disk_bytes=manifest["disk_bytes"], peak_rss_bytes=manifest["peak_rss_bytes"],
                    projected_seconds_1700_attempts=manifest["wall_seconds"] * 17,
                    projected_bytes_1700_attempts=manifest["disk_bytes"] * 17))
    write(DEST / "asset-inventory.json", dict(families=families, historical_asset_instances=entries,
        third_party_scene_assets=[], scope="four domains, corrected tether only",
        provenance_commit="4b997efd1dcbc8199c5981e44c71bd39fa8b7cb9",
        future_assets="Parameterized instances generated from frozen code and preassigned draws; hashes recorded per run, no future assets or data claimed generated."))
    notices = []
    for name in ("mujoco", "pybullet", "numpy", "jsonschema", "psutil"):
        dist = metadata.distribution(name)
        files = []
        for item in dist.files:
            if ("license" in str(item).lower() or "copying" in str(item).lower()) and ".dist-info/" in str(item):
                path = Path(dist.locate_file(item))
                files.append(dict(installed_path=str(item), sha256=hashed(path)))
                if name in ("mujoco", "pybullet"):
                    target = ROOT / "licenses/third-party" / (name + "-" + path.name)
                    target.parent.mkdir(parents=True, exist_ok=True); shutil.copyfile(path, target)
        notices.append(dict(package=name, version=dist.version, installed_license_metadata=dist.metadata.get("License"),
                            notices=files, bundled_in_public_dataset=False, role="runtime_dependency_not_scene_asset"))
    write(ROOT / "licenses/runtime-notices.json", notices)
    code = sorted(p.relative_to(ROOT).as_posix() for p in (ROOT / "src/phi_jepa/simulation").glob("*.py")
                  if p.name not in ("mjx.py", "quadruped.py"))
    code += ["src/phi_jepa/__init__.py", "src/phi_jepa/artifacts.py", "src/phi_jepa/validation.py", "pyproject.toml"]
    code += ["tools/" + name for name in ("prepare_dataset_release.py", "review_four_domain_release.py", "check_four_domain_solvers.py", "run_dataset_pilots.py", "collect_dataset_evidence.py")]
    code += ["tests/" + name for name in ("test_simulation.py", "test_simulation_bullet.py", "test_release_scope.py", "test_release_freeze.py")]
    write(ROOT / "licenses/scope.json", dict(status="prepared_not_granted", mit_files=sorted(code),
        cc_by_files=["dataset.schema.json", "configs/dataset_sampling.json", "configs/dataset_release_four_domain.json", "configs/dataset_release_freeze.json"] +
            [f"configs/dataset_registries/{d}{suffix}.json" for d in RELEASE_ENGINES for suffix in ("", ".extracted")] +
            [f"configs/frozen_dataset_domains/{d}.json" for d in RELEASE_ENGINES],
        cc_by_generated_files=["four-domain release inputs, references, labels, evaluator metadata, target texts, manifests, accepted shards and explicitly quarantined records", "authored assets/*.xml, assets/*.urdf, assets/*.json and embedded model descriptions"],
        cc_by_generated_globs=["dataset-runs/release-four-domain-v1/**/inputs.jsonl", "dataset-runs/release-four-domain-v1/**/references.jsonl", "dataset-runs/release-four-domain-v1/**/evaluator.jsonl", "dataset-runs/release-four-domain-v1/**/target-texts.jsonl", "dataset-runs/release-four-domain-v1/**/shards/*.jsonl", "dataset-runs/release-four-domain-v1/**/quarantine/*.jsonl", "dataset-runs/release-four-domain-v1/**/assets/*", "dataset-runs/release-four-domain-v1/**/*.json", "dataset-runs/release-four-domain-v1/**/rejections.jsonl"],
        embedded_scene_templates="The authored scene/model definitions embedded in MIT-covered generator files are also offered separately under CC BY 4.0 for asset reuse once authorized.",
        exclusions=["third-party packages/binaries/data", "docs/assets adopted prompts/schemas", "docs/references/sources", "historical quadruped/MJX artifacts", "unlisted legacy and model-training code", "all source_snapshot/** files except separately MIT-listed paths; source is not CC-BY dataset content"],
        distribution_note="Scope applies to the named four-domain bundle; no blanket repository relicensing."))
    write(DEST / "cost-estimate.json", dict(measurements=measurements,
        projected_serial_seconds=sum(m["projected_seconds_1700_attempts"] for m in measurements),
        projected_bytes=sum(m["projected_bytes_1700_attempts"] for m in measurements),
        caveats=["Linear calibration extrapolation, not a measured production run", "Release has a different ID/OOD mix; validation, filesystem scanning and serialization may scale nonlinearly", "Counts include retained rejection artifacts; no admission-rate promise", "Cross-platform timings differ; recommended serial budget six hours with resumable two-hour partitions"] ))
    print("Inventoried", len(entries), "historical scene asset instances; no simulation")


def freeze():
    source = code_provenance()
    if subprocess.check_output(["git", "status", "--porcelain", "--", "src", "pyproject.toml"], cwd=ROOT, text=True):
        raise ValueError("commit generator source before freezing")
    covered = read(ROOT / "licenses/scope.json")["mit_files"]
    selected = {p.removeprefix("src/phi_jepa/") for p in covered if p.startswith("src/phi_jepa/") or p == "pyproject.toml"}
    source["source_files"] = {k: v for k, v in source["source_files"].items() if k in selected}
    source["source_sha256"] = digest(source["source_files"])
    source["scope"] = "MIT-prepared generation dependencies, not unrelated legacy/model code"
    config = read(ROOT / "configs/dataset_release_four_domain.json")
    config.pop("experiment_freeze", None)
    config.update(status="frozen", final_generation_enabled=False, sampling=read(ROOT / "configs/dataset_sampling.json"),
        licensing_decision="licenses/decision.json", proposed_asset_license="CC-BY-4.0", proposed_code_license="MIT",
        attempt_policy=dict(total_attempted_base_scenarios=6800, per_domain=1700, resample_to_fill_quotas=False,
                            failures="preserve attempted draws, quarantine failures, report admitted counts separately"))
    config["limits"].update(max_run_wall_seconds=7200, max_generation_wall_seconds=21600)
    plans = []
    for domain in RELEASE_ENGINES:
        old = read(ROOT / f"configs/dataset_domains/{domain}.json")
        old.update(status="validation_frozen_license_pending", asset_license_status="not_granted",
            unmet_release_gates=["rights-holder identity and authority for CC BY 4.0 assets and MIT generation code"],
            generator_source_revision=source["git_commit"], generator_source_sha256=source["source_sha256"],
            asset_inventory="docs/reviews/artifacts/PDS_release_preparation/asset-inventory.json",
            planned_attempts=1700, production_generated=0, production_admitted=0,
            proposed_asset_license="CC-BY-4.0", licensing_decision="licenses/decision.json",
            numerical_settings=dict(integration_timestep_s=config["integration_timesteps_s"][domain], refinement_factor=.5,
                numeric_gate="half of target absolute accuracy tolerance", velocity_tolerance=.01,
                other_continuous_tolerance=.005, discrete_tolerance=0, event_time_tolerance_s=.01,
                unchanged_physics_policy="driving min velocity >= -0.02; tether tension >0 and length residual <1e-6"))
        path = f"configs/frozen_dataset_domains/{domain}.json"; write(ROOT / path, old)
        config["validated_domain_manifests"][domain] = path
        effective = copy.deepcopy(config); effective["time"]["default_timestep_s"] = config["integration_timesteps_s"][domain]
        for partition, count in config["counts"]["proposed_release_per_domain"].items():
            shift = partition.removeprefix("ood_") if partition.startswith("ood_") else "id"
            split = "test_ood" if partition.startswith("ood_") else partition
            draws = [asdict(sample(effective, domain, i, "release", shift, split)) for i in range(count)]
            model_hashes = [dict(group=s["group"], hashes=[sha256(model_text(domain, s["parameters"], s["subfamily"], dt).encode()).hexdigest()
                             for dt in (effective["time"]["default_timestep_s"], effective["time"]["default_timestep_s"] / 2)]) for s in draws]
            plans.append(dict(domain=domain, partition=partition, split=split, shift=shift,
                              attempted_draw_budget=count, scenario_plan_sha256=digest(draws),
                              planned_model_pairs_sha256=digest(model_hashes)))
    assert sum(p["attempted_draw_budget"] for p in plans) == 6800
    write(DEST / "partition-plan.json", plans)
    files = [ROOT / p for p in config["validated_domain_manifests"].values()]
    files += [ROOT / p for p in config["numeric_registries"].values()]
    files += [ROOT / f"configs/dataset_registries/{d}.extracted.json" for d in RELEASE_ENGINES]
    files += list((ROOT / "licenses").rglob("*"))
    files += list(DEST.glob("*.json"))
    files += [ROOT / p for p in ("dataset.schema.json", "MODEL_DATA_CONTRACT.md", "configs/dataset_sampling.json", "configs/dataset-bullet-linux.lock.txt", "tools/prepare_dataset_release.py")]
    files += [ROOT / p for p in covered if p.startswith("tools/")]
    for folder in ("PDS_four_domain",):
        files += list((ROOT / "docs/reviews/artifacts" / folder).glob("*"))
    frozen = dict(version="1.0.0", source=source, generation_contract=contract(config),
        partition_plan_path="docs/reviews/artifacts/PDS_release_preparation/partition-plan.json",
        files={p.relative_to(ROOT).as_posix(): hashed(p) for p in files if p.is_file()},
        runtime_packages={n: metadata.version(n) for n in ("mujoco", "pybullet", "numpy", "jsonschema", "psutil")},
        reviewed_evidence_commit="22aacf8", review="docs/reviews/PDS_four_domain_completion.md",
        preparation_note="Settings frozen; ownership/authority pending. 6800 attempted draws, no resampling. No simulations performed by freeze.")
    path = ROOT / "configs/dataset_release_freeze.json"; write(path, frozen)
    config["experiment_freeze"] = dict(path=path.relative_to(ROOT).as_posix(), sha256=hashed(path))
    write(ROOT / "configs/dataset_release_four_domain.json", config)
    verify_freeze(config)
    print("Freeze verified; production remains disabled; source", source["git_commit"])


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("stage", choices=("inventory", "freeze"))
    args = parser.parse_args()
    (inventory if args.stage == "inventory" else freeze)()
