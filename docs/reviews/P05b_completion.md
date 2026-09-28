# Stage 6/P05b implementation report — 24 September 2026

Status: **complete for the approved comparisons, two retraining ablations and
runtime controls, with bounded correctness validation**. The user supplied explicit
`no_enrichment` and `no_text_conditioning` definitions; both are independently
trained and validated below. Undefined structural-schema removal is not implemented
and is explicitly not a blocker. Stage 7 has not started at this handoff.

Branch `full-phi-jepa-from-dataset`, base/current HEAD
`7f2553ca6591301de588bd3362e72838354169a0`; changes uncommitted. Stage 5 was completed
before these fits. The original notebook, dataset and primary predictor/training
implementation are preserved. This report makes no benchmark-performance claim.

## Definitions, implementation and tests

See [the user-approved method definitions](../decisions/P05b_comparators.md).
`baselines/conventional.py`, `training.py` and `checkpoint.py` implement separate
projections/models, numerical-only targets, constant p, equal-transition training,
chronological recurrent hidden-state behavior, one LR SVD fit, strict finite checks,
method-specific checkpoint/resume and public-only autonomous inference.

`baselines/controls.py` implements distinctly labeled runtime controls: no fixed
assessment, no fallback, and public-only answers. It does not claim context/schema
removal retraining. `readout.py` accepts explicitly marked numerical-only outputs
without fabricating a predicted context block. Typed physical evaluation, Boolean
rules, unsupported statuses and final answer parsing are shared.

**104 P00–P05b offline tests passed in 12.650 seconds, zero skips.** Tests verify
independent parameter storage/updates, P gradients, constant p, LR fixed projection
and rank reporting, recurrent carry/reset and chronology, equal transition weighting
across unequal sequence lengths, resume parity, method/role isolation, invalid
input failure accounting and disabled runtime branches. Every real deployment
checkpoint reproduced its full saved validation trajectory exactly in a fresh
process. All three answer responses replay exactly from cache with network forbidden.

## Actual correctness fits and negative results

All methods used exactly the same 20 training transitions/one question as P03,
with a distinct validation scenario and 40 future samples. No primary checkpoint
weights were loaded. ODE and RNN independently trained their own P; LR's P remained
bitwise unchanged. Both neural runs checkpointed/resumed at update 100.

| Method | Actual fit | Initial / final pre-update training numerical MSE | Time |
| --- | --- | ---: | ---: |
| Constant-context text ODE | 200 updates | 0.714317 / 0.641551 | 3.583129 s |
| Fixed-projection LR | One SVD least-squares fit; rank 8, 20x281 design | Fit residual SSE 8.09684e-5; not neural MSE | unavailable after reporting failure |
| Constant-context text RNN | 200 updates | 325.797760 / 243.367477 | 4.265998 s |

These losses are numerical-block objectives and are not directly the primary
full-2d training objective. LR is strongly underdetermined/rank deficient. Its
143,500 fixed projection parameters and 39,340 fitted coefficients are distinct;
gradient-trainable count zero does not mean it has no fitted parameters. ODE has
214,168 gradient-trainable parameters; RNN has 214,040.

Same validation endpoint, original numerical forecast errors:

| Method | Position error (m) | Angle error (rad) | Angular velocity error (rad/s) | Complete numeric+rule / final-answer success |
| --- | ---: | ---: | ---: | --- |
| Constant-context text ODE | 0.001776294 | 0.005893637 | 0.018607939 | 1/1 / 1/1 |
| Fixed-projection LR | 802.289348 | 7315.978305 | 1221690.385241 | 0/1 / 0/1 |
| Constant-context text RNN | 0.093349873 | 0.002187640 | 0.029031767 | 0/1 / 0/1 |

Each method's single supported Boolean was correct; that does not rescue incorrect
numerical components from the complete-answer denominator. Tether-length PCVR:
ODE 0/40 violations; LR and RNN 40/40. This is narrow check coverage, not general
physical validity. Large finite LR errors and RNN failures remain recorded.
All three final-answer API calls succeeded, so the failed complete answers above
are model-output errors rather than transport/parser failures. The public-only
LLM answer from P04a has 0/1 complete success due to required Boolean abstention,
despite more accurate numerical estimates; that policy limitation is disclosed.

No threshold, early stopping, selection criterion or fit was changed to improve
these results. No test/OOD evaluation or full training occurred. The tiny data
selection cannot establish comparative benchmark performance.

## Accounting, recovery and artifacts

There was one real reporting failure: a NumPy Boolean prevented serialization of
the LR summary after its fit, checkpoint and forecast had completed. It was fixed
and the report recovered from the preserved fitted coefficients. ODE was reused;
LR was not fit or forecast again. Original LR fit time remains null. The resume
then ran the pending RNN once. Exact recovery details are in its saved summary.

Actual numerical work, excluding offline fixture tests: ODE training 200 solves /
800 NFE / 16000 sample-NFE; original and fresh-replay forecasts add 80 solves /
320 NFE / 320 sample-NFE. Total ODE **280 solves, 1120 NFE, 16320 sample-NFE**.
RNN training 4000 recurrent calls, original/replay forecasts 80 more; LR one fit
and 80 original/replay forecast calls. Read-only SVD recovery is separately disclosed.
Five encoder cache hits across the initial run, recovery and replay; zero new E
model calls. Two neural fits totaling 400 updates, no repeated completed fit.

Three live answer calls, no retries/failures: 44,555 input tokens, 1271 output tokens,
usage-priced USD **0.203640**. Answer cache replay adds three exact hits and zero
API calls. The reused direct-LLM answer retains its original Stage 4 cost, not a
new charge. Alias snapshot reproducibility remains limited to preserved responses.

Commands actually run in isolated WSL core:

```text
PYTHONPATH=src python -m unittest discover -s tests -p test_p05b.py -v
python tools/run_p05b_correctness.py --profile /home/aashraf/phi-jepa/p02b-profile --primary-run /home/aashraf/phi-jepa/p03-correctness-01 --cache-dir /home/aashraf/phi-jepa/model-cache --output /home/aashraf/phi-jepa/p05b-correctness-01
python tools/run_p05b_correctness.py --profile /home/aashraf/phi-jepa/p02b-profile --primary-run /home/aashraf/phi-jepa/p03-correctness-01 --cache-dir /home/aashraf/phi-jepa/model-cache --output /home/aashraf/phi-jepa/p05b-correctness-01 --resume
python tools/verify_p05b_replay.py --run /home/aashraf/phi-jepa/p05b-correctness-01 --profile /home/aashraf/phi-jepa/p02b-profile --cache-dir /home/aashraf/phi-jepa/model-cache
python tools/answer_p05b_forecasts.py --run /home/aashraf/phi-jepa/p05b-correctness-01
python tools/evaluate_p05b.py --run /home/aashraf/phi-jepa/p05b-correctness-01 --primary-answer-run /home/aashraf/phi-jepa/p04a-answers-01
PYTHONPATH=src python -m unittest discover -s tests -p 'test_p0*.py' -v
python tools/verify_p05b_answers.py --run /home/aashraf/phi-jepa/p05b-correctness-01
python tools/collect_p05b_evidence.py --run /home/aashraf/phi-jepa/p05b-correctness-01
```

Native independent weights, histories, immutable forecasts, provider caches and
per-time errors: `/home/aashraf/phi-jepa/p05b-correctness-01`. Compact evidence and
exact source/native hashes: `docs/reviews/artifacts/P05b/`. No credentials or weights
are added to Git. No push, publication or simulator regeneration occurred.

## Additional user-approved retraining ablations

Both used the same 20 question-conditioned transitions, uniform weights, independent
initializations, no borrowed primary weights, 200 updates each and the same separate
validation query. `no_enrichment` contains no generated notes in model inputs and
keeps full augmented training and both P gradients. `no_text_conditioning` removes
E/P/p entirely while retaining every accepted numerical conditioning coordinate.
The latter is a numerical-only component ablation, not a text-based comparison.

| Variant | State width / parameters | Training objective, initial -> final pre-update | Fit time |
| --- | --- | --- | ---: |
| no_enrichment | 280 / 232,228 | full augmented MSE 0.357145 -> 0.320721 | 2.577922 s |
| no_text_conditioning | 140 / 52,748 | numerical MSE 0.714287 -> 0.641662 | 2.104881 s |

Different loss widths/capacities are explicit. Numerical endpoint errors:

| Variant | Position (m) | Angle (rad) | Angular velocity (rad/s) | Complete numeric+rule / answer |
| --- | ---: | ---: | ---: | --- |
| no_enrichment | 0.001775697 | 0.005894912 | 0.018610907 | 1/1 / 1/1 |
| no_text_conditioning | 0.001776385 | 0.005893226 | 0.018608269 | 1/1 / 1/1 |

Both checkpoints and both final answers replay exactly. These close results do not
establish a benefit from enrichment or textual conditioning on this tiny profile.
No method was selected or modified from the validation outcome. Runtime removal
of inactive assessment/fallback is explicitly a no-op, not a distinct effective
ablation. High-score replacement remains disabled.

Additional numerical work: each variant 200 training solves/800 NFE/16000 sample-NFE,
plus 80 original/replay forecast solves/320 NFE/320 sample-NFE. Combined Stage 6
total across three ODE-based fits and replays: **840 solves, 3360 NFE, 48960
sample-NFE**. RNN and LR work remains as reported above. Stage 6 neural updates
total 800 across four separately capped methods. Three additional base-E cache
hits belong to no_enrichment preparation/replay; no_text uses no encoder. No new
E calls. Two additional answer calls: 30,970 input/753 output tokens, USD 0.138940.
Whole Stage 6 answer cost is **USD 0.342580** for five calls, no retries/failures.

Additional commands actually run (same core environment):

```text
python tools/run_p05b_ablations.py --profile /home/aashraf/phi-jepa/p02b-profile --primary-run /home/aashraf/phi-jepa/p03-correctness-01 --cache-dir /home/aashraf/phi-jepa/model-cache --output /home/aashraf/phi-jepa/p05b-ablations-01
python tools/verify_p05b_ablation_replay.py --run /home/aashraf/phi-jepa/p05b-ablations-01 --profile /home/aashraf/phi-jepa/p02b-profile --cache-dir /home/aashraf/phi-jepa/model-cache
python tools/answer_p05b_forecasts.py --run /home/aashraf/phi-jepa/p05b-ablations-01
python tools/evaluate_p05b.py --run /home/aashraf/phi-jepa/p05b-ablations-01 --primary-answer-run /home/aashraf/phi-jepa/p04a-answers-01
python tools/verify_p05b_answers.py --run /home/aashraf/phi-jepa/p05b-ablations-01
python tools/collect_p05b_evidence.py --run /home/aashraf/phi-jepa/p05b-ablations-01 --ablations
```

Full final regression includes the base-context training/resume guard and tests
that numerical-only models have no projection/embedding pathway. See
`artifacts/P05b/tests-wsl-final.log`. Native ablation artifacts are separate under
`/home/aashraf/phi-jepa/p05b-ablations-01`; compact evidence/hashes are in
`artifacts/P05b/ablations/`. The primary enriched procedure remains unchanged.

Next: Stage 7 custom Coconut-inspired/CODI-inspired models under the newly approved
fixed teacher projection, EOS-position alignment, descriptive training targets,
primary student-only inference and separately reported teacher-assisted hybrid.
No Stage 7 download, environment modification or fit ran before this handoff.
