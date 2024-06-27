#!/bin/bash

set -exvo pipefail -o nounset

IMAGE_TEST=managedtenants-cli

docker build -t ${IMAGE_TEST} -f Dockerfile.test .

docker_run_args=(
    --rm
    -v "/run/user/$(id -u)/docker.sock:/var/run/docker.sock"
    --net "host"
)

docker run "${docker_run_args[@]}" "${IMAGE_TEST}" check test
