$ErrorActionPreference = 'Stop'
$version = '4.5.13'
$root = Split-Path $PSScriptRoot -Parent
$toolsDir = Join-Path $root '.tools'
$package = "blender-$version-windows-x64"
$installDir = Join-Path $toolsDir $package
$exe = Join-Path $installDir 'blender.exe'
if (Test-Path -LiteralPath $exe) {
    & $exe --version
    if ($LASTEXITCODE -ne 0) { throw 'Blender version check failed.' }
    exit 0
}
if ([System.Runtime.InteropServices.RuntimeInformation]::OSArchitecture -ne 'X64') {
    throw 'This setup script requires Windows x64.'
}
New-Item -ItemType Directory -Path $toolsDir -Force | Out-Null
$baseUrl = 'https://download.blender.org/release/Blender4.5'
$zip = Join-Path $toolsDir "$package.zip"
$hashFile = Join-Path $toolsDir "blender-$version.sha256"
Invoke-WebRequest -Uri "$baseUrl/blender-$version.sha256" -OutFile $hashFile
if (-not (Test-Path -LiteralPath $zip)) {
    Write-Host "Downloading Blender $version (approximately 380 MB)..."
    $partial = "$zip.partial"
    Invoke-WebRequest -Uri "$baseUrl/$package.zip" -OutFile $partial
    Move-Item -LiteralPath $partial -Destination $zip -Force
}
$hashLine = Get-Content -LiteralPath $hashFile | Where-Object { $_ -match "\s+\*?$([regex]::Escape($package)).zip$" } | Select-Object -First 1
if (-not $hashLine) { throw 'Package not found in official checksum file.' }
$expected = ($hashLine -split '\s+')[0]
$actual = (Get-FileHash -LiteralPath $zip -Algorithm SHA256).Hash
if ($actual -ne $expected) { throw "Checksum mismatch. Remove the invalid archive manually: $zip" }
Write-Host 'SHA256 verified. Extracting...'
Expand-Archive -LiteralPath $zip -DestinationPath $toolsDir -Force
New-Item -ItemType Directory -Path (Join-Path $installDir 'portable') -Force | Out-Null
& $exe --version
if ($LASTEXITCODE -ne 0) { throw 'Blender version check failed.' }
Write-Host "Ready: $exe"
