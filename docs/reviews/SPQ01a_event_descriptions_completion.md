# SPQ01a grounded event descriptions completion

Parent 433c64186555fdc99f17261c069a2dd4b334a11e; branch simphysqa-naacl.
Final commit is recorded in the external event-description delivery receipt.
Main remains 7dd4a64e90cfb18be743503ac8345cabf2f6e28b and is preserved.

Export/schema simphysqa-associations/1.1.1 and deterministic event-description
renderer 1.0.1 add canonical shared text, separate public description bindings and
explicit semantic status to known events, state linked_events and gap associations.
Original generic description and inherited trajectory/timestamp text are preserved.
Reverse indexes and canonical temporal links remain unchanged. Source recovery
removes all derived fields and checks canonical JSON types, QA identities, physical
values and observation cutoffs. No private data enters description construction.

69 offline tests passed in 94.877 s (59 retained and ten targeted description tests).
They cover all four public controller types, additive/base distinctions, maximum
versus realized braking torque, direct/context entities, signed support phases,
unresolved laws/frames, point semantics, independent public description evidence,
altered/missing/consistently forged copies, display rounding versus exact matching,
stale renderer/display/schema hashes, source recovery, privacy and packet/baseline
consistency. Synthetic fixtures are software checks, not simulated research data.

Saved export: 32 public QA and audit packets, three blank forms, 288 prepared
baseline requests. All forms still import zero ratings /32 blanks. Sixteen physical
event descriptions: 12 supported_declared_semantics and four arm
limited_unresolved_semantics due to retained world/joint_local frame declarations.
These statuses describe software semantic coverage, not human annotation quality.
352 copied state/event descriptions (176 deduplicated physical pairs) are all
scheduled_future. Real active/gap coverage remains absent with unchanged .2 s
cutoffs; synthetic gap/point cases verify matching description copies separately.

Actual saved resume preserves all 122 final-output file hashes. All 140 original
SPQ01a output files, 122 prior 1.0.0 files and 122 prior 1.0.1 files are byte-checked;
214 indexed SPQ01 files verified unchanged. The preliminary 1.1.0 export (122 files)
is also retained. New simulations/model calls/spend: 0 /0 /$0; historical estimated
annotation spend $.522767 remains unchanged. No benchmark or human result exists.

## Inspectable examples and evidence

| Domain | Public example | Audit packet |
| --- | --- | --- |
| driving | [Public JSON](C:/Users/aashraf/.codex/visualizations/2026/10/04/01a10902-e2dc-7390-827b-382d2692622c/spq01a/associations-1.1.1/public-items/e52c5e8391589681cf355d960fb8f185.json) | [Audit HTML](C:/Users/aashraf/.codex/visualizations/2026/10/04/01a10902-e2dc-7390-827b-382d2692622c/spq01a/associations-1.1.1/audit-development/packets/SPQ-91a690c6ca9ce2a3.html) |
| object_pushing_stacking | [Public JSON](C:/Users/aashraf/.codex/visualizations/2026/10/04/01a10902-e2dc-7390-827b-382d2692622c/spq01a/associations-1.1.1/public-items/9ca52411dc610e46e81bafdb308f500b.json) | [Audit HTML](C:/Users/aashraf/.codex/visualizations/2026/10/04/01a10902-e2dc-7390-827b-382d2692622c/spq01a/associations-1.1.1/audit-development/packets/SPQ-03aa1dd9f5ba30b7.html) |
| robotic_arm | [Public JSON](C:/Users/aashraf/.codex/visualizations/2026/10/04/01a10902-e2dc-7390-827b-382d2692622c/spq01a/associations-1.1.1/public-items/01863fd6b9e584c3a5f506ed7013dd80.json) | [Audit HTML](C:/Users/aashraf/.codex/visualizations/2026/10/04/01a10902-e2dc-7390-827b-382d2692622c/spq01a/associations-1.1.1/audit-development/packets/SPQ-a5d0b4963c1a124a.html) |
| tethered_load | [Public JSON](C:/Users/aashraf/.codex/visualizations/2026/10/04/01a10902-e2dc-7390-827b-382d2692622c/spq01a/associations-1.1.1/public-items/222d4fd6c0e00e05726c1c1c94fa2d37.json) | [Audit HTML](C:/Users/aashraf/.codex/visualizations/2026/10/04/01a10902-e2dc-7390-827b-382d2692622c/spq01a/associations-1.1.1/audit-development/packets/SPQ-4eced0d7971798ee.html) |

[Four-domain descriptions and resolved public evidence](C:/Users/aashraf/.codex/visualizations/2026/10/04/01a10902-e2dc-7390-827b-382d2692622c/event-description-final-examples.json)
include inherited text, new text/status, resolved public source pointer values and packet
paths. [All public QA](C:/Users/aashraf/.codex/visualizations/2026/10/04/01a10902-e2dc-7390-827b-382d2692622c/spq01a/associations-1.1.1/public-qa.json),
[deduplicated canonical description/association index](C:/Users/aashraf/.codex/visualizations/2026/10/04/01a10902-e2dc-7390-827b-382d2692622c/spq01a/associations-1.1.1/event-state-associations.json),
[version/hash manifest](C:/Users/aashraf/.codex/visualizations/2026/10/04/01a10902-e2dc-7390-827b-382d2692622c/spq01a/associations-1.1.1/manifest.json),
[automatic checks](C:/Users/aashraf/.codex/visualizations/2026/10/04/01a10902-e2dc-7390-827b-382d2692622c/spq01a/associations-1.1.1/verification/checks.json) and
[saved resume/prior-output proof](C:/Users/aashraf/.codex/visualizations/2026/10/04/01a10902-e2dc-7390-827b-382d2692622c/event-description-final-saved-verification.json).
The organizer-only qa-records.jsonl has the original exact source bytes/SHA256
f519f4e60b57379f7fc17fa2f96da2fcebd1615478b5e5cfa9768fd69cd3022e.
baseline-requests holds nine condition files; none was executed.

## Exact commands run

Reuse the existing CPU environment. No installation/download/provider access.

~~~powershell
Set-Location 'C:/Users/aashraf/.codex/worktrees/simphysqa/phi-jepa'
$cpuPython = 'C:/Users/aashraf/.codex/visualizations/2026/10/04/01a10902-e2dc-7390-827b-382d2692622c/simphysqa-venv/Scripts/python.exe'
$source = 'C:/Users/aashraf/.codex/visualizations/2026/10/04/01a10902-e2dc-7390-827b-382d2692622c/spq01a/event-language-2.0.0'
$output = 'C:/Users/aashraf/.codex/visualizations/2026/10/04/01a10902-e2dc-7390-827b-382d2692622c/spq01a/associations-1.1.1'
$env:PYTHONDONTWRITEBYTECODE = '1'
$env:PYTHONPATH = 'C:/Users/aashraf/.codex/worktrees/simphysqa/phi-jepa/src'
$env:SIMPHYSQA_DATA_ROOT = 'C:/Users/aashraf/Desktop/Work/phi-jepa/phi-jepa/dataset-runs/release-four-domain-v1'
$env:SIMPHYSQA_DEVELOPMENT_RECORDS = 'C:/Users/aashraf/.codex/visualizations/2026/10/04/01a10902-e2dc-7390-827b-382d2692622c/spq01/selection/predictive-records.jsonl'
$env:SIMPHYSQA_SPQ01_QA = 'C:/Users/aashraf/.codex/visualizations/2026/10/04/01a10902-e2dc-7390-827b-382d2692622c/spq01/development/qa-records.jsonl'
$env:SIMPHYSQA_SPQ01A_ROOT = $source
& $cpuPython -m unittest discover -s tests -p 'test*.py' -v
& $cpuPython -m simphysqa.export_associations --source $source --output $output
# Calls the same export again and compares every saved/prior file hash.
& $cpuPython 'C:/Users/aashraf/.codex/visualizations/2026/10/04/01a10902-e2dc-7390-827b-382d2692622c/event_description_saved_check.py'
~~~

[Full final test log](C:/Users/aashraf/.codex/visualizations/2026/10/04/01a10902-e2dc-7390-827b-382d2692622c/event-description-final-tests.log),
[export preflight/results](C:/Users/aashraf/.codex/visualizations/2026/10/04/01a10902-e2dc-7390-827b-382d2692622c/event-description-final-export.log) and
[saved verification log](C:/Users/aashraf/.codex/visualizations/2026/10/04/01a10902-e2dc-7390-827b-382d2692622c/event-description-final-resume-success.log).

Specification: [event descriptions](../simphysqa/event_descriptions.md).
No machine prerequisite blocks this deterministic export. Resolving arm frame
relationships requires additional scientific/source clarification; they remain
explicitly unresolved. Real active-event coverage, independent reviewers,
alternative annotation-source qualification and counterfactual/explanation/
clarification QA remain pending. No definitive formal sample was exported.
