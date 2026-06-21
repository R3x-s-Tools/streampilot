param(
    [string]$Version = "local"
)

$ErrorActionPreference = "Stop"

$AppName = "DadR3x Command Center"
$RootDir = Resolve-Path "$PSScriptRoot\..\.."
Set-Location $RootDir

$ZipName = "DadR3x_Command_Center_${Version}_Windows.zip"

Write-Host "Building Windows app"
Write-Host "Version: $Version"
Write-Host "Python:"
python --version
Write-Host "Spec: DadR3xCommandCenter.spec"

python -m pip install --upgrade pip
pip install -r requirements.txt
pip install pyinstaller

Remove-Item -Recurse -Force dist, release, .pyinstaller_build -ErrorAction SilentlyContinue

pyinstaller --noconfirm --workpath .pyinstaller_build DadR3xCommandCenter.spec

New-Item -ItemType Directory -Force release | Out-Null

$AppDir = "dist\$AppName"

if (Test-Path $AppDir) {
    Compress-Archive -Path $AppDir -DestinationPath "release\$ZipName" -Force

    $hash = Get-FileHash "release\$ZipName" -Algorithm SHA256
    "$($hash.Hash.ToLower())  $ZipName" | Out-File -Encoding ascii "release\$ZipName.sha256"

    Write-Host "Built release\$ZipName"
} else {
    Write-Host "ERROR: $AppDir not found"
    Get-ChildItem -Recurse dist
    exit 1
}
