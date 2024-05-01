#!/bin/bash

set -eu

# first build the image if it doesn't exit.
BOLT12_PRISM_IMAGE_NAME="bolt12-prism-pyln-testing:v24.02.2"
if ! docker image inspect "$BOLT12_PRISM_IMAGE_NAME" &>/dev/null; then
    docker buildx build . -t "$BOLT12_PRISM_IMAGE_NAME" --load
fi

if ! docker ps -a | grep bolt12-tester >> /dev/null; then
    docker run --rm --name bolt12-tester -it bolt12-prism-pyln-testing:v24.02.2
fi