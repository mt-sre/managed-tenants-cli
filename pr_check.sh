#!/bin/bash

set -exvo pipefail -o nounset

IMAGE_TEST=managedtenants-cli

docker build -t ${IMAGE_TEST} -f Dockerfile.test .
docker run --rm ${IMAGE_TEST} check test
