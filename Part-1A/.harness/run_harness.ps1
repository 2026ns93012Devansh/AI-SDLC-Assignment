# Part-1A Automated Quality Harness
# Run from the Part-1A project directory.

$ErrorActionPreference = "Continue"

$ProjectRoot = Split-Path -Parent $PSScriptRoot
$EvidenceDir = Join-Path $ProjectRoot "evidence"
$Timestamp = Get-Date -Format "yyyyMMdd_HHmmss"
$ReportFile = Join-Path $EvidenceDir "harness_$Timestamp.txt"

New-Item -ItemType Directory -Force -Path $EvidenceDir | Out-Null

$Checks = @(
    @{
        Name = "Pytest"
        Command = "python -m pytest -v"
    },
    @{
        Name = "Ruff lint"
        Command = "python -m ruff check ."
    },
    @{
        Name = "Ruff format"
        Command = "python -m ruff format --check ."
    },
    @{
        Name = "Bandit security"
        Command = "python -m bandit -r smart_todo"
    }
)

$Results = @()

"PART-1A AUTOMATED HARNESS REPORT" | Out-File $ReportFile
"Timestamp: $(Get-Date -Format 'yyyy-MM-dd HH:mm:ss')" | Out-File $ReportFile -Append
"Project: $ProjectRoot" | Out-File $ReportFile -Append
"========================================" | Out-File $ReportFile -Append

foreach ($Check in $Checks) {
    Write-Host "`nRunning: $($Check.Name)" -ForegroundColor Cyan

    " " | Out-File $ReportFile -Append
    "CHECK: $($Check.Name)" | Out-File $ReportFile -Append
    "COMMAND: $($Check.Command)" | Out-File $ReportFile -Append

    $Output = Invoke-Expression "$($Check.Command) 2>&1"
    $ExitCode = $LASTEXITCODE

    $Output | Tee-Object -FilePath $ReportFile -Append

    if ($ExitCode -eq 0) {
        $Status = "PASS"
        Write-Host "$Status - $($Check.Name)" -ForegroundColor Green
    }
    else {
        $Status = "FAIL"
        Write-Host "$Status - $($Check.Name)" -ForegroundColor Red
    }

    $Results += [PSCustomObject]@{
        Check = $Check.Name
        Status = $Status
        ExitCode = $ExitCode
    }
}

" " | Out-File $ReportFile -Append
"FINAL SUMMARY" | Out-File $ReportFile -Append
$Results | Format-Table -AutoSize | Out-String | Out-File $ReportFile -Append

Write-Host "`n========== HARNESS SUMMARY ==========" -ForegroundColor Cyan
$Results | Format-Table -AutoSize

Write-Host "Report saved to: $ReportFile" -ForegroundColor Yellow

if ($Results.Status -contains "FAIL") {
    exit 1
}

exit 0