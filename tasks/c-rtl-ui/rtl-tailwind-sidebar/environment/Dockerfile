# Build stage: download the Tailwind v4.3.3 standalone CLI and verify it. Nothing from this stage
# but the binary reaches the final image. The apt packages only fetch the file; the sha256 below
# is what pins it.
FROM debian:bookworm-slim@sha256:734a72b3d6142a71993b4bc580ca01d8ca687f77a2c422d96a961d3376b179bc AS tw
ARG TARGETARCH
RUN apt-get update \
  && apt-get install -y --no-install-recommends ca-certificates curl \
  && rm -rf /var/lib/apt/lists/*
RUN case "$TARGETARCH" in \
    amd64) arch=x64; sum=dc61b3ac6b8c9ca874c0cc4c57b2409791a64c5540404ca5f5367360babc313a ;; \
    arm64) arch=arm64; sum=55fd0b241214eff3de1e8ee4f22796662f2d2e7a49bcfca7477cfd0bac398195 ;; \
    *) echo "unsupported arch: $TARGETARCH" >&2; exit 1 ;; \
  esac \
  && curl -fsSL -o /tailwindcss "https://github.com/tailwindlabs/tailwindcss/releases/download/v4.3.3/tailwindcss-linux-${arch}" \
  && echo "${sum}  /tailwindcss" | sha256sum -c - \
  && chmod 0755 /tailwindcss

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
COPY --from=tw /tailwindcss /usr/local/bin/tailwindcss
WORKDIR /app
COPY fixture/ /app/
