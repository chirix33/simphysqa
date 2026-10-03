# P12 training-run preparation — 29 September 2026

**Preparation is complete; expanded numerical training has not started.** The
new disabled proposal resolves the completed embedding manifests by explicit
paths and checksums. Preflight reports `data_ready: true`, zero missing contexts,
zero integrity failures, `training_authorized: false` and `can_train: false`.
The original disabled proposal and all historical results remain unchanged.

The checkout remains `main` at `248575fd500947edd325836e636aebe41f9f65d0`, with
uncommitted P12 work preserved. New answer-interface diagnostic files were found
in the checkout and left untouched. No model download, provider call, expanded
optimizer update, test-outcome evaluation, paper edit, push or merge occurred.

## New plan and source identity

Native preparation root: `/home/aashraf/phi-jepa/p12-training-plan-01`.
Proposed training destination: `/home/aashraf/phi-jepa/p12-expanded-study-seed11`.
That study directory still does not exist. Export is directly under
`docs/reviews/artifacts/P12_training_plan/`.

- [New disabled training proposal](artifacts/P12_training_plan/proposed-training-plan.json).
- [Preflight](artifacts/P12_training_plan/training-preflight.json) and [fresh population/pair audit](artifacts/P12_training_plan/population-audit.json).
- [Disabled-launch and historical-preservation verification](artifacts/P12_training_plan/readiness-verification.json).
- [Frozen numerical source](artifacts/P12_training_plan/source.json), [tests](artifacts/P12_training_plan/tests.log), and [artifact checksums](artifacts/P12_training_plan/artifact-index.json).

Proposal SHA-256:
`13cc4b3cbe8578abe22ebe8faa0987b2de2b3309639bf5e7a9988f4e0542add3`.
Numerical implementation identity:
`f22e7646a6f39ef74e84be0d10dd7b3935933721f625e4a897640485d91b9829`.
Preserved original proposal SHA-256:
`e3d9e9cf2afd02835b31d92c9bdf07deebbae5d00133d8c431a0faf5a71d1022`.

The new `p12-complete-context-training-v2` plan binds the selection, both complete
coverage manifests, both enrichment-origin manifests, encoder configuration and
completion audit, frozen confirmation cohort/public inputs, fresh population
audit, all four state layouts, numerical source files and runtime versions.
It obtains the encoder identity from completed preparation, not a P11 report.

Numerical source locking excludes unrelated local-answer implementations and
prompts so independent Llama diagnostics do not alter the numerical training
identity. The original local-model lock is retained as an informational evaluation
proposal reference. No new answer-interface condition is selected or authorized.

## Population, exposure and selection

The preparation streamed the admitted training records and recomputed adjacent
pair counts from their recorded states. Original training/validation and
confirmation memberships remain unchanged, with scenario-group isolation.
No test reference outcomes were opened. Public confirmation contexts were
checked against their completed coverage manifests only.

| Domain | Training scenarios | Training questions | Pairs/pass | Proposed updates | Proposed pair presentations | Validation questions/pass |
|---|---:|---:|---:|---:|---:|---:|
| driving | 740 | 740 | 66,600 | 2,602 | 666,112 | 148 |
| object_pushing_stacking | 1,000 | 2,000 | 130,000 | 5,079 | 1,300,224 | 400 |
| robotic_arm | 981 | 1,962 | 127,530 | 4,982 | 1,275,392 | 388 |
| tethered_load | 1,000 | 2,000 | 130,000 | 5,079 | 1,300,224 | 400 |
| Total | **3,721** | **6,702** | **454,130** | **17,742** | **4,541,952** | **1,336** |

All **8,038 training/validation** contexts and **500 confirmation** contexts pass
coverage, origin and file-integrity checks. There are zero missing or invalid
vectors. Enrichment, vector identities, dimensions, finiteness and normalization
were checked again during preflight; no new embedding calls were needed.

Proposed training remains fresh seed 11, CPU with two PyTorch threads, batches
of 256 equal-weight question-conditioned adjacent pairs, ten full shuffled
passes with carried tails. The final full batches add 652 pair presentations
beyond exactly ten passes. Adam learning rate 0.001, gradient clip 1.0, RK4 with
one substep, accepted train-only scaling and derivative-bias initialization
remain unchanged. E stays frozen; P and the ODE train jointly with target-side
projection gradients and raw augmented-vector MSE. Inference retains complete
augmented-vector feedback. Ten passes do not establish convergence.

Validate all original validation questions after each completed pass: 13,360
scheduled validation rollouts. Select each domain's checkpoint by the existing
mean tolerance-normalized numerical target error, using the fixed failure
penalty and earliest checkpoint on ties. No test result enters selection.
Exact per-domain update milestones are in the proposal. Save optimizer/RNG
resume checkpoints every 100 updates and retain pass checkpoints.

## Bounds, authorization and resume

The proposed numerical execution allowance is **14,400 wall seconds total**,
split into **3,600 seconds per domain**, with **16 GB artifacts total**. The
measured qualification-based training/selection estimate remains 1.6–2.5 hours;
it is not a measured full-population training duration. This plan-preparation
task does not activate those allowances. Enrichment/embedding preparation budgets
are neither renewed nor transferred.

`training_enabled`, global `enabled` and `evaluation_enabled` are all false.
A later authorized copy must bind this exact proposal checksum and may change
only `training_enabled`, `training_authorization` and
`authorized_proposal_sha256`. Global study/evaluation activation stays false,
so training approval cannot launch a direct baseline or open confirmation
outcomes through the existing study tools. Changes to immutable settings require
a new reviewed proposal.

Training now reads the paths in the plan, checks their hashes, and verifies
source/runtime/layout identities before preparing pairs. An exclusive domain
worker lock prevents duplicate execution. The first authorized domain launch
persists its deadline and approved-plan hash; restarts do not renew that deadline.

Resume requires matching optimizer/RNG state, pair population, sampler position,
ordered update history and durable update accounting. A reserved, failed or
uncheckpointed update blocks automatic replay. Interrupted pass validation also
blocks continuation instead of silently skipping a checkpoint-selection sweep.
These cases require explicit reconciliation with preserved artifacts and budget;
the runner does not claim transparent recovery from every crash. A clean matching
checkpoint can resume within its original window. Completed domains return
without new optimizer updates.

## Commands and checks actually run

In WSL, from the repository, using the existing core environment:

```bash
source /home/aashraf/phi-jepa/.venvs/phi-core/bin/activate
PYTHONPATH=src:tests:tools python -m unittest test_p12_training_plan test_p12 test_p03 -v
timeout 1200 python -u tools/p12_train.py plan
python tools/p12_training_plan_verify.py
```

**26 tests passed in 3.680 seconds.** They cover obsolete/disabled plan rejection,
manifest paths and tampering, full coverage, group isolation, approval binding,
persisted deadlines, unresolved updates/validation, and the existing gradient,
full-feedback and checkpoint contracts. Tiny fixture optimizer steps in offline
unit tests are not expanded-study training or empirical performance evidence.

The fresh population audit took **24.212 seconds**. Full context preflight took
**10.671 seconds**. A real CLI launch with the disabled proposal was rejected at
the authorization gate, before creating the study directory. Expanded optimizer
updates and pair presentations remain **zero**. No GPU model or paid API calls
were made by preparation.

Safe repeatable check:

```bash
python tools/p12_train.py preflight --approved-plan /home/aashraf/phi-jepa/p12-training-plan-01/proposed-training-plan.json
```

The option name does not grant approval; this file is still disabled. Future
commands, **only after separate numerical-training authorization**, using a
matching approved copy:

```bash
python tools/p12_train.py train --approved-plan /home/aashraf/phi-jepa/p12-approved-training-plan.json --domain driving
python tools/p12_train.py train --approved-plan /home/aashraf/phi-jepa/p12-approved-training-plan.json --domain robotic_arm
python tools/p12_train.py train --approved-plan /home/aashraf/phi-jepa/p12-approved-training-plan.json --domain object_pushing_stacking
python tools/p12_train.py train --approved-plan /home/aashraf/phi-jepa/p12-approved-training-plan.json --domain tethered_load
```

Run domains sequentially. The approved-copy path above does not yet exist.
Confirmation evaluation requires a separate finalized plan after the answer
diagnostics, plus all selected numerical checkpoints locked. Its proposed frozen
cohort remains 320 scenarios / 500 questions, with original limits of 1,500 local
requests, 18 generation hours, no automatic retries and zero paid calls. Existing
evaluation scripts must not be pointed at this training-only proposal as if it
were evaluation authorization. Numerical training can be approved independently
of those answer-interface decisions.
