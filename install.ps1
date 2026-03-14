param(
    [string]$Version = "latest",
    [string]$InstallRoot = "$env:LOCALAPPDATA\\Programs\\skb-mcp-server",
    [switch]$RegisterClaude,
    [switch]$BootstrapModel,
    [string]$ProjectRoot = ""
)

$ErrorActionPreference = "Stop"
$Repo = "ssheeriin/super-kb"
$StateDir = Join-Path $env:LOCALAPPDATA "skb-mcp-server"
$ManifestPath = Join-Path $StateDir "install-manifest.json"

function Get-ReleaseBaseUrl {
    param([string]$RequestedVersion)
    if ($RequestedVersion -eq "latest") {
        return "https://github.com/$Repo/releases/latest/download"
    }
    if (-not $RequestedVersion.StartsWith("v")) {
        $RequestedVersion = "v$RequestedVersion"
    }
    return "https://github.com/$Repo/releases/download/$RequestedVersion"
}

function Add-UserPathEntry {
    param([string]$Entry)
    $userPath = [Environment]::GetEnvironmentVariable("Path", "User")
    $entries = @()
    if ($userPath) {
        $entries = $userPath -split ";" | Where-Object { $_ }
    }
    if ($entries -contains $Entry) {
        return $false
    }
    $updated = @($entries + $Entry) -join ";"
    [Environment]::SetEnvironmentVariable("Path", $updated, "User")
    return $true
}

function Write-InstallManifest {
    param(
        [string]$InstallRootValue,
        [string]$CurrentDirValue,
        [string]$ExePathValue,
        [bool]$PathUpdatedValue,
        [bool]$ClaudeRegisteredValue
    )
    New-Item -ItemType Directory -Path $StateDir -Force | Out-Null
    [ordered]@{
        InstallRoot = $InstallRootValue
        CurrentDir = $CurrentDirValue
        ExecutablePath = $ExePathValue
        PathEntry = $CurrentDirValue
        PathUpdated = $PathUpdatedValue
        ClaudeServerName = "skb"
        ClaudeRegistered = $ClaudeRegisteredValue
    } | ConvertTo-Json | Set-Content -Encoding UTF8 -Path $ManifestPath
}

$assetName = "skb-mcp-server-windows-x64.zip"
$baseUrl = Get-ReleaseBaseUrl -RequestedVersion $Version
$tempDir = Join-Path ([System.IO.Path]::GetTempPath()) ("skb-install-" + [Guid]::NewGuid().ToString("N"))
New-Item -ItemType Directory -Path $tempDir | Out-Null

try {
    $checksumPath = Join-Path $tempDir "SHA256SUMS.txt"
    $archivePath = Join-Path $tempDir $assetName
    Write-Warning "The Windows standalone bundle is currently alpha and has CI smoke coverage only."
    Write-Host "Downloading $assetName from $baseUrl"
    Invoke-WebRequest -Uri "$baseUrl/SHA256SUMS.txt" -OutFile $checksumPath
    Invoke-WebRequest -Uri "$baseUrl/$assetName" -OutFile $archivePath

    $checksumLine = Select-String -Path $checksumPath -Pattern " $assetName$" | Select-Object -First 1
    if (-not $checksumLine) {
        throw "Could not find checksum for $assetName"
    }
    $expectedHash = ($checksumLine.Line -split "\s+")[0].ToLowerInvariant()
    $actualHash = (Get-FileHash -Algorithm SHA256 -Path $archivePath).Hash.ToLowerInvariant()
    if ($expectedHash -ne $actualHash) {
        throw "Checksum mismatch for $assetName"
    }

    $extractDir = Join-Path $tempDir "extract"
    Expand-Archive -Path $archivePath -DestinationPath $extractDir -Force

    $bundleDir = Join-Path $extractDir "skb-mcp-server"
    $exePath = Join-Path $bundleDir "skb-mcp-server.exe"
    if (-not (Test-Path $exePath)) {
        throw "Downloaded archive does not contain skb-mcp-server.exe"
    }

    $currentDir = Join-Path $InstallRoot "current"
    if (Test-Path $currentDir) {
        Remove-Item -Recurse -Force $currentDir
    }
    New-Item -ItemType Directory -Path $InstallRoot -Force | Out-Null
    Move-Item -Path $bundleDir -Destination $currentDir

    $pathUpdated = Add-UserPathEntry -Entry $currentDir
    $claudeRegistered = $false
    Write-Host "Installed SKB to $currentDir"
    if ($pathUpdated) {
        Write-Host "Added $currentDir to the user PATH. Open a new shell to pick it up."
    } else {
        Write-Host "$currentDir is already on the user PATH."
    }

    if ($RegisterClaude) {
        if (Get-Command claude -ErrorAction SilentlyContinue) {
            & claude mcp get skb *> $null
            if ($LASTEXITCODE -eq 0) {
                Write-Host "Claude MCP server 'skb' is already configured."
            } else {
                & claude mcp add skb --scope user -- $exePath
                $claudeRegistered = $true
            }
        } else {
            Write-Warning "Claude Code CLI not found on PATH; skipping registration."
        }
    }

    if ($BootstrapModel) {
        & $exePath bootstrap-model
    }

    if ($ProjectRoot) {
        & $exePath write-mcp-config --project-root $ProjectRoot
    }

    Write-InstallManifest `
        -InstallRootValue $InstallRoot `
        -CurrentDirValue $currentDir `
        -ExePathValue $exePath `
        -PathUpdatedValue $pathUpdated `
        -ClaudeRegisteredValue $claudeRegistered

    Write-Host ""
    Write-Host "Next steps:"
    Write-Host "  1. Open a new PowerShell window if PATH was updated."
    Write-Host "  2. Verify the executable: skb-mcp-server version"
    if (-not $RegisterClaude) {
        Write-Host "  3. Register Claude globally if desired: claude mcp add skb --scope user -- skb-mcp-server"
    }
    Write-Host "  4. For a shared repo, write a project .mcp.json: skb-mcp-server write-mcp-config --project-root C:\\path\\to\\project"
    Write-Host "  5. In a project, ask Claude to run: Provision SKB in this project"
    Write-Host "  6. Uninstall later with: irm https://raw.githubusercontent.com/$Repo/main/uninstall.ps1 | iex"
}
finally {
    if (Test-Path $tempDir) {
        Remove-Item -Recurse -Force $tempDir
    }
}
