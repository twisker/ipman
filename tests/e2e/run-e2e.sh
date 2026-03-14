#!/usr/bin/env bash
# Local entry point for running E2E tests via Docker Compose
# Usage:
#   ./tests/e2e/run-e2e.sh                    # both agents
#   ./tests/e2e/run-e2e.sh claude-code         # claude-code only
#   ./tests/e2e/run-e2e.sh openclaw            # openclaw only
#   IPMAN_VERSION=0.2.0 ./tests/e2e/run-e2e.sh # specific version
set -euo pipefail

cd "$(dirname "$0")"

AGENT="${1:-all}"

if [ "$AGENT" = "all" ]; then
    echo "Running E2E tests for all agents..."
    docker compose build
    docker compose run --rm claude-code
    docker compose run --rm openclaw
elif [ "$AGENT" = "claude-code" ] || [ "$AGENT" = "openclaw" ]; then
    echo "Running E2E tests for $AGENT..."
    docker compose build "$AGENT"
    docker compose run --rm "$AGENT"
else
    echo "Usage: $0 [claude-code|openclaw|all]"
    exit 1
fi
