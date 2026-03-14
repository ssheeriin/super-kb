#!/usr/bin/env bash
set -eu

REPO="ssheeriin/super-kb"
VERSION="latest"
INSTALL_ROOT="${SKB_INSTALL_ROOT:-$HOME/.local/opt/skb-mcp-server}"
BIN_DIR="${SKB_BIN_DIR:-$HOME/.local/bin}"
REGISTER_CLAUDE=0
BOOTSTRAP_MODEL=0
PROJECT_ROOT=""

usage() {
  cat <<'EOF'
Install SKB from GitHub Releases.

Usage:
  install.sh [--version vX.Y.Z] [--install-root PATH] [--bin-dir PATH] [--register-claude] [--bootstrap-model] [--write-project-mcp PATH]
EOF
}

while [ "$#" -gt 0 ]; do
  case "$1" in
    --version)
      VERSION="$2"
      shift 2
      ;;
    --install-root)
      INSTALL_ROOT="$2"
      shift 2
      ;;
    --bin-dir)
      BIN_DIR="$2"
      shift 2
      ;;
    --register-claude)
      REGISTER_CLAUDE=1
      shift
      ;;
    --bootstrap-model)
      BOOTSTRAP_MODEL=1
      shift
      ;;
    --write-project-mcp)
      PROJECT_ROOT="$2"
      shift 2
      ;;
    -h|--help)
      usage
      exit 0
      ;;
    *)
      echo "Unknown argument: $1" >&2
      usage >&2
      exit 1
      ;;
  esac
done

need_cmd() {
  if ! command -v "$1" >/dev/null 2>&1; then
    echo "Missing required command: $1" >&2
    exit 1
  fi
}

download() {
  url="$1"
  output="$2"
  if command -v curl >/dev/null 2>&1; then
    curl -fsSL "$url" -o "$output"
    return
  fi
  if command -v wget >/dev/null 2>&1; then
    wget -q "$url" -O "$output"
    return
  fi
  echo "Need curl or wget to download release assets." >&2
  exit 1
}

verify_sha256() {
  file="$1"
  expected="$2"
  if command -v sha256sum >/dev/null 2>&1; then
    actual=$(sha256sum "$file" | awk '{print $1}')
  elif command -v shasum >/dev/null 2>&1; then
    actual=$(shasum -a 256 "$file" | awk '{print $1}')
  else
    echo "Need sha256sum or shasum to verify release assets." >&2
    exit 1
  fi

  if [ "$actual" != "$expected" ]; then
    echo "Checksum mismatch for $file" >&2
    echo "Expected: $expected" >&2
    echo "Actual:   $actual" >&2
    exit 1
  fi
}

detect_platform_id() {
  os_name=$(uname -s)
  arch_name=$(uname -m)

  case "$os_name:$arch_name" in
    Darwin:arm64) echo "macos-arm64" ;;
    Darwin:x86_64) echo "macos-x64" ;;
    Linux:x86_64) echo "linux-x64" ;;
    *)
      echo "Unsupported platform: $os_name $arch_name" >&2
      exit 1
      ;;
  esac
}

print_platform_notice() {
  case "$1" in
    linux-x64)
      echo "Warning: the Linux standalone bundle is currently alpha and has CI smoke coverage only." >&2
      ;;
  esac
}

need_cmd tar
platform_id=$(detect_platform_id)
print_platform_notice "$platform_id"
asset_name="skb-mcp-server-${platform_id}.tar.gz"
release_ref="$VERSION"
if [ "$release_ref" != "latest" ]; then
  case "$release_ref" in
    v*) ;;
    *) release_ref="v$release_ref" ;;
  esac
  base_url="https://github.com/${REPO}/releases/download/${release_ref}"
else
  base_url="https://github.com/${REPO}/releases/latest/download"
fi

tmp_dir=$(mktemp -d)
trap 'rm -rf "$tmp_dir"' EXIT

echo "Downloading $asset_name from $base_url"
download "${base_url}/SHA256SUMS.txt" "$tmp_dir/SHA256SUMS.txt"
download "${base_url}/${asset_name}" "$tmp_dir/${asset_name}"

expected_sha=$(awk -v asset="$asset_name" '$2 == asset { print $1 }' "$tmp_dir/SHA256SUMS.txt")
if [ -z "$expected_sha" ]; then
  echo "Could not find checksum for $asset_name" >&2
  exit 1
fi
verify_sha256 "$tmp_dir/${asset_name}" "$expected_sha"

extract_dir="$tmp_dir/extract"
mkdir -p "$extract_dir"
tar -xzf "$tmp_dir/${asset_name}" -C "$extract_dir"

bundle_dir="$extract_dir/skb-mcp-server"
if [ ! -x "$bundle_dir/skb-mcp-server" ]; then
  echo "Downloaded archive does not contain skb-mcp-server executable." >&2
  exit 1
fi

current_dir="$INSTALL_ROOT/current"
mkdir -p "$INSTALL_ROOT" "$BIN_DIR"
rm -rf "$current_dir"
mv "$bundle_dir" "$current_dir"
ln -sfn "$current_dir/skb-mcp-server" "$BIN_DIR/skb-mcp-server"

echo "Installed SKB to $current_dir"
echo "Linked executable to $BIN_DIR/skb-mcp-server"

case ":$PATH:" in
  *":$BIN_DIR:"*) ;;
  *)
    echo
    echo "Add this directory to PATH if needed:"
    echo "  export PATH=\"$BIN_DIR:\$PATH\""
    ;;
esac

if [ "$REGISTER_CLAUDE" -eq 1 ]; then
  if command -v claude >/dev/null 2>&1; then
    if claude mcp get skb >/dev/null 2>&1; then
      echo "Claude MCP server 'skb' is already configured."
    else
      claude mcp add skb --scope user -- skb-mcp-server
    fi
  else
    echo "Claude Code CLI not found on PATH; skipping registration." >&2
  fi
fi

if [ "$BOOTSTRAP_MODEL" -eq 1 ]; then
  "$current_dir/skb-mcp-server" bootstrap-model
fi

if [ -n "$PROJECT_ROOT" ]; then
  "$current_dir/skb-mcp-server" write-mcp-config --project-root "$PROJECT_ROOT"
fi

echo
echo "Next steps:"
echo "  1. Verify the executable: skb-mcp-server version"
if [ "$REGISTER_CLAUDE" -eq 0 ]; then
  echo "  2. Register Claude globally if desired: claude mcp add skb --scope user -- skb-mcp-server"
fi
echo "  3. For a shared repo, write a project .mcp.json: skb-mcp-server write-mcp-config --project-root /path/to/project"
echo "  4. In a project, ask Claude to run: Provision SKB in this project"
