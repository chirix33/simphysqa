# P08 revised learning pilot — completed within the approved bounds

25 September 2026. The authorized execution and evidence package are complete.
**Learning quality remains unresolved:** the primary forecast-based answer
condition achieved **0/8 complete answers and 1/24 correct numerical targets** on
the frozen validation questions. Lower training losses did not establish reliable
autonomous forecasting or custom generation. No extra training, parser repair,
tolerance change or budget extension was used to improve these results.

## Evidence and reproducibility

- [Execution method, information flow and limits](P08_method_and_scope.md).
- [Frozen 32-training/eight-validation selection](artifacts/P08/selection.json),
  SHA256 `3d621fafc275c20ae96a020f0eaef34ad4fec1753a8db9318bdbd0ff5c5170d6`.
- [Coordinate groups, every coordinate's ranges/contributions, named physical and endpoint errors](artifacts/P08/evaluation/coordinate_and_physical_errors.md).
- [Generation diagnostics and all failure denominators](artifacts/P08/evaluation/generation_diagnostics.md).
- [Custom learning curves](artifacts/P08/evaluation/figures/custom-learning-curves.png),
  [numerical learning curves](artifacts/P08/evaluation/figures/numerical-learning-curves.png),
  [training-only generation checks](artifacts/P08/evaluation/figures/diagnostic-generation.png),
  [primary versus hold-last](artifacts/P08/evaluation/figures/primary-hold-last-validation.png).
  Each figure also has a same-name SVG. The
  [curve CSV](artifacts/P08/evaluation/figures/learning-curves.csv) contains 6,672
  component observations; [JSON](artifacts/P08/evaluation/learning-curves.json)
  retains complete histories and milestone losses.
- [Integrity and split checks](artifacts/P08/evaluation/artifact-verification.json),
  [resource ledger](artifacts/P08/evaluation/resource-accounting.json),
  [review manifest](artifacts/P08/manifest.json) and
  [native forecast identities](artifacts/P08/native-forecast-identities.json).

The implementation base is
`ba5d31d9251b58bf17c19a2f4dd9050d3109d4b6` on
`full-phi-jepa-from-dataset`, including the committed audit fixes. At inspection,
the local `origin/full-phi-jepa-from-dataset` reference identified the same commit;
no remote fetch/push was performed. **New P08 code, reports and review artifacts
are local working-tree changes, not a newly committed/pushed implementation.**
Per-stage source/configuration hashes record the code actually used, including
orchestration/accounting revisions and reporting additions during execution.
The final [source inventory](artifacts/P08/source/final_export.json) also hashes
the verification tests. Model equations, objectives and scientific configurations
were not changed during the run.

Full new checkpoints and trajectories remain separately under
`/home/aashraf/phi-jepa/p08-learning-01`. All **73 original P07 source-artifact
hashes remain unchanged**; all **16 latest new checkpoint hashes** were verified.
Intermediate checkpoints are preserved. Historical proposals, audit reports and
their original provenance are not rewritten as if they described this run.

## Executed training and checks

The 640 numerical pairs come from 32 different training scenarios. Every pair has
unit loss weight; validation excludes each of those entire scenarios. Numerical
training spans 0.20–0.60 s; validation forecasts span 0.20–1.00 s. The fixed seed
is 11. The final partial shuffle cycle has explicitly recorded exposure counts.

| Numerical method | Executed allowance | State width | Registered parameter count | Fit-operation seconds |
| --- | --- | --- | --- | --- |
| Primary Phi-JEPA | 1,000 updates | 280 | 232,228 | 15.694 |
| Constant-context text ODE | 1,000 updates | 140 | 214,168 | 14.881 |
| Fixed-projection LR | One least-squares fit | 140 | 143,500 fixed projection parameters; 39,340 fitted coefficients stored separately | 0.689 |
| Constant-context text RNN | 1,000 updates | 140 | 214,040 | 18.025 |
| no_enrichment | 1,000 independent updates | 280 | 232,228 | 16.106 |
| no_text_conditioning | 1,000 independent updates | 140 | 52,748 | 13.616 |

These times are the recorded fit operations; the resource ledger additionally
charges worker startup and other stage overhead. LR used NumPy SVD least squares,
`rcond=1e-12`, design shape 640×281 and numerical rank **40**. Its seeded projection
was fixed, not borrowed or learned. No exact capacity matching is claimed.

Primary still has frozen Qwen, trainable P with width 140, a 280-wide ODE, identical
current p in input and target with both gradient paths, adjacent-pair full-vector
MSE, RK4 on external physical time, and complete predicted-vector feedback.
No_enrichment removes generated enrichment from its model-facing context;
no_text_conditioning removes E/P/p while retaining all numerical conditioning.
Their independent checkpoint/initialization identities are preserved. PIN-ODE and
an undefined no-schema variant remain excluded.

| Custom run | Updates | First → last pre-update training loss | Peak allocated / reserved GPU GB |
| --- | --- | --- | --- |
| Coconut diagnostic, one training question | 20 | 8.86312 → 1.33360 | 2.422 / 2.827 |
| Coconut broader, fresh initialization | 180 | 9.22629 → 0.292180 | 2.431 / 2.856 |
| CODI diagnostic, one training question | 20 | 12.25912 → 1.34811 | 2.952 / 3.588 |
| CODI broader, fresh initialization | 180 | 12.26812 → 0.627017 | 2.968 / 3.622 |

Different loss components/objectives are plotted separately, not treated as
comparable accuracy scores. Eval-mode teacher-forced checks are on the training
diagnostic question. Both broader runs started in separate processes from their
original pinned initialization; neither loaded a diagnostic checkpoint. Initial
tensor hashes match their respective seed-11 starting states. Broader exposure
counts are five or six updates per training question, not 180 per question.

All 40 public inputs passed length preflight: **10,075–10,143 T5 tokens** against
the configured 32,768 limit. Complete training targets used **521–527 student
tokens** and **552–558 teacher/Coconut tokens**, including EOS, against 2,048.
Round trips were exact and truncations were zero. The prior EOS-position,
shifted-label/padding, gradient and checkpoint-restoration audit remains applicable;
the unchanged code was checked again in the offline suite.

CODI shares one T5 backbone between teacher and student. Its teacher projection
stayed fixed in both runs; student projection gradients were nonzero on all
20/180 updates. Each run changed 190 backbone tensors, 17 latent-path tensors and
four student-projection tensors. Coconut changed 190 backbone and 23 latent-path
tensors. Detaching the teacher alignment target does not freeze the shared
backbone against teacher CE or other losses. These observations support functioning
update paths, not successful learning or transfer of pre-answer reasoning.

## Generation quality, with failures retained

All diagnostic milestones 0/1/2/5/10/20 were reached. Across the **18 unique
training-only generation calls**, none produced a valid typed answer or a correct
complete answer: Coconut had two invalid-JSON EOS terminations and four token-cap
terminations; CODI student and teacher each had six token-cap/missing-EOS failures.
The six derived diagnostic hybrid fallback attempts recovered none. These are
repeated measurements of **one training example**, not 18 independent examples.

All 24 unique broader validation generations reached EOS without hitting the token
cap. Their final results were:

| Validation condition | Typed-valid answers / 8 | Complete correct / 8 | Failure / fallback detail |
| --- | --- | --- | --- |
| Coconut | 4 | 1 | Four `target_count` failures |
| CODI student-only, primary condition | 0 | 0 | Eight `answer_envelope` failures |
| CODI teacher component | 8 | 1 | Valid structure does not imply correct values |
| CODI hybrid, separate condition | 8 | 1 | Eight observable student-failure triggers, eight generated-teacher recoveries |

Inspection of the saved student text shows **all eight outputs used
`{"explanation", "targets"}`**, while the approved student target/parser requires
`{"targets"}`. No explanation field was stripped and no output was repaired.
This localizes the observed failure to generated output format, but does not by
itself establish why branch/format learning failed. Shared-backbone interference
or inadequate optimization are hypotheses requiring a separate diagnosis, not
proven causes. More updates are not guaranteed to fix it.

The hybrid's eight answers therefore came entirely from teacher fallback. They
cannot be reported as student-only performance. Its teacher explanation was
returned, never fed to the student. On validation, Coconut generation took
30.954 s; CODI student took 28.988 s and teacher 28.874 s, for **57.863 s total
hybrid generation work**. Both branches count even when a teacher answer is only
used for fallback. There were **42 unique local generation calls and 46,707 new
tokens** across diagnostic and validation work; deriving hybrid results adds no
calls. Load/process overhead is included separately in the aggregate ledger.

## Numerical forecasts, readout and answer controls

Every numerical method produced finite forecasts for all eight validation
questions. Primary one-step numerical MSE was **0.4068017**, versus autonomous
**225.1636**. The internal step index contributes **99.9997%** of autonomous raw
MSE: predicted range **102.45–198.13**, reference **110–500**. Timestamp prediction
closely follows 0.22–1.00 s; solver/readout times remain the external grid.
The physical block contributes 0.000611282 to raw 140-coordinate MSE and fixed
conditioning contributes 4.56e-12. These mixed-unit aggregates are not substitutes
for named physical errors.

| Load quantity | Primary one-step RMSE | Primary autonomous RMSE | Hold-last autonomous RMSE |
| --- | --- | --- | --- |
| Position, m, Euclidean | 0.004553 | 0.111685 | 0.110158 |
| Swing angle, rad | 0.006702 | 0.164960 | 0.148269 |
| Angular velocity, rad/s | 0.022125 | 0.213835 | 0.218302 |

The hold-last diagnostic is competitive: it has lower pooled position and angle
error, while primary has slightly lower angular-velocity error. This is a
diagnostic comparison, not a new paper baseline. One-step inputs use recorded
states and are explicitly separated from autonomous results. Full tables include
support position/velocity, all six methods, endpoint errors, units, ranges and
coordinate contributions. No sensitivity experiment was run; chaos cannot be
diagnosed from these errors or the familiarity score.

| Frozen answer condition | Correct numerical components / 24 | Supported Boolean correct / supported | Complete answers / 8 |
| --- | --- | --- | --- |
| Primary | 1 | 6/8 | 0 |
| Constant-context text ODE | 1 | 6/8 | 0 |
| LR | 0 | 6/8 | 0 |
| RNN | 3 | 6/8 | 0 |
| no_enrichment | 1 | 6/8 | 0 |
| no_text_conditioning | 1 | 6/8 | 0 |
| Public-only | 21 | No Boolean support | 0 |
| Reversed primary forecast | 0 | 6/8 | 0 |

All 64 answer-provider outputs parsed, but public-only abstained on three numerical
components of one question. Those remain in the 24-component denominator. Its
eight Booleans are unsupported by the control policy and remain in the complete
answer denominator. Forecast conditions supplied qualified sampled public-rule
readout; their predictions were false on all eight questions, whereas evaluator
labels contain six false and two true. Therefore 6/8 is not evidence of detecting
the positive events. The 0.02-s sampled-event limitation remains in force.

The LLM preserved all **168 supported numerical readout values** across the seven
forecast-based conditions exactly. Its prose did not replace the raw trajectories
for metrics. In this small frozen sample, public-only numerical QA was much better
than forecast-based QA; that observation is not a converged-method ranking.
Primary and no_enrichment physical RMSEs are almost indistinguishable, which does
not demonstrate useful exploitation of enrichment.

Reversal now changes each queried position by about **0.769×** its tolerance,
angle by **6.364×**, and angular velocity by **2.601×**: **16/24 numerical changes
exceed tolerance**. All eight Boolean outputs are unchanged. This differs from
the earlier two-update pilot's sub-tolerance reversal and is reported without
retuning the control. Primary versus reversed numerical success is 1/24 versus
0/24, with both 0/8 complete. Removing inactive primary fallback is a no-op;
removing partial assessment changes metadata but not forecasts/answers. Neither
is presented as independent performance evidence. CODI's active teacher fallback
is separately counted above.

## Fixed assessment and clarification status

All eight assessments are **partial, with no threshold decision**. The rebuilt
bank contains 32 training-only predicted references tied to the selected primary
checkpoint/P/Qwen/layout/solver identities. Familiarity scores range from
1.89e-6 to 2.22e-5 despite poor physical answers; they are development familiarity
scores, not correctness or calibrated uncertainty. The unchanged V1 judge returned
scenario/schema scores from 0 to 0.04. Required typed contract coverage was empty.
Separately, the limited taut-tether check evaluated 320 timepoints and flagged
201 violations at its unchanged tolerance. These components are not conflated.
Calibration remains absent, including the minimum-20 independent-scenario gate.

**Interactive clarification exists in the prototype; production integration, its
trigger, and its connection to OOD assessment remain unfinished.**
The notebook's cells 45 and 51 force a clarification request, supply a scripted
reply and make a second answer call using existing predictions. The
[correction and concise proposal](P08_clarification_correction_and_proposal.md)
specifies the remaining trigger, real permitted reply source, refinement and
evaluation decisions. No extension was implemented. Assessment-status explanation
is not substituted for that interaction.

For RQ1, this pilot adds learning curves, eight-scenario physical/QA measurements
and explicit failure evidence. It does not establish good forecasting/QA, reduced
domain engineering or reliable rich explanatory output. Authored layouts, public
rules, mappings and constraints remain disclosed in the
[four-domain coverage inventory](Post_P07_coverage_matrix.md). For RQ2, fixed
assessment mechanisms execute, but detection performance and a production
OOD-linked clarification interaction remain unestablished.

## Resource accounting and verification

| Aggregate resource | Charged / recorded use | Approved cap |
| --- | --- | --- |
| GPU worker time, including teacher work | 3,091.340 s = 51.522 min | 10,800 s |
| CPU charge, including reporting | 328.545 s = 5.476 min | 3,600 s |
| New native artifacts plus review export | 8,068,125,586 bytes, about 8.07 GB | 20,000,000,000 bytes |
| Provider attempts | 111: 39 enrichment, 64 answers, eight judges | 120 |
| Provider input tokens | 1,131,236 | 2,000,000 |
| Provider output tokens | 52,206 | 100,000 |
| Usage-priced provider spend | USD 5.569064 | USD 15 |

No aggregate resource cap was reached; the update allowances were exhausted as
prescribed, and no provider usage remained unknown. One existing enrichment
cache entry was reused. Returned provider model IDs were `gpt-5.6-sol`; this does
not pin an immutable service revision. The recorded price basis is $4 input /
$0.4 cached input / $20 output per million tokens, not a reconciled invoice.
CPU charge includes **75 explicitly conservative seconds** for preflight startup
and bookkeeping, not claimed measurements; the preflight test's measured 18.012 s
is also included. Component buckets and every recorded operation remain in the
ledger. Model CPU peak RAM was not instrumented and is not inferred from GPU
statistics. The reported GPU peaks are allocator allocated/reserved memory.

Runtime: RTX 5090, driver 610.60, PyTorch 2.7.1+cu128, Transformers 4.51.3,
Python 3.12.3. Core/Coconut/CODI environments stayed separate and unchanged;
Matplotlib 3.10.3 was installed in a new reporting-only environment, charged to
CPU/storage. All four generated figures were visually inspected.

Commands actually executed included `prepare_p08.py` selection/enrichment/encoding/
custom preparation, `run_p08_schedule.py` (21 sequential empirical stages), and
`run_p08_reporting.py` (six reporting/verification stages plus export). The final
offline command was:

```text
CUDA_VISIBLE_DEVICES= PYTHONPATH=src python -m unittest discover -s tests -p 'test_p*.py'
```

It passed **127 tests in 17.852 s**; P08 tool compilation also passed. The
[test log](artifacts/P08/tests-final.log), stage logs/identities and integrity
checks distinguish offline behavioral verification from the empirical quality
results above. New code implements the bounded budget/reservation supervisor,
frozen-selection runners, separate custom initializations, evaluator-only
diagnostics and report/export tooling. It does not modify the primary model or
readout architecture.

## Remaining issues and decisions

| Issue | Classification | Evidence and next boundary |
| --- | --- | --- |
| Primary/ODE/RNN forecast errors and weak answer success | Insufficient learning evidence / unresolved optimization quality | Successful finite updates are not sufficient training; diagnose before a larger performance study. No loss/coordinate/feedback redesign is presumed |
| Custom free-generation format and target-count failures | Unresolved learning/generation quality, not a demonstrated parser defect | Preserve exact failures; investigate branch/format discrimination separately. Do not strip fields or promise more updates will fix it |
| Contact-dependent outputs and missing typed assessment contracts | Unsupported capability | Existing four-domain inventory still applies; no hidden state or new head introduced |
| Calibration and OOD recognition performance | Pending scientific evaluation | Complete required components, independent validation calibration and sealed ID/OOD evaluation remain necessary |
| Production/OOD clarification | Scientific/interface decision | Prototype interaction is acknowledged; choose trigger, permitted replies, refinement semantics and evaluation before extending it |
| Full four-domain study, multiple seeds and convergence/ranking claims | Missing evidence | Not authorized or supplied by these eight short-horizon validation scenarios |

No additional decision is needed to close this approved pilot. Future decisions
are: (1) authorize a bounded diagnosis of the observed forecasting and branch-format
failures before assuming a larger run helps; and (2) choose the clarification
integration/evaluation policy in the linked proposal. Neither reopens the settled
primary architecture, target gradients, weighting, solver or feedback contract.
