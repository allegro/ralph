#! /bin/bash

set -eu

TAG=$(git describe | grep -E -o '^[0-9]{8}\.[0-9]+$' || true)

if [[ -z "$TAG" ]]; then
    >&2 echo "The HEAD is not tagged."
    exit 1
fi
