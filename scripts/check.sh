#!/usr/bin/env bash

set -o errexit -o nounset -o pipefail

python3 -m unittest discover -s tests -p 'test_*.py'
python3 -m compileall -q pilot_v1
git diff --check

echo 'PILOT_V1_CHECK=PASS'
