# Φ-JEPA dataset design package — revision 1.1.0

Start with MODEL_DATA_CONTRACT.md and SPECIFICATION.md, then give CODEX_PROMPT.md and this package to Codex in the Φ-JEPA repository.

The ZIP filename retains v1 as the major package version; its contents now contain design revision 1.1.0. The JSON record schema remains 1.0.0. This revision supersedes the original physical-state training interpretation.

## Files

- MODEL_DATA_CONTRACT.md: confirmed numerical-plus-answer-embedding objective, registries, source boundaries and tests.
- SPECIFICATION.md: scope, contract, scenes, parameters, splits, labels, validation and resource plan.
- dataset.schema.json: strict JSON Schema Draft 2020-12; root validates a complete record.
- pilot_config.json: proposed settings and counts, with final generation disabled.
- example_record.json: schematic future-prediction record; values are invented to illustrate structure, not simulated.
- example_public_input.json: input-only export of that example.
- example_keyed_bundle.json: numbered wrapper preserving the requested sample organization.
- CODEX_PROMPT.md: implementation task and acceptance criteria.
- VALIDATION.md: checks actually performed on this package.
- SHA256SUMS.txt: artifact checksums, excluding this checksum file itself.

To validate a public record or numbered bundle with the same schema, replace its top-level $ref with #/$defs/public_record or #/$defs/bundle in the validator's in-memory schema. Do not change the definitions.

JSON Schema verifies structure. The semantic and production-admission gates in SPECIFICATION.md remain required. The examples deliberately have record_origin=illustrative_only and incomplete runtime provenance; they must never enter a real benchmark.

Confirmed scope: five domains, no slosh/fluid, MuJoCo/PyBullet/MJX with one primary engine per domain, future prediction, and private reference outcomes. Concrete simulation settings remain pilot defaults. No simulator or GPU execution was performed for this design package.

## Implemented dataset generator

The paragraph above describes the supplied design package. Implementation and
measured development pilots now live under `src/phi_jepa/simulation/`. The actual
task file is `DATASET_CODEX_PROMPT.md`. See [the execution report](docs/reviews/PDS_completion.md)
and [recorded decisions](docs/decisions/Dataset_preparation.md) for tested paths,
counts, calibration changes and failed gates. Production generation remains off.

Use an editable installation from this repository; the CLI reads the preserved
schema, prompts and configuration here. No API credentials or online tracking
are needed. Three independent working environment locks are included. The
existing P00 environment and legacy code are not replaced.

Windows PowerShell, native MuJoCo and offline contracts:

```powershell
# Use any available Python 3.12; this checkout already has .p00-venv.
.p00-venv/Scripts/python.exe -m venv .dataset-venv
.dataset-venv/Scripts/python.exe -m pip install -r configs/dataset-windows.lock.txt
.dataset-venv/Scripts/python.exe -m pip install --no-build-isolation --no-deps -e .
.dataset-venv/Scripts/phi-dataset.exe inspect-environment
.dataset-venv/Scripts/phi-dataset.exe validate-schema
.dataset-venv/Scripts/phi-dataset.exe smoke --domain robotic_arm --scenarios 20 --config configs/dataset_refined_pilot.json --output dataset-runs/my-arm-smoke
.dataset-venv/Scripts/phi-dataset.exe calibrate --domain tethered_load --scenarios 100 --output dataset-runs/my-tether-calibration
.dataset-venv/Scripts/phi-dataset.exe validate-dataset --path dataset-runs/my-arm-smoke
.dataset-venv/Scripts/phi-dataset.exe export-public --path dataset-runs/my-arm-smoke
.dataset-venv/Scripts/python.exe -m unittest discover -s tests -v
```

PyBullet runs in WSL Ubuntu with Python 3.11 because the attempted Python 3.12
installations required unavailable compilers. Normal installation, from WSL:

```bash
cd /mnt/c/Users/aashraf/Desktop/Work/phi-jepa/phi-jepa
# uv may install the requested Python if 3.11 is not already installed.
uv venv --python 3.11 .dataset-bullet-venv
uv pip install --python .dataset-bullet-venv/bin/python -r configs/dataset-bullet-linux.lock.txt
uv pip install --python .dataset-bullet-venv/bin/python --no-build-isolation --no-deps -e .
.dataset-bullet-venv/bin/phi-dataset smoke --domain driving --scenarios 20 --config configs/dataset_refined_pilot.json --output dataset-runs/my-driving-smoke
.dataset-bullet-venv/bin/phi-dataset calibrate --domain object_pushing_stacking --scenarios 100 --output dataset-runs/my-object-calibration
.dataset-bullet-venv/bin/phi-dataset compare-engines --domain robotic_arm --pairs 20 --config configs/dataset_refined_pilot.json --output dataset-runs/my-arm-comparison
```

MJX-JAX uses a separate WSL Python 3.12 environment; the lock includes CUDA 12
packages. It was tested on this workstation, not assumed from its driver name:

```bash
python3 -m venv .dataset-wsl-venv
.dataset-wsl-venv/bin/python -m pip install -r configs/dataset-mjx-linux.lock.txt
.dataset-wsl-venv/bin/python -m pip install --no-build-isolation --no-deps -e .
export XLA_PYTHON_CLIENT_PREALLOCATE=false
.dataset-wsl-venv/bin/phi-dataset inspect-environment --device-step
.dataset-wsl-venv/bin/python tools/study_dataset_quadruped.py --output dataset-runs/my-quadruped-study
# This command verifies nominal refinement evidence before running smoke (20),
# then calibration (100). Failed nominal qualification stops before either run.
.dataset-wsl-venv/bin/python tools/run_qualified_quadruped_pilots.py --study dataset-runs/my-quadruped-study --output dataset-runs/my-qualified-quadruped-pilots
```

`python -m phi_jepa.simulation.cli` is equivalent to `phi-dataset`. The delivered
pilots are under `dataset-runs/final/<domain>/{smoke,calibrate}`; exploratory
failures are also retained under `dataset-runs/`. These large local outputs are
gitignored; durable compact evidence is linked in the completion report.

Quadruped refinement uses a fixed physical controller clock with held torques.
The bounded study in `configs/quadruped_refinement_study.json` compares 1, 0.5
and 0.25 ms integration at a fixed 1 ms controller period, records synchronized
1 ms states/commands/foot contacts, and changes one contact/solver/gait setting
at a time. The general adapter default controller period is 2 ms; explicitly
configure `quadruped_settings.controller_period_s` for a different experiment.
The old quadruped manifests/registries describe the earlier controller and are
not qualification evidence for this revision. See
[fixed-clock decisions](docs/decisions/Quadruped_fixed_clock.md).
`tools/audit_quadruped_study.py <study-directory>` independently checks saved
torque laws and contact timestamps; `tools/verify_quadruped_clock.py --output
<new-json-path>` runs two short instrumented MJX force/hold checks. These audits
are distinct from nominal qualification and varied-scenario performance.

The measured follow-up remains **implemented_pending_validation**: an initial
nominal pass failed subsequent repeats, including 0.125 ms; smoke admitted 5/20
scenarios and quarantined 15. The 100-case calibration remains gated. A revoked
qualification blocks the pilot wrapper. See the
[measured follow-up report](docs/reviews/PDS_quadruped_refinement_completion.md)
for unchanged tolerances, all failed configurations and the remaining blocker.

Add `--resume` to a smoke/calibration command with exactly the same source,
configuration, mode, domain and scenario count. Completed receipts are verified;
rejects are not silently rerun. Changed source/configuration needs a new output
directory. A scenario interrupted before its receipt may be rerun atomically.
Pilot limits include a 20 GiB output cap, 200 GiB free-space floor and 1,800-second
per-command wall budget. Counts and memory candidates are configured, not guessed
from the workstation specification.

Each run contains per-scenario `shards/*.jsonl`, model `assets/`, `partitions.json`,
`diagnostics/`, checksummed `receipts/`, `rejections.jsonl` when applicable,
quarantined records, source/config/environment records and a checksum manifest.
`inputs.jsonl` contains only public inputs; `references.jsonl` and `evaluator.jsonl`
are private. Models must receive only `inputs.jsonl`, whose context already
contains the shared model prior. Never pass full shards to an inference client.

`registry.json` freezes numeric columns and bindings. `target-texts.jsonl`
contains private training preparation: identical numeric input/target blocks,
serialized Q/C and Q/C/A, and **no embeddings**. `extracted-adapter.json` pins the
original extraction schema/prompt and strict canonical aliases. Unmapped
free-form names require an explicit reviewed binding revision; missing fields
are never completed from future simulation. A real frozen encoder must be
configured before `embed_pair` can export vectors. Token counts and model loss
are not reported without that encoder. Descriptive explanations are not verified
CoConuT/CODI solution traces.

The explicit future release command is:

```bash
phi-dataset generate --config configs/frozen-release.json --resume
```

There is deliberately no enabled `frozen-release.json` yet. It must specify
`status: frozen`, `final_generation_enabled: true`, `release_output`, all five
`validated_domain_manifests`, and five development-frozen `numeric_registries`.
Source and config must be committed; manifests must include passed calibration
and physical checks, cleared gates and granted asset licensing. The command
checks these before dispatching configured train/validation/ID/OOD partitions.
Do not create a success manifest to bypass failed physics evidence. No production
scale run, neural training or claimed model performance is part of this work.
