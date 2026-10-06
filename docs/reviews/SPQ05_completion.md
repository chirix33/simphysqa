# SPQ05 final 140 audit package — 6 October 2026

Status: **audit package complete and verified; human judgments uncollected**.
140 unique QA/140 distinct trajectories and split groups, 20 cells of 7; all three
R1/R2/R3 slots inspect the SAME 140 items independently, 420 individual ratings.
No calibration set or personal identity mapping. Shortfall:0. This supersedes the
pre-authorization preparation/shortfall report retained below.

Start at [blinded review entry](C:/Users/aashraf/.codex/visualizations/2026/10/06/01a1131b-eac2-7a31-afb4-f219a8dd6471/spq05/review-bundle-1.0.0/review-index.html).
Distribute only review-bundle-1.0.0 to reviewers; organizer protocol, request/output
provenance, budgets and generator identity stay in the separate delivery/run/archive
roots. Gold/extra verification are auditor-only links outside primary rating scope.

Branch `simphysqa-spq05`, existing SimPhysQA worktree; started fetched current main
`ff2fe26d178883a2cbc68938d661bb157342b5fc`. Main and AGENTS.md remain unchanged.
Initial live producer `6b7d5b53390ef746f8e0a7059bf504c00239b652`;
qualified continuation producer `2954f516c9ca1dbb86a8f50b5607aebd21e3e283`. Exact attempt 1–10
and 11–145 commit ranges are in run/producer-lineage.json. Intermediate `fbb4950`
performed no provider call. Archive producer `a84b99414fc03812cb1d29e43da3542bff7edbff`.
Final source commit is the commit containing this report; its full SHA is recorded
in external delivery.json after committing, and in the final handoff. No merge/push.

## Focus, sampling and qualification

Focused internal human audit: physical/global context, observed-window trajectory
language, question wording/canonical family, generated timestamp language and
state-event descriptions. Private answers, explanations, traces and benchmark
outcomes are not automatically a comprehensive rating scope. No model performance,
acceptance, agreement, achieved power or new OOD result is claimed.

Source: original admitted four-domain release 1.0.0,11,105 predictive QA/6,340 groups.
All 20 authoritative inspected/development groups excluded;6,320 source groups remain.
Preserve physical records, IDs, values/types, references, tolerances, splits,
cutoffs and historical artifacts. Four domains × five families × seven=140. Pooled
future ratings concern the balanced qualification-conditioned design, not natural
record-weighted quality of 11,105 source records. Seven/cell does not power subgroup claims.

| Domain | Direct | Predictive | Counterfactual | Explanation | Clarification | Total |
|---|---|---|---|---|---|---|
| robotic_arm | 7 | 7 | 7 | 7 | 7 | 35 |
| driving | 7 | 7 | 7 | 7 | 7 | 35 |
| object_pushing_stacking | 7 | 7 | 7 | 7 | 7 | 35 |
| tethered_load | 7 | 7 | 7 | 7 | 7 | 35 |

Frozen preparation 1.0.1, seed 20261006 and 280 unique-group candidates (140 primary,
140 reserves) precede live annotation/simulation. Group shuffle/disjoint family
pools and random source question/group remain unchanged. Candidate processing kept
first 7 qualified per cell, same-cell reserve order only. Final ledger accounts for
140 selected, 3 retained rejections and 137 unused reserves. No silently dropped case.

Two robotic_arm/predictive primaries failed an adapter implementation binding;
stop/repair preserved failures and outputs. A saved-output offline probe caught
text-hash normalization before further calls; explicit revision 001/002 pins the
corrected adapter. Accepted scientific source/procedures/schemas, allocation,
order, scoring and budgets were unchanged. Two same-cell reserves replaced those
failed primaries. One tethered_load/clarification primary lacked a disjoint query
gap and was replaced by the next qualifying same-cell reserve. Its selection
certificates remain saved; no scientific rule was relaxed.

Clarification:56 frozen candidates, 29 processed, 28 qualified, 1 query-gap rejection,
27 unused reserves. Qualified gaps:15 execution_condition, 6 entity_id, 7 readout_time.
All use two whole-visible-input-compatible completions with incompatible answers
under actual scorer/disjoint-acceptance-region checks. Extra-time readouts have
saved coarse/fine verification. Authored clarification/reply/resolved stages are
labeled reference turns, never executed answering-model conversations.

85 paired workers/340 trajectory executions:84 pairs support selected CF/explanation/
clarification items, one supports the rejected gap candidate. Each retains exact
factual replay and separate factual/omission admission evidence. Direct/predictive
use admitted original outcomes as applicable.21 arm model compilations have zero
trajectory steps and their work is charged to the simulation-work ceiling.

The selected 28 CF include 7 unchanged Booleans and 12 numeric contrasts within
existing answer tolerance;28 explanation items include 6 unchanged Booleans and 11
within-tolerance numeric contrasts. These are physical comparisons, not human
quality judgments. Unchanged outcomes did not trigger exclusion. Explanation
supplied comparison readouts are separate from observed prefix states.

## Execution and cumulative accounting

User separately authorized additional ceilings and the exact observed-prefix
annotation payloads to the fixed OpenAI Responses endpoint with the existing
credential reference. Initial automatic review rejected destination/payload
specificity; no call executed on that command. Subsequent explicit approval and
non-secret receipts are preserved. No per-item human approval gate.

Official [model](https://developers.openai.com/api/docs/models/gpt-5.6-sol) and
[pricing](https://developers.openai.com/api/docs/pricing) pages refreshed 6 October:
input 4/cached 0.4/cache-write 5/output 20 USD/million; conservative reservation rates
10/40 retained. gpt-5.6-sol,medium, 2,048 output tokens, 120-second timeout, default
tier, store=false, tools=[], omitted temperature/seed. Returned identities are saved;
no distinct immutable backend snapshot is asserted. No credentials in outputs/logs.

| Resource | Recorded/charged SPQ05 use | Additional authorized ceiling |
|---|---|---|
| Initial requests |143|280|
| Attempt reservations |145 (144 returned responses, 1 unknown)|560|
| Repairs |2; max 2 attempts/candidate|2 attempts/candidate|
| Known token-priced USD |4.694143|Included in 125 total|
| Unknown request reservation |0.203280|Included in 125 total|
| Total charged USD |4.897423|125|
| Reserved input tokens |1,721,085|7,000,000|
| Reserved output tokens |296,960|1,146,880|
| Annotation attempt work seconds |1,727.182, including 120 unknown reservation|7,200|
| Simulator executions |340|672;180 seconds/execution|
| Worker/static-compile work seconds |724.704|3,600|

Known returned usage:281,791 input/164,281 output tokens. Unknown attempt 10 has no
invented output/usage: its 12,136 input/2,048 output token bound and full 0.203280 USD/
120-second reservation remain charged. Its candidate used the one permitted repair.
A tether annotation initially failed missing_focal_physical_description and passed
its one logged repair. Every raw request/returned output/reservation/validation
failure/retry/solve/rejection/replacement is retained. Historical usage (16 initial
annotations, 16 attempts, 0.522767 USD;32 simulations) remains separate; no old ceiling
was renewed. No limit expanded. All package/export/verification work is offline.

## Validation, privacy and immutable review

Full saved-data verification passed:140 distinct sample IDs, 140 trajectories/groups,
all 20 exclusions, 20 × 7 allocation, source restore equality, 6340 unchanged source
shards, 62 unchanged historical manifests/5,002 indexed checks. All 140 exact public
views and private packets match frozen hashes. Original source values/types,
measurements, relations, entity/quantity/unit/frame metadata, split/cutoff and
references survive unchanged; derived new QA retains its exact source lineage.

Focused extraction uses actual packet keys, joining language timestamps by state_id.
All 1,540 public states/1,540 actual state-event links retained;116,734 public and
17,605 private answer/trace bindings resolved. Original event schedule/controllers
are beside generated descriptions. All required fields present; no empty-string
substitution. Primary pages clearly distinguish global physical setup, trajectory
language, original state.context and generated timestamp text.

Actual temporal coverage:1,540 scheduled_future links, no observed application or
causal effect claim. Description status:1,155 supported_declared_semantics and 385
limited_unresolved_semantics. No cutoff changed to manufacture active/past coverage.
Selected items have 0 no-event states; synthetic software tests verify their retention,
not an empirical no-event coverage claim. Declared uncertainty remains explicit.

R1/R2/R3 each have the exact same 140 assignments, 140 blanks/0 collected. Assignment
lists are byte-identical except reviewer slot. Original CSV and ratings import use
exclusive immutable creation; duplicate imports fail. Blank forms cannot become
collected submissions. Discussion, adjudication, rubric revisions and proposed
corrections go to separate roots/versions, never edits of frozen packets. Generator
identity/request settings are excluded from the 849-file blinded distribution.

Run resume preserved 3,991 prior files and identical 145-attempt/340-solve resource
counters, with 0 new calls/solves. Packet, readable-page, blinded-bundle and final
archive generation also passed actual exact-byte saved-output resume. The final
archive indexes 6,293 executed/reused/deterministic files, with exact per-attempt
producer commits; it inherits sealed prior archives and preparation mappings.
Prepared requests remain distinct from actual returned/unknown attempts.

Offline verification: full CPU suite 138 tests passed (one simulator-runtime class
skipped); current focused execution/extraction/import tests 16 passed after adapter
repair; the skipped class's six policy tests separately passed in the pinned WSL
simulator environment with 0 real simulations. An actual saved-response predictive
probe and direct/explanation/clarification packet/render probes passed with 0 calls.
Fixture tests are software checks, not empirical model or human performance.

Analysis specification and guide were frozen before review: pooled design summary,
complete-triplet Fleiss kappa, missing 420-assignment bounds and 80% stratified whole-
item bootstrap defined. Preserve the historical score-planning power discrepancy
(.8237409136 approximation vs.879659735 exact at 140;5.532 pp), not achieved audit power.
No ratings or numerical quality/agreement analysis has been executed.

## Commands and artifacts

External audit root: `C:/Users/aashraf/.codex/visualizations/2026/10/06/01a1131b-eac2-7a31-afb4-f219a8dd6471/spq05`. All prior/superseded roots retained.
The following commands were run from the existing worktree with PYTHONPATH=src
and PYTHONDONTWRITEBYTECODE=1; $Python is the pinned CPU venv path below.

```powershell
$Python = 'C:/Users/aashraf/.codex/visualizations/2026/10/04/01a10902-e2dc-7390-827b-382d2692622c/merge-review/cpu-venv/Scripts/python.exe'
$Audit = 'C:/Users/aashraf/.codex/visualizations/2026/10/06/01a1131b-eac2-7a31-afb4-f219a8dd6471/spq05'
$Prior = 'C:/Users/aashraf/.codex/visualizations/2026/10/04/01a10902-e2dc-7390-827b-382d2692622c'
& $Python -m unittest discover -s tests -p 'test_formal*.py'
# Full suite via scripts/simphysqa_spq04.ps1 -Mode check, with foundation artifact env set.
& $Python -m simphysqa.formal_live freeze --preparation "$Audit/preparation-1.0.1" --output "$Audit/run-1.0.0"
& $Python -m simphysqa.formal_live run --output "$Audit/run-1.0.0"
& $Python -m simphysqa.formal_live revise --output "$Audit/run-1.0.0" # twice; versioned repair chain
& $Python scripts/simphysqa_formal_dryrun.py --run "$Audit/run-1.0.0" --output "$Audit/authorized-payload-dryrun-1.0.0"
# Actual zero-call saved-run resume/proof: staging/spq05_saved_resume.py.
& $Python scripts/simphysqa_formal_readable.py --run "$Audit/run-1.0.0" --output "$Audit/delivery-1.0.0"
& $Python -m simphysqa.formal_delivery --run "$Audit/run-1.0.0" --output "$Audit/delivery-1.0.0"
& $Python scripts/simphysqa_verify_formal_delivery.py --run "$Audit/run-1.0.0" --delivery "$Audit/delivery-1.0.0" --preparation "$Audit/preparation-1.0.1" --prior $Prior --output "$Audit/delivery-verification.json"
& $Python scripts/simphysqa_formal_blinded_bundle.py --delivery "$Audit/delivery-1.0.0" --output "$Audit/review-bundle-1.0.0"
& $Python -m simphysqa.focused_audit import-ratings --packets "$Audit/review-bundle-1.0.0" --form "$Audit/review-bundle-1.0.0/forms/R1.csv" --reviewer R1
# R2/R3 also validate blank; no --output, no submission collected.
& $Python scripts/simphysqa_formal_live_archive.py --run "$Audit/run-1.0.0" --delivery "$Audit/delivery-1.0.0" --preparation "$Audit/preparation-1.0.1" --review-bundle "$Audit/review-bundle-1.0.0" --previous "$Prior/spq04/prompt-archive-1.0.7" --output "$Audit/executed-prompt-archive-1.0.1"
# Readable/delivery/bundle/archive commands repeated against actual saved outputs: passed.
```

WSL policy test command used Ubuntu-24.04 and the existing .dataset-bullet-venv
Python with PYTHONPATH set to the worktree src, SIMPHYSQA_SPQ02_PLAN set to the
retained prior plan; `-m unittest discover -s <worktree>/tests -p test_spq02_worker.py -v`.
Actual simulation-worker plans/logs/runtime/source snapshots and each execution
reservation/result live under run-1.0.0/cases/*/runs. Source/provider schema and
exact executed request bodies are archived in executed-prompt-archive-1.0.1.

| Artifact | SHA256 |
|---|---|
| initial protocol | `847a0ef94145236ca936c8e730cd75b3fef4f5ab350380317f5a89f88b17d85a` |
| initial execution plan | `25baa2b384788073f36494db6010124fed208323c1a648ecbedb4519399ec894` |
| execution repair 001 | `55acfd655dd8b6597136ef7dca22bf7d3a1f964fb1d82dc37fbf12f8d3bafbc8` |
| execution repair 002 | `5d092c2f211ba7acded62cd0458f92eafe59df4b4f50679c5c3a4883f5cf7d6d` |
| final 140 manifest | `c8c0fdd6b138d879d8e7104caed004ca8086f6710925fc0d0fef9ef02fbd6c04` |
| organizer delivery manifest | `31de52c4ccfab7d2e646c2db1ae25326f811a96367abe2eb687dfd5cb6884580` |
| blinded reviewer manifest | `783f8316dafad6040a91cb1787add4b56a1f02257b5e8b53d5d46cb2c9904648` |
| executed archive manifest | `8471e5446828b1ed75297a72eeb4d6cd3d54a79c3e13f0ef6309648aecf3f7f4` |
| executed per-file index | `61d1e8695cb4d6d7e7108fda1e43a9ff92379558ea4ab49d104a2102ed99a6c5` |

All 20 inspectable cells below point to the same final frozen review bundle.

| Cell | Packet | Inspect |
|---|---|---|
| driving/clarification | SPQ-7 b 26178409334 a 82 | [focused review](C:/Users/aashraf/.codex/visualizations/2026/10/06/01a1131b-eac2-7a31-afb4-f219a8dd6471/spq05/review-bundle-1.0.0/review-pages/SPQ-7b26178409334a82.html) |
| driving/counterfactual | SPQ-169 d 5 a 11813 fc 17 b | [focused review](C:/Users/aashraf/.codex/visualizations/2026/10/06/01a1131b-eac2-7a31-afb4-f219a8dd6471/spq05/review-bundle-1.0.0/review-pages/SPQ-169d5a11813fc17b.html) |
| driving/direct | SPQ-0554625 f 9 ba 09 e 55 | [focused review](C:/Users/aashraf/.codex/visualizations/2026/10/06/01a1131b-eac2-7a31-afb4-f219a8dd6471/spq05/review-bundle-1.0.0/review-pages/SPQ-0554625f9ba09e55.html) |
| driving/explanation | SPQ-c 0333 e 6 a 3 c 68192 d | [focused review](C:/Users/aashraf/.codex/visualizations/2026/10/06/01a1131b-eac2-7a31-afb4-f219a8dd6471/spq05/review-bundle-1.0.0/review-pages/SPQ-c0333e6a3c68192d.html) |
| driving/predictive | SPQ-ffe 241 dab 3 ac 1 f 4 d | [focused review](C:/Users/aashraf/.codex/visualizations/2026/10/06/01a1131b-eac2-7a31-afb4-f219a8dd6471/spq05/review-bundle-1.0.0/review-pages/SPQ-ffe241dab3ac1f4d.html) |
| object_pushing_stacking/clarification | SPQ-95402 f 6 be 3561384 | [focused review](C:/Users/aashraf/.codex/visualizations/2026/10/06/01a1131b-eac2-7a31-afb4-f219a8dd6471/spq05/review-bundle-1.0.0/review-pages/SPQ-95402f6be3561384.html) |
| object_pushing_stacking/counterfactual | SPQ-b 6133 b 49 fa 5 a 610 e | [focused review](C:/Users/aashraf/.codex/visualizations/2026/10/06/01a1131b-eac2-7a31-afb4-f219a8dd6471/spq05/review-bundle-1.0.0/review-pages/SPQ-b6133b49fa5a610e.html) |
| object_pushing_stacking/direct | SPQ-65442 eb 356 dd 8 d 15 | [focused review](C:/Users/aashraf/.codex/visualizations/2026/10/06/01a1131b-eac2-7a31-afb4-f219a8dd6471/spq05/review-bundle-1.0.0/review-pages/SPQ-65442eb356dd8d15.html) |
| object_pushing_stacking/explanation | SPQ-c 8 b 159 c 449 ad 0237 | [focused review](C:/Users/aashraf/.codex/visualizations/2026/10/06/01a1131b-eac2-7a31-afb4-f219a8dd6471/spq05/review-bundle-1.0.0/review-pages/SPQ-c8b159c449ad0237.html) |
| object_pushing_stacking/predictive | SPQ-6 b 8 f 16 d 02 f 627 a 63 | [focused review](C:/Users/aashraf/.codex/visualizations/2026/10/06/01a1131b-eac2-7a31-afb4-f219a8dd6471/spq05/review-bundle-1.0.0/review-pages/SPQ-6b8f16d02f627a63.html) |
| robotic_arm/clarification | SPQ-b 96046342605 a 210 | [focused review](C:/Users/aashraf/.codex/visualizations/2026/10/06/01a1131b-eac2-7a31-afb4-f219a8dd6471/spq05/review-bundle-1.0.0/review-pages/SPQ-b96046342605a210.html) |
| robotic_arm/counterfactual | SPQ-1 d 4 ba 1 cccb 35 b 59 a | [focused review](C:/Users/aashraf/.codex/visualizations/2026/10/06/01a1131b-eac2-7a31-afb4-f219a8dd6471/spq05/review-bundle-1.0.0/review-pages/SPQ-1d4ba1cccb35b59a.html) |
| robotic_arm/direct | SPQ-6 ebb 79 bba 4 b 93301 | [focused review](C:/Users/aashraf/.codex/visualizations/2026/10/06/01a1131b-eac2-7a31-afb4-f219a8dd6471/spq05/review-bundle-1.0.0/review-pages/SPQ-6ebb79bba4b93301.html) |
| robotic_arm/explanation | SPQ-6 b 3 e 7 a 3 e 1475 c 5 bb | [focused review](C:/Users/aashraf/.codex/visualizations/2026/10/06/01a1131b-eac2-7a31-afb4-f219a8dd6471/spq05/review-bundle-1.0.0/review-pages/SPQ-6b3e7a3e1475c5bb.html) |
| robotic_arm/predictive | SPQ-ac 12 d 9 f 615562961 | [focused review](C:/Users/aashraf/.codex/visualizations/2026/10/06/01a1131b-eac2-7a31-afb4-f219a8dd6471/spq05/review-bundle-1.0.0/review-pages/SPQ-ac12d9f615562961.html) |
| tethered_load/clarification | SPQ-fb 1 cf 7 f 523 b 394 d 0 | [focused review](C:/Users/aashraf/.codex/visualizations/2026/10/06/01a1131b-eac2-7a31-afb4-f219a8dd6471/spq05/review-bundle-1.0.0/review-pages/SPQ-fb1cf7f523b394d0.html) |
| tethered_load/counterfactual | SPQ-9 d 4 fc 49 f 4110000 d | [focused review](C:/Users/aashraf/.codex/visualizations/2026/10/06/01a1131b-eac2-7a31-afb4-f219a8dd6471/spq05/review-bundle-1.0.0/review-pages/SPQ-9d4fc49f4110000d.html) |
| tethered_load/direct | SPQ-6217 b 09788164 d 28 | [focused review](C:/Users/aashraf/.codex/visualizations/2026/10/06/01a1131b-eac2-7a31-afb4-f219a8dd6471/spq05/review-bundle-1.0.0/review-pages/SPQ-6217b09788164d28.html) |
| tethered_load/explanation | SPQ-228 f 7 fa 17026 d 9 bb | [focused review](C:/Users/aashraf/.codex/visualizations/2026/10/06/01a1131b-eac2-7a31-afb4-f219a8dd6471/spq05/review-bundle-1.0.0/review-pages/SPQ-228f7fa17026d9bb.html) |
| tethered_load/predictive | SPQ-f 9795 cdcb 057427 f | [focused review](C:/Users/aashraf/.codex/visualizations/2026/10/06/01a1131b-eac2-7a31-afb4-f219a8dd6471/spq05/review-bundle-1.0.0/review-pages/SPQ-f9795cdcb057427f.html) |

Remaining action: assign R1/R2/R3 to the three humans separately and obtain their
independent original submissions before discussion. Human scientific judgments,
quality/acceptance/agreement, adjudication and any proposed corrections remain
uncollected. Do not distribute the organizer archive as a blinded review bundle.
No answering-model benchmarks, full enriched release, merge or push occurred.

---

## Historical pre-authorization preparation report (preserved)

# SPQ05 preparation and explicit shortfall — 6 October 2026

Status: **implemented_pending_validation; formal human review is blocked**.
Complete formal packets: **0/140**, shortfall140. No final140-item manifest,
formal focused extraction or assigned140-row forms are claimed. No human ratings.
The requested protocol, candidate ordering, no-call preflight, focused extraction
and rating-import tooling, guide, analysis specification and provenance supplement
are prepared. Additional resources are genuinely required before live execution.

Branch `simphysqa-spq05`, existing worktree
C:/Users/aashraf/.codex/worktrees/simphysqa/phi-jepa.
Fetched current origin/main and branched from
`ff2fe26d178883a2cbc68938d661bb157342b5fc`; main unchanged. Initial producer33fd8f0;
accepted preparation1.0.1 producer0ff61ad (full SHA in protocol.json). Final delivery
commit is the commit containing this report; its exact full SHA is recorded in
external delivery.json and the final handoff. No merge/push or answering benchmark.
AGENTS.md is unchanged; explicit SPQ05 instruction supersedes its historical
calibration/review-only limits. Historical docs and artifacts are preserved.

## Behavior and limits

Archived the complete [SPQ05 instruction](../prompts/SPQ05_formal_audit.md).
[Protocol1.0.1](../simphysqa/formal_protocol.md),
[guide1.0.0](../simphysqa/formal_reviewer_guide.md),
[analysis1.0.0](../simphysqa/formal_analysis.md) freeze focused scope, missingness,
random processing/reserve rules, unchanged outcome eligibility, scorer-disjoint
clarification, separate admission/replay, source/privacy and rating procedures.
No separate20-item calibration and no reviewer identity mapping. All three slots
will inspect the same140 items independently,20 cells of7,420 ratings.

Verified actual source frame:11,105 records/6,340 groups/6,340 shards. Excluding
all20 authoritative inspected groups leaves6,320 source groups. All56 enriched
development items are excluded; none counts toward formal readiness. Random group
ordering, disjoint family pools, uniform random source question/group and
same-cell reserves yield140 primary plus140 reserve source candidates; every group
is distinct. Candidate IDs/source sample IDs are not final family/packet identities.
All280 candidates remain pending family qualification/budget, not accepted items.
Clarification eligibility attrition remains **unmeasured**, never zero by assumption.

Focused extraction uses actual exported keys and preserves original typed
global_context, trajectory text/bindings, question/family, state context,
state-ID-joined timestamp text, measurements/relations, full repeated linked events,
matching/description bindings and public schedule/controller declarations. It
reports missing fields explicitly. Authored clarification, recorded reply and
initial/resolved views have separate labels. Gold and extra verification are
auditor-only links outside the primary JSON/prose scope; generator identity is
omitted from focused fields. The software check contains56 excluded development
extractions,616 public states/616 state-event links and46,620 resolved bindings;
its56-row R1/R2/R3 forms are blank, identically assigned and explicitly development-only.
Header-only preparation templates are not formal reviewer forms.

Import validates original assignment list, phase/reviewer slot, packet hashes,
criteria/categories/locations/comments, contradictions, omitted/duplicate rows
and duplicate reviewer submissions. Blank imports collect0 and cannot create a
collected submission. Original CSV bytes and normalized JSON are exclusive-created;
adjudication/corrections live separately. Formal import requires a140-identity freeze.

The analysis plan specifies balanced-design acceptance, missing-rating bounds,
complete-triplet empirical Fleiss kappa, marginal/raw agreement diagnostics and
80% stratified whole-item bootstrap intervals (10,000 replicates, seed20261006).
It preserves the5.532-percentage-point conditional planning-power discrepancy,
distinguishes that fixed-p model from empirical Fleiss, and claims neither achieved
power nor subgroup power. No actual rating analysis has run; numerical analysis
implementation is pending ratings under this frozen specification.

## Resource preflight and blocker

Historical ceiling: annotation initial16/total32/USD5/4,200s; prior usage16 initial,
16 attempts, retained estimatedUSD.522767. Original simulation ceiling32/1,800s;
prior usage32. Remaining initial requests/simulation executions: **0/0**.
No old allowance was silently renewed or expanded; credentials were not opened.

| Request scope | Initial payloads | Input-token bound | Output-token cap | Historical full reservations |
|---|---:|---:|---:|---:|
| Primary140 |140|1,660,812|286,720|USD28.07692|
| All primary/reserve280 |280|3,321,482|573,440|USD56.15242|

Model/config: historical gpt-5.6-sol, medium,2,048 output tokens,120s timeout,
omitted temperature/seed, default tier, store=false/tools=[], prompt/schema1.0.0.
No distinct immutable snapshot is inferred. Prepared exact observed-only payloads
are unexecuted. Twice-initial reservations areUSD56.15384/112.30484 **before repair
feedback**, not complete all-retry upper bounds or expected invoice spend. Historical
October4 pricing must be refreshed before live requests. First140 require56
CF/explanation pairs ×4 coarse/fine factual/omission executions=224; including28
clarification pairs gives336, all280 candidates at most672. Matching verified
saved evidence can reduce solves, but the development pairs cannot count formally.

Asked for the missing explicit additional ceilings:280 initial/560 total annotation
attempts,USD125,7M input/1,146,880 output tokens,2h annotation work;672 simulations,
180s/execution,1h total. This is a pending proposal, **not authorized execution**.
The live runner must be adapted/qualified within that explicit budget before use;
old SPQ01/SPQ02 executors retain their hard-coded ceilings. See
[precise blocker](SPQ05_blocker.md). No mandatory per-item approval gate is introduced.

New annotation calls/simulations/answering calls/spend/ratings: **0/0/0/USD0/0**.
Bounded offline CPU verification only. Full release regeneration/enrichment did not run.

## Actual commands and verification

PowerShell paths used throughout:

```powershell
$Python='C:/Users/aashraf/.codex/visualizations/2026/10/04/01a10902-e2dc-7390-827b-382d2692622c/merge-review/cpu-venv/Scripts/python.exe'
$Prior='C:/Users/aashraf/.codex/visualizations/2026/10/04/01a10902-e2dc-7390-827b-382d2692622c'
$Audit='C:/Users/aashraf/.codex/visualizations/2026/10/06/01a1131b-eac2-7a31-afb4-f219a8dd6471/spq05'
$env:PYTHONPATH=(Join-Path (Get-Location) 'src')
$env:PYTHONDONTWRITEBYTECODE='1'
git fetch origin main
git switch -c simphysqa-spq05 origin/main
& $Python -m unittest discover -s tests -p test_formal_audit.py -v
& $Python -m simphysqa.formal_sampling --inventory "$Prior/spq01/inventory-final" --artifacts $Prior --output "$Audit/preparation-1.0.1"
& $Python -m simphysqa.focused_audit check-saved-extraction --artifacts $Prior --output "$Audit/development-extraction-check-1.0.0"
& ./scripts/simphysqa_spq04.ps1 -Mode check -Python $Python -Artifacts $Prior -SourceData 'C:/Users/aashraf/Desktop/Work/phi-jepa/phi-jepa/dataset-runs/release-four-domain-v1'
$env:SIMPHYSQA_FOUNDATION_ARTIFACTS=$Prior
& $Python -m unittest discover -s tests -p test_foundation.py -v
& $Python scripts/simphysqa_formal_archive.py --previous "$Prior/spq04/prompt-archive-1.0.7" --preparation "$Audit/preparation-1.0.1" --check "$Audit/development-extraction-check-1.0.0" --output "$Audit/prompt-archive-supplement-1.0.0"
& $Python scripts/simphysqa_verify_formal_preparation.py --root $Audit --prior $Prior
```

Initial prepare1.0.0 was also run and is preserved. Resume identity was tightened
to retain its scientific producer across report-only commits; new1.0.1 root freezes
the corrected code/config while preserving identical candidate ordering.
Preparation, extraction and archive commands were rerun on their **actual saved
outputs**, rather than a synthetic resume. Every indexed byte must match; no new
calls/solves. Exact resume evidence is in external resume-verification.json.

Targeted11 tests passed. Integration suite:131 tests in218.628s,OK with2 skipped
classes (foundation artifact variable missing and optional pinned simulator runtime).
Separate foundation run with the actual configured artifacts:4 tests in1.206s,OK,
covering the previously omitted3 saved-foundation tests. Simulator runtime class
(six methods), simulator-specific tests, GPU tests and audit numerical planning
simulation were not rerun; no such coverage is claimed. Additional source/extraction
verification passes all6,340 source shards and62 old manifests,5,002 indexed file
checks (with overlap),280 candidate uniqueness/exclusions/allocation,616 exact
state/timestamp/event extractions and all three zero-rating blank test forms.

Release manifest SHA256:
`ff339e8d282593fb0688158e2a410e197cfe4c357ea349fa0fbb60b88b771fdb`.
Frozen protocol file SHA256:
`847a0ef94145236ca936c8e730cd75b3fef4f5ab350380317f5a89f88b17d85a`.
Preparation manifest:
`726c04a019ef5690ac4b34666e7edcea95f2d51d0400bfad93c826771a293315`.
Focused development-check manifest:
`1cbf55055f0a15c6e594a2d3bfd4d9440c7bffe5eda36796a974eb879115a506`.
All other file hashes and resource accounting are in the linked manifests/index.

## Inspectable delivery and next step

New external root: `$Audit` above. The preparation index explicitly says review
blocked,0/140 packets. `preparation-1.0.1` contains protocol, source-frame/file
hashes,280 ordered candidates, eligibility/failure ledger JSON/JSONL,280 unexecuted
requests, preflight, shortfall, frozen guide/analysis and header-only templates.
`development-extraction-check-1.0.0/index.html` links all56 labeled development
examples with separate optional private evidence and blank test forms.
`prompt-archive-supplement-1.0.0/file-generation-index.json` indexes469 new files,
inherits54 sealed prior files and16 historical executed request lineages read-only,
and distinguishes reuse/deterministic generation from unexecuted requests.
The tracked [SPQ05 archive supplement](../simphysqa/prompt_archive/SPQ05/README.md)
links this new index without changing the prior sealed archive.

Required next step: resolve only the additional resource ceilings, refresh provider
preflight and qualify a budget-aware live runner, then process frozen ranks with
all failure/rejection/replacement evidence. Complete family/answer annotations,
qualify clarification witnesses, validate/freeze140 complete private packets and
separate public inputs, export formal focused extraction and identical140-row
R1/R2/R3 forms. If rules/budget exhaust before7/cell, preserve the shortfall.
Human review cannot begin yet. No assumption of eventual qualification/quality.

Inspectable software examples (excluded from formal sampling):
[predictive development extraction](C:/Users/aashraf/.codex/visualizations/2026/10/06/01a1131b-eac2-7a31-afb4-f219a8dd6471/spq05/development-extraction-check-1.0.0/items/SPQ-1273c770742a651a.html),
[arm clarification stages](C:/Users/aashraf/.codex/visualizations/2026/10/06/01a1131b-eac2-7a31-afb4-f219a8dd6471/spq05/development-extraction-check-1.0.0/items/SPQ-c1dfecaab1117e9f.html),
[driving clarification stages](C:/Users/aashraf/.codex/visualizations/2026/10/06/01a1131b-eac2-7a31-afb4-f219a8dd6471/spq05/development-extraction-check-1.0.0/items/SPQ-0d7e50ae23454fb0.html).
Each separates focused fields and optional private evidence. No formal item is illustrated.

Automatic approval review rejected the initial combined installation because it
included an AGENTS.md rewrite and unchecked overwrites. No part executed. A safer
exclusive-create install of verified-absent files succeeded; later edits used
explicit SHA256 guards. AGENTS.md remains byte-identical to main. This restriction
does not block the authorized preparation or account for the live-budget shortfall.
