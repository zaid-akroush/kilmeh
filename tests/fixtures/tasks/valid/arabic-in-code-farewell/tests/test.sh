#!/bin/bash
# (1) write 0 first on a root-owned log dir, (2) let the worker (uid 65534) read /app, (3) lock
# /tests, (4) verify with `-S` so a sitecustomize planted at agent time never runs as root,
# (5) write 1 or 0 in both branches, so a crash or a planted reward never leaves a stale 1.
mkdir -p /logs/verifier
chown 0:0 /logs/verifier
chmod 755 /logs/verifier
rm -f /logs/verifier/reward.txt
echo 0 > /logs/verifier/reward.txt
(cd /app && sha256sum README.md تحية.py && ls -b) > /logs/verifier/hashes.txt
(cd /tests/golden && sha256sum README.md orig.py) >> /logs/verifier/hashes.txt
chmod -R a+rX /app
if ! chown -R 0:0 /tests || ! chmod -R go-rwx /tests; then
  echo "test.sh: cannot lock /tests (grader must run as root, uid is $(id -u)); scoring 0" >&2
  exit 1
fi
cd /
if python3 -S /tests/verify.py > /logs/verifier/verify.log 2>&1; then echo 1 > /logs/verifier/reward.txt; else echo 0 > /logs/verifier/reward.txt; fi
