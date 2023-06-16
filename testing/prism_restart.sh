#!/bin/bash

set -u

echo "Stopping prism"
lightning-cli --lightning-dir=/tmp/l2-regtest plugin stop prism-plugin.py > /dev/null 2>&1

echo "Starting prism"
lightning-cli --lightning-dir=/tmp/l2-regtest plugin start ~/code/bolt12-prism/prism-plugin.py  > /dev/null

