"""SPQ02b offline 40-item enrichment using immutable saved SPQ01/SPQ02 evidence."""
import argparse
from collections import Counter
from copy import deepcopy
from hashlib import sha256
from pathlib import Path
from .answer_annotations import enrich, enriched_reference, versions, render, validate_answer_annotation
from .associations import VERSION as ASSOCIATIONS, validate_view as validate_associations
from .audit import export_packets, import_ratings
from .dataset import load, public_record, restore, validate
from .evaluation import export_requests
from .io import ROOT, canonical, digest, external, manifest, parse, read
from .spq01a import retained, verify_manifest

METHODS = {
    "robotic_arm": "MuJoCo mj_step with the saved XML RK4 integrator and generalized joint controls.",
    "driving": "PyBullet DIRECT stepSimulation, gravity/contact dynamics, 100 solver iterations and deterministic overlapping pairs; configured control updates precede numerical integration.",
    "object_pushing_stacking": "PyBullet DIRECT stepSimulation with gravity/friction/contact dynamics, 100 solver iterations and deterministic overlapping pairs; scheduled COM force is applied before each integration step.",
    "tethered_load": "Explicit RK4 of reduced-coordinate constrained pendulum dynamics using MuJoCo mass/bias terms and prescribed support motion at integration substeps."
}

def file_hash(path):
    return sha256(path.read_bytes()).hexdigest()

def context_for(record, pair, runs, implementation, arm):
    context = {"method": METHODS[record["public"]["input"]["domain"]], "implementation": implementation,
               "implementation_role": "Saved SPQ02 executed source; factual source method/settings independently documented in original simulation metadata. Exact replay qualified only for selected eight trajectories.",
               "verification": {"stored_source_admission": deepcopy(restore(record)["metadata"]["validation"]), "additional_exact_replay": "not_performed"},
               "runs": {}}
    if record["question_type"] == "direct":
        # Direct answers use only public evidence; no future physics or run receipts needed.
        return {"method": "observed exact channel readout", "implementation": {}, "verification": {"method": "public measurement/value equality"}, "runs": {}}
    if record["public"]["input"]["domain"] == "robotic_arm":
        context["arm_interpretation"] = arm
    if pair:
        key = pair["pair_id"]
        for role in ("original-coarse", "original-fine", "alternative-coarse", "alternative-fine"):
            folder = runs/"executions"/(key+"-"+role)
            result, reservation = read(folder/"result.json"), read(folder/"reservation.json")
            if result["status"] != "completed" or result["reservation_sha256"] != digest(reservation):
                raise ValueError("saved execution did not complete or reservation differs")
            context["runs"][role] = {"run_id": key+"-"+role, "result_file_sha256": file_hash(folder/"result.json"),
                "reservation_file_sha256": file_hash(folder/"reservation.json"), "reservation": reservation,
                "engine": result["rollout"]["engine"], "version": result["rollout"]["version"],
                "diagnostics": result["rollout"]["diagnostics"]}
        context["verification"].update({"additional_exact_replay": read(runs/"verification"/(key+"-replay.json")),
            "original_admission": read(runs/"verification"/(key+"-original-admission.json")),
            "alternative_admission": read(runs/"verification"/(key+"-alternative-admission.json"))})
        # Compare saved factual states directly to the immutable source at every requested timestamp.
        result = read(runs/"executions"/(key+"-original-coarse")/"result.json")
        saved = {s["state_id"]: s for s in result["rollout"]["states"]}
        source = restore(record)
        if any(canonical(saved[s["state_id"]]) != canonical(s) for s in source["reference"]["states"]):
            raise ValueError("factual execution evidence differs from source reference")
    return context

def retained_bytes(path, payload):
    path = external(path)
    if path.exists():
        if path.read_bytes() != payload:
            raise ValueError("resume content mismatch: "+str(path))
    else:
        path.parent.mkdir(parents=True, exist_ok=True)
        with path.open("xb") as stream:
            stream.write(payload)

def export(records_path, counterfactual_path, plan_path, runs, arm_path, output):
    output = external(output)
    if any(p.resolve() == output or p.resolve() in output.parents or output in p.resolve().parents for p in (records_path.parent, counterfactual_path.parent, runs)):
        raise ValueError("new export must be separate from prior evidence roots")
    prior = list(load(records_path))+list(load(counterfactual_path))
    if len(prior) != 40 or Counter(r["question_type"] for r in prior) != {"direct":16,"predictive":16,"counterfactual":8}:
        raise ValueError("require the accepted 40 development items")
    verify_manifest(runs)
    plan = read(plan_path); by_group = {p["scenario"]["group"]: p for p in plan["pairs"]}
    runtime = read(runs/"runtime.json"); implementation = {}
    for rel in ("src/phi_jepa/simulation/engines.py", "src/phi_jepa/simulation/bullet.py", "src/phi_jepa/simulation/scenes.py"):
        path = runs/"source-snapshot"/rel
        text = path.read_bytes().decode()
        if file_hash(path) != runtime["source_files"][rel]:
            raise ValueError("implementation snapshot differs from runtime")
        implementation[Path(rel).stem] = {"source_path": rel, "sha256": file_hash(path), "text": text}
    arm = read(arm_path)
    identity = {"versions": versions(), "parent_record_files": [file_hash(records_path),file_hash(counterfactual_path)],
                "saved_runs_manifest_sha256": digest(read(runs/"manifest.json")), "plan_sha256":digest(plan), "arm_sha256":digest(arm),
                "association_export_version": ASSOCIATIONS, "new_simulations":0,"new_model_calls":0,"new_spend_usd":0}
    retained(output/"preflight.json", identity)
    after=[]; comparisons=[]
    for before in prior:
        context = context_for(before, by_group.get(before["trajectory_id"]), runs, implementation, arm)
        record = enrich(before, context); validate(record)
        unchanged = deepcopy(record); unchanged["private"].pop("answer_annotation")
        if canonical(unchanged) != canonical(before):
            raise ValueError("non-annotation field changed")
        if canonical(public_record(before,association_version=ASSOCIATIONS)) != canonical(public_record(record,association_version=ASSOCIATIONS)):
            raise ValueError("private enrichment changed public view")
        retained(output/"organizer-private/items"/(record["sample_id"]+".json"),record)
        retained(output/"organizer-private/references"/(record["sample_id"]+".json"),enriched_reference(record))
        view=public_record(record,association_version=ASSOCIATIONS)
        validate_associations(public_record(record),view)
        retained(output/"public-items"/(record["sample_id"]+".json"),view)
        after.append(record)
        if record["question_type"] == "counterfactual":
            comparisons.append({"sample_id":record["sample_id"],"pair_id":record["private"]["counterfactual_evidence"]["pair_id"],
                "domain":record["public"]["input"]["domain"],"target":record["public"]["input"]["answer_spec"][0],
                **record["private"]["answer_annotation"]["targets"][0]["comparison"]})
            alternative = record["private"]["counterfactual_evidence"]["alternative_record"]
            projection=deepcopy(before)
            projection["sample_id"]=alternative["sample_id"]
            projection["public"]["input"]["answer_spec"]=deepcopy(alternative["input"]["answer_spec"])
            projection["private"]["reference"]=deepcopy(alternative["reference"])
            projection=enrich(projection,context)
            enriched_alt={"schema_version":"simphysqa-enriched-simulator-record/1.0.0","source_record_sha256":digest(alternative),
                "source_record":alternative,"annotation_projection":projection,"reference":enriched_reference(projection),
                "purpose":"private multi-target supporting alternative; original physical record retained unchanged"}
            retained(output/"organizer-private/alternative-records"/(alternative["sample_id"]+".json"),enriched_alt)
    retained_bytes(output/"organizer-private/qa-records.jsonl",b"".join(canonical(r) for r in after))
    retained(output/"public-qa.json",[public_record(r,association_version=ASSOCIATIONS) for r in after])
    retained(output/"organizer-private/comparisons.json",comparisons)
    header="| Domain | Target/time | Factual | Alternative | Exact equal | Scorer error | Factual passes alternative scorer |\n|---|---|---|---|---|---|---|\n"
    rows=[]
    from .answer_annotations import display
    for c in comparisons:
        t=c["target"];rows.append(f'| {c["domain"]} | {t["target_id"]} / {t["end_time"]} s | {display(c["factual_value"])} {t["unit"]} | {display(c["alternative_value"])} {t["unit"]} | {c["exact_canonical_equality"]} | {c["scorer_error"]} {c["scorer_error_unit"]} | {c["factual_answer_passes_alternative_scorer"]} |')
    retained_bytes(output/"organizer-private/comparisons.md",(header+"\n".join(rows)+"\n\nExact equality, numerical difference and answer distinguishability are separate. Equal Booleans and within-tolerance differences do not establish no physical effect. Human quality remains unreviewed.\n").encode())
    packets=output/"audit-development"
    if packets.exists(): pm=verify_manifest(packets)
    else: export_packets(after,packets,"development",association_version=ASSOCIATIONS);pm=read(packets/"manifest.json")
    if pm["record_hashes"] != {r["sample_id"]:digest(r) for r in after}:raise ValueError("audit record mismatch")
    evaluation=read(ROOT/"configs/simphysqa/evaluation.json")
    requests=output/"public-requests"
    if requests.exists(): verify_manifest(requests)
    else:export_requests(after,evaluation,requests,association_version=ASSOCIATIONS)
    expected={r["sample_id"]:public_record(r,association_version=ASSOCIATIONS) for r in after};n=0
    for condition in evaluation["conditions"]:
        for req in read(requests/(condition["condition_id"]+".json")):
            if req["tools"] or canonical(parse(req["messages"][0]["content"].split("\n",1)[1])) != canonical(expected[req["sample_id"]]):
                raise ValueError("request differs from accepted public-only projection")
            n+=1
    blanks=[]
    for reviewer in ("R1","R2","R3"):
        dest=output/"verification"/(reviewer+"-blank-import.json")
        rating=read(dest) if dest.exists() else import_ratings(packets,packets/"forms"/(reviewer+".csv"),dest)
        if rating["collected"] or rating["blank"] !=40:raise ValueError("blank form counted as a rating")
        blanks.append({"reviewer":reviewer,"collected":0,"blank":40})
    examples={}
    for r in after:
        key=r["public"]["input"]["domain"]+"/"+r["question_type"]
        assignment=next(a for a in pm["assignments"] if a["sample_id"]==r["sample_id"])
        packet=read(packets/"packets"/(assignment["packet_id"]+".json"))
        if packet["qa"]["reference"] != enriched_reference(r):raise ValueError("audit gold annotation mismatch")
        if "gpt-5.6-sol" in canonical(packet).decode():raise ValueError("organizer generator identity exposed")
        examples.setdefault(key,{"sample_id":r["sample_id"],"packet":str(packets/"packets"/(assignment["packet_id"]+".html")),
            "reference":str(output/"organizer-private/references"/(r["sample_id"]+".json"))})
    retained(output/"examples.json",examples)
    checks={"version":"spq02b-answer-export/1.0.3","qa_records":40,"families":dict(Counter(r["question_type"] for r in after)),
        "annotated_targets":sum(len(r["private"]["answer_annotation"]["targets"]) for r in after),
        "supporting_multi_target_alternatives":8,"prepared_public_requests":n,"examples":len(examples),
        "blank_rating_imports":blanks,"source_recovery":"exact after removing private.answer_annotation",
        "public_inputs":"exact accepted 1.1.1 projection; no gold/explanation/trace fields",
        "verification":"deterministic target readout and binding checks, saved admission; exact replay only eight selected groups",
        "human_quality_or_agreement":"pending_no_independent_judgments","new_simulations":0,"new_model_calls":0,"new_spend_usd":0}
    retained(output/"verification/checks.json",checks)
    if (output/"manifest.json").exists():verify_manifest(output)
    else:manifest(output,{"purpose":"SPQ02b_40_development_answer_annotations",**identity,"checks":checks})
    print(canonical(checks).decode(),end="");return checks

def main():
    parser=argparse.ArgumentParser(description=__doc__)
    for name in ("records","counterfactuals","plan","runs","arm-evidence","output"):
        parser.add_argument("--"+name,type=Path,required=True)
    a=parser.parse_args();export(a.records,a.counterfactuals,a.plan,a.runs,a.arm_evidence,a.output)

if __name__ == "__main__":main()
