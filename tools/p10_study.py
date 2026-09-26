"""Prepare an executable, explicitly unauthorized larger-study proposal."""
import math
from copy import deepcopy
from p10_common import *


def study_plan(run):
    inventory=load(run.root/'sealed_inventory.json')['domains']; seeds=(11,17,29)
    timings={}
    for short in ('coconut','codi'):
        fit=load(run.root/'custom'/f'{short}_broad/fit.json'); timings[short]=fit['seconds']/fit['updates']
    # Training contains all 6,702 question contexts. Two passes are a specified
    # exposure, not a convergence promise. Other domains can have ~2x token
    # length; use 4x measured update time as a conservative attention allowance.
    total_questions=sum(v['train']['questions'] for v in inventory.values())
    estimated_training_seconds=2*total_questions*len(seeds)*sum(timings.values())
    gpu_hours=math.ceil((estimated_training_seconds*4+12*3600)/3600/10)*10
    # CPU accounting includes independent numerical fits and the observed
    # forecast/evaluation stages. Extrapolate by updates and question counts;
    # use a 4x allowance for other layouts/horizons and data preparation.
    iterative=[m for m in run.methods() if m!='fixed_projection_lr']
    numerical_cpu=sum(load(run.root/'numerical'/m/'fit.json')['seconds']/load(run.root/'numerical'/m/'fit.json')['updates']*20000 for m in iterative)*len(inventory)*len(seeds)
    future_questions=sum(v['train']['questions']+math.ceil(32*len(v['calibration']['sample_ids'])/20) for v in inventory.values())*len(seeds)
    operations=run.b.read()['operations']
    # Reporting refreshes reuse cached diagnostics; do not inflate a future
    # workload estimate by summing repeated executions of the same stage.
    observed_evaluation=sum(max((o['seconds'] for o in operations if o['name']==name and o.get('exit_code')==0),default=0.) for name in ('forecast','evaluate'))
    evaluation_cpu=observed_evaluation*future_questions/len(run.rows())
    cpu_hours=max(8,math.ceil((numerical_cpu+evaluation_cpu)*4/3600/4)*4)
    artifact_gb=150
    selection_questions=sum(math.ceil(32*len(v['calibration']['sample_ids'])/20) for v in inventory.values())
    calibration_questions=sum(len(v['calibration']['sample_ids']) for v in inventory.values())
    sealed_questions=sum(len(v[p]['sample_ids']) for v in inventory.values() for p in ('test_id','ood_parameter_extrapolation','ood_unseen_combination','ood_timed_event'))
    enrichment_requests=total_questions+selection_questions+calibration_questions+sealed_questions
    answer_requests=(selection_questions+sealed_questions)*(6*len(seeds)+1)  # shared public-only cache
    observed=[r for r in run.b.read()['provider'] if r.get('usage_known')]
    mean_input=sum(r['charged_input'] for r in observed)/len(observed) if observed else None
    mean_output=sum(r['charged_output'] for r in observed)/len(observed) if observed else None
    provider_caps={'provider_attempts':32000,'provider_input_tokens':600000000,'provider_output_tokens':25000000,'provider_usd':3500}
    if observed:
        # Explicit allowance for longer domains, not a claim about measured
        # enrichment tokens: up to 32,768 input and configured 2,048 output per
        # new enrichment, plus 2x measured answer usage across planned requests.
        inp=math.ceil((2*mean_input*answer_requests+32768*enrichment_requests)/1000000)*1000000
        out=math.ceil((2*mean_output*answer_requests+2048*enrichment_requests)/1000000)*1000000
        provider_caps['provider_input_tokens']=max(provider_caps['provider_input_tokens'],inp)
        provider_caps['provider_output_tokens']=max(provider_caps['provider_output_tokens'],out)
        provider_caps['provider_usd']=math.ceil((provider_caps['provider_input_tokens']*5+provider_caps['provider_output_tokens']*20)/1000000/100)*100
    caps={'gpu_seconds':gpu_hours*3600,'cpu_seconds':cpu_hours*3600,'artifact_bytes':artifact_gb*1000000000,**provider_caps}
    shared=run.native/'full-study-proposed'; directory=ROOT/'configs/proposed_full_study'; directory.mkdir(exist_ok=True)
    profiles=[]; prior_roots=[str(run.root),str(run.old)]
    for domain,partitions in inventory.items():
        nq=partitions['train']['questions']; ns=partitions['train']['scenarios']
        for seed in seeds:
            name=f'{domain}-seed{seed}'; c=deepcopy(run.c)
            c.update(version='p10-proposed-full-study-v1',run_root=str(shared/name),previous_run=str(run.root),domain=domain,seed=seed,selection_seed=11,
                reuse_selection=False,training_scenarios=ns,validation_scenarios=32,questions_per_scenario='all',mixed_horizon_equal_pair_sampling=True,
                numerical_updates=20000,checkpoint_milestones=[5000,10000,20000],numerical_job_seconds=2400,
                custom_broad_updates=2*nq,custom_broad_milestones=[nq,2*nq],custom_selection_questions=4,
                custom_selection='minimum mean teacher-forced validation objective on first four fixed selection questions after one and two complete training passes',
                custom_job_seconds={**c['custom_job_seconds'],'coconut_broad':math.ceil(timings['coconut']*2*nq*4+300),'codi_broad':math.ceil(timings['codi']*2*nq*4+300)},
                shared_budget_root=str(shared),shared_context_cache=str(shared/'shared-context-cache'),shared_embedding_cache=str(shared/'shared-embedding-cache'),
                shared_answer_cache=str(shared/'shared-answer-cache'),
                shared_export_directory='docs/reviews/artifacts/FullStudy',export_directory=f'docs/reviews/artifacts/FullStudy/{name}',
                context_source_roots=prior_roots.copy(),full_study=True,execution_authorized=False,evaluation_authorized=False,
                assessment_judge_enabled=False,clarification_enabled=False,provider_stage_seconds=72000,caps=caps)
            file=directory/f'{name}.json'; save(file,c); profiles.append(str(file.relative_to(ROOT))); prior_roots.append(c['run_root'])
    work=[]
    for domain,parts in inventory.items():
        work.append({'domain':domain,'training_scenarios':parts['train']['scenarios'],'training_questions':parts['train']['questions'],
            'selection_scenarios':32,'calibration_scenarios':20,'sealed_scenarios_each_partition':20,
            'prepared_calibration_questions':len(parts['calibration']['sample_ids']),
            'prepared_sealed_questions':sum(len(parts[p]['sample_ids']) for p in ('test_id','ood_parameter_extrapolation','ood_unseen_combination','ood_timed_event'))})
    plan={'status':'proposal_not_authorized','seeds':seeds,'profiles':profiles,'workload':work,'measured_custom_seconds_per_update':timings,
        'provider_projection':{'new_answer_usage_records':len(observed),'mean_input_tokens':mean_input,'mean_output_tokens':mean_output,
            'enrichment_requests_before_cache_reuse':enrichment_requests,'answer_requests_with_shared_public_only_cache':answer_requests,
            'selection_questions':selection_questions,'calibration_questions':calibration_questions,'sealed_questions':sealed_questions,
            'allowance_policy':'2x measured answer usage, plus assumed 32768 input/2048 output per enrichment. Other-domain usage is not measured; caps can stop an incomplete study.'},
        'cpu_projection':{'numerical_training_seconds':numerical_cpu,'forecast_evaluation_seconds':evaluation_cpu,
            'qualification_forecast_evaluation_seconds':observed_evaluation,'future_training_selection_questions':future_questions,
            'policy':'Measured per-update and per-question extrapolation with 4x allowance; not a measured other-domain runtime.'},
        'naive_same_length_training_gpu_hours':estimated_training_seconds/3600,'conservative_shared_caps':caps,
        'extrapolation':'4x custom training time allowance for longer contexts plus 12 GPU h for generation/encoding/overhead; not a measured other-domain runtime',
        'scientific_limits':'Two passes are an exposure limit, not proof of convergence; no guarantee that additional updates solve generation/forecast failures.'}
    save(run.root/'report/next_study_plan.json',plan)
    save(directory/'aggregation.json',{'profiles':profiles,'roles':['test_id','ood_parameter_extrapolation','ood_unseen_combination','ood_timed_event']})
    text=f'''# Next executable study plan — not authorized for execution

The P10 qualification is separate from this proposed workload. **Do not launch
these profiles under the P10 allowance.** Each generated profile has
`execution_authorized:false` and `evaluation_authorized:false`; the supervisor
refuses execution until a separately approved configuration enables it.

## Workload and measured basis

Use all {total_questions:,} training question contexts across the four domains,
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
{timings['coconut']:.3f} s; CODI {timings['codi']:.3f} s on the RTX 5090 and roughly
11.8k-token qualification inputs. A same-length extrapolation for this training
work is {estimated_training_seconds/3600:.1f} GPU hours. Other-domain contexts in
the earlier P06 sample reached 22,323 tokens, so this is not a reliable upper bound.
The proposed conservative ceiling is **{gpu_hours} GPU hours, {cpu_hours} CPU hours,
{artifact_gb} GB, USD {provider_caps['provider_usd']:,}, 32,000 provider attempts, {provider_caps['provider_input_tokens']/1e6:g}M input and {provider_caps['provider_output_tokens']/1e6:g}M output
tokens**, shared by every profile. It uses a 4x attention-time allowance plus
12 GPU hours for encoding/generation/overhead. Actual other-domain runtime and
memory must be checked before consuming that allocation. Provider token/cost
limits are reservations, not a spending target; reuse public context caches across
seeds and never rerun unchanged requests. Identical public-only answer requests
also reuse a shared content-addressed output cache across seeds. The exact workload/configs are in
`artifacts/P10/report/next_study_plan.json` and `configs/proposed_full_study/`.

The CPU estimate uses measured numerical-fit cost ({numerical_cpu/3600:.1f} hours
at the proposed update count) plus forecast/evaluation cost extrapolated by
question count ({evaluation_cpu/3600:.1f} hours), then a 4x allowance for different
layouts, horizons and preparation. Identity-matched physical diagnostics are
reused when only answer-generation results have changed. These extrapolations
remain resource estimates, not proof that every other-domain case fits memory.

API waiting is additional wall-clock time, not GPU execution. A conservative
question-count estimate is {enrichment_requests:,} unique enrichment requests plus
{answer_requests:,} selected/sealed answer requests across three seeds with shared
public-only cache reuse, below the 32,000-attempt ceiling. No retries or correctness-based regeneration are
planned. Shared caches prevent repeating enrichment/embedding work across seeds.
Each provider stage has a separate 20-hour wall limit; its token/call/spend and
CPU caps remain enforced. This is not an invitation to consume unused budget.

The provider estimate uses {len(observed)} known-usage qualification records; mean
answer input/output tokens are {mean_input}/{mean_output}. The ceiling allows 2x
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
'''
    (ROOT/'docs/reviews/P10_next_full_study.md').write_text(text,encoding='utf-8')
    return plan
