# Supplemental receipts and future main commands

Actual execution procedures are archived under C:\Users\aashraf\.codex\visualizations\2026\10\06\01a1131b-eac2-7a31-afb4-f219a8dd6471\spq06\2026-10-09\supplemental-src.
Set PYTHONDONTWRITEBYTECODE before interpreter startup. The repository is the
SimPhysQA worktree, not the historical Desktop checkout. These commands preserve
all roots. The six supplemental job keys/processes are already reserved/completed;
rerunning `run` rejects them. No scientific retry or extra calls are authorized.

```powershell
$repoPath = 'C:\Users\aashraf\.codex\worktrees\simphysqa\phi-jepa'
$basePath = 'C:\Users\aashraf\.codex\visualizations\2026\10\06\01a1131b-eac2-7a31-afb4-f219a8dd6471\spq06\2026-10-09'
$cpuPython = 'C:/Users/aashraf/.codex/visualizations/2026/10/09/01a12258-7d16-7ac3-861b-c7326aff811e/cpu-venv/Scripts/python.exe'
$env:PYTHONPATH = "$repoPath/src;$repoPath/tests"
$env:PYTHONDONTWRITEBYTECODE = '1'
$env:PYTHONUTF8 = '1'
& $cpuPython -m unittest test_main_execution_queue test_supplemental_execution test_development_execution test_execution_readiness test_spq06 test_spq06_execution test_spq06_main test_spq06_analysis -v
& $cpuPython -m simphysqa.execution_adapter validate-package --package "$basePath/execution-public-1.1.1"
& $cpuPython -m simphysqa.supplemental_execution validate --package "$basePath/development-awq-public-1.0.0"
# Already executed serially (do not rerun):
& $cpuPython "$basePath/supplemental-src/execute_supplement.py" run --shard qwen3_32b_awq_off--enriched
& $cpuPython "$basePath/supplemental-src/execute_supplement.py" run --shard qwen3_32b_awq_on--enriched
& $cpuPython "$basePath/supplemental-src/execute_supplement.py" run --shard qwen3_32b_awq_on--structured_only
```

Exact WSL argv, timestamps and parent lifecycles are in the 15 *.log.command.json
and *.log.lifecycle.json pairs beside the run. Tokenizer-only final verification:

```powershell
wsl.exe -d Ubuntu-24.04 -- env PYTHONDONTWRITEBYTECODE=1 /home/aashraf/phi-jepa/.venvs/simphysqa-vllm-spq06/bin/python /mnt/c/Users/aashraf/.codex/visualizations/2026/10/06/01a1131b-eac2-7a31-afb4-f219a8dd6471/spq06/2026-10-09/supplemental-src/verify_actual.py --root /mnt/c/Users/aashraf/.codex/visualizations/2026/10/06/01a1131b-eac2-7a31-afb4-f219a8dd6471/spq06/2026-10-09/awq-supplement-1.0.0 --condition qwen3_32b_awq_off --condition qwen3_32b_awq_on --output <NEW-exclusive-receipt-path>
```

## Future main only â€” not authorized or executed

First inspect/adopt package-mapped task receipts; runtime metadata alone is rejected.
Use a SINGLE organizer ledger across executors, not independent database copies.
Assignments are explicit and disjoint, all200 items per combination. Keep initial/
conditional keys together. The eight Ashraf shard names are:
qwen3_8b_direct--enriched, qwen3_8b_thinking--enriched,
llama31_8b_direct--enriched, llama31_8b_cot--enriched,
qwen3_32b_awq_off--enriched, qwen3_32b_awq_on--enriched,
qwen3_8b_direct--structured_only, qwen3_32b_awq_on--structured_only.
No actual main assignment/ledger/stage has been created here.

Commands below use explicit reviewed parameters, not invented assignment IDs.
`<...>` fields are required future paths/receipts; main launch requires new authority.

```powershell
& $cpuPython -m simphysqa.execution_adapter init-ledger --ledger <CENTRAL-main.sqlite> --package "$basePath/execution-public-1.1.1"
& $cpuPython -m simphysqa.execution_adapter issue --ledger <CENTRAL-main.sqlite> --executor Ashraf --shard <ONE-listed-shard> --output <exclusive-assignment.json>
& $cpuPython -m simphysqa.execution_adapter approve-qualification --ledger <CENTRAL-main.sqlite> --receipt <reviewed-task-qualified-main-package-mapping.json>
& $cpuPython -m simphysqa.execution_adapter pending --ledger <CENTRAL-main.sqlite> --executor Ashraf --assignment <issued-ID>
& $cpuPython -m simphysqa.main_execution_queue reserve-overhead --ledger <CENTRAL-main.sqlite> --assignment <issued-ID> --executor Ashraf --condition <condition-ID> --representation <enriched-or-structured_only> --output <exclusive-process-ticket.json> --authorize-main
```

On the executor, using its pinned condition interpreter/bindings and relative package:

```text
env PYTHONDONTWRITEBYTECODE=1 <PINNED-PYTHON> procedures/execution_preflight.py --package <PUBLIC-PACKAGE> --bindings <bindings.json> --qualification <reviewed-qualification.json> --output <exclusive-fresh-preflight.json>
```

Record outer metadata lifecycle in accounted_preflight_seconds without double counting
the inner metadata elapsed. The queue wrapper defaults to recorded inner elapsed when
the outer measurement is unavailable; identify that unavailable outer boundary and
retain an overhead reserve. A failed preflight must stop the related queue:

```powershell
& $cpuPython -m simphysqa.main_execution_queue block-startup --ledger <CENTRAL-main.sqlite> --assignment <issued-ID> --executor Ashraf --condition <condition-ID> --process <allocated-process-ID> --reason <preserved-error-receipt-reference> --elapsed <measured-ended-seconds>
# If elapsed/end is unknown, omit --elapsed and retain the full reservation.
& $cpuPython -m simphysqa.main_execution_queue prepare-job --ledger <CENTRAL-main.sqlite> --assignment <issued-ID> --executor Ashraf --qualification <approved-qualification-SHA> --keys <never-reserved-max50-initial-keys.json> --bindings <bindings.json> --output <exclusive-public-job> --preflight <fresh-preflight.json> --process <allocated-process-ID>
```

Later executor launch/export and central immutable import:

```text
env PYTHONDONTWRITEBYTECODE=1 <PINNED-PYTHON> procedures/public_executor.py launch --package <PUBLIC-PACKAGE> --job <PUBLIC-JOB> --authorize-main
env PYTHONDONTWRITEBYTECODE=1 <PINNED-PYTHON> procedures/execution_adapter.py export-return --job <PUBLIC-JOB> --output <exclusive-RETURN>
```
```powershell
& $cpuPython -m simphysqa.main_execution_queue import --ledger <CENTRAL-main.sqlite> --source <RETURN> --output <exclusive-immutable-source-root>
& $cpuPython -m simphysqa.execution_adapter route --ledger <CENTRAL-main.sqlite> --key '<actual-clarification-initial-stage-key>' --preparation "$basePath/main-preparation-1.0.0" --output <exclusive-public-route-receipt>
# Stage2: reserve overhead, fresh preflight, prepare only supported never-reserved
# actual-history keys (<=40), launch/export/import identically. Unsupported routes
# remain unexecuted conditional receipts, never authored substitute questions.
& $cpuPython -m simphysqa.execution_adapter analyse --ledger <CENTRAL-main.sqlite> --plan "$basePath/main-run-preflight-1.0.0/main-run-plan.json" --output <exclusive-main-analysis>
```

Identical transfer hashes count once; differing artifacts conflict with no automatic
latest/success/score preference. Failures stay in fixed denominators. No pilot or
development raw responses are eligible as main outputs. Never resume a reserved key.
