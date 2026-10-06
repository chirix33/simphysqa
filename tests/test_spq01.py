"""Offline behavioral checks on selected real sources. Transports are synthetic test inputs only."""
from copy import deepcopy
from contextlib import redirect_stdout
import io
import os
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch
from jsonschema.exceptions import ValidationError
from simphysqa.annotation import decode, payload, project, validate_generated, ProviderError, usage_cost, reservation
from simphysqa.audit import preview, export_packets, import_ratings
from simphysqa.dataset import load, validate, restore, attach_annotation
from simphysqa.direct import build_direct
from simphysqa.io import ROOT, canonical, digest, read
from simphysqa.job import run, dry_run, ledger, export_development, comparison

def format_value(value):
    if isinstance(value,list):
        return "["+", ".join(f"{v:.6g}" for v in value)+"]"
    return f"{value:.6g}"

def proposal(record):
    view=project(record)
    states=view["observed"]
    focal=view["focal_entity"]+" "+view["focal_quantity"]
    first,last=states[0],states[-1]
    initial=view["facts"][first["value_binding"]]
    final=view["facts"][last["value_binding"]]
    text=f'{focal}: {format_value(initial["value"])} at {first["timestamp"]:.6g} s to {format_value(final["value"])} at {last["timestamp"]:.6g} s ({final["unit"]}, {final["frame"]}).'
    summary={"text":text,"bindings":[first["time_binding"],first["value_binding"],last["time_binding"],last["value_binding"]]}
    timestamps=[]
    for state in states:
        measured=view["facts"][state["value_binding"]]
        text=f'At {state["timestamp"]:.6g} s, {focal} is {format_value(measured["value"])} {measured["unit"]} ({measured["frame"]}).'
        timestamps.append({"state_id":state["state_id"],"timestamp":state["timestamp"],"text":text,
                           "bindings":[state["time_binding"],state["value_binding"]]})
    return {"summary":summary,"timestamps":timestamps}

def response(record):
    return {"status":"completed","model":"gpt-5.6-sol","service_tier":"default",
        "usage":{"input_tokens":100,"output_tokens":100,"input_tokens_details":{"cached_tokens":0}},
        "output":[{"type":"message","content":[{"type":"output_text","text":canonical(proposal(record)).decode()}]}]}

class SPQ01Tests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.records=list(load(Path(os.environ["SIMPHYSQA_DEVELOPMENT_RECORDS"])))
        cls.config=read(ROOT/"configs/simphysqa/annotation_spq01.json")
        cls.mapping={digest(project(r)):r for r in cls.records}

    def transport(self,body):
        return response(self.mapping[digest(__import__("json").loads(body["input"]))])

    def test_selection_and_dry_run_all_four_domains_no_network(self):
        self.assertEqual(len(self.records),16)
        self.assertEqual(len({r["trajectory_id"] for r in self.records}),16)
        counts=__import__("collections").Counter(r["public"]["input"]["domain"] for r in self.records)
        self.assertEqual(set(counts.values()),{4})
        with patch("socket.socket.connect",side_effect=AssertionError("network forbidden")):
            report=dry_run(self.records,self.config)
        self.assertEqual(report["model_calls"],0)
        self.assertTrue(report["budget_estimate"]["initial_requests_fit"])

    def test_all_timestamp_evidence_roundtrip_and_direct_readout(self):
        for record in self.records:
            original=deepcopy(record)
            annotations=validate_generated(record,proposal(record))
            record=attach_annotation(record,{"sample_id":record["sample_id"],"annotation_version":"synthetic-test-only/1",
                "annotations":annotations,"provenance":{"status":"generated_unreviewed","model_identity":"synthetic-test-only",
                    "prompt_version":"test-only/1","schema_version":"simphysqa/0.1.0","generation_settings":{},
                    "validation_failures":[],"attempts":[{"test_only":True}],"retries":0,"repairs":0}})
            direct=build_direct(record)
            validate(direct)
            self.assertEqual(restore(direct),restore(original))
            self.assertEqual(record["private"]["reference"],original["private"]["reference"])
            self.assertEqual(direct["private"]["reference"]["states"],[record["public"]["input"]["states"][-1]])
            label=direct["private"]["reference"]["structured_label"][0]
            target=direct["public"]["input"]["answer_spec"][0]
            measured=next(m for m in direct["public"]["input"]["states"][-1]["measurements"]
                if (m["entity_id"],m["name"])==(target["entity_id"],target["quantity"]))
            self.assertEqual(label["value"],measured["value"])
            self.assertEqual((label["unit"],label["frame"]),(measured["unit"],measured["frame"]))
            direct["private"]["reference"]["structured_label"][0]["value"]=999
            with self.assertRaises(ValueError):validate(direct)

    def test_private_outcomes_absent_from_project_and_final_view(self):
        for record in self.records:
            before=payload(record,self.config)
            mutated=deepcopy(record)
            mutated["private"]["reference"]={"PRIVATE_OUTCOME_SENTINEL":999}
            self.assertEqual(payload(mutated,self.config),before)
            self.assertNotIn("PRIVATE_OUTCOME_SENTINEL",str(before))
            proposed=proposal(record)
            proposed["timestamps"][-1]["text"]+=" will be 999"
            with self.assertRaises(ValueError):validate_generated(record,proposed)
            proposed=proposal(record)
            proposed["summary"]["bindings"].append("/reference/states/0")
            with self.assertRaises(ValueError):validate_generated(record,proposed)

    def test_missing_malformed_generic_wrong_time_and_value_rejected(self):
        record=self.records[0]
        for mutate in (
            lambda p:p["timestamps"].pop(),
            lambda p:p["timestamps"][0].update(timestamp=99),
            lambda p:p["timestamps"][0].update(text="Measured simulator state at the stated timestamp."),
            lambda p:p["timestamps"][0]["bindings"].pop(),
            lambda p:p["timestamps"][0].update(text="joint_1 angle is 999 rad (joint_local)."),
            lambda p:p["summary"].update(text="joint_1 angle increased because contact occurred.")):
            proposed=proposal(record);mutate(proposed)
            with self.assertRaises((ValueError,ValidationError)):validate_generated(record,proposed)
        with self.assertRaises(ValidationError):validate_generated(record,{"summary":{}})
        with self.assertRaises(ProviderError):decode({"status":"incomplete","incomplete_details":{"reason":"max_output_tokens"}})
        with self.assertRaises(ProviderError):decode({"status":"completed","output":[]})

    def test_resume_has_zero_new_calls_and_no_completed_overwrite(self):
        with tempfile.TemporaryDirectory() as temp,redirect_stdout(io.StringIO()):
            root=Path(temp)/"job"
            first=run(self.records,self.config,root,key="synthetic-test-only",transport=self.transport)
            self.assertEqual(first["initial_requests"],16)
            self.assertEqual(first["automatically_validated"],16)
            hashes={p.name:p.read_bytes() for p in (root/"items").glob("*.json")}
            def forbidden(body):raise AssertionError("resume called provider")
            second=run(self.records,self.config,root,key="synthetic-test-only",transport=forbidden)
            self.assertEqual(second["total_attempts"],16)
            self.assertEqual(hashes,{p.name:p.read_bytes() for p in (root/"items").glob("*.json")})
            changed=deepcopy(self.config);changed["reasoning_effort"]="low"
            with self.assertRaises(ValueError):run(self.records,changed,root,transport=forbidden)

    def test_retry_exhaustion_accounts_all_failures_and_blank_forms(self):
        with tempfile.TemporaryDirectory() as temp,redirect_stdout(io.StringIO()):
            root=Path(temp)
            def broken(body):return {"status":"completed","model":"gpt-5.6-sol","usage":{"input_tokens":1,"output_tokens":1},"output":[]}
            report=run(self.records,self.config,root/"job",transport=broken)
            self.assertEqual(report["total_attempts"],32)
            self.assertEqual(report["repairs"],16)
            self.assertEqual(report["failed_items"],16)
            self.assertLessEqual(report["charged_with_unknown_reservations_usd"],5)
            for item in (root/"job/items").glob("*.json"):
                self.assertEqual(len(read(item)["validation_failures"]),2)
                self.assertEqual(read(item)["reason"],"retry_exhaustion")
            export=export_development(self.records,root/"job",root/"export")
            self.assertEqual(export["qa_items"],32)
            for reviewer in ("R1","R2","R3"):
                imported=read(root/"export"/(reviewer+"-blank-import.json"))
                self.assertEqual((imported["collected"],imported["blank"]),(0,32))

    def test_unknown_usage_stays_reserved_and_budget_exhaustion_is_explicit(self):
        with tempfile.TemporaryDirectory() as temp,redirect_stdout(io.StringIO()):
            def unavailable(body):raise ProviderError("timeout")
            report=run(self.records,self.config,Path(temp)/"job",transport=unavailable)
            self.assertLessEqual(report["initial_requests"],16)
            self.assertLessEqual(report["total_attempts"],32)
            self.assertGreater(report["unknown_usage_attempts"],0)
            self.assertLessEqual(report["charged_with_unknown_reservations_usd"],5)
            self.assertEqual(report["stop_reason"],"budget_or_deadline_exhausted")
            config=deepcopy(self.config);config["budget"]["usd_cap"]=.01
            with self.assertRaises(ValueError):run(self.records,config,Path(temp)/"never",transport=unavailable)

    def test_interrupted_reservation_and_returned_pricing_bounds(self):
        with tempfile.TemporaryDirectory() as temp,redirect_stdout(io.StringIO()):
            root=Path(temp)/"job"
            def interrupted(body):raise KeyboardInterrupt()
            with self.assertRaises(KeyboardInterrupt):run(self.records,self.config,root,transport=interrupted)
            charges=ledger(root)
            self.assertEqual(len(charges),1)
            self.assertEqual(charges[0]["status"],"interrupted_unknown_reserved")
            report=run(self.records,self.config,root,transport=self.transport)
            self.assertEqual(report["initial_requests"],16)
            self.assertEqual(report["total_attempts"],17)
            self.assertEqual(report["automatically_validated"],16)
            self.assertEqual(report["unknown_usage_attempts"],1)
        body=payload(self.records[0],self.config)
        bound=reservation(body,self.config)
        wrong={"usage":{"input_tokens":100,"output_tokens":bound["output_token_limit"]+1},"service_tier":"default"}
        self.assertEqual(usage_cost(wrong,self.config,bound)["status"],"pricing_or_token_bound_violation")

    def test_unsafe_pricing_and_transport_configuration_rejected_before_calls(self):
        for change in (lambda c:c["pricing"].update(reserve_input_per_million=.1),
                       lambda c:c["pricing"].update(input_per_million=float("nan")),
                       lambda c:c.update(service_tier="priority"),
                       lambda c:c["budget"].update(framing_token_reserve=0)):
            config=deepcopy(self.config);change(config)
            with self.assertRaises(ValueError):dry_run(self.records,config)

    def test_implicit_cache_writes_use_distinct_rate_and_invalid_usage_reserves(self):
        bound=reservation(payload(self.records[0],self.config),self.config)
        raw={"usage":{"input_tokens":100,"output_tokens":10,"input_tokens_details":{"cached_tokens":20,"cache_write_tokens":60}},"service_tier":"default"}
        self.assertAlmostEqual(usage_cost(raw,self.config,bound)["recorded_cost_usd"],.000588)
        raw["usage"]["input_tokens_details"]["cache_write_tokens"]=100
        result=usage_cost(raw,self.config,bound)
        self.assertEqual(result["status"],"unknown_usage_reserved")
        self.assertEqual(result["charged_upper_bound_usd"],bound["usd"])

    def test_development_groups_are_durably_excluded_from_fresh_preview(self):
        result=preview(self.records,20261004)
        self.assertEqual(result["eligible_groups"],0)
        self.assertEqual(result["shortfall"],160)
        self.assertNotIn("formal_ids",result)
        with tempfile.TemporaryDirectory() as temp:
            pair=[self.records[0],build_direct(self.records[0])]
            with self.assertRaises(ValueError):export_packets(pair,Path(temp)/"calibration","calibration")
            with self.assertRaises(ValueError):export_packets(pair,Path(temp)/"formal","formal")

    def test_comparison_interface_uses_matched_physical_inputs(self):
        with tempfile.TemporaryDirectory() as temp:
            output=Path(temp)/"compare"
            result=comparison(self.records,self.config,{"model":None},output)
            self.assertEqual(result["model_calls"],0)
            pairs=read(output/"paired-requests.json")
            self.assertEqual(len(pairs),16)
            for pair in pairs:
                self.assertIsNone(pair["alternative"])
                source=next(r for r in self.records if r["sample_id"]==pair["sample_id"])
                self.assertEqual(pair["physical_input_sha256"],digest(project(source)))

if __name__=="__main__":unittest.main()
