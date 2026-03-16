#!/usr/bin/env bash
# E2E: Environment create → activate → list → status → deactivate → delete
set -euo pipefail

AGENT="${1:-claude-code}"
WORKDIR=$(mktemp -d)
cd "$WORKDIR"

# Initialize a fake project dir for the agent
if [ "$AGENT" = "claude-code" ]; then
    mkdir -p .claude
elif [ "$AGENT" = "openclaw" ]; then
    mkdir -p .openclaw
fi

# Create
ipman env create e2e-test --agent "$AGENT"

# List (should show e2e-test)
ipman env list | grep -q "e2e-test"

# Activate
ipman env activate e2e-test

# Status
ipman env status | grep -q "e2e-test"

# Deactivate
ipman env deactivate

# Delete
ipman env delete e2e-test

# Verify deleted (list should NOT contain e2e-test)
if ipman env list 2>/dev/null | grep -q "e2e-test"; then
    echo "ERROR: environment still exists after delete"
    exit 1
fi

rm -rf "$WORKDIR"
echo "env lifecycle OK"
