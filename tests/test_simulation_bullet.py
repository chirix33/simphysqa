"""Actual PyBullet checks; explicitly skipped when this optional engine is absent."""
import importlib.util
import unittest
from dataclasses import replace
from phi_jepa.simulation.common import ROOT,read,event_active
from phi_jepa.simulation.sampling import sample

@unittest.skipUnless(importlib.util.find_spec("pybullet"),"PyBullet not installed in this isolated environment")
class BulletPhysicsTests(unittest.TestCase):
    def setUp(self):
        from phi_jepa.simulation.bullet import BulletAdapter
        self.adapter=BulletAdapter(); self.c=read(ROOT/"pilot_config.json")

    def test_stationary_brakes_do_not_propel(self):
        s=sample(self.c,"driving",0)
        s=replace(s,parameters={**s.parameters,"initial_forward_speed_m_s":0.})
        r=self.adapter.simulate(s,self.c,.0005)
        speed=[next(v["value"] for v in st["measurements"] if v["name"]=="forward_velocity") for st in r.states]
        self.assertLess(max(map(abs,speed)),.02)
        self.assertTrue(r.diagnostics["stopped_by_T"])

    def test_unforced_stack_and_initial_state(self):
        s=sample(self.c,"object_pushing_stacking",1)
        s=replace(s,parameters={**s.parameters,"push_force_N":0.})
        r=self.adapter.simulate(s,self.c,.002)
        self.assertEqual(r.states[0]["timestamp"],0.)
        positions=[v["value"] for v in r.states[0]["measurements"] if v["name"]=="position"]
        self.assertEqual(positions,[[0.,0.,.05],[0.,0.,.15]])
        self.assertTrue(r.diagnostics["stable_stack_at_T"])

    def test_gravity_limit(self):
        import pybullet as b
        client=b.connect(b.DIRECT)
        try:
            b.setGravity(0,0,-9.81,physicsClientId=client); b.setTimeStep(.0005,physicsClientId=client)
            shape=b.createCollisionShape(b.GEOM_SPHERE,radius=.05,physicsClientId=client)
            obj=b.createMultiBody(1,shape,basePosition=[0,0,1],physicsClientId=client)
            b.changeDynamics(obj,-1,linearDamping=0,angularDamping=0,physicsClientId=client)
            for _ in range(200): b.stepSimulation(physicsClientId=client)
            z=b.getBasePositionAndOrientation(obj,physicsClientId=client)[0][2]
            self.assertAlmostEqual(z,1-.5*9.81*.1**2,delta=.0003)
        finally: b.disconnect(client)

class SchedulerTests(unittest.TestCase):
    def test_exact_float_boundary_and_interval_end(self):
        onset=.47800000000000004
        self.assertTrue(event_active(239,.002,onset,onset+.1))
        self.assertFalse(event_active(238,.002,onset,onset+.1))
        self.assertFalse(event_active(289,.002,onset,onset+.1))
