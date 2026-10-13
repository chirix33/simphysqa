# Remaining-200 offline preparation and future execution commands

[Review](../reviews/SPQ06_remaining200_preparation.md),
[decision](../decisions/SPQ06_remaining200_preparation.md),
[blocker](../reviews/SPQ06_remaining200_blocker.md).
All active commands in this milestone are OFFLINE. The conditional execution
paragraph is not current approval. Do not run future mutation/launch commands now.

```powershell
$repoPath = 'C:/Users/aashraf/.codex/worktrees/simphysqa/phi-jepa'
$basePath = 'C:/Users/aashraf/.codex/visualizations/2026/10/06/01a1131b-eac2-7a31-afb4-f219a8dd6471/spq06/2026-10-09'
$cpuPython = 'C:/Users/aashraf/.codex/visualizations/2026/10/09/01a12258-7d16-7ac3-861b-c7326aff811e/cpu-venv/Scripts/python.exe'
$preparedPath = "$basePath/complement-preparation-1.0.1"
$ledgerPath = "$basePath/central-main-1.0.0/main.sqlite"
$env:PYTHONPATH = "$repoPath/src;$repoPath/tests"
$env:PYTHONDONTWRITEBYTECODE = '1'
$env:PYTHONUTF8 = '1'
# Executed once; output root is exclusive and already sealed:
& $cpuPython -m simphysqa.complement_preparation prepare --base $basePath --repo $repoPath --output $preparedPath --historical "$basePath/organizer-private/historical-prompt-use-1.0.1.json" --audit "$basePath/../../spq05/delivery-1.0.0"
# Safe read-only validation; does not issue stages:
& $cpuPython -m simphysqa.complement_preparation validate --output $preparedPath
# Forecast output must be fresh/exclusive; use a new timestamped path:
& $cpuPython -m simphysqa.complement_preparation forecast --base $basePath --prepared $preparedPath --output "$basePath/complement-forecast-next.json"
# Already executed tokenizer-only verification, CUDA disabled and no weights:
& $cpuPython "$basePath/complement-render-driver-1.0.0/render.py"
# Already created; exclusive plan output, no ledger writes:
& $cpuPython -m simphysqa.complement_execution dry-plan --prepared $preparedPath --output "$basePath/complement-reservation-plan-1.0.0.json"
& $cpuPython -m unittest test_complement_execution test_complement_preparation test_complement_budget test_main_allocation test_main_import test_main_record_index test_restart_execution test_result_diagnostics test_spq06_analysis -v
```

The public overlay ZIP includes1,600 exact initial requests, six exact scientific
condition files, six unchanged workers/support, IDs/groups/ranks and hashes. It
REQUIRES the separately transferred, unchanged execution-public-1.1.1 package. It
is not a replacement package and the old sealed validator must not be relaxed.
No private records, gold, rollouts or credentials are transferred. Coordinator
routing/scoring stays private; intentional explanation comparisons remain public.
Fresh offline render proofs and tokenizer IDs are inspection/preparation artifacts,
not actual responses, task qualification or reserved stages.

## Future only — requires actual human budget AND execution approval

Do not fill approval fields by copying the conditional draft. The delivered template
has false approvals/null text and must reject. Record the actual subsequent Ashraf
message/date and exact allocation if approved. Refresh the live forecast and calendar
at that point; current 25%reserve does not fit the 18:00Chicago import cutoff. No
calendar extension, new allowance or alternate allocation is inferred.

```powershell
# FUTURE ONLY: actual approval file does not exist in this preparation.
& $cpuPython -m simphysqa.complement_budget apply --ledger $ledgerPath --approval "$basePath/actual-ashraf-expansion-approval.json" --output "$basePath/complement-budget-applied-1.0.0.json" --authorize-budget-revision
& $cpuPython -m simphysqa.complement_execution register --ledger $ledgerPath --prepared $preparedPath --approval "$basePath/actual-ashraf-expansion-approval.json" --output "$basePath/complement-registration-1.0.0.json" --authorize-complement
& $cpuPython -m simphysqa.complement_execution issue-all --ledger $ledgerPath --output "$basePath/complement-assignment-1.0.0.json"
```

Issue-all owns exactly all 1,920 possible Ashraf keys; no collaborator assignment.
The central reservation plan contains32 ordered initial batches of 50 and eight
conditional batches of at most40. These are possible stages, not booked attempts.
A later driver may shrink batches ONLY by remaining budget/calendar, retaining
complete assigned200 denominators and fixed order. It must never choose by scores.

For EACH later batch, reserve 600 s process/preflight overhead FIRST, then execute
public-only fresh metadata using the exact private Ashraf bindings/qualification/
reviewed mappings. The new complement_preflight.py changes request-registry lookup
only; artifacts, numeric UUID mapping, ModelConfig, template and capacity checks
remain the sealed procedure. It imports no gold and loads no answering weights.
The preflight stdout/log/exact argv/lifecycle and registry hash must be saved.

```powershell
# FUTURE ONLY; IDs/paths come from the issued assignment and actual batch plan:
& $cpuPython -m simphysqa.complement_execution reserve-overhead --ledger $ledgerPath --assignment $assignmentId --condition $conditionId --representation $representation --output $overheadReceipt
# In WSL, via the condition's PINNED interpreter and environment:
# python complement-support-1.0.0/complement_preflight.py --package <sealed1.1.1> --bindings <exact-binding.json> --qualification <main-qualified.json> --mapping <reviewed-mapping.json> --keys <never-reserved-keys.json> --routes <actual-complement-routes> --output <exclusive-preflight-root> --registry <prepared/public/execution-inputs.json> --registry-sha256 <exact-hash>
# Only after fresh proof/adoption is approved centrally:
& $cpuPython -m simphysqa.complement_execution prepare-job --ledger $ledgerPath --assignment $assignmentId --qualification $qualificationHash --keys $keysPath --bindings $bindingsPath --output $jobPath --preflight $proofPath --process $processId
# In WSL, the SAME sealed public_executor and original worker:
# python execution-public-1.1.1/procedures/public_executor.py launch --package <sealed1.1.1> --job <new-job> --authorize-main
# Export actual return with the sealed public adapter, then CENTRAL immutable import:
& $cpuPython -m simphysqa.complement_execution import --ledger $ledgerPath --source $actualReturnPath --output $immutableSourceRoot
& $cpuPython -m simphysqa.complement_execution route --ledger $ledgerPath --key $actualInitialKey --preparation "$basePath/main-preparation-1.0.0" --output $actualRouteReceipt
```

These are exact implemented APIs; the future loop must provide actual issued IDs,
proofs and reserved controls, not placeholders as evidence. The reviewed scope
sidecar binds each job to the frozen complement/registry. Worker keys remain four
parts; central provenance prefixes spq06-complement-1.0.0. It uses the SAME DB and
shared processes/control-work/guards, never another ledger. Core and recovery tables
remain untouched. Known lifecycle settles measured once; unknown retains full bound.
Reserve600 s central import/verification per batch and3,600 s for final analyses/export.
Stage/loading timings are nested; outer dispatcher gaps measured separately once.

After the FIRST normal Qwen3-8B enriched batch (at most50), require immutable import,
exact requests/render/token/raw preservation, memory/timing/qualification/scope
provenance, source joins, accounting and unchanged scoring checks. It belongs to the
extension and cannot be replaced. Accuracy is not a gate. The future loop is not
launched or inference-qualified by current offline success. Related startup failures
pause via existing queue mechanism; no automatic unblock/retry/orphan release.

For stage2, only actual imported first turns can route a supported reply. Preserve
assistant raw text verbatim. Unsupported and context-overflow cases are receipts/
failures in assigned denominators; never authored questions, truncation or new calls.
Twenty conservative full-first-output continuation bounds fail on the prepared
complement; actual first text may fit, but must be checked before reserve/inference.
This is not permission to omit or replace those cases.

Analysis after authorized outputs must materialize original/recovered CORE canonical
records plus complement-scoped canonical records (after conflict validation), then
run unchanged main_analysis.assess under original formal_scope. Generate separate
core 200/complement 200/union 400 rows. Call unchanged paired_intervals on the UNION,
10,000 replicates/seed 20261009, drawing20 groups/domain-family when400complete. Never
average prior CIs, count turns as items or import pilot/mock responses. Missing/failing
items stay in fixed denominators; comparisons with nonexpanded conditions use common
core 200. A partial extension is not complete400. Current delivery freezes this plan;
there are no new scientific results or human judgments to analyse.
