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
