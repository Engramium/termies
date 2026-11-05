# Install Termies themes into Warp on Windows.
#
# Run without a clone:
#   irm https://raw.githubusercontent.com/Engramium/termies/main/install-warp.ps1 | iex
#
# Install only some themes by setting $env:TERMIES_THEMES first, for example:
#   $env:TERMIES_THEMES = 'soft-chat,paper-dark'
#   irm https://raw.githubusercontent.com/Engramium/termies/main/install-warp.ps1 | iex

$ErrorActionPreference = 'Stop'

# Windows PowerShell 5.1 may default to an older TLS version that GitHub rejects.
[Net.ServicePointManager]::SecurityProtocol = [Net.ServicePointManager]::SecurityProtocol -bor [Net.SecurityProtocolType]::Tls12

$api = 'https://api.github.com/repos/Engramium/termies/contents/themes'
$raw = 'https://raw.githubusercontent.com/Engramium/termies/main/themes'
$dest = Join-Path $env:APPDATA 'warp\Warp\data\themes'

$listing = Invoke-RestMethod -Uri $api -Headers @{ 'User-Agent' = 'termies-installer' }
$available = $listing | Where-Object { $_.name -like '*.yaml' } | ForEach-Object { $_.name }
if (-not $available) {
    throw 'No themes found in the Termies repository.'
}

$wanted = $available
if ($env:TERMIES_THEMES) {
    $wanted = @()
    foreach ($name in ($env:TERMIES_THEMES -split ',')) {
        $file = $name.Trim() + '.yaml'
        if ($available -notcontains $file) {
            $names = ($available | ForEach-Object { $_ -replace '\.yaml$', '' }) -join ', '
            throw "No theme named '$($name.Trim())'. Available themes: $names"
        }
        $wanted += $file
    }
}

New-Item -ItemType Directory -Force -Path $dest | Out-Null
foreach ($file in $wanted) {
    Invoke-WebRequest -Uri "$raw/$file" -OutFile (Join-Path $dest $file) -UseBasicParsing
    Write-Host "Installed $($file -replace '\.yaml$', '') -> $dest"
}

Write-Host 'Done. In Warp, open Settings > Appearance > Themes and pick a theme.'
