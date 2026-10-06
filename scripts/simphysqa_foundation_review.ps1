param(
    [Parameter(Mandatory=$true)][string]$Artifacts,
    [Parameter(Mandatory=$true)][string]$Python,
    [Parameter(Mandatory=$true)][string]$SourceData,
    [string]$Output=''
)
$ErrorActionPreference='Stop'
$taskRepo=Split-Path $PSScriptRoot -Parent
$env:SIMPHYSQA_FOUNDATION_ARTIFACTS=(Resolve-Path -LiteralPath $Artifacts).Path
$env:PYTHONDONTWRITEBYTECODE='1'
if (-not $Output) { $Output=Join-Path $env:SIMPHYSQA_FOUNDATION_ARTIFACTS 'merge-review/foundation-1.0.0' }
Push-Location $taskRepo
try {
    & $Python -m pip check
    if ($LASTEXITCODE -ne 0) { throw 'Dependency check failed' }
    & $Python -m simphysqa.foundation --artifacts $env:SIMPHYSQA_FOUNDATION_ARTIFACTS --output $Output --validate-records
    if ($LASTEXITCODE -ne 0) { throw 'Accepted artifact validation failed' }
    & "$PSScriptRoot/simphysqa_spq04.ps1" -Mode check -Python $Python -Artifacts $env:SIMPHYSQA_FOUNDATION_ARTIFACTS -SourceData $SourceData
    $taskExit=$LASTEXITCODE
} finally { Pop-Location }
exit $taskExit
