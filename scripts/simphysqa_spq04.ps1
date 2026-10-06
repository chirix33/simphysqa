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
$taskOutput="$Artifacts/spq04/clarifications-1.0.0"
$taskArchive="$Artifacts/spq04/prompt-archive-1.0.7"
Push-Location $taskRepo
try {
    if ($Mode -eq 'export') {
        & $Python -m simphysqa.clarification_export --parents "$Artifacts/spq02b/answers-1.0.3/organizer-private/qa-records.jsonl" --explanations "$Artifacts/spq03/explanations-1.0.0" --plan "$Artifacts/spq02/plan.json" --runs "$Artifacts/spq02/runs" --output $taskOutput
    } elseif ($Mode -eq 'archive') {
        & $Python -m simphysqa.clarification_archive --previous "$Artifacts/spq03/prompt-archive-1.0.6" --clarifications $taskOutput --output $taskArchive
    } else {
        if ($SourceData) { $env:SIMPHYSQA_DATA_ROOT=$SourceData }
        $env:SIMPHYSQA_DEVELOPMENT_RECORDS="$Artifacts/spq01/selection/predictive-records.jsonl"
        $env:SIMPHYSQA_SPQ01_QA="$Artifacts/spq01/development/qa-records.jsonl"
        $env:SIMPHYSQA_SPQ01A_ROOT="$Artifacts/spq01a/event-language-2.0.0"
        $env:SIMPHYSQA_SPQ02_PLAN="$Artifacts/spq02/plan.json"
        $env:SIMPHYSQA_COUNTERFACTUAL_QA="$Artifacts/spq02/export-1.0.0/organizer-private/qa-records.jsonl"
        $env:SIMPHYSQA_ANSWER_EXPORT="$Artifacts/spq02b/answers-1.0.3"
        $env:SIMPHYSQA_PROMPT_ARCHIVE="$Artifacts/spq03/prompt-archive-1.0.6"
        $env:SIMPHYSQA_EXPLANATION_EXPORT="$Artifacts/spq03/explanations-1.0.0"
        $env:SIMPHYSQA_CLARIFICATION_EXPORT=$taskOutput
        $env:SIMPHYSQA_CLARIFICATION_ARCHIVE=$taskArchive
        & $Python -m unittest discover -s tests -p 'test*.py' -v
    }
    $taskExit=$LASTEXITCODE
} finally { Pop-Location }
exit $taskExit
