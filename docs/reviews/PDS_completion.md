# Dataset preparation implementation and validation report

24 September 2026. Branch `dataset-prep`, starting HEAD
`983feaec76acfd923cc7b7d18844ddd92696daff`. Changes remain uncommitted for review.
Status: **implemented_pending_validation; not release-ready**. Four domains have
admitted development datasets. The MJX quadruped implementation executes on GPU,
but its numerical/controller qualification failed. No model was trained and no
production dataset was generated.

## Implemented behavior

The separate `phi-dataset` CLI implements environment inspection, schema checks,
20-scenario smoke runs, 100-scenario calibration, matched engine comparison,
dataset validation, public export and gated/resumable release dispatch. It reuses
P00 canonical JSON/hashing/provenance; legacy modules and P00/P01 behavior remain
unchanged. New source is under `src/phi_jepa/simulation/`.

Five modular adapters implement the requested MuJoCo arm, PyBullet four-wheel
braking vehicle, PyBullet pushing/pre-stacked objects, MJX-JAX periodic-PD
quadruped, and MuJoCo constrained taut tether. Scenes expose authored assets,
physical parameters, controller equations or explicit controls, coordinate
conventions, observations, future interventions and named physical targets.
Labels come from separate readout functions. Numerical task failures remain
outcomes; numerical inconsistency is quarantined. No illustrative record is
promoted to simulated data.

The supplied JSON structure is preserved. Group/split assignment precedes
question variants. OOD ranges, pairings, quadrants, event windows and grouping
policy are configured. The numeric registry covers all numbers under public
`input`, including timestamps, steps and model/control numbers. Entity and
measurement ordering is semantic, not positional. Both strict simulator and
adopted-extraction adapters are implemented. The extraction prompt/schema are
pinned verbatim with their original hashes; explicit aliases address the original
schema's free-form names. No oracle completion occurs.

Training preparation exports exact serialized Q/C and Q/C/A, with equal numeric
blocks. There are no purported semantic embeddings, extra objectives or model
components. The embedding callback checks settings, width and overlength inputs;
its tests use a clearly named fixture. Real encoder selection, token counts,
embedding sensitivity, gradients through a future trained model and answer
decoding remain model-integration work.

## Actual development results

Counts are base scenarios, not independent question counts or model performance.
Every admitted record passed schema/semantic checks and the recorded refinement
checks. The retained rejection logs identify every failed draw; difficult cases
were not silently resampled.

| Domain | Smoke admitted / attempted | Calibration admitted / attempted | Status |
|---|---:|---:|---|
| Robotic arm | 20 / 20 | 98 / 100 | Development outputs admitted; two calibration cases quarantined |
| Driving | 16 / 20 | 87 / 100 | Contact/stop-sensitive cases quarantined |
| Objects, both subfamilies | 20 / 20 | 100 / 100 | Development outputs admitted |
| Tether, corrected scheduler | 20 / 20 | 100 / 100 | Development outputs admitted |
| Quadruped | 0 / 20 | Not run after failed smoke | Numerical/controller gate failed |

The arm and driving use 0.1 ms integration with 0.05 ms refinement. Objects and
the tether use 2 ms with 1 ms refinement. Endpoint gates use half the requested
accuracy tolerance; discrete outcomes must agree and event times must be within
0.01 s. Quaternion comparisons use sign-invariant rotation distance. No tolerance
was loosened to force acceptance. This supports numerical reference consistency,
not real-world validity.

All 20 matched arm pairs executed with independent MuJoCo/PyBullet named labels.
The diagnostic reports disagreement, not an expectation of exact cross-engine
agreement. Native MuJoCo versus MJX is explicitly a backend comparison.

## Verification and environment

- Final Windows suite: **55 tests, 52 passed and 3 PyBullet tests explicitly
  skipped** because that engine is isolated in Linux.
- Final Linux Python 3.11 suite: **55 tests passed**, including real PyBullet
  stationary-brake, unforced-stack, gravity and exact-event-boundary checks.
- Tests cover independent arm gravity/torque signs, the tether's small-angle
  limiting solution and pre-onset control isolation, t=0, schema/endpoint/evidence
  corruption, group leakage, numeric identity/collisions/missing fields,
  private-reference isolation, equal input/target numeric blocks, embedding widths,
  extraction wrapper rejection, resume integrity and disabled release generation.
- The Windows editable install and `phi-dataset validate-schema` were executed.
  Offline P00/P01 regression tests remain passing. No network is used by tests.
- `git diff --check` passed. The older `tools/verify_p00_handoff.py` exited 1 on
  a pre-existing false positive: the unchanged P02 prompt says **do not create**
  an obsolete nested handoff directory, but the scanner flags that negative instruction as a
  stale installation path. It reported no source-asset or prompt hash mismatch;
  the unrelated P02 prompt and checker were left unchanged. An independent hash
  check passed for all nine preserved source assets and four prompt strings.
- Actual Windows host: 24 logical CPUs, 68,135,153,664 bytes RAM. Actual WSL VM:
  33,363,247,104 bytes RAM. RTX 5090, driver 610.60, 32,607 MiB reported VRAM.
  Initial disk probe found about 1.87 TB free. Serial dataset workers were used.
- MuJoCo 3.14.0 and MJX 3.14.0; PyBullet 3.2.7; JAX/JAXlib 0.11.2. Complete
  working environment locks are under `configs/dataset-*.lock.txt`.
- A real MJX-JAX GPU step passed. Batch sizes 1, 8, 32 and 64 passed a short
  float32 device-step profile, with peak allocator use below 220 MB in that
  profile. This is **not** a full float64-rollout memory guarantee or qualification.
  Float64 primary quadruped rollouts were separately executed. Production batch
  size remains unselected; no Warp execution is claimed.

Exact commands are in [README](../../README.md). The reproducible pilot runner
is `tools/run_dataset_pilots.py`; `tools/collect_dataset_evidence.py` verifies
selected outputs and produces the linked compact evidence. The final tests used:

```text
.dataset-venv/Scripts/python.exe -m unittest discover -s tests -q
PYTHONPATH=src .dataset-bullet-venv/bin/python -m unittest discover -s tests -v
```

## Artifacts and provenance

[Machine-readable summary](artifacts/PDS/summary.json) contains actual counts,
subfamily/shift coverage, wall time, peak resident memory, disk usage, validation
results and run paths. [Checksums](artifacts/PDS/checksums.json) cover the compact
review artifacts. The directory also retains representative actual simulated
full/public records for the four admitted domains, a clearly quarantined
quadruped example, environment measurements, test logs, batch profiling and
cross-engine/nominal diagnostics.

Complete local shards, private references, public inputs, target texts, rejected
trajectories and logs remain in:

- `dataset-runs/final/robotic_arm/{smoke,calibrate}`
- `dataset-runs/final/driving/{smoke,calibrate}`
- `dataset-runs/final/object_pushing_stacking/{smoke,calibrate}`
- `dataset-runs/final/tethered_load/{corrected-smoke,corrected-calibrate}`
- `dataset-runs/quadruped-smoke-v2` and `dataset-runs/final/arm-comparison`

Versioned domain manifests and development-frozen numeric/extraction registries
are under `configs/dataset_domains/` and `configs/dataset_registries/`. Run
manifests record the base commit plus actual dirty source hashes; final native
and Bullet runs also preserve source snapshots. No clean-commit provenance is
claimed. Large `dataset-runs/` artifacts and environments are gitignored.

## Changes and deviations from provisional defaults

See [decisions](../decisions/Dataset_preparation.md) for exact engineering choices.
Initial arm 2 ms and 0.5 ms failures remain preserved; 0.1 ms was retained for
arm/driving development. Driving's finite test floor was replaced by the required
infinite flat plane. Brake/contact settings were calibrated and disclosed. The
requested primary driving labels are forward position/velocity; full 3D state
remains available as reference/observation, not an undeclared additional target.

Control scheduling now compares integer step indices. A later independent check
found that the tether helper returned nonzero acceleration before its onset;
this was corrected and regression-tested. **All earlier tether runs are
superseded** by `corrected-smoke` / `corrected-calibrate`; they are retained only
as development history. This defect did not alter the supplied specification.

PyBullet installs on Python 3.12 failed for missing compilers. A prebuilt Linux
Python 3.11 wheel resolved this without installing a system compiler or changing
drivers. MJX's initial allocator warnings were addressed with disabled bulk
preallocation. An x64 contact-index dtype mismatch in `lax.scan` was fixed by
preserving integer index dtypes; physical state values are not cast or replaced.

## Remaining blocker — package blocker format

- **Phase/substep and status:** Dataset / MJX locomotion numerical qualification;
  `implemented_pending_validation`.
- **Repository branch/commit and paths:** `dataset-prep`, base
  `983feaec76acfd923cc7b7d18844ddd92696daff`;
  `src/phi_jepa/simulation/mjx.py`, `scenes.py`,
  `tools/check_dataset_quadruped.py`.
- **Expected behavior and source requirement:** nominal periodic-PD locomotion
  must advance ≥0.2 m in 3 s without falling and have consistent refined labels;
  `SPECIFICATION.md` sections 5 and 9.
- **Exact command/minimal reproducer:** in WSL,
  `XLA_PYTHON_CLIENT_PREALLOCATE=false PYTHONPATH=src .dataset-wsl-venv/bin/python tools/check_dataset_quadruped.py`.
- **Observed behavior/log:** nominal unperturbed 1 ms MJX run advanced
  0.994174948 m without falling; 0.5 ms run advanced 0.846303214 m but fell.
  Discrete labels and endpoint tolerances disagree. This is a physics/controller
  validation failure, not a missing GPU or compilation claim.
- **Environment:** WSL Ubuntu, Python 3.12.3, MuJoCo/MJX 3.14.0,
  JAX/JAXlib 0.11.2, CUDA RTX 5090; exact locks and measured device evidence linked.
- **Attempts and outcomes:** real GPU step; four batch profiles; 16 bounded native
  periodic-controller candidates; real 20-scenario MJX smoke; independent finer
  nominal check. The gates still fail.
- **Root cause:** controller/contact behavior is sensitive to numerical step;
  the precise solver/contact/gait contribution remains unresolved.
- **Impact:** quadruped benchmark export and five-domain final release are
  blocked. Its executable adapter, public contract and diagnostics remain usable.
  The other four domain implementations and development outputs are independent.
- **Option A:** further bounded contact/solver/gait calibration within the
  transparent periodic-PD scope, preserving all failed cases and tolerances.
- **Option B:** a different pinned quadruped geometry or gait family, with new
  model manifests and full revalidation; no learned-policy substitution.
- **Recommendation:** Option A first; it preserves the selected engine and
  scientific scope. Do not expand to a 100-case quadruped calibration while the
  nominal reference itself is unstable.
- **Smallest question:** no new scientific decision is needed to understand this
  blocker; planner/user review should choose the next bounded calibration study
  if work continues beyond this initial pilot.
- **Evidence to close:** sustained nominal MJX locomotion at refined settings,
  consistent continuous/discrete labels, then the configured 100-scenario
  calibration with disclosed acceptance/rejection rates.

Release also requires granted asset licensing, committed/frozen configuration
and approved all-domain manifests. The supplied provisional configuration remains
unchanged and disabled. The next step is review of these artifacts and the
quadruped blocker, not model training or a production run.
