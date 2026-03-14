#!/usr/bin/env bash
# E2E test runner — executes all scenario scripts for the given agent
set -euo pipefail

AGENT="${1:-${AGENT:-claude-code}}"
PASS=0
FAIL=0
SKIP=0

echo "============================================"
echo "IpMan E2E Tests — Agent: $AGENT"
echo "ipman version: $(ipman --version 2>&1)"
echo "============================================"
echo ""

for scenario in /workspace/scenarios/test_*.sh; do
    name=$(basename "$scenario" .sh)
    echo -n "  $name ... "

    if bash "$scenario" "$AGENT" > /tmp/e2e-output.txt 2>&1; then
        echo "PASS"
        PASS=$((PASS + 1))
    else
        exit_code=$?
        if [ $exit_code -eq 77 ]; then
            echo "SKIP"
            SKIP=$((SKIP + 1))
        else
            echo "FAIL"
            FAIL=$((FAIL + 1))
            echo "    --- output ---"
            sed 's/^/    /' /tmp/e2e-output.txt | tail -20
            echo "    --- end ---"
        fi
    fi
done

echo ""
echo "============================================"
echo "Results: $PASS passed, $FAIL failed, $SKIP skipped"
echo "============================================"

[ $FAIL -eq 0 ] || exit 1
