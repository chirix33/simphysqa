"""SPQ01a real preservation checks and LABELED SYNTHETIC schedule fixtures.

Synthetic states/events test software boundaries, not physical applications,
human acceptability, causal effects, or empirical annotation performance.
"""
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
from simphysqa.annotation import validate_generated
from simphysqa.dataset import load, pointer, public_record, validate
from simphysqa.event_language import CONTRACT, enrich, generator_input, identity, measurement_base, render, validate_view
from simphysqa.events import derive, LAWS
from simphysqa.io import ROOT, digest, read
from simphysqa.spq01a import run
from test_spq01 import proposal

class SPQ01aTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.path = Path(os.environ["SIMPHYSQA_SPQ01_QA"])
        cls.old_root = cls.path.parent.parent
        cls.records = list(load(cls.path))
        cls.by_domain = {r["public"]["input"]["domain"]: r for r in cls.records if r["question_type"] == "predictive"}

    def fixture(self, domain="robotic_arm", times=(0.0, 0.1, 0.2, 0.3, 0.4), start=0.1, end=0.3):
        """Software fixture: altered public timing is NEVER exported as real data."""
        inp = deepcopy(self.by_domain[domain]["public"]["input"])
        original = deepcopy(inp["states"][0])
        inp["states"] = []
        for i, time in enumerate(times):
            state = deepcopy(original)
            state.update(state_id=f"SYNTHETIC-{i}", timestamp=time)
            inp["states"].append(state)
        inp["observation_cutoff"] = times[-1]
        event = inp["known_events"][0]
        event.update(event_id="SYNTHETIC-EVENT", start_time=start, end_time=end)
        return inp

    def software_language(self, inp):
        r = {"public": {"input": inp}}
        return validate_generated(r, proposal(r))

    def test_synthetic_half_open_onset_end_before_after(self):
        inp = self.fixture()
        links = derive(inp)["state_links"]
        self.assertEqual([l["temporal_relationship"] for l in links],
            ["scheduled_future", "scheduled_active", "scheduled_active", "scheduled_interval_ended", "scheduled_interval_ended"])
        self.assertEqual([l["state_id"] for l in links], [s["state_id"] for s in inp["states"]])
        language = render(inp, self.software_language(inp))
        self.assertIn("scheduled active", language["timestamps"][1]["text"])
        self.assertNotIn("scheduled active", language["timestamps"][3]["text"])
        self.assertIn("does not establish that its physical effects have ended", language["timestamps"][3]["text"])
        self.assertNotIn("has ended", language["timestamps"][4]["text"])
        validate_view(inp, language, CONTRACT)

    def test_synthetic_exact_matching_no_nearest_or_epsilon(self):
        inp = self.fixture(times=(0., 0.09999999999999999, 0.1, 0.2), start=0.1, end=0.2)
        self.assertEqual([l["temporal_relationship"] for l in derive(inp)["state_links"]],
            ["scheduled_future", "scheduled_future", "scheduled_active", "scheduled_interval_ended"])

    def test_synthetic_overlapping_events_are_independent(self):
        inp = self.fixture()
        other = deepcopy(inp["known_events"][0])
        other.update(event_id="SYNTHETIC-SECOND", start_time=.2, end_time=.4)
        inp["known_events"].append(other)
        links = derive(inp)["state_links"]
        active = [l for l in links if l["timestamp"] == .2 and l["temporal_relationship"] == "scheduled_active"]
        self.assertEqual({l["event_id"] for l in active}, {"SYNTHETIC-EVENT", "SYNTHETIC-SECOND"})
        language = render(inp, self.software_language(inp))
        claims = language["timestamps"][2]["claims"]
        self.assertEqual(sum(c["kind"] == "event_schedule" for c in claims), 2)

    def test_synthetic_event_entirely_between_states_no_boundary_state(self):
        inp = self.fixture(times=(0., .2, .4), start=.25, end=.35)
        context = derive(inp)
        self.assertEqual([l["temporal_relationship"] for l in context["state_links"]],
                         ["scheduled_future", "scheduled_future", "scheduled_interval_ended"])
        segment = context["between_state_links"][0]
        self.assertTrue(segment["entire_interval_between"])
        self.assertEqual(segment["state_id"], "SYNTHETIC-2")
        self.assertEqual(segment["previous_state_id"], "SYNTHETIC-1")
        self.assertEqual(segment["scheduled_overlap"], [.25, .35])
        self.assertEqual(segment["boundaries"], [{"kind": "onset", "timestamp": .25, "timestamp_decimal": "0.25", "sampled_state": False}, {"kind": "end", "timestamp": .35, "timestamp_decimal": "0.35", "sampled_state": False}])
        language = render(inp, self.software_language(inp))
        self.assertEqual(len(language["timestamps"]), 3)
        self.assertIn("Between the preceding saved state", language["timestamps"][-1]["text"])
        self.assertIn("no boundary state is invented", language["timestamps"][-1]["text"])

    def test_synthetic_sampled_boundaries_not_unsampled(self):
        context = derive(self.fixture())
        self.assertFalse(any(b["kind"] in ("onset", "end") for l in context["between_state_links"] for b in l["boundaries"]))
        self.assertEqual(len(context["between_state_links"]), 2)

    def test_synthetic_tether_positive_negative_phases_half_open(self):
        inp = self.fixture("tethered_load", times=(0., .1, .15, .2, .25, .3, .4))
        context = derive(inp)
        phases = context["events"][0]["controller"]["phases"]
        self.assertEqual([(p["start_time"], p["end_time"]) for p in phases], [(.1, .2), (.2, .3)])
        a = inp["controller"]["parameters"][2]["value"]
        self.assertEqual([p["value"] for p in phases], [a, -a])
        links = context["state_links"]
        self.assertEqual([l["scheduled_phase_id"] for l in links], [None, phases[0]["phase_id"], phases[0]["phase_id"], phases[1]["phase_id"], phases[1]["phase_id"], None, None])
        language = render(inp, self.software_language(inp))
        self.assertIn(str(-a), language["timestamps"][3]["text"])
        self.assertIn("controller_phase", str(language["timestamps"][3]["claims"]))
        inp["known_events"][0]["end_time"] = .31
        with self.assertRaisesRegex(ValueError, "duration contradicts"):
            derive(inp)

    def test_synthetic_phase_boundary_between_saved_states(self):
        inp = self.fixture("tethered_load", times=(0., .15, .25, .4))
        between = derive(inp)["between_state_links"]
        phase = [b for l in between for b in l["boundaries"] if b["kind"] == "phase_boundary"]
        self.assertEqual(phase, [{"kind": "phase_boundary", "timestamp": .2, "timestamp_decimal": "0.2", "sampled_state": False}])

    def test_synthetic_phase_decimal_boundary_is_not_rounded_for_matching(self):
        inp = self.fixture("tethered_load", times=(0., .41200000000000003, .512, .5120000000000001, .612), start=.41200000000000003, end=.612)
        context = derive(inp)
        phases = context["events"][0]["controller"]["phases"]
        self.assertEqual(phases[0]["end_time_decimal"], "0.51200000000000003")
        self.assertEqual(context["state_links"][2]["scheduled_phase_id"], phases[0]["phase_id"])
        self.assertEqual(context["state_links"][3]["scheduled_phase_id"], phases[1]["phase_id"])

    def test_synthetic_generic_magnitude_never_infers_phases_or_direction(self):
        inp = self.fixture("tethered_load")
        inp["controller"]["equations"] = ["Generic control magnitude; no phases specified."]
        context = derive(inp)
        profile = context["events"][0]["controller"]
        self.assertEqual(profile["kind"], "unresolved_declared_law")
        self.assertEqual(profile["phases"], [])
        self.assertEqual(profile["claims"], [])
        language = render(inp, self.software_language(inp))
        self.assertNotIn("negative phase", language["trajectory"]["text"])

    def test_synthetic_noninterval_completion_and_unknown_semantics(self):
        inp = self.fixture("driving", start=.2, end=.2)
        inp["known_events"][0]["type"] = "stopped"
        context = derive(inp)
        self.assertEqual([l["temporal_relationship"] for l in context["state_links"]],
            ["declared_point_future", "declared_point_future", "declared_point_at_timestamp", "declared_point_past", "declared_point_past"])
        self.assertIn("earliest end", context["events"][0]["point_definition"])
        self.assertEqual(context["events"][0]["target_entity_ids"], [])
        language = render(inp, self.software_language(inp))
        self.assertIn("not an active interval", language["timestamps"][2]["text"])
        inp["known_events"][0].update(start_time=.15, end_time=.15)
        context = derive(inp)
        self.assertEqual(context["between_state_links"][0]["temporal_relationship"], "point_between_saved_states")
        inp["known_events"][0]["type"] = "unknown-event"
        self.assertEqual({l["temporal_relationship"] for l in derive(inp)["state_links"]}, {"temporal_semantics_unresolved"})
        inp["known_events"][0].update(type="stopped", end_time=.25)
        with self.assertRaisesRegex(ValueError, "point event"):
            derive(inp)

    def test_synthetic_empty_interval_never_active(self):
        inp = self.fixture(start=.2, end=.2)
        self.assertNotIn("scheduled_active", [l["temporal_relationship"] for l in derive(inp)["state_links"]])
        self.assertEqual(derive(inp)["between_state_links"], [])

    def test_whole_state_targets_not_focal_and_context_not_direct(self):
        for domain, target, focal in (("object_pushing_stacking", "block_1", "block_2"), ("tethered_load", "support", "load")):
            inp = self.by_domain[domain]["public"]["input"]
            link = derive(inp)["state_links"][-1]
            self.assertEqual(link["target_entity_ids"], [target])
            self.assertIn(focal, link["contextual_entity_ids"])
            self.assertTrue(link["measurement_matches"])
            self.assertTrue(all(pointer(inp, b)["entity_id"] == target for b in link["measurement_matches"]))
            self.assertTrue(link["controller_matches"])
            self.assertTrue(all(pointer(inp, b)["entity_id"] == target for b in link["controller_matches"]))

    def test_real_controller_limits_additive_units_frames_separate_claims(self):
        arm = enrich(self.by_domain["robotic_arm"])["public"]["annotations"]
        self.assertIn("additive control, not total", arm["trajectory"]["text"])
        self.assertIn("joint_local", arm["trajectory"]["text"])
        self.assertIn("source frame world", arm["trajectory"]["text"])
        driving = enrich(self.by_domain["driving"])["public"]["annotations"]
        self.assertIn("maximum torque limit 0.25 N*m", driving["trajectory"]["text"])
        self.assertIn("realized applied torque is not specified", driving["trajectory"]["text"])
        for domain in self.by_domain:
            original = self.by_domain[domain]
            out = enrich(original)
            self.assertEqual(out["private"]["annotation_provenance"], original["private"]["annotation_provenance"])
            claims = out["public"]["annotations"]["trajectory"]["claims"]
            self.assertEqual(claims[0]["kind"], "measurement")
            self.assertTrue(any(c["kind"] == "event_schedule" for c in claims))
            self.assertTrue(any(c["kind"] == "controller_definition" for c in claims))
            for c in claims:
                self.assertTrue(c["bindings"])
                for b in c["bindings"]:
                    pointer(original["public"]["input"], b)

    def test_real_no_active_gap_summary_once_final_note_cutoffs_unchanged(self):
        total = Counter()
        for r in self.records:
            out = enrich(r)
            inp = out["public"]["input"]
            self.assertEqual(inp, r["public"]["input"])
            self.assertEqual(inp["observation_cutoff"], .2)
            context = out["public"]["annotations"]["event_context"]["links"]
            total.update(l["temporal_relationship"] for l in context["state_links"])
            self.assertEqual(context["between_state_links"], [])
            self.assertIn("no saved observed state has active overlap", out["public"]["annotations"]["trajectory"]["text"])
            sentences = out["public"]["annotations"]["timestamps"]
            self.assertIn("not yet started", sentences[-1]["text"])
            self.assertFalse(any("not yet started" in s["text"] for s in sentences[:-1]))
            self.assertEqual([(s["state_id"],s["timestamp"]) for s in sentences], [(s["state_id"],s["timestamp"]) for s in inp["states"]])
        self.assertEqual(total, {"scheduled_future": 352})  # paired QA; deduplicated physical count=176

    def test_real_reference_answer_identity_exact_all_32(self):
        for r in self.records:
            out = enrich(r)
            validate(out)
            self.assertEqual(out["sample_id"], r["sample_id"])
            self.assertEqual(out["source"], r["source"])
            self.assertEqual(out["private"]["reference"], r["private"]["reference"])
            self.assertEqual(out["private"]["evidence_bindings"], r["private"]["evidence_bindings"])
            self.assertEqual(out["completion"], r["completion"])
            self.assertEqual(measurement_base(out["public"]["annotations"]), r["public"]["annotations"])

    def test_public_construction_does_not_read_private_outcomes(self):
        class Poison(dict):
            def __getitem__(self, key):
                raise AssertionError("PRIVATE access")
            def __deepcopy__(self, memo):
                return Poison()
        r = deepcopy(self.by_domain["driving"])
        view = generator_input(r["public"]["input"])
        language = enrich(r)["public"]["annotations"]
        r["private"] = Poison()
        # Construction helpers receive only public input. Even the enrichment
        # wrapper can copy private metadata without reading reference fields.
        self.assertEqual(generator_input(r["public"]["input"]), view)
        self.assertEqual(render(r["public"]["input"], r["public"]["annotations"]), language)
        serialized = str(view) + str(language)
        self.assertNotIn("reference", view["public_input"])
        self.assertNotIn("private", view["public_input"])
        self.assertNotIn("structured_label", serialized)
        self.assertNotIn("solution_trace", serialized)

    def test_malformed_leaked_claims_stale_versions_and_links_rejected(self):
        r = enrich(self.by_domain["driving"])
        for mutate in (
            lambda x: x["public"]["annotations"]["trajectory"]["claims"][-1].update(text="It will stop at 999 s."),
            lambda x: x["public"]["annotations"]["timestamps"][-1].update(text="The outcome is 999."),
            lambda x: x["public"]["annotations"]["event_context"]["versions"].update(matching_rules_version="stale"),
            lambda x: x["public"]["annotations"]["event_context"]["links"]["state_links"][-1].update(temporal_relationship="scheduled_active"),
            lambda x: x["public"]["annotations"]["timestamps"][-1]["claims"][-1].update(bindings=["/reference/events/0"]),
            lambda x: x.update(annotation_version="legacy-unenriched/0"),
            lambda x: x["public"]["annotations"].pop("event_context"),
        ):
            bad = deepcopy(r)
            mutate(bad)
            with self.assertRaises((ValueError, KeyError, __import__("jsonschema").exceptions.ValidationError)):
                validate(bad)
        with self.assertRaises(ValueError):
            enrich(r)

    def test_cache_identity_contains_rules_schema_prompt_and_full_entities(self):
        r = self.by_domain["driving"]
        inp = r["public"]["input"]
        base = r["public"]["annotations"]
        key = identity(inp, base)
        inp = deepcopy(inp)
        inp["known_events"][0]["start_time"] += .01
        self.assertNotEqual(key, identity(inp, base))
        inp = deepcopy(r["public"]["input"])
        inp["entities"][-1]["type"] += "-SYNTHETIC"
        self.assertNotEqual(key, identity(inp, base))
        with patch("simphysqa.event_language.versions", return_value={"annotation_contract_version": "test-changed"}):
            self.assertNotEqual(key, identity(r["public"]["input"], base))

    def test_export_resume_blanking_and_baselines_without_network_or_overwrite(self):
        summary = self.old_root / "annotation-job/summaries/002.json"
        packets = self.old_root / "development/audit-development"
        with tempfile.TemporaryDirectory() as tmp, patch("socket.socket.connect", side_effect=AssertionError("network forbidden")):
            output = Path(tmp) / "event-v2"
            with redirect_stdout(io.StringIO()):
                report = run(self.path, summary, packets, output, ROOT / "configs/simphysqa/evaluation.json", ROOT / "configs/simphysqa/annotation_spq01a.json")
            hashes = {p.relative_to(output).as_posix(): sha256(p.read_bytes()).hexdigest() for p in output.rglob("*") if p.is_file()}
            with redirect_stdout(io.StringIO()):
                resumed = run(self.path, summary, packets, output, ROOT / "configs/simphysqa/evaluation.json", ROOT / "configs/simphysqa/annotation_spq01a.json")
            self.assertEqual(report, resumed)
            self.assertEqual(hashes, {p.relative_to(output).as_posix(): sha256(p.read_bytes()).hexdigest() for p in output.rglob("*") if p.is_file()})
            self.assertEqual(report["baseline_requests"], 288)
            self.assertEqual(report["blank_rating_imports"], [{"reviewer": reviewer, "collected": 0, "blank": 32} for reviewer in ("R1", "R2", "R3")])
            self.assertEqual(read(output / "coverage.json")["real_active_overlap"], 0)
            self.assertEqual(read(output / "organizer-private/accounting.json")["cumulative_estimated_spend_usd"], .522767)
            files = list((output / "baseline-requests").glob("*.json"))
            for path in files:
                if path.name == "manifest.json": continue
                requests = read(path)
                self.assertEqual(len(requests), 32)
                for request in requests:
                    self.assertEqual(request["tools"], [])
                    text = request["messages"][0]["content"]
                    self.assertIn(CONTRACT, text)
                    self.assertIn("event_context", text)
                    self.assertNotIn("annotation_provenance", text)
                    self.assertNotIn("structured_label", text)
            # Completed item tampering fails explicitly instead of regenerating.
            path = next((output / "items").glob("*.json"))
            path.write_text('{}\n')
            with self.assertRaisesRegex(ValueError, "cache identity/content mismatch"), redirect_stdout(io.StringIO()):
                run(self.path, summary, packets, output, ROOT / "configs/simphysqa/evaluation.json", ROOT / "configs/simphysqa/annotation_spq01a.json")

if __name__ == "__main__":
    unittest.main()
