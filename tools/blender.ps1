# Pass Blender CLI arguments directly: .\tools\blender.ps1 --background --python ...
$ErrorActionPreference = 'Stop'
$root = Split-Path $PSScriptRoot -Parent
$exe = Join-Path $root '.tools/blender-4.5.13-windows-x64/blender.exe'
if (-not (Test-Path -LiteralPath $exe)) {
    throw 'Blender is not installed. Run tools/setup-blender.ps1 first.'
}
& $exe @args
if ($LASTEXITCODE -ne 0) { throw "Blender failed with exit code $LASTEXITCODE" }
