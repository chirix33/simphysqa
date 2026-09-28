"""Empirical cache boundary tests use explicit synthetic payloads, not physics."""
from dataclasses import asdict, replace
from hashlib import sha256
from pathlib import Path
import sys
import tempfile
import unittest
from phi_jepa.artifacts import canonical, digest
from phi_jepa.simulation.common import ROOT, Rollout, Scenario, write
sys.path.insert(0,str(ROOT/"tools"))
from parallel_quadruped_calibration import EmpiricalCache, cache_identity
from run_qualified_quadruped_pilots import qualified_config


class EmpiricalCacheTests(unittest.TestCase):
    def setUp(self):
        self.temp=tempfile.TemporaryDirectory()
        self.path=Path(self.temp.name)
        self.scenario=Scenario("quadruped_locomotion",1,"test-group","development","id","default",{},.6)
        self.config={"time":{"default_timestep_s":.0005}}
        self.identity=cache_identity(self.scenario,self.config,.0005,"test-source")
        self.key=digest(self.identity)
        self.reader=EmpiricalCache(self.path,"test-source")

    def tearDown(self): self.temp.cleanup()

    def save(self,**changes):
        fixture=Rollout([],[],{},"explicit-unit-test-fixture","xml","mjx","fixture",{"backend":"gpu"})
        payload={"identity":self.identity,"rollout":asdict(fixture),**changes}
        raw=canonical(payload)
        write(self.path/(self.key+".json"),payload)
        write(self.path/(self.key+".receipt.json"),dict(path=self.key+".json",sha256=sha256(raw).hexdigest()))

    def test_missing_never_invokes_simulator_fallback(self):
        with self.assertRaisesRegex(ValueError,"unavailable"):
            self.reader.simulate(self.scenario,self.config,.0005)

    def test_later_negative_evidence_blocks_pilot_launch(self):
        write(self.path/"qualification-status.json",{"qualified":False})
        with self.assertRaisesRegex(ValueError,"revoked"):
            qualified_config(self.path)

    def test_identity_rejects_different_controls_scenario_step_or_source(self):
        self.save()
        for scenario,config,dt in ((replace(self.scenario,event_start=.7),self.config,.0005),(self.scenario,{**self.config,"quadruped_settings":{"kp":100}},.0005),(self.scenario,self.config,.00025)):
            with self.assertRaises(ValueError): self.reader.simulate(scenario,config,dt)
        with self.assertRaises(ValueError): EmpiricalCache(self.path,"other-source").simulate(self.scenario,self.config,.0005)

    def test_tampering_is_rejected(self):
        self.save()
        path=self.path/(self.key+".json")
        path.write_bytes(path.read_bytes()+b" ")
        with self.assertRaisesRegex(ValueError,"checksum"):
            self.reader.simulate(self.scenario,self.config,.0005)

    def test_recorded_failure_is_retained(self):
        self.save(error="explicit synthetic failure")
        with self.assertRaisesRegex(RuntimeError,"recorded simulator failure"):
            self.reader.simulate(self.scenario,self.config,.0005)


if __name__=="__main__": unittest.main()
