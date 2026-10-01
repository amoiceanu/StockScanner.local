$ErrorActionPreference = "Stop"
$ProjectDir = Split-Path -Parent $MyInvocation.MyCommand.Path
Set-Location -LiteralPath $ProjectDir

$PythonCommand = Get-Command py -ErrorAction SilentlyContinue
if ($PythonCommand) {
    & py -3.12 -m venv .venv
} else {
    $PythonCommand = Get-Command python -ErrorAction SilentlyContinue
    if (-not $PythonCommand -or $PythonCommand.Source -like "*WindowsApps*") {
        throw "Python 3.12+ was not found. Install it from https://www.python.org/downloads/ and enable Add Python to PATH."
    }
    & python -m venv .venv
}

$VenvPython = Join-Path $ProjectDir ".venv\Scripts\python.exe"
& $VenvPython -m pip install --upgrade pip
& $VenvPython -m pip install -r requirements.txt
New-Item -ItemType Directory -Force -Path data, data\cache, logs | Out-Null
if (-not (Test-Path -LiteralPath ".env")) { Copy-Item -LiteralPath ".env.example" -Destination ".env" }
& $VenvPython -m app.cli init-db
Write-Host "Setup complete. Edit .env, then run .\run_windows.ps1" -ForegroundColor Green
