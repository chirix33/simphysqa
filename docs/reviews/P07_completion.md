# Stage 8/P07 bounded implementation pilot — complete

The user-selected tethered-load correctness/resource evidence package is complete.
Existing data, checkpoints, training updates and generation limits are preserved.
**This is not convergence, generalization, ranking or four-domain-readiness evidence.**
The full study and its performance claims remain pending. No additional training,
model generation, encoder call or API request was made in Stage 8.

Branch `full-phi-jepa-from-dataset`, HEAD
`7f2553ca6591301de588bd3362e72838354169a0`; implementation remains uncommitted.
The [scope decision](../decisions/P07_pilot.md) and
[frozen configuration](../../configs/pilot_p07.json) govern this package. The
content-addressed native export is identified by [export.json](artifacts/P07/export.json).
The final bundle contains 77 verified payloads, manifest SHA256
`79675fd7676e26a051c23fd521a7d136a48b875fa5d590ff50007beec3263d1c`.
Original augmented/numerical trajectories, named physical forecasts, contextual
diagnostics, generated answers, typed errors, costs and checkpoint identities are
separate artifacts. Source files are hashed and the exported payloads are read back
and verified. No push, publication or dataset modification occurred.

## Exact selection and training identity

Seed 11. Training question `08930dbcfe8a3c2273ebd024c397ff39`, scenario
`6dcead753b8ad615a772be98d0c8906f`. Validation question
`494b17e6fb6b7a9dc42c0727f92e0b17`, scenario
`ba28c67a348a7459ddeca5b3de93b385`. A checksum-verified audit of **all 6,702
training metadata records across four domains** found no matching validation base
scenario or split group. All trained methods' scenario identities match the frozen
training selection; the primary/comparator physical-transition sets match exactly.

One training question/scenario supplies 20 question-conditioned pairs and 20 unique
physical transitions. Primary, constant-context ODE, RNN, no_enrichment and
no_text_conditioning each trained independently for 200 updates. LR uses one
least-squares fit (rank 8); it has no neural optimizer steps. Each custom T5 model
uses the same one training question and one descriptive/typed target, for two
updates. The hybrid shares the trained CODI checkpoint; it is an inference condition.
PIN-ODE is excluded. This is not matched training effort or matched capacity.

The validation forecast starts from permitted observations at 0.20 seconds and
contains 40 autonomous future samples, 0.22–1.00 seconds at 0.02-second spacing.
There are four answer targets and one Boolean target. Questions, scenarios, pairs,
timepoints and targets are not interchangeable independent sample counts. No
confidence interval or method ranking is justified from one validation scenario.

Full checkpoint identities are in the export and preceding phase reports. Primary
deployment SHA256 is `f639763501219c6d32e714b3a25daf36a5b4954137b7ae4c74c632f1a4befe8e`;
Coconut final training checkpoint is
`aad86b157cd7eb1e822e24e4bbb9581b5106e791be210fe93ce05263754b5277`;
CODI is `c8ff78fead53c3f7105e348e4c924ba6074092397b0b160363933ab6d955545f`.
Model/encoder pins, layouts, pair identities, objective/gradient/feedback policy,
solver, settings, fixed random projections, provider aliases, formatting and
decoding limits are preserved in their original manifests. Selection is the final
predeclared bounded update; no new validation tuning occurred.

## Behavior observed on the one held-out question

Typed validity and tolerance success are different. A syntactically valid answer
can be physically inaccurate. The table is an accounting of this one case, not a
ranking or estimate of generalization.

| Method / condition | Valid generated targets | Complete numerical/readout success | Complete generated answer success |
| --- | --- | --- | --- |
| Phi-JEPA | 4/4 | 1/1 | 1/1 |
| Constant-context text ODE | 4/4 | 1/1 | 1/1 |
| Fixed-projection LR | 4/4 | 0/1 | 0/1 |
| Constant-context text RNN | 4/4 | 0/1 | 0/1 |
| Independent no_enrichment | 4/4 | 1/1 | 1/1 |
| Independent no_text_conditioning | 4/4 | 1/1 | 1/1 |
| Custom Coconut | 0/4 | Not a numerical-trajectory method | 0/1 |
| Custom CODI student-only | 0/4 | Not a numerical-trajectory method | 0/1 |
| Separate CODI hybrid | 0/4 | Not a numerical-trajectory method | 0/1 |

Primary physical endpoint errors are 0.0017757765 m for load position,
0.0058948985 rad for swing angle and 0.0186108965 rad/s for angular velocity.
Its autonomous load-position RMSE over the 40 future samples is 0.0006688089 m.
Raw mixed-coordinate numerical MSE is 0.6410943 for recorded-input one-step
diagnostics and 354.8456 over autonomous rollout (terminal 1025.7506). The latter
includes advancing state-time/index and fixed numerical fields; it is not a
unit-consistent physical error. They remain separate from named physical metrics.
Terminal contextual L2 drift is 1.13727e-5, fixed-conditioning drift 2.76390e-5;
no resets/corrections are applied. Original by-horizon diagnostics are exported.

LR's load-position error is about 802.29 m, and RNN's about 0.09335 m; these failures
are retained despite valid output JSON and a correct Boolean on this one case.
The narrow tether-length check fails on all 40 LR/RNN samples, and on none of the
primary samples. This is check-specific coverage, not general physical verification.
Primary/no-text/no-enrichment similarity and the more accurate public-only numerical
estimates do not establish text/enrichment benefit or harm.

Primary/ODE/LR/RNN/ablations have Boolean coverage 1/1 and accuracy 1/1 on their one
supported target. Custom outputs have coverage 0/1; supported-only accuracy is
undefined, and complete-answer failure stays in the denominator. Contact-dependent
stable_stack/support_lost remain unsupported work toward full dataset support.

## Stage 7 failure audit and unchanged limits

The [read-only audit](artifacts/P07/output-and-split-audit.json) rechecked the actual
prepared targets and saved checkpoints before interpreting output failures:

- Exact reversible tokenizer and typed-parser round trips passed for all eight
  teacher/student training targets. Teacher lengths 425–1,025 and student lengths
  394–994 are below the 2,048-token target limit. The tether teacher/student lengths
  are 554/523. Every target has exactly one final EOS, no unknown tokens, and no
  truncation. The microbatch-one fit had no padding.
- Actual tether EOS prediction indices are 553/522. Shifted decoder input at each
  index is the preceding final serialized token; alignment is after the complete
  answer at the final decoder layer. CPU tests verify ignored padding does not
  change CE/alignment and receives zero gradient. Teacher alignment graph is
  detached, student gradients exist, and teacher CE still trains the shared T5.
- Saved stopping settings match the frozen configuration: EOS 1, pad/start 0,
  greedy one-beam decoding, 2,048 new tokens, no-repeat-ngram 0, no forced EOS and
  no minimum-length restriction. No budget was increased or generation repaired.
- Re-parsing original generated token IDs reproduces each failure. Across train
  and validation there are **six invalid typed outputs**: two Coconut outputs
  completed with EOS but failed JSON parsing (173/156 generated tokens), and four
  CODI student/teacher outputs reached 2,048 tokens without EOS. Missing-EOS and
  token-cap flags both apply to those four; they are not eight distinct failures.
- Hybrid fallback was attempted for both student failures (2/2), recovered zero
  valid teacher labels (0/2), and consumed both teacher generations. Student-only
  results use no teacher explanation/prediction/fallback. The teacher explanation
  is not supplied to the hybrid's student. All three reported conditions have
  0/1 complete success on training and separately 0/1 on validation.

These implementation checks passed; generated-output quality remains unresolved.
Two updates are not a meaningful answer-quality evaluation. No convergence,
generalization or comparative quality conclusion follows from these failures.

## Controls, assessment and resources

Removing fixed assessment skips its diagnostic callback but produces **no numerical
or answer change** here: assessment does not modify this pilot's prediction.
Removing the inactive fallback is a **no-op**. These are not distinct effective
accuracy ablations or new independent observations. The bounded control execution
read two verified cached answers and one cached assessment, with zero provider calls.
Public-only and reversed-forecast controls preserve their original live provenance.
Public-only numerics were more accurate here, but its Boolean is forced unsupported
by the approved public-only readout policy; full-answer coverage is not a fair
unrestricted-Boolean reasoning comparison. Reversal remained within these generous
target tolerances and is only a diagnostic.

Fixed assessment is partial, uncalibrated and has no threshold decision. Its full-2d
development familiarity score is 1.30849e-5; the unchanged scenario/schema V1 judge
score is 0.0. Required typed contract coverage is empty. No detection accuracy,
physical-correctness probability or calibrated uncertainty is inferred; no numerical
replacement occurred. Reference-bank and checkpoint/encoder identity checks remain.

CPU fitting: primary 2.8435 s, comparator ODE 3.5831 s, RNN 4.2660 s,
no_enrichment 2.5779 s, no_text_conditioning 2.1049 s. LR fit timing is unavailable
because its earlier reporting recovery preserved the completed fit without timing
reconstruction. Solver/model work and historical failures are in each phase report.

| Custom GPU measurement | Coconut | CODI |
| --- | ---: | ---: |
| Longest selected input forward/backward | 28.713 s | 55.345 s |
| Peak allocated memory for that check | 2.857 GB | 3.889 GB |
| Two-update fit including resume | 16.237 s | 25.031 s |
| Fit peak allocated memory | 2.415 GB | 2.959 GB |
| Fresh-process train+validation generation, including load | 6.222 s | 51.946 s |
| Inference peak allocated memory | 0.892 GB | 0.892 GB |

One GPU job at a time; BF16 autocast/FP32 parameters, query blocks 512, microbatch
one. The original eager-attention attempt was terminated at a shortened diagnostic
cap after about ten minutes without completing the first forward; it is retained
as extra attempted compute, not concealed or called CUDA OOM. The equivalent full-key
query-block implementation passed output/all-parameter-gradient comparison and real
long-context qualification. Decoder/cross-attention and scientific objectives remain.

Custom inference made six unique calls, 60,648 input and 8,521 generated tokens.
The validation CODI hybrid costs 24.436 s and 4,096 generated tokens across its two
branches; primary student-only branch time is 12.291 s. Shared student generation
is counted once physically and included in each condition's attributed cost.
There is no fabricated GPU-dollar conversion. Historical provider evidence totals
17 calls, USD 0.831996, including shared four-domain context preparation. Stage 8
added zero API calls/spend; this total is not a per-method tether-only bill.

Native checkpoint read+hash passes measured 0.001162/0.000377 s for the 1,051,853-byte
primary deployment file and 0.484920/0.253796 s for the 956,496,163-byte CODI training
checkpoint. OS cache was not controlled: these are first/second observed passes,
not cold-disk benchmarks. Original cache/resume/replay evidence is exported.

## Verification, recovery and remaining work

**119 model/handoff tests passed in 11.008 s**, including the explicit padding-mask
check. See [test log](artifacts/P07/tests-final.log). The 6,702-record scenario audit,
actual target/stopping/parser audit, immutable export integrity and cached runtime
controls pass. Historical simulation-environment dependency failures remain disclosed
in [P06](P06_completion.md); the frozen dataset was not regenerated.

The initial export wrote and hash-verified its 71 payloads, then its reporting check
unpacked `read_run` in the wrong order. This reporting error was corrected; recovery
read the existing immutable bundle without repeating controls, model work or the
two-pass checkpoint I/O profile. The original bundle is preserved. A final bundle
adds the user-requested audit, final test evidence, control interpretation and
explicit scope approval. Existing checkpoints and results remain byte-identical.

Actual Stage 8 commands (core environment, except the read-only T5 audit uses the
CODI environment; all from repository root in WSL):

```text
python tools/export_p07_pilot.py --native-root /home/aashraf/phi-jepa --output /home/aashraf/phi-jepa/p07-pilot
python tools/export_p07_pilot.py --native-root /home/aashraf/phi-jepa --output /home/aashraf/phi-jepa/p07-pilot --recover /home/aashraf/phi-jepa/p07-pilot/3cfa53cf0ebf9713a5eb5d09ed324593ddf7be46b8fba1883e2b17f585534f1d
CUDA_VISIBLE_DEVICES= python tools/audit_p07_baseline_outputs.py --native-root /home/aashraf/phi-jepa
CUDA_VISIBLE_DEVICES= PYTHONPATH=src python -m unittest discover -s tests -p 'test_p*.py' -v
python tools/finalize_p07_pilot.py --source /home/aashraf/phi-jepa/p07-pilot/3cfa53cf0ebf9713a5eb5d09ed324593ddf7be46b8fba1883e2b17f585534f1d --output /home/aashraf/phi-jepa/p07-pilot
```

The [next-budget proposal](P07_next_budget_proposal.md) specifies a **not-launched**
broader tether diagnostic: 32 train/eight validation scenarios, 1,000 updates per
numerical neural model, 200 per custom model, three GPU hours/one CPU hour, and
at most 120 provider attempts or USD 15 (plus token caps). These are ceilings based
on measured work, not promises of convergence. Approval and frozen IDs precede it.

Full study remains pending: meaningful independent training, all-release input and
target coverage, validation-only checkpoint/calibration policy, missing required
contract evidence, unsupported contact-event mechanisms, four-domain ID/OOD matrix,
multiple seeds and scenario-grouped uncertainty. No new architecture, primary loss,
Boolean head, PIN-ODE, EBM, latent optimization or schema repair is implied.
