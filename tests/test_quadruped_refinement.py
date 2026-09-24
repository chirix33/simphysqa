"""Offline fixed-experiment contracts, independent of GPU availability."""
import copy
import unittest
import numpy as np
from phi_jepa.simulation.quadruped import settings, schedule, experiment, reference, synchronized_comparison
from phi_jepa.simulation.scenes import quadruped_model


class RefinementTests(unittest.TestCase):
    def test_control_and_event_clocks_are_physical(self):
        ticks=[]
        for dt in (.001,.0005,.00025):
            clock=schedule(dt,.001,3.,.6)
            indices=np.arange(clock["steps"])
            ticks.append(np.round(indices[indices%clock["control_stride"]==0]*dt,10).tolist())
            self.assertEqual((clock["event_end_step"]-clock["event_start_step"])*dt,.1)
            self.assertEqual(clock["event_start_step"]*dt,.6)
        self.assertEqual(ticks[0],ticks[1]); self.assertEqual(ticks[1],ticks[2])
        self.assertEqual(len(ticks[0]),3000)
        for dt in (.002,.0003):
            with self.assertRaises(ValueError): schedule(dt,.001,3.,.6)

    def test_exact_experiment_identity_excludes_only_timestep(self):
        cfg=settings({"controller_period_s":.001})
        def identity(dt, c=cfg, event=.6, force=3., qpos=None):
            return experiment(quadruped_model(0,.8,dt,c),qpos or [0.,0.,.4,1.,0.,0.,0.], [0.]*6,c,1.,.02,event,force)[1]
        baseline=identity(.001)
        self.assertEqual(baseline,identity(.0005))
        self.assertEqual(baseline,identity(.00025))
        for change in (dict(c=settings({"controller_period_s":.002})),dict(event=.7),dict(force=4.),dict(c={**cfg,"kp":60.}),dict(c={**cfg,"contact_time_constant_s":.04}),dict(qpos=[0.,0.,.41,1.,0.,0.,0.])):
            self.assertNotEqual(baseline,identity(.001,**change))

    def test_reference_derivative_and_order(self):
        cfg=settings({})
        pos,vel=reference(.123,1.,cfg)
        numerical=(reference(.123+1e-6,1.,cfg)[0]-reference(.123-1e-6,1.,cfg)[0])/2e-6
        np.testing.assert_allclose(vel,numerical,atol=1e-8)
        self.assertEqual(pos.shape,(8,))
        np.testing.assert_allclose(pos[:2],pos[6:])
        np.testing.assert_allclose(pos[2:4],pos[4:6])

    def test_invalid_configuration_fails_explicitly(self):
        for cfg in ({"kp":float("nan")},{"kd":0},{"unknown":1},{"iterations":1.5},{"solver":"bad"},{"controller_period_s":False}):
            with self.assertRaises(ValueError): settings(cfg)

    def test_synchronized_first_divergence_and_quaternion_sign(self):
        trace=dict(times_s=[0.,.001,.002],base_orientation_wxyz=[[1.,0.,0.,0.]]*3,foot_contacts=[[False]*4]*3)
        for key,n in (("base_position",3),("base_velocity",3),("base_angular_velocity",3),("joint_position",8),("joint_velocity",8),("commanded_torque",8)):
            trace[key]=[[0.]*n for _ in range(3)]
        a=dict(experiment_hash="same",trace=trace); b=copy.deepcopy(a)
        b["trace"]["base_orientation_wxyz"]=[[-1.,0.,0.,0.]]*3
        self.assertIsNone(synchronized_comparison(a,b)["first_material_divergence_s"])
        b["trace"]["commanded_torque"][1][2]=.02
        b["trace"]["base_position"][2][0]=.006
        out=synchronized_comparison(a,b)
        self.assertEqual(out["first_material_divergence_s"],.001)
        self.assertEqual(out["channels"]["base_position"]["first_material_divergence_s"],.002)
        b["experiment_hash"]="different"
        with self.assertRaises(ValueError): synchronized_comparison(a,b)
        b["experiment_hash"]="same"; b["trace"]["times_s"]=[0.,.002,.004]
        with self.assertRaises(ValueError): synchronized_comparison(a,b)


if __name__=="__main__": unittest.main()
