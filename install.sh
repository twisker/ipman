#!/usr/bin/env bash
# IpMan one-line installer for Linux / macOS
# Usage: curl -sSL https://raw.githubusercontent.com/twisker/ipman/main/install.sh | bash
set -euo pipefail

PACKAGE="ipman-cli"

echo "Installing IpMan..."

# Prefer uv, fall back to pip
if command -v uv >/dev/null 2>&1; then
    uv pip install "$PACKAGE"
elif command -v pip3 >/dev/null 2>&1; then
    pip3 install --user "$PACKAGE"
elif command -v pip >/dev/null 2>&1; then
    pip install --user "$PACKAGE"
else
    echo "Error: Python pip not found. Install Python 3.10+ first."
    exit 1
fi

echo ""
echo "IpMan installed successfully!"
echo "Run 'ipman --version' to verify."
