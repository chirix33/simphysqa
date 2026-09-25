# Stage 3/P03 completion — 24 September 2026

Status: **complete for implementation and bounded correctness validation**.
This is not full training or a validated predictive model. Branch
`full-phi-jepa-from-dataset`, base/current HEAD
`7f2553ca6591301de588bd3362e72838354169a0`; phase changes uncommitted.
Stage 2 was completed before Stage 3 began. Stage 4 had not begun at this report.

## Behavior

- `models/augmented_ode.py`, `solvers/rk4.py`, `training/pairs.py`: recorded adjacent
  pair supervision, full 2d MSE, same trainable p in input/target, both gradient
  paths, joint optimizer, explicit physical time, finite-state/failure checks,
  NFE accounting. User-selected equal question-pair weights are now supported by
  the P02a readers; their historical inverse-weight behavior remains available.
- `inference/rollout.py`: initializes from final public observation, then feeds
  back the entire predicted vector. No reference/evaluator/simulator handle,
  p reset, rounding, clipping of coordinates or LLM correction.
- `training/checkpoint.py`: atomic content-addressed checkpoints, strict layout/
  context/role/integrity checks, training RNG/optimizer/sampler/provenance resume,
  and separate minimal deployment bundles.
- `tools/run_p03_correctness.py`: fixed 20-pair/200-update/900-second maximum,
  separate autonomous validation before evaluator-only one-step diagnostics.
  `tools/inspect_p03_checkpoint.py` performs forward-only replay/refinement/
  question-sensitivity checks. No full benchmark launcher was run.

## Tests and actual fit

The initial seven P03 tests passed (4.556 s), including separate target/input P
gradient paths through a real RK4 solve, joint P/ODE updates, analytic exponential
and time-dependent ODEs, solver refinement, full predicted-p feedback, reference
independence, RNG/optimizer checkpoint continuation and fresh-process parity.
The final regression suite passed 72 tests in 13.913 seconds, with zero skips.
It additionally tests rejected nonfinite optimizer updates and records all failed
update attempts; see `artifacts/P03/tests-wsl.log`.

Actual CPU correctness run, Python 3.12.3 in isolated WSL core, Torch 2.7.1+cu128,
two CPU threads, native artifact storage:

| Quantity | Measured result |
| --- | --- |
| Training questions/scenarios | 1 / 1 tethered-load training selection |
| Training examples/unique transitions | 20 / 20 |
| Updates / training wall time | 200 / 2.843465 s |
| Initial / final pre-update full MSE | 0.3571448922 / 0.3207199574 |
| Training solves / NFE / sample-NFE | 200 / 800 / 16000 |
| Failed solves/updates | 0 / 0 |
| P mean norm, first/final logged update | 0.498230 / 1.615984 |
| P gradient norm range | 3.15805e-9 to 3.08100e-6 |
| Recorded-input validation one-step numeric MSE | 0.6410943270 |
| Identity recorded-input one-step numeric MSE | 0.7142886519 |
| Autonomous validation numeric MSE over horizon | 354.8456116 |
| Autonomous terminal numeric MSE | 1025.7506104 |
| Fresh-process real deployment replay | Exact trajectory match |
| RK4 refinement, 1 versus 2 substeps | Max absolute coordinate delta 4.76837e-6 |
| Question change: max numeric forecast delta | 4.36557e-11 |
| Question change: terminal numeric L2 delta | 1.20438e-10 |

Numeric MSE here includes every selected numeric state/fixed-conditioning
coordinate, including step index/time. It is a raw mixed-coordinate diagnostic,
not physical-unit accuracy or complete-answer success. Validation is one distinct
question/scenario, not a representative study. High autonomous error and near-zero
question influence are preserved. No criterion required beating a baseline.

Counts after fit: autonomous validation 40 solves/160 NFE; batched recorded-input
diagnostic 1 solve/4 NFE over 40 pairs (160 sample-NFE). Fresh-process repeat,
alternative-question and refinement diagnostics add 120 solves/640 NFE. Combined
real-run total: **361 solves, 1604 NFE, 16960 sample-NFE**. Fixture test work is
separate. Four verified E cache hits across fit/inspection, zero new E calls,
zero provider calls, no additional API spend.

## Reproduction and artifacts

Commands actually run from repository root through WSL, using
`/home/aashraf/phi-jepa/.venvs/phi-core/bin/python`:

```text
PYTHONPATH=src python -m unittest discover -s tests -p test_p03.py -v
python tools/run_p03_correctness.py --profile /home/aashraf/phi-jepa/p02b-profile --cache-dir /home/aashraf/phi-jepa/model-cache --output /home/aashraf/phi-jepa/p03-correctness-01
python tools/inspect_p03_checkpoint.py --run /home/aashraf/phi-jepa/p03-correctness-01 --profile /home/aashraf/phi-jepa/p02b-profile --cache-dir /home/aashraf/phi-jepa/model-cache
PYTHONPATH=src python -m unittest discover -s tests -p 'test_p0*.py' -v
```

Raw training history, checkpoints, immutable autonomous trajectory, and validation
metrics are under `/home/aashraf/phi-jepa/p03-correctness-01`. Compact copies and
exact hashes are in `docs/reviews/artifacts/P03/`. Model weights/large trajectories
remain outside Git. Each run records source/config/context/release identities;
final failed-update-accounting improvements were separately regression-tested
without repeating or extending the capped correctness fit.

No algorithm deviation, new scientific loss, input normalization, event head,
schema repair, simulator generation or full training was introduced. The prior
inverse-multiplicity proposal is explicitly superseded by the user's equal-pair
decision. The only current model is a tiny correctness checkpoint.

Next: Stage 4 named predictions and the user-authorized deterministic public-rule
readout, per-target support qualification, unsupported contact-dependent outcomes,
and the selected frozen `gpt-5.6-sol` answer model. This changes output readout
only, not the training procedure. No Stage 5+ work is started here.
