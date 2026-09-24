# Φ-JEPA simulation dataset specification — design revision 1.1.0

> Release amendment, 24 September 2026: the first release includes robotic arm
> (MuJoCo), driving (PyBullet), object pushing/stacking (PyBullet), and tethered
> load (MuJoCo). Quadruped locomotion and further MJX qualification are deferred.
> The retained current quadruped configuration failed unchanged numerical gates;
> this is not a claim that MJX generally cannot support locomotion. Historical
> quadruped records, including five admitted smoke groups, are development only.
> No further quadruped experiments, production generation, or training are authorized
> in this scope update. See docs/reviews/PDS_four_domain_completion.md.


Prepared 24 September 2026; updated after the user confirmed the numeric-plus-answer-embedding objective. Status: design contract and provisional pilot configuration, not a completed dataset. No simulations, GPU checks, or training were run while preparing this package. No project source code was changed.

Release preparation amendment: the budget is **6,800 attempted base scenarios**.
Preserve all attempted draws and quarantine failures; do not resample to fill
quotas. Actual admitted counts must be reported separately. CC BY 4.0 dataset/assets
and MIT generation-code notices are prepared but not granted until the exact
rights-holder and authority are confirmed; see `LICENSE.md`. The configuration
is frozen for review and production remains disabled.

## 1. Scope and authority

The user's decisions in this session supersede the older domain list in the 22 September decision ledger:

- Four release domains: robotic arm, driving, object pushing/stacking, and tethered load/swinging payload. Quadruped requirements below are retained for deferred development only.
- Liquid slosh and its former mechanical proxy are excluded.
- Release engines: MuJoCo and PyBullet; MJX is deferred; one primary engine per domain, with selected matched cross-simulator studies.
- Future-state prediction is the primary task. Future event prediction is secondary. Observed-outcome counting and counterfactual questions are outside this first release.
- Keep the requested readable fields: global_context, question, states, explanation, label. Place inputs and reference outputs in distinct objects and exports.
- User-reported workstation: RTX 5090, 32,607 MiB VRAM, driver 610.60, approximately 1.89 TB free storage. OS, CPU, RAM, and actual runtime compatibility remain unmeasured.
- Source-code implementation belongs in Codex. This package supplies its specification and task prompt.

The approved engine strategy is settled. The concrete mapping, scene designs, numerical ranges, thresholds, and counts below are implementation defaults to validate in the pilot. They are not scientifically verified optima. The confirmed training interface is now defined in MODEL_DATA_CONTRACT.md: the ODE predicts a final vector whose numeric block reconstructs its numeric input and whose semantic block targets Embed(question + public context + answer). This supersedes the earlier terminal physical-state MSE interpretation. Retain terminal physical labels and full simulator reference trajectories for answer construction and independent evaluation. Schema repair, EBM policy, model implementation and baseline training remain outside this dataset task.

## 2. Deliverables and record organization

`dataset.schema.json` is JSON Schema Draft 2020-12. Its default root validates one complete record. Definitions `public_record` and `bundle` validate public exports and a numbered wrapper matching the user's example.

A complete record has:

- `schema_version`, `sample_id`: contract version and opaque stable identifier.
- `input`: public problem, entities and properties, initial/observed states, coordinate conventions, control specification, known future events, and answer specification.
- `reference`: held-out future states, actual events, structured and readable labels, descriptive explanation, evidence, and optional verified solution trace.
- `metadata`: scenario grouping, split and shift annotations, engine/model provenance, and validation.

The user's global_context/question/states reside in `input`; label/explanation reside in `reference`. `reference.states` covers the future after the observation cutoff through the last requested target. `input.states` covers saved observations at or before the cutoff. Both use the same state representation.

Use JSONL shards for generation, with one full record per line; include a numbered JSON export for small review batches. JSONL is still JSON per record and avoids rewriting an enormous object after each run. Generate physically separate `inputs.jsonl` and `references.jsonl` files for model evaluation, joined by opaque sample ID. Keep provenance and OOD annotations in an evaluator manifest. Model clients receive only the public export. Do not hand them the full record and ask them to ignore the reference.

Use a single canonical record builder and deterministic input exporter. Allowlist public fields; do not build public context by summarizing full trajectories. The dataset contract is distinct from the LLM's extracted schema (observations, events, relations, symmetries_or_invariances, unknowns). Dataset preparation must not replace frozen LLM extraction with an oracle schema.

## 3. Time and state meaning

All times are seconds relative to the recorded initial state. Save the actual initialized, settled state at t=0 before integration. If settling is used, record its method and duration privately; the public initial state must describe the state after settling.

Default pilot integration step: 0.002 s. Saved state interval: 0.02 s. Observation cutoff: 0.2 s. Candidate prediction times: 1.0 and 2.0 s; quadruped additionally 3.0 s. These are absolute times; prediction horizon is target minus cutoff. Every question states its requested time explicitly. Events occur on the integration grid; store the actual applied times. Integrate exactly to requested target times or reject misaligned configurations. Do not silently round a question time.

Record exact step_index, timestamp and state_id. State IDs and sample IDs must not encode outcomes, OOD classes, or physical values. Scalar/vector quantities carry entity ID, name, value, unit and frame. Use SI; world frame is right-handed x-forward/y-left/z-up. Declare quaternion order (xyzw), joint sign convention, angle wrapping policy and any adapter conversion in the frozen domain manifest. Unknown is null, never a guessed zero. Missing/nonfinite requested labels invalidate the record.

Do not assume the engine's packed qpos/qvel arrays already use the shared convention. Publish channel names and mappings in the model manifest. Contact events are detected every integration step, even when fewer states are exported. Event counts must use contact onset plus hysteresis, not one event per contact point or time sample.

## 4. Answerability and information access

For the primary deterministic prediction track, provide physical parameters and state variables that materially determine the requested outcome, along with all future applied controls or a completely specified feedback law. In particular:

- The driving question includes braking timing and law.
- The quadruped question includes reference trajectories, PD gains, joint ordering, saturation and control update period.
- The tether question includes the support motion, not merely a statement that the cart will move.
- Disturbance times, durations, magnitudes and application points are public if they affect the requested future.

A controller name or private checkpoint hash alone does not make a problem answerable. Any internal controller state must be provided; the pilot uses memoryless feedback or explicit controls. No actor policy training is required for this dataset task. If a learned controller is later introduced, it requires a new controller-access protocol shared by all methods.

Public entity properties must resolve geometry, masses/inertias, joint limits, damping, actuator properties, friction and other relevant model assumptions. Do not rely on an inaccessible asset path to convey them. Full model assets remain available for reproduction, while a versioned public model description supplies the benchmark's shared prior. Specify any parameters held fixed across every sample there and distribute that description to all methods. The public input assembly includes that prior; token budgets must be measured.

Hidden disturbances or deliberately unobserved states create a different, partially observed task. Do not include them in this first deterministic track. Freeze both the exact measurements available and their serialization; equal questions alone do not guarantee equal input information across baselines.

## 5. Domain manifests and first scenes

Create one manifest per domain with every fixed model parameter, every sampled parameter, model source/license/hash, observable channel list, target list, controller definition, label functions and validation tests. Any unset required item blocks that domain's export, not unrelated domains.

| Domain | Primary engine | Initial scene and scope | Primary numeric targets | Secondary event targets |
|---|---|---|---|---|
| Robotic arm | MuJoCo native | Custom planar two-link arm; model dimensions and inertias pinned; commanded joint torques, optional attached payload | Joint angles and angular velocities at T; end-effector position at T | Joint-limit contact by T |
| Driving | PyBullet | Four-wheel vehicle on a flat surface, low-speed straight braking, explicit wheel geometry and control | Forward position and speed at T | Stopped by T; stop time when observed |
| Object pushing/stacking | PyBullet | Two rigid blocks on a table, with distinct pushing and pre-stacked subfamilies | Each block's position and orientation at T | Support lost, object left table, or stable stack at T |
| Quadruped locomotion (deferred, excluded from release) | MJX-JAX development only | One pinned quadruped on level ground; fully specified periodic reference and PD control | Base position, velocity, roll and pitch at T | Fall by T; sustained locomotion criterion |
| Tethered load | MuJoCo native | Moving support with one load; fixed-length taut suspension approximation | Load position, swing angle and angular velocity at T | Crossing a declared spatial boundary |

Robotic-arm pilot is implemented and checked first. Then add other domains using the same contract. Pushing/stacking contains two explicit task subfamilies; report their coverage separately.

The quadruped model revision, geometry and gait parameters must be pinned by implementation and checked before export. A controller that only causes falls cannot be presented as a locomotion benchmark. The pilot must demonstrate sustained forward motion on nominal conditions; preserve physical falls under perturbation as outcomes. If no simple gait passes, report the blocker instead of silently switching to a learned policy.

The tether scene covers a taut suspended payload, not elastic cables or slack-to-taut impacts. Confirm positive tension throughout its admitted parameter range; label negative/zero-tension cases outside this model's validity envelope. A slack cable requires a different validated scene version. Keep prescribed support motion bounded and public.

## 6. Initial sampling ranges and OOD construction

`pilot_config.json` contains proposed ranges and time settings. Uniform sampling refers to values within the listed closed ranges; boundaries are handled consistently. Fixed geometry, inertia and controller constants are pinned per manifest. Final ranges are frozen only after calibration.

| Domain | ID ranges varied | Parameter OOD range |
|---|---|---|
| Arm | Payload 0–0.5 kg; initial angle -0.4–0.4 rad; angular velocity -0.2–0.2 rad/s; commanded torque -1–1 N m | Payload 0.6–0.8 kg |
| Driving | Initial speed 1–3 m/s; lateral friction 0.5–0.9; mass multiplier 0.9–1.1 | Friction 0.2–0.35 |
| Objects | Block mass 0.2–0.6 kg; friction 0.4–0.8; push 0.5–2 N | Mass 0.8–1 kg |
| Quadruped | Added payload/body mass 0–0.1; friction 0.6–1; joint-reference frequency 0.8–1.2 Hz | Added payload/body mass 0.15–0.2 |
| Tether | Length 0.5–1 m; mass 0.5–1.5 kg; initial swing -0.2–0.2 rad; support acceleration 0.2–0.6 m/s² | Length 1.2–1.5 m |

All mass changes must update inertias and payload placement consistently with the chosen physical construction. Changing an arbitrary mass field alone is not a validated payload experiment. Friction parameters are engine-specific model settings, not universal physical equivalents.

Define three first-release OOD subsets:

1. Parameter extrapolation: vary only the named held-out parameter outside ID support; other sampled factors use ID rules.
2. Unseen combination: hold out the upper-right quarter of two ID parameter ranges. Divide each range at its midpoint; train/validation/ID use the other three quadrants equally. The OOD set uses the omitted high/high quadrant. Pairs: arm(payload, torque magnitude); driving(initial speed, mass multiplier); objects(block mass, push magnitude); quadruped(payload fraction, gait frequency); tether(length, support acceleration). Keep signed torque direction balanced separately. ID is the intentionally restricted joint distribution, not its entire rectangular envelope.
3. Timed-event shift: use familiar event types and magnitudes, with onset in the later window specified in the config. Train/validation/ID use the earlier window. Keep unrelated factors within ID support. For event-conditioned questions, use target T=2 s (quadruped T=3 s), so the full event precedes the target. Do not call a shifted event structural OOD.

Structural OOD is reserved but disabled initially. Different object counts, joints or connections require model/schema coverage, readout compatibility and answerability checks. A numeric parameter change is not structural. Registry/readout dimensions are fixed per domain under MODEL_DATA_CONTRACT.md; structural changes need explicit representation support.

Scenario grouping precedes paraphrases and matched simulator runs. Every derived variant inherits a split group, and train/validation/test groups are disjoint. For OOD suites, reserve distinct source families; never create a test variant from a training base instance. Source-family IDs include shared geometric layouts and control templates when those are intended to be held out. Log the chosen grouping granularity.

Freeze shift definitions before final generation; final test results never tune them. Calibration/development samples cannot be reused as final test data. Publish subgroup counts and acceptance/rejection rates, so filtering does not hide difficult conditions.

## 7. Labels and evaluation rules

Label code reads simulator state through a canonical adapter and is tested independently of question templates. Keep numerical values unrounded in structured_label; readable labels use documented display rounding. Never treat an LLM-generated explanation as numerical ground truth.

Proposed pilot thresholds, all subject to numerical validation:

- Angular endpoint accuracy: absolute tolerance 0.01 rad. Angle comparisons use declared wrap semantics; quaternion targets use rotation-angle distance and are invariant to quaternion sign.
- Position: 0.01 m; linear velocity: 0.02 m/s; angular velocity: 0.02 rad/s; event time: 0.02 s. Relative tolerance defaults to zero. Use per-target vector norms, not unreported componentwise mixtures.
- Driving stopped: forward speed magnitude below 0.02 m/s and planar speed below 0.03 m/s continuously for 0.2 s. Report earliest qualifying interval's end. If never stopped by T, return a boolean false; do not fabricate a stop time or include null in numeric physical-error evaluation.
- Stable stack: intended supporting contact exists, upper block tilt below 10 degrees, centre-of-mass projection inside the designated support footprint, speed below 0.02 m/s for 0.2 s, with contact threshold and geometry tolerance pinned in the model manifest.
- Quadruped fall: base height below 0.5 times nominal standing height OR absolute roll/pitch above 60 degrees for 0.1 s. These are operational benchmark definitions, not universal robotics standards.
- Nominal locomotion qualification: forward displacement at least 0.2 m over 3 s without meeting the fall rule. Calibration may adjust this and the controller jointly before freeze.
- Boundary crossing: signed centre-of-mass coordinate passes the public threshold with 0.005 m hysteresis. Record detection at integration resolution; public reporting follows event-time tolerance.

Answer rules and operational success definitions belong in public answer_spec, so all methods know the requested criterion. Exact contact/geometry definitions live in versioned manifests and must be included in the shared prior when relevant. Contact threshold values require measured engine-specific calibration.

For independent physical evaluation, compare parsed physical predictions with simulator quantities; text or embedding agreement is not a substitute. Save named terminal physical references for all records, plus task-specific event labels. These yield the answer text in the semantic training target; they do not replace the unchanged numeric block of that target. Split multiple targets into distinct questions when needed to keep answers compact; report base-scenario counts separately from question counts.

Score numeric targets with per-quantity RMSE/MAE and native units. Normalization statistics come from training only. Report invalid outputs and parse coverage; do not silently remove failed model answers from denominators. Physical-constraint evaluation requires actual predicted quantities and applicable constraints. If no constraints can be checked, mark coverage unavailable rather than perfect compliance.

## 8. Explanations, context, and Coconut/CODI compatibility

For pilot generation, use deterministic language templates. Inputs are rendered only from approved public facts; references are rendered from private measured labels and evidence. A future outcome must never appear in input.states.context, global_context, entity names or question wording.

Reference explanations initially describe supporting outcomes and events. They do not assert untested causal explanations. A simulation time series is not automatically a solution derivation.

Retain `solution_trace` as an explicit optional resource. Default is status unavailable, empty steps, null verification record. Do not fill it with generic phrases or a restatement of the final answer. Neither Coconut nor CODI training is part of this generator implementation. Verified traces can be added later with named verification evidence and a documented supervision policy. If only a subset receives traces, report baseline training coverage and give comparable trace-based methods the same eligible training pool. Do not restrict test questions silently to easy trace-producing cases.

Optional LLM paraphrases are later derivatives, with shared split groups and automated factual checks. Log prompt/version/provider, costs and validation; they cannot revise simulator values or labels.

## 9. Validation and release gates

JSON Schema checks shapes/types. Separate semantic validation is mandatory:

- Unique IDs and valid entity, target and evidence references; bundle keys need not equal opaque sample IDs.
- Strictly increasing state times/steps; t=0 exists; last public state is at cutoff; no future public measurements; targets strictly after cutoff; interval targets end after start.
- Point targets have equal start/end times; event intervals begin at or after cutoff. Known future event descriptions may reference future time because they specify interventions, not outcomes.
- Unit/frame consistency; vector lengths match domain channels; answer_type agrees with label value; reference labels exactly cover requested target IDs; no null primary numeric label.
- Controller and known-event coverage, public parameter completeness, asset/checksum/revision completeness, no nonfinite numbers.
- Production admission: record_origin=simulation; validation=accepted; all required checks pass; exact engine version, code revision and config hash present; at least one complete model asset; runtime/solver metadata present. Illustrative records are always rejected by release export.
- Immutable split assignment, duplicate scenario detection, and cross-split group exclusion across all shards/engines.
- A leakage test modifies private references/metadata while holding input fixed and verifies that public export bytes remain unchanged.

Per-domain physics checks: arm gravity/torque sign and simple limiting-case response; car braking cannot produce artificial reverse propulsion; objects correctly fall under gravity and report contact/support; quadruped gait and perturbation timing verified; tether tautness, length constraint and small-angle period checked in the static-support limit.

Repeat selected runs at half timestep and tighter solver settings. Starting numerical agreement gate: numeric labels differ by <= half the target accuracy tolerance, discrete labels agree, and event times differ by <= 0.01 s. Repeat at finer settings if needed. For threshold-adjacent or sensitive cases, record instability/ambiguity and quarantine with counts; do not repeatedly resample until every hard case disappears. State explicitly that convergence supports a numerical reference, not real-world validity. Compare against analytical limiting cases where available.

Physical task failure (fall, collision, missed stack) is a valid outcome. Numerical corruption, unintended actuator behavior, missing required fields and invalid scene assumptions are rejected runs. Keep an append-only rejection log with seed, parameters and reason. Export pilot examples only after required domain checks pass.

## 10. Cross-simulator protocol

First candidate: MuJoCo arm versus PyBullet arm, 20 matched development pairs. Use common physical geometry, mass/inertia, initial states, public actions, coordinate frames and saved times. Each engine produces its own reference label. Compare disagreement before attempting transfer evaluation; never copy MuJoCo labels to PyBullet.

MuJoCo versus MJX is useful backend consistency evidence but does not establish transfer to an independent physics-engine family. Log implementation (native, jax, warp) as well as engine name. A backend change creates a new generation run/version.

Reserve evaluation families before generating any final cross-simulator set; no near-identical training twins in the primary held-out transfer test. A paired diagnostic on previously seen scenarios must be explicitly labeled as such.

## 11. Pilot and proposed release budget

Progression: arm smoke run of 20 base scenarios -> arm calibration and validation -> other domain smoke runs -> calibration of each -> frozen manifests -> release generation. Smoke and calibration records use development split and do not measure generalization.

Smoke: 20 base scenarios/domain (10 nominal, 4 parameter shift, 3 combination shift, 3 event shift), at most two questions per scenario. All four release domains total 80 scenarios, up to 160 questions. This is a software/physics check, not a statistical comparison.

Calibration: 100 fresh development scenarios/domain, including nominal and each shift family. Suggested allocation 40/20/20/20. Measure labels, input lengths, rejection rates, wall time, disk growth and numerical agreement.

Proposed first release, disabled by default: per domain 1,000 train + 200 validation + 200 ID test + 100 parameter OOD + 100 combination OOD + 100 event OOD = 1,700 independent base scenarios. Across four domains: 6,800 planned base scenarios and up to 13,600 questions. Split totals: 4,000 train, 800 validation, 800 ID test, and 400 per OOD category. Calibration totals 400 planned development scenarios. Quadruped quota is removed without redistribution. Planned counts are not generated or admitted counts; no claim of statistical sufficiency is attached.

Headless generation; do not render every rollout. Stream shards and avoid retaining all trajectories in GPU RAM. CPU workers depend on measured CPU/RAM, which are not yet known. For deferred MJX development only, retain the historical batch profiles 1, 8, 32, 64; further profiling is deferred, reserving memory headroom; initial cap 75% of reported VRAM. Budget 20 GiB pilot output, 100 GiB proposed initial release, and retain at least 200 GiB free disk. These are conservative run limits, not predicted consumption.

Detect OS/Python/CPU/RAM/driver/GPU in Codex's actual execution environment, then pin compatible native MuJoCo/PyBullet packages. MJX device-step qualification is deferred. Do not assert that the reported driver guarantees compatibility. Record compilation separately from steady-state runtime. Verify deterministic-seed replay within declared tolerances; do not promise bitwise equality across platforms or engines.

Final generation requires a frozen manifest, successful pilot report, explicit release command, and final_generation_enabled=true in a committed config. This is a reproducibility gate, not a recurring request for permission. A failed gate blocks only the dependent generation and explains the concrete failure.

## 12. What is sealed and what the pilot freezes

Settled: four-domain first release, no fluid simulation, MuJoCo/PyBullet release engines with MJX deferred, future prediction, readable JSON, private labels, grouped splits and no source implementation in this document session.

Specified here for Codex implementation: JSON contract v1.0.0 plus model–dataset contract revision 1.1.0, proposed engine mapping, scenes, export layout, pilot workflow, provisional parameter ranges, time grids, label rules, OOD definitions and resource limits.

Pilot-frozen values: asset revisions, engine/package versions, exact fixed scene constants and controller parameters, accepted numeric tolerances/ranges, batch size, production counts and measured acceptance rates. They must appear in a release manifest; no null placeholders in production provenance.

Generator implementation can proceed under these defaults. Exact registry manifests and encoder settings must be pinned before vector/embedding export; the downstream semantic-to-answer adapter remains a model dependency as described in MODEL_DATA_CONTRACT.md. If a pilot requires a scientific scope change (learned controller, hidden-state uncertainty, elastic/slack tether, extra domains, different training supervision), flag it rather than quietly reinterpreting this contract.

## Sources and boundaries

Project source: Phi-JEPA-project-memory-and-decision-ledger.txt (22 September 2026), especially data/evaluation and baseline sections; corrected by explicit user decisions in this session. Original project instructions preserve the separation between simulator/evaluator engineering and learned-method engineering.

Official documentation checked 24 September 2026:
- MuJoCo MJX: https://mujoco.readthedocs.io/en/latest/mjx.html — MJX exposes JAX and Warp implementations with different capabilities; record the selected implementation.
- MuJoCo Playground: https://github.com/google-deepmind/mujoco_playground — candidate environment/model reference for the quadruped adapter.
- Bullet/PyBullet: https://github.com/bulletphysics/bullet3 — primary source for PyBullet and its examples.

All proposed dataset sizes, thresholds, scenes, split rules and configuration values in this document are design recommendations, not claims taken from these sources or experimental measurements.
