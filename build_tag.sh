#!/bin/bash

set -exvo pipefail -o nounset

IMAGE_TEST=managedtenants-cli

# Run build in sandbox and inject secrets from gh-build-tag integration
docker build -t ${IMAGE_TEST} -f Dockerfile.test .
docker run --rm \
    -e "TWINE_USERNAME=${TWINE_USERNAME}" \
    -e "TWINE_PASSWORD=${TWINE_PASSWORD}" \
    -e "GITHUB_TOKEN=${GITHUB_TOKEN}" \
    ${IMAGE_TEST} release
