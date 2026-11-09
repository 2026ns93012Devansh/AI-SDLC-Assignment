$ErrorActionPreference = "Continue"

$ProjectRoot = Split-Path -Parent $PSScriptRoot
$EvidenceDir = Join-Path $ProjectRoot "evidence"

New-Item -ItemType Directory -Force -Path $EvidenceDir | Out-Null

$Timestamp = Get-Date -Format "yyyyMMdd_HHmmss"
$LogPath = Join-Path $EvidenceDir "harness_$Timestamp.txt"
$TempOutput = Join-Path $env:TEMP "part1b_harness_output.txt"

Set-Location $ProjectRoot

$Passed = 0
$Failed = 0

"PART 1B - AUTOMATED QUALITY HARNESS" | Out-File $LogPath
"Timestamp: $(Get-Date -Format o)" | Out-File $LogPath -Append
"Project: $ProjectRoot" | Out-File $LogPath -Append
"Model: qwen2.5:3b" | Out-File $LogPath -Append
"==================================================" | Out-File $LogPath -Append

function Invoke-Check {
    param(
        [string]$Name,
        [string]$Executable,
        [string[]]$Arguments
    )

    Write-Host "`nRunning: $Name" -ForegroundColor Cyan
    " `nRunning: $Name" | Out-File $LogPath -Append

    & $Executable @Arguments *> $TempOutput
    $ExitCode = $LASTEXITCODE

    Get-Content $TempOutput | Tee-Object -FilePath $LogPath -Append

    if ($ExitCode -eq 0) {
        Write-Host "$Name : PASS" -ForegroundColor Green
        "RESULT: PASS (exit code $ExitCode)" | Out-File $LogPath -Append
        $script:Passed++
    }
    else {
        Write-Host "$Name : FAIL (exit code $ExitCode)" -ForegroundColor Red
        "RESULT: FAIL (exit code $ExitCode)" | Out-File $LogPath -Append
        $script:Failed++
    }
}

Invoke-Check "Pytest automated tests" "python" @("-m", "pytest", "tests", "-v")

Invoke-Check "Ruff lint" "python" @("-m", "ruff", "check", "src", "evals", "tests")

Invoke-Check "Ruff format check" "python" @("-m", "ruff", "format", "--check", "src", "evals", "tests")

Invoke-Check "Bandit security scan" "python" @("-m", "bandit", "-r", "src", "evals", "-ll")

" `n==================================================" | Out-File $LogPath -Append
"Passed: $Passed" | Out-File $LogPath -Append
"Failed: $Failed" | Out-File $LogPath -Append
"Completed: $(Get-Date -Format o)" | Out-File $LogPath -Append

Write-Host "`n========================================"
Write-Host "Harness completed."
Write-Host "Passed: $Passed"
Write-Host "Failed: $Failed"
Write-Host "Report: $LogPath"

Remove-Item $TempOutput -ErrorAction SilentlyContinue

if ($Failed -gt 0) {
    exit 1
}

exit 0
