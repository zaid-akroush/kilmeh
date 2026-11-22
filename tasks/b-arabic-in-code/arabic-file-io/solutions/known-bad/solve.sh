#!/bin/bash
# solve.py is the finished ingest.py. KILMEH_APP lets repo tests target a temp copy.
set -euo pipefail
cp "$(dirname "$0")/solve.py" "${KILMEH_APP:-/app}/ingest.py"
