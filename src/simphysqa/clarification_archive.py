"""Append SPQ04 mappings to the accepted archive without rewriting historical lineage."""
import argparse
from copy import deepcopy
from hashlib import sha256
from pathlib import Path
from .io import ROOT, canonical, digest, parse, read, external, manifest
from .spq01a import retained, verify_manifest
from .answer_export import retained_bytes
from .dataset import load
from .annotation import project
from .associations import strip_associations
from .event_language import measurement_base

VERSION="simphysqa-prompt-archive/1.0.7"
PROCEDURES={
    "clarification-qa/1.0.0":("src/simphysqa/clarification.py","Deterministic query-gap selection, disjoint acceptance-region witnesses, complete initial-surface projection, author reply, resolved readout and claim/trace bindings; saved evidence only. No annotation-model prompt."),
    "clarification-export/1.0.0":("src/simphysqa/clarification_export.py","Eight frozen development groups, explicit candidate failures, private witnesses and two-stage public views, packets/blank forms, 72 initial requests and 72 conditional templates. No model execution."),
    "clarification-evaluation/1.0.0":("src/simphysqa/clarification_evaluation.py","Actual prepared answering instructions, dedicated stage contracts, equivalent wording via declared-slot routing, typed post-reply scorer. Text adequacy/premature prose answers require human review. No executed interaction."),
    "clarification-partial-schema/1.0.0":("src/simphysqa/clarification.schema.json","Dedicated partial query omits an unknown condition/entity/time instead of inventing defaults or filling the complete schema. No model prompt."),
    "clarification-rubric/1.0.0":("configs/simphysqa/clarification_rubric.json","Gap recognition, relevance/sufficiency, premature answering, resolved answer and explanation quality are separate. Independent human judgments uncollected."),
    "clarification-audit/1.0.0":("src/simphysqa/audit.py","Private two-stage/witness/evidence rendering, organizer identity separate, three blank independent forms. Deterministic, not ratings."),
    "clarification-typed-scorer/1.0.0":("src/simphysqa/scoring.py","Unchanged distance() defines Boolean/scalar/vector/quaternion acceptance. Initial clarification records cannot be numerically graded without resolution.")}


def nodes(value, prefix=""):
    if isinstance(value,list):
        for i,v in enumerate(value):yield from nodes(v,prefix+"/"+str(i))
    elif isinstance(value,dict):
        if value.get("sample_id"):
            yield prefix,value
        for k,v in value.items():
            if k=="content" and isinstance(v,str):
                try:nested=parse(v.split("\n",1)[1])
                except (ValueError,IndexError):continue
                yield from nodes(nested,prefix+"/content:public_json")
            elif isinstance(v,(dict,list)):yield from nodes(v,prefix+"/"+k)


def build(previous, clarifications, output):
    output=external(output);verify_manifest(previous);verify_manifest(clarifications)
    for parent in (previous,clarifications):
        if output==parent or parent in output.parents or output in parent.parents:raise ValueError("archive must be separate")
    previous_index=read(previous/"file-generation-index.json")
    if previous_index["version"]!="simphysqa-prompt-archive/1.0.6":raise ValueError("require accepted archive1.0.6")
    for p in previous.rglob("*"):
        if p.is_file() and p.name not in ("manifest.json","README.md","catalogue.md","file-generation-index.json","coverage.json"):
            retained_bytes(output/p.relative_to(previous),p.read_bytes())
    index=deepcopy(previous_index);index["version"]=VERSION
    index["accepted_parent_archive_sha256"]=digest(read(previous/"manifest.json"))
    index["root_aliases"]["SPQ04-clarification"]=clarifications.name
    index["SPQ04_disclosure"]="Incomplete and resolved query views contain no witness answers; recorded author reply supplies missing query information only. Prepared two-stage conversations are unexecuted. All generated new gold/trace/witness fields are deterministic and private."
    code=[]
    for pid,(rel,rule) in PROCEDURES.items():
        raw=(ROOT/rel).read_text(encoding="utf-8").encode()
        filename="procedures/"+pid.replace("/","-")+(".json" if rel.endswith(".json") else ".py")
        retained_bytes(output/filename,raw)
        index["procedures"].append({"procedure_id":pid,"kind":"deterministic_no_model_prompt","source_path":rel,"source_commit":"SPQ04 implementation pinned by SHA256; final commit in completion receipt","implementation_sha256":sha256(raw).hexdigest(),"source_file":filename,"rules":rule})
        code.append((pid,filename,rule,raw.decode()))
    records=list(load(clarifications/"organizer-private/qa-records.jsonl"));new={r["sample_id"]:r for r in records}
    old_by_sid={}
    for key,m in previous_index["mapping_definitions"].items():
        if m.get("sample_id") and m.get("executed_request_id"):old_by_sid.setdefault(m["sample_id"],(key,m))
    group_request={m["trajectory_id"]:m["executed_request_id"] for m in previous_index["mapping_definitions"].values() if m.get("trajectory_id") and m.get("executed_request_id")}
    req={r["request_id"]:r for r in index["requests"]}
    newfiles=0;newmappings=0
    for p in sorted(clarifications.rglob("*")):
        if not p.is_file() or p.suffix not in (".json",".jsonl",".html") or p.name=="manifest.json":continue
        rel=p.relative_to(clarifications).as_posix()
        if rel.startswith("verification/") or rel in ("preflight.json","examples.json","item-index.json"):continue
        raw=p.read_bytes()
        parsed=parse(p.with_suffix(".json").read_text(encoding="utf-8")) if p.suffix==".html" and p.with_suffix(".json").exists() else [parse(l) for l in raw.decode().splitlines() if l] if p.suffix==".jsonl" else parse(raw.decode()) if p.suffix==".json" else None
        if parsed is None:continue  # inspection HTML copies indexed packet references, not new annotations.
        mappings=[]
        for ptr,node in nodes(parsed):
            sid=node["sample_id"]
            if sid not in new:
                if sid in old_by_sid:
                    key,m=old_by_sid[sid];mappings.append({"record_pointer":ptr,"mapping_id":key})
                continue
            r=new[sid];rid=group_request[r["trajectory_id"]];request=req[rid]
            inp=node.get("input",node.get("public",{}).get("input",node.get("structured_inputs",{})))
            language=node.get("annotations",node.get("public",{}).get("annotations",node.get("language_annotations")))
            fg=[];fields=[];pids=["clarification-qa/1.0.0"]
            parent="SPQ02b-enriched/organizer-private/items/"+r["private"]["clarification_evidence"]["parent_sample_id"]+".json"
            if language is not None:
                parent_language=r["private"]["clarification_evidence"]["parent_record"]["public"]["annotations"]
                if canonical(language)!=canonical(parent_language):raise ValueError("reused language differs")
                if inp:
                    projection=project({"public":{"input":strip_associations(inp)}})
                    if canonical(projection)!=canonical(parse(read(previous/request["payload_file"])["input"])):raise ValueError("annotation projection changed")
                for f in ("trajectory.text","timestamps[*].text"):
                    fields.append(f);fg.append({"field":f,"method":"reuse_copy_of_executed_model_measurement_annotation","procedure_id":"public-language/1.0.0","parent_artifact":"SPQ01-annotation-job/items/"+request["sample_id"]+".json","complete_request":request["payload_file"]})
                for f,pid in (("event_context/claims","event-language/2.0.0"),("states[*].linked_events/known_events[*].linked_states/between_state_associations","associations/1.1.1"),("event_description and copies","event-description/1.0.1")):
                    fields.append(f);pids.append(pid);fg.append({"field":f,"method":"reuse_copy_of_deterministic_public_annotation","procedure_id":pid,"parent_artifact":parent})
            generated=[]
            if inp:
                generated += [("input.question/query","clarification-qa/1.0.0"),("input.interaction.response_schema","clarification-evaluation/1.0.0")]
                if "recorded_reply" in inp:generated.append(("input.recorded_reply/resolved_question/answer_spec","clarification-qa/1.0.0"))
            private=node.get("private",{})
            if "reference" in private or "reference" in node.get("qa",{}):generated.append(("reference.explanation/claims/solution_trace/verification","clarification-qa/1.0.0"))
            if "clarification_evidence" in private:generated.append(("private.clarification_evidence/clarification_annotation","clarification-qa/1.0.0"))
            if "selection" in node:generated.append(("selection","clarification-qa/1.0.0"))
            if "witnesses" in node:generated.append(("witnesses","clarification-qa/1.0.0"))
            if "messages" in node:generated.append(("messages[*].content/prepared public request","clarification-evaluation/1.0.0"))
            if "conditional_continuation" in node:generated.append(("conditional_continuation/template","clarification-evaluation/1.0.0"))
            for f,pid in generated:
                fields.append(f);pids.append(pid);fg.append({"field":f,"method":"deterministic_no_model_prompt","procedure_id":pid,"parent_artifact":parent})
            if not fields:continue
            detail={"sample_id":sid,"trajectory_id":r["trajectory_id"],"annotated_fields":fields,"field_generation":fg,"origin":"deterministic_clarification_with_reused_observed_language",
                "procedure_ids":list(dict.fromkeys(pids)),"parent_artifact":parent,"executed_request_id":rid if language is not None else None,
                "complete_instantiated_request":request["payload_file"] if language is not None else None,
                "input_sha256":digest(inp) if inp else None,"annotation_output_sha256":digest(language) if language is not None else None,
                "new_annotation_model_request":False,"prepared_interaction_executed":False}
            key=digest(detail);index["mapping_definitions"].setdefault(key,detail);mappings.append({"record_pointer":ptr,"mapping_id":key});newmappings+=1
        # Scalar catalogue/schema/rubric/selection files still resolve to their producer.
        entry={"artifact":"SPQ04-clarification/"+rel,"file_sha256":sha256(raw).hexdigest(),"mappings":mappings,
            "procedure_ids":["clarification-export/1.0.0"] if not mappings else [],
            "copy_kind":"HTML rendering of sibling JSON" if p.suffix==".html" else "versioned deterministic/reused annotation artifact",
            "parent_file":"SPQ04-clarification/"+p.with_suffix(".json").relative_to(clarifications).as_posix() if p.suffix==".html" else None,
            "redaction":"Identities, field pointers, hashes and provenance only; full private witnesses/answers/traces/receipts remain external."}
        index["files"].append(entry);newfiles+=1
    retained(output/"file-generation-index.json",index)
    note=("\n## SPQ04 clarification QA — deterministic procedures\n\nEight new engineering-development items use five condition gaps, one block-entity gap and two readout-time gaps. Frozen groups remain excluded from fresh formal sampling. Both witnesses erase to the complete same initial public input, including annotations, associations, identifiers and response schema. Numerical witness regions are disjoint under the actual typed scorer; equal/sub-tolerance omission contrasts were rejected, not relabeled. Tether .4 s readouts were additionally checked against already saved fine-step results using existing admission thresholds. No new simulation or provider request occurred.\n\nInitial public queries use a dedicated partial-input contract with the missing slot absent. Conditional templates never insert authored reference clarification questions as assistant responses. The recorded reply contains missing query information only; gold answer/explanation/trace/private verification remain private. Wording equivalence is assessed by humans; declared-slot routing is deterministic and does not prove prose adequacy. All conversations are prepared, never executed. Historical executed/reused/procedure distinctions and unrecoverable early source material remain unchanged.\n")
    for pid,filename,rule,source in code:
        note+=f'\n### {pid}\n\n{rule}\n\n[Exact pinned templates/projection]({filename})\n\n<details><summary>Complete deterministic source</summary>\n\n```{ "json" if filename.endswith("json") else "python"}\n{source}\n```\n</details>\n'
    retained_bytes(output/"catalogue.md",(previous/"catalogue.md").read_bytes()+note.encode())
    retained_bytes(output/"README.md",("# Annotation prompt/procedure archive — SPQ04 /1.0.7\n\nInspect [the consolidated catalogue](catalogue.md) and [per-file generation index](file-generation-index.json). [Recovered executed request and output mappings](provenance-example.md) remains unchanged. SPQ04 deterministic query projection/witness qualification, reply routing, references/traces, schemas/rubric and export procedures are appended. No annotation requests or answering conversations executed. Reused observation language resolves directly to the original complete executed payload.\n\nFull gold/witness/outcome/receipt information is private and external. Historical archive1.0.6 and all prior artifacts are preserved. Authoring instruction: [SPQ04](../../prompts/SPQ04_clarification_qa.md), distinct from annotation-model prompts.\n").encode())
    counts={"version":VERSION,"indexed_files":len(index["files"]),"new_indexed_files":newfiles,"new_record_mappings":newmappings,"unique_mapping_definitions":len(index["mapping_definitions"]),"exact_recovered_requests":16,"unavailable_executed_requests":0,"reconstructed_requests":0,"new_model_calls":0,"gold_fields_in_paper_archive":False,"historical_mappings_preserved":True}
    retained(output/"coverage.json",counts)
    if (output/"manifest.json").exists():verify_manifest(output)
    else:manifest(output,{"purpose":"paper_facing_prompt_procedure_archive","version":VERSION,"accepted_parent_sha256":index["accepted_parent_archive_sha256"],"builder_sha256":sha256(Path(__file__).read_text(encoding="utf-8").encode()).hexdigest(),"counts":counts})
    print(canonical(counts).decode(),end="");return counts


def main():
    p=argparse.ArgumentParser(description=__doc__)
    for name in ("previous","clarifications","output"):p.add_argument("--"+name,type=Path,required=True)
    a=p.parse_args();build(a.previous,a.clarifications,a.output)


if __name__=="__main__":main()
