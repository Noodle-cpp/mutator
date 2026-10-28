# Build mutator.exe (bundles crapper). Clone ../crapper or set CRAPPER_ROOT.
$ErrorActionPreference = "Stop"
$Root = Split-Path -Parent $PSScriptRoot
$CrapperRoot = if ($env:CRAPPER_ROOT) { $env:CRAPPER_ROOT } else { Join-Path (Split-Path $Root -Parent) "crapper" }

if (-not (Test-Path (Join-Path $CrapperRoot "pyproject.toml"))) {
    throw "crapper not found at $CrapperRoot. Set CRAPPER_ROOT or use ub layout (ub/mutator + ub/crapper)."
}

Set-Location $Root
if (-not (Test-Path ".venv")) {
    python -m venv .venv
}
$Py = Join-Path $Root ".venv\Scripts\python.exe"
$Pip = Join-Path $Root ".venv\Scripts\pip.exe"

& $Pip install -q -e $CrapperRoot
& $Pip install -q -e ".[dev]" pyinstaller
& $Py -m PyInstaller packaging\mutator.spec --noconfirm

Write-Host ""
Write-Host "Built: $Root\dist\mutator.exe"
Write-Host "No separate crapper install needed on target PC."
