# SPQ02 consolidated user specification

Authority: user's consolidated chat specification, 5 October 2026.
Continue on simphysqa-naacl from e379013b7e80fe28172682cd39e42f4066fde841.
Preserve association export 1.1.1 and all prior outputs.

Scope: eight verified counterfactual pairs, two per domain.

## Pair selection
- Select from the existing 16 SPQ01 development trajectories.
- Use deterministic selection with seed 20261004 and record the method.
- Freeze the eight selected trajectory IDs before simulator execution.
- Preserve parent/group identity and existing formal-audit exclusions.
- Report qualification failures; do not silently replace failed cases.

## Replay and tolerances
- First qualify original-scenario replay on one selected case per domain,
  then verify the remaining selected cases.
- Use existing simulator/reference verification and admission procedures,
  including coarse/fine checks where prescribed.
- Record exact simulator versions, configurations, thresholds and results.
- Keep QA answer-scoring tolerances distinct from simulator admission and
  replay validation. Passing an answer tolerance alone is insufficient
  evidence of reproducible simulation.
- Do not loosen thresholds or rewrite references to make replay pass.
- If a required replay criterion is absent, identify the missing criterion
  and propose it explicitly rather than inventing an undocumented value.

## Intervention isolation
Run an explicit no-intervention alternative:
- arm: omit the additional pulse, retain base controls;
- driving: omit scheduled braking;
- pushing/stacking: omit the scheduled external push;
- tethered load: omit scheduled support motion.

Hold initial conditions, physical parameters, other controls, seeds,
solver settings and horizons fixed. Record all changed fields.
Verify the alternative using the existing admission procedures.

## Arm semantics
Trace the pulse through the simulator implementation to resolve the
world/joint_local metadata distinction. Preserve raw source provenance.
Do not infer a conversion or physical interpretation without evidence.

## Counterfactual QA
- Create one new question per qualified pair, targeting a supported
  quantity at an existing target time after intervention onset.
- State the alternative intervention explicitly.
- Derive the reference from the verified alternative simulation.
- Preserve the permitted observed prefix and observation cutoff.
- Assign new QA/alternative-run IDs while retaining parent/group links.
- Keep alternative outcomes and verification evidence private.
- Integrate schema validation, evidence bindings, audit packets, public
  request preparation and applicable numerical/Boolean scoring.

## Observed-event coverage
Inspect existing admitted public views for real active, ended and
between-state events. Report availability by domain.
Do not expand established QA cutoffs or expose private outcomes.
If none exist, document the gap and propose separately identified new
views. This does not block independently qualified counterfactual work.

## Deliverables and limits
Deliver the commit, exact commands, frozen selection manifest, replay
results, intervention differences, alternative admission results,
counterfactual packets and execution/runtime accounting.

Count every simulation execution, including verification runs.
Continue qualified domains independently if another domain is blocked.
No answering-model benchmarks, full-release regeneration, or definitive
formal-audit sampling. Report completed/failed/pending counts accurately.

## User-confirmed exact replay clarification

Use exact canonical equality as the initial factual-replay criterion. Replay with
original generation configuration and pinned simulator, dependency, solver and seed
settings where recoverable; record the environment comparison. Compare saved
physical states, event records, public model/controller definitions and structured
labels. Canonicalization may normalize JSON key order/formatting, but must not round
numerical values or conflate Boolean and numeric types. Exclude only documented
non-scientific metadata (runtime, creation time, output paths); no physical fields.
On mismatch report first differing fields, numeric differences by quantity/unit/
timestamp, Boolean/event differences and configuration/environment differences.
Do not modify references or silently introduce tolerance. Classify not exactly
reproduced and diagnose; propose an evidenced explicit numeric replay criterion
before using such a case for export. Retain separate factual and alternative
coarse/fine admission. Continue independently with domains that qualify.
