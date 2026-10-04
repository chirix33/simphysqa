"""Behavioral tests on existing release records. Synthetic ratings are test inputs only."""
from copy import deepcopy
import csv
import os
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch
from jsonschema.exceptions import ValidationError
from simphysqa.audit import COLUMNS, CRITERIA, export_packets, import_ratings, preview
from simphysqa.cli import smoke
from simphysqa.dataset import SourceLocation, attach_annotation, iter_source, load, migrate, public_record, restore, validate
from simphysqa.evaluation import request
from simphysqa.scoring import distance, score
from simphysqa.io import DOMAINS, ROOT, canonical, external, read

class RealDataContractTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.data = Path(os.environ["SIMPHYSQA_DATA_ROOT"])
        cls.records = []
        cls.sources = []
        for domain in DOMAINS:
            source, location = next(iter_source(cls.data / domain / "validation"))
            cls.sources.append(source)
            cls.records.append(migrate(source, location))

    def test_exact_ids_reference_and_provenance_roundtrip(self):
        for source, record in zip(self.sources, self.records):
            self.assertEqual(restore(record), source)
            self.assertEqual(record["sample_id"], source["sample_id"])
            self.assertEqual(record["private"]["reference"], source["reference"])
            self.assertEqual(record["private"]["metadata"], source["metadata"])

    def test_private_mutation_does_not_change_requests(self):
        record = deepcopy(self.records[0])
        before = request(record, {"condition_id": "test-only", "reasoning": "direct"})
        record["private"]["annotation_provenance"]["model_identity"] = "PRIVATE_SENTINEL"
        after = request(record, {"condition_id": "test-only", "reasoning": "direct"})
        self.assertEqual(before, after)
        self.assertNotIn("PRIVATE_SENTINEL", str(after))
        self.assertIn('"annotations"', after["messages"][0]["content"])
        self.assertEqual(after["tools"], [])
        self.assertNotIn("reference", public_record(record))
        self.assertNotIn("source", public_record(record))

    def test_reference_changes_and_qa_relabel_fail(self):
        record = deepcopy(self.records[0])
        record["private"]["reference"]["structured_label"][0]["value"] = 999
        with self.assertRaises(ValueError):
            validate(record)
        record = deepcopy(self.records[0])
        record["question_type"] = "counterfactual"
        with self.assertRaises(ValueError):
            validate(record)

    def test_unknown_fields_and_future_annotations_rejected(self):
        record = deepcopy(self.records[0])
        record["public"]["annotations"]["private"] = {"answer": 999}
        with self.assertRaises(ValidationError):
            validate(record)
        record = deepcopy(self.records[0])
        future = record["private"]["reference"]["states"][0]
        record["public"]["annotations"]["timestamps"] = [{"status": "generated_unreviewed", "text": "Synthetic test annotation",
            "bindings": ["/states/0"], "state_id": future["state_id"], "timestamp": future["timestamp"]}]
        with self.assertRaises(ValueError):
            validate(record)

    def test_public_annotation_import_and_provenance(self):
        record = self.records[0]
        result = {"sample_id": record["sample_id"], "annotation_version": "test-only/1",
                  "annotations": {"trajectory": {"status": "generated_unreviewed", "text": "Synthetic test text",
                      "bindings": ["/states/0/measurements/0"]}, "timestamps": []},
                  "provenance": {"status": "generated_unreviewed", "model_identity": "synthetic-test-only",
                      "prompt_version": "test-only/1", "schema_version": record["schema_version"],
                      "generation_settings": {"temperature": 0}, "validation_failures": [], "attempts": [{"test_only": True}],
                      "retries": 0, "repairs": 0}}
        enriched = attach_annotation(record, result)
        self.assertEqual(restore(enriched), restore(record))
        self.assertIn("Synthetic test text", request(enriched, {"condition_id": "test-only", "reasoning": "direct"})["messages"][0]["content"])
        result["provenance"]["model_identity"] = None
        with self.assertRaises(ValueError):
            attach_annotation(record, result)

    def test_evidence_wrong_time_rejected(self):
        record = deepcopy(self.records[0])
        record["private"]["evidence_bindings"][0]["state_ids"] = [record["public"]["input"]["states"][0]["state_id"]]
        with self.assertRaises(ValueError):
            validate(record)

    def test_sampling_disjoint_groups_and_no_formal_export(self):
        duplicated_group = deepcopy(self.records[0])
        # Same item in frame must fail rather than silently overrepresent its group.
        with self.assertRaises(ValueError):
            preview(self.records + [duplicated_group], 7)
        report = preview(self.records, 7, 2, 2)
        self.assertEqual(report, preview(self.records, 7, 2, 2))
        self.assertEqual(report["available_preview"], {"calibration": 2, "formal": 2})
        self.assertNotIn("formal_ids", report)
        excluded = preview(self.records, 7, 2, 2, (self.records[0]["trajectory_id"],))
        self.assertEqual(excluded["eligible_groups"], 3)
        with tempfile.TemporaryDirectory() as tmp:
            with self.assertRaises(ValueError):
                export_packets(self.records, Path(tmp) / "formal", "formal")

    def test_packets_blank_forms_and_immutable_import(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            packets = export_packets(self.records, root / "packets")
            self.assertNotIn("annotation_provenance", str(read(next((packets / "packets").glob("*.json")))))
            result = import_ratings(packets, packets / "forms/R1.csv", root / "original.json")
            self.assertEqual(result["collected"], 0)
            self.assertEqual(result["blank"], 4)
            with self.assertRaises(FileExistsError):
                import_ratings(packets, packets / "forms/R1.csv", root / "original.json")

    def test_synthetic_rating_import_and_assignment_validation(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            packets = export_packets(self.records, root / "packets")
            with (packets / "forms/R2.csv").open(newline="", encoding="utf-8") as stream:
                rows = list(csv.DictReader(stream))
            rows[0].update(judgment="material_error", criteria=";".join(k + "=material_error" for k in CRITERIA),
                           error_categories="missing_annotation", notes="SYNTHETIC TEST INPUT, NOT A HUMAN RATING")
            edited = root / "synthetic-only.csv"
            def save():
                with edited.open("w", newline="", encoding="utf-8") as stream:
                    writer = csv.DictWriter(stream, fieldnames=COLUMNS)
                    writer.writeheader()
                    writer.writerows(rows)
            save()
            result = import_ratings(packets, edited, root / "synthetic-import.json")
            self.assertEqual(result["collected"], 1)
            self.assertEqual(result["blank"], 3)
            self.assertEqual(result["kind"], "original_independent")
            rows[0]["sample_id"] = "wrong-assignment"
            save()
            with self.assertRaises(ValueError):
                import_ratings(packets, edited, root / "rejected.json")

    def test_packet_tampering_rejected(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            packets = export_packets(self.records, root / "packets")
            (packets / "rubric.txt").write_text("changed", encoding="utf-8")
            with self.assertRaises(ValueError):
                import_ratings(packets, packets / "forms/R1.csv", root / "rejected.json")

    def test_output_roots_are_external(self):
        with self.assertRaises(ValueError):
            external(ROOT / "outputs" / "new")
        with self.assertRaises(ValueError):
            external(ROOT)

    def test_smoke_has_no_network_and_loads_migrated_records(self):
        with tempfile.TemporaryDirectory() as tmp, patch("socket.socket.connect", side_effect=AssertionError("network forbidden")):
            output = Path(tmp) / "smoke"
            result = smoke(self.data, output, ROOT / "configs/simphysqa/evaluation.json")
            self.assertEqual(result["domains"], 4)
            self.assertEqual(result["model_calls"], 0)
            self.assertEqual(result["human_ratings_collected"], 0)
            migrated = list(load(output / "records.jsonl"))
            self.assertEqual([r["sample_id"] for r in migrated], [r["sample_id"] for r in self.records])


    def test_private_scoring_preserves_failure_denominators(self):
        record = self.records[0]
        condition = "synthetic-only"
        prediction = {"sample_id": record["sample_id"], "condition_id": condition,
            "annotation_version": record["annotation_version"], "status": "completed",
            "targets": deepcopy(record["private"]["reference"]["structured_label"])}
        result = score(self.records, [prediction], [condition])
        self.assertEqual(sum(v["examples"] for v in result["tables"]), 4)
        self.assertEqual(sum(v["whole_question_correct"] for v in result["tables"]), 1)
        self.assertEqual(sum(v["status_counts"]["missing"] for v in result["tables"]), 3)
        self.assertEqual(result["uncertainty"]["status"], "pending_analysis_freeze")
        self.assertEqual(result["model_calls"], 0)
        prediction["targets"][0]["unit"] = "wrong"
        result = score([record], [prediction], [condition])
        self.assertEqual(result["items"][0]["valid_targets"], len(prediction["targets"])-1)
        self.assertFalse(result["items"][0]["whole_question_correct"])

    def test_boolean_and_quaternion_metrics(self):
        target = {"answer_type":"boolean","unit":"1"}
        with self.assertRaises(ValueError):
            distance(1, True, target)
        target = {"answer_type":"vector","quantity":"orientation","unit":"1",
            "absolute_tolerance":.01,"relative_tolerance":0}
        error, ok, unit = distance([0,0,0,-1], [0,0,0,1], target)
        self.assertEqual(error, 0)
        self.assertTrue(ok)
        self.assertEqual(unit, "rad")
        with self.assertRaises(ValueError):
            distance([0,0,0,0], [0,0,0,1], target)

    def test_scoring_rejects_annotation_version_mismatch(self):
        record = self.records[0]
        prediction = {"sample_id": record["sample_id"], "condition_id": "synthetic-only",
            "annotation_version": "wrong-version", "status":"failed","targets":[]}
        with self.assertRaises(ValueError):
            score([record], [prediction], ["synthetic-only"])

if __name__ == "__main__":
    unittest.main()
