"""Offline behavior checks against saved admitted examples; no provider/physics calls."""
import json
import os
from copy import deepcopy
from pathlib import Path
import tempfile
import unittest
from simphysqa.answer_annotations import comparison, enriched_reference, render, validate_answer_annotation
from simphysqa.dataset import load, public_record, validate
from simphysqa.io import canonical, digest, read
from simphysqa.spq01a import retained, verify_manifest

class AnswerAnnotationTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        value=os.environ.get("SIMPHYSQA_ANSWER_EXPORT")
        if not value:raise unittest.SkipTest("set SIMPHYSQA_ANSWER_EXPORT to saved offline development export")
        cls.root=Path(value)
        cls.records=[json.loads(l) for l in (cls.root/"organizer-private/qa-records.jsonl").read_text(encoding="utf-8").splitlines()]

    def test_all_families_domains_targets_and_raw_source_recovery(self):
        self.assertEqual(len(self.records),40)
        self.assertEqual(len({(r["question_type"],r["public"]["input"]["domain"]) for r in self.records}),12)
        for r in self.records:
            a=r["private"]["answer_annotation"]
            self.assertEqual([t["target_id"] for t in a["targets"]],[t["target_id"] for t in r["public"]["input"]["answer_spec"]])
            original=deepcopy(r);original["private"].pop("answer_annotation")
            self.assertEqual(digest(original),a["parent_record_sha256"])
            self.assertEqual(r["public"]["input"]["observation_cutoff"],.2)
            for t in a["targets"]:
                label=next(l for l in r["private"]["reference"]["structured_label"] if l["target_id"]==t["target_id"])
                self.assertEqual(canonical(t["value"]),canonical(label["value"]))
                self.assertTrue(t["solution_trace"]["verification_record"]["bindings"])

    def test_direct_trace_requires_only_observed_public_evidence(self):
        for r in self.records:
            if r["question_type"]!="direct":continue
            a=r["private"]["answer_annotation"]
            self.assertFalse(a["evidence_context"]["runs"])
            for t in a["targets"]:
                self.assertEqual(len(t["solution_trace"]["steps"]),3)
                self.assertFalse(t["solution_trace"]["verification_record"]["simulation_required"])
                self.assertEqual({b["namespace"] for part in t["claims"]+t["solution_trace"]["steps"] for b in part["bindings"]},{"public"})

    def test_predictive_replay_coverage_is_truthful_and_case_specific(self):
        preds=[r for r in self.records if r["question_type"]=="predictive"]
        self.assertEqual(sum(bool(r["private"]["answer_annotation"]["evidence_context"]["runs"]) for r in preds),8)
        self.assertEqual(len({enriched_reference(r)["explanation"] for r in preds}),16)
        for r in preds:
            for t in r["private"]["answer_annotation"]["targets"]:
                self.assertEqual(len(t["solution_trace"]["steps"]),6)
                if t["target"]["answer_type"]=="boolean":
                    claim=next(c for c in t["claims"] if c["kind"]=="boolean_rule")
                    self.assertIn(t["target"]["rule_definition"],claim["text"])
                    self.assertTrue(any(b["pointer"]=="/reference/events" for b in claim["bindings"]))

    def test_counterfactual_omissions_namespaces_and_own_target(self):
        for r in self.records:
            if r["question_type"]!="counterfactual":continue
            a=r["private"]["answer_annotation"];self.assertEqual(len(a["targets"]),1)
            t=a["targets"][0]
            self.assertEqual(len(t["solution_trace"]["steps"]),6)
            self.assertIn("omitting scheduled event",t["solution_trace"]["steps"][0]["text"])
            claim=next(c for c in t["claims"] if c["kind"]=="matched_comparison")
            self.assertTrue({"factual","alternative","public"}<={b["namespace"] for b in claim["bindings"]})
            self.assertIn("do not establish absence",claim["text"])
            control=next(c for c in t["claims"] if c["kind"]=="effective_control")
            d=r["public"]["input"]["domain"]
            self.assertIn({"robotic_arm":"joint_2 base torque","driving":"maximum torque limit","object_pushing_stacking":"block_1","tethered_load":"subsequent prescribed displacement"}[d],control["text"])

    def test_multi_target_alternatives_cover_each_source_target(self):
        paths=list((self.root/"organizer-private/alternative-records").glob("*.json"));self.assertEqual(len(paths),8)
        for path in paths:
            x=read(path);self.assertEqual(digest(x["source_record"]),x["source_record_sha256"])
            r=x["annotation_projection"];validate_answer_annotation(r)
            self.assertEqual([t["target_id"] for t in r["private"]["answer_annotation"]["targets"]],[t["target_id"] for t in x["source_record"]["input"]["answer_spec"]])
            self.assertEqual(x["reference"]["structured_label"],x["source_record"]["reference"]["structured_label"])

    def test_tampered_claim_binding_run_value_and_context_are_rejected(self):
        original=next(r for r in self.records if r["question_type"]=="counterfactual")
        for change in ("text","binding","run","value","receipt"):
            r=deepcopy(original);t=r["private"]["answer_annotation"]["targets"][0]
            if change=="text":t["claims"][0]["text"]="Invented causation unsupported by saved evidence."
            elif change=="binding":t["claims"][0]["bindings"][0]["pointer"]="/states/99999"
            elif change=="run":t["run_id"]="wrong-world"
            elif change=="value":t["value"]=0
            else:r["private"]["answer_annotation"]["evidence_context"]["verification"]["additional_exact_replay"]["passed"]=False
            with self.assertRaises((ValueError,KeyError,IndexError)):validate_answer_annotation(r)

    def test_equality_difference_and_scoring_are_distinct(self):
        number={"answer_type":"number","quantity":"angle","unit":"rad","absolute_tolerance":.01,"relative_tolerance":0}
        c=comparison(1.,1.001,number);self.assertFalse(c["exact_canonical_equality"]);self.assertTrue(c["factual_answer_passes_alternative_scorer"]);self.assertGreater(c["scorer_error"],0)
        boolean={**number,"answer_type":"boolean","unit":"1"}
        c=comparison(False,False,boolean);self.assertTrue(c["exact_canonical_equality"]);self.assertIsNone(c["alternative_minus_factual"])
        with self.assertRaises(ValueError):comparison(0,False,boolean)

    def test_public_requests_have_exact_accepted_projection_and_no_gold(self):
        expected={r["sample_id"]:public_record(r,association_version="simphysqa-associations/1.1.1") for r in self.records}
        total=0
        for path in (self.root/"public-requests").glob("*.json"):
            if path.name=="manifest.json":continue
            for request in read(path):
                actual=json.loads(request["messages"][0]["content"].split("\n",1)[1])
                self.assertEqual(canonical(actual),canonical(expected[request["sample_id"]]));self.assertEqual(request["tools"],[]);total+=1
                self.assertNotIn("answer_annotation",actual);self.assertNotIn("private",actual);self.assertNotIn("solution_trace",actual)
        self.assertEqual(total,360)

    def test_resumability_verifies_existing_bytes_without_overwrite(self):
        with tempfile.TemporaryDirectory() as tmp:
            path=Path(tmp)/"item.json";value=self.records[0]
            retained(path,value);before=path.read_bytes();retained(path,value);self.assertEqual(path.read_bytes(),before)
            changed=deepcopy(value);changed["sample_id"]="other"
            with self.assertRaises(ValueError):retained(path,changed)
            self.assertEqual(path.read_bytes(),before)

    def test_cache_survives_source_line_ending_conversion(self):
        import importlib.util
        from hashlib import sha256
        import simphysqa.answer_annotations as original
        text=Path(original.__file__).read_text(encoding="utf-8")
        source=next(r for r in self.records if r["question_type"]=="direct")
        with tempfile.TemporaryDirectory() as tmp:
            path=Path(tmp)/"answer_annotations.py"
            (Path(tmp)/"answer_annotation.schema.json").write_bytes(Path(original.__file__).with_name("answer_annotation.schema.json").read_bytes())
            for content in (text,text.replace("\n","\r\n")):
                path.write_bytes(content.encode())
                spec=importlib.util.spec_from_file_location("simphysqa._newline_probe",path)
                module=importlib.util.module_from_spec(spec);spec.loader.exec_module(module)
                self.assertEqual(module.versions(),original.versions())
                self.assertEqual(canonical(module.render(source,source["private"]["answer_annotation"]["evidence_context"])),canonical(source["private"]["answer_annotation"]))

    def test_blank_forms_and_audit_references_remain_separate(self):
        pm=verify_manifest(self.root/"audit-development")
        self.assertEqual(len(pm["assignments"]),40)
        for reviewer in ("R1","R2","R3"):
            result=read(self.root/"verification"/(reviewer+"-blank-import.json"));self.assertEqual(result["collected"],0);self.assertEqual(result["blank"],40)
        r=self.records[0];p=next(p for p in pm["assignments"] if p["sample_id"]==r["sample_id"])
        packet=read(self.root/"audit-development/packets"/(p["packet_id"]+".json"))
        self.assertEqual(packet["qa"]["reference"],enriched_reference(r));self.assertIn("answer_evidence_roots",packet["verification"])
        self.assertNotEqual(packet["qa"]["reference"]["explanation"],r["private"]["reference"]["explanation"])

class PromptArchiveTests(unittest.TestCase):
    def test_actual_payload_and_per_file_generation_completeness(self):
        value=os.environ.get("SIMPHYSQA_PROMPT_ARCHIVE")
        if not value:self.skipTest("set SIMPHYSQA_PROMPT_ARCHIVE")
        root=Path(value);index=read(root/"file-generation-index.json")
        self.assertEqual(len(index["requests"]),16)
        requests={r["request_id"]:r for r in index["requests"]}
        for r in requests.values():
            body=read(root/r["payload_file"]);self.assertEqual(digest(body),r["request_sha256"])
            self.assertEqual(r["timestamp_outputs"],11);self.assertFalse(r["repair"])
            self.assertNotIn("credential",canonical(body).decode().lower())
        mapped=0
        for file in index["files"]:
            for member in file.get("mappings",[]):
                m=index.get("mapping_definitions",{}).get(member.get("mapping_id"),member)
                self.assertTrue(m["annotated_fields"])
                if m["executed_request_id"]:
                    self.assertIn(m["executed_request_id"],requests)
                    self.assertEqual(m["complete_instantiated_request"],requests[m["executed_request_id"]]["payload_file"]);mapped+=1
                self.assertEqual(len(m["field_generation"]),len(m["annotated_fields"]))
        self.assertGreater(mapped,1000)
        self.assertTrue(any(f["artifact"].startswith("SPQ02b-enriched/organizer-private/references/") for f in index["files"]))
        self.assertEqual(index["recovery"]["unavailable_executed_payloads"],0)
        catalogue=(root/"catalogue.md").read_text(encoding="utf-8");self.assertIn("Create only grounded public descriptions",catalogue)
        self.assertEqual(catalogue.count("Exact instantiated input string:"),16)

if __name__=="__main__":unittest.main()
