a$ErrorActionPreference = "Stop"

$projectRoot = $PSScriptRoot
$venvPython = Join-Path (Split-Path $projectRoot -Parent) "venv\Scripts\python.exe"

if (-not (Test-Path -LiteralPath $venvPython)) {
    throw "Virtual environment Python was not found at: $venvPython"
}

Write-Host "Using $(& $venvPython --version)" -ForegroundColor Cyan
& $venvPython (Join-Path $projectRoot "manage.py") migrate --noinput
if ($LASTEXITCODE -ne 0) { exit $LASTEXITCODE }

& $venvPython (Join-Path $projectRoot "manage.py") runserver
exit $LASTEXITCODE
k