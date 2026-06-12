param(
    [int]$Port = 8501
)

$ErrorActionPreference = "Stop"
$repoRoot = Split-Path -Parent $PSScriptRoot
Set-Location $repoRoot

python -m streamlit run app.py --server.port $Port --server.headless true
