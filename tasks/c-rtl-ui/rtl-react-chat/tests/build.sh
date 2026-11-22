#!/bin/bash
# React + esbuild: rebuild the bundle (and any CSS imported from JS) from src/ into OUT, as
# OUT/app.js and OUT/app.css. Only a copy of /app/src goes into a fresh temp directory, so no
# package.json, tsconfig.json or jsconfig.json from /app, and no /app/node_modules, can reach the
# build: esbuild and react, react-dom and scheduler come from the image's own copy under /opt
# (the aliases pin the imports there), the tsconfig is empty and the JSX runtime is fixed.
# The agent's dist/ is never used. Usage: build.sh APP OUT (OUT absolute)
set -euo pipefail
mkdir -p "$2"
work=$(mktemp -d)
trap 'rm -rf "$work"' EXIT
cp -rL "$1/src" "$work/src"
cd "$work"
T=/opt/kilmeh-build/node_modules
"$T/.bin/esbuild" src/main.jsx --bundle --tsconfig-raw='{}' \
  --jsx=automatic --jsx-import-source=react \
  --define:process.env.NODE_ENV='"production"' \
  --alias:react="$T/react" --alias:react-dom="$T/react-dom" --alias:scheduler="$T/scheduler" \
  --entry-names=app --outdir="$2"
