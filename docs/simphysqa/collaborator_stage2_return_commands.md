# Central processing after complete collaborator returns

These commands run only after receiving the two complete-return ZIPs. The public
runner's fresh metadata gate and new central reservations were already issued.
Do not use the sealed ordinary importer to mislabel native history as old central
tickets. The versioned native wrapper validates the actually issued payloads,
fresh proofs/activation, original native first-turn hash, full returned file hashes,
actual runtime/hardware/rendering and verbatim history before canonicalization.
Malformed/differing transports are preserved; conflicts block scoring. Unknown
processes retain their bounds. Identical transfers do not settle science work twice.

```powershell
$nativeRepo = 'C:/Users/aashraf/.codex/worktrees/simphysqa/phi-jepa'
$nativeBase = 'C:/Users/aashraf/.codex/visualizations/2026/10/06/01a1131b-eac2-7a31-afb4-f219a8dd6471/spq06/2026-10-09'
$nativeCPU = 'C:/Users/aashraf/.codex/visualizations/2026/10/09/01a12258-7d16-7ac3-861b-c7326aff811e/cpu-venv/Scripts/python.exe'
$nativeIssued = 'C:/Users/aashraf/.codex/visualizations/2026/10/12/01a13168-edb1-7ec2-af49-de486a5552c9/collaborator-issued-1.0.0'
$env:PYTHONPATH = "$nativeRepo/src;$nativeRepo/tests"
$env:PYTHONDONTWRITEBYTECODE = '1'
$env:PYTHONUTF8 = '1'
# Place both received complete ZIPs at these designated new paths:
& $nativeCPU -m simphysqa.native_reconciliation import-continuation --ledger "$nativeBase/central-main-1.0.0/main.sqlite" --source "$nativeIssued/incoming/deepseek-stage2-complete-return.zip" --output "$nativeIssued/immutable-stage2-imports"
& $nativeCPU -m simphysqa.native_reconciliation import-continuation --ledger "$nativeBase/central-main-1.0.0/main.sqlite" --source "$nativeIssued/incoming/gemma-cot-stage2-complete-return.zip" --output "$nativeIssued/immutable-stage2-imports"
# Only after both issued stages have been processed, with conflicts resolved:
& $nativeCPU -m simphysqa.native_reconciliation analyse-core --ledger "$nativeBase/central-main-1.0.0/main.sqlite" --plan "$nativeBase/restart-execution-1.0.0/central-analysis-1.0.0/main-run-plan.json" --output "$nativeIssued/joint-core-analysis-1.0.0"
```

Import reserves 600 s central work per invocation and analysis 1800 s under unchanged
Collaborator allocation; all measured/unknown original work and reservations remain.
The ZIPs are preserved before safe extraction. The existing frozen bridge/scorers/
paired bootstrap see original+recovered Ashraf core and reconciled collaborator
first turns alongside genuine stage-2 outputs; assigned 200 / 40-family denominators
remain unchanged. The new provenance/accounting sidecar discloses original independent
authority and newly issued continuations. No intermediate resolved scores are
reported while supported jobs/routes remain unprocessed. Failed metadata or absent
answers retain failure status; there is no retry, fabricated response or repair.
Preserve existing core/complement/400 analyses rather than replacing old files.
