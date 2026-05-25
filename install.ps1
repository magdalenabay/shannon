# shannon installer (Windows)
#
# Usage:
#   iwr -useb https://raw.githubusercontent.com/magdalenabay/shannon/main/install.ps1 | iex
#
# Environment:
#   $env:SHANNON_REPO   Override the repo URL
#   $env:SHANNON_REF    Git ref to install (default: main)

$ErrorActionPreference = "Stop"

$repo = if ($env:SHANNON_REPO) { $env:SHANNON_REPO } else { "https://github.com/magdalenabay/shannon" }
$ref  = if ($env:SHANNON_REF)  { $env:SHANNON_REF }  else { "main" }

if (-not (Get-Command uv -ErrorAction SilentlyContinue)) {
    Write-Host "-> uv not found; installing uv..."
    powershell -ExecutionPolicy ByPass -c "irm https://astral.sh/uv/install.ps1 | iex"
    $env:PATH = "$env:USERPROFILE\.local\bin;$env:PATH"
    if (-not (Get-Command uv -ErrorAction SilentlyContinue)) {
        throw "uv install completed but 'uv' is still not on PATH. Open a new shell and re-run."
    }
}

Write-Host "-> installing shannon from $repo@$ref..."
uv tool install --force "git+$repo@$ref"

Write-Host ""
Write-Host "shannon installed."
Write-Host ""
Write-Host "Try:"
Write-Host "  shannon --doctor          # see what's installed"
Write-Host "  shannon --install-all     # install light backends"
Write-Host "  shannon C:\file.mp4 mp3   # do a conversion"
