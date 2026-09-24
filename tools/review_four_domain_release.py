"""Read-only audit of existing pilots; does not run engines or enable release."""
import ast
from collections import Counter
from hashlib import sha256
import json
from phi_jepa.simulation.common import ROOT, read, write, public_record
from phi_jepa.simulation.pipeline import records_at, validate_dataset
from phi_jepa.simulation.numeric import Registry, text_pair
from phi_jepa.simulation.scope import RELEASE_ENGINES, check_release_scope, check_release_partition


def function(text, name):
    node = next(n for n in ast.parse(text).body if isinstance(n, (ast.FunctionDef, ast.ClassDef)) and n.name == name)
    if name == "comparison" and isinstance(node.body[0], ast.If):
        # The added quadruped-only experiment identity precondition is inapplicable.
        if "quadruped_locomotion" in ast.unparse(node.body[0].test):
            node.body.pop(0)
    return ast.dump(node, include_attributes=False)


def main():
    config = read(ROOT / "configs/dataset_release_four_domain.json")
    check_release_scope(config)
    summaries = []
    for domain in RELEASE_ENGINES:
        registry = Registry.from_manifest(read(ROOT / config["numeric_registries"][domain]))
        for mode in ("smoke", "calibrate"):
            folder = "corrected-" + mode if domain == "tethered_load" else mode
            path = ROOT / "dataset-runs/final" / domain / folder
            validation = validate_dataset(path)
            records = list(records_at(path))
            for record in records:
                assert record["input"]["domain"] == domain
                assert record["metadata"]["split"] == "development"
                pair = text_pair(public_record(record), record["reference"]["label"], registry)
                assert pair["n_initial"] == pair["n_target"]
            old = read(path / "config.json")
            assert old["domains"][domain] == config["domains"][domain]
            assert old["counts"] == config["counts"]
            assert old["master_seed"] == config["master_seed"]
            assert old["model_data_contract"] == config["model_data_contract"]
            assert old["sampling"] == read(ROOT / "configs/dataset_sampling.json")
            assert old["time"] == {**config["time"], "default_timestep_s": config["integration_timesteps_s"][domain]}
            source_checks = {}
            for name in ("common.py", "engines.py", "bullet.py", "records.py", "sampling.py", "validation.py", "numeric.py", "extracted.py"):
                prior = path / "source_snapshot/simulation" / name
                current = ROOT / "src/phi_jepa/simulation" / name
                # Newline conversion is not a physics change; retain raw hashes too.
                current_text = current.read_text()
                if name == "records.py" and "asset_license" not in old and 'config.get("asset_license"' not in prior.read_text():
                    current_text = current_text.replace('config.get("asset_license","Authored in this repository; redistribution license not yet granted")', '"Authored in this repository; redistribution license not yet granted"')
                if name == "validation.py" and "readable answer differs" not in prior.read_text():
                    current_text = current_text.replace('    from .records import answer_text\n    ordered_labels=[next(l for l in labels if l["target_id"]==t["target_id"]) for t in targets]\n    if ref["label"]!=answer_text(targets,ordered_labels): raise ValueError("readable answer differs from verified structured labels")\n', '')
                same = prior.read_text() == current_text
                assert same, (domain, mode, name)
                source_checks[name] = dict(compatible_after_documented_checks=same, prior_sha256=sha256(prior.read_bytes()).hexdigest(), current_sha256=sha256(current.read_bytes()).hexdigest())
            scene_names = ("tether_model", "support_motion") if domain == "tethered_load" else ("arm_model", "box_inertia")
            for filename, names in (("scenes.py", scene_names), ("pipeline.py", ("comparison",))):
                prior = (path / "source_snapshot/simulation" / filename).read_text()
                current = (ROOT / "src/phi_jepa/simulation" / filename).read_text()
                for name in names:
                    assert function(prior, name) == function(current, name), (domain, mode, name)
                    source_checks[filename + ":" + name] = dict(unchanged_applicable_ast=True, ast_sha256=sha256(function(current, name).encode()).hexdigest())
            shifts = {}
            manifest = read(path / "manifest.json")
            for scenario in read(path / "partitions.json"):
                row = shifts.setdefault(scenario["shift"], dict(attempted=0, admitted=0, rejected=0, reasons=Counter()))
                row["attempted"] += 1
                receipt = read(path / "receipts" / (scenario["group"] + ".json"))
                if receipt["status"] == "accepted":
                    row["admitted"] += 1
                else:
                    row["rejected"] += 1
                    quarantine = path / "quarantine" / (scenario["group"] + ".jsonl")
                    if quarantine.exists():
                        rejected = next(records_at(quarantine))
                        for check in rejected["metadata"]["validation"]["checks"]:
                            if check["status"] != "pass":
                                row["reasons"][check["name"]] += 1
                        diagnostics = read(path / "diagnostics" / (scenario["group"] + ".json"))
                        if not diagnostics["agreement"]["event_agreement"]:
                            row["reasons"]["event_or_discrete_disagreement"] += 1
                    else:
                        row["reasons"][receipt["reason"]] += 1
            for row in shifts.values():
                row["rejection_fraction"] = row["rejected"] / row["attempted"]
            ood = [v for k, v in shifts.items() if k != "id"]
            ood_rate = sum(v["rejected"] for v in ood) / sum(v["attempted"] for v in ood)
            summaries.append(dict(domain=domain, mode=mode, path=path.relative_to(ROOT).as_posix(),
                                  manifest_sha256=sha256((path / "manifest.json").read_bytes()).hexdigest(),
                                  counts=manifest["counts"], validation=validation, shifts=shifts,
                                  id_rejection_fraction=shifts["id"]["rejection_fraction"], ood_rejection_fraction=ood_rate,
                                  ood_filtered_more=ood_rate > shifts["id"]["rejection_fraction"],
                                  config_compatible=True, source_checks=source_checks,
                                  original_identity=read(path / "identity.json")))
    quad = ROOT / "dataset-runs/quadruped-qualified-pilots/smoke"
    quad_records = list(records_at(quad))
    assert len(quad_records) == 9
    for split in ("train", "validation", "test_id", "test_ood"):
        try:
            check_release_partition(read(quad / "manifest.json"), quad_records, "quadruped_locomotion", split)
        except ValueError:
            pass
        else:
            raise AssertionError("historical quadruped admission escaped exclusion")
    dest = ROOT / "docs/reviews/artifacts/PDS_four_domain"
    write(dest / "readiness.json", dict(status="development_evidence_reused_release_pending", runs=summaries,
        quadruped_exclusion=dict(historical_groups=5, historical_records=9, release_splits_rejected=4),
        planned_base_scenarios=6800, production_generated=0, production_admitted=0,
                                  source_reuse_note="Whole source/config hashes changed. Applicable physics, sampler, registry and comparison logic match. Record license lookup has the same default without a configured license. The added readable-answer validator was rerun on every admitted record. Pipeline changes isolate quadruped and add release guards; no old run identity was rewritten."))
    print(json.dumps([{k: r[k] for k in ("domain", "mode", "counts", "shifts")} for r in summaries], indent=2))


if __name__ == "__main__":
    main()
