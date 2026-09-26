# Next executable study plan — not authorized for execution

The P10 qualification is separate from this proposed workload. **Do not launch
these profiles under the P10 allowance.** Each generated profile has
`execution_authorized:false` and `evaluation_authorized:false`; the supervisor
refuses execution until a separately approved configuration enables it.

## Workload and measured basis

Use all 6,702 training question contexts across the four domains,
32 checkpoint-selection scenarios per domain, 20 disjoint calibration scenarios,
and 20 scenarios from each sealed ID/OOD partition. Use fixed selection seed 11
and independent model seeds 11, 17 and 29. All methods see the same selected
questions/partitions. Forecast all available intervals; every question-conditioned
pair has equal loss weight. Fixed-size shuffled pair cycles handle numerical ODEs;
length-proportional sampling of complete chronological trajectories keeps the
RNN's expected per-transition weight equal without changing its MSE.

Five iterative numerical methods receive up to 20,000 updates each, with
checkpoints at 5,000/10,000/20,000; LR performs its independent least-squares fit.
Each custom model receives two full passes through its domain's training questions,
with a fresh initialization and selection after each pass. Shared CODI backbone,
fixed teacher projection, alignment targets and latent paths remain unchanged.
Do not repeat the P10 factorials or repeated-example diagnostics in this study.

Measured broader fitting time per update (including milestone overhead): Coconut
6.571 s; CODI 13.080 s on the RTX 5090 and roughly
11.8k-token qualification inputs. A same-length extrapolation for this training
work is 219.5 GPU hours. Other-domain contexts in
the earlier P06 sample reached 22,323 tokens, so this is not a reliable upper bound.
The proposed conservative ceiling is **900 GPU hours, 52 CPU hours,
150 GB, USD 3,900, 32,000 provider attempts, 657M input and 28M output
tokens**, shared by every profile. It uses a 4x attention-time allowance plus
12 GPU hours for encoding/generation/overhead. Actual other-domain runtime and
memory must be checked before consuming that allocation. Provider token/cost
limits are reservations, not a spending target; reuse public context caches across
seeds and never rerun unchanged requests. Identical public-only answer requests
also reuse a shared content-addressed output cache across seeds. The exact workload/configs are in
`artifacts/P10/report/next_study_plan.json` and `configs/proposed_full_study/`.

The CPU estimate uses measured numerical-fit cost (4.9 hours
at the proposed update count) plus forecast/evaluation cost extrapolated by
question count (7.9 hours), then a 4x allowance for different
layouts, horizons and preparation. Identity-matched physical diagnostics are
reused when only answer-generation results have changed. These extrapolations
remain resource estimates, not proof that every other-domain case fits memory.

API waiting is additional wall-clock time, not GPU execution. A conservative
question-count estimate is 7,566 unique enrichment requests plus
13,756 selected/sealed answer requests across three seeds with shared
public-only cache reuse, below the 32,000-attempt ceiling. No retries or correctness-based regeneration are
planned. Shared caches prevent repeating enrichment/embedding work across seeds.
Each provider stage has a separate 20-hour wall limit; its token/call/spend and
CPU caps remain enforced. This is not an invitation to consume unused budget.

The provider estimate uses 49 known-usage qualification records; mean
answer input/output tokens are 14837.0/441.9387755102041. The ceiling allows 2x
that measured answer usage and assumes 32,768 input / 2,048 output tokens per new
enrichment for budgeting. Those enrichment allowances and other-domain usage
are not empirical measurements. Cache reuse can reduce spending; token/call/cost
caps can still stop an incomplete study. No higher P10 allowance is created.
Unknown-usage reservations remain charged in the qualification ledger and are
not treated as zero usage. Before activating a later study, recheck the provider
rates against the recorded 25 September 2026 pricing basis and update the charge
policy if necessary; an old rate estimate is not a future billing guarantee.

This is a costly study on one workstation. Current qualification failures do not
justify claiming that two passes or this budget will yield adequate performance.
The recommended execution gate is to review the measured P10 results first, then
approve a staged allocation if the same-objective study remains scientifically
useful. No loss/head/layout change is silently bundled into this proposal.

## Commands after separate execution approval

The profiles share one resource ledger and global worker lock. After approval,
make an authorized copy of each proposed JSON, keeping its shared budget/caches
and fixed scenario policy; enable the two authorization fields. Run one at a time:

```bash
python tools/run_pipeline.py --config AUTHORIZED_DOMAIN_SEED.json study
python tools/run_pipeline.py --config AUTHORIZED_DOMAIN_SEED.json public_cohort calibration--enrich
python tools/run_pipeline.py --config AUTHORIZED_DOMAIN_SEED.json public_cohort calibration--encode
python tools/run_pipeline.py --config AUTHORIZED_DOMAIN_SEED.json public_cohort calibration--forecast
python tools/run_pipeline.py --config AUTHORIZED_DOMAIN_SEED.json assessment_cohort calibration
python tools/run_pipeline.py --config AUTHORIZED_DOMAIN_SEED.json calibrate
```

For each of `test_id`, `ood_parameter_extrapolation`, `ood_unseen_combination` and
`ood_timed_event`, use its literal name in place of ROLE:

```bash
python tools/run_pipeline.py --config AUTHORIZED_DOMAIN_SEED.json public_cohort ROLE--enrich
python tools/run_pipeline.py --config AUTHORIZED_DOMAIN_SEED.json public_cohort ROLE--encode
python tools/run_pipeline.py --config AUTHORIZED_DOMAIN_SEED.json public_cohort ROLE--forecast
python tools/run_pipeline.py --config AUTHORIZED_DOMAIN_SEED.json public_cohort ROLE--answers
python tools/run_pipeline.py --config AUTHORIZED_DOMAIN_SEED.json custom_cohort ROLE--coconut
python tools/run_pipeline.py --config AUTHORIZED_DOMAIN_SEED.json custom_cohort ROLE--codi
python tools/run_pipeline.py --config AUTHORIZED_DOMAIN_SEED.json assessment_cohort ROLE
python tools/run_pipeline.py --config AUTHORIZED_DOMAIN_SEED.json benchmark_cohort ROLE
python tools/run_pipeline.py --config AUTHORIZED_DOMAIN_SEED.json export --refresh
```

The evaluator alone opens outcomes. Keep raw per-target/physical records, failed
generations and unsupported contact targets. Aggregate matched questions across
methods and scenario-clustered intervals across seeds; do not tune on sealed
outcomes. Human-reviewed clarification is a separately enabled and priced condition.

After every declared cohort has been evaluated, update the profile paths in
`configs/proposed_full_study/aggregation.json` to the approved configuration
copies and run:

```bash
python tools/run_pipeline.py --config AUTHORIZED_DOMAIN_SEED.json aggregate aggregation
python tools/run_pipeline.py --config AUTHORIZED_DOMAIN_SEED.json export --refresh
```

This writes `report/full_study_aggregate.json`, with method/condition/partition
summaries, numeric denominators, failure categories and scenario-clustered
intervals across seeds. It verifies common questions across methods/seeds and
refuses a pooled summary if any declared cohort/configuration is missing.
Missing individual generations stay explicit failures through `benchmark_cohort`.

## Remaining gates and decisions

1. **Execution budget:** the configurations are concrete and guarded, but this
   larger allowance is not approved. Recommendation: review P10 validation and
   strict-generation evidence before committing to the full cost. A smaller
   domain/seed prefix uses the same commands/ledger and must be labeled partial.
2. **Assessment contract evidence:** the release does not provide the required
   immutable typed public constraints. Keep assessment partial and calibration
   ineligible until a reviewed evidence/contract policy exists. Enabling more V1
   calls alone cannot fix this. `assessment_judge_enabled` stays false; enable it
   only when eligible assessment work is approved. Calibration never substitutes
   answer thresholds for constraints or tunes on test data.
3. **Contact-dependent outputs:** stable-stack/support-lost require sufficient
   future contact/support evidence or a separately approved mechanism. Current
   state/layout does not supply it. Recommendation: retain explicit unsupported
   values and complete-answer denominators. An expanded state/head/mechanism
   requires a separate scientific decision.

Larger mixed-horizon sampling, cohort paths and budget guards have software tests;
these tests are not empirical four-domain learning evidence. Layout/overlength
failures remain failures and must be resolved within the accepted contract or
reported as a concrete representation decision. Source/checkpoint identities,
cap stops and partial execution remain visible; no study is called complete merely
because its budget expires.
