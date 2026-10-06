# SPQ03 completion — 6 October 2026

Branch simphysqa-naacl; accepted base 10ace28d6a9642d303c7321b53c2d0e49a68c03f.
Worktree C:/Users/aashraf/.codex/worktrees/simphysqa/phi-jepa. Final commit is in
the external spq03/delivery.json receipt. Main and historical data stay unchanged.
The complete current user instruction is docs/prompts/SPQ03_explanation_qa.md.

## Completed scope and scientific limits

Eight explanation QA completed, zero failed, zero pending; two per domain, reusing
every frozen SPQ02 pair and selected target. These explicitly ask for an explanation
of changed control, fixed conditions, supplied selected outcome, supported simulator
comparison and uncertainty. Three unchanged Booleans and two nonzero within-
tolerance contrasts remain; no replacement or more dramatic outcome was selected.

New external export spq03/explanations-1.0.0: eight organizer records, eight public
views, eight JSON/HTML packets, three independent blank reviewer forms and 72
prepared requests across nine conditions. item-index.json links all new items to
the accepted 40-item export and their three related QA per selected group.
Established .2 s prefixes, exact target/tolerances/frames/time, group/split identities,
source records, formal exclusions, answer annotations 1.0.3 and association 1.1.1
are preserved. No definitive formal sample was selected/exported.

The new supplied_comparison explicitly discloses only the selected factual and
omission simulator readouts. It is not an observation, a longer prefix, or a change
to existing predictive/counterfactual input. Gold explanations/traces, rollouts,
receipts and generator identity stay private. All requests use tools=[] and the
common versioned explanation JSON response contract. No models were executed.

References/claim-level bindings use real saved controller/source implementation,
matched outcomes and exact replay/separate admission receipts. Trace steps connect
each supported claim to factual/alternative namespaces, state/run identity and
configuration/evidence. Solver details and receipts remain private. There are no
new physical measurements, simulation verifications or mechanism demonstrations.
New simulations/model calls/spend: 0/0/$0. The existing 32 saved SPQ02 executions
are evidence, not newly rerun. Human explanation judgments remain uncollected.

## Rubric/evaluation and provenance

[Contract](../simphysqa/explanation_qa.md) and
[rubric](../../configs/simphysqa/explanation_rubric.json), matched-explanation-rubric/1.0.0.
Six human criteria identify required supported claims, acceptable paraphrases,
contradictions/unsupported claims and explanatory adequacy. Automatic evaluator
explanation-factual-components/1.0.0 covers only six structured factual components:
intervention identity, fixed-condition declarations, two selected values and two
comparison facts. It does not grade prose semantics, quality or adequacy; overall
explanation correctness stays null. No exact-text/keyword/MSE explanation score.
All missing/invalid/failed/abstained results remain in future metric denominators.

[Archive entry](../simphysqa/prompt_archive/README.md),
[consolidated catalogue](../simphysqa/prompt_archive/catalogue.md) and
[per-file index](../simphysqa/prompt_archive/file-generation-index.json).
Archive 1.0.6 inventories 1,668 files/5,704 record mappings, with separate deterministic
explanation procedures, prepared answering prompts, reused language and embedded
accepted parents. All sixteen executed SPQ01 requests are recovered exactly and
byte-identical to prior archive payloads; none newly executed/reconstructed.
Original preliminary association 1.1.0/event-description 1.0.0 source remains
unrecoverable and labeled, not replaced by invented historical code.

Internal archive 1.0.5 is preserved. Its field-level parent links for new gold QA
were made more precise in 1.0.6 (matched counterfactual parent, rather than the
measurement-language source). QA outputs needed no change. A strengthened focused
test checks these links and reused-language request identity separately.

## Commands actually run

From the SimPhysQA worktree in PowerShell, using the existing qualified CPU runtime:

```powershell
$taskArtifacts='C:/Users/aashraf/.codex/visualizations/2026/10/04/01a10902-e2dc-7390-827b-382d2692622c'
$taskPython="$taskArtifacts/simphysqa-venv/Scripts/python.exe"
./scripts/simphysqa_spq03.ps1 -Artifacts $taskArtifacts -Python $taskPython -Mode export
./scripts/simphysqa_spq03.ps1 -Artifacts $taskArtifacts -Python $taskPython -Mode archive
./scripts/simphysqa_spq03.ps1 -Artifacts $taskArtifacts -Python $taskPython -Mode check -SourceData 'C:/Users/aashraf/Desktop/Work/phi-jepa/phi-jepa/dataset-runs/release-four-domain-v1'
& $taskPython "$taskArtifacts/check_spq03.py"
& "$taskArtifacts/resume_spq03.ps1"
```

The full suite ran 106 tests in 121.496 s, OK, with one retained simulator-runtime
class skipped; no simulator installation/run was required. Twelve new saved-data
tests cover frozen selection/lineage, disclosure, target fidelity, claim/step binding
resolution, Boolean history, tamper rejection, all 72 requests, fact/prose coverage
separation, missing/invalid denominators, blank forms, offline construction,
immutable writes and per-file provenance. A final focused run after the archive
parent-link correction covers those tests plus PromptArchiveTests. Logs:
spq03/tests-1.0.0.txt and spq03/final-focused-tests.txt. Probes in these tests are
software fixtures, not model outputs or human ratings. Original-source/preservation
checks verify all eight accepted parent records and historical manifests unchanged.
Blank import: each reviewer has 0 collected /8 blank ratings. Actual byte-preserving
resume and final preservation receipts are spq03/resume.json and preservation.json.

## Four domain examples

Each link includes readable question/reference, structured solution trace and
resolvable private bindings, alongside the fixed explanation rubric:

- [Arm](C:/Users/aashraf/.codex/visualizations/2026/10/04/01a10902-e2dc-7390-827b-382d2692622c/spq03/explanations-1.0.0/audit-development/packets/SPQ-8c099c055a8925ab.html)
- [Driving](C:/Users/aashraf/.codex/visualizations/2026/10/04/01a10902-e2dc-7390-827b-382d2692622c/spq03/explanations-1.0.0/audit-development/packets/SPQ-961f116148674b65.html)
- [Objects](C:/Users/aashraf/.codex/visualizations/2026/10/04/01a10902-e2dc-7390-827b-382d2692622c/spq03/explanations-1.0.0/audit-development/packets/SPQ-366c417f4b732f16.html)
- [Tether](C:/Users/aashraf/.codex/visualizations/2026/10/04/01a10902-e2dc-7390-827b-382d2692622c/spq03/explanations-1.0.0/audit-development/packets/SPQ-b67e0291c9ba03df.html)

[All eight cases](C:/Users/aashraf/.codex/visualizations/2026/10/04/01a10902-e2dc-7390-827b-382d2692622c/spq03/explanations-1.0.0/inspection.html).

## Remaining decisions and work

No additional physical tolerance/frame/solver decision was needed; source evidence
resolved the bounded cases. Human explanation adequacy/quality is unreviewed;
rubric calibration and independent judgments precede empirical explanation-quality
claims. The formal release/annotation/rubric readiness and inferential-analysis
freeze remain separate. Additional models need local artifact/runtime qualification
and a bounded answering experiment before any benchmark or uncertainty estimate.
Clarification QA requires genuine missing information and remains a subsequent
milestone, as do full-release enrichment and separately scoped later observed-event
views/annotation-source comparison. This engineering sample supports no release-wide
quality claim and does not power all domain/question-type subgroups.

Final focused run: 13 tests passed in 14.262 s after the field-parent correction.
Final resume: all 109 export/archive files remained byte-identical; export resume
9.2186861 s, export plus archive 22.158521 s. Final preservation check validates
52 earlier manifests and all sixteen historical request payloads, and regenerates
all 72 requests in memory for exact comparison. No failed item or numerical run
was substituted. Internal archive 1.0.5 remains preserved alongside current 1.0.6.
