# SimPhysQA foundation merge review — 6 October 2026

Prepared from accepted52f47ace928d339239a262836cff67818d6d68da on simphysqa-naacl,
worktree `C:/Users/aashraf/.codex/worktrees/simphysqa/phi-jepa`.
Comparison/base/main:7dd4a64e90cfb18be743503ac8345cabf2f6e28b.
Main, historical artifacts and original physical data remain unchanged. No push/merge.

## Review result and resolved findings

The accepted complete branch diff was inventoried with rename detection disabled:
470 paths =180 additions,281 deletions,9 modifications (464 entries with rename
detection). A full binary diff and per-file blob/hash/check ledger are external:

- [Complete accepted diff](C:/Users/aashraf/.codex/visualizations/2026/10/04/01a10902-e2dc-7390-827b-382d2692622c/merge-review/main-to-accepted.diff).
- [Per-file review ledger](C:/Users/aashraf/.codex/visualizations/2026/10/04/01a10902-e2dc-7390-827b-382d2692622c/merge-review/branch-diff-review.json).

Review categories cover40 active implementation files,16 tests/entry points,
19 schema/config/provenance files,55 sealed archive files,59 instruction/build/doc
files and281 deletion/relocation paths. All changed Python was parsed, JSON was
strictly parsed, every deleted inventory blob matched its original hash and all
221 retained absolute/relative internal import relationships resolved.276 legacy removals match the
SPQ00 dependency inventory; the five remaining deleted paths are byte-identical
simulator-test relocations. Historical source/assets/references remain reachable.
Hash/AST/provenance checks on pinned duplicate snapshots are not new execution.

The only retained simulator physics changes against main are the explicit,
default-false omission flags in engines.py/bullet.py. Inspection confirms arm base
joint torques remain while only the pulse is omitted; driving suppresses only the
scheduled brake command; objects suppress only the block_1 external force; tether
disables the whole support program. Existing saved exact-replay and separate
admission receipts support the eight selected groups. This preparation ran zero
simulations and does not claim arbitrary-environment simulator qualification.

Resolved findings: stale40-item README/phase authority and family-pending text;
missing clarification schema in package metadata; fragmented item/path/exclusion
inventories; ambiguous editable-versus-wheel setup and combined optional dependencies.
The new [foundation contract](../simphysqa/foundation.md) provides a current version
matrix, five-family privacy/evaluation boundaries, explicit query-gap scope and
setup limits. Dated scientific findings and cache-pinned producer code/schemas stay
unchanged. The [authoritative56-item index](../simphysqa/development-index.md) and
[JSON](../simphysqa/development-index.json) resolve all current records, public views,
packets, hashes, groups/splits, .2s cutoffs and20 formal exclusions.

## Reproducibility and verification

Python3.12.14; fresh external CPU venv, seven exact local pinned distributions,
setuptools84.0.0, jsonschema4.26.0; pip25.0.1. Actual offline editable installation
and pip check passed. Distribution files/hashes are recorded in
[offline setup manifest](C:/Users/aashraf/.codex/visualizations/2026/10/04/01a10902-e2dc-7390-827b-382d2692622c/merge-review/cpu-venv/offline-setup-manifest.json).
This tests local pinned reconstruction, not public-index availability.

Initial full cross-family CPU suite:122 tests in156.927s, OK, one skipped class.
After fixing relative-root normalization in the new registry, four focused
foundation tests passed in1.189s. It also passed full record validation and
byte-identical resume with an equivalent relative artifact root. Refusal of a
different rendered path exposed the normalization bug; no prior output was
overwritten. Final consolidated run: **123 tests in156.903s, OK (one skipped class)**,
after full56-record validation and index resume. Recorded in the adjacent receipt.

The skipped ReplayPolicySoftwareTests class contains six software replay-policy
tests requiring NumPy. The separate five `tests/simulator/` files are outside the
default CPU discovery and were not executed (including historical quadruped coverage
outside the four-domain scope). Audit-power Python/NumPy/SciPy computation was not
rerun; prior supplied-package and finite-sample receipts are preserved/inspected.
No GPU, model downloads/provider access, live annotation, answering interactions,
full-release regeneration or formal sampling ran.0 new solves/calls/spend.

Package-data inspection of a no-index/no-deps built wheel confirms all five
runtime JSON schemas, including clarification.schema.json. Root assets/configs
still require editable checkout; standalone wheel runtime is not qualified.
Optional environments: simulator numpy2.4.6/mujoco3.14.0/psutil7.2.2 with Bullet3.2.7;
audit numpy2.5.3/scipy1.18.1. Do not combine their conflicting numpy pins.

Exact commands (PowerShell, from the SimPhysQA worktree):

```powershell
$Artifacts='C:/Users/aashraf/.codex/visualizations/2026/10/04/01a10902-e2dc-7390-827b-382d2692622c'
$ProvisionedPython="$Artifacts/simphysqa-venv/Scripts/python.exe"
$FreshEnv="$Artifacts/merge-review/cpu-venv"
$FreshPython="$FreshEnv/Scripts/python.exe"
$SourceData='C:/Users/aashraf/Desktop/Work/phi-jepa/phi-jepa/dataset-runs/release-four-domain-v1'
& $ProvisionedPython scripts/bootstrap_cpu_offline.py --output $FreshEnv
& $FreshPython -m pip install --no-index --no-build-isolation --no-deps -e .
& $FreshPython -m pip check
& $FreshPython -m simphysqa --help
& $FreshPython -m pip wheel --no-index --no-build-isolation --no-deps . --wheel-dir "$Artifacts/merge-review/wheels"
./scripts/simphysqa_foundation_review.ps1 -Artifacts $Artifacts -Python $FreshPython -SourceData $SourceData
```

Bootstrap refuses an existing env; use a new external destination for reproduction.
The last command reruns read-only saved-record validation/index resume and all
cross-family CPU integration checks. The wheel check does not execute simulation.
External logs: `merge-review/cpu-tests.txt`, `foundation-tests.txt`,
`foundation-validation.txt`, `final-integration.txt`, `wheel-inspection.json`,
`preservation.json` and `verification.json`. The complete diff can be regenerated
with `git diff --binary --no-renames main...52f47ace928d339239a262836cff67818d6d68da`.

## Provenance and research readiness

[Archive entry](../simphysqa/prompt_archive/README.md),
[consolidated prompt/procedure catalogue](../simphysqa/prompt_archive/catalogue.md),
[per-file mappings](../simphysqa/prompt_archive/file-generation-index.json) and
[executed-request/output mapping example](../simphysqa/prompt_archive/provenance-example.md)
remain sealed1.0.7: 1,740 files,1,352 mapping definitions,34 deterministic procedures;
all16 executed language requests recovered, no reconstructed/unavailable executed
payloads, zero historical repairs/failures. Unrecoverable preliminary implementation
sources are disclosed separately. Reuse does not imply another request per copied
packet/timestamp. Prepared answering prompts are unexecuted.

Completed accepted development items:56; failed items:0; pending items:0 within
this bounded set. Clarification's18 rejected candidates are qualification outcomes,
not concealed failed executions. Human judgments and research coverage remain pending.
Current explicit query gaps are5 condition,1 entity and2 time; no missing-parameter,
general-dialogue or new OOD claim.504 initial requests and72 conditional templates
are prepared, with tools=[]; three separate reviewer form sets collectively cover56
records/reviewer and remain blank.20 inspected/development groups excluded.

[Outstanding research](../simphysqa/pending.md) includes human rubric calibration,
release enrichment/population freeze, alternative annotation-source comparison,
event-observed/new-target and broader gap coverage, locally-qualified five-model
runtimes, failure-aware uncertainty/analysis and fresh formal-sample freeze.
Preservation checks verified62 prior manifests,55 byte-identical archived files,
all16 original executed payloads and the unchanged release manifest. Main is clean.
Software evidence/scorer passes do not establish explanation adequacy, human
acceptance/agreement, answering performance or release readiness.

## Proposed merge title

SimPhysQA: five-family dataset, annotation and evaluation foundation

## Proposed merge body

Pivot the active repository to a simulator-grounded dataset/evaluation contribution
for NAACL Resources, Benchmarks, and Evaluation. Retain the four-domain simulator
pipeline, immutable physical source and historical Phi-JEPA provenance, while
removing unrelated training code only from this branch. Main's old tip/history and
external datasets/results are preserved by the documented preservation plan.

Add bounded direct, predictive, matched-omission counterfactual, explanation and
explicit query-gap clarification development infrastructure. The authoritative
registry contains56 QA in16 train groups, accepted versioned exports, private
evidence-bound explanations/traces, public tool-free views, blank independent
audit forms and504 prepared requests plus72 conditional clarification templates.
Keep all20 inspected/development groups excluded from future formal sampling.
Archive exact executed annotation requests separately from deterministic procedures,
reused outputs and unexecuted answering preparation.

Validation: fresh offline editable CPU setup/pip check, complete diff/import/blob
review, package-schema inspection and saved-data cross-family integration. Optional
simulator/audit/GPU runtimes were not rerun. Existing32 saved SPQ02 executions support
eight verified pairs; no new empirical runs, human ratings or answering results.
Human evaluation, full-release enrichment, model qualification and fresh formal
sampling remain pending. Proposed review only; no merge or push performed.

Preservation plan: [historical Phi-JEPA decisions](../decisions/foundation_merge_preservation.md).
