"""Real bidirectional preservation checks; synthetic schedules are software fixtures."""
from collections import Counter
from contextlib import redirect_stdout
from copy import deepcopy
from hashlib import sha256
import io
import os
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch
from jsonschema.exceptions import ValidationError
from simphysqa.associations import VERSION, _project, associated_view, strip_associations, validate_input, validate_view
from simphysqa.dataset import load, public_record
from simphysqa.events import derive
from simphysqa.export_associations import run
from simphysqa.io import canonical, digest, read
from simphysqa.evaluation import request

class AssociationTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.root=Path(os.environ["SIMPHYSQA_SPQ01A_ROOT"])
        cls.records=list(load(cls.root / "qa-records.jsonl"))
        cls.by_domain={r["public"]["input"]["domain"]:r for r in cls.records if r["question_type"]=="predictive"}

    def fixture(self, times=(0.,.1,.2,.3), start=.1, end=.2, domain="robotic_arm"):
        inp=deepcopy(self.by_domain[domain]["public"]["input"])
        state=deepcopy(inp["states"][0])
        inp["states"]=[]
        for i,t in enumerate(times):
            item=deepcopy(state)
            item.update(state_id=f"SYNTHETIC-{i}",timestamp=t)
            inp["states"].append(item)
        inp["observation_cutoff"]=times[-1]
        inp["known_events"][0].update(event_id="SYNTHETIC-EVENT",start_time=start,end_time=end)
        return inp

    def project_fixture(self,inp):
        links=derive(inp)
        result=_project(inp,links)
        validate_input(inp,links,result)
        return links,result

    def test_all_real_views_complete_mirrors_and_lossless_nonrecursive(self):
        for record in self.records:
            original=deepcopy(record)
            base=public_record(record)
            result=public_record(record,association_version=VERSION)
            self.assertEqual(record,original)
            self.assertEqual(strip_associations(result["input"]),base["input"])
            self.assertEqual(result["annotations"],base["annotations"])
            self.assertEqual(result["sample_id"],record["sample_id"])
            self.assertEqual(result["input"]["observation_cutoff"],.2)
            self.assertNotIn("private",result)
            self.assertNotIn("source_record",str(result))
            for state in result["input"]["states"]:
                self.assertEqual(len(state["linked_events"]),1)
                entry=state["linked_events"][0]
                self.assertEqual(entry["temporal_relationship"],"scheduled_future")
                self.assertEqual(set(entry),{"event_id","event_type","temporal_relationship","target_entity_ids","link_id","bindings"})
                event=next(e for e in result["input"]["known_events"] if e["event_id"]==entry["event_id"])
                mirror=next(s for s in event["linked_states"] if s["state_id"]==state["state_id"])
                self.assertEqual(set(mirror),{"state_id","link_id","temporal_relationship","bindings"})
                self.assertEqual([mirror[k] for k in ("link_id","temporal_relationship","bindings")],[entry[k] for k in ("link_id","temporal_relationship","bindings")])
                canonical_link=next(l for l in base["annotations"]["event_context"]["links"]["state_links"] if l["link_id"]==entry["link_id"])
                self.assertEqual(entry["target_entity_ids"],canonical_link["target_entity_ids"])
            validate_view(base,result)

    def test_default_exports_remain_legacy_opt_in_version_is_explicit(self):
        record=self.records[0]
        self.assertNotIn("linked_events",public_record(record)["input"]["states"][0])
        self.assertIn("linked_events",public_record(record,association_version=VERSION)["input"]["states"][0])
        with self.assertRaises(ValueError):
            public_record(record,association_version="unsupported")
        with self.assertRaises(ValueError):
            associated_view(public_record(record,association_version=VERSION))

    def test_synthetic_interval_onset_end_and_overlap_semantics_preserved(self):
        inp=self.fixture()
        second=deepcopy(inp["known_events"][0])
        second.update(event_id="SYNTHETIC-SECOND",start_time=.2,end_time=.3)
        inp["known_events"].append(second)
        links,result=self.project_fixture(inp)
        self.assertEqual([s["linked_events"][0]["temporal_relationship"] for s in result["states"]],
                         ["scheduled_future","scheduled_active","scheduled_interval_ended","scheduled_interval_ended"])
        self.assertEqual(result["states"][2]["linked_events"][1]["temporal_relationship"],"scheduled_active")
        self.assertEqual(len(links["state_links"]),8)

    def test_synthetic_gap_separate_endpoints_no_active_assignment(self):
        inp=self.fixture(times=(0.,.2,.4),start=.25,end=.35)
        links,result=self.project_fixture(inp)
        between=result["between_state_associations"]
        self.assertEqual(len(between),1)
        self.assertEqual(between[0]["endpoint_state_ids"],["SYNTHETIC-1","SYNTHETIC-2"])
        self.assertEqual(between[0]["temporal_relationship"],"interval_between_saved_states")
        self.assertEqual(between[0]["link_id"],links["between_state_links"][0]["link_id"])
        self.assertNotIn("endpoint_relationship",between[0])
        self.assertEqual(result["states"][1]["linked_events"][0]["temporal_relationship"],"scheduled_future")
        self.assertEqual(result["states"][2]["linked_events"][0]["temporal_relationship"],"scheduled_interval_ended")
        self.assertFalse(any(e["temporal_relationship"]=="scheduled_active" for s in result["states"] for e in s["linked_events"]))
        self.assertEqual(len(result["states"]),3)

    def test_synthetic_point_and_phase_semantics_are_copied(self):
        inp=self.fixture(times=(0.,.1,.2),start=.15,end=.15,domain="driving")
        inp["known_events"][0]["type"]="stopped"
        links,result=self.project_fixture(inp)
        self.assertEqual([s["linked_events"][0]["temporal_relationship"] for s in result["states"]],
                         ["declared_point_future","declared_point_future","declared_point_past"])
        self.assertEqual(result["between_state_associations"][0]["temporal_relationship"],"point_between_saved_states")
        self.assertEqual(result["states"][0]["linked_events"][0]["target_entity_ids"],[])
        inp=self.fixture(times=(0.,.1,.2,.3),start=.1,end=.3,domain="tethered_load")
        links,result=self.project_fixture(inp)
        self.assertEqual([s["linked_events"][0]["link_id"] for s in result["states"]],[l["link_id"] for l in links["state_links"]])
        self.assertEqual(links["state_links"][1]["scheduled_phase_id"],"SYNTHETIC-EVENT/phase-1")
        self.assertEqual(links["state_links"][2]["scheduled_phase_id"],"SYNTHETIC-EVENT/phase-2")

    def test_synthetic_no_events_empty_intervals_and_unknown_types(self):
        inp=self.fixture()
        inp["known_events"]=[]
        _,result=self.project_fixture(inp)
        self.assertTrue(all(s["linked_events"]==[] for s in result["states"]))
        self.assertEqual(result["known_events"],[])
        self.assertEqual(result["between_state_associations"],[])
        inp=self.fixture(start=.1,end=.1)
        _,result=self.project_fixture(inp)
        self.assertNotIn("scheduled_active",str(result["states"]))
        inp["known_events"][0]["type"]="SYNTHETIC-UNKNOWN"
        _,result=self.project_fixture(inp)
        self.assertEqual({s["linked_events"][0]["temporal_relationship"] for s in result["states"]},{"temporal_semantics_unresolved"})

    def test_dangling_duplicate_missing_and_mismatched_directions_rejected(self):
        inp=self.records[0]["public"]["input"]
        links=self.records[0]["public"]["annotations"]["event_context"]["links"]
        result=_project(inp,links)
        mutations=(
            lambda r:r["states"][0]["linked_events"][0].update(event_id="dangling"),
            lambda r:r["known_events"][0]["linked_states"][0].update(state_id="dangling"),
            lambda r:r["states"][0]["linked_events"].append(deepcopy(r["states"][0]["linked_events"][0])),
            lambda r:r["known_events"][0]["linked_states"].append(deepcopy(r["known_events"][0]["linked_states"][0])),
            lambda r:r["known_events"][0]["linked_states"].pop(),
            lambda r:r["known_events"][0]["linked_states"][0].update(temporal_relationship="scheduled_active"),
            lambda r:r["known_events"][0]["linked_states"][0].update(link_id="wrong"),
            lambda r:r["states"][0]["linked_events"][0].update(event_type="wrong"),
            lambda r:r["states"][0]["linked_events"][0].update(target_entity_ids=["wrong"]),
        )
        for mutate in mutations:
            bad=deepcopy(result); mutate(bad)
            with self.assertRaises((ValueError,ValidationError)):
                validate_input(inp,links,bad)

    def test_consistent_but_noncanonical_relationships_and_bindings_rejected(self):
        inp=self.records[0]["public"]["input"]
        links=self.records[0]["public"]["annotations"]["event_context"]["links"]
        for replacement in ({"temporal_relationship":"scheduled_active"},{"bindings":["/private/reference"]},{"link_id":"forged"}):
            result=_project(inp,links)
            result["states"][0]["linked_events"][0].update(replacement)
            result["known_events"][0]["linked_states"][0].update(replacement)
            with self.assertRaisesRegex(ValueError,"canonical"):
                validate_input(inp,links,result)
        bad=deepcopy(links)
        bad["state_links"][0]["temporal_relationship"]="scheduled_active"
        with self.assertRaisesRegex(ValueError,"canonical"):
            validate_input(inp,bad,_project(inp,bad))

    def test_between_endpoints_duplicates_and_active_labels_rejected(self):
        inp=self.fixture(times=(0.,.2,.4),start=.25,end=.35)
        links,result=self.project_fixture(inp)
        for mutate in (
            lambda r:r["between_state_associations"][0].update(endpoint_state_ids=["SYNTHETIC-0","SYNTHETIC-2"]),
            lambda r:r["between_state_associations"][0].update(endpoint_state_ids=["SYNTHETIC-2","SYNTHETIC-1"]),
            lambda r:r["between_state_associations"][0].update(temporal_relationship="scheduled_active"),
            lambda r:r["between_state_associations"].append(deepcopy(r["between_state_associations"][0])),
        ):
            bad=deepcopy(result); mutate(bad)
            with self.assertRaises((ValueError,ValidationError)):
                validate_input(inp,links,bad)

    def test_recursive_embeddings_physical_changes_and_stale_versions_rejected(self):
        record=self.records[0]
        base=public_record(record)
        good=associated_view(base)
        for mutate in (
            lambda v:v["input"]["states"][0]["linked_events"][0].update(linked_states=[]),
            lambda v:v["input"]["known_events"][0]["linked_states"][0].update(state={}),
            lambda v:v["input"]["states"][0]["measurements"][0].update(value=999),
            lambda v:v["input"].update(observation_cutoff=999),
            lambda v:v["input"]["known_events"][0].update(start_time=0),
            lambda v:v["annotations"]["trajectory"].update(text="PRIVATE future outcome 999"),
            lambda v:v.update(export_version="stale"),
            lambda v:v["association_provenance"].update(association_schema_sha256="stale"),
        ):
            bad=deepcopy(good); mutate(bad)
            with self.assertRaises((ValueError,ValidationError)):
                validate_view(base,bad)

    def test_json_boolean_number_type_changes_are_not_equal_source_data(self):
        record=self.by_domain["driving"]
        base=public_record(record)
        good=associated_view(base)
        for field in ("boolean_measurement", "numeric_timestamp"):
            bad=deepcopy(good)
            if field=="boolean_measurement":
                measured=next(m for m in bad["input"]["states"][0]["measurements"] if type(m["value"]) is bool)
                measured["value"]=int(measured["value"])
            else:
                bad["input"]["states"][0]["timestamp"]=False
            with self.assertRaisesRegex(ValueError,"physical input"):
                validate_view(base,bad)
        links=deepcopy(base["annotations"]["event_context"]["links"])
        links["state_links"][0]["timestamp"]=False
        with self.assertRaisesRegex(ValueError,"canonical SPQ01a"):
            validate_input(base["input"],links,_project(base["input"],links))

    def test_baseline_private_isolation_and_version_presence(self):
        r=deepcopy(self.records[0])
        q=request(r,{"condition_id":"test","reasoning":"direct"},association_version=VERSION)
        r["private"]["annotation_provenance"]["model_identity"]="PRIVATE_SENTINEL"
        self.assertEqual(q,request(r,{"condition_id":"test","reasoning":"direct"},association_version=VERSION))
        self.assertEqual(q["tools"],[])
        self.assertIn(VERSION,q["messages"][0]["content"])
        self.assertNotIn("PRIVATE_SENTINEL",str(q))
        self.assertNotIn("structured_label",str(q))

    def test_saved_export_packets_baselines_blanks_resume_and_prior_preservation(self):
        before={p.relative_to(self.root).as_posix():sha256(p.read_bytes()).hexdigest() for p in self.root.rglob("*") if p.is_file()}
        with tempfile.TemporaryDirectory() as tmp, patch("socket.socket.connect",side_effect=AssertionError("no network")):
            output=Path(tmp)/"associations"
            with redirect_stdout(io.StringIO()):
                report=run(self.root,output)
            self.assertEqual(report["baseline_public_views_checked"],288)
            self.assertEqual(report["deduplicated_state_event_associations"],176)
            self.assertEqual(report["deduplicated_between_state_associations"],0)
            self.assertEqual((output/"qa-records.jsonl").read_bytes(),(self.root/"qa-records.jsonl").read_bytes())
            snapshots={p.relative_to(output).as_posix():sha256(p.read_bytes()).hexdigest() for p in output.rglob("*") if p.is_file()}
            with redirect_stdout(io.StringIO()):
                self.assertEqual(run(self.root,output),report)
            self.assertEqual(snapshots,{p.relative_to(output).as_posix():sha256(p.read_bytes()).hexdigest() for p in output.rglob("*") if p.is_file()})
            for reviewer in ("R1","R2","R3"):
                imported=read(output/"verification"/(reviewer+"-blank-import.json"))
                self.assertEqual((imported["collected"],imported["blank"]),(0,32))
            old_ids={a["packet_id"] for a in read(self.root/"audit-development/manifest.json")["assignments"]}
            new_ids={a["packet_id"] for a in read(output/"audit-development/manifest.json")["assignments"]}
            self.assertTrue(old_ids.isdisjoint(new_ids))
        self.assertEqual(before,{p.relative_to(self.root).as_posix():sha256(p.read_bytes()).hexdigest() for p in self.root.rglob("*") if p.is_file()})

if __name__=="__main__":
    unittest.main()
