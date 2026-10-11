# Authorized restart recovery commands — /1.0.0

This is the explicitly authorized post-result external-interruption exception.
[Authorization](../prompts/SPQ06_restart_recovery.md),
[decision](../decisions/SPQ06_restart_recovery.md),
[review](../reviews/SPQ06_restart_recovery.md).
Keep the public execution package /1.1.1 and historical workers untouched.

```powershell
$repoPath = 'C:/Users/aashraf/.codex/worktrees/simphysqa/phi-jepa'
$basePath = 'C:/Users/aashraf/.codex/visualizations/2026/10/06/01a1131b-eac2-7a31-afb4-f219a8dd6471/spq06/2026-10-09'
$cpuPython = 'C:/Users/aashraf/.codex/visualizations/2026/10/09/01a12258-7d16-7ac3-861b-c7326aff811e/cpu-venv/Scripts/python.exe'
$env:PYTHONPATH = "$repoPath/src;$repoPath/tests"
$env:PYTHONDONTWRITEBYTECODE = '1'
$env:PYTHONUTF8 = '1'
& $cpuPython -m unittest test_restart_execution test_main_restart test_main_import test_main_record_index test_main_allocation test_main_execution_queue test_spq06_analysis -v
& $cpuPython -m unittest test_execution_readiness test_main_import test_main_allocation test_main_restart test_restart_execution test_result_diagnostics test_spq06_analysis -v
& $cpuPython -m unittest test_result_diagnostics test_restart_execution -v
# Executed once; completed roots/eligibility tables are exclusive, not reusable:
& $cpuPython "$basePath/restart-execution-src-1.0.0/recover.py" freeze
& $cpuPython "$basePath/restart-execution-src-1.0.0/recover.py" run
& $cpuPython "$basePath/restart-analysis-src-1.0.0/finish.py"
```

The driver uses the same authoritative `central-main-1.0.0/main.sqlite`. The additive
restart tables retain original logical stage keys and explicit original-process and
authorization links. Original tables/reservations, unknown charge and immutable
sources remain untouched. Original issuance continues rejecting already-reserved
initials. Recovery issuance filters ONLY the frozen exception keys and supported
new continuation children; a second recovery attempt for a reserved key is rejected.
A preserved QUEUE-PAUSED receipt is never automatically cleared. A future
interruption cannot authorize retrying a newly reserved recovery attempt.

Each actual WSL preflight, launch and token verifier has exact argv/lifecycle
receipts beside its log. The same sealed public executor receives `--authorize-main`
for this authorized MAIN recovery, never for a development workaround. Fresh GPU,
artifact, tokenizer/template/runtime identity and actual history capacity checks
precede scientific reservations. Jobs run serially. Public workers have no private
scoring resources or simulator access.

The ten original null-response routes remain original history. Separate new route
receipts link to them and to each recovered raw first response. Only a supported
actual request can run stage2. The five earlier unsupported first responses stay
outside the exception. No truncation, repair, substitution or expanded allowance.

`restart_execution.combined_records(ledger)` is the explicit versioned central
projection for recovered analysis. It validates immutable original and recovery
sources, keeps conflicts unresolved, and fills only absence of original canonical
answers under this authorization. Do not feed recovery returns into the historical
bare importer: its original reservation identity differs. Use the recovery-layer
ledger plus unchanged central importer. Do not replace original analysis files or
run an old exclusive finish procedure again. Later combined central analysis must
explicitly adopt this projection, not forget recovered evidence or conceal the
original interrupted version.

The recovered analysis calls unchanged `main_analysis.assess`, family scorers and
`paired_intervals` (10, 000 stratified paired trajectory draws, seed 20261009). No
parser/scorer acceptance changes. Reporting-only alternate fenced-JSON detection
never produces a scored replacement. First-turn clarification contract validity is
reported independently of continuation validity and legacy answer_valid.

External evidence is in `restart-execution-1.0.0`: eligibility/search receipts,
jobs, raw requests/token IDs/outputs, immutable imports, central-stage records,
route/history links, original/recovered diagnostics, analyses and accounting.
`audit-bundle-1.0.0.zip` is PRIVATE organizer material, with exact file hashes and
selected examples. `audit-export-receipt.json` binds its SHA256 and final
compression accounting; `completion-accounting.json` is the terminal ledger
snapshot. The bundle's internal analysis-accounting snapshot precedes separately
charged final compression. Historical 6, 600 s remains unknown, never measured zero.

No collaborator run, data generation, annotation, simulation, push or merge is part
of these commands. The collaborator still requires separate authorization and
qualification on his workstation. Main200/400 sizes, allocation and scientific
contracts stay unchanged.
