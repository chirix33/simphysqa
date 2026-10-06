"""SPQ03: eight saved-pair explanation items; no simulations or model calls."""
import argparse
from collections import Counter
from pathlib import Path
from html import escape
from hashlib import sha256
from .io import ROOT, canonical, digest, read, manifest, external
from .dataset import load, validate, public_record
from .explanation import build, versions, rubric_text
from .explanation_evaluation import VERSION as RESPONSE, EVALUATOR
from .answer_export import retained_bytes, file_hash
from .spq01a import retained, verify_manifest
from .audit import export_packets, import_ratings
from .evaluation import export_requests

VERSION="spq03-explanation-export/1.0.0"

def export(parents_path,plan_path,output):
    output=external(output)
    if output==parents_path.parent or output in parents_path.resolve().parents or parents_path.parent.resolve() in output.parents:
        raise ValueError("explanation export must be separate from accepted parent artifacts")
    source_root=parents_path.parent.parent
    verify_manifest(source_root)
    all_parents=list(load(parents_path));parents=[p for p in all_parents if p["question_type"]=="counterfactual"]
    plan=read(plan_path);by_pair={p["private"]["counterfactual_evidence"]["pair_id"]:p for p in parents}
    expected_ids=[p["pair_id"] for p in plan["pairs"]]
    if len(all_parents)!=40 or len(parents)!=8 or set(by_pair)!=set(expected_ids) or Counter(p["public"]["input"]["domain"] for p in parents)!={d:2 for d in ("robotic_arm","driving","object_pushing_stacking","tethered_load")}:
        raise ValueError("require all eight frozen pairs from accepted 40-item export")
    preflight={"export_version":VERSION,"versions":versions(),"parent_export_sha256":digest(read(source_root/"manifest.json")),
        "parent_file_sha256":file_hash(parents_path),"frozen_plan_sha256":digest(plan),"frozen_pair_ids":expected_ids,
        "exporter_sha256":sha256(Path(__file__).read_text(encoding="utf-8").encode()).hexdigest(),
        "sampling":"Reuse all eight frozen SPQ02 pairs and their selected targets; no new selection or replacement",
        "formal_exclusions_sha256":digest(read(ROOT/"configs/simphysqa/development_exclusions.json")),
        "new_simulations":0,"new_model_calls":0,"new_spend_usd":0}
    retained(output/"preflight.json",preflight)
    records=[];failures=[];links=[]
    for selected in plan["pairs"]:
        parent=by_pair[selected["pair_id"]]
        if parent["trajectory_id"]!=selected["scenario"]["group"]:raise ValueError("frozen group differs")
        try:
            record=build(parent);validate(record)
        except Exception as exc:
            failure={"pair_id":selected["pair_id"],"parent_sample_id":parent["sample_id"],"status":"failed",
                "error_type":type(exc).__name__,"message":str(exc),"versions":versions()}
            retained(output/"organizer-private/failures"/(selected["pair_id"]+".json"),failure)
            failures.append(failure);continue
        retained(output/"organizer-private/items"/(record["sample_id"]+".json"),record)
        view=public_record(record,association_version="simphysqa-associations/1.1.1")
        retained(output/"public-items"/(record["sample_id"]+".json"),view)
        records.append(record)
        links.append({"explanation_sample_id":record["sample_id"],"counterfactual_parent_id":parent["sample_id"],
            "pair_id":selected["pair_id"],"trajectory_id":record["trajectory_id"],
            "split":record["private"]["metadata"]["split"],"split_group_id":record["private"]["metadata"]["split_group_id"],
            "target":record["public"]["input"]["answer_spec"][0],"related_existing_qa_ids":[p["sample_id"] for p in all_parents if p["trajectory_id"]==record["trajectory_id"]],
            "fresh_formal_excluded":True})
    retained_bytes(output/"organizer-private/qa-records.jsonl",b"".join(canonical(r) for r in records))
    retained(output/"public-qa.json",[public_record(r,association_version="simphysqa-associations/1.1.1") for r in records])
    retained(output/"item-index.json",{"version":VERSION,"existing_export":source_root.name,
        "existing_export_manifest_sha256":preflight["parent_export_sha256"],
        "existing_40_items":[{"sample_id":p["sample_id"],"trajectory_id":p["trajectory_id"],"question_type":p["question_type"],"domain":p["public"]["input"]["domain"]} for p in all_parents],
        "new_explanation_items":links,"formal_sample_exported":False})
    rubric=read(ROOT/"configs/simphysqa/explanation_rubric.json")
    retained(output/"explanation-rubric.json",rubric)
    retained_bytes(output/"explanation-rubric.txt",rubric_text().encode())
    packets=output/"audit-development"
    if records:
        if packets.exists():verify_manifest(packets)
        else:export_packets(records,packets,"development",association_version="simphysqa-associations/1.1.1")
        pm=read(packets/"manifest.json")
        if pm["record_hashes"]!={r["sample_id"]:digest(r) for r in records}:raise ValueError("stale packet export")
        requests=output/"public-requests"
        if requests.exists():verify_manifest(requests)
        else:export_requests(records,read(ROOT/"configs/simphysqa/evaluation.json"),requests,association_version="simphysqa-associations/1.1.1")
        blanks=[]
        for reviewer in ("R1","R2","R3"):
            dest=output/"verification"/(reviewer+"-blank-import.json")
            result=read(dest) if dest.exists() else import_ratings(packets,packets/"forms"/(reviewer+".csv"),dest)
            if result["collected"] or result["blank"]!=len(records):raise ValueError("blank forms became ratings")
            blanks.append({"reviewer":reviewer,"collected":0,"blank":len(records)})
        examples={};sections=[]
        for r in records:
            entry=next(a for a in pm["assignments"] if a["sample_id"]==r["sample_id"])
            packet=packets/"packets"/(entry["packet_id"]+".html")
            domain=r["public"]["input"]["domain"]
            examples.setdefault(domain,{"sample_id":r["sample_id"],"packet":str(packet)})
            sections.append('<section><h2>'+escape(domain)+' — '+escape(r["sample_id"])+
                '</h2><a href="'+packet.as_uri()+'">Complete question/reference/trace/bindings and rubric</a><p>'+escape(r["public"]["input"]["question"])+
                '</p><pre>'+escape(r["private"]["reference"]["explanation"])+ '</pre></section>')
        retained(output/"examples.json",examples)
        retained_bytes(output/"inspection.html",('<!doctype html><meta charset="utf-8"><title>SPQ03 explanation QA development</title><style>body{max-width:1050px;margin:2em auto;font:17px system-ui;line-height:1.5}pre{white-space:pre-wrap}section{border-top:1px solid #aaa;padding-top:1em}</style><h1>Eight matched-intervention explanation QA — development</h1><p>Intentionally supplied selected simulation outcomes; observed prefix unchanged. Private auditor evidence. Human judgments uncollected.</p>'+''.join(sections)).encode())
    else:blanks=[]
    counts={"version":VERSION,"completed":len(records),"failed":len(failures),"pending":8-len(records)-len(failures),
        "domains":dict(Counter(r["public"]["input"]["domain"] for r in records)),"prepared_requests":9*len(records),
        "blank_rating_imports":blanks,"response_contract":RESPONSE,"factual_evaluator":EVALUATOR,
        "supplied_outcome_disclosure":"Only selected factual/omission readouts in supplied_comparison; no inserted observed states",
        "automatic_verification":"target/typed readout equality, saved parent evidence, claim resolution, deterministic consistency; not human prose quality",
        "human_explanation_judgments":"uncollected","new_simulations":0,"new_model_calls":0,"new_spend_usd":0}
    retained(output/"verification/checks.json",counts)
    if (output/"manifest.json").exists():verify_manifest(output)
    else:manifest(output,{"purpose":"SPQ03_eight_development_explanation_items",**preflight,"counts":counts})
    print(canonical(counts).decode(),end="")
    return counts

def main():
    p=argparse.ArgumentParser(description=__doc__)
    for name in ("parents","plan","output"):p.add_argument("--"+name,type=Path,required=True)
    a=p.parse_args();c=export(a.parents,a.plan,a.output)
    if c["failed"] or c["pending"]:raise SystemExit(1)

if __name__=="__main__":main()
