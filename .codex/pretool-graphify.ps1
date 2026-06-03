$ErrorActionPreference = "Stop"

$repoRoot = (Resolve-Path (Join-Path $PSScriptRoot "..")).Path
Set-Location $repoRoot

$graphPath = Join-Path $repoRoot "graphify-out/graph.json"
$reportPath = Join-Path $repoRoot "graphify-out/GRAPH_REPORT.md"

if ((Test-Path $graphPath) -and (Test-Path $reportPath)) {
    $payload = @{
        hookSpecificOutput = @{
            hookEventName = "PreToolUse"
            additionalContext = "graphify: Knowledge graph exists. Read graphify-out/GRAPH_REPORT.md for god nodes and community structure before searching raw files."
        }
    } | ConvertTo-Json -Compress
    Write-Output $payload
}

exit 0
