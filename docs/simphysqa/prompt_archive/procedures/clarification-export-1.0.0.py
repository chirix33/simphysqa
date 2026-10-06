"""Bounded SPQ04 export: saved evidence only, immutable outputs, no model calls."""
import argparse
from collections import Counter
from pathlib import Path
from html import escape
from hashlib import sha256
from .io import ROOT, canonical, digest, read, manifest, external
from .dataset import load, validate, public_record
from .clarification import build, select, versions, rubric_text, VERSION as CONTRACT
from .clarification_evaluation import initial_request, continuation_template
from .answer_export import retained_bytes, file_hash
from .spq01a import retained, verify_manifest
from .audit import export_packets, import_ratings

VERSION="spq04-clarification-export/1.0.0"


def export(parents_path, explanations, plan_path, runs, output):
    output=external(output)
    source_root=parents_path.parent.parent
    for root in (source_root,explanations,runs):
        verify_manifest(root)
        if output==root or root in output.parents or output in root.parents:raise ValueError("new export must be separate from all parents")
    original=list(load(parents_path));accepted_explanations=list(load(explanations/"organizer-private/qa-records.jsonl"))
    parents=[r for r in original if r["question_type"]=="counterfactual"]
    plan=read(plan_path);by_pair={r["private"]["counterfactual_evidence"]["pair_id"]:r for r in parents}
    if len(original)!=40 or len(accepted_explanations)!=8 or len(parents)!=8 or set(by_pair)!={p["pair_id"] for p in plan["pairs"]}:raise ValueError("require accepted 48 QA and all eight frozen pairs")
    preflight={"version":VERSION,"versions":versions(),"accepted_base":"395139d3ee9717df0cb48b480daafa40b691b5f8",
        "accepted_40_sha256":file_hash(parents_path),"accepted_8_explanations_sha256":file_hash(explanations/"organizer-private/qa-records.jsonl"),
        "frozen_plan_sha256":digest(plan),"saved_runs_manifest_sha256":digest(read(runs/"manifest.json")),
        "export_implementation_sha256":sha256(Path(__file__).read_text(encoding="utf-8").encode()).hexdigest(),
        "selection_rule":"Reuse eight frozen groups, in frozen plan order. Original selected target first, then sorted original source targets for condition ambiguity; pre-stacked block positions for entity gap; tether saved .4/1 s position for time gap. Strict scorer-region separation, no replacement or threshold changes.",
        "formal_exclusions_sha256":digest(read(ROOT/"configs/simphysqa/development_exclusions.json")),
        "new_simulations":0,"new_model_calls":0,"executed_interactions":0,"spend_usd":0}
    retained(output/"preflight.json",preflight)
    records=[];failures=[];selection=[]
    for pair in plan["pairs"]:
        parent=by_pair[pair["pair_id"]]
        chosen=select(parent)
        try:
            if parent["trajectory_id"]!=pair["scenario"]["group"]:raise ValueError("frozen group differs")
            record,chosen=build(parent,runs)
            if record is None:raise ValueError(chosen["reason"])
            validate(record)
        except Exception as exc:
            failure={"pair_id":pair["pair_id"],"parent_sample_id":parent["sample_id"],"trajectory_id":parent["trajectory_id"],"domain":parent["public"]["input"]["domain"],"status":"failed","candidate_selection":chosen,"error_type":type(exc).__name__,"message":str(exc),"versions":versions()}
            retained(output/"organizer-private/failures"/(pair["pair_id"]+".json"),failure)
            failures.append(failure);selection.append(failure);continue
        sid=record["sample_id"]
        retained(output/"organizer-private/items"/(sid+".json"),record)
        retained(output/"organizer-private/witnesses"/(sid+".json"),{"sample_id":sid,"trajectory_id":record["trajectory_id"],"selection":record["private"]["clarification_evidence"]["selection"],"witnesses":record["private"]["reference"]["witnesses"]})
        retained(output/"public-initial"/(sid+".json"),public_record(record))
        retained(output/"public-resolved"/(sid+".json"),record["private"]["resolved_view"])
        records.append(record)
        selection.append({"sample_id":sid,"pair_id":pair["pair_id"],"trajectory_id":record["trajectory_id"],"domain":record["public"]["input"]["domain"],"status":"qualified","selection":record["private"]["clarification_evidence"]["selection"]})
    retained(output/"organizer-private/selection-manifest.json",{"version":CONTRACT,"rule":preflight["selection_rule"],"candidates":selection,"population":"bounded engineering groups, not OOD or unbiased quality sample","replacement":False})
    retained_bytes(output/"organizer-private/qa-records.jsonl",b"".join(canonical(r) for r in records))
    retained(output/"public-initial.json",[public_record(r) for r in records])
    retained(output/"public-resolved.json",[r["private"]["resolved_view"] for r in records])
    retained(output/"clarification-rubric.json",read(ROOT/"configs/simphysqa/clarification_rubric.json"))
    retained_bytes(output/"clarification-rubric.txt",rubric_text().encode())
    retained(output/"item-index.json",{"version":VERSION,"accepted_items":[{"sample_id":r["sample_id"],"question_type":r["question_type"],"trajectory_id":r["trajectory_id"]} for r in original+accepted_explanations],
        "new_items":[{"sample_id":r["sample_id"],"pair_id":r["private"]["clarification_evidence"]["parent_record"]["private"]["counterfactual_evidence"]["pair_id"],"parent_sample_id":r["private"]["clarification_evidence"]["parent_sample_id"],"trajectory_id":r["trajectory_id"],"split":r["private"]["metadata"]["split"],"split_group_id":r["private"]["metadata"]["split_group_id"],"fresh_formal_excluded":True} for r in records],"formal_sample_exported":False,"ood_claim":False})
    conditions=read(ROOT/"configs/simphysqa/evaluation.json")["conditions"]
    if len(conditions)!=9 or len({c["condition_id"] for c in conditions})!=9:raise ValueError("require nine configured conditions")
    for c in conditions:
        retained(output/"public-requests"/(c["condition_id"]+".json"),[initial_request(r,c) for r in records])
        retained(output/"continuation-templates"/(c["condition_id"]+".json"),[continuation_template(r,c) for r in records])
    packets=output/"audit-development";blanks=[];examples={};sections=[]
    if records:
        if packets.exists():verify_manifest(packets)
        else:export_packets(records,packets,"development",association_version="simphysqa-associations/1.1.1")
        pm=read(packets/"manifest.json")
        if pm["record_hashes"]!={r["sample_id"]:digest(r) for r in records}:raise ValueError("stale audit export")
        for reviewer in ("R1","R2","R3"):
            dest=output/"verification"/(reviewer+"-blank-import.json")
            result=read(dest) if dest.exists() else import_ratings(packets,packets/"forms"/(reviewer+".csv"),dest)
            if result["collected"] or result["blank"]!=len(records):raise ValueError("blank forms became judgments")
            blanks.append({"reviewer":reviewer,"collected":0,"blank":len(records)})
        for r in records:
            a=next(a for a in pm["assignments"] if a["sample_id"]==r["sample_id"])
            path=packets/"packets"/(a["packet_id"]+".html");d=r["public"]["input"]["domain"]
            examples.setdefault(d,{"sample_id":r["sample_id"],"packet":str(path)})
            sections.append('<section><h2>'+escape(d)+' — '+escape(r["sample_id"])+ '</h2><a href="'+path.as_uri()+'">Two-stage question/reference/trace/private witnesses</a><p>'+escape(r["public"]["input"]["question"])+ '</p><p>Authored reference clarification: '+escape(r["private"]["reference"]["reference_clarification_question"])+ '</p><p>Recorded reply: '+escape(r["private"]["resolved_view"]["input"]["recorded_reply"]["text"])+ '</p><pre>'+escape(r["private"]["reference"]["explanation"])+ '</pre></section>')
    retained(output/"examples.json",examples)
    retained_bytes(output/"inspection.html",('<!doctype html><meta charset="utf-8"><title>SPQ04 clarification development</title><style>body{max-width:1050px;margin:2em auto;font:17px system-ui;line-height:1.5}pre{white-space:pre-wrap}section{border-top:1px solid #aaa;padding-top:1em}</style><h1>Clarification QA — private development inspection</h1><p>Reference questions and recorded author replies; zero executed model interactions. Witness answers are private. Human judgments uncollected.</p>'+''.join(sections)).encode())
    counts={"version":VERSION,"completed":len(records),"failed":len(failures),"pending":8-len(records)-len(failures),"domains":dict(Counter(r["public"]["input"]["domain"] for r in records)),"gap_types":dict(Counter(r["private"]["clarification_evidence"]["selection"]["ambiguity_type"] for r in records)),"prepared_initial_requests":9*len(records),"conditional_templates":9*len(records),"executed_interactions":0,"blank_imports":blanks,"new_simulations":0,"new_model_calls":0,"human_judgments":"uncollected"}
    retained(output/"verification/checks.json",counts)
    if (output/"manifest.json").exists():verify_manifest(output)
    else:manifest(output,{"purpose":"SPQ04_development_clarification_QA",**preflight,"counts":counts})
    print(canonical(counts).decode(),end="");return counts


def main():
    p=argparse.ArgumentParser(description=__doc__)
    for name in ("parents","explanations","plan","runs","output"):p.add_argument("--"+name,type=Path,required=True)
    a=p.parse_args();c=export(a.parents,a.explanations,a.plan,a.runs,a.output)
    if c["failed"] or c["pending"]:raise SystemExit(1)


if __name__=="__main__":main()
