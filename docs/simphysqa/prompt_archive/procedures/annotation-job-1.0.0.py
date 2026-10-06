"""Durable bounded annotation execution. All reservations/attempts/outputs are immutable."""
from contextlib import contextmanager
from copy import deepcopy
from pathlib import Path
import os
import math
import time
from jsonschema.exceptions import ValidationError
from .annotation import (PROMPT_VERSION, PROMPT, ENDPOINT, decode, http_call, load_key,
                         payload, project, reservation, schema, usage_cost, validate_generated, ProviderError)
from .dataset import VERSION, attach_annotation, public_record, validate
from .direct import build_direct
from .audit import export_packets, import_ratings
from .io import canonical, digest, external, manifest, read, write

@contextmanager
def locked(path):
    path.parent.mkdir(parents=True,exist_ok=True)
    with path.open("a+b") as stream:
        stream.seek(0)
        if not stream.read(1):
            stream.write(b"0")
            stream.flush()
        stream.seek(0)
        if os.name=="nt":
            import msvcrt
            msvcrt.locking(stream.fileno(),msvcrt.LK_NBLCK,1)
        else:
            import fcntl
            fcntl.flock(stream,fcntl.LOCK_EX|fcntl.LOCK_NB)
        try:
            yield
        finally:
            stream.seek(0)
            if os.name=="nt":
                msvcrt.locking(stream.fileno(),msvcrt.LK_UNLCK,1)
            else:
                fcntl.flock(stream,fcntl.LOCK_UN)

def validate_config(config):
    budget=config["budget"]
    if config["endpoint"]!=ENDPOINT or not config["model"] or not config["pricing"].get("verified_sources"):
        raise ValueError("unresolved_provider_identity_endpoint_or_pricing")
    if budget["initial_requests"]!=16 or budget["total_attempts"]>32 or budget["usd_cap"]>5 or budget["usd_cap"]<=0:
        raise ValueError("SPQ01_hard_budget_not_enforced")
    if not 1<=budget["attempts_per_item"]<=2 or budget["total_attempts"]<16:
        raise ValueError("invalid_per_item_attempt_limit")
    if config["max_output_tokens"]!=2048 or config["reasoning_effort"]!="medium":
        raise ValueError("historical_generation_setting_changed")
    if type(budget["framing_token_reserve"]) is not int or budget["framing_token_reserve"] < 4096:
        raise ValueError("insufficient_input_framing_reservation")
    if not 0 < config["pricing"]["short_context_input_limit"] <= 272000:
        raise ValueError("unverified_context_pricing_limit")
    rate=config["pricing"]
    write_rate=rate.get("cache_write_per_million",1.25*rate["input_per_million"])
    prices=[rate[k] for k in ("input_per_million","cached_input_per_million","output_per_million","reserve_input_per_million","reserve_output_per_million")]+[write_rate]
    if any(type(v) not in (int,float) or not math.isfinite(v) or v < 0 for v in prices):
        raise ValueError("invalid_or_nonfinite_pricing")
    if rate["reserve_input_per_million"] < max(rate["input_per_million"],rate["cached_input_per_million"],write_rate) or rate["reserve_output_per_million"] < rate["output_per_million"]:
        raise ValueError("reservation_rates_do_not_cover_resolved_prices")
    if config["service_tier"] != "default" or config["tools"] or config["store"] is not False:
        raise ValueError("configured_provider_settings_do_not_match_transport")
    if budget["wall_seconds"]<=0 or budget["total_input_tokens"]<=0 or budget["total_output_tokens"]<=0:
        raise ValueError("finite_token_and_wall_limits_required")

def dry_run(records,config,output=None):
    validate_config(config)
    if len(records)!=16 or len({r["trajectory_id"] for r in records})!=16:
        raise ValueError("SPQ01_requires_16_distinct_trajectories")
    sizes=[]
    requests=[]
    for record in records:
        validate(record)
        body=payload(record,config)
        bound=reservation(body,config)
        sizes.append({"sample_id":record["sample_id"],"domain":record["public"]["input"]["domain"],
            "observed_timestamps":len(record["public"]["input"]["states"]),"request_bytes":len(canonical(body)),**bound})
        requests.append({"sample_id":record["sample_id"],"public_view_sha256":digest(project(record)),
            "prompt_version":PROMPT_VERSION,"prompt_sha256":digest(PROMPT),"annotation_schema_sha256":digest(schema()),
            "request_sha256":digest(body),"payload":body})
    initial=sum(v["usd"] for v in sizes)
    report={"version":"simphysqa-annotation-dry-run/1.0.0","resolved_nonsecret_config":{**config,"pricing":{**config["pricing"],
            "cache_write_per_million":config["pricing"].get("cache_write_per_million",1.25*config["pricing"]["input_per_million"]) }},
        "initial_request_count":16,"maximum_total_attempts":config["budget"]["total_attempts"],
        "input_size_summary":{"min_bytes":min(v["request_bytes"] for v in sizes),"max_bytes":max(v["request_bytes"] for v in sizes),
                             "sum_bytes":sum(v["request_bytes"] for v in sizes),
                             "initial_input_token_upper_bound":sum(v["input_token_upper_bound"] for v in sizes)},
        "budget_estimate":{"initial_full_reservation_usd":initial,"all_32_full_reservations_usd":initial*2,
                           "hard_cap_usd":config["budget"]["usd_cap"],"initial_requests_fit":initial<=config["budget"]["usd_cap"],
                           "policy":"admit each request only if retained charges plus its full token-price reservation fit; unknown usage retains reservation"},
        "items":sizes,"model_calls":0,"quality":"no_annotations_generated_or_human_assessed"}
    if output is not None:
        output=external(output)
        output.mkdir(parents=True,exist_ok=False)
        write(output/"dry-run.json",report)
        for req in requests:
            write(output/"requests"/(req["sample_id"]+".json"),req)
        manifest(output,{"purpose":"SPQ01_annotation_dry_run_no_calls","config_sha256":digest(config)})
    return report

def ledger(root):
    attempts=[read(p) for p in sorted((root/"attempts").glob("*.json"))]
    charges=[]
    for attempt in attempts:
        response=root/"responses"/(str(attempt["attempt_number"]).zfill(3)+".json")
        account=read(response)["accounting"] if response.exists() else {
            "recorded_cost_usd":None,"charged_upper_bound_usd":attempt["reservation"]["usd"],"status":"interrupted_unknown_reserved"}
        # Recompute from immutable raw usage with the executed settings; old summaries remain untouched.
        if response.exists() and (root/"job.json").exists():
            raw=read(response).get("raw_response")
            if raw is not None:
                account=usage_cost(raw,read(root/"job.json")["identity"]["config"],attempt["reservation"])
        charges.append({**attempt,**account})
    return charges

def run(records,config,output,key=None,transport=None):
    preflight=dry_run(records,config)
    print(canonical({"preflight":preflight}).decode(),flush=True)
    if not preflight["budget_estimate"]["initial_requests_fit"]:
        raise ValueError("initial_request_reservations_exceed_budget")
    output=external(output)
    output.mkdir(parents=True,exist_ok=True)
    identity={"version":"simphysqa-annotation-job/1.0.0","config":config,"prompt":PROMPT,"schema":schema(),
              "records":{r["sample_id"]:digest(r) for r in records}}
    with locked(output/".job.lock"):
        if (output/"job.json").exists():
            if read(output/"job.json")["identity"]!=identity:
                raise ValueError("resume_identity_mismatch")
        else:
            write(output/"job.json",{"identity":identity,"created_unix":time.time(),"deadline_unix":time.time()+config["budget"]["wall_seconds"]})
            for record in records:
                write(output/"requests"/(record["sample_id"]+".json"),payload(record,config))
        deadline=read(output/"job.json")["deadline_unix"]
        stop_reason=None
        if transport is None:
            try:
                key=key or load_key(Path(config["credential_reference_file"]))
            except (OSError,ValueError):
                stop_reason="credential_access_unresolved"
            transport=lambda body:http_call(body,config,key)
        # Two rounds ensure all initial items get an opportunity before repair requests.
        for round_no in range(config["budget"]["attempts_per_item"]):
            for record in records:
                item_path=output/"items"/(record["sample_id"]+".json")
                if item_path.exists() or stop_reason:
                    continue
                history=ledger(output)
                own=[a for a in history if a["sample_id"]==record["sample_id"]]
                if len(own)>round_no:
                    continue
                feedback=None
                if own:
                    previous=output/"responses"/(str(own[-1]["attempt_number"]).zfill(3)+".json")
                    feedback=read(previous).get("failure","interrupted_request") if previous.exists() else "interrupted_request"
                body=payload(record,config,feedback)
                reserved=reservation(body,config)
                charged=sum(a["charged_upper_bound_usd"] for a in history)
                input_reserved=sum(a["reservation"]["input_token_upper_bound"] for a in history)
                output_reserved=sum(a["reservation"]["output_token_limit"] for a in history)
                budget=config["budget"]
                if (len(history)>=budget["total_attempts"] or charged+reserved["usd"]>budget["usd_cap"] or
                    input_reserved+reserved["input_token_upper_bound"]>budget["total_input_tokens"] or
                    output_reserved+reserved["output_token_limit"]>budget["total_output_tokens"] or
                    time.time()+config["timeout_seconds"]>deadline):
                    stop_reason="budget_or_deadline_exhausted"
                    continue
                attempt_no=len(history)+1
                initial=not own
                if initial and sum(a["initial_request"] for a in history)>=budget["initial_requests"]:
                    stop_reason="initial_request_cap"
                    continue
                attempt={"attempt_number":attempt_no,"sample_id":record["sample_id"],"initial_request":initial,
                    "repair":not initial,"request_sha256":digest(body),"reservation":reserved,"started_unix":time.time()}
                write(output/"attempts"/(str(attempt_no).zfill(3)+".json"),attempt)
                write(output/"attempt-requests"/(str(attempt_no).zfill(3)+".json"),body)
                failure=None
                raw=None
                accounting={"recorded_cost_usd":None,"charged_upper_bound_usd":reserved["usd"],"status":"unknown_usage_reserved"}
                annotation=None
                started=time.monotonic()
                try:
                    raw=transport(body)
                    accounting=usage_cost(raw,config,reserved)
                    if accounting["status"]=="pricing_or_token_bound_violation":
                        raise ProviderError("pricing_or_token_bound_violation")
                    returned=raw.get("model")
                    if not returned or not (returned==config["model"] or returned.startswith(config["model"]+"-")):
                        raise ProviderError("returned_model_identity_mismatch")
                    proposed=decode(raw)
                    annotation=validate_generated(record,proposed)
                    # Validate the actual final answering-model view, not just the request.
                    exported=public_record(record)
                    exported["annotations"]=annotation
                    validate_generated({"public":{"input":exported["input"]}},
                                       {"summary":{k:v for k,v in annotation["trajectory"].items() if k!="status"},
                                        "timestamps":[{k:v for k,v in a.items() if k!="status"} for a in annotation["timestamps"]]})
                except (ProviderError,ValueError,KeyError,ValidationError,TimeoutError) as exc:
                    failure=exc.message if isinstance(exc,ValidationError) else str(exc)
                    failure=failure[:240]
                except Exception as exc:
                    # Do not print provider exception bodies or credentials.
                    failure="unexpected_"+type(exc).__name__
                response={"attempt_number":attempt_no,"sample_id":record["sample_id"],"raw_response":raw,
                    "accounting":accounting,"failure":failure,"wall_seconds":time.monotonic()-started}
                write(output/"responses"/(str(attempt_no).zfill(3)+".json"),response)
                print(canonical({"attempt":attempt_no,"sample_id":record["sample_id"],"failure":failure,
                                 "accounting":accounting}).decode(),flush=True)
                if failure is None:
                    history=ledger(output)
                    own=[a for a in history if a["sample_id"]==record["sample_id"]]
                    provenance={"status":"generated_unreviewed","model_identity":raw["model"],
                        "prompt_version":PROMPT_VERSION,"schema_version":VERSION,
                        "generation_settings":{**config,"prompt_sha256":digest(PROMPT),"annotation_schema_sha256":digest(schema())},
                        "validation_failures":[read(output/"responses"/(str(a["attempt_number"]).zfill(3)+".json"))["failure"] for a in own[:-1]
                            if (output/"responses"/(str(a["attempt_number"]).zfill(3)+".json")).exists()],
                        "attempts":own,"retries":len(own)-1,"repairs":len(own)-1}
                    write(item_path,{"status":"automatically_validated_human_unreviewed","sample_id":record["sample_id"],
                        "annotations":annotation,"provenance":provenance})
                if failure and any(code in failure for code in ("http_401","http_403","http_404","pricing_or_token_bound_violation","returned_model_identity_mismatch")):
                    stop_reason=failure
        history=ledger(output)
        for record in records:
            path=output/"items"/(record["sample_id"]+".json")
            if not path.exists():
                own=[a for a in history if a["sample_id"]==record["sample_id"]]
                failures=[]
                for a in own:
                    p=output/"responses"/(str(a["attempt_number"]).zfill(3)+".json")
                    failures.append(read(p)["failure"] if p.exists() else "interrupted_unknown_reserved")
                write(path,{"status":"failed_annotations_pending","sample_id":record["sample_id"],"model_identity":config["model"],
                    "prompt_version":PROMPT_VERSION,"schema_version":VERSION,"settings":config,"attempts":own,
                    "validation_failures":failures,"reason":stop_reason or "retry_exhaustion"})
        items=[read(output/"items"/(r["sample_id"]+".json")) for r in records]
        summary={"version":"simphysqa-annotation-accounting/1.0.0","requests":len(records),
            "initial_requests":sum(a["initial_request"] for a in history),"total_attempts":len(history),
            "repairs":sum(a["repair"] for a in history),"automatically_validated":sum(v["status"]=="automatically_validated_human_unreviewed" for v in items),
            "failed_items":sum(v["status"]=="failed_annotations_pending" for v in items),
            "recorded_spend_usd":sum(a["recorded_cost_usd"] or 0 for a in history),
            "charged_with_unknown_reservations_usd":sum(a["charged_upper_bound_usd"] for a in history),
            "unknown_usage_attempts":sum(a["recorded_cost_usd"] is None for a in history),
            "input_tokens_reported":sum((a.get("usage") or {}).get("input_tokens",0) for a in history),
            "output_tokens_reported":sum((a.get("usage") or {}).get("output_tokens",0) for a in history),
            "cache_write_tokens_reported":sum(((a.get("usage") or {}).get("input_tokens_details") or {}).get("cache_write_tokens",0) for a in history),
            "accounting_version":"simphysqa-token-accounting/1.0.1-cache-write-aware",
            "stop_reason":stop_reason,"human_ratings":0,"quality_assessment":"not_performed"}
        number=len(list((output/"summaries").glob("*.json")))+1 if (output/"summaries").exists() else 1
        write(output/"summaries"/(str(number).zfill(3)+".json"),summary)
        return summary

def export_development(records,job_root,output):
    pairs=[]
    for predictive in records:
        item=read(job_root/"items"/(predictive["sample_id"]+".json"))
        enriched=deepcopy(predictive)
        if item["status"]=="automatically_validated_human_unreviewed":
            enriched=attach_annotation(predictive,{"sample_id":predictive["sample_id"],"annotation_version":"spq01-public-language/1.0.0",
                "annotations":item["annotations"],"provenance":item["provenance"]})
            # Recheck persisted result and final public export on reload.
            pub=public_record(enriched)
            annotations=pub["annotations"]
            validate_generated(enriched,{"summary":{k:v for k,v in annotations["trajectory"].items() if k!="status"},
                "timestamps":[{k:v for k,v in a.items() if k!="status"} for a in annotations["timestamps"]]})
        else:
            enriched["private"]["generation_job"]={"status":item["status"],"model_identity":item["model_identity"],
                "prompt_version":item["prompt_version"],"validation_failures":item["validation_failures"],"attempts":item["attempts"],"reason":item["reason"]}
        enriched["private"]["generation_job"]={**enriched["private"].get("generation_job",{}),
            "accounting_version":"simphysqa-token-accounting/1.0.1-cache-write-aware",
            "accounting":[a for a in ledger(job_root) if a["sample_id"]==predictive["sample_id"]]}
        if enriched["private"]["reference"]!=predictive["private"]["reference"]:
            raise ValueError("predictive_reference_changed")
        direct=build_direct(enriched)
        validate(direct)
        pairs.extend([enriched,direct])
    output=external(output)
    output.mkdir(parents=True,exist_ok=False)
    with (output/"qa-records.jsonl").open("xb") as stream:
        for record in pairs:
            stream.write(canonical(record))
    write(output/"public-qa.json",[public_record(r) for r in pairs])
    export_packets(pairs,output/"audit-development",phase="development")
    for reviewer in ("R1","R2","R3"):
        import_ratings(output/"audit-development",output/"audit-development/forms"/(reviewer+".csv"),output/(reviewer+"-blank-import.json"))
    manifest(output,{"purpose":"SPQ01_development_pairs_not_formal_sample","qa_items":32,"trajectories":16,
        "question_types":{"direct":16,"predictive":16},"annotation_job_root":str(job_root.resolve()),"human_ratings":0})
    return {"qa_items":32,"trajectories":16,"direct":16,"predictive":16,"human_ratings":0}

def comparison(records,primary,alternative,output):
    requests=[]
    for record in records:
        primary_request=payload(record,primary)
        requests.append({"sample_id":record["sample_id"],"physical_input_sha256":digest(project(record)),
            "prompt_sha256":digest(PROMPT),"schema_sha256":digest(schema()),
            "primary":primary_request,"alternative":payload(record,alternative) if alternative.get("model") else None})
    output=external(output)
    output.mkdir(parents=True,exist_ok=False)
    write(output/"paired-requests.json",requests)
    return manifest(output,{"purpose":"paired_source_comparison_interface_no_calls","status":"pending_exact_alternative_and_protocol",
        "items":len(records),"same_physical_input_prompt_schema":True,"generator_identity":"organizer_only",
        "model_calls":0,"main_audit_allocation_changed":False})
