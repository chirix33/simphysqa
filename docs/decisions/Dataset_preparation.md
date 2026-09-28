# Dataset preparation decisions — 24 September 2026

Authorized by the user on `dataset-prep`, starting at
`983feaec76acfd923cc7b7d18844ddd92696daff`. The pre-existing README edit and all
untracked specification/example files are preserved. No commit, push, model
training, provider call or production generation is authorized or performed.

1. **Authority:** `DATASET_CODEX_PROMPT.md`, `SPECIFICATION.md` and
   `MODEL_DATA_CONTRACT.md` revision 1.1.0 govern this dataset work. They supersede
   older physical-readout training instructions for the future model. Historical
   P00/P01 code and reports remain intact. This does not implement P02–P08.
2. **Isolation/reuse:** `phi_jepa.simulation` contains disclosed benchmark physics.
   Reuse P00 canonical JSON, hashes and code provenance, but do not reuse the
   passive-stopping generator as a four-wheel simulator or its truth contracts as
   the new schema. `phi-dataset` is separate from the existing `phi-jepa` commands.
3. **Source contracts:** full records retain the supplied Draft 2020-12 schema.
   Public exports allowlist `schema_version`, `sample_id`, `input`. References and
   evaluator metadata are physically separate files. Complete authored XML/URDF
   or construction JSON, compiled numeric physical parameters, controls and all
   scheduled interventions are public. Model-array conventions are explicit.
4. **Extraction clarification:** the user instructed retrieval of the actual older
   extraction envelope, not reconstruction from its five headings. The exact
   originals were located at `docs/assets/extract_schema.json` and
   `docs/assets/prompts.json`. Their existing manifest hashes are checked at
   runtime. Source root is the validated extraction object, with no API wrapper.
   Since its free-form names contain no formal entity IDs, frozen explicit aliases
   bind `(name, unit, relation)` or event description to stable registry columns.
   Generated canonical-key alias manifests are strict interfaces, not a claim
   that an unmodified live extractor naturally returns every canonical alias.
   Missing, ambiguous and extra numeric facts fail; no future reference supplies
   an absent input. Live extraction coverage remains unmeasured.
5. **Numeric target:** simulator registry root is `input`. Entity/measurement
   lists bind by semantic identity; observation slots and ordinary arrays retain
   explicit indices. All numeric leaves, including steps, times, controls,
   tolerances and public model properties, enter `n`. Booleans and strings do not.
   `x0` and `y` use exactly equal copies of `n`; Q/C and Q/C/A are serialized for
   one frozen embedding apiece. No real encoder is selected or called. No loss,
   decoder, normalization, tree encoder or auxiliary physical objective is added.
6. **Sampling:** `configs/dataset_sampling.json` pins grouping granularity,
   admitted quadrants, held-out pairings, allocation and subfamily cycling.
   Geometry/control laws are intentionally shared public priors; independent
   parameter draws and schedules are the held-out families. Development and
   release namespaces differ. Structural OOD fails closed. Sorted parameter keys
   make random draws invariant to JSON object serialization order.
7. **Numerics:** the provisional 2 ms arm step failed refinement around joint
   limits. Trials at 0.5 ms and 0.1 ms are retained; final arm/driving development
   configuration uses 0.1 ms with 0.05 ms refinement. Other domains initially use
   2 ms / 1 ms. Acceptance compares requested endpoints using half the specified
   tolerance, sign-invariant quaternion angles, equal discrete outcomes and event
   times within 0.01 s. Intermediate discrepancies remain diagnostic. Threshold
   and contact failures are quarantined; no repeated resampling hides them.
8. **Scene calibration:** driving uses an infinite plane, cylindrical wheels,
   zero-velocity axle brakes capped at 0.25 N m, wheel contact stiffness 10,000
   N/m and damping 100 N s/m. These values and all inertias are public. Object
   support is upward normal force with 0.01 N onset / 0.005 N release hysteresis,
   plus a 1 mm footprint margin. The tether is a constrained point pendulum;
   MuJoCo mass/bias dynamics supply its reduced acceleration in RK4 under the
   analytic prescribed support motion. It is not elastic or slack cable physics.
9. **Gait development:** a bounded 16-candidate native-MuJoCo sweep tunes only
   transparent periodic references and PD gains; no learned controller is used.
   The selected candidate has hip `-0.25+0.3 sin(a)`, knee
   `0.5+0.2 sin(a-pi/2)`, gains 50/2 and torque saturation ±8 N m. Native success
   is not MJX validation. Failed MJX pilots remain explicit evidence; export
   requires a separate nominal gate and numerical agreement. Physical falls are
   valid labels, not per-case exclusion criteria when those gates are satisfied.
10. **Environments:** native Windows Python 3.12 for MuJoCo; isolated WSL Python
    3.11 for an available PyBullet wheel; separate WSL Python 3.12 for MJX-JAX
    CUDA. Lower the package minimum to 3.11 because this source works and is
    tested there. Do not alter existing core/CoConuT/CODI environments or drivers.
    Package locks come from installed environments. MJX uses JAX, not Warp;
    disable large GPU preallocation after allocator warnings in the first probe.
11. **Durability:** atomic one-scenario JSONL shards, checksummed receipts,
    append-only rejections, source/config identity checks on resume, local logs,
    runtime/memory/disk measurements and source snapshots. Release requires
    committed source/config, all domain evidence, frozen registries and resolved
    asset redistribution licensing. Authored model assets are currently marked
    unlicensed rather than inventing a grant. Production remains disabled.

Outstanding model dependencies: real frozen text encoder and settings, measured
token lengths/embedding sensitivity, live extraction alias coverage, and the
semantic-representation-to-answer adapter. These are not simulator fallbacks.
