#!/usr/bin/env bash
# E2E: pack → produces .ip.yaml → installable
set -euo pipefail

AGENT="${1:-claude-code}"
WORKDIR=$(mktemp -d)
cd "$WORKDIR"

if [ "$AGENT" = "claude-code" ]; then mkdir -p .claude; else mkdir -p .openclaw; fi

# Pack (will have 0 skills in fresh env, but should succeed)
ipman pack --name e2e-roundtrip --version 1.0.0 --agent "$AGENT" \
    --output "$WORKDIR/e2e-roundtrip.ip.yaml"

# Verify file created with correct content
test -f "$WORKDIR/e2e-roundtrip.ip.yaml"
grep -q "name: e2e-roundtrip" "$WORKDIR/e2e-roundtrip.ip.yaml"
grep -q "version: 1.0.0" "$WORKDIR/e2e-roundtrip.ip.yaml"
grep -q "ipman install" "$WORKDIR/e2e-roundtrip.ip.yaml"

# Dry-run install from the packed file
ipman install "$WORKDIR/e2e-roundtrip.ip.yaml" --dry-run --no-vet

rm -rf "$WORKDIR"
echo "pack roundtrip OK"
