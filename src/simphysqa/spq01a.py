"""Offline SPQ01a enrichment, immutable cache/resume and development exports."""
from __future__ import annotations
import argparse
from collections import Counter, defaultdict
from copy import deepcopy
from hashlib import sha256
from pathlib import Path
from .audit import export_packets, import_ratings
from .dataset import load, public_record, validate
from .event_language import CONTRACT, enrich, generator_input, identity, versions
from .evaluation import export_requests
from .io import ROOT, canonical, digest, external, manifest, read, write

def retained(path, value):
    """Exclusive-create or verify exact existing bytes; never overwrite work."""
    expected = canonical(value)
    if path.exists():
        if path.read_bytes() != expected:
            raise ValueError("resume content mismatch: " + str(path))
    else:
        write(path, value)

def verify_manifest(folder):
    info = read(folder / "manifest.json")
    for rel, expected in info["files"].items():
        path = (folder / rel).resolve()
        if folder.resolve() not in path.parents or sha256(path.read_bytes()).hexdigest() != expected:
            raise ValueError("retained export integrity failure: " + rel)
    return info

def run(records_path, prior_summary, prior_packets, output, plan_path, config_path):
    output = external(output)
    config = read(config_path)
    if config["contract"] != CONTRACT or config["new_model_requests"] != 0 or config["method"] != "deterministic_schedule_enrichment":
        raise ValueError("SPQ01a configuration permits offline deterministic enrichment only")
    before = list(load(records_path))
    if len(before) != 32 or Counter(r["question_type"] for r in before) != {"direct": 16, "predictive": 16}:
        raise ValueError("SPQ01a development frame must retain the 32 SPQ01 QA items")
    groups = defaultdict(list)
    for r in before:
        groups[r["trajectory_id"]].append(r)
    if len(groups) != 16 or any({r["question_type"] for r in pair} != {"direct", "predictive"} or len(pair) != 2 for pair in groups.values()):
        raise ValueError("development physical pairing mismatch")
    physical = [next(r for r in pair if r["question_type"] == "predictive") for pair in groups.values()]
    if Counter(r["public"]["input"]["domain"] for r in physical) != dict(config["trajectories_per_domain"]):
        raise ValueError("development domain allocation mismatch")
    ledger = read(prior_summary)
    accounting = {"method": config["method"], "prior_accounting_sha256": digest(ledger),
        "prior_initial_requests": ledger["initial_requests"], "prior_total_attempts": ledger["total_attempts"],
        "prior_estimated_spend_usd": ledger["charged_with_unknown_reservations_usd"],
        "new_model_requests": 0, "new_attempts": 0, "new_estimated_spend_usd": 0,
        "cumulative_initial_requests": ledger["initial_requests"], "cumulative_total_attempts": ledger["total_attempts"],
        "cumulative_estimated_spend_usd": ledger["charged_with_unknown_reservations_usd"],
        "limits": config["cumulative_budget"],
        "remaining_estimated_spend_usd": round(config["cumulative_budget"]["usd"] - ledger["charged_with_unknown_reservations_usd"], 6),
        "model_generation": "not_needed_existing_measurement_language_retained", "invoice_charge": "not_confirmed"}
    if accounting["cumulative_initial_requests"] > config["cumulative_budget"]["initial_requests"] or accounting["cumulative_total_attempts"] > config["cumulative_budget"]["total_attempts"] or accounting["remaining_estimated_spend_usd"] < 0:
        raise ValueError("shared SPQ01 budget exceeded")
    prepared = {r["trajectory_id"]: generator_input(r["public"]["input"]) for r in physical}
    plan = read(plan_path)
    old_packets = verify_manifest(prior_packets)
    preflight = {"versions": versions(), "configuration": config, "accounting": accounting,
        "qa_records": len(before), "unique_physical_inputs": len(physical),
        "input_bytes": {"minimum": min(len(canonical(v)) for v in prepared.values()),
                        "maximum": max(len(canonical(v)) for v in prepared.values()),
                        "total": sum(len(canonical(v)) for v in prepared.values())},
        "request_count": 0, "budget_estimate_usd": 0,
        "job_identity": digest({"records_sha256": sha256(records_path.read_bytes()).hexdigest(),
                                "versions": versions(), "config": config, "ledger": ledger,
                                "baseline_plan": plan, "prior_packets_sha256": digest(old_packets)})}
    print(canonical(preflight).decode(), end="", flush=True)
    retained(output / "preflight.json", preflight)
    after = []
    # Entire export is deterministic; item completion is durable before packaging.
    for r in before:
        key = identity(r["public"]["input"], r["public"]["annotations"])
        path = output / "items" / (r["sample_id"] + ".json")
        expected = enrich(r)
        validate(expected)
        if path.exists():
            cached = read(path)
            if cached != expected or cached["public"]["annotations"]["event_context"]["cache_identity"] != key:
                raise ValueError("completed cache identity/content mismatch")
            validate(cached)
        else:
            write(path, expected)
        after.append(expected)
    retained(output / "organizer-private" / "accounting.json", accounting)
    for group, value in prepared.items():
        retained(output / "generator-inputs" / (group + ".json"), value)
    for original, revised in zip(before, after):
        if original["sample_id"] != revised["sample_id"] or original["source"] != revised["source"] or original["public"]["input"] != revised["public"]["input"]:
            raise ValueError("QA identity, source or physical input changed")
        for key in ("reference", "metadata", "evidence_bindings", "annotation_provenance", "source_record", "derivation"):
            if original["private"].get(key) != revised["private"].get(key):
                raise ValueError("original QA/provenance changed: " + key)
    payload = b"".join(canonical(r) for r in after)
    path = output / "qa-records.jsonl"
    if path.exists():
        if path.read_bytes() != payload:
            raise ValueError("resume QA export mismatch")
    else:
        path.parent.mkdir(parents=True, exist_ok=True)
        with path.open("xb") as stream:
            stream.write(payload)
    retained(output / "public-qa.json", [public_record(r) for r in after])
    revised_physical = [r for r in after if r["question_type"] == "predictive"]
    linkage = [{"trajectory_id": r["trajectory_id"], "source_sample_id": r["sample_id"],
                "public_input_sha256": digest(r["public"]["input"]),
                **r["public"]["annotations"]["event_context"]} for r in revised_physical]
    retained(output / "event-state-linkage.json", {"purpose": "development_public_only_deduplicated_physical_views", "trajectories": linkage})
    coverage = {}
    for domain in sorted(config["trajectories_per_domain"]):
        items = [r for r in revised_physical if r["public"]["input"]["domain"] == domain]
        contexts = [r["public"]["annotations"]["event_context"]["links"] for r in items]
        counts = Counter(l["temporal_relationship"] for c in contexts for l in c["state_links"])
        coverage[domain] = {"trajectories": len(items), "saved_states": sum(len(r["public"]["input"]["states"]) for r in items),
            "declared_events": sum(len(c["events"]) for c in contexts), "state_event_relationships": dict(counts),
            "between_saved_state_links": sum(len(c["between_state_links"]) for c in contexts),
            "controller_phases": sum(len(e["controller"]["phases"]) for c in contexts for e in c["events"]),
            "unresolved_controllers": sum(e["controller"]["kind"] == "unresolved_declared_law" for c in contexts for e in c["events"])}
    retained(output / "coverage.json", {"population": "16 engineering development trajectories; not release quality estimates", "deduplicated": True,
        "domains": coverage, "real_active_overlap": sum(c["state_event_relationships"].get("scheduled_active", 0) for c in coverage.values()),
        "coverage_gap": "All observed windows end at 0.2 s before later interventions. Active/between-state boundaries are exercised only in labeled synthetic software tests."})
    packet_root = output / "audit-development"
    # Build directories transactionally. Incomplete packaging never gets a ready
    # manifest; leave it intact and report rather than erase or overwrite it.
    if packet_root.exists():
        packet_manifest = verify_manifest(packet_root)
        if packet_manifest["record_hashes"] != {r["sample_id"]: digest(r) for r in after}:
            raise ValueError("retained audit export uses other records")
    else:
        export_packets(after, packet_root, "development")
        packet_manifest = read(packet_root / "manifest.json")
    baseline_root = output / "baseline-requests"
    if baseline_root.exists():
        baseline_manifest = verify_manifest(baseline_root)
        if baseline_manifest["conditions"] != plan["conditions"]:
            raise ValueError("retained baseline condition mismatch")
    else:
        baseline_manifest = export_requests(after, plan, baseline_root)
    blank_results = []
    for reviewer in ("R1", "R2", "R3"):
        rating_path = output / "verification" / (reviewer + "-blank-import.json")
        if rating_path.exists():
            value = read(rating_path)
        else:
            value = import_ratings(packet_root, packet_root / "forms" / (reviewer + ".csv"), rating_path)
        if value["collected"] != 0 or value["blank"] != 32:
            raise ValueError("blank ratings changed")
        blank_results.append({"reviewer": reviewer, "collected": value["collected"], "blank": value["blank"]})
    examples = {}
    for r in revised_physical:
        domain = r["public"]["input"]["domain"]
        if domain in examples:
            continue
        original = next(old for old in before if old["sample_id"] == r["sample_id"])
        old_id = next(a["packet_id"] for a in old_packets["assignments"] if a["sample_id"] == r["sample_id"])
        new_id = next(a["packet_id"] for a in packet_manifest["assignments"] if a["sample_id"] == r["sample_id"])
        examples[domain] = {"sample_id": r["sample_id"], "before_packet": str(prior_packets / "packets" / (old_id + ".html")),
            "after_packet": str(packet_root / "packets" / (new_id + ".html")),
            "before_summary": original["public"]["annotations"]["trajectory"]["text"],
            "after_summary": r["public"]["annotations"]["trajectory"]["text"],
            "before_final_timestamp": original["public"]["annotations"]["timestamps"][-1]["text"],
            "after_final_timestamp": r["public"]["annotations"]["timestamps"][-1]["text"]}
    retained(output / "before-after.json", examples)
    report = {"qa_records": 32, "preserved_sample_ids": True, "preserved_public_inputs_and_cutoffs": True,
        "preserved_source_provenance": True, "preserved_predictive_references": 16, "preserved_direct_references": 16,
        "event_annotation_validation": "passed_for_all_32_final_views", "baseline_conditions": len(plan["conditions"]),
        "baseline_requests": 32 * len(plan["conditions"]), "blank_rating_imports": blank_results,
        "new_requests": 0, "new_spend_usd": 0, "human_quality_or_agreement": "pending_no_judgments", "failures": []}
    retained(output / "verification" / "checks.json", report)
    details = {"purpose": "SPQ01a_event_aware_development_enrichment", "versions": versions(),
        "job_identity": preflight["job_identity"], "qa_records": 32, "development_trajectories": 16,
        "baseline_manifest_sha256": digest(baseline_manifest), "audit_manifest_sha256": digest(packet_manifest),
        "original_packets_manifest_sha256": digest(old_packets), "accounting": accounting}
    if (output / "manifest.json").exists():
        info = verify_manifest(output)
        if any(info[k] != v for k, v in details.items()):
            raise ValueError("resumed manifest identity mismatch")
    else:
        manifest(output, details)
    print(canonical(report).decode(), end="", flush=True)
    return report

def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--records", type=Path, required=True)
    parser.add_argument("--prior-summary", type=Path, required=True)
    parser.add_argument("--prior-packets", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--evaluation-config", type=Path, default=ROOT / "configs/simphysqa/evaluation.json")
    parser.add_argument("--config", type=Path, default=ROOT / "configs/simphysqa/annotation_spq01a.json")
    args = parser.parse_args()
    run(args.records, args.prior_summary, args.prior_packets, args.output, args.evaluation_config, args.config)

if __name__ == "__main__":
    main()
