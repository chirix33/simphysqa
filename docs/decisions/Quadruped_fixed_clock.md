# Quadruped fixed-clock refinement decisions

24 September 2026; branch `dataset-prep`; starting commit
`4b997efd1dcbc8199c5981e44c71bd39fa8b7cb9`.
Authority: the user's five-point refinement/calibration follow-up.

The former adapter evaluated PD feedback on every integration step. Its nominal
1/0.5 ms comparison therefore changed both integration and controller sampling.
Those raw runs are retained, but they do not isolate timestep convergence.

The controller now uses a physical period and a zero-order torque hold. Integer
step indices select controller ticks and force intervals; reference phases use
the integer control tick multiplied by its period. The general adapter default
is 2 ms (the original pilot's coarse control period). This study explicitly uses
1 ms at **all** integration resolutions. Coarser or noncommensurate integration
steps are rejected. Initial joint pose remains the original initialized pose,
even in gait development variants; no settling trajectory is silently inserted.

An experiment descriptor includes the initial generalized state, full model XML
with only its integration timestep removed, all controller settings, physical
control ticks and reference positions/velocities, horizon, force magnitude,
onset and duration. Refined runs must have identical descriptor hashes. Actual
feedback torques can diverge as states diverge; prescribed references cannot.

MJX step outputs have advanced generalized coordinates but pre-integration
contact geometry. Diagnostics recompute MJX kinematics/collision independently
at each 1 ms trace state without feeding that data back into integration.
Foot contact means ground/foot geometric separation <=0, in FL/FR/RL/RR order.
This is an explicitly named geometric indicator, not a measured support force.
An independent native geometry audit checks these indicators at 10 ms intervals
without stepping native dynamics or replacing any MJX state.

Trace torque is right-continuous: the command used over the interval beginning
at that timestamp, after any controller update. At the terminal timestamp there
is no further update; the last applied command is reported. The public sampled
states include commanded joint torques and the public controller specifies its
hold and initial state. Older quadruped numeric registries/manifests describe
the previous adapter and cannot qualify this version; regenerate them only from
the subsequent development smoke/calibration records.

Existing endpoint, fall and event thresholds are unchanged. Diagnostic limits
are 0.005 m/rad, 0.01 m/s or rad/s, and an additional 0.01 N m torque difference.
Quaternion rotation differences are sign invariant. Raw foot-contact mismatches
are reported separately and do not redefine label admission. “First divergence”
means first exceedance on the 1 ms observation grid, not an exact continuous-time
instability onset or proof of causality.

The predeclared study is eight configurations, each at 1, 0.5 and 0.25 ms: baseline;
Newton solver; 100 CG iterations; contact time constant 40 or 10 ms; contact
damping ratio 2; hip amplitude 0.2 rad; derivative gain 4. Every variant changes
one setting from baseline. No settings are stacked based on favorable outcomes.
Limits: 28 simulations, 2,400 seconds between launches, 2 GiB output, 200 GiB
free-space floor. One 0.125 ms run per candidate is permitted only when the last
two runs locomote and all four main state RMS differences decrease but label
tolerances still fail. Repeated falls do not justify chasing finer timesteps
to try to qualify nominal locomotion. Each run finishes before the next budget
check; a wall limit is a launch bound, not a hard process-kill deadline.

Nominal qualification requires locomotion in both runs of the final refinement
pair and the unchanged numerical/event label gate. It is only a prerequisite:
the 20-case varied smoke set and then 100-case calibration must still be run and
assessed. A falling but numerically more consistent trajectory is not qualified.
All attempted configurations, traces and failures remain available. No geometry,
fall rule, threshold or learned-policy substitution is authorized by this study.

The 0.2 rad hip-amplitude variant initially passed the existing nominal label gates
at 0.5/0.25 ms. The subsequent varied smoke used that exact setting and engine
source. Measured pair cost is roughly 65–74 seconds in its initial scenarios.
The execution budget therefore allows one smoke invocation and at most two
calibration invocations, each capped at 3,600 seconds between scenario launches,
to finish the requested 100 unique calibration scenarios. A second invocation
only resumes a wall-budget interruption under the exact source/config identity;
it cannot rerun completed rejects. See
`configs/quadruped_pilot_execution_budget.json`. No rejection-based resampling or
threshold adjustment is part of that budget. That calibration budget was **not
used**: later nominal replay failures revoked the initial pass.

Two workers were considered after measuring 3,129 MiB total GPU usage in the
serial run and ample host RAM. Four nominal replay runs were measured before
calibration; a later spot measurement with smoke plus both replay workers showed
4,755 MiB GPU usage (a point observation, not a peak measurement). Replay failed
both strict state equality and, separately, the original endpoint tolerances.
The strict 1e-9 diagnostic was not used to redefine benchmark admission. The
worker verifier now reports original label gates separately from that diagnostic;
the exact earlier verifier and its failed results are retained. Parallel
calibration is implemented but unqualified and was not executed.

Because the repeat failure created new evidence that refinement was needed, a
second bounded study added two serial 0.125 ms runs (two launches, 600-second
launch budget) with identical physical settings. All three retained 0.25 ms runs
were compared with both new runs; no favorable realization was selected. All six
comparisons failed. The two new runs themselves differ at T=3 s in base velocity
by 0.016544569 m/s, above the unchanged 0.01 m/s limit. A separate WSL audit found
identical initialized physical/controller/warmstart state at all four timesteps.
There is no reliable nominal reference yet; reducing dt indefinitely is not an
evidence-based completion strategy for this bounded task.

The 20-case smoke completed with 5 admitted and 15 quarantined. Its successful
per-case records are retained as development evidence, not a frozen release.
The serial orchestrator was stopped after its smoke manifest while calibration
was only gathering code provenance, before any calibration engine call. Its
original handoff reason and actual outcome are both recorded. Negative nominal
evidence now gates fresh pilot launches; calibration remains unrun. The next
bounded investigation should isolate solver/backend repeatability on the chosen
gait before expanding scenario counts. Other domains and production-disable
settings are unchanged.
