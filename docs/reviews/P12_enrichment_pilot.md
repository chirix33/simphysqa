# P12 separately authorized enrichment pilot — 28 September 2026

Completed the newly authorized **USD 5 / 32 attempted requests** pilot. All 32
unique requests succeeded, with **zero retries, zero failed attempts and zero
confirmation requests**. The attempt cap is exhausted; the remaining dollar
allowance does not authorize another request. No remaining full workload ran.

The checkout remains `main` at `248575fd500947edd325836e636aebe41f9f65d0`, with
uncommitted P12 work. The actual pilot execution source snapshot is
`8299849d4232e451f4f707e9c8daa2dbd2cd4537e93fd20d6749fadf2df5b16e`, preserved in
[execution.json](artifacts/P12_enrichment/execution.json) and its content-addressed
source archive. Subsequent resume/budget hardening has a separate proposal
identity; it is not attributed to the completed pilot. Native artifacts are at
`/home/aashraf/phi-jepa/p12-enrichment-pilot-01`; the repository export is
`docs/reviews/artifacts/P12_enrichment/`.

## Selection and unchanged provider

The cache-first public inventory reproduced **231 compatible existing records**,
**7,807 missing training/validation records**, and **500 missing confirmation
records** before dispatch. Compatibility checks cover the full original public
request, prompt/schema, provider settings, returned model, output digest and note
validation. The historical one-attempt transport variant is compatible with the
same scientific request; no model/prompt variant was substituted.

The frozen pilot selected four missing records per domain per split (training
and validation): one from each input-length stratum, including the longest.
There are 32 distinct scenarios, with eight requests per domain. Selection used
public payload length only. Confirmation inputs were inventoried for costs but
excluded from selection, prompt development and generation.

The original `gpt-5.6-sol` Responses request, medium reasoning, 2,048 output-token
cap, enrichment asset/schema and public observation cutoff were preserved.
This service exposes no immutable model snapshot; the returned model identifier
is recorded for every response. No future states, reference answers or private
explanations were supplied. Direct Qwen/Llama inputs remain original public
problems and requested target specifications, without these notes.

## Measured pilot cost

| Measurement | Result |
|---|---:|
| Attempted / successful unique requests | 32 / 32 |
| Failures / retries | 0 / 0 |
| Input tokens | 228,743 |
| Output tokens, including billed reasoning | 7,053 |
| Cached-read input tokens | 0 |
| Cache-write input tokens (included in input total) | 228,647 |
| Usage-based cost | **USD 1.284679** |
| Summed provider latency | 123.398 seconds |
| Worker wall time | 125.932 seconds |
| Mean / median / p95 request latency | 3.856 / 3.587 / 5.705 seconds |

Current official prices were verified before dispatch: standard short-context
input $4, cached input $0.40, cache writes $5, and output $20 per million tokens.
The reservation uses the higher Fast rates, $10 input/cache-write and $40 output,
full serialized UTF-8 payload bytes plus 4,096 as an input-token upper bound,
and the complete 2,048-token output allowance. Per-request reservations ranged
from $0.30519 to $0.47936. See the official
[model pricing](https://developers.openai.com/api/docs/models/gpt-5.6-sol),
[pricing table](https://developers.openai.com/api/docs/pricing) and
[cache accounting](https://developers.openai.com/api/docs/guides/prompt-caching).

Every response supplied known usage and cache-write detail, so the usage-based
cost is exact under these verified rates (not an invoice reconciliation).
The original provider event/cache `cost_usd` omits cache-write charges and is
preserved unchanged. **The new [spend ledger](artifacts/P12_enrichment/spend-ledger.json)
is authoritative for this pilot.** Missing usage would retain the full reservation;
missing cache-write detail would retain the conservative input-write charge.
Reservations are persisted before dispatch. Raw responses, failures, usage and
successful content-hashed caches are written immediately, with one worker lock.

## Remaining coverage and concrete proposal

There are now **263 compatible train/validation enrichment records**, leaving:

| Domain | Missing train | Missing validation | Missing confirmation |
|---|---:|---:|---:|
| robotic_arm | 1,909 | 375 | 140 |
| driving | 687 | 135 | 80 |
| object_pushing_stacking | 1,947 | 387 | 140 |
| tethered_load | 1,948 | 387 | 140 |
| Total | **6,491** | **1,284** | **500** |

Thus **8,275 unique enrichment requests remain**, of which 7,775 are training/
validation. The pilot did not generate embeddings: the previous exact embedding
gaps remain 7,814 training/validation plus 500 confirmation. Existing notes and
embeddings remain reusable only when their full identities match.

| Remaining scope | Requests | Point cost | Cost sensitivity before retries | Point sequential time | Time sensitivity with retry allowance | Proposed hard cap / attempts |
|---|---:|---:|---:|---:|---:|---:|
| Training/validation | 7,775 | $293.77 | $202.20–$353.63 | 8.44 h | 6.33–16.98 h | **$425 / 8,942** |
| Confirmation public inputs | 500 | $19.31 | $13.29–$23.21 | 0.54 h | 0.40–1.08 h | **$50 / 575** |
| Total | 8,275 | $313.08 | $215.48–$376.84 | 8.97 h | 6.73–18.06 h | **$475 / 9,517** |

These are sensitivity estimates, not confidence intervals. They use domain,
split and payload-length strata, token/byte ratios, observed output lengths and
latency. There is only one pilot observation per domain/split/length cell.
Confirmation estimates transfer training/validation observations without
generating confirmation notes. Assumptions: standard service, no future cached-read
discount, input-token uncertainty ±15%, output sensitivity from 0.75 times the
cell mean to 1.25 times the observed domain maximum, and at least 15% retry
headroom. Zero failures in 32 requests still permits roughly a 9.4% rule-of-three
failure-rate upper bound. Fast service or distribution shifts may exhaust caps
before completion; the runner must stop rather than exceed them.

The [machine-readable proposal](artifacts/P12_enrichment/proposed-full-enrichment.json)
is **disabled**, with no authorization and no authorized scopes. It proposes a
new native directory `/home/aashraf/phi-jepa/p12-enrichment-full-01`, a shared
$475 maximum plus the separate $425/$50 scope limits, 9,517 total attempts,
20 hours of cumulative provider-call allowance and 2 GB artifacts. These are
additional caps; the already spent $1.284679 is separately charged profiling.
The maximum combined spend, if the new cap is approved, is $476.284679.

Both scopes require explicit approval. Confirmation enrichment uses only frozen
public requests, stays in separate scope records and cannot affect training,
checkpoint selection, prompts or thresholds. No Phi prose generation is funded.
The source/config/inventory are hashed, and pricing verification must be current
within 24 hours of each dispatch. A changed price requires a reviewed configuration,
not silently continued spending. Interrupted requests with unresolved reservations
stop for reconciliation. Completed successes and terminal failures are not
automatically repeated; safe resume preserves all previous charges and outputs.

## Validation and outstanding gates

The expanded offline suite passed **54 tests**; see
[test log](artifacts/P12_enrichment/tests-final.log). Coverage includes money and
attempt caps, per-scope/global accounting, unknown usage, raw incomplete outputs,
authorization before credential access, adjacent-pair gradients, full augmented
feedback, cache identities, answer parsing and failure accounting. The completed
pilot resume returned `pilot_closed`, 32 attempts and **zero additional requests**.

Qwen direct/thinking and numerical diagnostics remain as reported in
[P12 completion](P12_completion.md). Llama remains `implemented_pending_validation`
until the pinned gated checkpoint is accessible. Full training remains blocked
on complete, verified context preparation. No full study or confirmation outcome
evaluation has started. The [study plan](P12_full_run_plan.md) and
[enrichment resume commands](../P12_enrichment_pipeline.md) are separate: approval
of enrichment does not implicitly start training or the remaining study.

Required next decision: approve the proposed **additional $475 cap** and both
listed scopes, or authorize training/validation only under a revised **$425 cap**.
