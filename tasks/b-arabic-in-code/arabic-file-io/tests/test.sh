#!/bin/bash
# Track B grader entry. (1) write 0 first on a root-owned log dir, (2) make /app readable and
# lock /tests (owned by root, no group/other access), (3) verify with -B -I -S (no bytecode, no
# site, so nothing planted at agent time runs as root), (4) write 1 or 0 in both branches, so a
# crash or a planted reward never leaves a stale 1. verify.py refuses to run if /tests is still
# readable by others, and kills leftover uid 65534 processes before and after reading /app.
export PYTHONDONTWRITEBYTECODE=1
mkdir -p /logs/verifier
chown 0:0 /logs/verifier
chmod 755 /logs/verifier
rm -f /logs/verifier/reward.txt
echo 0 > /logs/verifier/reward.txt
chmod -R a+rX /app
if ! chown -R 0:0 /tests || ! chmod -R go-rwx /tests; then
  echo "test.sh: cannot lock /tests (grader must run as root, uid is $(id -u)); scoring 0" >&2
  exit 1
fi
cd /
if python3 -B -I -S /tests/verify.py > /logs/verifier/checks.json 2> /logs/verifier/verify.log; then
  echo 1 > /logs/verifier/reward.txt
else
  echo 0 > /logs/verifier/reward.txt
fi
