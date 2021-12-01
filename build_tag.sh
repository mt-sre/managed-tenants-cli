#!/bin/bash

set -exvo pipefail -o nounset

IMAGE_TEST=managedtenants-cli

docker build -t ${IMAGE_TEST} -f Dockerfile.test .

# sync secrets from app-interface
# - secrets: /resources/jenkins/global/secrets.yaml
# - for job `gh-build-tag`: /resources/jenkins/global/templates.yaml
docker_run_args=(
    --rm
    # pypi
    -e "TWINE_USERNAME=${TWINE_USERNAME}"
    -e "TWINE_PASSWORD=${TWINE_PASSWORD}"
    # goreleaser
    -e "GITHUB_TOKEN=${GITHUB_TOKEN}"
)
docker run "${docker_run_args[@]}" "${IMAGE_TEST}" release
