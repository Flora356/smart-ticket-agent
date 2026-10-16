# Start backend (FastAPI, port 8000) and frontend (Vite, port 5173) together.
$ErrorActionPreference = "Stop"
$root = $PSScriptRoot
$nodeBin = "C:\Users\admin\.cache\codex-runtimes\codex-primary-runtime\dependencies\node\bin"

if (Test-Path $nodeBin) {
    $env:Path = "$nodeBin;$env:Path"
}

Write-Host "Starting backend on http://127.0.0.1:8000 ..." -ForegroundColor Cyan
Start-Process -FilePath "python" `
    -ArgumentList "-m", "uvicorn", "app.api.server:app", "--host", "127.0.0.1", "--port", "8000" `
    -WorkingDirectory $root -WindowStyle Hidden

Start-Sleep -Seconds 3

Write-Host "Starting frontend on http://127.0.0.1:5173 ..." -ForegroundColor Cyan
Start-Process -FilePath "node" `
    -ArgumentList "node_modules\vite\bin\vite.js", "--host", "127.0.0.1", "--port", "5173" `
    -WorkingDirectory (Join-Path $root "frontend") -WindowStyle Hidden

Start-Sleep -Seconds 3

Write-Host ""
Write-Host "Ready:" -ForegroundColor Green
Write-Host "  App     http://127.0.0.1:5173/"
Write-Host "  API     http://127.0.0.1:8000/docs"
Write-Host "  Demo    http://127.0.0.1:5173/standalone.html"
