#!/bin/bash
# Rebuild the Tailwind output from the agent's source. Usage: build.sh APP OUT
# verify.py serves OUT/app.css in place of /dist/app.css, so an edited dist/ is never graded.
set -e
mkdir -p "$2"
cd "$1" && tailwindcss -i src/input.css -o "$2/app.css"
