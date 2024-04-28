#!/bin/bash

set -ex

docker buildx build . -t bolt12-prism-pyln-testing:v24.02.2 --load
