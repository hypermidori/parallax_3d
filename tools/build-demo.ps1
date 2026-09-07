param(
    [string]$Name = 'demo',
    [switch]$SkipRender
)
$ErrorActionPreference = 'Stop'
if ($Name -notmatch '^[a-zA-Z0-9][a-zA-Z0-9_-]*$') {
    throw 'Name must contain only ASCII letters, numbers, underscore or hyphen.'
}
$root = Split-Path $PSScriptRoot -Parent
$destination = Join-Path $root "output/$Name"
if (Test-Path -LiteralPath $destination) {
    throw "Output already exists. Choose another -Name to preserve previous work: $destination"
}
$script = Join-Path $root 'blender_scripts/create_demo.py'
$scriptArgs = @('--output', $destination)
if ($SkipRender) { $scriptArgs += '--skip-render' }
& "$PSScriptRoot/blender.ps1" --background --factory-startup --python-exit-code 1 --python $script '--' @scriptArgs
& "$PSScriptRoot/blender.ps1" --background --factory-startup --python-exit-code 1 --python (Join-Path $root 'blender_scripts/verify_exports.py') '--' --output $destination
Write-Host "Build and GLB import verification completed: $destination"
