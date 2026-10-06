"""Bounded checks on saved SPQ01 artifacts; resume verification forbids provider calls."""
from collections import Counter
from hashlib import sha256
from pathlib import Path
from .annotation import project, validate_generated
from .audit import preview
from .dataset import load, restore, validate
from .direct import build_direct
from .io import ROOT, canonical, digest, external, manifest, parse, read, write
from .job import run, ledger

def verify(selection_root, job_root, development_root, output):
    originals=list(load(selection_root/"predictive-records.jsonl"))
    saved=list(load(development_root/"qa-records.jsonl"))
    selection=read(selection_root/"selection.json")
    expected_groups={r["private"]["metadata"]["split_group_id"] for r in originals}
    durable=set(read(ROOT/"configs/simphysqa/development_exclusions.json")["excluded_groups"])
    if len(originals)!=16 or len(saved)!=32 or not expected_groups<=durable:
        raise ValueError("development_count_or_durable_exclusion_mismatch")
    if len(expected_groups)!=16:
        raise ValueError("related_development_groups")
    by_id={r["sample_id"]:r for r in saved}
    sources_checked=0
    for original in originals:
        src=original["source"]
        path=Path(src["path"])
        if sha256(path.read_bytes()).hexdigest()!=src["file_sha256"]:
            raise ValueError("source_file_changed")
        with path.open(encoding="utf-8") as stream:
            actual=next(parse(line) for number,line in enumerate(stream,1) if number==src["line"])
        if actual!=restore(original) or digest(actual)!=src["record_sha256"]:
            raise ValueError("source_id_reference_provenance_changed")
        predictive=by_id[original["sample_id"]]
        if restore(predictive)!=actual or predictive["private"]["reference"]!=actual["reference"]:
            raise ValueError("predictive_reference_changed")
        direct=by_id[build_direct(predictive)["sample_id"]]
        validate(direct)
        if restore(direct)!=actual:
            raise ValueError("direct_lineage_changed")
        if project(predictive)!=project(direct):
            raise ValueError("paired_public_physical_views_differ")
        # The request projection reads only public fields even with adversarial private outcomes.
        mutated={"public":predictive["public"],"private":{"reference":"PRIVATE_OUTCOME_SENTINEL"}}
        if project(mutated)!=project(predictive):
            raise ValueError("private_outcome_leakage")
        for record in (predictive,direct):
            annotations=record["public"]["annotations"]
            if annotations["trajectory"]["status"]=="generated_unreviewed":
                validate_generated(record,{"summary":{k:v for k,v in annotations["trajectory"].items() if k!="status"},
                    "timestamps":[{k:v for k,v in a.items() if k!="status"} for a in annotations["timestamps"]]})
        sources_checked+=1
    publics=read(development_root/"public-qa.json")
    if len(publics)!=32 or any(set(p)!={"schema_version","sample_id","question_type","annotation_version","input","annotations"} for p in publics):
        raise ValueError("public_export_allowlist_mismatch")
    for p in publics:
        r=by_id[p["sample_id"]]
        if p["input"]!=r["public"]["input"] or p["annotations"]!=r["public"]["annotations"]:
            raise ValueError("final_export_not_same_validated_view")
        if any(s["timestamp"]>p["input"]["observation_cutoff"] for s in p["input"]["states"]):
            raise ValueError("future_state_in_public")
    blanks={}
    for reviewer in ("R1","R2","R3"):
        imported=read(development_root/(reviewer+"-blank-import.json"))
        if (imported["blank"],imported["collected"],imported["ratings"])!=(32,0,[]):
            raise ValueError("blank_ratings_mislabeled")
        blanks[reviewer]=32
    items={p.name:sha256(p.read_bytes()).hexdigest() for p in (job_root/"items").glob("*.json")}
    before_attempts=len(ledger(job_root))
    def forbidden(body):
        raise AssertionError("resume_verification_forbids_provider_calls")
    config=read(job_root/"job.json")["identity"]["config"]
    accounting=run(originals,config,job_root,transport=forbidden)
    after_items={p.name:sha256(p.read_bytes()).hexdigest() for p in (job_root/"items").glob("*.json")}
    if after_items!=items or len(ledger(job_root))!=before_attempts:
        raise ValueError("completed_work_changed_during_resume")
    corrected=ledger(job_root)
    revisions=[]
    for attempt in corrected:
        raw=read(job_root/"responses"/(str(attempt["attempt_number"]).zfill(3)+".json"))
        old=raw["accounting"]["recorded_cost_usd"]
        if old!=attempt["recorded_cost_usd"]:
            revisions.append({"attempt":attempt["attempt_number"],"old_estimate_usd":old,
                "corrected_estimate_usd":attempt["recorded_cost_usd"],"usage":attempt["usage"]})
    fresh=preview(originals,20261004)
    if fresh["eligible_groups"]!=0:
        raise ValueError("development_groups_eligible_for_fresh_formal")
    output=external(output);output.mkdir(parents=True,exist_ok=False)
    write(output/"accounting-reconciliation.json",{"version":"SPQ01-accounting-correction/1.0.1","source_job":str(job_root.resolve()),
        "originals_preserved":True,"method":"ordinary=input-cached-cache_write; cache reads .40, ordinary 4, cache writes 5, output 20 USD/M",
        "source":"https://developers.openai.com/api/docs/guides/prompt-caching","revisions":revisions,"final":accounting})
    examples={}
    packets=read(development_root/"audit-development/manifest.json")["assignments"]
    for original in originals:
        domain=original["public"]["input"]["domain"]
        if domain not in examples:
            packet=next(p for p in packets if p["sample_id"]==original["sample_id"])
            examples[domain]={"sample_id":original["sample_id"],"packet_id":packet["packet_id"],
                "html":str((development_root/"audit-development/packets"/(packet["packet_id"]+".html")).resolve()),
                "json":str((development_root/"audit-development/packets"/(packet["packet_id"]+".json")).resolve()),
                "annotation_status":by_id[original["sample_id"]]["public"]["annotations"]["trajectory"]["status"]}
    write(output/"examples.json",examples)
    result={"version":"SPQ01-saved-artifact-verification/1.0.0","sources_checked":sources_checked,"qa_records":32,
        "counts":dict(Counter(r["public"]["input"]["domain"]+"/"+r["question_type"] for r in saved)),
        "predictive_references_exact":16,"direct_answers_source_verified":16,
        "final_public_views_revalidated":32,"completed_item_hashes_preserved":True,"resume_new_requests":0,
        "blank_forms":blanks,"human_ratings":0,"fresh_preview_eligible_development_groups":0,
        "excluded_group_count":len(durable),"formal_sample_exported":False,"accounting":accounting,
        "automatic_validation_not_human_assessment":True}
    write(output/"verification.json",result)
    write(output/"fresh-preview.json",fresh)
    manifest(output,{"purpose":"saved_SPQ01_artifact_and_no_call_resume_verification","result":result})
    if not (job_root/"manifest.json").exists():
        manifest(job_root,{"purpose":"SPQ01_bounded_live_annotations_with_original_and_corrected_accounting",
            "final_accounting":accounting,"quality_status":"automatically_validated_human_unreviewed",
            "original_accounting_correction":str((output/"accounting-reconciliation.json").resolve())})
    return result
