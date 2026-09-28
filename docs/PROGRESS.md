# P10 integrated qualification — bounded execution complete, 25 September 2026

The latest user instruction authorizes the integrated workflow and a new budget,
superseding the earlier follow-up's offline-only restriction. See the
[active prompt](prompts/P10_integrated_qualification.md),
[recorded decisions](decisions/P10_qualification.md), and
[executable workflow](P10_pipeline.md). Current base commit is `5a375bd` on
`full-phi-jepa-from-dataset`. P10 changes are local and have not been committed or
pushed by the agent. The earlier P09 changes were committed by the user before
this run; the historical status below describes their original execution time.

The integrated pipeline ran through independent training, selected-checkpoint
deployment, separate evaluation, assessment, budgeted answers and export. See
[completion](reviews/P10_completion.md), [measured benchmark](reviews/P10_benchmark_report.md)
and [the unexecuted full-study proposal](reviews/P10_next_full_study.md).
103 targeted tests pass. The two-question numerical fitting check succeeds;
validation load forecasting improves over hold-last, but primary complete-answer
success is only 1/8. Selected Coconut/CODI outputs parse on 8/8 validation questions;
complete-answer accuracy remains 1/8 and 2/8 respectively. The public-only control
is stronger on common numerical targets. No primary-method superiority,
four-domain performance, calibrated OOD detection or convergence is claimed.
All original evidence, failed attempts and unsupported components are preserved.

## Historical P08/P09 follow-up status — 25 September 2026

Completed the [offline P08 diagnosis](reviews/Post_P08_diagnosis.md), then the
[clarification v1 implementation](reviews/P09_clarification_completion.md), with
separate evidence and reports. P08 is closed as a completed bounded pilot;
learning quality and research claims remain unresolved. No additional training,
paid calls or model generation occurred in these follow-ups.

Diagnosis found near-constant primary derivatives with heavily saturated tanh
layers, time/index dominance in both loss and gradients, no post-event training
transitions, CODI student teacher-envelope outputs and duplicate Coconut targets.
These measurements do not establish causal explanations or justify an objective
change. Original strict scores, checkpoints and P07/P08 evidence are preserved.

Clarification now supports one structured question, an actual attributed reply,
recorded human reply review, conservative routing and at most one frozen-answer
refinement. Unreviewed replies remain unresolved. No calibrated OOD alarm,
automatic reforecasting or unsupported-value invention is implemented. Mock
traces verify software behavior; effectiveness and independently reviewed live
evaluation remain pending. The historical
[P08 clarification proposal](reviews/P08_clarification_correction_and_proposal.md)
is unchanged; its proposal-only restriction is superseded by the user's latest
approval and the [active scope](decisions/Post_P08_and_P09_scope.md).

Base implementation revision: `c6922b16a254a72be58482773e3410fa6eecd0c8`.
Follow-up changes are local; the agent has not committed or pushed them.

## Historical P08 learning-pilot status

P08 completed the user-approved [revised pilot](reviews/Post_P07_next_pilot_revision.md)
within every cap. The [completion report](reviews/P08_completion.md) includes
learning curves, generation failures, coordinate/physical errors, hold-last
comparisons and resource accounting. All five numerical neural fits reached
1,000 updates, LR performed one fit, and each custom method completed separate
fresh 20-update diagnostic and 180-update broader runs. The exact
[32/eight selection](reviews/artifacts/P08/selection.json) was frozen before work;
entire validation scenarios were excluded from training.

Primary achieved 0/8 complete validation answers and 1/24 correct numerical
components. Coconut typed validity was 4/8; CODI student validity was 0/8, with
eight teacher fallback recoveries reported only in the separate hybrid condition.
These failures remain in all denominators. The bounded execution is complete,
but learning quality, convergence and full-study claims are not established.
The run used 51.52 GPU minutes, 5.48 charged CPU minutes, about 8.07 GB of new
artifacts and USD 5.57 over 111 provider attempts. Final offline verification
passed 127 tests; all 73 original P07 source-artifact hashes were unchanged.
The current implementation base is `ba5d31d` (including the committed audit fixes);
each new stage records working-tree source hashes and configuration identities.
New P08 work remains local and uncommitted/unpushed.
Original evidence/checkpoints are preserved; new native results are under
`/home/aashraf/phi-jepa/p08-learning-01`.

**Clarification correction:** Interactive clarification exists in the prototype;
production integration, its trigger, and its connection to OOD assessment remain
unfinished. Notebook cells 45 and 51 implement the forced/scripted two-call demo.
The [correction and proposal](reviews/P08_clarification_correction_and_proposal.md)
supersede the prototype omission in the historical audit. Assessment-status
explanation is not substituted for interactive clarification. This extension,
calibration and full-study claims remain pending and do not delay this pilot.

# Historical post-P07 audit status — 25 September 2026

The requested [focused source/artifact audit](reviews/Post_P07_focused_audit.md)
is complete, with three contract-preserving fixes and **124 passing targeted
tests**. The saved primary rollout replays exactly; coordinate diagnostics show
step-index error dominates raw numerical MSE. Custom checkpoint updates and
gradient/optimizer paths are verified, but output-quality failures remain.
The [four-domain matrix](reviews/Post_P07_coverage_matrix.md) records contact-event,
initial-crossing-state, typed-contract and calibration gaps. RQ1/RQ2 evidence is
mapped explicitly; OOD clarification still needs an operational definition.

The audit began from clean implementation commit
`5810d1899007ae602c3db1ca486d43a1b7865ba4` on `full-phi-jepa-from-dataset`;
the local origin-tracking reference matches (no remote refresh performed).
Audit changes are uncommitted; no commit/push was requested or performed.
The older status entries below retain their historical run-time meaning.
Original reports/checkpoints are preserved. No new empirical training, encoder
forward, model generation, paid call or dataset regeneration occurred.
The [revised proposed budget](reviews/Post_P07_next_pilot_revision.md) reserves a
training-only fitting diagnostic inside the previous caps; it is not launched.

# Historical sequential-plan status — 24 September 2026

Stage 8/P07 is **complete for the user-approved bounded correctness/resource
evidence package**. Existing seed-11 tether selections/checkpoints and limits are
preserved. 119 tests pass. All 6,702 training metadata records exclude the entire
validation scenario. Actual target round trips, EOS shift, padding/loss masking,
stopping settings and failure parsing pass; two invalid completed outputs and four
token-cap/missing-EOS outputs remain failures, with 2/2 hybrid fallback attempts
and 0/2 recoveries. No new training/generation/API calls or altered limits. Immutable
export, runtime controls/no-op labels and resource evidence are in the
[P07 report](reviews/P07_completion.md). Full study, convergence/generalization and
performance claims remain pending. The [broader budget](reviews/P07_next_budget_proposal.md)
is proposed only, not launched. All implementation changes remain uncommitted.

Stage 7 is complete for bounded implementation/correctness validation. 118 tests
pass; both independently trained custom T5 models pass longest-selected-input
forward/backward, checkpoint resume and fresh-process generation. All generated
answers fail after two updates; the 0/1 complete-answer result per condition and
split is retained. Original eager-attention timeout and the equivalent query-block
memory correction are documented. See [P06 report](reviews/P06_completion.md) and
[decisions](decisions/P06_custom_baselines.md). Stage 8 now uses the existing bounded
one-domain profile as correctness/resource evidence, without additional tuning or
full-study expansion; a broader pilot was offered for user clarification.

Stage 6 is now complete for the approved comparisons, runtime controls and explicit
`no_enrichment`/`no_text_conditioning` retraining variants. Both extra independent
fits ran 200 updates, replay exactly, and preserve negative/no-benefit evidence.
No undefined no-schema variant is added; it is not a blocker. Whole Stage 6 answer
cost USD 0.342580. See the updated [P05b report](reviews/P05b_completion.md).
Stage 7 alignment/target/inference policies are approved and recorded in the task;
Stage 7 is next. Full study remains unlaunched.

Stage 6/P05b approved independent ODE/LR/RNN comparisons and runtime controls are
implemented and correctness-validated: 104 tests pass, all checkpoint/answer
replays exact, 200 updates per neural method and one LR fit. LR reporting recovery
did not repeat the fit. Large LR and RNN forecast failures remain recorded. Three
answer calls cost USD 0.203640. Context/schema retraining-ablation scope remains
pending user clarification; Stage 7 has not started. See
[P05b report](reviews/P05b_completion.md).

Stage 5/P04b–P05a is complete for implementation and bounded development validation.
97 offline tests pass. Training-only full-2d reference assessment and exact V1
judge ran on one tether validation question. Combined assessment remains partial
and uncalibrated because typed contract coverage is empty; no threshold decision
or numerical replacement. One judge call cost USD 0.025868. See
[P04b completion](reviews/P04b_completion.md). Stage 6 comparator definitions and
optional LR/RNN selection are pending user replies; Stage 6+ has not started.

Stage 4/P04a is complete for the approved initial deterministic readout and bounded
answer diagnostic. Named physical forecasts remain separate from full augmented
states and LLM answers. Target-specific support checks retain unsupported contact
outcomes and full failure denominators. Three live validation answer calls cost
USD 0.196584; exact cached replay passes. The answer model uses the supplied
forecasts, but public-only numeric estimates are more accurate on this single
question; no forecasting-benefit claim. See [P04a completion](reviews/P04a_completion.md).
The user approved Stage 5 full-2d development familiarity assessment; Stage 5 is
next. No Stage 6+ work or full training has launched.

Stage 3/P03 is complete for bounded correctness validation. User-approved equal
question-pair weights, adjacent-pair full-vector loss, both P gradient paths,
complete predicted feedback and atomic training/deployment checkpoints are
implemented. A 20-pair tether fit ran 200 CPU updates in 2.8435 s, with exact
checkpoint continuation/replay. Autonomous error is high and tested numeric
forecast sensitivity to Q is near zero; no performance claim is made. See
[P03 completion](reviews/P03_completion.md). Stage 4 output-only Boolean/readout
policy and gpt-5.6-sol answer model are now explicitly authorized. Stage 4 is next;
no Stage 5+ work or full training has launched.

Stage 2/P02b is complete with declared API snapshot/semantic-audit limitations.
User replaced MiniLM with pinned `Qwen/Qwen3-Embedding-0.6B`, authorized downloads
and live calls without a current spending limit, and selected a dotenv key-file
reference. 36 offline tests pass (zero skips); 8038 base contexts fit; eight live
enrichments and their GPU encodings pass; usage-priced cost USD 0.266964.
See [completion](reviews/P02b_completion.md). Stage 3 is next, with user-confirmed
**equal weight per question-conditioned pair**. Model training has not begun.

## Historical initial P02b status — superseded above

Revision-4 sequential implementation is authorized by the user. P02a/Stage 1
remains complete. P02b/Stage 2 is **in progress**: offline provider/context/cache
boundaries implemented; tensor and real-model validation pending. User selected
`sentence-transformers/all-MiniLM-L6-v2` and OpenAI `gpt-5.6-sol`. Download/live
budgets, core runtime preparation and MiniLM full-context policy remain pending.
12 new offline tests passed, 3 tensor tests skipped; 15 P02a regressions passed.
No live inference, model downloads, training or later-stage launch occurred.
See [P02b interim report](reviews/P02b_completion.md) and
[decisions](decisions/P02b_context.md). Work is uncommitted on
`full-phi-jepa-from-dataset`, base `7f2553ca6591301de588bd3362e72838354169a0`.

# Active P02a status — 24 September 2026

Implementation/evidence commit: `cd6497856a94b3d01e0500ac54134a844e01e003`.
43 offline tests passed; final export audit 188.131772 seconds.
All three P02a policy choices are settled; next-stage work remains unlaunched.

Stage 1/P02a offline implementation and real-export validation are complete on `full-phi-jepa-from-dataset`, starting HEAD
`4f7d3e6b53009627b0b4223b2138ec5993c93726`, initially clean. Current user
decisions supersede contract 1.1.0 and older endpoint-only architectures. See
[active training contract](../MODEL_TRAINING_CONTRACT.md),
[supersession](decisions/P02a_supersession.md), and
[state mapping](docs/P02a_state_mapping.md). Historical entries below retain their
original dates and status; they do not override current authority.

Verified 6,340 scenarios / 11,105 questions and 28,405 payload checksums.
Training plan: 454,130 question-conditioned adjacent pairs / 334,890 unique
physical transitions. User accepted state-plus-fixed-conditioning and public-only
LLM enrichment. Separate Boolean/event mechanism proposal selected; training is disabled.
See [P02a completion](reviews/P02a_completion.md).

# Implementation progress

Four-domain production generation and local export completed on 24 September 2026.
Generation revision `a8920b23dfbdb089b95cee5c00a47758b942d4ce`: exactly 6,800
attempted base scenarios, 6,340 admitted, 460 quarantined, 11,105 admitted questions.
All 24 partitions and combined-data checks passed; frozen thresholds and rejection
policy were preserved. Native-storage resume reused 711 completed attempts.
See [completion report](reviews/PDS_generation_completion.md) for counts, measured
runtime/storage, hashes and commands. No training, push or publication occurred.
Earlier preparation/disabled-state entries below are historical.

License finalization, 24 September 2026: user confirmed rights-holder Kaushik Roy
and authority for the scoped CC BY 4.0 dataset/assets and MIT generation code.
Notices and frozen legal metadata finalized; production remains disabled.
See [authorization decision](decisions/License_authorization.md). Earlier pending
licensing entries below describe the historical preparation state.

Release preparation, 24 September 2026: CC BY 4.0 dataset/asset and MIT code
licenses prepared with explicit file scope; rights-holder name and authority
remain pending. Frozen source `f70ee987abea09607260f34407f8b841753fb70d`; 6,800
attempted draws, no resampling, production disabled. 74 offline tests passed.
See [preparation report](reviews/PDS_release_preparation_completion.md).

Four-domain scope amendment, 24 September 2026: quadruped/MJX deferred; current
configuration failed unchanged qualification thresholds. Investigation preserved
in commit `3fcbf8f32d6d0732c11016b67ad5b0f460f68f58`. Release selection now includes
only arm, driving, objects and corrected tether. Planned total 6,800; production
generated/admitted 0. Production remains disabled. See
[readiness review](reviews/PDS_four_domain_completion.md). Earlier entries below
are historical and their five-domain release blocker is superseded.

Updated from P00/P01 and the separately authorized dataset preparation task.
P02–P08 remain plans, not completed model code. The newer dataset/model contract
1.1.0 supersedes older physical-readout training assumptions for future work.

Quadruped follow-up, 24 September 2026, `dataset-prep`, starting commit
`4b997efd1dcbc8199c5981e44c71bd39fa8b7cb9`: fixed the controller-frequency
confound in timestep refinement. A 24-run fixed-clock/one-factor MJX study
initially qualified the 0.2 rad hip-amplitude gait at 0.5/0.25 ms under unchanged
nominal endpoint/event thresholds. A later repeat audit failed those original
tolerances, revoking that provisional qualification. Two serial 0.125 ms runs
also fail: terminal base velocity differs by 0.016544569 m/s versus 0.01 m/s.
Intermediate trajectory discrepancies remain explicit.
Real force-duration/torque-hold checks and all 26 trace audits passed; Linux
regression: 65 tests passed. Varied smoke completed with 5/20 admitted and 15/20
quarantined (nine development records); these do not qualify a release. Calibration
remains gated, with zero calibration scenarios simulated. Status remains
`implemented_pending_validation`. See the
[follow-up report](reviews/PDS_quadruped_refinement_completion.md) and
[decisions](decisions/Quadruped_fixed_clock.md). Earlier quadruped comparisons
changed controller frequency and are preserved as historical raw evidence, not
isolated integration-convergence measurements.

Dataset preparation, 24 September 2026, branch `dataset-prep`, starting commit
`983feaec76acfd923cc7b7d18844ddd92696daff`: **implemented_pending_validation**.
Five simulator adapters and the strict numeric/text/extraction contracts exist;
four domains have admitted smoke/calibration artifacts. The MJX quadruped executes
on GPU but fails controller/refinement qualification; its 100-case calibration
and final generation remain blocked. Final Linux suite: 55 tests passed. No
model training or production generation occurred. See the
[dataset report](reviews/PDS_completion.md), [decisions](decisions/Dataset_preparation.md)
and [measured summary](reviews/artifacts/PDS/summary.json). Earlier tether pilots
are superseded by the corrected-onset runs identified in the report. Changes
remain uncommitted for review; the pre-existing user assets are preserved.

| Phase | Status | Evidence/report |
| --- | --- | --- |
| P00 | complete | [Completion report](reviews/P00_completion.md), [repository audit](reviews/P00_repo_audit.md); eight CPU tests passed; offline editable install and CLI verified |
| P01 | complete | [Completion report](reviews/P01_completion.md); 28 CPU tests passed, 32-family dataset and independent oracle/evaluator verification |
| P02 | not_started | — |
| P03 | not_started | — |
| P04 | not_started | — |
| P05 | not_started | — |
| P06 | not_started | — |
| P07 | not_started | — |
| P08 | not_started | — |

Environment evidence: the active P00 prompt records the user-reported WSL check PASS: PyTorch 2.7.1+cu128, CUDA runtime 12.8, RTX 5090 capability (12, 0), BF16 support and FP32/BF16 forward/backward. The coding agent did not run that GPU check; model-specific gates remain pending. P00 was verified locally on Windows CPU with Python 3.12.14 and setuptools 84.0.0. Scientific decision items Q1–Q4 remain open in [defaults and decisions](docs/08_defaults_decisions.md).

P00 branch: `codex/p00-bootstrap`; base/current HEAD `8e1cd56feb8f9fb0ec8aee92b0d0365b32722066`; changes uncommitted for review. No unresolved P00 blockers. Fixture manifests/results and exact commands are linked in the completion report. [Engineering decisions](decisions/P00_bootstrap.md) record installation, environment, packaging and artifact choices. Next step: planner/user review of P00; P01 requires separate authorization.

For every change: date, phase/substep, exact commit, actual checks, artifacts, remaining blockers and next step. Do not replace this with a list of aspirational completed checkboxes.

P01: authorized by the user after planner acceptance of P00. Started at `dbff9573fa3d13adf4edafa42976afc2e5208e90` on `codex/p00-bootstrap` with only the expanded P01 prompt dirty; preserved it unchanged. P01 additions are uncommitted. See [P01 decisions](decisions/P01_data.md) and the completion report for exact checks, artifacts and limitations. No unresolved P01 blockers. Next: review P01; P02 requires separate authorization.

Boolean/event update (24 September 2026): the user selected a separate mechanism
proposal for later review. No Boolean casting, new head or objective is implemented
here. See `docs/docs/P02a_boolean_event_proposal.md` from the repository root.
