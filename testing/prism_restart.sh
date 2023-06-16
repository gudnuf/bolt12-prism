#!/bin/bash

set -x


echo "Stopping prism"
lightning-cli --lightning-dir=/tmp/l2-regtest plugin stop prism-plugin.py

echo "Starting prism"
lightning-cli --lightning-dir=/tmp/l2-regtest plugin start /home/daim/code/bolt12-prism/prism-plugin.py

