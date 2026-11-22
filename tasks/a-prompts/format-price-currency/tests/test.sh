#!/bin/bash
mkdir -p /logs/verifier
if python3 /tests/verify.py > /logs/verifier/verify.log 2>&1; then echo 1 > /logs/verifier/reward.txt; else echo 0 > /logs/verifier/reward.txt; fi
