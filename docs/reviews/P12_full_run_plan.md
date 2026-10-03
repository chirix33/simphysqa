# Expanded study — historical proposal and current execution boundary

**29 September execution update:** the user has now authorized the separate
training-only proposal with SHA-256
`13cc4b3cbe8578abe22ebe8faa0987b2de2b3309639bf5e7a9988f4e0542add3`.
Its fixed numerical run completed under the original bounded settings: ten
passes per domain, 17,742 updates, 4,541,952 pair presentations and 54.51 minutes.
See the [training completion report](P12_training_completion.md),
[execution decisions](../decisions/P12_training_execution.md) and
[current progress](../PROGRESS.md). The preparation-time status below is preserved
as history; it does not override the later explicit training authorization.

Confirmation evaluation and local-baseline generation remain disabled. The final
evaluation plan must contain Qwen thinking-off/on, **Llama direct-answer and
Llama prompted CoT**. The historical three-condition/1,500-attempt evaluation
proposal below cannot be enabled unchanged: four conditions on 500 questions
require 2,000 attempts before retries, separately qualified settings and a new
explicit evaluation budget. This training run grants none of that generation scope.

## Preserved preparation-time proposal

Latest: the [regenerated training plan](P12_training_preparation.md) binds all
completed context manifests and passes preflight with zero missing/integrity
failures. **Numerical training has not started.** The new
[machine-readable proposal](artifacts/P12_training_plan/proposed-training-plan.json)
is disabled and separates numerical-training authorization from later evaluation.
The population, exposure and validation schedule below remain unchanged.

Preparation update, 29 September: [enrichment is complete](P12_enrichment_recovery.md)
for all 8,038 train/validation and 500 confirmation questions after the separately
approved full run and two-record recovery. Earlier missing-note figures and API
estimates below describe the initial plan. [Frozen-encoder preparation](P12_embedding_preparation.md)
is also complete: 8,038 train/validation plus 500 confirmation embeddings passed
the identity/provenance audit, with zero missing. [Llama runtime qualification](P12_llama_qualification.md)
is now complete, but all eight diagnostic responses failed the frozen JSON parser.
Full-study execution is still disabled and has not started.

The embedding run reused 224 vectors and generated 7,814 training/validation
plus 500 confirmation vectors in 1,193.655 encoding seconds. Its completed
coverage/origin manifests are separate from the original historical audits.
The numerical-training proposal has now been regenerated to bind those manifests.
Its numerical source is locked independently of the user's local-answer
diagnostics. A separate evaluation plan must freeze the final answer conditions;
the old disabled proposal cannot be enabled unchanged.

This is a new seed-11 study, separate from qualification and all historical
results. The proposed native destination is
`/home/aashraf/phi-jepa/p12-expanded-study-seed11`. The current native proposal is
`/home/aashraf/phi-jepa/p12-training-plan-01/proposed-training-plan.json`, with
`training_enabled: false`, global `enabled: false` and `evaluation_enabled: false`.
The [original proposal](artifacts/P12/proposed-training-plan.json) is preserved.
No training-run budget has been activated. See [the completion report](P12_completion.md)
for the original measured evidence and preparation gates. The later
[enrichment pilot](P12_enrichment_pilot.md) supplies measured preparation costs
and its original spending proposal. That historical qualification source remains
preserved. The new numerical proposal contains current source/runtime/layout
identities, but is not execution approval. Numerical training may be approved
independently of the later answer-interface decisions.

## Population and exposure

Use every admitted original training simulation and every eligible
question-conditioned adjacent pair. Batch 256, shuffled complete cycles with
carried tails, ten full passes, seed 11, Adam learning rate 0.001, gradient clip
1.0, existing RK4 with one substep. All pair weights are one. Fresh models use
the accepted train-only conditioning and derivative initialization. The frozen
encoder, projection, augmented loss, target gradients and inference recurrence
remain unchanged. CPU is recommended: CUDA did not materially improve the
small-model update timings and is needed for encoder/LLM work.

| Domain | Scenarios | Questions | Pairs/pass | Updates | Actual pair presentations | Tail beyond ten passes |
|---|---:|---:|---:|---:|---:|---:|
| robotic_arm | 981 | 1,962 | 127,530 | 4,982 | 1,275,392 | 92 |
| driving | 740 | 740 | 66,600 | 2,602 | 666,112 | 112 |
| object_pushing_stacking | 1,000 | 2,000 | 130,000 | 5,079 | 1,300,224 | 224 |
| tethered_load | 1,000 | 2,000 | 130,000 | 5,079 | 1,300,224 | 224 |
| Total | **3,721** | **6,702** | **454,130** | **17,742** | **4,541,952** | **652** |

Every pair receives ten presentations; only the final shuffled partial cycle
receives an eleventh. Exposure is based on the expanded population, not the old
20,000-update allowance. Historical P11 presented 400,000 pairs per domain;
the proposed exposure is 1.67–3.25 times that, spread across the complete training
population. Ten passes are an initial bounded learning-curve study. They do not
establish convergence. Further passes require a new decision using training and
validation curves only.

Save resumable optimizer/RNG state every 100 updates, and retain deployment
checkpoints after every completed pass. Pass checkpoints are:

- Driving: 261, 521, 781, 1,041, 1,301, 1,561, 1,822, 2,082, 2,342, 2,602.
- Arm: 499, 997, 1,495, 1,993, 2,491, 2,989, 3,488, 3,986, 4,484, 4,982.
- Objects and tether: 508, 1,016, 1,524, 2,032, 2,540, 3,047, 3,555, 4,063, 4,571, 5,079.

At each milestone, evaluate all original validation questions for that domain:
148 driving, 388 arm, 400 objects, 400 tether. Use the existing mean
tolerance-normalized numerical target error, a fixed `1e12` failed-question
penalty, and the earliest checkpoint on ties. The Boolean/contact capability
gaps do not alter the selection score. Total scheduled validation is 13,360
question rollouts over ten passes. Lock all four chosen checkpoints before
opening any confirmation outcomes. Test results must not change checkpoints,
prompts, decoding, supported-target masks or tolerances.

## Preparation gate

Current state: compatible enrichment and embeddings are complete (8,038
train/validation and 500 confirmation). All 224 reused vector hashes are unchanged;
all 8,314 new calls succeeded. There are no remaining context coverage blockers.
The paragraphs below retain the initial enrichment cost
proposal; its approved workload has since completed, as linked above.

Initial qualification found 231 verified enrichment records and 224 exact
embeddings out of 8,038 training/validation questions. The separately authorized
32-request pilot increased compatible notes to 263: **7,775 notes and 7,814
embeddings remain**. Confirmation adds 500 of each. The combined current
requirement is **8,275 notes and 8,314 embeddings**, with no dropped scenarios.

The unchanged enrichment provider is OpenAI `gpt-5.6-sol`; the frozen encoder is
Qwen3-Embedding-0.6B revision
`97b0c614be4d77ee51c0cef4e5f07c00f9eb65b3`. Local answer-model selection does not
replace either. First import any compatible existing caches, then rerun exact
identity and origin audits. The completed pilot cost $1.284679 and exhausted its
32-attempt authorization. The remaining [preparation proposal](P12_enrichment_pilot.md)
requires approval of a new cap: $425 training/validation plus $50 confirmation.
Preparation and study budgets are separate; neither full run has started.

## Evaluation cohorts and conditions

The primary confirmation cohort is fixed in
[confirmation-cohort.json](artifacts/P12/confirmation-cohort.json):
20 unused scenarios per domain per distribution, preserving every question.

| Domain | ID questions | Parameter OOD | Timed-event OOD | Combination OOD | Total |
|---|---:|---:|---:|---:|---:|
| driving | 20 | 20 | 20 | 20 | 80 |
| robotic_arm | 40 | 40 | 20 | 40 | 140 |
| object_pushing_stacking | 40 | 40 | 20 | 40 | 140 |
| tethered_load | 40 | 40 | 20 | 40 | 140 |
| Total | 140 | 140 | 80 | 140 | **500** |

This is 320 simulations, with zero overlap against the conservative historical
inspection inventory. Existing P11 main/appendix results and the later
40-question Sol comparison remain separate historical tables. They are not
pooled with confirmation, and are not used for tuning. The eight validation
diagnostics likewise remain outside headline results.

Report four matched streams: fresh Phi-JEPA numerical/readout, Qwen3-8B thinking
false, Qwen3-8B thinking true, and Llama-3.1-8B-Instruct direct. Keep any Phi prose
generation in an additional separately costed stream; it cannot replace the
numerical predictions for metrics. No paid prose generation is proposed here.
Disclose retained OpenAI enrichment and historical OpenAI answer dependencies.

The three local conditions share the adopted public direct-answer prompt and
the complete original public input/target specification. Use the official
template and immutable pins in
[local_answers_p12.lock.json](../../configs/local_answers_p12.lock.json):

| Setting | Qwen direct | Qwen thinking | Llama direct |
|---|---|---|---|
| Checkpoint/tokenizer revision | `b968826d9c46dd6066d109eabc6255188de91218` | same | `0e9e39f249a16976918f6564b8830bc894c89659` |
| Native thinking control | false | true | absent |
| Temperature / top-p / top-k | 0.7 / 0.8 / 20 | 0.6 / 0.95 / 20 | 0.6 / 0.9 / 50 |
| Output tokens reserved | 1,024 | 2,048 including reasoning | 1,024 |
| Precision / quantization / attention | BF16 / none / SDPA | same | same, measured 29 September |
| Input plus output limit | 32,768 | 32,768 | 32,768 |
| Per-request generation allowance | 120 s | 120 s | 120 s |

The Qwen template hash is
`46b150267cce1a1cfb0543078b45e2267a34b361c3df26afe288636f31f83351`.
The subsequently qualified Llama template hash is
`4193666d58af6747ecfd55b2b1da103aac2bf158cde51cd0d48c1b6f6c561585`.
Its eight validation generations completed, but none produced a valid answer
under the frozen parser. Retain these failures; no prompt/parser change has
been made. Refresh the proposal identity and pin the updated local model lock
before future approval. No implicit thinking switch is passed to Llama.
Official model documentation: [Qwen3-8B](https://huggingface.co/Qwen/Qwen3-8B),
[Llama-3.1-8B-Instruct](https://huggingface.co/meta-llama/Llama-3.1-8B-Instruct).

Keep the current strict answer schema and unchanged typed evaluator. Report
complete-answer accuracy on all 500 questions, including failures/unsupported
targets, individual physical errors and Boolean accuracy, typed output validity,
supported coverage, domain/distribution breakdowns, scenario-group intervals,
input/reasoning/final token counts, EOS/cap/runtime failures, latency and peak
memory. Also report the predefined common supported set of 2,340/2,620 targets.
The common mask comes from public capability declarations, not observed answers.
Raw reasoning is retained only as model output, not verified explanation evidence.

## Measured costs and estimates

The following extrapolations use the eight long-input validation diagnostics
and small training probes; they are not full-run measurements.

| Stage | Measured evidence | Proposed-population estimate |
|---|---|---|
| Full training numerical IO/vectorization | 354.373 s; 0.90 GiB process peak RSS | About 6 min, plus context loading, scaling, pair objects and checkpoint IO |
| Numerical optimizer updates, CPU batch 256 | 0.081–0.146 s/update | 2,003.657 s, about 33.4 min |
| Same updates on CUDA | 0.088–0.141 s/update; under 30 MiB allocated | About 33.7 min; no useful measured advantage |
| Ten full validation sweeps | CUDA public-rollout probes: 0.105–0.196 s for 40/90 intervals | About 53.7 min using 90 intervals/question and GPU timing as an explicitly approximate CPU proxy; CPU full-validation timing remains unmeasured |
| Missing train/validation embeddings | 0.082–0.914 s per sampled existing-note context | About 27.5 GPU min for 7,814; about 2.1 additional min for 500 confirmation questions; excludes API enrichment, loading/tokenization/storage variation |
| Completed embedding follow-up | 8,314 new vectors; 1,193.655 encoding seconds; 1.544 GiB peak allocated | Complete; zero remaining embeddings. This replaces the initial preparation estimate above |
| Qwen direct, 500 questions | 192.008 s for eight long inputs | About 3.45 GPU h, stratified by domain |
| Qwen thinking, 500 questions | 264.233 s for eight long inputs | About 4.67 GPU h, stratified by domain |
| Llama direct, 500 questions | Follow-up: 85.454 s for eight long inputs; 0/8 valid outputs | About 1.58 GPU h stratified by domain; short malformed outputs limit this extrapolation |
| Missing OpenAI enrichment | Later pilot: 32 successes, 123.398 s summed provider latency, $1.284679 | Remaining train/validation: 8.44 h / $293.77 point estimate; confirmation: 0.54 h / $19.31; uncertainty and proposed caps in the separate pilot report |

Updated remaining local work is roughly 1.6–2.5 CPU/wall hours for training and
selection and 9.7 GPU generation hours for the three original frozen direct
baselines. This is roughly 11.3–12.2 sequential hours plus orchestration,
not a measured end-to-end run or convergence estimate. Enrichment and embeddings
have completed and are no longer added to remaining time. The Llama estimate reflects failed,
often short responses; no estimate applies to a changed prompt. Allow up to
4 CPU/wall hours for numerical work and stop if that cap is reached. Plan at
least 8 GiB available host RAM; the 0.90 GiB preparation measurement excludes
simultaneous full pair/context objects. Peak allocated GPU memory was 18.48 GiB
for Qwen and 17.35 GiB for Llama, excluding driver/desktop allocations. Run models
sequentially and retain the shared limits below.

Proposed new stage limits, still disabled:

- Numerical preparation/training/selection: 14,400 seconds wall, divided into
  3,600 seconds per domain; 16 GB artifacts total with checkpoint headroom.
- Frozen-encoder preparation: 3,600 GPU seconds after approved notes exist;
  **completed separately**, using 1,193.655 encoding seconds. Its allowance is
  not renewed or transferred to training/evaluation. No further encoding is planned.
- Local answer evaluation: maximum 1,500 requests, no automatic retry, shared
  64,800 generation GPU seconds (18 h), with the frozen per-request caps above.
  A time budget can stop before all 1,500 finish; never drop missing cases or
  report a partial cohort as a completed study. The Llama follow-up now provides
  a measured estimate, with the malformed-output limitation described above.
- Reserve one wall hour for orchestration/reporting. These stage maxima total
  23 remaining hours if executed sequentially, excluding the separately completed
  enrichment and encoder stages. Profiling already performed is charged separately and its
  weights cannot initialize this study.

The regenerated numerical proposal freezes implementation, selection, origin
audit, complete cache audit and cohort hashes. It also persists each domain's
execution deadline upon future authorized launch and refuses unresolved updates
or interrupted pass validation on resume. Explicit numerical-training approval
must bind the new proposal checksum; evaluation stays disabled. Final evaluation
configuration remains a separate follow-up after answer-interface decisions.
[Resume and preparation commands](../P12_pipeline.md) distinguish currently safe
checks from the disabled future execution commands.
