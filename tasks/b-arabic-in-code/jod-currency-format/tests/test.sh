#!/bin/bash
# Track B grader entry. (1) write 0 first, (2) let the worker (uid 65534) read /app, (3) lock
# /tests so the worker cannot read the grader, (4) verify, (5) write 1 or 0 in both branches, so
# a crash or a planted reward never leaves a stale 1. verify.mjs refuses to run if /tests is
# still readable by others.
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
if node /tests/verify.mjs > /logs/verifier/checks.json 2> /logs/verifier/verify.log; then
  echo 1 > /logs/verifier/reward.txt
else
  echo 0 > /logs/verifier/reward.txt
fi
