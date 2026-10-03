"""Authored analytic geometry, explicit inertias and public model descriptions."""
import math

def box_inertia(m, size):
    x, y, z = size
    return [m*(y*y+z*z)/12, m*(x*x+z*z)/12, m*(x*x+y*y)/12]

def arm_model(payload, dt):
    # Payload is a finite sphere rigidly attached at the endpoint, not arbitrary link mass.
    return f'''<mujoco model="phi_planar_arm_v1">
 <compiler angle="radian"/><option timestep="{dt}" gravity="0 0 -9.81" integrator="RK4" tolerance="1e-10" iterations="100"/>
 <default><joint damping="0.05" limited="true" range="-2.8 2.8"/><geom contype="0" conaffinity="0"/></default>
 <worldbody><body name="link1" pos="0 0 1"><joint name="joint_1" axis="0 1 0"/>
 <geom type="box" pos="0.2 0 0" size="0.2 0.025 0.025" mass="1"/>
 <body name="link2" pos="0.4 0 0"><joint name="joint_2" axis="0 1 0"/>
 <geom type="box" pos="0.15 0 0" size="0.15 0.025 0.025" mass="0.8"/>
 <body name="payload" pos="0.3 0 0"><geom type="sphere" size="0.025" mass="{max(payload, 1e-12)}"/><site name="tip" size="0.005"/></body>
 </body></body></worldbody></mujoco>'''

def tether_model(length, mass, dt):
    return f'''<mujoco model="phi_taut_pendulum_v1"><compiler angle="radian"/>
 <option timestep="{dt}" gravity="0 0 -9.81" integrator="RK4" tolerance="1e-10" iterations="100"/>
 <worldbody><body name="support" mocap="true" pos="0 0 2"/>
 <body name="pivot" pos="0 0 2"><joint name="support_x" type="slide" axis="1 0 0" damping="0"/>
 <inertial pos="0 0 0" mass="0.1" diaginertia="0.001 0.001 0.001"/>
 <body name="swing"><joint name="swing" axis="0 -1 0" damping="0"/>
 <inertial pos="0 0 -{length}" mass="{mass}" diaginertia="0.000000001 0.000000001 0.000000001"/>
 <geom type="sphere" pos="0 0 -{length}" size="0.025" contype="0" conaffinity="0" mass="0"/>
 <site name="load" pos="0 0 -{length}"/></body></body></worldbody></mujoco>'''

def quadruped_model(payload_fraction, friction, dt, settings=None):
    from .quadruped import settings as validated_settings
    cfg = validated_settings(settings or {})
    legs = []
    for name, x, y in (("fl", .22, .14), ("fr", .22, -.14), ("rl", -.22, .14), ("rr", -.22, -.14)):
        legs.append(f'''<body name="{name}_upper" pos="{x} {y} 0"><joint name="{name}_hip" axis="0 1 0"/>
<geom type="capsule" fromto="0 0 0 0 0 -0.2" size="0.025" mass="0.3" contype="0" conaffinity="0"/>
<body name="{name}_lower" pos="0 0 -0.2"><joint name="{name}_knee" axis="0 1 0"/>
<geom type="capsule" fromto="0 0 0 0 0 -0.2" size="0.02" mass="0.2" contype="0" conaffinity="0"/>
<geom name="{name}_foot" type="sphere" pos="0 0 -0.2" size="0.03" mass="0.05" friction="{friction} 0.005 0.0001"/></body></body>''')
    return f'''<mujoco model="phi_quadruped_v1"><compiler angle="radian"/><option timestep="{dt}" solver="{cfg['solver']}" iterations="{cfg['iterations']}" ls_iterations="10" tolerance="{cfg['solver_tolerance']}" gravity="0 0 -9.81"/>
<default><joint damping="0.1" armature="0.01"/><geom condim="3" solref="{cfg['contact_time_constant_s']} {cfg['contact_damping_ratio']}"/></default>
<worldbody><geom name="ground" type="plane" size="10 10 0.1" friction="{friction} 0.005 0.0001"/>
<body name="base" pos="0 0 {0.4*math.cos(.25)+.03}"><freejoint/><geom type="box" size="0.25 0.12 0.06" mass="4"/>
<geom type="box" pos="0 0 0.07" size="0.1 0.08 0.01" mass="{max(4*payload_fraction, 1e-12)}" contype="0" conaffinity="0"/>
{''.join(legs)}</body></worldbody></mujoco>'''

def support_motion(t, start, acceleration):
    # Smooth bounded excursion: acceleration pulse followed by its negative.
    h = 0.1
    if t < start:
        return 0., 0., 0.
    u = max(0., t-start)
    if u < h: return .5*acceleration*u*u, acceleration*u, acceleration
    if u < 2*h:
        v = u-h
        return .5*acceleration*h*h+acceleration*h*v-.5*acceleration*v*v, acceleration*(h-v), -acceleration
    return acceleration*h*h, 0., 0.

def gait(t, frequency):
    q, v = [], []
    for phase in (0., math.pi, math.pi, 0.):
        a = 2*math.pi*frequency*t+phase
        q.extend([-.25+.3*math.sin(a), .5+.2*math.sin(a-math.pi/2)])
        v.extend([.3*2*math.pi*frequency*math.cos(a), .2*2*math.pi*frequency*math.cos(a-math.pi/2)])
    return q, v
