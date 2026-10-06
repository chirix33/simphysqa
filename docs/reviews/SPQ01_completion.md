# SPQ01 completion — 4 October 2026

Branch **simphysqa-naacl**, worktree C:/Users/aashraf/.codex/worktrees/simphysqa/phi-jepa.
Parent/accepted SPQ00: 129155be63a44c8c3c31af1d69049ef0769548ac.
Original main/base remains 7dd4a64e90cfb18be743503ac8345cabf2f6e28b, clean.
The delivery commit is the commit containing this report; its full hash is recorded
in the external delivery manifest and final handoff. No further cleanup, main/history
rewrite, simulator regeneration, model download or answering-model experiment.

## Delivered behavior and evidence

- Actual release: **11,105 predictive QA / 6,340 trajectory groups**, across train,
  validation, test_id and three OOD partitions. Versioned lightweight inventory
  records domain/split/group/trajectory/family/actual context status and source,
  input/reference hashes. All source contexts are generic, not completed language.
- **16 admitted train trajectories, four/domain**, seed 20261004: earliest original
  predictive horizon/group; seeded first group, then normalized public-feature
  farthest-point diversity. No dedicated development partition exists. Selection
  uses public physical/control/event timing variation, never private outcomes.
  All selected windows have **11 observed states / .2-second cutoff**; length
  variation is unavailable. This is engineering development, not unbiased estimation.
- **16 live human-unreviewed annotations**: 16 observed-window summaries and
  **176 timestamp descriptions**. Initial compact views describe one focal quantity
  per domain; broader multi-entity/event language remains development work.
- **16 new deterministic direct QA** with stable IDs and exact observed values,
  units, frames, timestamps and evidence; **16 existing predictive QA/references
  unchanged**. Private source_record/derivation preserve original IDs/provenance.
- **32 development audit packets**, HTML/JSON, fixed draft rubric and separate blank
  R1/R2/R3 forms. Organizer-private identity/accounting; reviewer-facing packets
  omit generator identity. Blank imports collect **zero** judgments.
- Persist **20 inspected groups** (SPQ00 four + SPQ01 sixteen) as default fresh
  sampling exclusions. Group-then-question sampling targets trajectory-balanced
  estimates, not uniform release-wide QA-record estimates. No definitive formal
  sample is frozen/exported. Development pairs share groups intentionally;
  calibration/formal must remain group-disjoint with one record/group.
- Matched-input annotation-source interface prepared; exact alternative model,
  subset, comparison protocol/reviewers and live comparison remain pending.
- **27 offline behavioral tests passed**. Saved-output verification checked all
  16 source identities/provenance, all 16 direct answers, all predictive references,
  all 32 final public views and blank forms. Resume made **zero new calls** and
  preserved completed item hashes. Synthetic test transports/ratings are not results.

## Exact generator and accounting

Historical configs/model_context_p02b.json and P02b/provider-ledger.json resolve
callable **gpt-5.6-sol**; all 16 responses returned that exact identity. Medium
reasoning, max_output_tokens=2048, timeout=120 s, omitted temperature/seed,
default service tier, store=false, tools=[]; Responses strict structured output,
no redirects/hidden retries. Prompt/schema simphysqa-public-language/1.0.0 and
hashes, source/config hashes, all reservations/raw responses/items and failure
histories are durable. No distinct immutable snapshot is documented; do not infer
immutable weights from this service ID. [Official model documentation](https://developers.openai.com/api/docs/models/gpt-5.6-sol).

Hard caps: **16 initial / 32 total attempts / two attempts per item / $5**,
4,200 s, 1,000,000 input / 65,536 output tokens. Before execution the adapter prints
complete non-secret configuration and size/reservation summaries. Input bytes
7,643–8,069, total 124,297; initial input-token upper bound 189,833.
Initial full reservations **$3.20905**. All-32 reservations **$6.41810**, so repairs
depend on remaining charged budget; unknown usage retains reservations.

Actual: **16 initial / 16 total attempts, zero repairs, zero failed items**.
Tokens: input 31, 323, cache-write 31,275, output 18,310. Corrected token-based
estimated spend **$0.522767**, not a reconciled invoice. Initial $0.491492 omitted
implicit cache writes. Immutable original responses/items/summary remain; additive
reconciliation and summary 002 correct reporting without rerunning outputs.
Pre-call reserves covered write pricing. Final code/tests account separately for
ordinary input ($4/M), cached reads ($.40/M), writes ($5/M) and output ($20/M);
reservation rates are $10/M input and $40/M output.
[Pricing](https://developers.openai.com/api/docs/pricing),
[cache accounting](https://developers.openai.com/api/docs/guides/prompt-caching).

The provider projection contains observed fields and declared controls, without
references/future outcomes. Exported views are checked again for timestamp IDs,
coverage, public bindings, numeric fidelity, exact observed units/frames and
supported scalar direction. These are incomplete semantic checks, not human
acceptability or proof of all prose entailment. Status remains generated_unreviewed.

## Audit-method reconciliation

Supplied archive and all five original members preserved byte-for-byte with hashes
under docs/references/spq01_audit. Supplied Python/SciPy reproduction traces to
kappaSize 1.2 PowerBinary: alpha=.20 two-sided, power=.80, p=.90 expected
acceptability, kappa .60 vs .80, three raters. N=129.03095760509072 (minimum 130);
approximate power at 140=.8237409136. Preserve **20 calibration / 140 formal**;
calibration is excluded from formal analysis.

The explicit fixed-prevalence one-parameter score statistic matches the supplied
local df=1 noncentrality. It is not four-cell df=3 Pearson or estimated-prevalence
Fleiss Wald testing. Fleiss may remain descriptive; it does not implement the
powered conditional test. [Full method/estimator distinctions](../simphysqa/audit.md).

Seed 20261004 / NumPy PCG64, 200,000 simulations per hypothesis:

| Quantity | Estimate | 95% Monte Carlo Wilson interval | Exact enumeration |
| --- | ---: | --- | ---: |
| Type-I error | .199855 | [.198108204,.201613326] | .198617376 |
| Power | .879060 | [.877623731,.880481708] | .879659735 |

Power is **5.532 percentage points above** the approximation: report the material
discrepancy, keep allocation. Sparse expected cells include 1.512 under null / .756
under alternative. The check fixes prevalence and assumes independent records/
exchangeable reviewers. It does not validate nuisance prevalence, reviewer
heterogeneity, missingness, weighting or confidence-interval choices. Monte Carlo
intervals are simulation uncertainty, not audit confidence intervals.
No human acceptance, agreement or annotation-quality result exists.

## Inspectable outputs

External artifact root: C:/Users/aashraf/.codex/visualizations/2026/10/04/01a10902-e2dc-7390-827b-382d2692622c/spq01. Each artifact directory has a versioned hash manifest.

| Artifact | Link |
| --- | --- |
| Actual release inventory/counts | [summary](C:/Users/aashraf/.codex/visualizations/2026/10/04/01a10902-e2dc-7390-827b-382d2692622c/spq01/inventory-final/summary.json), [record frame](C:/Users/aashraf/.codex/visualizations/2026/10/04/01a10902-e2dc-7390-827b-382d2692622c/spq01/inventory-final/records.jsonl), [source hashes](C:/Users/aashraf/.codex/visualizations/2026/10/04/01a10902-e2dc-7390-827b-382d2692622c/spq01/inventory-final/source-files.json) |
| Development selection/variation/exclusions | [selection](C:/Users/aashraf/.codex/visualizations/2026/10/04/01a10902-e2dc-7390-827b-382d2692622c/spq01/selection/selection.json), [original sources](C:/Users/aashraf/.codex/visualizations/2026/10/04/01a10902-e2dc-7390-827b-382d2692622c/spq01/selection/predictive-records.jsonl) |
| Resolved config/no-call budget | [final dry-run](C:/Users/aashraf/.codex/visualizations/2026/10/04/01a10902-e2dc-7390-827b-382d2692622c/spq01/dry-run-final/dry-run.json) |
| All requests/attempts/responses/items | [job manifest](C:/Users/aashraf/.codex/visualizations/2026/10/04/01a10902-e2dc-7390-827b-382d2692622c/spq01/annotation-job/manifest.json); requests, attempts, attempt-requests, responses, items, summaries |
| Corrected accounting | [reconciliation](C:/Users/aashraf/.codex/visualizations/2026/10/04/01a10902-e2dc-7390-827b-382d2692622c/spq01/verification/accounting-reconciliation.json), [summary002](C:/Users/aashraf/.codex/visualizations/2026/10/04/01a10902-e2dc-7390-827b-382d2692622c/spq01/annotation-job/summaries/002.json) |
| 32 QA / public exports | [QA records](C:/Users/aashraf/.codex/visualizations/2026/10/04/01a10902-e2dc-7390-827b-382d2692622c/spq01/development/qa-records.jsonl), [public views](C:/Users/aashraf/.codex/visualizations/2026/10/04/01a10902-e2dc-7390-827b-382d2692622c/spq01/development/public-qa.json) |
| Audit packets/organizer keys/blank forms | [packet manifest](C:/Users/aashraf/.codex/visualizations/2026/10/04/01a10902-e2dc-7390-827b-382d2692622c/spq01/development/audit-development/manifest.json); packets, organizer-private, forms/R1.csv, R2.csv, R3.csv |
| Saved checks | [verification](C:/Users/aashraf/.codex/visualizations/2026/10/04/01a10902-e2dc-7390-827b-382d2692622c/spq01/verification/verification.json), [example index](C:/Users/aashraf/.codex/visualizations/2026/10/04/01a10902-e2dc-7390-827b-382d2692622c/spq01/verification/examples.json) |
| Audit power reproduction/simulation | [reconciliation](C:/Users/aashraf/.codex/visualizations/2026/10/04/01a10902-e2dc-7390-827b-382d2692622c/spq01/audit-method/audit-reconciliation.json) |
| Controlled source comparison interface | [manifest](C:/Users/aashraf/.codex/visualizations/2026/10/04/01a10902-e2dc-7390-827b-382d2692622c/spq01/source-comparison/manifest.json) |
| Offline tests | [27-test log](C:/Users/aashraf/.codex/visualizations/2026/10/04/01a10902-e2dc-7390-827b-382d2692622c/spq01/offline-tests-final.log) |

One actual human-unreviewed predictive development packet per domain:

- [Robotic arm](C:/Users/aashraf/.codex/visualizations/2026/10/04/01a10902-e2dc-7390-827b-382d2692622c/spq01/development/audit-development/packets/SPQ-bab3341a45950585.html)
- [Driving](C:/Users/aashraf/.codex/visualizations/2026/10/04/01a10902-e2dc-7390-827b-382d2692622c/spq01/development/audit-development/packets/SPQ-aab38b4bda710538.html)
- [Pushing/stacking](C:/Users/aashraf/.codex/visualizations/2026/10/04/01a10902-e2dc-7390-827b-382d2692622c/spq01/development/audit-development/packets/SPQ-d6d754b68497c8a4.html)
- [Tethered load](C:/Users/aashraf/.codex/visualizations/2026/10/04/01a10902-e2dc-7390-827b-382d2692622c/spq01/development/audit-development/packets/SPQ-3fdb49f01ac9ba76.html)

Packets contain private evidence for auditors. All actual attempts have failure=null;
there are no failed live items to conceal. Failed-item/retry-exhaustion/budget behavior
was tested offline. Earlier inventory/dry-run/console versions are retained too.

## Exact setup and executed commands

Reused established SPQ00 CPU environment; audit math reused the existing dataset
environment with NumPy 2.5.3 / SciPy 1.18.1. Both Python 3.12.14. No new install/GPU
qualification was needed. For a fresh CPU environment install requirements.lock.txt,
audit-requirements.lock.txt, then editable --no-build-isolation --no-deps installation;
preserved root schemas/assets require editable packaging.

Below are the executed logical commands; console output was also tee'd to linked logs.
Outputs use exclusive creation. Inspect existing artifacts or choose new paths for
OFFLINE reproduction. The initial select used development_exclusions.json while it
contained only the four SPQ00 groups. Committed spq01_selection_exclusions.json retains
that exact input. Reproduction after expanding formal exclusions produced identical
record SHA256 aa5fc3980c7bdc9a33e1a8efbd2dfdc23c4601936e31bb4b5e36ec2808124eb0.

~~~powershell
Set-Location 'C:/Users/aashraf/.codex/worktrees/simphysqa/phi-jepa'
$artifactRoot = 'C:/Users/aashraf/.codex/visualizations/2026/10/04/01a10902-e2dc-7390-827b-382d2692622c/spq01'
$cpuPython = 'C:/Users/aashraf/.codex/visualizations/2026/10/04/01a10902-e2dc-7390-827b-382d2692622c/simphysqa-venv/Scripts/python.exe'
$auditPython = 'C:/Users/aashraf/Desktop/Work/phi-jepa/phi-jepa/.dataset-venv/Scripts/python.exe'
$env:PYTHONDONTWRITEBYTECODE = '1'
$env:PYTHONPATH = 'C:/Users/aashraf/.codex/worktrees/simphysqa/phi-jepa/src'
$env:SIMPHYSQA_DATA_ROOT = 'C:/Users/aashraf/Desktop/Work/phi-jepa/phi-jepa/dataset-runs/release-four-domain-v1'
$env:SIMPHYSQA_DEVELOPMENT_RECORDS = "$artifactRoot/selection/predictive-records.jsonl"

& $cpuPython -m simphysqa.spq01 inventory --data-root $env:SIMPHYSQA_DATA_ROOT --output "$artifactRoot/inventory"
& $cpuPython -m simphysqa.spq01 select --inventory "$artifactRoot/inventory" --exclusions configs/simphysqa/development_exclusions.json --seed 20261004 --output "$artifactRoot/selection"
& $auditPython -m simphysqa.spq01 audit-check --output "$artifactRoot/audit-method" --replicates 200000 --seed 20261004
& $cpuPython -m simphysqa.spq01 dry-run --records $env:SIMPHYSQA_DEVELOPMENT_RECORDS --output "$artifactRoot/dry-run"
& $cpuPython -m unittest discover -s tests -p 'test*.py' -v

# Executed once within the authorized live allowance. Same output resumes.
# A new job directory would be another live job, outside the spent SPQ01 allowance.
& $cpuPython -m simphysqa.spq01 annotate --records $env:SIMPHYSQA_DEVELOPMENT_RECORDS --config configs/simphysqa/annotation_spq01.json --output "$artifactRoot/annotation-job"

& $cpuPython -m simphysqa.spq01 export-development --records $env:SIMPHYSQA_DEVELOPMENT_RECORDS --job "$artifactRoot/annotation-job" --output "$artifactRoot/development"
& $cpuPython -m simphysqa.spq01 compare-prepare --records $env:SIMPHYSQA_DEVELOPMENT_RECORDS --output "$artifactRoot/source-comparison"
& $cpuPython -m simphysqa.spq01 verify-development --selection "$artifactRoot/selection" --job "$artifactRoot/annotation-job" --development "$artifactRoot/development" --output "$artifactRoot/verification"

# Final checks after pricing/budget validation and actual-context classification:
& $cpuPython -m unittest discover -s tests -p 'test*.py' -v
& $cpuPython -m simphysqa.spq01 dry-run --records $env:SIMPHYSQA_DEVELOPMENT_RECORDS --output "$artifactRoot/dry-run-final"
& $cpuPython -m simphysqa.spq01 inventory --data-root $env:SIMPHYSQA_DATA_ROOT --output "$artifactRoot/inventory-final"
& $cpuPython -m simphysqa.spq01 select --inventory "$artifactRoot/inventory-final" --exclusions configs/simphysqa/spq01_selection_exclusions.json --seed 20261004 --output "$artifactRoot/selection-reproduction"
~~~

## Remaining decisions and work

Human inspect broader language and final rubric; automatic validation establishes
no human quality outcome. Counterfactual requires matched verified interventions;
explanation requires appropriate claim/causal evidence; clarification requires a
genuine gap and justified requested information. Those families are pending.

Scientific decisions: fixed/estimated prevalence and matching estimator/test,
reviewer heterogeneity, missingness/interval policy; final annotation version,
release population/rubric/weighting; exact alternative model/subset/blinded protocol.
Machine decisions: permanent external storage/portable paths, immutable service
snapshot availability and locally qualified answering artifacts/runtimes.
The missing-power-source blocker is resolved; API access worked. Full-release
annotation, formal sampling, downloads and answering benchmarks remain pending.
