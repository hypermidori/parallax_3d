$ErrorActionPreference = 'Stop'
$projectRoot = Split-Path $PSScriptRoot -Parent
$nodeCommand = Get-Command node -ErrorAction SilentlyContinue
$nodeCandidates = @(
    (Join-Path $projectRoot '.tools/node-v24.14.0-win-x64/node.exe'),
    'C:/workspace/codex_sample/.tools/node-v24.14.0-win-x64/node.exe'
)
$nodeExe = if ($nodeCommand) { $nodeCommand.Source } else {
    $nodeCandidates | Where-Object { Test-Path -LiteralPath $_ } | Select-Object -First 1
}
if (-not $nodeExe) { throw 'Node.js 20.19+ or 22+ is required. Install Node.js and run npm ci.' }
if (-not (Test-Path -LiteralPath (Join-Path $projectRoot 'node_modules/vite/bin/vite.js'))) {
    throw 'Dependencies are missing. Run npm ci in the project directory first.'
}
Push-Location $projectRoot
try { & $nodeExe 'node_modules/vite/bin/vite.js' --host 127.0.0.1 --port 5180 --strictPort }
finally { Pop-Location }
