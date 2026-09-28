# Dataset follow-up: fixed-clock quadruped refinement

24 September 2026. Branch `dataset-prep`, clean starting commit
`4b997efd1dcbc8199c5981e44c71bd39fa8b7cb9`. Changes are local and uncommitted.
This follows the user's five-point refinement instruction; it does not authorize
neural training, new geometry, a learned policy or changed validation thresholds.

**The initial nominal pass was revoked by a later repeat failure.**
The 0.2 rad hip-amplitude variant passed its original refinement pair, but one
repeated pair failed the same endpoint tolerances. Two serial 0.125 ms runs also
fail the original gates. Status: **implemented_pending_validation**; calibration
remains gated, with zero calibration scenarios simulated.
The varied-scenario smoke/calibration results are recorded below separately.
The qualification gate concerns the existing endpoint/event rules, not uniform convergence
of every intermediate joint/contact/torque channel or real-world validity.

## Experiment correction and verification

The earlier adapter updated feedback every integration step, changing the control
frequency during refinement. The older raw results remain intact but cannot
isolate integration error. The new adapter uses integer controller ticks and holds
torques between ticks. The study fixes its period at 1 ms across all resolutions.
Geometry, initial pose/velocity, payload, friction, frequency, phase, gains, force
magnitude/onset/duration and physical horizon are identical within each sequence;
the descriptor hash excludes only the XML integration timestep.

The nominal experiment uses zero payload, friction 0.8, frequency 1 Hz, horizon
3 s and an intervention scheduled at 4 s (outside the horizon). Separately, two
real MJX instrumented runs check an **active** force from 0.01 to 0.11 s:
0.5 and 0.25 ms integration each perform 120 controller updates over 0.12 s,
hold each torque exactly between updates, apply the force for exactly 0.1 s and
produce the same commanded impulse, 0.30440265967423047 N s. The callback only
observes forces; it does not replace dynamics. Each run also has one separately
counted compile-probe step, restarted before the physical rollout.

The 1 ms traces include base position/quaternion/velocity, all joint states,
actually commanded torque and four foot-ground contact indicators. Contact
geometry is recomputed at the recorded qpos: MJX's step-returned contacts otherwise
belong to the preceding state. Independent checks passed for all 24 original study runs:
72,000 controller ticks and 7,224 geometric contact timestamps. Native MuJoCo is
used only for this geometric audit, never to replace MJX trajectories. The two
finer runs passed the same audit later, adding 6,000 controller ticks and 602
geometry timestamps. A separate native initialization audit verifies identical
qpos/qvel, warmstart acceleration, applied forces, controls, activation and mocap
state across 1/0.5/0.25/0.125 ms; the initial warmstart acceleration is zero.

## Bounded one-factor study

24 real GPU simulations in 661.413 s. The predeclared cap was 28 simulations,
2,400 seconds between launches, 2 GiB output and 200 GiB free disk. Each row changes
one baseline setting. Initial state and geometry are fixed even across gait
variants. No 0.125 ms run was triggered inside the original eight-configuration
study. The later repeat failure provides a separate reason for the bounded finer
check.

Values are 3 s forward displacement in metres; F means the fall rule was met,
U means upright under that rule. The final column requires both fine runs to
locomote and their endpoint/event comparison to pass unchanged thresholds.

| Setting | 1 ms | 0.5 ms | 0.25 ms | Initial pair gate |
| --- | ---: | ---: | ---: | --- |
| Baseline | 0.808191 U | 0.870446 F | 0.866988 F | No |
| Newton solver | 0.701100 U | 0.844937 F | 0.861050 F | No |
| CG iterations 100 | 1.040425 F | 0.844529 F | 0.871141 F | No |
| Contact time constant 40 ms | 0.481534 U | 0.419056 U | 0.393787 U | No |
| Contact time constant 10 ms | 1.010045 F | 0.999593 F | 0.948036 F | No |
| Contact damping ratio 2 | 0.841314 F | 0.857419 F | 0.872159 F | No |
| Hip amplitude 0.2 rad | 0.208081 U | 0.208507 U | 0.206768 U | Pass, later revoked |
| Derivative gain 4 | 1.088652 F | 1.107772 F | 1.105004 F | No |

The baseline becomes much more consistent between 0.5/0.25 ms but falls in both.
Its position RMS difference falls from 0.292864 m to 0.003541 m; orientation RMS
from 1.159012 rad to 0.010484 rad. This is improved numerical consistency without
nominal success. The softer-contact alternative stays upright, but its orientation
RMS difference grows while its endpoint tolerance violations remain.

For the selected hip variant, successive position RMS differences decrease from
0.004587 to 0.001208 m; orientation from 0.011429 to 0.003091 rad; maximum-per-joint
position RMS from 0.011620 to 0.002957 rad; velocity RMS from 0.275922 to 0.131326
rad/s. The 0.5/0.25 ms label comparison passes; the 1/0.5 ms comparison does not.
The selected pilot integration step is therefore 0.5 ms, always checked against
0.25 ms, with 1 ms control updates. The finest nominal displacement exceeds the
0.2 m requirement by only 0.006768 m; varied qualification is essential.

## Where trajectories first differ

First threshold exceedance on the synchronized 1 ms grid, in seconds. Contact is
raw geometric mismatch; its threshold is diagnostic only. Torque's 0.01 N m
limit is likewise diagnostic. Position/orientation limits are 0.005 m/rad and
velocity limits 0.01 m/s or rad/s. Quaternion distance is sign invariant.

| Channel | Baseline 1/0.5 ms | Baseline 0.5/0.25 ms | Selected gait 0.5/0.25 ms |
| --- | ---: | ---: | ---: |
| Commanded torque | 0.033 | 0.126 | 0.101 |
| Foot contact mismatch | 0.060 | 0.125 | 0.124 |
| Joint velocity | 0.061 | 0.126 | 0.114 |
| Base angular velocity | 0.080 | 0.126 | 0.125 |
| Base linear velocity | 0.124 | 0.206 | 0.175 |
| Base orientation | 0.493 | 1.608 | 1.756 |
| Joint position | 0.529 | 1.800 | 1.896 |
| Base position | 0.687 | 1.715 | None |

The selected gait's maximum base-position difference is 0.002444 m, but its
intermediate maximum joint-velocity difference reaches 0.921914 rad/s and torque
2.127173 N m. These are disclosed discrepancies, not discarded samples. The
existing benchmark asks for designated base endpoint/fall labels; passing those
does not establish uniformly accurate contact transients or joint trajectories.

## Repeated nominal runs and the finer check

Two independent workers each repeated the 0.5/0.25 ms nominal pair. Their saved
trajectories differ from the original study. A strict 1e-9 state-equality audit
failed, but that is **not** the reason for revoking nominal qualification: a
separate audit using the unchanged benchmark thresholds also failed. One 0.5 ms
same-timestep replay had maximum endpoint error 0.010033; one repeated refinement
pair had maximum endpoint error 0.019810. All four runs remained upright with
forward displacement >=0.2 m. We do not attribute the difference specifically to
concurrency; compiled GPU arithmetic/solver/contact sensitivity remains unresolved.
The two-worker calibration path exists but was not used or qualified.

This evidence triggered two additional **serial**, same-experiment runs at
0.125 ms, bounded to two launches and 600 seconds. They took 157.440 s and advanced
0.202813709 and 0.200108139 m without falling. All six comparisons to the three
retained 0.25 ms realizations failed the original endpoint gate. The two 0.125 ms
runs themselves disagree in base velocity at T=3 s by **0.016544569 m/s**, above
the unchanged **0.01 m/s** refinement limit; their other requested endpoint
channels pass. Event/fall labels agree. The final run's locomotion margin is only
0.000108139 m. These results do not establish a reliable nominal reference.

Position RMS disagreement versus the original 0.25 ms run grows to 0.002501 m
for the first finer run, versus 0.001208 m in the preceding refinement pair.
Joint-position RMS also grows, from 0.002957 to 0.004770 rad. There is no consistent
overall settling trend that would justify unbounded further timestep reduction.
Every original/repeated/finer run is retained; no favorable realization was
selected to bypass the failures. The fixed-clock experiment check itself passes.

## Varied smoke and gated calibration

The smoke set was launched after the initial pair passed, and completed while
the repeatability audit was assessed. At 0.5/0.25 ms: **5/20 scenarios admitted,
15/20 quarantined, nine development records exported**, in 1,467.810 s. The runtime
includes overlap with the worker audit and is not a pure throughput benchmark.

| Shift | Attempted | Admitted | Quarantined |
| --- | ---: | ---: | ---: |
| ID | 10 | 2 | 8 |
| Parameter extrapolation | 4 | 1 | 3 |
| Unseen combination | 3 | 1 | 2 |
| Timed event | 3 | 1 | 2 |

These are per-case admission results at the time of the run, **not** a qualified
quadruped release. The later negative nominal evidence is recorded separately in
`qualification-status.json`; it revokes the original candidate without rewriting
its raw measurements or the smoke manifest. Existing quadruped registries and
the newly generated smoke registry must not be used as a frozen release registry.

The serial orchestrator was intentionally interrupted after the complete smoke
manifest, during calibration's `code_provenance` setup. **No calibration engine
call occurred**, no calibration scenario was resampled, and no completed receipt
was lost. The initial handoff plan was to use two workers; their failed audit
instead gated calibration and led to the finer study. Both the initial handoff
record and its actual outcome are preserved. Fresh pilot launch now rejects a
revoked nominal qualification. The requested 100-case calibration is pending a
reliable nominal reference; it was not replaced by the successful single pair.

## Reproduction and evidence

From the WSL repository directory, using the existing isolated MJX environment:

```bash
XLA_PYTHON_CLIENT_PREALLOCATE=false PYTHONPATH=src .dataset-wsl-venv/bin/python tools/study_dataset_quadruped.py --output dataset-runs/quadruped-fixed-clock-study
XLA_PYTHON_CLIENT_PREALLOCATE=false PYTHONPATH=src .dataset-wsl-venv/bin/python tools/verify_quadruped_clock.py --output dataset-runs/quadruped-clock-audit.json
XLA_PYTHON_CLIENT_PREALLOCATE=false PYTHONPATH=src .dataset-wsl-venv/bin/python tools/run_qualified_quadruped_pilots.py --study dataset-runs/quadruped-fixed-clock-study --output dataset-runs/quadruped-qualified-pilots
XLA_PYTHON_CLIENT_PREALLOCATE=false PYTHONPATH=src .dataset-wsl-venv/bin/python tools/verify_quadruped_workers.py --study dataset-runs/quadruped-fixed-clock-study --output dataset-runs/quadruped-worker-replay
XLA_PYTHON_CLIENT_PREALLOCATE=false PYTHONPATH=src .dataset-wsl-venv/bin/python tools/refine_quadruped_nominal.py --study dataset-runs/quadruped-fixed-clock-study --replays dataset-runs/quadruped-worker-replay --output dataset-runs/quadruped-finer-nominal
PYTHONPATH=src .dataset-bullet-venv/bin/python -m unittest discover -s tests -v
```

The Windows command `.dataset-venv/Scripts/python.exe
tools/audit_quadruped_study.py dataset-runs/quadruped-fixed-clock-study` checks saved
traces without GPU dynamics. Existing output directories intentionally cannot be
overwritten. Use a new directory when reproducing.
These are the commands executed during the study. The original candidate is now
revoked, so current pilot/worker commands reject it; the explicitly designated
development finer-check command can still diagnose it. The original worker tool
and its later original-tolerance analysis are both archived. An initial WSL
initializer-audit command lacked `PYTHONPATH`; it was corrected by explicitly
adding `src`, then passed. That failed import performed no physics calls.

Offline regression: **65 tests passed** in the Linux environment including
MuJoCo/PyBullet. Windows: 65 run, 62 passed, 3 skipped for absent PyBullet. Ten new
tests cover fixed physical clocks, experiment fingerprints, reference
derivatives/order, invalid settings, synchronized quaternion/divergence logic,
empirical-cache identity/integrity/failure handling and revoked qualification.
The real force/hold and 26-run trace audits are additional measured checks. The
failed worker and finer-repeat audits are reported as failures, not test passes.
Campaign accounting: 70 full rollouts and two short clock audits; 612,720 physical
integration steps plus 72 separately counted compile probes (612,792 MJX step
calls), 210,240 physical controller updates, 72 controller-probe updates and zero
calibration engine calls. Native initialization and geometric audits are disclosed
separately; inner CG iterations are not individually measured. The nine historical
smoke records also pass schema/group/artifact-integrity validation, which does
not undo the later nominal-qualification failure.

Local full traces, hashes, failed configurations and source snapshots remain in
`dataset-runs/quadruped-fixed-clock-study`; all earlier raw runs are preserved.
Decisions and interpretation limits are in
[the decision record](../decisions/Quadruped_fixed_clock.md).

Compact durable evidence is under
[PDS_quadruped_refinement](artifacts/PDS_quadruped_refinement/), including original
study plan/summary, measured environment, exact execution-source snapshots,
clock/trace audits, repeat/finer summaries, smoke manifest/rejections, tests and
checksums. Large full trajectories remain in the local gitignored run folders.
The source snapshot distinguishes the original study's pipeline from the later
export-gate improvement. All earlier dataset work/assets remain preserved.

## Remaining blocker — package format

- **Phase/substep/status:** Dataset / reliable quadruped numerical reference;
  `implemented_pending_validation`.
- **Branch/commit/paths:** `dataset-prep`, base
  `4b997efd1dcbc8199c5981e44c71bd39fa8b7cb9`; MJX/scenes/fixed-clock modules,
  study/replay/finer tools and the artifact paths above. Changes are uncommitted.
- **Expected behavior/source:** same experiment under refinement; repeatable
  nominal >=0.2 m locomotion without falling and numerical agreement under
  SPECIFICATION.md sections 7/9, then varied smoke/calibration; user's five points.
- **Reproducer:** `XLA_PYTHON_CLIENT_PREALLOCATE=false PYTHONPATH=src
  .dataset-wsl-venv/bin/python tools/refine_quadruped_nominal.py --study
  dataset-runs/quadruped-fixed-clock-study --replays
  dataset-runs/quadruped-worker-replay --output dataset-runs/new-finer-check`.
- **Observed:** 0.125 ms serial repeats differ in terminal base velocity by
  0.016544569 m/s versus a 0.01 m/s limit; all six 0.25/0.125 ms comparisons fail.
- **Environment:** real RTX 5090 GPU, WSL Ubuntu, Python 3.12.3, MuJoCo/MJX 3.14,
  JAX/JAXlib 0.11.2, x64 JAX backend. Exact measured details are archived.
- **Attempts/outcomes:** fixed controller-clock correction; 24 one-factor study
  runs; 20-case smoke; four concurrent nominal repeats; two serial finer repeats;
  active-force/hold audits; initialized-state/warmstart and contact audits. Initial
  nominal success was revoked when new evidence failed unchanged thresholds.
- **Root cause:** the original controller-frequency confound is fixed. Remaining
  solver/contact/GPU numerical sensitivity is measured but not causally isolated;
  initial physical and warmstart states match, and control/event clocks are correct.
- **Impact:** 100-case quadruped calibration and release remain gated. The other
  four domains and their earlier development results are unaffected.
- **Options/recommendation:** next bounded study should isolate solver convergence
  and same-timestep repeatability on the selected gait before more scenario counts;
  a changed geometry/gait family requires a separately pinned model and revalidation.
- **Smallest unresolved decision:** the scope/budget of a subsequent solver/backend
  repeatability investigation; no extraction-schema or model-training clarification
  is needed for this blocker.
- **Evidence to close:** repeated nominal/refinement pairs passing the unchanged
  gates, followed by fresh varied smoke and 100-case calibration with every reject
  retained. No production generation, model training, push or publication occurred.
