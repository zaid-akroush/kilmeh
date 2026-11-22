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
WORKDIR /app
COPY fixture/ /app/
