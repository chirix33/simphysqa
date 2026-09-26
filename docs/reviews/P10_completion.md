# P10 integrated implementation and learning qualification

**Bounded qualification complete; research performance remains unresolved.**
The executable pipeline now runs independent learning, deployment without
reference access, separate evaluation, assessment, answer generation and export.
This is empirical qualification on tethered-load, not a completed four-domain study.

Branch: `full-phi-jepa-from-dataset`. Base commit:
`5a375bdc7193d77b404e5e7459b5ffce7fbb6933`. P10 changes are local, uncommitted and
not pushed. Per-attempt source hashes identify execution versions; the exported
`sources/final-source.zip` contains the final executable implementation. Earlier
source snapshots exist where recorded, with hashes retained for all stages;
the final source is not retroactively attributed to earlier runs. P07/P08/P09
reports, checkpoints and provenance were not replaced.

## Entry points and evidence

- [Commands, stage boundaries, resume policy and clarification](../P10_pipeline.md).
- [Integrated benchmark and capability matrix](P10_benchmark_report.md).
- [Measured larger-study proposal and commands](P10_next_full_study.md).
- [Export manifest](artifacts/P10/manifest.json), [resource ledger](artifacts/P10/budget.json),
  [test output](artifacts/P10/tests.log), [source identity](artifacts/P10/sources/final-source.json).
- [Numerical learning curves](artifacts/P10/report/numerical_learning.png),
  [custom loss curves](artifacts/P10/report/custom_learning.png),
  [physical error curves](artifacts/P10/report/validation_physical_curves.png).
- [Per-time/scenario/quantity physical errors](artifacts/P10/evaluation/physical_by_time.json),
  [physical summary CSV](artifacts/P10/report/physical_errors.csv),
  [strict generation diagnostics](artifacts/P10/report/generation_diagnostics.json),
  [answer results](artifacts/P10/evaluation/answers.json).
- Coordinate ranges, units and raw-MSE contributions are under
  `artifacts/P10/evaluation/numerical/METHOD/SPLIT/SAMPLE.json`, separately for
  one-step and autonomous predictions. Bounded gradient/saturation/sensitivity
  evidence is under `artifacts/P10/diagnostics/`.

Native weights and optimizer states remain at
`/home/aashraf/phi-jepa/p10-qualification-01`; selected checkpoint hashes/pointers
are exported. Private references and credentials are excluded from export.

## Implemented changes

| Files | Concrete behavior |
| --- | --- |
| `src/phi_jepa/models/conditioning.py`, `models/augmented_ode.py`, `training/checkpoint.py` | Frozen train-input affine n conditioning inside the field, reversible constant-coordinate policy, checkpoint restoration; raw 140/280-dimensional state/loss/derivatives/feedback preserved. |
| `src/phi_jepa/baselines/conventional.py`, `baselines/checkpoint.py`, `training/sampling.py` | Independent compatible numerical methods; optional tested equal-pair mixed-horizon sampler for the future study. |
| `src/phi_jepa/baselines/custom_io.py`, `baselines/custom_t5.py` | Explicit teacher/student/Coconut output instructions and exact target inventory, used consistently in training and generation; separate teacher instruction input with shared CODI backbone; strict parsing/objectives/latent paths unchanged. |
| `src/phi_jepa/capabilities.py` | All 20 public answer bindings across four domains inventoried; per-target failure/unsupported status and explicit contact gaps. |
| `tools/run_pipeline.py`, `p10_worker.py`, `p10_common.py`, `src/phi_jepa/pilot_budget.py` | Stage supervision, immutable configs, provenance/cache identities, caps, resource ledgers, checkpoint-aware resume and inference file-access guard. |
| `tools/p10_data.py`, `p10_numerical.py`, `p10_continuation.py`, `p10_custom.py`, `p10_inference.py` | Frozen scenario selection/caches, independent learning and selection, preserved exposure continuation, standalone selected-checkpoint deployment. |
| `tools/p10_benchmark.py`, `p10_diagnostics.py`, `p10_cohort.py`, `p10_aggregate.py` | Separate truth-accessing evaluation, named errors/controls, fixed assessment, guarded calibration/sealed cohorts and fail-closed matched cross-run aggregation. |
| `tools/p10_clarification.py` | Separately enabled P09 human-reviewed interface; absent from autonomous benchmark; no live clarification experiment performed. |
| `tools/p10_report.py`, `p10_setup.py`, `p10_study.py`, `configs/report-p10.lock.txt` | Rendered evidence/export, isolated plotting environment, concrete guarded larger-study configurations. |
| `tests/test_p10.py`, qualification configs and P10 docs | Behavioral verification, frozen scope/budget and reproducible commands. |

The user-authorized affine/coverage remedies are separately compared in a seeded
2×2 experiment at 4,000 updates. Because affine conditioning alone did not resolve
saturation, a distinct documented initialization factor uses mean *training*
adjacent derivatives to initialize the existing numerical output bias. The bias
remains trainable; no head, rescaling, fixed derivative rule or objective change
is introduced. Both factorials and their failures remain. The successful small
fitting check precedes the five independent 20,000-update continuations under the
same aggregate budget. Original 4,000-update evidence is preserved.

## Measured outcomes and limits

The exact 32 training and eight validation scenarios are frozen in the exported
selection. They are disjoint; calibration and sealed outcome partitions are not
used for checkpoint selection. One question per scenario is used here.

- **Training-only fit:** two questions, 80 adjacent pairs, 4,000 updates: all six
  numerical targets and both complete answers meet the unchanged tolerances.
  This is fitting evidence, not held-out performance.
- **Primary validation:** continued full-coverage model selects update 20,000.
  Mean endpoint error/tolerance decreases from 9.409 at the original selected
  checkpoint to 2.220. Load-position full-horizon RMSE is 0.01463 m versus
  0.11016 m for hold-last. Load angle/velocity also improve; support velocity
  does not (0.02959 versus 0.01082 m/s). Primary answers remain only **1/8**
  complete and **11/24** correct numerical targets.
- **Controls/comparators:** full coverage is not better than early-only at the
  fixed 4,000-update allowance; exposure per distinct pair differs. The constant-
  context ODE, no-enrichment and numerical-only conditions are competitive.
  RNN selection retains update 4,000 after 20,000 updates. These observations
  establish neither primary superiority nor text/enrichment usefulness.
- **Custom generation:** independent broader fits stop at 441 Coconut and 444
  CODI updates within component allowances. Selection chooses 441 and 300.
  Selected Coconut and CODI student outputs are strictly valid with EOS on **8/8**
  validation questions, but only **1/8** and **2/8** complete answers are correct.
  The separate 40-update fitting runs still fail strict generation. CODI's later
  update-444 validation generations have malformed JSON despite EOS; teacher
  fallback attempts there recover neither example. Those failures are retained.
  Instructions and exposure both changed from P08; causal attribution to the
  instruction change alone is not established.
- **Frozen answer layer:** all 48 forecast-based answers preserve their numerical
  readout scores. Public-only answers achieve **24/24** common numerical targets;
  their **0/8** whole-answer score reflects eight unsupported Boolean components.
  It would be misleading to use that whole-answer difference to claim primary QA
  superiority. Seven public-only responses reuse exact caches; one is newly called.
- **Coverage:** all 8,038 public train/validation inputs pass the four-domain
  layout preflight. This does not demonstrate four-domain learning. One training
  question's boundary event is unqualified and remains unsupported for every
  numerical method (127/128 supported typed targets); all validation Boolean
  targets in this selection are supported. Stable-stack/support-lost remain
  unsupported capabilities of the numerical readout.
- **Assessment/clarification:** the checkpoint-matched training prediction bank
  and fixed assessment execute. Required typed public contract declarations are
  absent, so assessment remains partial and uncalibrated. Clarification is a
  separate human-reviewed capability with software evidence, not an OOD alarm
  or a measured answer-quality improvement.

## Verification, recovery and accounting

Executed the documented `all` workflow, then resumed only failed/reporting stages.
Final verification: `tools/run_pipeline.py verify --refresh` invokes
`python -m unittest test_p10 test_p03 test_p04a test_p04b test_p05b test_p06
test_p08_budget test_clarification -v`: **103 tests passed**.
The tests cover raw-coordinate/gradient invariants, conditioning/checkpoints,
teacher/student input paths, leakage guards, failures/denominators, equal-pair
sampling, safe continuation recovery and cross-run aggregation. Fixtures are
software evidence only. `git diff --check` passes. All three exported figures
were visually inspected.

Two execution defects were fixed without rerunning completed learning/calls:
semantic quantity paths contain triples, not only key/value pairs, so diagnostic
column naming was corrected and tested. Its interrupted 5,000-update candidate
was evaluated from saved weights before selection; no optimizer updates were
replayed. Report rendering initially lacked Matplotlib; a pinned reporting-only
environment fixed it without modifying model environments. Original failed
attempts remain in `attempts/` and `logs/`.

The recovered primary run's historical per-fit elapsed-time counter did not carry
the failed segment forward. Its update-indexed learning data and optimizer state
are intact, and the aggregate ledger includes that segment. Subsequent resume
code carries the recorded elapsed time forward; historical timestamps are not
rewritten. Use stage/attempt accounting, rather than summing fit-table seconds,
for total execution cost.

At the first completed export: **36.57/60 CPU minutes, 161.36/180 GPU minutes,
11.753/20 GB**, **49/120 new provider attempts**, **727,013/2,000,000 input tokens**,
**21,655/100,000 output tokens**, and **USD 4.068165/15** conservatively charged.
All 49 calls report usage. The count is 48 forecast calls plus one public-only
cache miss, not 48 total. Reporting/verification refresh overhead is subsequently
charged in the authoritative exported ledger; no new training or paid calls
follow this completion record. CPU/GPU execution uses whole worker wall time;
provider waiting time is separate and its process CPU is charged. The initial
external package-cache bytes are included. No aggregate cap was reached.

## Remaining blockers and decisions

| Classification | Exact gap | Recommended next action / consequence |
| --- | --- | --- |
| Missing evidence | Low complete-answer accuracy; late CODI regressions; weak RNN autonomous forecasts; no demonstrated advantage over the strong public-only numerical control | Preserve these results. The proposed fixed-objective study tests broader exposure/seeds; additional updates are not guaranteed to help. |
| Missing evidence | Other-domain learning, sealed ID/OOD performance, mixed-horizon runtime and live human clarification effectiveness | Execute only a separately approved portion of the prepared study; software tests/preflight are not substitutes. |
| Missing implementation **and scientific decision** | Qualified future contact/support mechanism for stable-stack/support-lost | Retain unsupported. Approve sufficient evidence/mechanism explicitly before introducing a state/head change. |
| Missing evidence **and scientific decision** | Provenance and representation of required immutable typed public assessment contracts | Supply/review legitimate contracts; do not substitute answer thresholds. Until then, partial assessment and no calibration/OOD alarm. |
| Execution approval | Full-study resource allocation exceeds this qualification budget | Prepared 12 guarded profiles, with measured naive custom-training estimate 219.5 GPU hours and conservative aggregate caps of 900 GPU hours, 52 CPU hours, 150 GB and USD 3,900. Review the measured limitations before authorizing a staged prefix or full execution. Nothing has been launched. |

No unsettled decision blocks the implemented autonomous bounded workflow.
The remaining contact/assessment choices are genuine scientific extensions;
the approved architecture, loss, feedback and clarification policies are not
reopened. The next study's exact provider/token/workload caps and executable
aggregation command are in the linked proposal.
