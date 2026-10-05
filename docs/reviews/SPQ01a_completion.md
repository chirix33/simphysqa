# SPQ01a completion — 5 October 2026

Implemented event-aware public language on simphysqa-naacl in
C:/Users/aashraf/.codex/worktrees/simphysqa/phi-jepa. Accepted parent/base:
6d420b779e0204868fec4c45e26bb1cdcd2b98c7. This report is in the SPQ01a
commit; the finalized SHA is recorded in the external SPQ01a delivery receipt.
Original main/base 7dd4a64e90cfb18be743503ac8345cabf2f6e28b is preserved.
No broad cleanup, simulation regeneration, new QA family or answering-model run.

## Changed behavior

- Public-only deterministic links implement onset inclusion/end exclusion,
  future/active/ended distinctions, separate inter-state intervals and unsampled
  boundaries, overlapping events and declared point-event semantics. Whole states,
  measurements/relations, entities and declared controller information are scanned;
  direct intervention targets and context entities remain distinct.
- Controller-aware claims preserve additive joint pulse/base torque, driving
  maximum brake torque versus realized values, block_1 push target versus block_2
  readout and the tethered support's positive/negative acceleration phases.
  Unknown laws/types remain unresolved instead of guessing application details.
- Measurement prose is retained verbatim. Separate claim-level evidence supports
  every added schedule/controller statement; scheduled active does not verify
  application or causation. Intervening links are separate from endpoint-active
  status; ended intervals do not prove effects ended.
- Annotation contract 2.0.0 / matching rules 1.0.0, schema/prompt/renderer/registry
  hashes and full public-input/original-annotation digests distinguish revised
  caches. Original provider provenance stays organizer-private, with a separate
  deterministic revision record. Strict final-view reconstruction rejects altered
  claims, unsupported evidence, private outcomes, stale versions and links.
- All 32 development QA records/packets and three blank reviewer forms are
  re-exported. Nine baseline conditions receive 288 public prepared requests,
  including revised language and no private references; zero model execution.

See [annotation specification](../simphysqa/event_language.md) and
[consequential decisions](../decisions/SPQ01a_event_language.md).

## Real-data coverage and preservation

| Domain | Trajectories | Observed states /future links | Declared events | Supported declared phases | Active/between links |
| --- | ---: | ---: | ---: | ---: | ---: |
| Robotic arm | 4 | 44 | 4 | 0 | 0 |
| Driving | 4 | 44 | 4 | 0 | 0 |
| Pushing/stacking | 4 | 44 | 4 | 0 | 0 |
| Tethered load | 4 | 44 | 4 | 8 | 0 |

These counts deduplicate the direct/predictive pairs: 16 physical trajectories,
176 observations /176 scheduled-future state–event links and 16 declared events.
The 32 QA views repeat the paired physical inputs (352 timestamp descriptions).
Every observation cutoff remains exactly .2 s. All interventions begin later;
there is **no real active/ended/between-state coverage** in this development set.
Summary schedules and brief final not-yet-started notes report this absence.
No cutoff was expanded. Synthetic fixtures are software tests only.

All 16 predictive references and 16 deterministic direct references, QA IDs,
questions, answer specs, public physical input, source hashes/provenance and
private evidence bindings are equal to SPQ01. Original SPQ01 model provenance
is unchanged. All 214 files indexed by the SPQ01 root manifest verified; that
manifest's byte SHA256 remains
1082e6ffa4281d1015b9c3d7794ccf2dbec2a38844d06499413ff0a5c772f701.

## Accounting and validation evidence

No new API/model requests, attempts, repairs or estimated spend. Reuse meaningful
existing model-generated measurement descriptions and deterministic schedule facts.
Shared allowance remains 16 initial /32 total attempts /USD5. Cumulative 16 initial
/16 total attempts and estimated $.522767, remaining $4.477233; invoice charge is
unconfirmed. The historical gpt-5.6-sol identity/settings stay in organizer-private
provenance; these additions are not attributed to a new model call.

Preflight reports 16 public physical inputs (25,671–43,537 UTF-8 bytes; 520,939
total), 32 QA records, exact versions/non-secret config and a zero request/cost
estimate before execution. No credential lookup or network access is needed.

46 offline behavior tests passed (27 retained +19 SPQ01a; final full run
75.157 seconds). Synthetic fixtures cover onset/end, strict before/after without
epsilon, overlaps, intervals entirely between states, sampled versus unsampled
boundaries, signed controller phases and exact decimal boundaries, unknown laws,
point-event completion semantics and empty intervals. Real checks cover whole-state
target matching, units/frames, all original measurement text and references,
private-input isolation, malformed/stale/leaked claims, strict final views, cache
identity, blank imports and immutable resumption. Tests forbid network connections.
The initial leakage assertion wrongly matched the word reference in an instruction
string; it was corrected to inspect actual public fields, and the final suite passed.

The actual saved export revalidated all 32 final views; all three forms imported
zero ratings /32 blanks each. Actual resume made zero calls and left all 140 revised
output-file hashes identical. All 32 saved reviewer packets were checked for absence
of generator identity/organizer revision provenance. Baseline exports are public-only.

Automatic validation is not human annotation quality, acceptability or agreement.
**No independent reviewer judgments or annotation-quality result exists.**

## Inspectable artifacts

New versioned external root: C:/Users/aashraf/.codex/visualizations/2026/10/04/01a10902-e2dc-7390-827b-382d2692622c/spq01a/event-language-2.0.0.
All original SPQ01 outputs remain at C:/Users/aashraf/.codex/visualizations/2026/10/04/01a10902-e2dc-7390-827b-382d2692622c/spq01.

| Artifact | Location |
| --- | --- |
| Version/hash manifest | [manifest](C:/Users/aashraf/.codex/visualizations/2026/10/04/01a10902-e2dc-7390-827b-382d2692622c/spq01a/event-language-2.0.0/manifest.json) |
| All revised records/items | [QA records](C:/Users/aashraf/.codex/visualizations/2026/10/04/01a10902-e2dc-7390-827b-382d2692622c/spq01a/event-language-2.0.0/qa-records.jsonl); items/ |
| Public views | [public QA](C:/Users/aashraf/.codex/visualizations/2026/10/04/01a10902-e2dc-7390-827b-382d2692622c/spq01a/event-language-2.0.0/public-qa.json) |
| Event–state links and phase derivations | [linkage manifest](C:/Users/aashraf/.codex/visualizations/2026/10/04/01a10902-e2dc-7390-827b-382d2692622c/spq01a/event-language-2.0.0/event-state-linkage.json) |
| Deduplicated real coverage | [coverage](C:/Users/aashraf/.codex/visualizations/2026/10/04/01a10902-e2dc-7390-827b-382d2692622c/spq01a/event-language-2.0.0/coverage.json) |
| Non-secret preflight and budget | [preflight](C:/Users/aashraf/.codex/visualizations/2026/10/04/01a10902-e2dc-7390-827b-382d2692622c/spq01a/event-language-2.0.0/preflight.json), organizer-private/accounting.json |
| Whole public generator inputs | generator-inputs/ (16 versioned prepared views; no model calls) |
| Development packets /blank forms | audit-development/packets/; forms/R1.csv, R2.csv, R3.csv; organizer-private/identity-key.json |
| Nine-condition public requests | baseline-requests/ (288 prepared requests, zero answering calls) |
| Final-view/preservation checks | [checks](C:/Users/aashraf/.codex/visualizations/2026/10/04/01a10902-e2dc-7390-827b-382d2692622c/spq01a/event-language-2.0.0/verification/checks.json) |
| Before/after text and packet index | [before-after](C:/Users/aashraf/.codex/visualizations/2026/10/04/01a10902-e2dc-7390-827b-382d2692622c/spq01a/event-language-2.0.0/before-after.json) |
| Saved-output resume/blinding/old preservation | [saved verification](C:/Users/aashraf/.codex/visualizations/2026/10/04/01a10902-e2dc-7390-827b-382d2692622c/spq01a/saved-output-verification.json) |
| Full offline tests | [46-test log](C:/Users/aashraf/.codex/visualizations/2026/10/04/01a10902-e2dc-7390-827b-382d2692622c/spq01a-final-tests.log) |

Every added statement has separate claim bindings in packet language_annotations:
measurement, event_schedule and controller_definition (controller_phase and
between_saved_states in applicable software fixtures). In the real arm example,
the additive claim binds /controller/equations/0 and /known_events/0/parameters/0;
base torque binds /controller/controls/0 plus the declared law/event parameter.
The driving limit binds /controller/parameters/1 and the equation/event; pushing
binds the block_1 force parameter; tethered phase derivations bind its acceleration
parameter, onset/end and the declared .1 s phase law. Timestamp schedule claims
also bind the relevant observed state ID/time. All pointers resolve publicly.

| Domain | Before SPQ01 | After SPQ01a |
| --- | --- | --- |
| Robotic arm | [before](C:/Users/aashraf/.codex/visualizations/2026/10/04/01a10902-e2dc-7390-827b-382d2692622c/spq01/development/audit-development/packets/SPQ-bab3341a45950585.html) | [after](C:/Users/aashraf/.codex/visualizations/2026/10/04/01a10902-e2dc-7390-827b-382d2692622c/spq01a/event-language-2.0.0/audit-development/packets/SPQ-21332c80bfa2debc.html) |
| Driving | [before](C:/Users/aashraf/.codex/visualizations/2026/10/04/01a10902-e2dc-7390-827b-382d2692622c/spq01/development/audit-development/packets/SPQ-aab38b4bda710538.html) | [after](C:/Users/aashraf/.codex/visualizations/2026/10/04/01a10902-e2dc-7390-827b-382d2692622c/spq01a/event-language-2.0.0/audit-development/packets/SPQ-02eb440c5f3860d5.html) |
| Pushing/stacking | [before](C:/Users/aashraf/.codex/visualizations/2026/10/04/01a10902-e2dc-7390-827b-382d2692622c/spq01/development/audit-development/packets/SPQ-d6d754b68497c8a4.html) | [after](C:/Users/aashraf/.codex/visualizations/2026/10/04/01a10902-e2dc-7390-827b-382d2692622c/spq01a/event-language-2.0.0/audit-development/packets/SPQ-40dc70628b821c09.html) |
| Tethered load | [before](C:/Users/aashraf/.codex/visualizations/2026/10/04/01a10902-e2dc-7390-827b-382d2692622c/spq01/development/audit-development/packets/SPQ-3fdb49f01ac9ba76.html) | [after](C:/Users/aashraf/.codex/visualizations/2026/10/04/01a10902-e2dc-7390-827b-382d2692622c/spq01a/event-language-2.0.0/audit-development/packets/SPQ-3f703f76148a2a95.html) |

## Exact executed commands

The existing CPU environment was reused; no new packages or models were downloaded.
Re-run at this pinned source revision with the retained external SPQ01 input files.
A different destination produces another offline versioned export; the same
destination validates/resumes without overwriting completed output. Preserve source
artifacts; interrupted packaging without a ready manifest is detected and retained
for explicit recovery, not erased automatically.

~~~powershell
Set-Location 'C:/Users/aashraf/.codex/worktrees/simphysqa/phi-jepa'
$cpuPython = 'C:/Users/aashraf/.codex/visualizations/2026/10/04/01a10902-e2dc-7390-827b-382d2692622c/simphysqa-venv/Scripts/python.exe'
$previous = 'C:/Users/aashraf/.codex/visualizations/2026/10/04/01a10902-e2dc-7390-827b-382d2692622c/spq01'
$revised = 'C:/Users/aashraf/.codex/visualizations/2026/10/04/01a10902-e2dc-7390-827b-382d2692622c/spq01a/event-language-2.0.0'
$env:PYTHONDONTWRITEBYTECODE = '1'
$env:PYTHONPATH = 'C:/Users/aashraf/.codex/worktrees/simphysqa/phi-jepa/src'
$env:SIMPHYSQA_DATA_ROOT = 'C:/Users/aashraf/Desktop/Work/phi-jepa/phi-jepa/dataset-runs/release-four-domain-v1'
$env:SIMPHYSQA_DEVELOPMENT_RECORDS = "$previous/selection/predictive-records.jsonl"
$env:SIMPHYSQA_SPQ01_QA = "$previous/development/qa-records.jsonl"

& $cpuPython -m unittest discover -s tests -p 'test*.py' -v
& $cpuPython -m simphysqa.spq01a --records $env:SIMPHYSQA_SPQ01_QA --prior-summary "$previous/annotation-job/summaries/002.json" --prior-packets "$previous/development/audit-development" --output $revised
# Repeat the same command to validate/resume with unchanged completed-file hashes.
& $cpuPython -m simphysqa.spq01a --records $env:SIMPHYSQA_SPQ01_QA --prior-summary "$previous/annotation-job/summaries/002.json" --prior-packets "$previous/development/audit-development" --output $revised

# Additional executed saved-file integrity /blinding /old-output check:
& $cpuPython 'C:/Users/aashraf/.codex/visualizations/2026/10/04/01a10902-e2dc-7390-827b-382d2692622c/spq01a_saved_check.py'
~~~

Portable setup remains in root README.md. New active files: events.py (links/law
registry), event_language.py and its strict JSON schema (claims/renderer/validation),
spq01a.py (offline/resumable export), annotation_spq01a.json (zero-call policy),
test_spq01a.py (real preservation plus labeled fixtures), this specification/report.
Existing dataset loader, packet/rating and evaluation interfaces are retained.

## Remaining work and decisions

1. Obtain real admitted observed views that overlap interventions in a subsequent
   development milestone, while respecting each QA cutoff. Broaden multi-entity
   language and known-law/event coverage; unknown semantics need explicit contracts.
2. Independent human calibration/review and rubric revision remain pending. No
   definitive formal sample was exported; allocation/power reconciliation and
   group exclusions from SPQ01 are unchanged.
3. Retain the source arm event/base-control frame distinction. Any physical frame
   reconciliation needs an explicit source/schema decision and verification;
   this milestone performs no conversion or realized-total-control inference.
4. Pin the alternative annotation source and matched/blinded protocol separately
   for the revised annotation version; no comparison calls/results here.
5. Counterfactual references need matched interventions/verified re-simulation;
   explanation claims need appropriate support beyond timing; clarification items
   need genuine missing information and justified requested clarification.
6. Workstation model qualification, token/context admission and tool-free evaluation
   remain pending. Revised public inputs are prepared; no benchmark result exists.

No machine/API prerequisite blocks this offline milestone. The retained input/
artifact paths are machine-specific; users can pass external paths through CLI.
Strict exact-law recognition is intentionally bounded, not a general controller
interpreter. The declared point registry and tested synthetic coverage do not imply
that such events were observed in these real development windows.
