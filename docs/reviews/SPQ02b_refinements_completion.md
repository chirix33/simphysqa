# SPQ02b bounded answer/provenance refinement — 6 October 2026

Base: 1796b8d9cb475b8579330854b298021a200b4c08; branch simphysqa-naacl;
worktree C:/Users/aashraf/.codex/worktrees/simphysqa/phi-jepa. Final commit in the
external refinement delivery receipt. Main remains 7dd4a64e90cfb18be743503ac8345cabf2f6e28b.

## Delivered behavior

Private answer contract/schema/renderer/export 1.0.3 preserves all 40 existing QA
(16 direct,16 predictive,8 counterfactual) and eight multi-target alternative
records. 104 QA targets and 40 alternative targets retain exact gold. Derived
reference.explanation presents shared physical conditions once, then each target's
answer and supported interpretation. Every sentence is selected from explicitly
bound shared_claims or per-target claims (explanation_claim_kinds identifies them).
Solver settings, run IDs, hashes and detailed numerical verification stay in
solution traces/evidence context/verification, not the readable explanation.

Quaternion change is 2 acos(min(1,abs(dot(q1,q2))/(norm(q1) norm(q2)))) radians,
using the unchanged answer scorer. Signs q/-q are equivalent rotations; raw exact
quaternions and canonical equality remain unchanged. Orientation comparisons use
rotation_angle_rad, sign_invariant_rotation_angle, and null component subtraction.
Scalar/non-orientation vector differences retain existing semantics. No additional
mechanism claims, simulator executions, provider requests or new QA families.

New export: external spq02b/answers-1.0.3. 40 audit packets, three independent
40-row blank forms and 360 prepared requests; all 360 request files' contents and
40 public views are byte-identical to accepted answers-1.0.2. Raw wrappers are
exactly recovered by removing private.answer_annotation. Alternative source
records, answer specs, references, tolerances, group/split IDs and cutoffs exact.
Accepted association export remains 1.1.1. All prior exports remain preserved.

## Prompt/procedure inspection

Stable [entry point](../simphysqa/prompt_archive/README.md),
[consolidated catalogue](../simphysqa/prompt_archive/catalogue.md), and
[per-file index](../simphysqa/prompt_archive/file-generation-index.json).
Archive 1.0.4 has 1,625 indexed files /5,520 per-record mappings, including accepted
answer 1.0.2 and current 1.0.3 with separately pinned procedures. 16/16 actual
executed annotation payloads recovered; zero unavailable/reconstructed model
payloads, zero retries/repairs. Preliminary association 1.1.0/event-description
1.0.0 exact original source remains unrecoverable and explicitly identified;
accepted successors are not presented as that historical implementation.

[Worked provenance entry](../simphysqa/prompt_archive/provenance-example.md) and
[complete worked file mappings](../simphysqa/prompt_archive/provenance-example.json):
SPQ01-attempt-001, sample 01863fd6b9e584c3a5f506ed7013dd80, actual returned
gpt-5.6-sol. Exact [executed wire payload](../simphysqa/prompt_archive/requests/attempt-001.json)
contains instructions then fully instantiated input; no invented role messages.
One execution yielded a summary and 11 timestamp descriptions in
SPQ01-annotation-job/items/01863fd6b9e584c3a5f506ed7013dd80.json and
SPQ01-annotation-job/responses/001.json. Later packet/public-request copies are
reuse, not new executions. Field-specific deterministic event/gold enrichments
are mapped separately. [answer-annotation/1.0.3](../simphysqa/prompt_archive/procedures/answer-annotation-1.0.3.py)
is a deterministic code/template procedure with no model prompt. Prepared answering
requests are unexecuted. Archive excludes credentials and private outcomes/evidence.

## Commands actually run

From the worktree in PowerShell:

```powershell
$taskArtifacts='C:/Users/aashraf/.codex/visualizations/2026/10/04/01a10902-e2dc-7390-827b-382d2692622c'
$taskPython="$taskArtifacts/simphysqa-venv/Scripts/python.exe"
./scripts/simphysqa_spq02b.ps1 -Artifacts $taskArtifacts -Python $taskPython -Mode export
./scripts/simphysqa_spq02b.ps1 -Artifacts $taskArtifacts -Python $taskPython -Mode archive
./scripts/simphysqa_spq02b.ps1 -Artifacts $taskArtifacts -Python $taskPython -Mode check -SourceData 'C:/Users/aashraf/Desktop/Work/phi-jepa/phi-jepa/dataset-runs/release-four-domain-v1'
& $taskPython "$taskArtifacts/check_refinement.py"
```

Export and archive commands repeated for resume: no overwrite/no simulation/model
call. Full test log: external spq02b/refinement-tests-1.0.3.txt. 94 offline tests
pass in 108.122 s, one retained simulator-runtime class skipped. Focused new tests
verify bound concise assembly/shared conditions once; q/-q invariance, known
90-degree rotation and zero-quaternion rejection; real orientation gold/text.
Existing evidence tampering, source recovery, privacy, target/readout fidelity,
multi-target coverage, resumability and blank-rating checks continue passing.
Automatic checks are not human explanation-quality results.

## Inspectable new examples and receipts

External [all-domain/all-family inspection page](C:/Users/aashraf/.codex/visualizations/2026/10/04/01a10902-e2dc-7390-827b-382d2692622c/spq02b/refinement-1.0.3/inspection.html)
links 12 representative packets with explanation, solution trace and bindings.
All 40 packets are in answers-1.0.3/audit-development/packets and all-eight matched
comparison is answers-1.0.3/organizer-private/comparisons.md. Three forms import
0 collected /40 blanks each. Preservation receipt: refinement-1.0.3/checks.json;
resumability: refinement-1.0.3/resume.json. 40 prior manifests checked unchanged.
Total QA explanation words: 17,171 before /4,332 after (automatic count, not
a human quality measurement). Eight real QA orientation targets retain exact
gold; supporting alternatives are validated separately for every target.

New simulations/model calls/spend: 0/0/$0. No answering benchmark, human quality,
acceptance/agreement or formal audit result. Subsequent explanation/clarification
QA and reviewer judgments remain pending. No new scientific threshold, tolerance,
frame conversion or solver decision introduced. A receipt-only helper initially
used Windows default text encoding, causing a hash check to fail; it was corrected
to explicit UTF-8. Exported artifacts did not change, and all preservation checks
then passed. This was not a simulator/reference mismatch.

Final resume: 235 export files plus 43 archive files (278 total) remained byte-exact;
export resume 27.6260263 s, export+archive resume 39.7557407 s. Initial archive
resume invoked from the main cwd encountered sandbox-account Git ownership checks;
rerunning the same helper from the authorized SimPhysQA worktree succeeded. No
global Git safety configuration or scientific artifact was changed. Receipt helper:
`& "$taskArtifacts/resume_refinement.ps1"` from the SimPhysQA worktree.
