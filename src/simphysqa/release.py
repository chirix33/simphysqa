"""Lightweight inventory and representative engineering selection from actual shards."""
from collections import Counter, defaultdict
from pathlib import Path
import random
from .dataset import SourceLocation, migrate
from .io import ROOT, DOMAINS, canonical, digest, external, manifest, parse, read, write
from hashlib import sha256

def numeric_features(value, prefix=""):
    if isinstance(value, dict):
        for key, item in sorted(value.items()):
            yield from numeric_features(item, prefix + "/" + key)
    elif isinstance(value, list):
        for index, item in enumerate(value):
            yield from numeric_features(item, prefix + "/" + str(index))
    elif type(value) in (int, float, bool):
        yield prefix, float(value)

def inventory(data_root: Path, output: Path):
    output = external(output)
    output.mkdir(parents=True, exist_ok=False)
    counts, groups, files = Counter(), set(), {}
    seen = set()
    with (output / "records.jsonl").open("xb") as sink:
        for domain in DOMAINS:
            for partition in sorted((data_root / domain).iterdir()):
                if not partition.is_dir() or not (partition / "shards").is_dir():
                    continue
                for file in sorted((partition / "shards").glob("*.jsonl")):
                    file_hash = sha256(file.read_bytes()).hexdigest()
                    files[str(file.resolve())] = file_hash
                    with file.open(encoding="utf-8") as stream:
                        for line_no, line in enumerate(stream, 1):
                            if not line.strip():
                                continue
                            record = parse(line)
                            inp, meta, ref = record["input"], record["metadata"], record["reference"]
                            if record["sample_id"] in seen:
                                raise ValueError("duplicate release identity")
                            seen.add(record["sample_id"])
                            if meta["validation"]["status"] != "accepted":
                                raise ValueError("non-admitted record in release shards")
                            group = meta["split_group_id"]
                            groups.add(group)
                            observed = {"initial": inp["states"][0]["measurements"],
                                        "cutoff_measurements": inp["states"][-1]["measurements"],
                                        "properties": [e["properties"] for e in inp["entities"]],
                                        "control_parameters": inp["controller"]["parameters"],
                                        "events": [{"start_time":e["start_time"],"end_time":e["end_time"]} for e in inp["known_events"]],
                                        "observed_count": len(inp["states"]), "cutoff": inp["observation_cutoff"]}
                            # All selection features derive from public inputs, not realized outcomes.
                            row = {"sample_id": record["sample_id"], "domain": domain, "partition": partition.name,
                                "split": meta["split"], "trajectory_id": meta["base_scenario_id"], "group_id": group,
                                "question_type": "predictive" if inp["task_type"] == "future_state_prediction" else "unsupported",
                                "annotation_status": "legacy_generic_context_only_meaningful_language_pending" if all(s.get("context") == "Measured simulator state at the stated timestamp." for s in inp["states"]) else "legacy_context_present_meaningfulness_unassessed",
                                "observation_count": len(inp["states"]), "observation_cutoff": inp["observation_cutoff"],
                                "target_time": min(t["end_time"] for t in inp["answer_spec"]),
                                "source": {"path": str(file.resolve()), "line": line_no, "file_sha256": file_hash,
                                           "record_sha256": digest(record)},
                                "reference_sha256": digest(ref), "public_input_sha256": digest(inp),
                                "source_schema_version": record["schema_version"],
                                "generator_commit": meta["simulation"]["generator_commit"],
                                "simulation_config_sha256": meta["simulation"]["config_sha256"],
                                "public_selection_features": dict(numeric_features(observed))}
                            sink.write(canonical(row))
                            counts[(domain, partition.name, meta["split"], row["question_type"], row["annotation_status"])] += 1
    result = {"version": "simphysqa-release-inventory/0.1.1", "data_root":str(data_root.resolve()),
              "records": len(seen), "groups":len(groups), "source_files":len(files),
              "counts":[{"domain":k[0],"partition":k[1],"split":k[2],"question_type":k[3],
                         "annotation_status":k[4],"records":v} for k,v in sorted(counts.items())],
              "release_manifest_sha256": sha256((data_root/"release-manifest.json").read_bytes()).hexdigest(),
              "source_file_inventory_sha256":digest(files), "schema_sha256":sha256((ROOT/"dataset.schema.json").read_bytes()).hexdigest(),
              "meaningful_language": "pending_in_source_release_not_counted_as_completed",
              "population": "actual admitted release QA records; not the SPQ00 four-record smoke frame"}
    write(output/"summary.json",result)
    write(output/"source-files.json",files)
    manifest(output, {"purpose":"actual_release_inventory","summary":result})
    return result

def inventory_rows(path):
    with path.open(encoding="utf-8") as stream:
        return [parse(line) for line in stream if line.strip()]

def select(inventory_root: Path, output: Path, excluded: list[str], seed=20261004):
    rows = inventory_rows(inventory_root/"records.jsonl")
    rng = random.Random(seed)
    chosen = []
    variation = {}
    for domain in DOMAINS:
        by_group = defaultdict(list)
        for row in rows:
            if row["domain"] == domain and row["split"] == "train" and row["group_id"] not in excluded and row["trajectory_id"] not in excluded:
                by_group[row["group_id"]].append(row)
        # Earliest original predictive horizon per group; never use private outcomes for selection.
        candidates = sorted((min(values,key=lambda r:(r["target_time"],r["sample_id"])) for values in by_group.values()),
                            key=lambda r:r["group_id"])
        if len(candidates)<4:
            raise ValueError("insufficient admitted train development groups")
        keys = sorted(set.intersection(*(set(r["public_selection_features"]) for r in candidates)))
        ranges = {k:(min(r["public_selection_features"][k] for r in candidates),
                    max(r["public_selection_features"][k] for r in candidates)) for k in keys}
        ranges = {k:v for k,v in ranges.items() if v[1]>v[0]}
        def distance(a,b):
            return sum(((a["public_selection_features"][k]-b["public_selection_features"][k])/(hi-lo))**2
                       for k,(lo,hi) in ranges.items())/max(1,len(ranges))
        order = list(candidates)
        rng.shuffle(order)
        selected = [order.pop(0)]
        while len(selected)<4:
            best=max(range(len(order)),key=lambda i:min(distance(order[i],s) for s in selected))
            selected.append(order.pop(best))
        chosen.extend(selected)
        variation[domain] = {"available_train_groups":len(candidates),
                            "nonconstant_public_features":ranges,
                            "observation_counts":sorted({r["observation_count"] for r in selected}),
                            "observation_cutoffs":sorted({r["observation_cutoff"] for r in selected}),
                            "selected_feature_values":{r["group_id"]:r["public_selection_features"] for r in selected}}
    output=external(output)
    output.mkdir(parents=True,exist_ok=False)
    records=[]
    for row in chosen:
        source_path=Path(row["source"]["path"])
        if sha256(source_path.read_bytes()).hexdigest()!=row["source"]["file_sha256"]:
            raise ValueError("source changed after inventory")
        with source_path.open(encoding="utf-8") as stream:
            source=next(parse(line) for n,line in enumerate(stream,1) if n==row["source"]["line"])
        if digest(source)!=row["source"]["record_sha256"]:
            raise ValueError("source record hash mismatch")
        records.append(migrate(source, SourceLocation(row["source"]["path"],row["source"]["line"],row["source"]["file_sha256"])))
    with (output/"predictive-records.jsonl").open("xb") as stream:
        for record in records:
            stream.write(canonical(record))
    result={"version":"simphysqa-development-selection/0.1.0","seed":seed,"selected_trajectories":16,
        "per_domain":4,"split":"train","purpose":"engineering_development_not_unbiased_quality_estimation",
        "rule":"one earliest-horizon predictive question per physical group; seeded initial group, then normalized public-feature farthest-point diversity",
        "frame_inventory_sha256":sha256((inventory_root/"records.jsonl").read_bytes()).hexdigest(),
        "prior_excluded_groups":sorted(set(excluded)),"future_formal_excluded_groups":sorted(set(excluded)|{r["group_id"] for r in chosen}),
        "selected":chosen,"variation":variation,"formal_sample_exported":False,
        "observation_length_limitation":"preserve observed availability; no artificial observation length variation"}
    write(output/"selection.json",result)
    manifest(output,{"purpose":"SPQ01_engineering_development_selection","selection_sha256":digest(result)})
    return result
