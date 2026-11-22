#!/bin/bash
# solve.js is the finished src/money.js. KILMEH_APP lets repo tests target a temp copy.
set -euo pipefail
cp "$(dirname "$0")/solve.js" "${KILMEH_APP:-/app}/src/money.js"
