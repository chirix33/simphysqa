"""Blinded packets, disjoint sampling previews, append-only independent rating imports."""
from __future__ import annotations
from collections import Counter, defaultdict
import csv
from html import escape
from pathlib import Path
import random
from .dataset import validate, public_record
from .answer_annotations import enriched_reference
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
            excluded_groups: tuple[str, ...] = (), include_development: bool = False) -> dict:
    if calibration_n < 0 or formal_n < 0:
        raise ValueError("negative sample size")
    if not include_development:
        durable = read(ROOT / "configs/simphysqa/development_exclusions.json")["excluded_groups"]
        excluded_groups = tuple(sorted(set(excluded_groups) | set(durable)))
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
    return {"status": "engineering_preview_exclusions_bypassed" if include_development else "preview_only_not_frozen", "seed": seed, "sampling_unit": "split_group_then_one_question",
            "frame_sha256": digest(sorted((r["sample_id"], digest(r)) for r in records)),
            "frame_records": len(records), "eligible_groups": len(groups), "excluded_groups": list(excluded_groups),
            "requested": {"calibration": calibration_n, "formal": formal_n},
            "available_preview": {"calibration": len(calibration), "formal": len(formal)},
            "allocation": {"calibration": allocation(calibration), "formal": allocation(formal)},
            "shortfall": max(0, calibration_n + formal_n - len(candidates)),
            "inclusion": "accepted simulator records in explicitly supplied frame; one item per split group; exclude prior calibration/development groups",
            "population": "group-balanced physical trajectories in the supplied versioned release frame, random question within trajectory; pooled only",
            "formal_identity_export": "disabled_initial_milestone"}

def export_packets(records: list[dict], output: Path, phase: str = "development", *, association_version: str | None = None) -> Path:
    if phase not in ("development", "calibration"):
        raise ValueError("definitive formal sample export disabled until annotation/release/rubric readiness")
    output = external(output)
    if not records:
        raise ValueError("empty audit packet set")
    if len({r["sample_id"] for r in records}) != len(records):
        raise ValueError("duplicate packet record")
    related = defaultdict(list)
    for record in records:
        related[record["private"]["metadata"]["split_group_id"]].append(record)
    for group in related.values():
        if (phase == "development" and all("answer_annotation" in r["private"] for r in group)
                and len(group) <= 3 and len({r["question_type"] for r in group}) == len(group)
                and {r["question_type"] for r in group} <= {"direct", "predictive", "counterfactual"}):
            continue  # Explicit 40-item engineering enrichment; never formal sampling.
        if len(group) > 1 and (phase != "development" or len(group) != 2 or {r["question_type"] for r in group} != {"direct", "predictive"}):
            raise ValueError("related records allowed only as development direct/predictive pairs")
    for record in records:
        validate(record)
    output.mkdir(parents=True, exist_ok=False)
    audit_rubric = RUBRIC
    if any(r["question_type"] == "explanation" for r in records):
        from .explanation import rubric_text
        audit_rubric += "\nExplanation-task supplement (selected outcomes intentionally supplied):\n" + rubric_text()
    if any(r["question_type"] == "clarification" for r in records):
        from .clarification import rubric_text
        audit_rubric += "\nClarification-task supplement (intentional gap, then recorded reply):\n" + rubric_text()
    (output / "rubric.txt").write_text(audit_rubric, encoding="utf-8")
    assignments = []
    key = []
    for index, record in enumerate(records, 1):
        view = public_record(record, association_version=association_version) if association_version else record["public"]
        identity = {"phase": phase, "sample": record["sample_id"], "version": record["annotation_version"]}
        if association_version:
            identity["export_version"] = association_version
        if "answer_annotation" in record["private"]:
            identity["answer_annotation_cache"] = record["private"]["answer_annotation"]["cache_identity"]
        if "explanation_annotation" in record["private"]:
            identity["explanation_annotation_cache"] = record["private"]["explanation_annotation"]["cache_identity"]
        if "clarification_annotation" in record["private"]:
            identity["clarification_annotation_cache"] = record["private"]["clarification_annotation"]["cache_identity"]
        packet_id = "SPQ-" + digest(identity)[:16]
        packet = {"packet_id": packet_id, "phase": phase, "sample_id": record["sample_id"],
                  "annotation_version": record["annotation_version"], "question_type": record["question_type"],
                  "structured_inputs": view["input"], "language_annotations": view["annotations"],
                  "qa": {"question": record["public"]["input"]["question"], "reference": enriched_reference(record)},
                  "verification": {"metadata": record["private"]["metadata"], "bindings": record["private"]["evidence_bindings"]},
                  "annotation_completion": record["completion"], "rubric_version": "draft/0.1"}
        if association_version:
            packet.update(export_version=view["export_version"], association_provenance=view["association_provenance"])
        if record["question_type"] == "counterfactual":
            proof = record["private"]["counterfactual_evidence"]
            packet["verification"]["paired_counterfactual"] = {
                "pair_id": proof["pair_id"], "parent_sample_id": record["private"]["source_record"]["sample_id"],
                "parent_group_id": record["trajectory_id"], "original_run_id": proof["original_run_id"],
                "alternative_run_id": proof["alternative_run_id"],
                "original_reference": record["private"]["source_record"]["reference"],
                "alternative_reference": record["private"]["reference"],
                "verification": proof["verification"], "intervention_change": proof["intervention_change"],
                "simulation_artifacts": proof["simulation_artifacts"]}
        if "answer_annotation" in record["private"]:
            from .answer_annotations import roots
            annotation = record["private"]["answer_annotation"]
            packet["answer_annotation"] = annotation
            packet["verification"]["answer_evidence_roots"] = roots(record, annotation["evidence_context"])
        if record["question_type"] == "explanation":
            from .explanation import evidence_roots
            packet["explanation_annotation"] = record["private"]["explanation_annotation"]
            packet["verification"]["answer_evidence_roots"] = evidence_roots(record)
            packet["rubric_version"] = record["private"]["reference"]["rubric_version"]
        if record["question_type"] == "clarification":
            from .clarification import roots
            packet["clarification_annotation"] = record["private"]["clarification_annotation"]
            packet["two_stage_task"] = {"initial_view": record["private"]["initial_view"],
                "reference_clarification_question": record["private"]["reference"]["reference_clarification_question"],
                "reference_question_origin": "authored_reference_not_actual_model_response",
                "recorded_reply": record["private"]["resolved_view"]["input"]["recorded_reply"],
                "resolved_view": record["private"]["resolved_view"]}
            packet["verification"]["answer_evidence_roots"] = roots(record)
            packet["verification"]["private_gap_witnesses"] = record["private"]["reference"]["witnesses"]
            packet["rubric_version"] = "information-gap-clarification-rubric/1.0.0"
        # Annotation provider identity lives only in the organizer key.
        key.append({"packet_id": packet_id, "sample_id": record["sample_id"], "source": record["source"],
                    "annotation_provenance": record["private"]["annotation_provenance"],
                    "generation_job": record["private"].get("generation_job")})
        write(output / "packets" / (packet_id + ".json"), packet)
        body = escape(canonical(packet).decode())
        html = '<!doctype html><meta charset="utf-8"><title>SimPhysQA auditor packet</title><style>body{max-width:1100px;margin:32px auto;font:16px system-ui}pre{white-space:pre-wrap;overflow-wrap:anywhere}summary{cursor:pointer}</style>'
        html += "<h1>" + packet_id + "</h1><p>Private verification evidence: auditor use only. Development packet; annotations may be pending.</p>"
        html += "<h2>Question</h2><p>" + escape(packet["qa"]["question"]) + "</p>"
        if record["question_type"] == "clarification":
            stages=packet["two_stage_task"]
            html += "<h2>Stage 1 reference clarification (authored; no model interaction executed)</h2><p>" + escape(stages["reference_clarification_question"]) + "</p>"
            html += "<h2>Recorded reply</h2><p>" + escape(stages["recorded_reply"]["text"]) + "</p>"
            html += "<h2>Stage 2 resolved question</h2><p>" + escape(stages["resolved_view"]["input"]["resolved_question"]) + "</p>"
        html += "<h2>Reference</h2><p>" + escape(packet["qa"]["reference"]["label"]) + "</p>"
        if "answer_annotation" in record["private"] or "explanation_annotation" in record["private"] or "clarification_annotation" in record["private"]:
            html += "<h2>Answer explanation (human unreviewed)</h2><pre>" + escape(packet["qa"]["reference"]["explanation"]) + "</pre>"
            html += "<h2>Numerical/observed solution trace and evidence bindings</h2><pre>" + escape(canonical(packet["qa"]["reference"]["solution_trace"]).decode()) + "</pre>"
        html += "<h2>Language status</h2><pre>" + escape(canonical(packet["language_annotations"]).decode()) + "</pre>"
        html += "<h2>Rubric</h2><pre>" + escape(audit_rubric) + "</pre><details><summary>Complete inputs and verification evidence</summary><pre>" + body + "</pre></details>"
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
    manifest(output, {"purpose": "human_audit_" + phase, "rubric_sha256": digest(audit_rubric),
                      "annotation_versions": sorted({r["annotation_version"] for r in records}),
                      "assignments": assignments, "reviewers": list(REVIEWERS), "ratings_status": "blank_not_collected",
                      "record_hashes": {r["sample_id"]: digest(r) for r in records},
                      **({"export_version": association_version, "public_view_hashes": {
                          r["sample_id"]: digest(public_record(r, association_version=association_version)) for r in records}}
                         if association_version else {})})
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
