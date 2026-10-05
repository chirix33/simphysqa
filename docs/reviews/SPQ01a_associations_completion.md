# SPQ01a bidirectional association export completion

Branch simphysqa-naacl, parent 05a546623a6f71758efeb78001dcf296568e7ef3.
Finalized commit is in the external association delivery receipt. Main/base remains
7dd4a64e90cfb18be743503ac8345cabf2f6e28b. Scope is the requested derived representation.

New export_version **simphysqa-associations/1.0.1** adds linked_events to each
public state and linked_states to each full known-event definition. Compact entries
share canonical link IDs, relationships and evidence. Between-state associations
use a separate array with ordered endpoint IDs and gap-only relationships. Strict
schema/semantic checks reject dangling/duplicate/disagreeing/noncanonical links,
recursive embeddings, stale version hashes and changed physical data. Source QA
records/references, all annotation text, measurements, units/frames and .2 s
cutoffs are preserved. Canonical SPQ01a interval/point/controller rules are untouched.

The new CLI shares the same projection with audit packets and baseline inputs.
Existing export APIs remain backward compatible; association_version explicitly
selects the new representation. Packet identities include the derived export
version; QA sample IDs and reference values are unchanged. Organizer identity/
private verification stay private, and all baseline requests remain tool-free.

**59 offline tests passed** in 89.189 s (46 retained plus 13 association tests).
Tests cover referential integrity, uniqueness, both-direction agreement, canonical
authority, compact shapes, source recovery, private isolation, interval/point/phase
semantics, gap-only endpoint associations, malformed/stale values and saved
packet/baseline consistency, blank ratings and resume. Synthetic schedule fixtures
are labeled software tests, not measured physical examples.

Actual saved exports: 32 public QA views and audit packets, three separate blank
reviewer forms and 288 prepared public requests for nine conditions. All forms
import zero ratings /32 blanks. 352 forward plus 352 reverse entries correspond to
176 pairs after trajectory deduplication, all scheduled_future; no real active or
between-state association coverage exists in these observation windows. The gap
is unchanged from SPQ01a and tested synthetically without expanding cutoffs.

Actual resume preserved all **122 output-file hashes**. All **140 prior SPQ01a
output files** were byte-verified unchanged; all **214 SPQ01 indexed files** verified.
Copied canonical organizer QA JSONL has exactly the source bytes/SHA256
f519f4e60b57379f7fc17fa2f96da2fcebd1615478b5e5cfa9768fd69cd3022e.
New simulations/model calls/spend: **0 /0 /$0**. Previous estimated annotation
spend $.522767 remains historical accounting; no additional charge is introduced.
No human annotation quality/acceptability/agreement result exists.

## Artifacts

New output: C:/Users/aashraf/.codex/visualizations/2026/10/04/01a10902-e2dc-7390-827b-382d2692622c/spq01a/associations-1.0.1; retained source: C:/Users/aashraf/.codex/visualizations/2026/10/04/01a10902-e2dc-7390-827b-382d2692622c/spq01a/event-language-2.0.0.

- [Version/hash manifest](C:/Users/aashraf/.codex/visualizations/2026/10/04/01a10902-e2dc-7390-827b-382d2692622c/spq01a/associations-1.0.1/manifest.json)
- [All public views](C:/Users/aashraf/.codex/visualizations/2026/10/04/01a10902-e2dc-7390-827b-382d2692622c/spq01a/associations-1.0.1/public-qa.json), public-items/ (32 individual files)
- [Deduplicated association index](C:/Users/aashraf/.codex/visualizations/2026/10/04/01a10902-e2dc-7390-827b-382d2692622c/spq01a/associations-1.0.1/event-state-associations.json)
- [Automatic verification](C:/Users/aashraf/.codex/visualizations/2026/10/04/01a10902-e2dc-7390-827b-382d2692622c/spq01a/associations-1.0.1/verification/checks.json)
- audit-development/packets/, forms/R1.csv, R2.csv, R3.csv and organizer-private/
- baseline-requests/ (nine conditions; 288 requests; no answering execution)
- qa-records.jsonl (unchanged canonical organizer/private source records)
- [59-test log](C:/Users/aashraf/.codex/visualizations/2026/10/04/01a10902-e2dc-7390-827b-382d2692622c/association-final-tests.log)
- [Saved resume and prior-file verification](C:/Users/aashraf/.codex/visualizations/2026/10/04/01a10902-e2dc-7390-827b-382d2692622c/association-final-saved-verification.json)
- [Projection/schema specification](../simphysqa/associations.md)

| Domain | Public example | Audit packet |
| --- | --- | --- |
| robotic_arm | [JSON](C:/Users/aashraf/.codex/visualizations/2026/10/04/01a10902-e2dc-7390-827b-382d2692622c/spq01a/associations-1.0.1/public-items/01863fd6b9e584c3a5f506ed7013dd80.json) | [HTML](C:/Users/aashraf/.codex/visualizations/2026/10/04/01a10902-e2dc-7390-827b-382d2692622c/spq01a/associations-1.0.1/audit-development/packets/SPQ-88052b9d4c814efa.html) |
| driving | [JSON](C:/Users/aashraf/.codex/visualizations/2026/10/04/01a10902-e2dc-7390-827b-382d2692622c/spq01a/associations-1.0.1/public-items/e52c5e8391589681cf355d960fb8f185.json) | [HTML](C:/Users/aashraf/.codex/visualizations/2026/10/04/01a10902-e2dc-7390-827b-382d2692622c/spq01a/associations-1.0.1/audit-development/packets/SPQ-fa103f4b9e4f106b.html) |
| object_pushing_stacking | [JSON](C:/Users/aashraf/.codex/visualizations/2026/10/04/01a10902-e2dc-7390-827b-382d2692622c/spq01a/associations-1.0.1/public-items/9ca52411dc610e46e81bafdb308f500b.json) | [HTML](C:/Users/aashraf/.codex/visualizations/2026/10/04/01a10902-e2dc-7390-827b-382d2692622c/spq01a/associations-1.0.1/audit-development/packets/SPQ-a6b28dd0e1d12e91.html) |
| tethered_load | [JSON](C:/Users/aashraf/.codex/visualizations/2026/10/04/01a10902-e2dc-7390-827b-382d2692622c/spq01a/associations-1.0.1/public-items/222d4fd6c0e00e05726c1c1c94fa2d37.json) | [HTML](C:/Users/aashraf/.codex/visualizations/2026/10/04/01a10902-e2dc-7390-827b-382d2692622c/spq01a/associations-1.0.1/audit-development/packets/SPQ-418ccb470cefe9a5.html) |

## Exact commands

Reuse the existing CPU environment; no installation, download or provider access.
All output paths are configurable and external to the tracked worktree.

~~~powershell
Set-Location 'C:/Users/aashraf/.codex/worktrees/simphysqa/phi-jepa'
$cpuPython = 'C:/Users/aashraf/.codex/visualizations/2026/10/04/01a10902-e2dc-7390-827b-382d2692622c/simphysqa-venv/Scripts/python.exe'
$source = 'C:/Users/aashraf/.codex/visualizations/2026/10/04/01a10902-e2dc-7390-827b-382d2692622c/spq01a/event-language-2.0.0'
$output = 'C:/Users/aashraf/.codex/visualizations/2026/10/04/01a10902-e2dc-7390-827b-382d2692622c/spq01a/associations-1.0.1'
$env:PYTHONDONTWRITEBYTECODE = '1'
$env:PYTHONPATH = 'C:/Users/aashraf/.codex/worktrees/simphysqa/phi-jepa/src'
$env:SIMPHYSQA_DATA_ROOT = 'C:/Users/aashraf/Desktop/Work/phi-jepa/phi-jepa/dataset-runs/release-four-domain-v1'
$env:SIMPHYSQA_DEVELOPMENT_RECORDS = 'C:/Users/aashraf/.codex/visualizations/2026/10/04/01a10902-e2dc-7390-827b-382d2692622c/spq01/selection/predictive-records.jsonl'
$env:SIMPHYSQA_SPQ01_QA = 'C:/Users/aashraf/.codex/visualizations/2026/10/04/01a10902-e2dc-7390-827b-382d2692622c/spq01/development/qa-records.jsonl'
$env:SIMPHYSQA_SPQ01A_ROOT = $source
& $cpuPython -m unittest discover -s tests -p 'test*.py' -v
& $cpuPython -m simphysqa.export_associations --source $source --output $output
# Same command verifies/resumes without replacing completed files.
& $cpuPython -m simphysqa.export_associations --source $source --output $output
~~~

The saved hash comparison also executed association_final_saved_check.py from the
external artifact-tools directory (receipt outside the export). Existing source
records may be loaded with the original dataset loader; indexed public views are
validated with associations.validate_view(original_public_view, exported_view).
strip_associations recovers the original public input without changing source data.

The initial development export 1.0.0 is also retained; final 1.0.1 adds strict
canonical JSON comparisons to reject Boolean/number type substitutions.

No additional scientific or machine prerequisite blocks this export. Real active
coverage, independent human review, model qualification and subsequent
counterfactual/explanation/clarification work remain pending. No formal sample,
new annotation prose, physical simulation or benchmark result was produced.

## Grounded event-description follow-up
[Export 1.1.1 completion/examples/verification](SPQ01a_event_descriptions_completion.md)
adds shared public event prose and independent evidence. The historical association
export findings above remain unchanged.
