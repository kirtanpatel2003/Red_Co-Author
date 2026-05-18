# Red_Co-Author Windows installer (PowerShell).
# Mirrors setup.sh exactly: pulls Ollama models, builds a Python venv,
# installs requirements.txt, and smoke-imports the ollama client.
#
# Usage:
#   .\setup.ps1
#
# If PowerShell blocks unsigned scripts on your machine:
#   powershell -ExecutionPolicy Bypass -File .\setup.ps1
#
# Idempotent: safe to re-run; skips anything already in place.
#
# Models pulled:
#   v1: mistral (drafter), qwen3:8b (target)
#   v2: llama3 (judge)
#   v5: gemma2, phi3 (additional targets)
#   v7: nomic-embed-text (embeddings for the trained monitor)

$ErrorActionPreference = "Stop"

$RepoRoot = Split-Path -Parent $MyInvocation.MyCommand.Path
Set-Location $RepoRoot

$VenvDir        = ".venv"
$RequiredModels = @("mistral", "qwen3:8b", "llama3", "gemma2", "phi3", "nomic-embed-text")

function Say($msg)  { Write-Host "[setup] $msg" -ForegroundColor Cyan }
function Warn($msg) { Write-Host "[warn]  $msg" -ForegroundColor Yellow }
function Die($msg)  { Write-Host "[fail]  $msg" -ForegroundColor Red; exit 1 }

# 1. Ollama binary
Say "checking ollama..."
if (-not (Get-Command ollama -ErrorAction SilentlyContinue)) {
    Die "ollama is not installed. Install from https://ollama.com/download/windows then re-run this script."
}
$ollamaVersion = (ollama --version 2>&1 | Select-Object -First 1)
Say "ollama $ollamaVersion"

# 2. Ollama daemon
$null = ollama list 2>&1
if ($LASTEXITCODE -ne 0) {
    Warn "ollama daemon not reachable. Start the Ollama app from the Start menu, then re-run."
    exit 1
}

# 3. Models (idempotent -- ollama pull is a no-op if already present)
$installedModels = (ollama list | Select-Object -Skip 1 | ForEach-Object { ($_ -split '\s+')[0] })
foreach ($model in $RequiredModels) {
    $present = ($installedModels -contains $model) -or ($installedModels -contains "$($model):latest")
    if ($present) {
        Say "model present: $model"
    } else {
        Say "pulling $model ..."
        ollama pull $model
        if ($LASTEXITCODE -ne 0) { Die "failed to pull $model" }
    }
}

# 4. Python venv
$pythonCmd = $null
if (Get-Command python -ErrorAction SilentlyContinue)      { $pythonCmd = "python" }
elseif (Get-Command python3 -ErrorAction SilentlyContinue) { $pythonCmd = "python3" }
else { Die "neither python nor python3 found. Install Python 3.11+ from https://www.python.org/downloads/ (tick 'Add Python to PATH')." }

if (-not (Test-Path $VenvDir)) {
    Say "creating venv at $VenvDir ..."
    & $pythonCmd -m venv $VenvDir
    if ($LASTEXITCODE -ne 0) { Die "venv creation failed" }
} else {
    Say "venv present: $VenvDir"
}

# 5. Python deps
$venvPython = Join-Path $VenvDir "Scripts\python.exe"
$venvPip    = Join-Path $VenvDir "Scripts\pip.exe"

Say "installing python deps from requirements.txt ..."
& $venvPython -m pip install --quiet --upgrade pip
if ($LASTEXITCODE -ne 0) { Die "pip self-upgrade failed" }
& $venvPip install --quiet -r requirements.txt
if ($LASTEXITCODE -ne 0) { Die "pip install -r requirements.txt failed" }

# 6. Smoke import
& $venvPython -c "import ollama"
if ($LASTEXITCODE -ne 0) { Die "python 'ollama' import failed after install" }

# 7. Optional: prime .env from the template if it's missing
if ((-not (Test-Path ".env")) -and (Test-Path ".env.example")) {
    Say "no .env yet -- to enable Laminar tracing later, copy the template:"
    Say "    Copy-Item .env.example .env    # then paste your LMNR_PROJECT_API_KEY"
}

Say "done. Activate with: .\.venv\Scripts\Activate.ps1"
Say "then run:           python run_pipeline.py --prompt `"how to hack Windows 10`" --domain cyberattack"
Say "or launch the UI:   streamlit run app.py"
