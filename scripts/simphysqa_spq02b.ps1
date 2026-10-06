param(
    [Parameter(Mandatory=$true)][string]$Artifacts,
    [Parameter(Mandatory=$true)][string]$Python,
    [ValidateSet('export','archive','check')][string]$Mode='export',
    [string]$SourceData=''
)
$ErrorActionPreference='Stop'
$taskRepo=Split-Path $PSScriptRoot -Parent
$env:PYTHONPATH=Join-Path $taskRepo 'src'
$env:PYTHONDONTWRITEBYTECODE='1'
$taskOutput=Join-Path $Artifacts 'spq02b/answers-1.0.2'
$taskArchive=Join-Path $Artifacts 'spq02b/prompt-archive-1.0.3'
Push-Location $taskRepo
try {
    if ($Mode -eq 'export') {
        & $Python -m simphysqa.answer_export --records "$Artifacts/spq01a/event-language-2.0.0/qa-records.jsonl" --counterfactuals "$Artifacts/spq02/export-1.0.0/organizer-private/qa-records.jsonl" --plan "$Artifacts/spq02/plan.json" --runs "$Artifacts/spq02/runs" --arm-evidence "$Artifacts/spq02/arm-interpretation.json" --output $taskOutput
    } elseif ($Mode -eq 'archive') {
        & $Python -m simphysqa.prompt_archive --spq01 "$Artifacts/spq01" --spq01a "$Artifacts/spq01a" --spq02 "$Artifacts/spq02" --enriched $taskOutput --output $taskArchive
    } else {
        if ($SourceData) { $env:SIMPHYSQA_DATA_ROOT=$SourceData }
        $env:SIMPHYSQA_DEVELOPMENT_RECORDS="$Artifacts/spq01/selection/predictive-records.jsonl"
        $env:SIMPHYSQA_SPQ01_QA="$Artifacts/spq01/development/qa-records.jsonl"
        $env:SIMPHYSQA_SPQ01A_ROOT="$Artifacts/spq01a/event-language-2.0.0"
        $env:SIMPHYSQA_SPQ02_PLAN="$Artifacts/spq02/plan.json"
        $env:SIMPHYSQA_COUNTERFACTUAL_QA="$Artifacts/spq02/export-1.0.0/organizer-private/qa-records.jsonl"
        $env:SIMPHYSQA_ANSWER_EXPORT=$taskOutput
        $env:SIMPHYSQA_PROMPT_ARCHIVE=$taskArchive
        & $Python -m unittest discover -s tests -p 'test*.py' -v
    }
    $taskExit=$LASTEXITCODE
} finally { Pop-Location }
exit $taskExit
