"""Offline behavioral tests: no network/provider calls; real native physics."""
import copy
from dataclasses import replace
import math
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch
from phi_jepa.artifacts import canonical,code_provenance
from phi_jepa.simulation.common import ROOT,read,public_record,grid_index
from phi_jepa.simulation.sampling import sample,allocation,PAIRS
from phi_jepa.simulation.numeric import Registry,text_pair,embed_pair
from phi_jepa.simulation.engines import MujocoAdapter
from phi_jepa.simulation.records import build_records
from phi_jepa.simulation.validation import validate,validate_groups,validator
from phi_jepa.simulation.pipeline import run,validate_dataset
from phi_jepa.simulation.release import release_gates

class ContractTests(unittest.TestCase):
    def setUp(self):
        self.public=public_record(read(ROOT/"example_record.json"))
        self.registry=Registry.build(self.public,"robotic_arm")

    def test_numeric_order_and_identity(self):
        changed=copy.deepcopy(self.public)
        changed["input"]["entities"].reverse()
        for st in changed["input"]["states"]: st["measurements"].reverse()
        self.assertEqual(self.registry.flatten(self.public),self.registry.flatten(changed))
        values=self.registry.flatten(self.public)
        self.assertEqual([r["value"] for r in self.registry.restore(values)],values)

    def test_collision_free_paths_and_booleans(self):
        p={"observations":{"a_b":1.,"a":{"b":2.},"bool":True,"digits":"42"}}
        r=Registry.build(p,"robotic_arm","llm_extracted_json","fixture-v1",("observations",))
        self.assertEqual(sorted(r.flatten(p)),[1.,2.])
        self.assertNotEqual(r.entries[0]["key"],r.entries[1]["key"])

    def test_duplicate_quantity_rejected(self):
        p=copy.deepcopy(self.public); p["input"]["states"][0]["measurements"]*=2
        with self.assertRaises(ValueError): self.registry.flatten(p)

    def test_missing_extra_null_nonfinite_units_frames_rejected(self):
        for change in ("missing","extra","null","nan","unit","frame"):
            p=copy.deepcopy(self.public); values=p["input"]["states"][0]["measurements"]
            if change=="missing": values.pop()
            elif change=="extra": p["input"]["unexpected_numeric"]=1
            elif change=="null": values[0]["value"]=None
            elif change=="nan": values[0]["value"]=float("nan")
            elif change=="unit": values[0]["unit"]="degrees"
            else: values[0]["frame"]="world"
            with self.subTest(change=change),self.assertRaises(ValueError): self.registry.flatten(p)

    def test_private_isolation_and_equal_numeric_blocks(self):
        record=read(ROOT/"example_record.json")
        before=canonical(public_record(record)); pair=text_pair(public_record(record),"A",self.registry)
        record["reference"]["label"]="changed answer"; record["metadata"]["split"]="test_id"
        self.assertEqual(before,canonical(public_record(record)))
        after=text_pair(public_record(record),record["reference"]["label"],self.registry)
        self.assertEqual(pair["n_initial"],pair["n_target"])
        self.assertEqual(pair["problem_text"],after["problem_text"])
        self.assertEqual(pair["n_target"],after["n_target"])
        self.assertNotEqual(pair["solution_text"],after["solution_text"])

    def test_fixture_encoder_once_each_and_width(self):
        class Fixture:
            calls=[]
            def token_count(self,text): return len(text)
            def encode(self,text): self.calls.append(text); return [float(len(text)),0.]
        settings=dict(model="TEST_FIXTURE_NOT_SEMANTIC",revision="1",dimension=2,pooling="fixture",max_tokens=100000,precision="float64",normalization="none",frozen=True,truncation="reject")
        pair=text_pair(self.public,"A",self.registry); encoder=Fixture()
        result=embed_pair(pair,encoder,settings)
        self.assertEqual(len(encoder.calls),2); self.assertEqual(len(result["x0"]),len(result["y"]))
        with self.assertRaises(ValueError): embed_pair(pair,encoder,{**settings,"dimension":3})
        with self.assertRaises(ValueError): embed_pair(pair,encoder,{**settings,"max_tokens":1})

    def test_registry_cannot_fit_test_or_private(self):
        with self.assertRaises(ValueError): Registry.build(self.public,"robotic_arm",partition="test_id")
        with self.assertRaises(ValueError): Registry.build({"reference":{"x":1}},"robotic_arm",root=("reference",))

    def test_structural_change_fails(self):
        p=copy.deepcopy(self.public); p["input"]["states"][0]["measurements"].append(dict(entity_id="joint_3",name="angle",value=1.,unit="rad",frame="joint_local"))
        with self.assertRaises(ValueError): self.registry.flatten(p)

    def test_illustrative_rejected_by_admission(self):
        r=read(ROOT/"example_record.json"); validator().validate(r)
        with self.assertRaises(ValueError): validate(r,admission=True)

class SamplingTests(unittest.TestCase):
    def test_allocations(self):
        self.assertEqual([allocation(20,"smoke").count(s) for s in ("id","parameter_extrapolation","unseen_combination","timed_event")],[10,4,3,3])

    def test_replay_key_order_and_group_disjointness(self):
        c=read(ROOT/"pilot_config.json"); other=__import__("json").loads(canonical(c))
        for d in c["domains"]:
            a=sample(c,d,0); self.assertEqual(a,sample(other,d,0)); self.assertNotEqual(a.group,sample(c,d,0,"calibrate").group)

    def test_ood_support_and_balanced_quadrants(self):
        c=read(ROOT/"pilot_config.json")
        for d in c["domains"]:
            a,b=PAIRS[d]
            for i in range(12):
                s=sample(c,d,i); o=sample(c,d,i,shift="unseen_combination")
                mid_a=sum(c["domains"][d]["id"][a])/2
                mid_b=.5 if b=="joint_torque_Nm" else sum(c["domains"][d]["id"][b])/2
                self.assertFalse(s.parameters[a]>mid_a and abs(s.parameters[b])>mid_b)
                self.assertTrue(o.parameters[a]>=mid_a and abs(o.parameters[b])>=mid_b)
                e=sample(c,d,i,shift="timed_event")
                self.assertGreaterEqual(e.event_start,c["domains"][d]["event_ood_time_s"][0])

    def test_grid_rejects_rounding(self):
        with self.assertRaises(ValueError): grid_index(.101,.002)
        self.assertEqual(grid_index(.1,.002),50)

    def test_release_fails_closed(self):
        with self.assertRaises(ValueError): release_gates(ROOT/"pilot_config.json")

class ExtractedTests(unittest.TestCase):
    def setUp(self):
        from phi_jepa.simulation.extracted import ExtractedAdapter
        self.registry=Registry.build({"input":{"angle":.2,"timestamp":.1}},"robotic_arm")
        self.adapter=ExtractedAdapter(self.registry,tuple([dict(kind="observation",name="joint_1 angle",unit="rad",relation="equal",column=0),dict(kind="event",description="observation cutoff",column=1)]))
        self.extraction=dict(observations=[dict(name="joint_1 angle",value=.3,unit="rad",relation="equal",evidence="joint_1 angle 0.3 rad")],events=[dict(description="observation cutoff",time=.1,evidence="cutoff 0.1s")],relations=[],symmetries_or_invariances=[],unknowns=[])

    def test_original_hashes_and_root(self):
        from phi_jepa.simulation.extracted import adopted_contract
        schema,prompt=adopted_contract(); self.assertIn("Never invent a number",prompt)
        self.assertEqual(self.adapter.flatten(self.extraction),[.3,.1])
        self.assertEqual(self.adapter.manifest()["source_root"],[])
        with self.assertRaises(Exception): self.adapter.flatten({"response":self.extraction,"usage":1})

    def test_coverage_ambiguity_and_null(self):
        for kind in ("missing","duplicate","unexpected","null"):
            e=copy.deepcopy(self.extraction)
            if kind=="missing": e["observations"]=[]
            elif kind=="duplicate": e["observations"]*=2
            elif kind=="unexpected": e["observations"][0]["name"]="unknown_joint angle"
            else: e["events"][0]["time"]=None
            with self.subTest(kind=kind),self.assertRaises(ValueError): self.adapter.flatten(e)

    def test_observations_reorder_by_identity(self):
        from phi_jepa.simulation.extracted import ExtractedAdapter
        adapter=ExtractedAdapter(self.registry,(dict(kind="observation",name="joint_1 angle",unit="rad",relation="equal",column=0),dict(kind="observation",name="timestamp",unit="s",relation="equal",column=1)))
        e=copy.deepcopy(self.extraction); e["events"]=[]
        e["observations"].append(dict(name="timestamp",value=.1,unit="s",relation="equal",evidence="0.1s"))
        first=adapter.flatten(e); e["observations"].reverse()
        self.assertEqual(first,adapter.flatten(e))

class NativePhysicsTests(unittest.TestCase):
    def setUp(self): self.c=read(ROOT/"pilot_config.json")

    def test_arm_true_zero_and_deterministic_replay(self):
        s=sample(self.c,"robotic_arm",0)
        r=MujocoAdapter().simulate(s,self.c,.002); rr=MujocoAdapter().simulate(s,self.c,.002)
        self.assertEqual(r.states,rr.states)
        self.assertEqual(r.states[0]["timestamp"],0)
        self.assertEqual(r.states[0]["measurements"][0]["value"],s.parameters["initial_joint_angles_rad"])

    def test_arm_gravity_and_torque_sign(self):
        import mujoco
        from phi_jepa.simulation.scenes import arm_model
        m=mujoco.MjModel.from_xml_string(arm_model(.1,.0001)); d=mujoco.MjData(m)
        mujoco.mj_forward(m,d); mujoco.mj_step(m,d)
        self.assertGreater(d.qvel[0],0) # +y rotation carries +x link downward
        m.opt.gravity[:]=0; mujoco.mj_resetData(m,d); d.qfrc_applied[0]=1
        mujoco.mj_step(m,d); self.assertGreater(d.qvel[0],0)
        mujoco.mj_resetData(m,d); mujoco.mj_step(m,d)
        self.assertEqual(list(d.qvel),[0.,0.])

    def test_tether_small_angle_period_and_length(self):
        s=sample(self.c,"tethered_load",0); p={**s.parameters,"cable_length_m":1.,"load_mass_kg":1.,"initial_swing_angle_rad":.01,"support_acceleration_m_s2":0.}
        r=MujocoAdapter().simulate(replace(s,parameters=p),self.c,.002)
        for st in r.states:
            theta=st["measurements"][1]["value"]
            self.assertAlmostEqual(theta,.01*math.cos(math.sqrt(9.81)*st["timestamp"]),delta=1e-6)
        self.assertGreater(r.diagnostics["min_tension_N"],0)
        self.assertLess(r.diagnostics["max_length_error_m"],1e-10)

    def test_tether_control_has_no_pre_onset_effect(self):
        from phi_jepa.simulation.scenes import support_motion
        self.assertEqual(support_motion(.1,.5,.6),(0.,0.,0.))
        self.assertEqual(support_motion(.5,.5,.6),(0.,0.,.6))
        s=sample(self.c,"tethered_load",0)
        a=MujocoAdapter().simulate(s,self.c,.002)
        b=MujocoAdapter().simulate(replace(s,parameters={**s.parameters,"support_acceleration_m_s2":0.}),self.c,.002)
        self.assertEqual([st for st in a.states if st["timestamp"]<=.2],[st for st in b.states if st["timestamp"]<=.2])
        self.assertNotEqual(a.states[-1]["measurements"],b.states[-1]["measurements"])

    def test_semantic_endpoint_and_evidence_mutations(self):
        s=sample(self.c,"tethered_load",0); r=MujocoAdapter().simulate(s,self.c,.002)
        records=build_records(s,r,self.c,code_provenance(),[]); validate(records[0])
        for kind in ("endpoint","evidence","time","entity"):
            bad=copy.deepcopy(records[0])
            if kind=="endpoint": bad["reference"]["structured_label"][0]["value"][0]+=1
            elif kind=="evidence": bad["reference"]["evidence"][0]["state_ids"]=["missing"]
            elif kind=="time": bad["input"]["states"][0]["timestamp"]=.001
            else: bad["input"]["states"][0]["measurements"][0]["entity_id"]="missing"
            with self.subTest(kind=kind),self.assertRaises(ValueError): validate(bad)
        bad=copy.deepcopy(records[1]); bad["metadata"]["split"]="test_id"
        with self.assertRaises(ValueError): validate_groups([records[0],bad])

    def test_atomic_resume_integrity_and_no_duplicates(self):
        with tempfile.TemporaryDirectory() as temp,patch("socket.socket",side_effect=AssertionError("offline")):
            path=Path(temp); first=run(self.c,"tethered_load",2,path)
            second=run(self.c,"tethered_load",2,path,resume=True)
            self.assertEqual(first["counts"]["questions"],second["counts"]["questions"])
            self.assertEqual(second["counts"]["resumed"],2)
            self.assertEqual(validate_dataset(path)["groups"],2)
            shard=next((path/"shards").glob("*.jsonl")); shard.write_text("corrupt")
            with self.assertRaises(ValueError): run(self.c,"tethered_load",2,path,resume=True)

if __name__=="__main__": unittest.main()
