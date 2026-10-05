"""Offline versioned export of the 32 SPQ01a development association views."""
import argparse
from collections import Counter
from hashlib import sha256
from pathlib import Path
from .associations import VERSION, strip_associations, validate_view, versions
from .audit import export_packets, import_ratings
from .dataset import load, public_record
from .evaluation import export_requests
from .io import ROOT, canonical, digest, external, manifest, parse, read, write
from .spq01a import retained, verify_manifest

def run(source, output, plan_path=ROOT / "configs/simphysqa/evaluation.json"):
    output = external(output)
    source = source.resolve()
    if output == source or source in output.parents or output in source.parents:
        raise ValueError("new associations must use a separate output root")
    old_manifest = verify_manifest(source)
    original_bytes = (source / "qa-records.jsonl").read_bytes()
    records = list(load(source / "qa-records.jsonl"))
    if len(records) != 32 or Counter(r["question_type"] for r in records) != {"direct":16,"predictive":16} or len({r["trajectory_id"] for r in records}) != 16:
        raise ValueError("bounded export requires the existing 32 SPQ01a development QA")
    plan = read(plan_path)
    views = [public_record(r, association_version=VERSION) for r in records]
    identity = {**versions(), "source_manifest_sha256": digest(old_manifest),
                "source_records_file_sha256": sha256(original_bytes).hexdigest(), "baseline_plan_sha256": digest(plan)}
    preflight = {**identity, "qa_records":len(records), "new_simulations":0, "new_model_calls":0, "new_spend_usd":0}
    print(canonical(preflight).decode(), end="", flush=True)
    retained(output / "preflight.json", preflight)
    for record, view in zip(records, views):
        retained(output / "public-items" / (record["sample_id"] + ".json"), view)
    retained(output / "public-qa.json", views)
    # Canonical private organizer records are copied byte-for-byte, never indexed
    # in place or relabeled with a new physical/source schema.
    path = output / "qa-records.jsonl"
    if path.exists():
        if path.read_bytes() != original_bytes:
            raise ValueError("canonical organizer records changed")
    else:
        with path.open("xb") as stream:
            stream.write(original_bytes)
    frame = []
    for r, v in zip(records, views):
        if r["question_type"] != "predictive":
            continue
        frame.append({"trajectory_id":r["trajectory_id"], "sample_id":r["sample_id"],
            "states":[{"state_id":s["state_id"],"linked_events":s["linked_events"]} for s in v["input"]["states"]],
            "known_events":[{"event_id":e["event_id"],"linked_states":e["linked_states"]} for e in v["input"]["known_events"]],
            "between_state_associations":v["input"]["between_state_associations"],
            "association_provenance":v["association_provenance"]})
    retained(output / "event-state-associations.json", {"export_version":VERSION,"deduplicated_physical_views":True,"trajectories":frame})
    packets = output / "audit-development"
    hashes = {r["sample_id"]:digest(r) for r in records}
    if packets.exists():
        pm = verify_manifest(packets)
        if pm.get("export_version") != VERSION or pm["record_hashes"] != hashes or pm["public_view_hashes"] != {v["sample_id"]:digest(v) for v in views}:
            raise ValueError("retained packet export version/content mismatch")
    else:
        export_packets(records, packets, "development", association_version=VERSION)
        pm = read(packets / "manifest.json")
    baseline = output / "baseline-requests"
    if baseline.exists():
        bm = verify_manifest(baseline)
        if bm.get("export_version") != VERSION or bm["conditions"] != plan["conditions"]:
            raise ValueError("retained baseline export mismatch")
    else:
        bm = export_requests(records, plan, baseline, association_version=VERSION)
    for reviewer in ("R1", "R2", "R3"):
        path = output / "verification" / (reviewer + "-blank-import.json")
        if path.exists():
            rating = read(path)
        else:
            rating = import_ratings(packets, packets / "forms" / (reviewer + ".csv"), path)
        if rating["collected"] != 0 or rating["blank"] != 32:
            raise ValueError("blank-rating import mismatch")
    assignments = {a["sample_id"]:a["packet_id"] for a in pm["assignments"]}
    examples = {}
    for r, v in zip(records, views):
        original = public_record(r)
        validate_view(original, v)
        assert strip_associations(v["input"]) == r["public"]["input"]
        packet = read(packets / "packets" / (assignments[r["sample_id"]] + ".json"))
        if packet["structured_inputs"] != v["input"] or packet["language_annotations"] != v["annotations"] or packet["qa"]["reference"] != r["private"]["reference"] or packet["association_provenance"] != v["association_provenance"]:
            raise ValueError("audit packet is inconsistent with public view/source QA")
        if "gpt-5.6-sol" in canonical(packet).decode() or "annotation_provenance" in packet:
            raise ValueError("organizer identity exposed in packet")
        domain = r["public"]["input"]["domain"]
        if domain not in examples and r["question_type"] == "predictive":
            examples[domain] = {"sample_id":r["sample_id"],"packet":str(packets / "packets" / (assignments[r["sample_id"]] + ".html")), "public_view":str(output / "public-items" / (r["sample_id"] + ".json"))}
    expected = {v["sample_id"]:v for v in views}
    for condition in plan["conditions"]:
        requests = read(baseline / (condition["condition_id"] + ".json"))
        if len(requests) != 32 or len({q["sample_id"] for q in requests}) != 32:
            raise ValueError("baseline request count/identity mismatch")
        for q in requests:
            content = parse(q["messages"][0]["content"].split("\n",1)[1])
            if q["tools"] != [] or content != expected[q["sample_id"]] or "private" in content:
                raise ValueError("baseline public projection mismatch")
    retained(output / "examples.json", examples)
    relationships = Counter(x["temporal_relationship"] for t in frame for s in t["states"] for x in s["linked_events"])
    report = {"export_version":VERSION, "qa_records":32,"deduplicated_trajectories":16,
        "deduplicated_state_event_associations":sum(relationships.values()),"deduplicated_relationships":dict(relationships),
        "deduplicated_between_state_associations":sum(len(t["between_state_associations"]) for t in frame),
        "qa_identity_reference_measurement_cutoff_preservation":"passed", "canonical_records_byte_preservation":True,
        "bidirectional_integrity_uniqueness_agreement":"passed_all_32_views", "audit_packets":32,
        "baseline_public_views_checked":32*len(plan["conditions"]),"independent_ratings":0,"blank_forms":3,
        "new_simulations":0,"new_model_calls":0,"new_spend_usd":0,
        "real_active_overlap_coverage":"absent_unchanged_from_SPQ01a", "human_quality":"pending"}
    retained(output / "verification" / "checks.json", report)
    if verify_manifest(source) != old_manifest:
        raise ValueError("original SPQ01a output changed")
    details = {"purpose":"SPQ01a_bidirectional_association_development_export", **identity,
        "audit_manifest_sha256":digest(pm),"baseline_manifest_sha256":digest(bm),"checks":report}
    if (output / "manifest.json").exists():
        info = verify_manifest(output)
        if any(info[k] != v for k,v in details.items()):
            raise ValueError("resumed association export manifest mismatch")
    else:
        manifest(output, details)
    print(canonical(report).decode(), end="", flush=True)
    return report

def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--source",type=Path,required=True,help="retained SPQ01a event-language output root")
    parser.add_argument("--output",type=Path,required=True,help="new external versioned output root")
    parser.add_argument("--evaluation-config",type=Path,default=ROOT / "configs/simphysqa/evaluation.json")
    args=parser.parse_args()
    run(args.source,args.output,args.evaluation_config)

if __name__ == "__main__":
    main()
