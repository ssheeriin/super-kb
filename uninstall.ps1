param(
    [string]$InstallRoot = "",
    [switch]$RemoveCache,
    [string]$RemoveProjectMcp = "",
    [switch]$Yes
)

$ErrorActionPreference = "Stop"
$Repo = "ssheeriin/super-kb"
$StateDir = Join-Path $env:LOCALAPPDATA "skb-mcp-server"
$ManifestPath = Join-Path $StateDir "install-manifest.json"

if (Test-Path $ManifestPath) {
    $manifest = Get-Content -Raw -Path $ManifestPath | ConvertFrom-Json
} else {
    $manifest = $null
}

if (-not $PSBoundParameters.ContainsKey("InstallRoot")) {
    if ($manifest -and $manifest.InstallRoot) {
        $InstallRoot = $manifest.InstallRoot
    } else {
        $InstallRoot = "$env:LOCALAPPDATA\\Programs\\skb-mcp-server"
    }
}

$currentDir = if ($manifest -and $manifest.CurrentDir -and -not $PSBoundParameters.ContainsKey("InstallRoot")) {
    $manifest.CurrentDir
} else {
    Join-Path $InstallRoot "current"
}
$exePath = if ($manifest -and $manifest.ExecutablePath -and -not $PSBoundParameters.ContainsKey("InstallRoot")) {
    $manifest.ExecutablePath
} else {
    Join-Path $currentDir "skb-mcp-server.exe"
}
$claudeServerName = if ($manifest -and $manifest.ClaudeServerName) { $manifest.ClaudeServerName } else { "skb" }
$claudeRegistered = [bool]($manifest -and $manifest.ClaudeRegistered)
$pathEntry = if ($manifest -and $manifest.PathEntry) { $manifest.PathEntry } else { $currentDir }
$pathUpdated = [bool]($manifest -and $manifest.PathUpdated)

function Remove-UserPathEntry {
    param([string]$Entry)
    $userPath = [Environment]::GetEnvironmentVariable("Path", "User")
    if (-not $userPath) {
        return $false
    }
    $entries = $userPath -split ";" | Where-Object { $_ -and $_ -ne $Entry }
    $updated = $entries -join ";"
    if ($updated -eq $userPath) {
        return $false
    }
    [Environment]::SetEnvironmentVariable("Path", $updated, "User")
    return $true
}

function Remove-ClaudeRegistration {
    if (-not (Get-Command claude -ErrorAction SilentlyContinue)) {
        Write-Warning "Claude Code CLI not found on PATH; skipping user MCP cleanup."
        return
    }
    $output = (& claude mcp get $claudeServerName 2>&1 | Out-String)
    if (-not $output) {
        return
    }
    if ($claudeRegistered -or $output.Contains($exePath)) {
        & claude mcp remove $claudeServerName -s user *> $null
        Write-Host "Removed Claude MCP server '$claudeServerName' from user config."
    }
}

function Remove-ProjectScopedMcp {
    if (-not $RemoveProjectMcp) {
        return
    }
    if (-not (Test-Path $exePath)) {
        Write-Warning "Cannot remove project .mcp.json entry because $exePath is not available."
        return
    }
    & $exePath remove-mcp-config --project-root $RemoveProjectMcp
}

if ($Yes) {
    # Accepted for parity with the shell script. Uninstall is non-interactive.
}

Remove-ProjectScopedMcp
Remove-ClaudeRegistration

$userPath = [Environment]::GetEnvironmentVariable("Path", "User")
if ($pathEntry -and ($pathUpdated -or ($userPath -and $userPath.Contains($pathEntry)))) {
    if (Remove-UserPathEntry -Entry $pathEntry) {
        Write-Host "Removed $pathEntry from the user PATH."
    }
}

if (Test-Path $currentDir) {
    Remove-Item -Recurse -Force $currentDir
    Write-Host "Removed $currentDir"
}

if (Test-Path $InstallRoot) {
    $remaining = Get-ChildItem -Force -ErrorAction SilentlyContinue $InstallRoot
    if (-not $remaining) {
        Remove-Item -Force $InstallRoot
    }
}

if (Test-Path $ManifestPath) {
    Remove-Item -Force $ManifestPath
}
if (Test-Path $StateDir) {
    $remaining = Get-ChildItem -Force -ErrorAction SilentlyContinue $StateDir
    if (-not $remaining) {
        Remove-Item -Force $StateDir
    }
}

if ($RemoveCache) {
    $homeDir = if ($env:HOME) { $env:HOME } else { $env:USERPROFILE }
    $cacheDir = Join-Path $homeDir ".skb"
    if (Test-Path $cacheDir) {
        Remove-Item -Recurse -Force $cacheDir
        Write-Host "Removed $cacheDir"
    }
}

Write-Host "SKB uninstall complete."
Write-Host "Project-local .skb/, .claude/, and CLAUDE.md files were left untouched."
Write-Host "If needed, remove them manually from specific repos."
