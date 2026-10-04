# Annotation contract and bounded SPQ01 implementation

The paper contributes simulator-grounded structured/language trajectories,
QA/evidence/reproducible annotation and model/domain/question-type evaluation.
Schema development is iterative creation, enrichment and human revision.
The actual dataset.schema.json 1.0.0 and four-domain release remain source truth.

Predictive wrapping stays simphysqa/0.1.0, preserving source ID/input/reference/
metadata hashes and values. Direct records use simphysqa/0.2.0 with a new stable
question ID and private original source_record plus deterministic derivation.
restore() returns the original predictive source for either family. The direct
adapter asks a new observed-state readout question and derives the exact numerical
answer, units, frame and timestamp from the last observed state. It never relabels
a predictive question. One original predictive question per selected trajectory
and its reference are preserved exactly.

SPQ01 language is a bounded engineering pilot on 16 trajectories, four per domain.
There is no designated development partition, so use train; leave validation,
test_id and OOD partitions unused by this pilot. Seed 20261004 selects an initial
group, then normalized public-feature farthest-point diversity, one earliest
predictive horizon per group. Source physical/control/event timing variation is
recorded in selection.json; no private realized outcome influences selection.
All selected examples have 11 timestamps / a .2-second observation cutoff.
They do not represent an unbiased annotation-quality sample.

## Provider and grounded views

Use configs/simphysqa/annotation_spq01.json and python -m simphysqa.spq01.
The historical identity resolves from configs/model_context_p02b.json and
docs/reviews/artifacts/P02b/provider-ledger.json to callable gpt-5.6-sol.
The prior enrichment_p12_pilot configuration supplies pricing/reservation
precedent. The old bootstrap annotation.json values were an inactive draft,
not evidence of a previously used model/temperature/seed.

The [official model documentation](https://developers.openai.com/api/docs/models/gpt-5.6-sol)
supports Responses and structured outputs with this exact service ID. No distinct
immutable snapshot is listed. Record the exact returned identity on every call;
this run returned gpt-5.6-sol throughout. Do not infer immutable weights from an
alias. Settings retain medium reasoning, 2,048 max output tokens, 120-second
timeout and omitted temperature/seed; SPQ01 specifies default service tier,
store=false, tools=[] and no automatic transport retries or redirects.

Prompt/schema version simphysqa-public-language/1.0.0 and their hashes are retained.
The prompt requests an observed-window summary and a meaningful sentence per
timestamp. This initial compact view focuses on joint_1 angle, car
forward_velocity, block_2 position and load swing_angle respectively, while making
declared controls/schedules and coordinate convention available. Broader
multi-entity/event descriptions remain development work; do not infer goals,
contacts or causal claims. Full-trajectory/private language is not generated.

The provider projection has no reference, future states, reference answer or
verification metadata. Every timestamp ID/time must match observed input exactly.
Claim bindings must resolve to whitelisted public measurement/timestamp/control
fields. Final exported views are revalidated for coverage, binding resolution,
numeric fidelity, observed units/frames, supported scalar direction and prohibited
future/causal/contact wording. These checks are conservative and incomplete
semantic tests: they do not establish all prose entailment or human acceptability.
Each public annotation remains generated_unreviewed. Generic source contexts remain
original data and are never counted as meaningful language.

## Durable execution and budget

Before calls print the resolved non-secret config, request count, input bytes,
token bounds and reservations. Credential access is an explicit file-reference
boundary; neither key nor unrelated environment values enter outputs.
Hard limits: 16 initial requests, 32 total attempts, two attempts/item, $5 total
retained estimated cost, 4,200 seconds, 1,000,000 input tokens / 65,536 output tokens.
Each request is admitted only if charges plus its full reservation fit every limit.
Unknown usage/interruption retains the full reservation. A failure never falls back
to synthetic language. Authorization for a new output directory is not permission
to start another live pilot automatically.

Durable exclusive-created requests, reservations, raw responses, item results,
attempt histories and additive summaries support resume under the same job identity.
Completed item files are not overwritten. A process lock prevents concurrent jobs.
HTTP access/model/pricing failures stop the job explicitly. Other malformed/incomplete
outputs may get one controlled repair; all attempts and failures remain in organizer
provenance. Model identity, record/config/prompt/schema hashes, usage, retries and
repairs accompany output. No mandatory human software approval gate is added.

[Pricing](https://developers.openai.com/api/docs/pricing) on 4 October 2026 is
$4 ordinary input, $.40 cached reads, $5 cache writes and $20 output per million
short-context tokens. Cache writes replace ordinary input pricing for those tokens,
as specified by [prompt caching](https://developers.openai.com/api/docs/guides/prompt-caching).
The adapter derives the documented 1.25 write multiplier unless an explicit
cache_write_per_million is configured. Conservative reservation rates are $10 input
and $40 output; complete request UTF-8 bytes plus 4,096 framing tokens bound input.
Initial full reservations total $3.20905. Reserving all 32 upfront would cost
$6.41810, so repairs are conditional on remaining charged budget.

The live run completed 16 initial requests / 16 total attempts, zero repairs and
zero failures. It reported 31,323 input, 31,275 cache-write and 18,310 output tokens.
Corrected token-based estimated spend is $.522767, not a confirmed invoice charge.
The initial $.491492 estimate omitted implicit writes; immutable raw responses and
initial summaries remain, with additive cache-write-aware reconciliation and final
summary. Pre-call reserves covered the higher rate throughout. No answering-model
experiment was run. Independent human judgments are still absent.

## Separate alternative-source comparison

The primary adapter does not depend on choosing an alternative generator.
configs/simphysqa/annotation_alternative.proposed.json deliberately has model=null.
compare-prepare writes matched physical inputs plus identical prompt/schema hashes
and primary requests; alternative requests stay null until its exact model,
access, comparable settings, subset and separate protocol are pinned.
All 16 development physical inputs are available as a candidate frame, not a frozen
comparison study subset. No live alternative calls or comparison results exist.

Before running that separate study, pin reviewers/overlap, randomized anonymized
source labels/order, budgets, failures in denominators, paired acceptability/criterion
analysis and trajectory-based uncertainty. Keep identity mappings organizer-private.
The main audit's 20/140 allocation does not power this comparison.

## Remaining QA construction

| Family | SPQ01 status | Required next work |
| --- | --- | --- |
| Direct | 16 deterministic observed readouts, automatically verified | Human assess wording/evidence; broaden entity/channel coverage |
| Predictive | 16 original questions/references exact; public language generated | Human assess validity/leakage and enrich representative views |
| Counterfactual | Pending; none fabricated | Matched interventions or verified re-simulation; paired initial state, seed, control and evidence manifests |
| Explanation | Pending; none fabricated | Claim-level support; causal assertions need intervention/mechanistic verification beyond temporal association |
| Clarification | Pending; none fabricated | Genuine missing public information, demonstrable underdetermination and justified requested clarification |

Release language enrichment and calibration/revision remain pending. Source
simulations were not regenerated. Human review is research, not a generation gate.
