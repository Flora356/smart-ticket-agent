$ErrorActionPreference = "Stop"

$ProjectRoot = Split-Path -Parent $PSScriptRoot
Set-Location $ProjectRoot

if (Test-Path ".\.venv\Scripts\python.exe") {
    $Python = ".\.venv\Scripts\python.exe"
} else {
    $Python = "python"
}

Write-Host "[1/3] Running tests..."
& $Python -m pytest

Write-Host "[2/3] Running benchmark..."
& $Python -m app.cli benchmark `
    --dataset benchmark/datasets/tickets_l1_l3.jsonl `
    --database benchmark.db `
    --output reports/benchmark_report.json

Write-Host "[3/3] Checking runtime..."
& $Python -m app.cli health --database ticket_agent.db
