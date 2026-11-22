#!/bin/bash
# Rebuild the Tailwind output from the agent's source. Usage: build.sh APP OUT
# verify.py serves OUT/app.css in place of /dist/app.css, so an edited dist/ is never graded.
# OUT/pristine.css is the build of the untouched fixture (tests/pristine), for ltr_layout_unchanged.
set -e
mkdir -p "$2"
(cd "$(dirname "$0")/pristine" && tailwindcss -i src/input.css -o "$2/pristine.css")
cd "$1" && tailwindcss -i src/input.css -o "$2/app.css"
