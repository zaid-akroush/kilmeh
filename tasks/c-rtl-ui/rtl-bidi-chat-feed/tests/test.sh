#!/bin/bash
mkdir -p /logs/verifier
echo 0 > /logs/verifier/reward.txt
cd /
if bash /tests/build.sh /app /tmp/kilmeh-build > /logs/verifier/build.log 2>&1 \
  && python3 -I /tests/verify.py /app /tmp/kilmeh-build > /logs/verifier/checks.json 2> /logs/verifier/verify.log
then echo 1 > /logs/verifier/reward.txt; fi
