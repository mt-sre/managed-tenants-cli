#!/bin/bash

# Collection of helper functions to be sourced by other scripts

# failIfRepoIsDirty - makes sure generators and formatters have been run
function failIfRepoIsDirty() {
    if [[ -n "$(git status --porcelain)" ]]; then
        git diff
        echo "Repo is dirty! Please run 'make fmt' and 'make generate'. Please also install pre-commit hooks with: 'pre-commit install'."
        exit 1
    fi
}
