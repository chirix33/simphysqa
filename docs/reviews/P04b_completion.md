# Stage 5/P04b–P05a completion — 24 September 2026

Status: **complete for implementation and bounded development validation**.
Combined assessment is intentionally **partial and uncalibrated** on this release;
no full-study detector, uncertainty, fallback-benefit or physical-validity claim.
Branch `full-phi-jepa-from-dataset`, base/current HEAD
`7f2553ca6591301de588bd3362e72838354169a0`; changes remain uncommitted.
Stage 4 completed before Stage 5. Stage 6 has not started at this handoff.

## Behavior and authority

The user approved training-only predicted references, exact physical compatibility,
whole-scenario exclusion for training queries, full-2d terminal cosine, separate
block diagnostics, original V1 judge, explicit missing components, validation-only
calibration and no high-score numerical replacement. See
[the decision/method record](../decisions/P04b_assessment.md).

- `typed_evaluation.py`: scalar/vector/Boolean target binding, quaternion sign
  equivalence, native-unit errors, public tolerance success, complete-answer
  denominators and scenario-grouped bootstrap/macro/pooled reports. Autonomous
  versus recorded-input diagnostics are explicit; only named physical channels
  enter physical trajectory errors. Unsupported, missing and invalid cases remain.
- `assessment/reference.py`: immutable content-addressed training-prediction bank,
  checkpoint/P/E/solver/layout/profile invalidation, compatibility before k=1
  retrieval, scenario exclusion, full-vector score and additive block diagnostics.
- `assessment/checks.py`: independent limited physical checks; empty PCVR unavailable.
  Generic public contract operators cannot reinterpret observations as constraints.
- `assessment/fixed.py`: fixed combination, recorded validation calibration policy,
  partial/no-threshold behavior, bounded technical fallback and explicit deterministic
  answer formatter. No numerical replacement on high score.
- `providers/openai_judge.py`: exact adopted V1 prompt/schema, bounded calls/cache,
  separate component identity, no trajectory/reference judgment substitution.
- Readout now permits explicitly labeled recorded-input diagnostic mapping only
  through its separate flag. Such payloads are rejected by autonomous answer readout.

## Tests and actual bounded run

**97 offline P00–P04b tests passed in 14.045 seconds, zero skips.** New checks cover
training-only bank source, immutable contents, identity invalidation, filter order,
whole-scenario exclusion, stable ties, zero/nonfinite vectors, contribution sums,
partial semantics, calibration provenance/integrity and strict trigger, independent
checks, contract monotonicity, typed errors/quaternions, grouping, exact V1 scope,
fallback caps and preservation. Tests do not establish model performance.

One real training reference and one distinct tether validation query used the
existing tiny Stage 3 deployment checkpoint. Source selection verifies public
files and routing metadata only; no reference truth is opened by the assessment
process. Both 40-step rollouts were autonomous. Validation exactly replayed P03.

| Measurement | Result |
| --- | ---: |
| Training references / validation queries | 1 / 1 |
| Frozen-context retrieval cosine | 0.9976696551 |
| Full-2d terminal familiarity score | 0.000013084925 |
| Dynamic numerical block width / norm / score contribution | 13 / 121.074861 / 2.17313e-7 |
| Fixed-conditioning block width / norm / contribution | 127 / 6.232738 / 1.28352e-5 |
| Context block width / norm / contribution | 140 / 1.613803 / 3.24366e-8 |
| V1 scenario/schema inconsistency score | 0.0 |
| Generic contract checks | 0; unavailable |
| Combined assessment / threshold decision | partial / null |
| Calibration | uncalibrated; zero calibration scenarios |
| Tether length checks / violations | 40 / 0 |

The state timestamp/index norm is 121.051494, dominating the dynamic numerical
block. Fixed-conditioning terminal drift is 2.76390e-5 in raw L2; contextual drift
is 1.13727e-5. These are disclosed diagnostics, not silently normalized away.
Small familiarity is not physical correctness or calibrated uncertainty. V1's zero
score concerns only scenario/schema consistency. The tether check's zero violation
rate has narrow coverage and says nothing about missing contact outcomes.

Separate evaluator-only measured physical errors over 40 timestamps:

| Channel | Autonomous RMSE | Recorded-input one-step diagnostic RMSE |
| --- | ---: | ---: |
| Load position (m, vector Euclidean error) | 0.000668809 | 0.000062791 |
| Load swing angle (rad) | 0.003119891 | 0.000239666 |
| Load angular velocity (rad/s) | 0.010625094 | 0.003244455 |
| Support position (m) | 0.001949771 | 0.000139927 |
| Support velocity (m/s) | 0.007097230 | 0.002198391 |

These unit-specific errors coexist with P03's high mixed-coordinate MSE. Final
answer results reproduce P04a: all numerical targets within tolerance; public-only
Boolean unsupported; no forecast-benefit claim. One scenario cannot provide useful
scenario uncertainty, so bootstrap intervals are unavailable for this live profile.
Four-domain parsing/check interfaces are implemented; other domains/OOD have no
empirical Stage 5 forecast result yet. Quarantine remains untouched and separate.

Actual cost: 80 autonomous solves/320 NFE/320 sample-NFE, plus one separate batched
recorded-input solve/4 NFE/160 sample-NFE: **81 solves, 324 NFE, 480 sample-NFE**.
Three verified encoder cache hits across the two processes; zero new E calls or
training updates. One live judge call, 5262 input/241 output tokens, usage-priced
USD **0.025868**, no retry/failure. Judge cache replay is exact with zero API calls;
bank integrity and preservation during deterministic fallback also pass.

## Commands, evidence and remaining gates

Commands actually run in the isolated WSL core from repository root:

```text
python tools/run_p04b_assessment.py --profile /home/aashraf/phi-jepa/p02b-profile --training-run /home/aashraf/phi-jepa/p03-correctness-01 --answer-run /home/aashraf/phi-jepa/p04a-answers-01 --cache-dir /home/aashraf/phi-jepa/model-cache --output /home/aashraf/phi-jepa/p04b-assessment-01
python tools/evaluate_p04b_profile.py --run /home/aashraf/phi-jepa/p04b-assessment-01 --profile /home/aashraf/phi-jepa/p02b-profile --training-run /home/aashraf/phi-jepa/p03-correctness-01 --answer-run /home/aashraf/phi-jepa/p04a-answers-01 --cache-dir /home/aashraf/phi-jepa/model-cache
PYTHONPATH=src python -m unittest discover -s tests -p 'test_p0*.py' -v
python tools/verify_p04b_replay.py --run /home/aashraf/phi-jepa/p04b-assessment-01 --answer-run /home/aashraf/phi-jepa/p04a-answers-01
python tools/collect_p04b_evidence.py --run /home/aashraf/phi-jepa/p04b-assessment-01
```

Compact evidence and source/native hashes: `docs/reviews/artifacts/P04b/`.
Native bank, trajectories, response cache and full per-channel evaluation:
`/home/aashraf/phi-jepa/p04b-assessment-01`. Final extra guards and the complete
deterministic answer formatter were verified offline without repeating live calls
or extending the bounded run. Raw forecasts remain preserved.

Remaining gates: no complete-score calibration while required contract coverage
is absent; no high-score replacement; no qualified independently trained numerical
fallback; no demonstrated correction/harm benefit; contact outputs unsupported;
tiny one-domain checkpoint and no final/OOD study. These are explicit limits, not
failures hidden by zero-filled scores or fixture substitutions.

Next: Stage 6 after the requested comparator/projection/recurrent-state definitions
are resolved. Optional LR/RNN retention is awaiting user selection. No later-stage
training, dependency installation or model download has been launched.
