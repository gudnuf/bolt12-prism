#!/bin/bash

set -ex

cd /cln-plugins

python3 -m pytest .
