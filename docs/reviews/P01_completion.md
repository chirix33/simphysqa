# P01 completion

Status: **complete** for the authorized small data-to-evaluation slice. No P02 work,
neural training, model download, API call, push or merge occurred.

Starting/current branch: `codex/p00-bootstrap`; HEAD
`dbff9573fa3d13adf4edafa42976afc2e5208e90`. P00 was already committed. The only
starting dirty file was the planner's expanded `docs/prompts/P01_data.md`; its SHA-256
remains `4778fd4c5ebc580f6675293a9ea32b65f457f32ad6e04bbaa74f5e62bd70a969`.
P01 changes are uncommitted and layered on that working tree; nothing was stashed/reset.

## Delivered interfaces and scope

Added benchmark-only analytic/event and numerical stopping implementations, configurable
family-partitioned dataset generation, immutable truth/training/scaler contracts and a
numerical prediction-file evaluator. CLI adds `generate-data`, `validate-data`, `evaluate`.
P00's `fixture` still only round-trips input with no prediction. Artifact source hashing
now includes nested modules; the new bundle reader verifies manifests and artifact hashes.
No new dependency, legacy code change, source-asset change or scientific-method change.

See [decisions](../decisions/P01_data.md) for full parameter ranges, tolerances, time/event
semantics, marginal anchors, metrics policy and bounded configuration. Default seed 11:
32 families (16 train, 4 selection, 4 calibration, 4 ID test, 1 low-mu, 1 high-mu,
1 combination, 1 event OOD), two paraphrases and two time queries = 128 records.
Actual outcomes: 86 moving and 42 stopped records.
Train and all ID partitions exclude v0>=15, mu<=0.4. Exact combination marginal values
17.5 m/s and 0.35 occur separately in training. All correlated variants stay in-family.

## Commands actually run

All commands ran from repository root. Existing `.p00-venv` uses Windows Python 3.12.14;
no GPU check was run here. The earlier user-reported WSL GPU pass is separate evidence.

```powershell
& '.\.p00-venv\Scripts\python.exe' -m unittest discover -s tests -v
$p01Dataset = & '.\.p00-venv\Scripts\phi-jepa.exe' generate-data --config configs/p01_fixture.json --output docs/reviews/artifacts/P01/data
& '.\.p00-venv\Scripts\phi-jepa.exe' validate-data --dataset $p01Dataset --output docs/reviews/artifacts/P01/validation
& '.\.p00-venv\Scripts\phi-jepa.exe' evaluate --dataset $p01Dataset --predictions "$p01Dataset/oracle_predictions.json" --output docs/reviews/artifacts/P01/evaluation
& '.\.p00-venv\Scripts\phi-jepa.exe' evaluate --dataset $p01Dataset --predictions "$p01Dataset/corrupted_predictions.json" --output docs/reviews/artifacts/P01/evaluation
& '.\.p00-venv\Scripts\phi-jepa.exe' --help
Get-FileHash docs/prompts/P01_data.md -Algorithm SHA256
```

All executable commands above succeeded. Final test run: **28 passed in 3.043 seconds**,
including all eight unchanged P00 tests. First run had 27 passes and one test failure:
the import-boundary test falsely matched `dataclasses` as forbidden `data`. Matching
module path components fixed the test; no forbidden production import was found.
The corrected test is independent of test execution order.

Final checks also ran `python tools/verify_p00_handoff.py` in `.p00-venv`:
9 preserved source hashes, 4 prompt-string hashes and all links in 33 Markdown
files passed. `git -c core.safecrlf=false diff --check` passed. A read-only Python
check loaded all four persisted P01 bundles through `read_run`, verified their
source hashes against the current implementation, rechecked the user prompt hash,
and confirmed no diff in legacy sources, original assets/references or P00 artifacts.

Tests cover closed-form edge cases, zero speed/friction, stopping before/at/after T,
negative position, events before/at/after stop, zero-friction changes, event continuity,
invalid units/values/grids/budgets, independent numerical refinement, 20 fixed-seed
random event cases unrelated to dataset split selection, family containment, label
exclusion, train-only scaling and constant columns, invalid/missing/duplicate/unknown
predictions, weakly compliant wrong answers, actual versus absent/incompatible trajectories,
content integrity and generation-to-evaluation with sockets/DNS blocked. Repeated CLI
generation in two roots yields byte-identical bundles. Evaluation does not call an oracle.

## Oracle validation evidence

Validated 32 families / 128 records. Validation executed
64 analytic solves and 128 numerical solves,
21692 Euler steps; generation used 64 analytic solves, with paraphrases
sharing labels. Validation compares 0.02 s and 0.01 s maximum steps.
Maximum position error: 0.190770459469 m coarse,
0.0953831052321 m fine. Maximum fine speed error:
2.29150032283e-13 m/s. All per-case position bounds
`g*max_mu*T*0.01 + 1e-8 m`, speed tolerance `1e-8 m/s`, and non-worsening refinement
checks passed. Numerical position error is expected first-order Euler discretization,
not uncertainty in the analytic labels or a Phi-JEPA prediction metric.

## Evaluator evidence (fixtures only)

| Measure | Oracle fixture | Deliberately corrupted fixture |
| --- | --- | --- |
| Expected / valid predictions | 128 / 128 | 128 / 126 |
| Missing / invalid rows | 0 / 0 | 1 / 1 (wrong units) |
| Valid-prediction coverage | 1 | 0.984375 |
| x endpoint RMSE (m), valid-only | 0 | 1.09305350437 |
| v endpoint RMSE (m/s), valid-only | 0 | 1.2996257177 |
| Train-normalized macro MSE, valid-only | 0 | 0.0411638730787 |
| PCVR violations / evaluated checks | 0 / 512 | 2 / 504 |
| Eligible / unsupported checks | 512 / 0 | 512 / 0 |
| PCVR check coverage | 1 | 0.984375 |
| Families with evaluated checks | 32 / 32 | 32 / 32 |
| Family macro PCVR | 0 | 0.0078125 |
| Compatible trajectories | 128 / 128 | 125 / 128 |

The corrupted numerical row violates nonnegative speed and no reverse displacement.
Missing/invalid predictions are explicit failures, not assigned perfect error/PCVR.
Remaining valid trajectories are oracle trajectories and therefore have zero trajectory
error; that does not hide the three unavailable trajectories. All-missing and unsupported
check tests return null unavailable metrics. This is evaluator verification only, not
Phi-JEPA accuracy or OOD performance.

## Durable artifacts

Each run directory name is its manifest SHA-256. Each manifest records source/environment
and hashes of contained artifacts. Source hashes include all new nested benchmark files;
`git_dirty=true` distinguishes the uncommitted implementation from HEAD.

- [Dataset manifest](artifacts/P01/data/f6eb1ae7fde44e3d98f9c56a8301b99c79ff6c0ff7c0c03bebfed7b13a8fdcb4/manifest.json): `f6eb1ae7fde44e3d98f9c56a8301b99c79ff6c0ff7c0c03bebfed7b13a8fdcb4`.
- [Label-free inputs](artifacts/P01/data/f6eb1ae7fde44e3d98f9c56a8301b99c79ff6c0ff7c0c03bebfed7b13a8fdcb4/inputs.json), [separate truth](artifacts/P01/data/f6eb1ae7fde44e3d98f9c56a8301b99c79ff6c0ff7c0c03bebfed7b13a8fdcb4/truths.json),
  [family partitions](artifacts/P01/data/f6eb1ae7fde44e3d98f9c56a8301b99c79ff6c0ff7c0c03bebfed7b13a8fdcb4/partitions.json), [training-only scaler](artifacts/P01/data/f6eb1ae7fde44e3d98f9c56a8301b99c79ff6c0ff7c0c03bebfed7b13a8fdcb4/scaler.json),
  [dataset-source registry](artifacts/P01/data/f6eb1ae7fde44e3d98f9c56a8301b99c79ff6c0ff7c0c03bebfed7b13a8fdcb4/source_registry.json).
- [Oracle/partition validation](artifacts/P01/validation/5bb92fdd6c6ed8f789bdb89de7c0d9b8c41f6dd70632a3a8e4f6e78818b355dc/validation.json) (manifest `5bb92fdd6c6ed8f789bdb89de7c0d9b8c41f6dd70632a3a8e4f6e78818b355dc`).
- [Oracle evaluator report](artifacts/P01/evaluation/d22b3bfa1ddd42a726046926560044ff0cff7ed8362e2f542019d42aef55dbc5/metrics.json) (manifest `d22b3bfa1ddd42a726046926560044ff0cff7ed8362e2f542019d42aef55dbc5`).
- [Corrupted evaluator report](artifacts/P01/evaluation/adca063ab3f9b4448319330a6e4db5d7f6bac5e378463a50033a808a9bae0ade/metrics.json) (manifest `adca063ab3f9b4448319330a6e4db5d7f6bac5e378463a50033a808a9bae0ade`).
- [Oracle fixture predictions](artifacts/P01/data/f6eb1ae7fde44e3d98f9c56a8301b99c79ff6c0ff7c0c03bebfed7b13a8fdcb4/oracle_predictions.json) and [corrupted fixture predictions](artifacts/P01/data/f6eb1ae7fde44e3d98f9c56a8301b99c79ff6c0ff7c0c03bebfed7b13a8fdcb4/corrupted_predictions.json).

Scaler SHA-256: `aaf95cb1106a7eb51f9479ccc3e1af1aea3c95d38467d888d00e8c6aaf1b99f3`. Physical labels and original numerical predictions
remain separate. Sources, original notebook, P00 evidence and legacy results are preserved.
The local analytic registry does not invent a license; external candidates remain not adopted.

## Limits and next step

No unresolved P01 blocker. This is a tiny unsealed wiring dataset, not a study or evidence
of model quality. Physical checks are necessary bounds, not an exact-answer verifier;
endpoint truth error is reported separately. Arbitrary-language semantic deduplication,
worked-solution annotation generation, NCS, detection/diagnosis and later experimental
metrics remain outside this slice. Counts/ranges are configurable within a small fixture
cap, not permission to run a large study. Zero horizon is explicitly rejected.
No target-latent or judge decision was invented; Q1–Q4 and later GPU/model gates remain.
Next: planner/user review of P01; wait for authorization before P02.
