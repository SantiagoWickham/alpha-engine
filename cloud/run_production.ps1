$ErrorActionPreference = 'Stop'
$Root = 'C:\Users\santi\OneDrive\Escritorio\ALPHA_ENGINE_V12_RETURN_FIRST'
$V13 = Join-Path $Root 'ALPHA_ENGINE_V13_RETURN_FIRST_MULTI_HORIZON'
$V12 = Join-Path $Root 'ALPHA_ENGINE_V12_RETURN_FIRST_STARTER'
$env:PYTHONPATH = "$($V13)\src;$($V12)\src"
$env:MMM_SEC_USER_AGENT = 'AlphaEngineV13 research github.com/SantiagoWickham/alpha-engine'

function Run-Step([string]$Name,[string]$Script) {
  Write-Host "`n============================================================"
  Write-Host $Name
  Write-Host "============================================================"
  $p = Join-Path $V13 $Script
  if (-not (Test-Path $p)) { throw "Missing production runner: $p" }
  Push-Location $V13
  try {
    & powershell.exe -NoProfile -ExecutionPolicy Bypass -File $p
    if ($LASTEXITCODE -ne 0) { throw "$Name failed with exit code $LASTEXITCODE" }
  } finally { Pop-Location }
}

Run-Step 'V13 IDEAL - LIVE SHADOW' 'RUN_V13_PHASE5B_LIVE_SHADOW.ps1'

Write-Host "`nPreparing BYMA reference input from the SAME live V13 snapshot..."
python (Join-Path $PSScriptRoot 'prepare_byma_input.py')
if ($LASTEXITCODE -ne 0) { throw 'BYMA reference input failed' }

Run-Step 'BYMA TRANSFER - CURRENT GEOMETRY' 'RUN_V13_PHASE5H_V4_EXECUTABLE.ps1'

Write-Host "`nCLOUD_PRODUCTION_ENGINE: PASS"
