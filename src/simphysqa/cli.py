"""Bounded offline commands; generation and formal release remain separate work."""
from __future__ import annotations
import argparse
from hashlib import sha256
from pathlib import Path
from jsonschema.exceptions import ValidationError
from .audit import export_packets, import_ratings, preview
from .dataset import attach_annotation, iter_source, load, migrate, public_record, restore, validate
from .evaluation import export_requests
from .scoring import export_scores
from .io import DOMAINS, canonical, digest, external, manifest, output_root, read, write

def smoke(data_root: Path, output: Path, plan: Path) -> dict:
    # Read a single actual admitted record in each domain; no simulation/generation.
    records = []
    preservation = []
    for domain in DOMAINS:
        source, location = next(iter_source(data_root / domain / "validation"))
        record = migrate(source, location)
        assert restore(record) == source
        assert record["sample_id"] == source["sample_id"]
        assert record["private"]["reference"] == source["reference"]
        assert record["private"]["metadata"] == source["metadata"]
        assert not ({"reference", "metadata", "source", "private"} & public_record(record).keys())
        records.append(record)
        preservation.append({"domain": domain, "sample_id": record["sample_id"], "trajectory_id": record["trajectory_id"],
                             "reference_sha256": digest(source["reference"]), "source": record["source"],
                             "checks": ["source_schema_and_semantics", "lossless_roundtrip", "ids_provenance_reference_exact",
                                        "public_allowlist", "question_evidence_alignment"]})
    output = external(output)
    output.mkdir(parents=True, exist_ok=False)
    with (output / "records.jsonl").open("xb") as stream:
        for record in records:
            stream.write(canonical(record))
    write(output / "public.json", [public_record(r) for r in records])
    packets = export_packets(records, output / "audit-development")
    imports = {}
    for reviewer in ("R1", "R2", "R3"):
        result = import_ratings(packets, packets / "forms" / (reviewer + ".csv"), output / (reviewer + "-blank-import.json"))
        assert result["collected"] == 0 and result["blank"] == 4
        imports[reviewer] = {"collected": result["collected"], "blank": result["blank"]}
    export_requests(records, read(plan), output / "baseline-requests")
    summary = {"status": "pass", "domains": len(records), "real_existing_records": preservation,
               "audit_packets": 4, "blank_rating_imports": imports, "human_ratings_collected": 0,
               "model_calls": 0, "simulator_calls": 0, "formal_sample_exported": False,
               "formal_sampling_preview": preview(records, 20261004),
               "annotations": "missing_features_explicitly_pending", "benchmark_results": "pending"}
    write(output / "smoke-evidence.json", summary)
    manifest(output, {"purpose": "bootstrap_smoke", "status": "pass",
                      "base_commit": "7dd4a64e90cfb18be743503ac8345cabf2f6e28b"})
    return summary

def main(argv=None) -> int:
    parser = argparse.ArgumentParser(prog="simphysqa")
    sub = parser.add_subparsers(dest="command", required=True)
    test = sub.add_parser("smoke")
    test.add_argument("--data-root", required=True, type=Path)
    test.add_argument("--output", type=Path)
    test.add_argument("--plan", type=Path, default=Path("configs/simphysqa/evaluation.json"))
    for command in ("validate", "migrate", "audit-export", "sample-preview", "baseline-requests", "attach-annotation", "score"):
        cmd = sub.add_parser(command)
        cmd.add_argument("--input", required=True, type=Path)
        if command not in ("validate",):
            cmd.add_argument("--output", type=Path)
        if command == "sample-preview":
            cmd.add_argument("--seed", type=int, default=20261004)
            cmd.add_argument("--exclude-group", action="append", default=[])
        if command == "audit-export":
            cmd.add_argument("--phase", choices=("development", "calibration"), default="development")
        if command in ("baseline-requests", "score"):
            cmd.add_argument("--plan", type=Path, default=Path("configs/simphysqa/evaluation.json"))
        if command == "score":
            cmd.add_argument("--predictions", required=True, type=Path)
            cmd.add_argument("--condition", required=True, action="append")
        if command == "attach-annotation":
            cmd.add_argument("--result", required=True, type=Path)
    imp = sub.add_parser("import-ratings")
    imp.add_argument("--packets", required=True, type=Path)
    imp.add_argument("--form", required=True, type=Path)
    imp.add_argument("--output", required=True, type=Path)
    args = parser.parse_args(argv)
    try:
        if args.command == "smoke":
            result = smoke(args.data_root, output_root(args.output), args.plan)
        elif args.command == "import-ratings":
            result = import_ratings(args.packets, args.form, args.output)
            result = {k: result[k] for k in ("collected", "blank", "kind")}
        else:
            records = list(load(args.input))
            if args.command == "validate":
                result = {"validated": len(records)}
            elif args.command == "migrate":
                output = output_root(args.output)
                output.mkdir(parents=True, exist_ok=False)
                with (output / "records.jsonl").open("xb") as stream:
                    for record in records:
                        stream.write(canonical(record))
                result = manifest(output, {"purpose": "lossless_migration", "records": len(records),
                                           "source_records": {r["sample_id"]: r["source"] for r in records}})
            elif args.command == "audit-export":
                result = {"packets": str(export_packets(records, output_root(args.output), args.phase))}
            elif args.command == "sample-preview":
                result = preview(records, args.seed, excluded_groups=tuple(args.exclude_group))
                write(output_root(args.output) / "preview.json", result)
            elif args.command == "baseline-requests":
                result = export_requests(records, read(args.plan), output_root(args.output))
            elif args.command == "score":
                result = export_scores(records, read(args.predictions), read(args.plan), args.condition, output_root(args.output))
            elif args.command == "attach-annotation":
                if len(records) != 1:
                    raise ValueError("annotation import requires exactly one record")
                result_record = attach_annotation(records[0], read(args.result))
                write(output_root(args.output) / "record.json", result_record)
                result = {"sample_id": result_record["sample_id"], "annotation_version": result_record["annotation_version"]}
        print(canonical(result).decode(), end="")
        return 0
    except (ValueError, OSError, StopIteration, KeyError, ValidationError) as exc:
        print(canonical({"status": "failed", "error": type(exc).__name__ + ": " + str(exc)}).decode(), end="")
        return 1
