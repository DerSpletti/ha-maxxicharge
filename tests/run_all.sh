#!/usr/bin/env bash
# Führt alle Tests aus (ohne Home Assistant). Die Broker-Tests brauchen paho-mqtt:
#   python3 -m venv .venv && .venv/bin/pip install paho-mqtt && PYTHON=.venv/bin/python tests/run_all.sh
set -euo pipefail
cd "$(dirname "$0")/.."
PY="${PYTHON:-python3}"
fail=0
for t in test_calc test_discovery test_broker test_broker_callbacks test_e2e; do
  echo "== $t"
  if ! timeout 90 "$PY" -I "tests/$t.py" 2>/dev/null | grep -E "^(OK|FAIL)"; then fail=1; fi
done
exit $fail
