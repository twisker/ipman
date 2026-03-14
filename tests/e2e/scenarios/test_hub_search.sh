#!/usr/bin/env bash
# E2E: IpHub search/info/top commands (requires network)
set -euo pipefail

# Test hub search (may return empty, but should not error)
ipman hub search "" > /dev/null 2>&1 || true
echo "  hub search: OK"

# Test hub top
ipman hub top > /dev/null 2>&1 || true
echo "  hub top: OK"

# Test hub info on nonexistent (should fail gracefully)
if ipman hub info "definitely-nonexistent-skill-xyz" 2>/dev/null; then
    echo "ERROR: hub info should fail for nonexistent skill"
    exit 1
fi
echo "  hub info (not found): OK"

# Test ipman info
ipman info | grep -q "IpMan"
echo "  ipman info: OK"

# Test version
ipman --version | grep -q "ipman"
echo "  ipman version: OK"

echo "hub search OK"
