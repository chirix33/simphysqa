# SPQ06 commands and environment boundaries

Use the existing checkout on `simphysqa-spq06`. No branch switch, second worktree,
hosted answering, simulator access from answering workers or main launch is part
of preparation. Source releases and prior exports are read-only inputs.

## Windows CPU environment

The editable CPU environment points to a different checkout; set the explicit
source path for every invocation. In PowerShell:

```powershell
$spqRepo = 'C:/Users/aashraf/.codex/worktrees/simphysqa/phi-jepa'
$spqBase = 'C:/Users/aashraf/.codex/visualizations/2026/10/06/01a1131b-eac2-7a31-afb4-f219a8dd6471/spq06/2026-10-09'
$spqPython = 'C:/Users/aashraf/.codex/visualizations/2026/10/09/01a12258-7d16-7ac3-861b-c7326aff811e/cpu-venv/Scripts/python.exe'
$env:PYTHONPATH = "$spqRepo/src;$spqRepo/tests"
$env:PYTHONDONTWRITEBYTECODE = '1'
Set-Location -LiteralPath $spqRepo
```

The completion receipt distinguishes actual executed commands from future ones.
The following preparation commands create new exclusive roots. Re-running the
completed generation and main export commands resumes saved outputs; verification,
forecast and index roots require a new version unless explicitly documented.

```powershell
& $spqPython -m simphysqa.heldout_live run --output "$spqBase/heldout-execution-1.0.0"
& $spqPython -m simphysqa.main_preparation --run "$spqBase/heldout-execution-1.0.0" --pilot "$spqBase/pilot-1.0.0" --output "$spqBase/main-preparation-1.0.0"
& $spqPython -m simphysqa.preparation_verification main --run "$spqBase/heldout-execution-1.0.0" --preparation "$spqBase/main-preparation-1.0.0" --output "$spqBase/preparation-verification-1.0.0"
& $spqPython -m simphysqa.saved_resume_verification --run "$spqBase/heldout-execution-1.0.0" --pilot "$spqBase/pilot-1.0.0" --preparation "$spqBase/main-preparation-1.0.0" --output "$spqBase/saved-resume-verification-1.0.0"
& $spqPython -m simphysqa.delivery_provenance index --run "$spqBase/heldout-execution-1.0.0" --pilot "$spqBase/pilot-1.0.0" --output "$spqBase/execution-provenance-1.0.0"
```

Do not retry the pilot's already-reserved stages. Original failed/interrupted and
context-rejected stages remain in the 20-item denominator for every condition.
Its raw requests, model outputs, immutable revisions and private scores are under
`pilot-1.0.0` and `pilot-analysis-1.0.0`; prepared requests are not execution proof.

## Main request capacity: CPU tokenization only

The pinned standalone procedure uses actual local tokenizer snapshots and the
GGUF vocabulary tool with GPU visibility disabled. It verifies Gemma rendering
against saved actual server prompts and token IDs. It performs no model inference.

```powershell
wsl.exe -d Ubuntu-24.04 -- env PYTHONDONTWRITEBYTECODE=1 HF_HUB_OFFLINE=1 TRANSFORMERS_OFFLINE=1 /home/aashraf/phi-jepa/.venvs/simphysqa-vllm-spq06/bin/python /mnt/c/Users/aashraf/.codex/visualizations/2026/10/06/01a1131b-eac2-7a31-afb4-f219a8dd6471/spq06/2026-10-09/tokenization_capacity.py --preparation /mnt/c/Users/aashraf/.codex/visualizations/2026/10/06/01a1131b-eac2-7a31-afb4-f219a8dd6471/spq06/2026-10-09/main-preparation-1.0.0 --pilot /mnt/c/Users/aashraf/.codex/visualizations/2026/10/06/01a1131b-eac2-7a31-afb4-f219a8dd6471/spq06/2026-10-09/pilot-1.0.0 --base /mnt/c/Users/aashraf/.codex/visualizations/2026/10/06/01a1131b-eac2-7a31-afb4-f219a8dd6471/spq06/2026-10-09 --output /mnt/c/Users/aashraf/.codex/visualizations/2026/10/06/01a1131b-eac2-7a31-afb4-f219a8dd6471/spq06/2026-10-09/main-tokenization-1.0.0
& $spqPython -m simphysqa.runtime_forecast --pilot "$spqBase/pilot-1.0.0" --preparation "$spqBase/main-preparation-1.0.0" --capacity "$spqBase/main-tokenization-1.0.0/capacity-checks.json" --output "$spqBase/runtime-decision-1.0.0"
& $spqPython -m simphysqa.main_run preflight --preparation "$spqBase/main-preparation-1.0.0" --decision "$spqBase/runtime-decision-1.0.0/runtime-forecast-and-size-decision.json" --output "$spqBase/main-run-preflight-1.0.0"
```

The decision reads timing/completion/loading receipts and preparation feasibility,
never main outputs or pilot correctness. Conditional capacity uses the full first
and second output allowances plus exact recorded reply updates. Actual dialogue
capacity is checked again without truncation; failures never trigger replacements.

## Future main experiment: separate launch authorization required

These are **future commands**, not commands executed by this preparation milestone.
After explicit authorization, the saved preflight root is the resumable run root:

```powershell
& $spqPython -m simphysqa.main_run run --output "$spqBase/main-run-preflight-1.0.0" --authorize-local-main --gpu-hours 48
& $spqPython -m simphysqa.main_analysis --run "$spqBase/main-run-preflight-1.0.0" --output "$spqBase/main-analysis-1.0.0"
```

The first command loads all nine frozen conditions sequentially and both matched
ablation conditions. Every model stage has one immutable reservation; resume
schedules only never-reserved stages. Process interruption retains the full unknown
reservation. No automatic scientific item retry, answer repair or main-set change.
The exact standalone workers and their hashes are in the preparation manifest.
Scoring stays in the CPU organizer process, outside public GPU worker inputs.

## Separate model-answer prose study

```powershell
& $spqPython -m simphysqa.model_prose_review forms --subset "$spqBase/main-preparation-1.0.0/model-prose-assessment-subset.json" --output "$spqBase/model-prose-forms-1.0.0"
& $spqPython -m simphysqa.model_prose_review import --root "$spqBase/model-prose-forms-1.0.0" --form "$spqBase/model-prose-forms-1.0.0/P1.csv" --assessor P1 --output "$spqBase/model-prose-blank-validation-1.0.0"
& $spqPython -m simphysqa.model_prose_review import --root "$spqBase/model-prose-forms-1.0.0" --form "$spqBase/model-prose-forms-1.0.0/P2.csv" --assessor P2 --output "$spqBase/model-prose-blank-validation-1.0.0"
```

Blank imports collect zero judgments. Actual human submissions must point to the
returned CSV and a new external import root; exact source bytes are retained.
After main responses exist, export blinded response packets with this future command:

```powershell
& $spqPython -m simphysqa.model_prose_review packets --root "$spqBase/model-prose-forms-1.0.0" --run "$spqBase/main-run-preflight-1.0.0" --output "$spqBase/model-prose-packets-1.0.0"
```

This assessment is independent of the SPQ05 annotation audit. Eight explanation
tasks × nine conditions =72 responses, with separate blank P1/P2 forms covering
the same responses. No identity assumption, fabricated model conversation or human
judgment. Missing model text remains unavailable. See the frozen
[main design](spq06_main_design.md) for criteria, missingness and uncertainty.
