"""Blinded packets, disjoint sampling previews, append-only independent rating imports."""
from __future__ import annotations
from collections import Counter, defaultdict
import csv
from html import escape
from pathlib import Path
import random
from .dataset import validate
from .io import ROOT, canonical, digest, external, manifest, read, write

REVIEWERS = ("R1", "R2", "R3")
CRITERIA = ("physical_reference", "language_fidelity", "qa_validity", "evidence_sufficiency", "public_private_separation")
ERRORS = ("reference_error", "unit_frame_error", "language_error", "ambiguous_question", "unsupported_claim",
          "insufficient_evidence", "future_leakage", "missing_annotation", "other")
COLUMNS = ("packet_id", "sample_id", "reviewer_id", "phase", "judgment", "criteria", "error_categories", "notes")
RUBRIC = """SimPhysQA rubric draft 0.1 (development; not final)
Primary judgment: acceptable / material_error. Acceptable means the record is correct and sufficiently complete for its declared task.
A material error could alter an answer or interpretation, unsupported physical/causal claims, missing required language, ambiguity, or leaked outcomes.
Check physical_reference (values, Booleans, units, frames, controls, events, provenance); language_fidelity (trajectory and timestamp meaning);
qa_validity (family-specific question/reference, genuine clarification gap); evidence_sufficiency (target/claim-specific bindings);
public_private_separation (observed states and declared controls only in predictive public language).
Mark each criterion acceptable / material_error / not_applicable, and record relevant categories and evidence IDs.
Generic timestamp context is not a completed annotation. A descriptive readout explanation is not causal explanation QA.
Private reference states are for audit only. Do not infer causation from temporal association.
Rate independently; do not discuss formal items until originals are locked. Missing annotations remain findings.
Calibration feedback may revise the rubric before formal sampling; all three review the same 20 calibration records.
"""

def preview(records: list[dict], seed: int, calibration_n: int = 20, formal_n: int = 140,
            excluded_groups: tuple[str, ...] = ()) -> dict:
    if calibration_n < 0 or formal_n < 0:
        raise ValueError("negative sample size")
    groups = defaultdict(list)
    ids = set()
    for record in records:
        validate(record)
        if record["sample_id"] in ids:
            raise ValueError("duplicate sampling identity")
        ids.add(record["sample_id"])
        meta = record["private"]["metadata"]
        if record["trajectory_id"] not in excluded_groups and meta["split_group_id"] not in excluded_groups:
            groups[meta["split_group_id"]].append(record)
    rng = random.Random(seed)
    # One item per physical group, random choice within group. Both phases share one randomized frame.
    candidates = [rng.choice(sorted(group, key=lambda r: r["sample_id"])) for _, group in sorted(groups.items())]
    rng.shuffle(candidates)
    calibration = candidates[:calibration_n]
    formal = candidates[calibration_n:calibration_n + formal_n]
    def allocation(items):
        return dict(sorted(Counter(r["public"]["input"]["domain"] + "/" + r["question_type"] for r in items).items()))
    return {"status": "preview_only_not_frozen", "seed": seed, "sampling_unit": "split_group_then_one_question",
            "frame_sha256": digest(sorted((r["sample_id"], digest(r)) for r in records)),
            "frame_records": len(records), "eligible_groups": len(groups), "excluded_groups": list(excluded_groups),
            "requested": {"calibration": calibration_n, "formal": formal_n},
            "available_preview": {"calibration": len(calibration), "formal": len(formal)},
            "allocation": {"calibration": allocation(calibration), "formal": allocation(formal)},
            "shortfall": max(0, calibration_n + formal_n - len(candidates)),
            "inclusion": "accepted simulator records in explicitly supplied frame; one item per split group; exclude prior calibration/development groups",
            "population": "group-balanced physical trajectories in the supplied versioned release frame, random question within trajectory; pooled only",
            "formal_identity_export": "disabled_initial_milestone"}

def export_packets(records: list[dict], output: Path, phase: str = "development") -> Path:
    if phase not in ("development", "calibration"):
        raise ValueError("definitive formal sample export disabled until annotation/release/rubric readiness")
    output = external(output)
    if not records:
        raise ValueError("empty audit packet set")
    if len({r["sample_id"] for r in records}) != len(records):
        raise ValueError("duplicate packet record")
    if len({r["private"]["metadata"]["split_group_id"] for r in records}) != len(records):
        raise ValueError("multiple closely related records; select one per physical group")
    for record in records:
        validate(record)
    output.mkdir(parents=True, exist_ok=False)
    (output / "rubric.txt").write_text(RUBRIC, encoding="utf-8")
    assignments = []
    key = []
    for index, record in enumerate(records, 1):
        packet_id = "SPQ-" + digest({"phase": phase, "sample": record["sample_id"], "version": record["annotation_version"]})[:16]
        packet = {"packet_id": packet_id, "phase": phase, "sample_id": record["sample_id"],
                  "annotation_version": record["annotation_version"], "question_type": record["question_type"],
                  "structured_inputs": record["public"]["input"], "language_annotations": record["public"]["annotations"],
                  "qa": {"question": record["public"]["input"]["question"], "reference": record["private"]["reference"]},
                  "verification": {"metadata": record["private"]["metadata"], "bindings": record["private"]["evidence_bindings"]},
                  "annotation_completion": record["completion"], "rubric_version": "draft/0.1"}
        # Annotation provider identity lives only in the organizer key.
        key.append({"packet_id": packet_id, "sample_id": record["sample_id"], "source": record["source"],
                    "annotation_provenance": record["private"]["annotation_provenance"]})
        write(output / "packets" / (packet_id + ".json"), packet)
        body = escape(canonical(packet).decode())
        html = '<!doctype html><meta charset="utf-8"><title>SimPhysQA auditor packet</title><style>body{max-width:1100px;margin:32px auto;font:16px system-ui}pre{white-space:pre-wrap;overflow-wrap:anywhere}summary{cursor:pointer}</style>'
        html += "<h1>" + packet_id + "</h1><p>Private verification evidence: auditor use only. Development packet; annotations may be pending.</p>"
        html += "<h2>Question</h2><p>" + escape(packet["qa"]["question"]) + "</p>"
        html += "<h2>Reference</h2><p>" + escape(packet["qa"]["reference"]["label"]) + "</p>"
        html += "<h2>Language status</h2><pre>" + escape(canonical(packet["language_annotations"]).decode()) + "</pre>"
        html += "<h2>Rubric</h2><pre>" + escape(RUBRIC) + "</pre><details><summary>Complete inputs and verification evidence</summary><pre>" + body + "</pre></details>"
        (output / "packets" / (packet_id + ".html")).write_text(html, encoding="utf-8")
        assignments.append({"packet_id": packet_id, "sample_id": record["sample_id"], "phase": phase})
    write(output / "organizer-private" / "identity-key.json", key)
    for reviewer in REVIEWERS:
        path = output / "forms" / (reviewer + ".csv")
        path.parent.mkdir(parents=True, exist_ok=True)
        with path.open("x", encoding="utf-8", newline="") as stream:
            writer = csv.DictWriter(stream, fieldnames=COLUMNS)
            writer.writeheader()
            for assignment in assignments:
                writer.writerow({**assignment, "reviewer_id": reviewer})
    manifest(output, {"purpose": "human_audit_" + phase, "rubric_sha256": digest(RUBRIC),
                      "annotation_versions": sorted({r["annotation_version"] for r in records}),
                      "assignments": assignments, "reviewers": list(REVIEWERS), "ratings_status": "blank_not_collected",
                      "record_hashes": {r["sample_id"]: digest(r) for r in records}})
    return output

def import_ratings(packet_root: Path, form: Path, output: Path) -> dict:
    info = read(packet_root / "manifest.json")
    for name, expected in info["files"].items():
        path = (packet_root / name).resolve()
        if packet_root.resolve() not in path.parents or __import__("hashlib").sha256(path.read_bytes()).hexdigest() != expected:
            raise ValueError("packet integrity failure")
    assignments = {a["packet_id"]: a for a in info["assignments"]}
    originals = []
    seen = set()
    with form.open(encoding="utf-8-sig", newline="") as stream:
        reader = csv.DictReader(stream)
        if tuple(reader.fieldnames or ()) != COLUMNS:
            raise ValueError("rating form columns mismatch")
        for row in reader:
            expected = assignments.get(row["packet_id"])
            if expected is None or any(row[k] != expected[k] for k in ("sample_id", "phase")) or row["reviewer_id"] not in REVIEWERS:
                raise ValueError("rating assignment mismatch")
            identity = (row["packet_id"], row["reviewer_id"])
            if identity in seen:
                raise ValueError("duplicate independent rating")
            seen.add(identity)
            if not row["judgment"]:
                if row["criteria"] or row["error_categories"] or row["notes"]:
                    raise ValueError("findings without primary judgment")
                continue  # Blank forms are uncollected, never acceptable.
            if row["judgment"] not in ("acceptable", "material_error"):
                raise ValueError("invalid primary judgment")
            findings = dict(item.split("=", 1) for item in row["criteria"].split(";") if item)
            if set(findings) != set(CRITERIA) or any(v not in ("acceptable", "material_error", "not_applicable") for v in findings.values()):
                raise ValueError("all criterion findings required")
            categories = [s for s in row["error_categories"].split(";") if s]
            if not set(categories) <= set(ERRORS):
                raise ValueError("unknown error category")
            if row["judgment"] == "acceptable" and ("material_error" in findings.values() or categories):
                raise ValueError("acceptable rating contradicts findings")
            if row["judgment"] == "material_error" and (not categories or not row["notes"].strip()):
                raise ValueError("material error requires category and evidence notes")
            originals.append({**row, "criteria": findings, "error_categories": categories})
    result = {"rating_version": "simphysqa-ratings/0.1.0", "kind": "original_independent",
              "source_form_sha256": __import__("hashlib").sha256(form.read_bytes()).hexdigest(),
              "packet_manifest_sha256": digest(info), "ratings": originals,
              "collected": len(originals), "blank": len(seen) - len(originals),
              "adjudication": "separate_record_required", "corrections": "separate_version_required"}
    write(output, result)  # Exclusive-create; original files cannot be overwritten.
    return result
