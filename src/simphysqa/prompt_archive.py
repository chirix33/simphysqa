"""Offline paper-facing catalogue of executed payloads, reuse and deterministic code."""
import argparse
from collections import Counter
from copy import deepcopy
from hashlib import sha256
from pathlib import Path
import subprocess
from .io import ROOT, canonical, digest, external, manifest, parse, read
from .annotation import project
from .event_language import measurement_base
from .associations import strip_associations
from .spq01a import retained, verify_manifest
from .answer_export import retained_bytes

ARCHIVE = "simphysqa-prompt-archive/1.0.6"
HISTORY = {
    "SPQ01": "6d420b779e0204868fec4c45e26bb1cdcd2b98c7",
    "SPQ01a-events": "328ef3f",
    "SPQ01a-associations": "433c64186555fdc99f17261c069a2dd4b334a11e",
    "SPQ01a-descriptions": "e379013b7e80fe28172682cd39e42f4066fde841",
    "SPQ02": "1ae35749421283e63344504dc6a5d24ce18f32e7",
    "SPQ02b": "1796b8d9cb475b8579330854b298021a200b4c08"
}
PROCEDURES = {
    "source-readout-placeholder": ("SPQ02", "src/phi_jepa/simulation/records.py", "Original simulator question/label templates and descriptive placeholders, not model prompts; unavailable solution traces are historical fields, not completed reasoning."),
    "public-language/1.0.0": ("SPQ01", "src/simphysqa/annotation.py", "Executed Responses instructions plus exact public focal projection; one summary and all observed timestamp descriptions per request."),
    "annotation-job/1.0.0": ("SPQ01", "src/simphysqa/job.py", "Durable reservations/attempts, controlled repair feedback and reuse. Sixteen actual initial attempts, zero repairs/failures."),
    "direct-readout/1.0.0": ("SPQ01", "src/simphysqa/direct.py", "Choose the final observed focal channel; derive exact target/readout and direct question. No model prompt."),
    "event-matching/1.0.0": ("SPQ01a-events", "src/simphysqa/events.py", "Public-only decimal interval/point matching, whole-state targets/controller phases; no nearest-state active assignment."),
    "event-language/2.0.0": ("SPQ01a-events", "src/simphysqa/event_language.py", "Retain model measurement prose; deterministic public controller/schedule claims and state/gap links. No model prompt."),
    "associations/1.0.1": ("SPQ01a-associations", "src/simphysqa/associations.py", "Copy canonical links into compact forward/reverse indexes; gap endpoints remain separate. No model prompt."),
    "associations/1.1.1": ("SPQ01a-descriptions", "src/simphysqa/associations.py", "Accepted 1.1.1 public projection, exact stripping/source recovery; copies shared canonical event descriptions. No model prompt."),
    "event-description/1.0.1": ("SPQ01a-descriptions", "src/simphysqa/event_descriptions.py", "Exact public definition/recognized controller templates; action/target/limit/phases, half-even six-significant decimal display, unresolved semantics explicit. No model prompt."),
    "counterfactual/1.0.0": ("SPQ02", "src/simphysqa/counterfactual.py", "Matched omission question and single verified alternative target; new stable ID, original public prefix, independent replay/admission evidence. No model prompt."),
    "answer-annotation/1.0.3": ("current", "src/simphysqa/answer_annotations.py", "Concise shared physical conditions once; target-specific public direct readout or saved numerical readout/rule; sign-invariant quaternion rotation angle, never componentwise physical change; detailed method/settings/verification stay in private solution traces; paired omission comparisons; claim/step pointers and hashes. Eight-significant prose, exact typed source values. Private overlay only. No model prompt."),
    "answer-export/1.0.3": ("current", "src/simphysqa/answer_export.py", "40 private enriched QA, eight multi-target alternatives, audit reference rendering and 360 unchanged public requests. No model prompt."),
    "explanation-qa/1.0.0": ("current", "src/simphysqa/explanation.py", "New matched-intervention explanation questions and supported claims; selected factual/omission outcomes intentionally supplied separately; fixed prefix/target/group; saved paired evidence, no new simulations/model prompt."),
    "explanation-export/1.0.0": ("current", "src/simphysqa/explanation_export.py", "Eight frozen paired explanation records, public disclosures, packets, blank forms and 72 requests; links to accepted 40 items. Deterministic, no model prompt."),
    "explanation-evaluation/1.0.0": ("current", "src/simphysqa/explanation_evaluation.py", "Compatible explanation JSON response contract for nine conditions; factual structured checks only, no text/keyword/MSE explanation-quality score. Prepared answering prompts, never executed."),
    "explanation-rubric/1.0.0": ("current", "configs/simphysqa/explanation_rubric.json", "Supported-claim human rubric, acceptable paraphrases and contradictions; human ratings uncollected. Not an annotation-model prompt."),
    "prepared-explanation-request/1.0.0": ("current", "src/simphysqa/evaluation.py", "Actual dispatch to the explanation-specific prompt/JSON response contract for all nine tool-free answering conditions; requests prepared only, not annotation requests or model execution."),
    "prepared-answering-request": ("SPQ02", "src/simphysqa/evaluation.py", "Tool-free public input plus retained public annotations under nine configured conditions; prepared, never executed. Not an annotation-generation request.")
}

def annotated_nodes(value, prefix=""):
    """Find annotation-bearing records, including copies inside prepared request strings."""
    if isinstance(value, list):
        for i,v in enumerate(value):yield from annotated_nodes(v,prefix+"/"+str(i))
    elif isinstance(value, dict):
        sample=value.get("sample_id")
        if sample and ("annotations" in value or "public" in value or "language_annotations" in value or "reference" in value):
            yield prefix, value
            # A wrapper embeds legacy source records; inventory these separately too.
            if "public" in value:
                yield from annotated_nodes(value.get("private",{}).get("source_record",{}),prefix+"/private/source_record")
                yield from annotated_nodes(value.get("private",{}).get("counterfactual_evidence",{}).get("alternative_record",{}),prefix+"/private/counterfactual_evidence/alternative_record")
                yield from annotated_nodes(value.get("private",{}).get("explanation_evidence",{}).get("parent_record",{}),prefix+"/private/explanation_evidence/parent_record")
            return
        if "messages" in value and sample:
            for i,m in enumerate(value["messages"]):
                content=m.get("content","")
                try: nested=parse(content.split("\n",1)[1])
                except (ValueError,IndexError):continue
                yield from annotated_nodes(nested,prefix+f"/messages/{i}/content:public_json")
            return
        for k,v in value.items():yield from annotated_nodes(v,prefix+"/"+k)

def build(spq01, spq01a, spq02, enriched, output, explanations=None):
    output=external(output)
    # Source/parent identities resolve all copied summaries/timestamps back to their actual request.
    mapping={};group_request={};families={};explanation_parents={}
    for line in (spq01a/"event-language-2.0.0/qa-records.jsonl").read_text(encoding="utf-8").splitlines():
        r=parse(line);mapping[r["sample_id"]]=r["trajectory_id"];families[r["sample_id"]]=r["question_type"]
        if r["question_type"]=="predictive":group_request[r["trajectory_id"]]=r["sample_id"]
    for line in (enriched/"organizer-private/qa-records.jsonl").read_text(encoding="utf-8").splitlines():
        r=parse(line);mapping[r["sample_id"]]=r["trajectory_id"];families[r["sample_id"]]=r["question_type"]
        if r["question_type"]=="counterfactual":
            alt=r["private"]["counterfactual_evidence"]["alternative_record"]
            mapping[alt["sample_id"]]=r["trajectory_id"];families[alt["sample_id"]]="counterfactual"
    if explanations is not None:
        for line in (explanations/"organizer-private/qa-records.jsonl").read_text(encoding="utf-8").splitlines():
            r=parse(line);mapping[r["sample_id"]]=r["trajectory_id"];families[r["sample_id"]]="explanation";explanation_parents[r["sample_id"]]=r["private"]["explanation_evidence"]["parent_sample_id"]
    job=spq01/"annotation-job";requests=[];notes=[]
    for file in sorted((job/"attempts").glob("*.json")):
        attempt=read(file);number=attempt["attempt_number"];path=job/"attempt-requests"/(f"{number:03}.json")
        response=read(job/"responses"/(f"{number:03}.json"))
        item_path=job/"items"/(attempt["sample_id"]+".json")
        body=read(path)
        if digest(body)!=attempt["request_sha256"]:raise ValueError("executed request checksum differs")
        if response["sample_id"]!=attempt["sample_id"] or response["failure"] is not None:raise ValueError("unexpected historical failed request; explicit accounting required")
        # Wire payload contains public projection, no Authorization header or credential reference.
        projection=parse(body["input"])
        if set(projection)!= {"domain","focal_entity","focal_quantity","observation_cutoff","observed","facts"}:
            raise ValueError("request projection cannot be safely classified public")
        if any(not k.startswith(("/states/","/controller","/known_events","/coordinate_convention")) for k in projection["facts"]):
            raise ValueError("historical request contains nonpublic evidence")
        ref=f"requests/attempt-{number:03}.json"
        retained(output/ref,body)
        item=read(item_path)
        entry={"request_id":f"SPQ01-attempt-{number:03}","sample_id":attempt["sample_id"],"attempt_number":number,
            "prompt_id":"public-language/1.0.0","recovery":"exact_saved_executed_payload", "payload_file":ref,
            "request_sha256":digest(body),"saved_payload_file_sha256":sha256(path.read_bytes()).hexdigest(),
            "input_sha256":sha256(body["input"].encode()).hexdigest(),"output_file_sha256":sha256(item_path.read_bytes()).hexdigest(),
            "output_annotation_sha256":digest(item["annotations"]),"returned_model":response["raw_response"]["model"],
            "repair":attempt["repair"],"failure":response["failure"],"retry_count":item["provenance"]["retries"],
            "produced_fields":["annotations.trajectory", "annotations.timestamps[*]"],"timestamp_outputs":len(item["annotations"]["timestamps"]),
            "message_representation":"Actual Responses wire instructions then input string; no role-tagged system/developer messages were supplied. Do not invent them.",
            "settings":{k:body[k] for k in ("model","reasoning","max_output_tokens","service_tier","store","tools")},
            "timeout_seconds":item["provenance"]["generation_settings"]["timeout_seconds"],"temperature":"omitted","seed":"omitted",
            "redaction":"HTTP Authorization/header and credential file paths are excluded; exact JSON body has no secret/private outcome and is unredacted."}
        requests.append(entry)
    if len(requests)!=16:raise ValueError("historical executed request count changed")
    request_by_sample={r["sample_id"]:r for r in requests}
    originals={sid:read(job/"items"/(sid+".json"))["annotations"] for sid in request_by_sample}
    def annotation_content(value):
        if isinstance(value,dict):return {k:annotation_content(v) for k,v in value.items() if k!="status"}
        if isinstance(value,list):return [annotation_content(v) for v in value]
        return value
    procedures=[]
    for id,(stage,rel,rule) in PROCEDURES.items():
        if stage=="current":raw=(ROOT/rel).read_text(encoding="utf-8").encode();commit="working implementation pinned by SHA256; final commit in delivery receipt"
        else:
            commit=subprocess.check_output(["git","rev-parse",HISTORY[stage]],cwd=ROOT).decode().strip()
            raw=subprocess.check_output(["git","show",commit+":"+rel],cwd=ROOT)
        name="procedures/"+id.replace("/","-")+(".json" if rel.endswith(".json") else ".py")
        retained_bytes(output/name,raw)
        procedures.append({"procedure_id":id,"kind":"executed_annotation_model_prompt" if id=="public-language/1.0.0" else "deterministic_no_model_prompt",
            "source_path":rel,"source_commit":commit,"implementation_sha256":sha256(raw).hexdigest(),"source_file":name,"rules":rule})
    roots={"SPQ01-annotation-job":job,"SPQ01-development":spq01/"development",
        "SPQ01-dry-run":spq01/"dry-run","SPQ01-dry-run-final":spq01/"dry-run-final",
        "SPQ01-source-comparison":spq01/"source-comparison","SPQ02-counterfactual":spq02/"export-1.0.0",
        "SPQ02-alternative-records":spq02/"runs/alternative-records","SPQ02b-enriched":enriched}
    if explanations is not None:
        roots["SPQ03-explanation"]=explanations
    preliminary=enriched.parent/"answers-1.0.0"
    if preliminary.exists() and preliminary != enriched:
        roots["SPQ02b-preliminary-1.0.0"]=preliminary
        payload=read(enriched.parent.parent/"spq02b-payload.json")
        for id,rel in (("answer-annotation/1.0.0","src/simphysqa/answer_annotations.py"),("answer-export/1.0.0","src/simphysqa/answer_export.py")):
            raw=payload[rel].encode();name="procedures/"+id.replace("/","-")+".py"
            retained_bytes(output/name,raw)
            procedures.append({"procedure_id":id,"kind":"deterministic_no_model_prompt","source_path":rel,
                "source_commit":"uncommitted preliminary 1.0.0, exact saved installer payload","implementation_sha256":sha256(raw).hexdigest(),"source_file":name,
                "rules":"Preserved first offline export; superseded by final 1.0.1. Exact source recovered from saved installer payload, not reconstructed."})
    for path in sorted(spq01a.iterdir()):
        if path.is_dir():roots["SPQ01a-"+path.name]=path
    # An exact saved installer payload recovers the preliminary 1.0.0 source.
    old_payload=read(enriched.parent.parent/"association_payload.json")
    old_code=old_payload["src/simphysqa/associations.py"].encode()
    old_manifest=read(spq01a/"associations-1.0.0/manifest.json")
    if sha256(old_code).hexdigest()!=old_manifest["association_implementation_sha256"]:
        raise ValueError("preliminary source payload does not match executed hash")
    retained_bytes(output/"procedures/associations-1.0.0.py",old_code)
    procedures.append({"procedure_id":"associations/1.0.0","kind":"deterministic_no_model_prompt",
        "source_path":"src/simphysqa/associations.py","source_commit":"uncommitted preliminary output; exact saved installer payload",
        "implementation_sha256":sha256(old_code).hexdigest(),"source_file":"procedures/associations-1.0.0.py",
        "rules":"Recovered original executed source from saved installer payload; exact SHA256 matches preliminary export manifest. No model prompt."})
    old_manifest=read(spq01a/"associations-1.1.0/manifest.json")
    for id,key in (("associations/1.1.0","association_implementation_sha256"),("event-description/1.0.0","event_description_renderer_sha256")):
        procedures.append({"procedure_id":id,"kind":"deterministic_no_model_prompt","source_path":"unavailable original preliminary source",
            "source_commit":"uncommitted preliminary revision","implementation_sha256":old_manifest[key],"source_file":None,
            "rules":"Exact original source text unrecoverable from saved payloads/historical commits. Output manifest pins executed hash; accepted successor templates are archived separately. No reconstruction is presented as executed code."})
    # Preserve the prior internal 1.0.1 artifacts and their actual archived source.
    prior=enriched.parent/"answers-1.0.1"
    if prior.exists() and prior!=enriched:
        roots["SPQ02b-prior-1.0.1"]=prior
        for id in ("answer-annotation/1.0.1","answer-export/1.0.1"):
            name="procedures/"+id.replace("/","-")+".py"
            original=enriched.parent/"prompt-archive-1.0.2"/name
            raw=original.read_bytes();retained_bytes(output/name,raw)
            procedures.append({"procedure_id":id,"kind":"deterministic_no_model_prompt","source_path":name,
                "source_commit":"prior internal export; exact preserved procedure snapshot","implementation_sha256":sha256(raw).hexdigest(),"source_file":name,
                "rules":"Superseded internal 1.0.1 output and source snapshot retained; final 1.0.2 normalizes code fingerprint newlines to repository LF convention. No model prompt."})
    # Retain accepted 1.0.2 files and recover their exact committed procedures.
    prior=enriched.parent/"answers-1.0.2"
    if prior.exists() and prior!=enriched:
        roots["SPQ02b-prior-1.0.2"]=prior
        for id,rel in (("answer-annotation/1.0.2","src/simphysqa/answer_annotations.py"),("answer-export/1.0.2","src/simphysqa/answer_export.py")):
            commit=HISTORY["SPQ02b"]
            raw=subprocess.check_output(["git","show",commit+":"+rel],cwd=ROOT)
            name="procedures/"+id.replace("/","-")+".py"
            retained_bytes(output/name,raw)
            procedures.append({"procedure_id":id,"kind":"deterministic_no_model_prompt","source_path":rel,
                "source_commit":commit,"implementation_sha256":sha256(raw).hexdigest(),"source_file":name,
                "rules":"Accepted prior answer export 1.0.2; exact committed code recovered. Preserved prior artifacts, no new model request."})
    def gold_id(alias):
        return "answer-annotation/1.0.0" if alias=="SPQ02b-preliminary-1.0.0" else "answer-annotation/1.0.1" if alias=="SPQ02b-prior-1.0.1" else "answer-annotation/1.0.2" if alias=="SPQ02b-prior-1.0.2" else "answer-annotation/1.0.3"
    entries=[];all_files=[]
    for alias,folder in roots.items():
        for path in sorted(folder.rglob("*")):
            if not path.is_file() or path.suffix not in (".json",".jsonl",".html"):continue
            rel=path.relative_to(folder).as_posix();raw=path.read_bytes()
            if path.suffix==".html":
                sibling=path.with_suffix(".json")
                if not sibling.exists():continue
                value=read(sibling)
            elif path.suffix==".jsonl":value=[parse(l) for l in raw.decode("utf-8-sig").splitlines() if l.strip()]
            else:value=read(path)
            if alias == "SPQ01-annotation-job" and rel.startswith("responses/"):
                response = value
                content = [p["text"] for m in response["raw_response"]["output"] if m.get("type")=="message" for p in m.get("content",[]) if p.get("type")=="output_text"]
                proposed = parse(content[0])
                value = {"sample_id":response["sample_id"],"annotations":{"trajectory":proposed["summary"],"timestamps":proposed["timestamps"]}}
            if alias.startswith("SPQ02b-") and rel.startswith("organizer-private/references/"):
                value = {"sample_id":path.stem,"reference":value}
            if alias.startswith("SPQ02b-") and rel.startswith("organizer-private/alternative-records/"):
                value = {**value,"sample_id":value["source_record"]["sample_id"],"answer_annotation":value["annotation_projection"]["private"]["answer_annotation"],"input":value["annotation_projection"]["public"]["input"]}
            nodes=list(annotated_nodes(value))
            if not nodes:
                # Actual requests and prepared/dry-run requests have no completed annotation.
                if alias.startswith("SPQ01-") and (rel.startswith(("requests/","attempt-requests/")) or rel=="paired-requests.json"):
                    sid=path.stem if path.stem in request_by_sample else None
                    actual=next((r for r in requests if rel==f'attempt-requests/{r["attempt_number"]:03}.json'),None) if alias=="SPQ01-annotation-job" else None
                    entries.append({"artifact":alias+"/"+rel,"file_sha256":sha256(raw).hexdigest(),"fields":["request.instructions","request.input"],
                        "origin":"executed_request_payload" if actual else "prepared_or_reused_request_not_new_execution",
                        "request_id":actual["request_id"] if actual else request_by_sample.get(sid,{}).get("request_id"),
                        "complete_payload":actual["payload_file"] if actual else request_by_sample.get(sid,{}).get("payload_file"),
                        "procedure_ids":["public-language/1.0.0"],"parent_artifact":None,
                        "redaction":"alias replaces absolute organizer path; body public where archived"})
                continue
            mappings=[]
            for pointer,node in nodes:
                sid=node["sample_id"];group=mapping.get(sid,node.get("trajectory_id") or node.get("metadata",{}).get("base_scenario_id"))
                request=request_by_sample.get(group_request.get(group))
                language=node.get("public",{}).get("annotations",node.get("annotations",node.get("language_annotations")))
                fields=[];pids=[];origin="deterministic_no_model_prompt";parent=None
                if language is not None:
                    fields+=["trajectory.text","timestamps[*].text"]
                    if request:
                        origin="executed_model_output" if alias=="SPQ01-annotation-job" and rel.startswith(("items/","responses/")) else "reuse_copy_of_executed_model_measurement_annotation"
                        parent="SPQ01-annotation-job/items/"+request["sample_id"]+".json";pids.append("public-language/1.0.0")
                    else:raise ValueError("annotation copy cannot resolve actual generation parent: "+sid)
                    if "event_context" in language:fields.append("event_context/claims");pids += ["event-matching/1.0.0","event-language/2.0.0"]
                inp=node.get("input",node.get("public",{}).get("input",node.get("structured_inputs",{})))
                if inp.get("states") and "linked_events" in inp["states"][0]:
                    fields += ["states[*].linked_events","known_events[*].linked_states","between_state_associations"]
                    pids.append("associations/1.0.0" if alias=="SPQ01a-associations-1.0.0" else "associations/1.1.0" if alias=="SPQ01a-associations-1.1.0" else "associations/1.1.1" if "event_description" in inp.get("known_events",[{}])[0] else "associations/1.0.1")
                    if "event_description" in inp.get("known_events",[{}])[0]:fields.append("event_description and copies");pids.append("event-description/1.0.0" if alias=="SPQ01a-associations-1.1.0" else "event-description/1.0.1")
                family=node.get("question_type",families.get(sid))
                node_gold="explanation-qa/1.0.0" if family=="explanation" else gold_id(alias)
                if family=="explanation":
                    fields += ["question", "supplied_comparison", "explanation_response_contract"]
                    pids += ["explanation-qa/1.0.0", "explanation-evaluation/1.0.0", "explanation-rubric/1.0.0"]
                ref=node.get("reference",node.get("private",{}).get("reference",node.get("qa",{}).get("reference")))
                if not isinstance(ref,dict):ref=None
                if language is not None:
                    base=measurement_base(language) if "event_context" in language else language
                    if canonical(annotation_content(base))!=canonical(annotation_content(originals[request["sample_id"]])):
                        raise ValueError("copied measurement annotation differs from executed output: "+alias+"/"+rel)
                    if inp.get("states"):
                        raw_input=deepcopy(inp)
                        for state in raw_input["states"]:state.pop("linked_events",None)
                        for event in raw_input["known_events"]:
                            for field in ("linked_states","event_description","event_description_bindings","event_description_status"):event.pop(field,None)
                        raw_input.pop("between_state_associations",None)
                        actual_projection=project({"public":{"input":raw_input}})
                        if canonical(actual_projection)!=canonical(parse(read(output/request["payload_file"])["input"])):
                            raise ValueError("copied public input differs from executed annotation projection")
                if ref is not None:
                    fields += ["reference.explanation","reference.solution_trace"]
                    pids.append(node_gold if ref.get("solution_trace",{}).get("status")=="evidence_checked_human_unreviewed" else "source-readout-placeholder")
                if "answer_annotation" in node or "answer_annotation" in node.get("private",{}):
                    fields.append("private.answer_annotation/claims/solution_trace");pids.append(gold_id(alias))
                if "explanation_annotation" in node or "explanation_annotation" in node.get("private",{}):
                    fields.append("private.explanation_annotation/reference/claims/solution_trace");pids.append("explanation-qa/1.0.0")
                if family=="direct":pids.append("direct-readout/1.0.0")
                if family=="counterfactual" or "counterfactual" in inp:pids.append("counterfactual/1.0.0")
                if "requests" in rel or "baseline" in rel:pids.append("prepared-explanation-request/1.0.0" if family=="explanation" else "prepared-answering-request")
                field_generation=[]
                for field in fields:
                    if field.startswith(("trajectory", "timestamps")):
                        field_generation.append({"field":field,"method":origin,"procedure_id":"public-language/1.0.0","parent_artifact":parent,"complete_request":request["payload_file"] if request else None})
                    else:
                        gold_procedure=node_gold
                        procedure = "explanation-evaluation/1.0.0" if field=="explanation_response_contract" else "explanation-qa/1.0.0" if field in ("question","supplied_comparison") or "explanation_annotation" in field else gold_procedure if "answer_annotation" in field or (field.startswith("reference") and gold_procedure in pids) else "source-readout-placeholder" if field.startswith("reference") else ("event-description/1.0.0" if alias=="SPQ01a-associations-1.1.0" else "event-description/1.0.1") if field.startswith("event_description") else "event-language/2.0.0" if field.startswith("event_context") else "associations/1.1.1" if "associations/1.1.1" in pids else "associations/1.1.0" if "associations/1.1.0" in pids else "associations/1.0.0" if "associations/1.0.0" in pids else "associations/1.0.1"
                        deterministic_parent=("SPQ02b-enriched/organizer-private/items/"+explanation_parents[sid]+".json") if family=="explanation" else ("SPQ02-counterfactual/organizer-private/items/"+sid+".json" if family=="counterfactual" else "SPQ01a-event-language-2.0.0/qa-records.jsonl") if alias=="SPQ02b-enriched" else parent
                        field_generation.append({"field":field,"method":"deterministic_no_model_prompt","procedure_id":procedure,"parent_artifact":deterministic_parent})
                if not fields:continue
                mappings.append({"record_pointer":pointer,"sample_id":sid,"trajectory_id":group,"annotated_fields":fields,"field_generation":field_generation,
                    "origin":origin,"procedure_ids":list(dict.fromkeys(pids)),"parent_artifact":parent,
                    "executed_request_id":request["request_id"] if language is not None and request else None,
                    "complete_instantiated_request":request["payload_file"] if language is not None and request else None,
                    "input_sha256":digest(inp) if inp else None,"annotation_output_sha256":digest(language) if language is not None else None})
            if not any(m["annotated_fields"] for m in mappings):continue
            entry={"artifact":alias+"/"+rel,"file_sha256":sha256(raw).hexdigest(),"mappings":mappings,
                "copy_kind":"HTML rendering of sibling JSON" if path.suffix==".html" else "JSON annotation-bearing artifact",
                "parent_file":alias+"/"+path.with_suffix(".json").relative_to(folder).as_posix() if path.suffix==".html" else None,
                "versions":{k:value.get(k) for k in ("schema_version","annotation_version","export_version") if isinstance(value,dict) and k in value},
                "redaction":"Only identities, field paths, procedure/request pointers and hashes; all gold outcomes/evidence remain in external organizer storage."}
            entries.append(entry);all_files.append((path,entry))
    # Deduplicate repeated QA/annotation mappings across packet, aggregate and
    # nine-condition copies. Every file member resolves directly through this table.
    mapping_definitions={}
    for entry in entries:
        refs=[]
        for mapping in entry.get("mappings",[]):
            details={k:v for k,v in mapping.items() if k!="record_pointer"}
            key=digest(details)
            mapping_definitions.setdefault(key,details)
            refs.append({"record_pointer":mapping["record_pointer"],"mapping_id":key})
        if "mappings" in entry:entry["mappings"]=refs
    index={"version":ARCHIVE,"scope":"all annotation-bearing JSON/JSONL and paired HTML in listed versioned development roots; scientific raw release is not recopied; manifests/accounting/ratings contain no generated annotation text",
        "root_aliases":{alias:folder.name for alias,folder in roots.items()},"requests":requests,"procedures":procedures,"files":entries,"mapping_definitions":mapping_definitions,
        "recovery":{"executed_requests":16,"exact_executed_payloads_recovered":16,"unavailable_executed_payloads":0,"reconstructed_executed_payloads":0,"repairs":0,"failures":0,
            "legacy_source_model_prompt":"No source model prompt: original simulator generic context/explanation is deterministic, not completed language annotation.",
            "early_deterministic_implementation":"Historical commits pin accepted code. Preliminary association 1.0.0 source recovered exactly from installer payload and matched to its executed hash. The 1.1.0 association/description working revision original source remains unavailable. Their output hashes are retained; accepted matching rules/templates are documented, not misrepresented as recovered early source."},
        "SPQ03_disclosure":"Selected factual/omission readouts are intentionally public for explanation QA. Their values and gold/rollouts/receipts are not copied into this paper-facing index; field paths/hashes are mapped. No new annotation-model request occurred.",
        "redactions":["Organizer absolute paths and credential reference paths omitted.","Raw provider response metadata, usage/accounting and organizer-private QA/paired outcome evidence not copied into paper catalogue.","No authorization header was stored in JSON request payload; archived exact payloads contain only permitted public focal input."]}
    retained(output/"file-generation-index.json",index)
    example_request=requests[0]
    example_files=[]
    for entry in entries:
        for member in entry.get("mappings",[]):
            detail=mapping_definitions[member["mapping_id"]]
            if detail.get("executed_request_id")==example_request["request_id"]:
                example_files.append({"artifact":entry["artifact"],"file_sha256":entry["file_sha256"],
                    "record_pointer":member["record_pointer"],**detail})
    example={"executed_request":example_request,"complete_exact_payload":example_request["payload_file"],
        "output_file_mappings":example_files,"deterministic_example":next(p for p in procedures if p["procedure_id"]=="answer-annotation/1.0.3"),
        "categories":{"executed":"SPQ01 items/responses: actual returned annotation", "reused":"Subsequent packets/requests copy measurement annotation; no new execution",
            "deterministic":"Answer/trace rendering and event enrichment use pinned code, not model prompts", "unrecoverable":"Preliminary association 1.1.0/event-description 1.0.0 source; all 16 executed model payloads recovered"}}
    retained(output/"provenance-example.json",example)
    worked=["# Recovered executed request and deterministic procedure\n",
        f'Actual request [{example_request["request_id"]}]({example_request["payload_file"]}); sample `{example_request["sample_id"]}`. One execution produced a summary and {example_request["timestamp_outputs"]} timestamps. Complete unchanged instructions, instantiated input and settings: [exact wire payload]({example_request["payload_file"]}).\n',
        "## Output-file mappings\n\n| Artifact | Origin | Fields |\n|---|---|---|\n"]
    for m in example_files:
        worked.append(f'| `{m["artifact"]}` | {m["origin"]} | {", ".join(m["annotated_fields"])} |')
    worked.append("\n## Deterministic procedure\n\n[answer-annotation/1.0.3](procedures/answer-annotation-1.0.3.py) implements shared physical context once, evidence-bound target readouts and sign-invariant quaternion rotation angle. Exact values remain unchanged; no model prompt or request. Detailed numerical method and verification stay in private traces.\n\nExecuted requests, reused outputs and deterministic field procedures are separately mapped in [the index](file-generation-index.json) and [this complete worked mapping](provenance-example.json). All 16 executed payloads are recovered; preliminary association 1.1.0/event-description 1.0.0 original source remains unrecoverable, not reconstructed. Prepared answering requests are unexecuted.\n")
    retained_bytes(output/"provenance-example.md","\n".join(worked).encode())
    catalogue=["# SimPhysQA annotation prompts and deterministic procedures\n",
        "This is an annotation provenance archive, not a record of answering-model experiments. All 16 executed language requests are recovered exactly; no reconstruction is needed. One request produced one trajectory summary and 11 timestamp descriptions. Later QA packets copy/enrich those annotations without new requests. Authoring instructions live in docs/prompts and are distinct from generator payloads. Gold answer enrichments are deterministic and remain human-unreviewed.\n",
        "## Exact executed annotation instructions\n\nThe Responses API received an `instructions` string followed by a canonical public `input` string, not a role-tagged system/developer/user message array. Below is the actual instruction text. The complete raw body (including output schema) and fully instantiated input for every attempt are linked and reproduced below.\n"]
    instructions={read(output/r["payload_file"])["instructions"] for r in requests}
    for text in sorted(instructions):catalogue.append("```text\n"+text+"```\n")
    for r in requests:
        body=read(output/r["payload_file"])
        catalogue.append(f'\n## {r["request_id"]} — {r["sample_id"]}\n\nExact saved payload: [{r["payload_file"]}]({r["payload_file"]}). Request SHA256 `{r["request_sha256"]}`. Returned model `{r["returned_model"]}`. Output: summary plus {r["timestamp_outputs"]} timestamps; no repair/retry.\n\nGeneration settings:\n```json\n'+canonical({**r["settings"],"timeout_seconds":r["timeout_seconds"],"temperature":"omitted","seed":"omitted"}).decode()+"```\n\nExact instantiated input string:\n```json\n"+body["input"]+"```\n")
    catalogue.append("\n## Deterministic procedures (no annotation-model prompt)\n\nEach link contains exact pinned implementation text, including actual templates and input projections. Matching code is never executed as extracted formula text. Earlier preliminary output-only revisions are explicitly distinguished from accepted code.\n")
    for p in procedures:
        catalogue.append(f'\n### {p["procedure_id"]}\n\n{p["rules"]}\n\n[Actual code/templates]({p["source_file"]}); source `{p["source_path"]}`, commit `{p["source_commit"]}`, SHA256 `{p["implementation_sha256"]}`.\n')
        if p["source_file"] is None:continue
        code=(output/p["source_file"]).read_text(encoding="utf-8")
        catalogue.append("<details><summary>Exact templates, rules and input projection</summary>\n\n```python\n"+code+"\n```\n\n</details>\n")
    if explanations is not None:
        catalogue.append("\n## SPQ03 explanation-task disclosure and generation\n\nEight new explanation QA reuse the frozen verified pairs and their original selected targets. Public supplied_comparison deliberately discloses only factual/omission target readouts; the observed prefix and original language stay unchanged. Questions/references/traces and the rubric are deterministic, with no new annotation-model request. The explanation-specific answering JSON contract and prompt are prepared under all nine conditions, never executed. Human prose quality and explanatory adequacy remain uncollected; structured factual checks alone cannot establish explanation correctness. New items and their embedded accepted parent copies have distinct per-field mappings in the index.\n")
    catalogue.append("\n## Per-file mappings\n\n[file-generation-index.json](file-generation-index.json) inventories every annotation-bearing file, individual sample/trajectory, annotated field, model-request parent, instantiated payload and deterministic stage. Aggregate QA lists and prepared requests retain individual mappings. HTML packets map to their sibling JSON. Each file member has a mapping_id that resolves directly to a deduplicated mapping_definitions entry and its complete executed request; this saves repeating the same mapping across nine conditions. Full private inputs/evidence are deliberately excluded from this paper-facing index. Source/output hashes permit organizer-side verification. All answering requests remain prepared, never executed.\n\n## Historical limitations\n\nAll executed model payloads recovered: 16/16; unavailable: 0; reconstructed: 0; repairs: 0. Original generic simulator contexts/explanations were deterministic placeholders, with no model request to recover. Preliminary association 1.0.0 source is recovered exactly from its saved installer payload (executed hash matches). The preliminary 1.1.0 association/description source remains unrecoverable; its recorded source/output hashes and accepted successor templates remain separate. Credential headers/paths and private QA outcomes/verification are excluded; no redaction alters the 16 public JSON request bodies.\n")
    retained_bytes(output/"catalogue.md","\n".join(catalogue).encode())
    retained_bytes(output/"README.md",("# Annotation prompt/procedure archive\n\nInspect [one recovered executed request and its output-file mappings, plus a deterministic procedure](provenance-example.md). SPQ03 adds eight deterministic matched-intervention explanation items, with separately disclosed selected target readouts and no new model request. Start with [the consolidated catalogue](catalogue.md): actual prompt text, all 16 fully instantiated executed inputs, model/settings, and pinned deterministic templates. Use [the per-file index](file-generation-index.json) to resolve every annotation output/copy to its executed request or deterministic procedure.\n\nThis public archive intentionally excludes gold answers, traces, future outcomes, paired verification and organizer credential locations. Complete private evidence remains in the external versioned export. Request bodies use only observed focal states/declared controls; no answering benchmark has run. Authoring instructions: [active milestone](../../prompts/SPQ03_explanation_qa.md).\n").encode())
    counts={"version":ARCHIVE,"annotation_files":len(all_files),"indexed_files":len(entries),"record_mappings":sum(len(e.get("mappings",[])) for e in entries),"unique_mapping_definitions":len(mapping_definitions),
            "exact_recovered_requests":16,"unavailable_executed_requests":0,"reconstructed_requests":0,
            "new_model_calls":0,"unavailable_preliminary_source_snapshots":["associations-1.1.0 association implementation and event-description/1.0.0 renderer"],
            "gold_fields_in_paper_archive":False}
    retained(output/"coverage.json",counts)
    if (output/"manifest.json").exists():verify_manifest(output)
    else:manifest(output,{"purpose":"paper_facing_prompt_procedure_archive","archive_version":ARCHIVE,"index_sha256":digest(index),"builder_sha256":sha256(Path(__file__).read_text(encoding="utf-8").encode()).hexdigest(),"counts":counts})
    print(canonical(counts).decode(),end="");return counts

def main():
    p=argparse.ArgumentParser(description=__doc__)
    for name in ("spq01","spq01a","spq02","enriched","output"):p.add_argument("--"+name,type=Path,required=True)
    p.add_argument("--explanations",type=Path)
    a=p.parse_args();build(a.spq01,a.spq01a,a.spq02,a.enriched,a.output,a.explanations)

if __name__=="__main__":main()
