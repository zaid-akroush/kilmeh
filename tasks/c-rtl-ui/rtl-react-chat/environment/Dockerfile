# Build stage: install the pinned npm packages from package-lock.json. --ignore-scripts keeps
# install scripts off; esbuild's per-platform binary is a plain optional package (@esbuild/linux-x64
# or linux-arm64), which npm picks for the stage's own platform. No network after this stage.
FROM node:22.23.5-bookworm-slim@sha256:e9f565d32859f0cbfb52125eafe8be39390f24dac302dc3cdf566e8ba3ab21ee AS deps
WORKDIR /deps
COPY fixture/package.json fixture/package-lock.json ./
RUN npm ci --ignore-scripts

FROM mcr.microsoft.com/playwright/python:v1.64.1-noble@sha256:330d401ae23c905896a0c26c66c36fc971b621519e7b11b435a8328d7bf6e031
# Python bindings for the image's Chromium: versions and sha256 from uv.lock (linux amd64 and arm64 wheels).
RUN printf '%s\n' \
  'playwright==1.64.1 --hash=sha256:577b8d88778c245cfbd145ae17cf53044f084b1b46c55c69081d4069d56057e2 --hash=sha256:a29fda44725e11b0b625c4bff6458a1f6dbee97b88c9788d12e18a8344458c2d' \
  'pyee==14.0.0 --hash=sha256:3ac2d3229a9677f7de2c33d7f52fe25b638a46b19c413fea2edc8c6d0a644e4d' \
  'greenlet==3.5.6 --hash=sha256:975736b002ed080d124cf81a79cb7e05cb26d6b3f5c7a7b651c0fcce70353aa1 --hash=sha256:e85880b538e59a59f55117b81f208a6660ad5ac328aad9305f812d9b8bc67a0f' \
  'typing-extensions==4.16.0 --hash=sha256:481caa481374e813c1b176ada14e97f1f67a4539ce9cfeb3f350d78d6370c2e8' \
  > /tmp/req.txt \
  && pip install --no-cache-dir --break-system-packages --require-hashes --no-deps -r /tmp/req.txt \
  && rm /tmp/req.txt
# The Playwright image has no node: copy node and npm from the pinned build stage.
COPY --from=deps /usr/local/bin/node /usr/local/bin/node
COPY --from=deps /usr/local/lib/node_modules/npm /usr/local/lib/node_modules/npm
RUN ln -s ../lib/node_modules/npm/bin/npm-cli.js /usr/local/bin/npm
WORKDIR /app
COPY fixture/ /app/
COPY --from=deps /deps/node_modules /app/node_modules
# The grading toolchain: a second copy of the same pinned packages outside the workspace, so
# replacing or editing /app/node_modules cannot change how the grader builds. DIGESTS records
# the sha256 of esbuild (shim and platform binary), react, react-dom and scheduler as installed;
# the grader's toolchain_intact check recomputes it with the same digest.py.
COPY --from=deps /deps/node_modules /opt/kilmeh-build/node_modules
RUN printf '%s\n' \
  'import hashlib, os, sys' \
  'root = sys.argv[1]' \
  'parts = ["node_modules/.bin", "node_modules/esbuild", "node_modules/@esbuild",' \
  '         "node_modules/react", "node_modules/react-dom", "node_modules/scheduler"]' \
  'lines = []' \
  'for part in parts:' \
  '    for d, dirs, files in os.walk(os.path.join(root, part)):' \
  '        links = [x for x in dirs if os.path.islink(os.path.join(d, x))]' \
  '        for n in files + links:' \
  '            p = os.path.join(d, n)' \
  '            rel = os.path.relpath(p, root)' \
  '            if os.path.islink(p):' \
  '                lines.append("link " + os.readlink(p) + " " + rel)' \
  '            else:' \
  '                lines.append(hashlib.sha256(open(p, "rb").read()).hexdigest() + " " + rel)' \
  'print("\n".join(sorted(lines)))' \
  > /opt/kilmeh-build/digest.py \
  && python3 /opt/kilmeh-build/digest.py /opt/kilmeh-build > /opt/kilmeh-build/DIGESTS \
  && chmod -R a-w /opt/kilmeh-build
# The page loads dist/app.js, so ship it built from the (buggy) source, as a real project would.
RUN npm run build
