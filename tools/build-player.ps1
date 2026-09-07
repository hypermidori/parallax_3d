param([string]$Name = 'player-next', [switch]$SkipRender)
$ErrorActionPreference='Stop'
if ($Name -notmatch '^[a-zA-Z0-9][a-zA-Z0-9_-]*$') { throw 'Use letters, numbers, underscore or hyphen for Name.' }
$root=Split-Path $PSScriptRoot -Parent
$destination=Join-Path $root "output/$Name"
if (Test-Path -LiteralPath $destination) { throw "Choose a new Name; output already exists: $destination" }
$scriptArgs=@('--output',$destination)
if ($SkipRender) { $scriptArgs+='--skip-render' }
& "$PSScriptRoot/blender.ps1" --background --factory-startup --python-exit-code 1 --python (Join-Path $root 'blender_scripts/create_player.py') '--' @scriptArgs
& "$PSScriptRoot/blender.ps1" --background --factory-startup --python-exit-code 1 --python (Join-Path $root 'blender_scripts/verify_player.py') '--' --output $destination
