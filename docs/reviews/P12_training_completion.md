# P12 numerical training completion — 29 September 2026

**All four authorized domain fits completed.** Total execution window: 3270.541 seconds (54.51 minutes). This is numerical training and validation-only checkpoint selection; no confirmation evaluation or local-baseline generation ran. Paid calls were zero. Ten passes are a fixed exposure, not evidence of convergence.

Checkout: `main` at `248575fd500947edd325836e636aebe41f9f65d0`, with existing uncommitted work preserved. No paper edit, push or merge.

## Completed exposure and resources

| Domain | Passes | Updates | Pair presentations | Validation sweeps | Domain wall (s) | Peak RSS (GiB) |
|---|---:|---:|---:|---:|---:|---:|
| driving | 10 | 2,602 | 666,112 | 10 | 467.163 | 1.241 |
| object_pushing_stacking | 10 | 5,079 | 1,300,224 | 10 | 709.364 | 1.774 |
| robotic_arm | 10 | 4,982 | 1,275,392 | 10 | 1115.127 | 2.233 |
| tethered_load | 10 | 5,079 | 1,300,224 | 10 | 923.644 | 1.926 |

Total successful updates: **17,742**; actual pair presentations: **4,541,952**. The fixed training population is 3,721 scenarios, 6,702 questions and 454,130 pairs/pass. Final full batches add 112 driving, 92 arm, 224 object and 224 tether pair presentations beyond exactly ten passes.

Execution used Intel(R) Core(TM) Ultra 9 285K under WSL, the approved CPU profile with two PyTorch threads, Python 3.12.3 and torch 2.7.1+cu128. Optimizer-step time totals 1817.684 s; validation time totals 968.083 s. Child user+system CPU time totals 3978.174 s. Remaining wall time includes context/pair preparation, checkpoint I/O and launch/preflight bookkeeping. Domain wall times include each child preflight; aggregate time also includes initial preflight and sequential dispatch overhead.

## Validation-selected checkpoints

Selection used all original validation questions after each pass, the unchanged mean tolerance-normalized numerical error and fixed failure penalty, with the earliest checkpoint on ties. No test outcome entered selection. These are selection diagnostics, not held-out benchmark estimates.

| Domain | Selected pass | Update | Validation score | Complete validation answers |
|---|---:|---:|---:|---:|
| driving | 3 | 781 | 36.711235 | 0/148 |
| object_pushing_stacking | 1 | 508 | 0.927504484 | 0/400 |
| robotic_arm | 10 | 4,982 | 575.71135 | 0/388 |
| tethered_load | 1 | 508 | 2.44597071 | 19/400 |

Native selected model files (SHA-256 is the filename stem):

- driving: `/home/aashraf/phi-jepa/p12-expanded-study-seed11/driving/checkpoints/781/73322a05bb040700904c42a9eb3b123a0cd75980e64df0a9d854a65a3d5de0bf.pt`.
- object_pushing_stacking: `/home/aashraf/phi-jepa/p12-expanded-study-seed11/object_pushing_stacking/checkpoints/508/57c8419f55b615484950cb9173560815df78e101e5080a9df43fa81c4b3e22ce.pt`.
- robotic_arm: `/home/aashraf/phi-jepa/p12-expanded-study-seed11/robotic_arm/checkpoints/4982/75fc9ecb45e428d2f9f0f283110333090ba4ef406db110c5fd1957a9a4e31497.pt`.
- tethered_load: `/home/aashraf/phi-jepa/p12-expanded-study-seed11/tethered_load/checkpoints/508/54891597a3a5a57585a4f986f4ef01841c15e13d9d0f0fd2021ec45fc74a7eb6.pt`.

## Training and validation curves

[Vector curve figure](artifacts/P12_training_run/training-validation-curves.svg) · [Full audited values](artifacts/P12_training_run/audit.json). Raw per-update histories and per-question validation records are retained under the export’s `domains/` directory. Training means below cover the full batches between successive pass milestones, including carried tails. Training loss is the raw augmented-vector MSE; validation scores use physical-target tolerances and are not the same scale.

### driving

| Pass | End update | Mean training MSE | Validation score | Rollout exceptions |
|---|---:|---:|---:|---:|
| 1 | 261 | 0.000221188343 | 94.8448458 | 0 |
| 2 | 521 | 0.000184272366 | 40.7276046 | 0 |
| 3 | 781 | 0.000202116824 | 36.711235 | 0 |
| 4 | 1,041 | 0.000201560907 | 73.83446 | 0 |
| 5 | 1,301 | 0.000167665703 | 40.9936997 | 0 |
| 6 | 1,561 | 0.000132549311 | 60.7339322 | 0 |
| 7 | 1,822 | 0.000208296526 | 75.1331539 | 0 |
| 8 | 2,082 | 0.000166446632 | 67.0519242 | 0 |
| 9 | 2,342 | 0.000147593443 | 47.7011349 | 0 |
| 10 | 2,602 | 0.000161838425 | 39.1472079 | 0 |

### object_pushing_stacking

| Pass | End update | Mean training MSE | Validation score | Rollout exceptions |
|---|---:|---:|---:|---:|
| 1 | 508 | 1.1109808e-07 | 0.927504484 | 0 |
| 2 | 1,016 | 1.54336845e-07 | 5.84143373 | 0 |
| 3 | 1,524 | 1.11705966e-07 | 2.02493545 | 0 |
| 4 | 2,032 | 1.06812963e-07 | 1.42664617 | 0 |
| 5 | 2,540 | 1.16606866e-07 | 1.40614929 | 0 |
| 6 | 3,047 | 1.08152657e-07 | 24.5765201 | 0 |
| 7 | 3,555 | 1.04704074e-07 | 2.11839381 | 0 |
| 8 | 4,063 | 1.02710772e-07 | 1.25803359 | 0 |
| 9 | 4,571 | 1.03327284e-07 | 1.39023295 | 0 |
| 10 | 5,079 | 1.01015029e-07 | 1.45291141 | 0 |

### robotic_arm

| Pass | End update | Mean training MSE | Validation score | Rollout exceptions |
|---|---:|---:|---:|---:|
| 1 | 499 | 0.00574332982 | 939.894003 | 0 |
| 2 | 997 | 0.00361963211 | 690.993121 | 0 |
| 3 | 1,495 | 0.0028177785 | 606.228234 | 0 |
| 4 | 1,993 | 0.00231243024 | 647.307715 | 0 |
| 5 | 2,491 | 0.00213161498 | 1647.59383 | 0 |
| 6 | 2,989 | 0.00199157106 | 863.520325 | 0 |
| 7 | 3,488 | 0.00181755684 | 2511.8504 | 0 |
| 8 | 3,986 | 0.00143476569 | 2166.72807 | 0 |
| 9 | 4,484 | 0.0023020596 | 1639.59993 | 0 |
| 10 | 4,982 | 0.00150399103 | 575.71135 | 0 |

### tethered_load

| Pass | End update | Mean training MSE | Validation score | Rollout exceptions |
|---|---:|---:|---:|---:|
| 1 | 508 | 2.14663016e-07 | 2.44597071 | 0 |
| 2 | 1,016 | 4.4898846e-08 | 17.1952585 | 0 |
| 3 | 1,524 | 1.84790629e-08 | 31.2599436 | 0 |
| 4 | 2,032 | 1.43926054e-08 | 13.9136915 | 0 |
| 5 | 2,540 | 1.24157886e-08 | 12.9475428 | 0 |
| 6 | 3,047 | 1.09386169e-08 | 14.9269771 | 0 |
| 7 | 3,555 | 1.02236128e-08 | 19.2161725 | 0 |
| 8 | 4,063 | 9.39815982e-09 | 25.7819459 | 0 |
| 9 | 4,571 | 8.68768623e-09 | 33.8986049 | 0 |
| 10 | 5,079 | 8.20328945e-09 | 37.9048143 | 0 |

## Failure accounting and limits

- driving: 0 validation rollout exceptions; 0 questions with score ≥ 1e12; target/rollout failure reasons across all selection sweeps: `{}`.
- object_pushing_stacking: 0 validation rollout exceptions; 0 questions with score ≥ 1e12; target/rollout failure reasons across all selection sweeps: `{"missing_contact_force_and_history": 8000}`.
- robotic_arm: 0 validation rollout exceptions; 0 questions with score ≥ 1e12; target/rollout failure reasons across all selection sweeps: `{}`.
- tethered_load: 0 validation rollout exceptions; 0 questions with score ≥ 1e12; target/rollout failure reasons across all selection sweeps: `{"initial_crossing_state_not_qualified": 240}`.

The supervisor persisted the four-hour aggregate deadline and one-hour dispatch deadlines; the unchanged trainer enforced its own one-hour domain guards and checkpoint artifact reserve. No budget was extended. Models ran sequentially. Native study/checkpoint artifacts occupy 686,361,243 bytes. The final integrity manifest records hashes for every retained checkpoint blob.

## Identity, verification and commands

- User-authorized proposal SHA-256: `13cc4b3cbe8578abe22ebe8faa0987b2de2b3309639bf5e7a9988f4e0542add3`.
- Authorized copy SHA-256: `985ee2c11bc0212275cac95620044ea7e4742fc90581edbacf31deace1aaec5c`.
- Frozen numerical implementation: `f22e7646a6f39ef74e84be0d10dd7b3935933721f625e4a897640485d91b9829`.
- [Approved copy](artifacts/P12_training_run/execution/approved-plan.json), [execution window/source](artifacts/P12_training_run/execution/execution-window.json), [initial preflight](artifacts/P12_training_run/execution/preflights/initial/training-preflight.json), [export checksums](artifacts/P12_training_run/artifact-index.json).

Fresh preflight verified all 8,038 train/validation contexts and 500 confirmation public contexts with zero missing/integrity failures. Confirmation outcomes remained unopened. Only the three authorized activation fields changed; original proposals and preparation exports were preserved. The final audit checks source/runtime/input hashes, exact update/exposure totals, validation IDs/aggregates, earliest minimum selection and all checkpoint content hashes. All 255 checkpoint blobs passed; all four selected deployment models and final optimizer/RNG bundles reloaded successfully, with zero failed optimizer updates and no added updates or rollouts. A second completed-wrapper invocation returned "Already complete; no optimizer updates."

Commands actually run in the existing WSL core environment:

```bash
PYTHONPATH=src:tests:tools python -m unittest test_p12_training_plan test_p12 test_p03 -q
PYTHONPATH=src:tests:tools python -m unittest test_p12_training_execution -v
python -u tools/p12_training_execution.py run
python tools/p12_training_report.py --status
python tools/p12_training_report.py
```

The first suite passed 26 tests in 3.243 s; the outer-envelope suite passed two tests in 0.015 s. Its printed timeout/artifact errors were deliberately exercised fixture guards, not failures of the live run. Curves were rendered offline with the bundled Windows Python and ReportLab LinePlot; the numerical runtime was not changed.

## Preserved artifacts and next boundary

- Native checkpoints, histories and validation records: `/home/aashraf/phi-jepa/p12-expanded-study-seed11`.
- Execution controls, child logs and resource records: `/home/aashraf/phi-jepa/p12-training-execution-01`.
- Repository evidence export: `docs/reviews/artifacts/P12_training_run/`.
- [Execution decisions](../decisions/P12_training_execution.md) and [run commands](../P12_pipeline.md).

Confirmation evaluation and baseline generation remain disabled. The next evaluation plan must qualify/freeze Qwen thinking-off/on, Llama direct and Llama prompted CoT, preserve reasoning/final separation, and bind the selected numerical checkpoints under a separate budget. The older three-condition evaluation allowance is not silently expanded. Phi-JEPA retains its disclosed historical OpenAI enrichment dependency; this numerical run made zero paid calls and generated no prose answers.

## Nonblocking resume limitation found during artifact audit

The frozen trainer writes a blank line after each canonical update record. Its strict `json_lines` reader rejects that blank line when called by `check_resume_boundary` for an incomplete-domain resume. A read-only two-record probe reproduces `JSONDecodeError`; the raw logs have not been rewritten. The report explicitly skips blank separator lines and validates all actual update records. This did not affect uninterrupted training, checkpoint integrity or completed-domain no-op behavior. No resume was needed.

The frozen source was preserved as authorized. Any future incomplete-run recovery must reconcile this parser issue and the original remaining budget explicitly; it must not silently replay updates, alter the approved source, or renew an expired window.
