#!/bin/bash

set -exvo pipefail -o nounset

IMAGE_TEST=managedtenants-cli

podman build -t ${IMAGE_TEST} -f Dockerfile.test .

systemctl --user start podman.socket

podman_run_args=(
    --rm
    -e "CONTAINER_HOST=unix:///var/run/podman.sock"
    -e "CONTAINER_RUNTIME=podman"
    --security-opt label=disable
    -v "${XDG_RUNTIME_DIR}/podman/podman.sock:/var/run/podman.sock"
    --net "host"
)

podman run "${podman_run_args[@]}" "${IMAGE_TEST}" check test
