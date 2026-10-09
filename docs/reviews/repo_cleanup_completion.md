# Repository cleanup completion - 9 October 2026

Base/current remote before cleanup: `ccfde9ee904ac5efdc330ba707ebf54843ffb135`.
Branch: `simphysqa-repo-cleanup`; cleanup implementation commit:
`a7d9fd5f8c983af4f5f7127eb2424f398069588d`.
[PR #3](https://github.com/chirix33/phi-jepa/pull/3) is published and open. The user
subsequently directed that they will merge it; no merge is performed in this session.
Local main and GitHub main remain at the base above. This report/instruction follow-up
is a separate documentation commit on the same PR. No experiments or SPQ06 are authorized.

## Changed behavior and inventory

The repository presents SimPhysQA first, with current authority, editable setup,
environment separation, external paths, privacy, evidence status and ordinary
branch/validation/review/merge workflow. Scientific implementation is unchanged.

| Disposition | Files | Reason |
| --- | ---: | --- |
| Remove old method configs/locks | 39 | No current runtime/test dependency; learned methods are out of scope |
| Remove old method setup launchers | 2 | Their implementation/environments were already removed |
| Remove old root method files | 4 | Training contract, prototype notebook, README-old and unused requirements |
| Remove method guides/architecture/prompts/decisions/references/reports | 111 | Superseded pipeline and method results remain recoverable in Git |
| Untrack method-result files and CLI outputs | 9,569 | No active SimPhysQA use; every local file remains byte-identical and ignored |
| Total removed tracked paths | 9,725 | All original blobs match the verified archival revision |

Retain all active source/tests/scripts, five families/schemas, annotation/event/
association/answer evidence, audit/extraction/rating/sampling, evaluation/scorers/
nine-condition plan, licenses/citations, exact adopted assets and executed archives,
SPQ accepted evidence and PDS generation/admission/freeze receipts. See the
[decision/inventory](../decisions/repo_cleanup.md) and [specific legacy reasons](../history.md).

Runtime, tests, packaging, schemas and operative scientific configs remain exact.
Only the unused path-example template changes to a configurable external placeholder.
Obsolete Git attributes are removed; specific ignore entries preserve untracked
historical results. Source-index historical links are repaired; current SPQ05 audit
scope supersedes old calibration planning. Archived payloads and mappings are exact.
No values, IDs, splits, tolerances, cutoffs, controllers, answers or conclusions change.

## Validation actually run

Fresh isolated Python 3.12.14 CPU venv reconstructed from seven exact installed pins;
setuptools 84.0.0, jsonschema 4.26.0. Offline editable install and pip check pass.
This verifies provisioned local reconstruction, not public-index resolution.

- Existing offline suite: **139 tests in 228.252 seconds, OK (skipped=1)**.
  The skipped ReplayPolicySoftwareTests class requires optional simulator NumPy
  and contains six methods. All artifact variables, including foundation, were set.
- Read-only foundation validation: all 56 accepted records, four domains/five
  families, 16 groups, 20 exclusions, 504 initial requests/72 conditional templates.
- Core and annotation CLI help, simulator CLI help and source schema validation pass.
  Schema CLI explicitly reports physics not checked.
- Core module imports pass; spq02_arm_inspect requires MuJoCo and spq02_worker requires
  NumPy, so these optional runtime imports remain unqualified.
- Static parsing/internal-import resolution, strict JSON parse, actual offline wheel
  build and all five runtime schema resource checks pass. This does not qualify a
  wheel installed away from root assets/configs.
- Complete deletion/diff review: every removed Git blob matches archive; all 9,569
  preserved local artifacts retain hashes; all unmodified retained files match.
  Source/tests/scripts/pyproject/schemas/prompt archives have no diff against base.
- All 62 prior external manifests and original release manifest match; all 55 sealed
  archive files and 16 exact executed annotation payloads match prior archive bytes.
- Tracked documentation/reference checks and git diff --check pass. Two original
  sealed catalogue `None` links remain explicitly unavailable preliminary procedure
  sources; exact archive payloads are preserved, with explanation in history.md.

No optional simulator test files, MuJoCo/PyBullet/MJX engines, GPU/model runtime,
numerical audit-power environment, live annotation, answering benchmark or human
rating collection was run. No scientific simulation/model/provider calls or spend.
No deletion-only tests were added.

## Exact commands and historical local receipts

These paths describe this cleanup execution, not required setup locations:

```powershell
$Repo='C:/Users/aashraf/.codex/visualizations/2026/10/04/01a10902-e2dc-7390-827b-382d2692622c/local-foundation-merge/main'
$Prior='C:/Users/aashraf/.codex/visualizations/2026/10/04/01a10902-e2dc-7390-827b-382d2692622c'
$Evidence='C:/Users/aashraf/.codex/visualizations/2026/10/09/01a12258-7d16-7ac3-861b-c7326aff811e'
$Provisioned="$Prior/merge-review/cpu-venv/Scripts/python.exe"
$Python="$Evidence/cpu-venv/Scripts/python.exe"
Set-Location $Repo
& $Provisioned scripts/bootstrap_cpu_offline.py --output "$Evidence/cpu-venv"
& $Python -m pip install --no-index --no-build-isolation --no-deps -e .
& $Python -m pip check
& $Python -m simphysqa --help
& $Python -m simphysqa.spq01 --help
& $Python -m phi_jepa.simulation.cli --help
& $Python -m phi_jepa.simulation.cli validate-schema
& $Python -m pip wheel --no-index --no-build-isolation --no-deps . --wheel-dir "$Evidence/wheels"
$env:SIMPHYSQA_FOUNDATION_ARTIFACTS=$Prior
& $Python -m simphysqa.foundation --artifacts $Prior --output "$Evidence/foundation-check" --validate-records
./scripts/simphysqa_spq04.ps1 -Mode check -Artifacts $Prior -Python $Python -SourceData 'C:/Users/aashraf/Desktop/Work/phi-jepa/phi-jepa/dataset-runs/release-four-domain-v1'
& $Python "$Evidence/cleanup_verify.py" $Repo $Evidence
git -c core.longpaths=true diff --check HEAD
```

Evidence files: inventory-before.json (per-path hashes/recovery), complete-cleanup.diff,
review-verification.json, external-preservation.json, foundation-validation.log,
cpu-tests.log, cpu-venv/offline-setup-manifest.json and wheels/. Session scripts stay
external; they are review tools, not additions to the scientific pipeline.

## Preservation, deviations and next step

Verified archive `7dd4a64e90cfb18be743503ac8345cabf2f6e28b`, original checkout clean.
Existing SimPhysQA worktree remains clean at ccfde9e. No worktrees/artifact roots moved,
removed or cleaned; no history rewritten. The archival branch was local only; all
removed files are also recoverable from the already published pre-cleanup main.

Bounded issues resolved: sandbox remote DNS required normal escalated Git access;
Windows Git long-path warnings required per-command core.longpaths=true for review;
mixed historical PROGRESS encoding was confined to superseded method entries and
removed from the active tracker. Original bytes remain in Git. No scientific change.

The remaining integration step is the user-owned PR merge. After that merge,
future work branches from cleaned current main. Active
paths and commands are unchanged: src/simphysqa, configs/simphysqa, existing test and
export scripts; phi_jepa simulator namespace and original assets/root schemas remain
required. SPQ06 is unstarted. Human judgments, answering-runtime qualification,
release-wide enrichment and broader study gates remain pending.
