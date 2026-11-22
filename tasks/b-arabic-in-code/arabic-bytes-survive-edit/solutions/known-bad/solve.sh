#!/bin/bash
# solve.py makes the edit. KILMEH_APP lets repo tests target a temp copy.
set -euo pipefail
python3 "$(dirname "$0")/solve.py"
