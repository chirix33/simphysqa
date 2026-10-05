# SPQ02 completion — verified matched omission counterfactual QA

Branch **simphysqa-naacl**, worktree
`C:/Users/aashraf/.codex/worktrees/simphysqa/phi-jepa`.
Accepted parent **e379013b7e80fe28172682cd39e42f4066fde841**; final commit is
recorded in the external SPQ02 delivery receipt. Original main remains
**7dd4a64e90cfb18be743503ac8345cabf2f6e28b**; source data and unrelated work are preserved.
The consolidated chat specification is saved in
[SPQ02 prompt](../prompts/SPQ02_counterfactual_qa.md), with the user's replay clarification.
No broad cleanup or accepted association-renderer edits were performed.

## Outcome and artifacts

**Eight completed pairs, zero failed, zero pending: two per domain.** All factual
coarse replays reproduce stored physical states, private events, public model/
controller definitions and structured labels exactly. Separate original and omission
coarse/fine admission, physical-domain checks and existing source validation pass.
No numeric replay tolerance was introduced; no reference was changed to pass.

32 actual simulation executions: 16 factual +16 omission, half coarse/half fine.
32 completed, zero failed/timeouts/retries. Simulator-call wall time
**14.946897820 s**; complete worker wall time **51.244188115 s**, including process
startup, serialization and validation. Actual saved resume took **1.092065879 s**
inside the worker and launched zero new simulations. One separate static arm
model compilation used zero integration steps. Software mocks are separate tests.

| Domain | Actual calls | Simulator-call wall seconds | Integration steps | Engine solves |
| --- | ---: | ---: | ---: | ---: |
| robotic_arm | 8 | 5.061902399 | 240000 | 240000 |
| driving | 8 | 6.889200082 | 240000 | 240000 |
| object_pushing_stacking | 8 | 0.817703756 | 12000 | 12000 |
| tethered_load | 8 | 2.178091583 | 12000 | 48000 |

The serial budget allows at most 32 reservations, 180 s per subprocess and 1800 s
total wall time; prior calls/time count on resume. Failed/orphaned executions are
retained and cannot be automatically retried. No answering model, annotation
generator, model download, full-release simulation or formal audit sample ran.
New model requests/spend: **0 /USD0**; historical annotation estimated spend
USD.522767 is unchanged. Human independent ratings remain **zero**.

Eight new 0.3.0 counterfactual QA items select two scalar, two vector and four
Boolean targets from existing supported post-onset target times. Five selected
readouts differ between original and omission runs; three Boolean readouts remain
the same. This does not measure annotation quality or benchmark performance.
Some physical differences are small relative to retained answer tolerances; the
development sample is not intended to guarantee challenging/different answers.
No case was replaced to increase effect size.

All eight development audit packets include the original public scenario/language,
explicit omission question, alternative reference and private paired evidence.
Three separate reviewer forms remain blank and each imports zero ratings/eight
blanks. 72 tool-free public baseline requests (eight by nine conditions) are
prepared, not executed. Annotation-provider identity remains in organizer-private
provenance. Existing 32 QA packets/288 requests are untouched.

[Frozen private expanded plan](C:/Users/aashraf/.codex/visualizations/2026/10/04/01a10902-e2dc-7390-827b-382d2692622c/spq02/plan.json), [lightweight selection/exclusion manifest](C:/Users/aashraf/.codex/visualizations/2026/10/04/01a10902-e2dc-7390-827b-382d2692622c/spq02/selection-manifest.json),
[explicit replay decision](C:/Users/aashraf/.codex/visualizations/2026/10/04/01a10902-e2dc-7390-827b-382d2692622c/spq02/replay-criterion.json), [resolved preflight](C:/Users/aashraf/.codex/visualizations/2026/10/04/01a10902-e2dc-7390-827b-382d2692622c/spq02/preflight-ready.json),
[execution ledger](C:/Users/aashraf/.codex/visualizations/2026/10/04/01a10902-e2dc-7390-827b-382d2692622c/spq02/runs/execution-ledger.json), [runtime/source snapshots manifest](C:/Users/aashraf/.codex/visualizations/2026/10/04/01a10902-e2dc-7390-827b-382d2692622c/spq02/runs/manifest.json),
[environment comparison](C:/Users/aashraf/.codex/visualizations/2026/10/04/01a10902-e2dc-7390-827b-382d2692622c/spq02/runs/environment-comparison.json), [run summary](C:/Users/aashraf/.codex/visualizations/2026/10/04/01a10902-e2dc-7390-827b-382d2692622c/spq02/runs/run-summary.json).
All raw factual/omission results, verification runs and admission receipts are
retained beneath the private `runs` root. There are no failed empirical executions
to suppress; the failure-policy software tests use explicitly labeled synthetic mocks.

[Private paired QA/evidence JSONL](C:/Users/aashraf/.codex/visualizations/2026/10/04/01a10902-e2dc-7390-827b-382d2692622c/spq02/export-1.0.0/organizer-private/qa-records.jsonl), [all model-visible QA](C:/Users/aashraf/.codex/visualizations/2026/10/04/01a10902-e2dc-7390-827b-382d2692622c/spq02/export-1.0.0/public-qa.json),
[export manifest](C:/Users/aashraf/.codex/visualizations/2026/10/04/01a10902-e2dc-7390-827b-382d2692622c/spq02/export-1.0.0/manifest.json), [saved verification and readout comparisons](C:/Users/aashraf/.codex/visualizations/2026/10/04/01a10902-e2dc-7390-827b-382d2692622c/spq02/organizer-private-saved-verification.json).
Organizer-private references are not part of the model-visible JSON/requests.

## Frozen selection and intervention isolation

Seed **20261004**, Python Random, fixed domain order, candidate IDs sorted; two
without replacement per domain, object domain one from each sorted pre_stacked/
pushing subfamily. All selected sources are admitted SPQ01 development train
trajectories. The eight IDs were frozen before any simulator execution; the
expanded-plan SHA256 is **486e25a5bdbfab4726ae88d80dc4ea36f059751b4c28a170c773387bae21bb58**.
Original qualifier order visits the first case in each domain, then the second
cases. Omission runs only follow completed factual qualification. Existing twenty
fresh-formal excluded groups remain unchanged; all eight are already members.
No definitive formal sample was exported. This is engineering selection, not
unbiased quality estimation or a subgroup-powered human sample.

| Domain | Frozen group | Pair |
| --- | --- | --- |
| robotic_arm | `a9563dc9343a2c57b624ae5048f3216a` | `spq-cf-cb6d47eb575e8f009119e0b6` |
| driving | `8527f5b0a2fef1d647c2fb239b52e473` | `spq-cf-632234e5dde98c9e3f45bb83` |
| object_pushing_stacking | `de7550b6e98df7e249dc3c44f1874120` | `spq-cf-3433d54a77e5aca3aa5da6ba` |
| tethered_load | `3c44b44c4f41c3e7b89ffb6ab352a9a3` | `spq-cf-17fa1b217076ba1ea1c40fce` |
| robotic_arm | `8c6023bf3a70e990db8eb51fb1ff9106` | `spq-cf-51acc3cc64c1fa0f5accc571` |
| driving | `75d5bf58ef3677542fb0eeedc7ef467c` | `spq-cf-f14d72eca263068b20ca273b` |
| object_pushing_stacking | `201bd588247c0ba999f1955a18d6d3f5` | `spq-cf-f0c4ff7a3c3ffac4eb9c1b7d` |
| tethered_load | `fe9fbb418a17d5412a16024d7a76ea64` | `spq-cf-cb55c59d6c4094f3d4411fa3` |

The only scientific execution change is `omit_scheduled_intervention=false -> true`:
arm removes the additional .5 N m pulse while retaining both base joint torques;
driving removes scheduled wheel braking (maximum torque .25 N m/wheel, not a
realized-torque measurement); object cases remove the scheduled external world-x
force on block_1; tether removes the whole support-motion program, including both
acceleration phases and its later displacement. Same scenario/configuration,
initial states, parameters, seeds, assets, other controls and horizons at each
matched dt. Original dt is .0001 s for arm/driving and .002 s for object/tether;
fine dt is half, and horizons remain 2 s.

Derived alternative records get new IDs/references, empty scheduled-event lists,
an explicit controller-description omission override, absent applied-intervention
events and provenance/configuration hashes identifying the omission run. Applied
interval diagnostic fields are null. These are documented derived changes; raw
parent source and its physical/reference/provenance fields stay exact. Every
question binding specifies its alternative run namespace, target and terminal
state; units/frame/time are taken unchanged from the original answer specification.

## Arm frame resolution and replay/admission

The simulator sets `data.qfrc_applied[:] = joint_torque_Nm` and adds `.5` only to
coordinate zero during the pulse. Declared XML/model introspection identifies
joint_1 as hinge DOF zero with local axis [0,1,0]. This establishes scalar
generalized joint torque in the same coordinate as the base torque. The raw `world`
event parameter frame comes from the generic `quantity` helper's default, with no
Cartesian torque transformation in the implementation. Preserve raw source metadata
and accepted 1.1.1 annotations; resolved interpretation is recorded separately in
private audit omission semantics and the [arm trace/model/header evidence](C:/Users/aashraf/.codex/visualizations/2026/10/04/01a10902-e2dc-7390-827b-382d2692622c/spq02/arm-interpretation.json).
The local MuJoCo header and [official 3.14 API](https://mujoco.readthedocs.io/en/3.14.0/APIreference/APItypes.html)
distinguish generalized qfrc_applied from Cartesian xfrc_applied.

The user explicitly confirmed exact canonical replay before any trajectory run.
JSON canonicalization preserves every numerical value and Boolean/numeric type;
runtime, creation time and output paths are the only excluded non-scientific
metadata. All eight have zero differing scientific fields and zero numeric/Boolean/
event differences. The comparator reports first differing fields and quantity/unit/
timestamp diagnostics on failure. No fallback numerical criterion was needed.

Recovered simulator runtime matches original **Python3.11.16, WSL2 Linux
6.18.33.2/glibc2.39**, MuJoCo3.14.0, PyBullet3.2.7, NumPy2.4.6,
jsonschema4.26.0 and psutil7.2.2. Original configurations, solver values/assets and
seeds are in the private plan/environment comparison. Simulator modifications
have a default-false omission flag; executed sources are pinned by normalized-text
hashes and snapshots. Their accepted base commit is distinct from the final source
commit. Native Windows CPU annotation/export Python3.12.14 is not the replay runtime.

Original and alternative refinement use unchanged `pipeline.comparison`: exact
Booleans; .01 endpoint tolerance for m/s or rad/s, .005 for other numeric channels;
vector norms and sign-invariant quaternion rotation angles; matching event type/
count/order with times <=.01+1e-10 s and prescribed terminal Boolean diagnostics.
Full trajectory worst errors are retained; admission uses prescribed endpoints/
events. Driving min forward velocity >=-.02 m/s; tether min tension >0 and length
error <1e-6 m. Arm/object use existing source semantic/finite-state validation.
All sixteen factual/alternative refinement checks and all domain/source checks
pass. Individual results/worst channels are in the private paired verification
and raw rollouts. QA answer tolerances remain the original target-specific values,
not replay/admission tolerances. Typed scorer probes verify exact supplied readouts,
missing failure denominators and wrong-frame rejection; no answering model ran.

## Public coverage and examples

[Actual admitted public-release coverage/proposals](C:/Users/aashraf/.codex/visualizations/2026/10/04/01a10902-e2dc-7390-827b-382d2692622c/spq02/public-event-coverage.json)
scans 11,105 QA records /6,340 trajectory groups in 18.3747682 s. It does not
count private future events as public overlap or use the smoke frame as population.

| Domain | Release QA records | Trajectory groups | Active /ended /between-state records |
| --- | ---: | ---: | --- |
| robotic_arm | 3226 | 1661 | 0 /0 /0 |
| driving | 1279 | 1279 | 0 /0 /0 |
| object_pushing_stacking | 3300 | 1700 | 0 /0 /0 |
| tethered_load | 3300 | 1700 | 0 /0 /0 |

All established cutoffs remain .2 s, with later known interventions. Four separate
new-view IDs/cutoff proposals are recorded, not exported; they require separately
validated public prefixes/language and retained later targets. This gap did not
block the eight matched pairs. No observed state or boundary was invented.

| Domain | Model-visible JSON | Private development audit packet |
| --- | --- | --- |
| driving | [Public JSON](C:/Users/aashraf/.codex/visualizations/2026/10/04/01a10902-e2dc-7390-827b-382d2692622c/spq02/export-1.0.0/public-items/spq-counterfactual-e3457ad6b03d422ebc6191a3.json) | [Audit HTML](C:/Users/aashraf/.codex/visualizations/2026/10/04/01a10902-e2dc-7390-827b-382d2692622c/spq02/export-1.0.0/audit-development/packets/SPQ-2f6fa7d41ba8aa01.html) |
| object_pushing_stacking | [Public JSON](C:/Users/aashraf/.codex/visualizations/2026/10/04/01a10902-e2dc-7390-827b-382d2692622c/spq02/export-1.0.0/public-items/spq-counterfactual-68a75d394cefe37a0d48a30c.json) | [Audit HTML](C:/Users/aashraf/.codex/visualizations/2026/10/04/01a10902-e2dc-7390-827b-382d2692622c/spq02/export-1.0.0/audit-development/packets/SPQ-d2bb85d47d4de054.html) |
| robotic_arm | [Public JSON](C:/Users/aashraf/.codex/visualizations/2026/10/04/01a10902-e2dc-7390-827b-382d2692622c/spq02/export-1.0.0/public-items/spq-counterfactual-880173bd9c70a2ba3e5efa4d.json) | [Audit HTML](C:/Users/aashraf/.codex/visualizations/2026/10/04/01a10902-e2dc-7390-827b-382d2692622c/spq02/export-1.0.0/audit-development/packets/SPQ-13d5eb47ed23f1d6.html) |
| tethered_load | [Public JSON](C:/Users/aashraf/.codex/visualizations/2026/10/04/01a10902-e2dc-7390-827b-382d2692622c/spq02/export-1.0.0/public-items/spq-counterfactual-a41f46c4b8284962632afb9c.json) | [Audit HTML](C:/Users/aashraf/.codex/visualizations/2026/10/04/01a10902-e2dc-7390-827b-382d2692622c/spq02/export-1.0.0/audit-development/packets/SPQ-6f79b2ffed09b04c.html) |

## Verification and saved preservation

Final CPU suite: **79 tests passed in 102.268 s**, with the simulator-runtime-only
class skipped. Pinned WSL policy suite: **six additional tests passed** with zero
real integration calls (explicit software mocks). Combined 85 unique checks cover
existing contracts, frozen selection/exclusions, target/cutoff fidelity, exact vs
tolerant comparison, missing decisions, failures/resume, alternative admission
requirements, evidence namespaces, source restore, public separation, accepted
association recovery and numerical/Boolean scoring. The initial scalar-only test
assumption and missing-artifact exception expectation were corrected; initial
failure logs remain preserved. They were test errors, not empirical simulation failures.

[Final CPU test log](C:/Users/aashraf/.codex/visualizations/2026/10/04/01a10902-e2dc-7390-827b-382d2692622c/spq02-offline-tests-success.log), [final WSL policy log](C:/Users/aashraf/.codex/visualizations/2026/10/04/01a10902-e2dc-7390-827b-382d2692622c/spq02-replay-policy-tests-final.log),
[simulation log](C:/Users/aashraf/.codex/visualizations/2026/10/04/01a10902-e2dc-7390-827b-382d2692622c/spq02-simulations.log), [actual simulation resume](C:/Users/aashraf/.codex/visualizations/2026/10/04/01a10902-e2dc-7390-827b-382d2692622c/spq02-simulation-resume.log), [saved verification log](C:/Users/aashraf/.codex/visualizations/2026/10/04/01a10902-e2dc-7390-827b-382d2692622c/spq02-saved-verification.log).

All 128 run files and 56 export files are byte-stable after actual resumption.
All 122 accepted 1.1.1 files and 140 SPQ01a files remain byte-identical, and 214
indexed SPQ01 files verify unchanged. Selected original shard/config/partition
hashes also match. Original measurement values, QA IDs/references, units/frames,
cutoffs and public/private boundaries are unchanged. Historical root instructions/
README/progress bytes are retained under dated active pointers.

## Exact commands

Reuse installed environments; no installation or downloads were needed. The replay
decision file already records the user's approval. These commands are resumable;
existing completed outputs are checked, not overwritten.

```powershell
Set-Location 'C:/Users/aashraf/.codex/worktrees/simphysqa/phi-jepa'
$spqRoot = 'C:/Users/aashraf/.codex/visualizations/2026/10/04/01a10902-e2dc-7390-827b-382d2692622c'
$cpuPython = "$spqRoot/simphysqa-venv/Scripts/python.exe"
$env:PYTHONDONTWRITEBYTECODE = '1'
$env:PYTHONPATH = 'C:/Users/aashraf/.codex/worktrees/simphysqa/phi-jepa/src'
& $cpuPython -m simphysqa.spq02_prepare --source "$spqRoot/spq01a/event-language-2.0.0" --baseline "$spqRoot/spq01a/associations-1.1.1" --exclusions "$spqRoot/spq01/selection/selection.json" --output "$spqRoot/spq02"

$wslSource = '/mnt/c/Users/aashraf/.codex/worktrees/simphysqa/phi-jepa/src'
$simPython = '/mnt/c/Users/aashraf/Desktop/Work/phi-jepa/phi-jepa/.dataset-bullet-venv/bin/python'
$wslSpq = '/mnt/c/Users/aashraf/.codex/visualizations/2026/10/04/01a10902-e2dc-7390-827b-382d2692622c/spq02'
wsl.exe -d Ubuntu-24.04 -- env PYTHONDONTWRITEBYTECODE=1 "PYTHONPATH=$wslSource" $simPython -m simphysqa.spq02_worker --plan "$wslSpq/plan.json" --output "$wslSpq/preflight-ready.json" --preflight
wsl.exe -d Ubuntu-24.04 -- env PYTHONDONTWRITEBYTECODE=1 "PYTHONPATH=$wslSource" $simPython -m simphysqa.spq02_worker --plan "$wslSpq/plan.json" --output "$wslSpq/runs"
# The same worker command was run again: zero new calls, preserved evidence.

& $cpuPython -m simphysqa.spq02_export --plan "$spqRoot/spq02/plan.json" --runs "$spqRoot/spq02/runs" --output "$spqRoot/spq02/export-1.0.0"
& $cpuPython -m simphysqa.spq02_verify --plan "$spqRoot/spq02/plan.json" --runs "$spqRoot/spq02/runs" --export "$spqRoot/spq02/export-1.0.0" --baseline "$spqRoot/spq01a/associations-1.1.1" --source "$spqRoot/spq01a/event-language-2.0.0" --original "$spqRoot/spq01" --output "$spqRoot/spq02/organizer-private-saved-verification.json"

$env:SIMPHYSQA_DATA_ROOT = 'C:/Users/aashraf/Desktop/Work/phi-jepa/phi-jepa/dataset-runs/release-four-domain-v1'
$env:SIMPHYSQA_DEVELOPMENT_RECORDS = "$spqRoot/spq01/selection/predictive-records.jsonl"
$env:SIMPHYSQA_SPQ01_QA = "$spqRoot/spq01/development/qa-records.jsonl"
$env:SIMPHYSQA_SPQ01A_ROOT = "$spqRoot/spq01a/event-language-2.0.0"
$env:SIMPHYSQA_SPQ02_PLAN = "$spqRoot/spq02/plan.json"
$env:SIMPHYSQA_COUNTERFACTUAL_QA = "$spqRoot/spq02/export-1.0.0/organizer-private/qa-records.jsonl"
& $cpuPython -m unittest discover -s tests -p 'test*.py' -v
wsl.exe -d Ubuntu-24.04 -- env PYTHONDONTWRITEBYTECODE=1 "PYTHONPATH=$wslSource" "SIMPHYSQA_SPQ02_PLAN=$wslSpq/plan.json" $simPython -m unittest discover -s tests -p test_spq02_worker.py -v
```

The coverage and static arm-inspection commands also ran once, to new outputs:

```powershell
# Source modules now provide the same implementation used by the recorded staging commands.
& $cpuPython -m simphysqa.spq02_coverage --release $env:SIMPHYSQA_DATA_ROOT --plan "$spqRoot/spq02/plan.json" --output "$spqRoot/spq02/public-event-coverage.json"
wsl.exe -d Ubuntu-24.04 -- env PYTHONDONTWRITEBYTECODE=1 "PYTHONPATH=$wslSource" $simPython -m simphysqa.spq02_arm_inspect --plan "$wslSpq/plan.json" --output "$wslSpq/arm-interpretation.json"
```

These two inventory/inspection outputs are exclusive-write artifacts; already
existing files are preserved. To repeat those commands, choose a fresh output path.
The recorded staging file commands were `spq02_coverage.py` and
`spq02_arm_inspect.py` under the external root, with the same arguments/contents.

## Active files and remaining work

`src/simphysqa/spq02_*`: prepare/preflight/execution/export/integrity/coverage/trace.
`src/simphysqa/counterfactual.py`: typed QA, omission contract and private proof
validation. `dataset.py`, `record.schema.json`, `audit.py`: family integration.
`src/phi_jepa/simulation/engines.py` and `bullet.py`: default-false omission only.
`configs/simphysqa/counterfactual.json`: pinned budget/runtime/target policy.
`docs/simphysqa`, `docs/prompts`, `docs/decisions`, `docs/reviews`: research contract
and durable handoff. Original simulator admission/assets and association 1.1.1
modules remain active. No generated data is tracked in this source commit.

No unresolved machine prerequisite blocks these eight CPU pairs. Scientific
limitations: engineering sample, original .2 s observed-event coverage gap, three
unchanged Boolean readouts and small numerical contrasts, unchanged coarse/fine
admission assumptions, and unreviewed human language/QA quality. Exact replay is
qualified only for the frozen cases/runtime, not every release trajectory or machine.

Next: independent development audit/corrections; separately authorized observed-
event views; broader counterfactual interventions/target selection and release
qualification. Explanation QA needs appropriate causal evidence beyond timing;
clarification QA needs a genuine information gap and justified requested information.
Alternative annotation-source model/subset/protocol pinning, local answering-model
qualification, uncertainty analysis and formal rubric/population readiness remain
pending. No human agreement, annotation acceptance or benchmark results exist.
