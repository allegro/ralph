#!/bin/bash

set -eux

VERSION=${VERSION:-""}
SCRIPT_DIR=$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )
cd "${SCRIPT_DIR}/.."

if [[ -z "${VERSION}" ]]; then
    VERSION=$("./get_version.sh")
fi


if [[ "${VERSION}" == *"SNAPSHOT"* ]]; then
    VERSION_PARAMS="--snapshot"
else
    VERSION_PARAMS="--release"
fi

echo ${VERSION}
gbp dch --ignore-branch --git-author --spawn-editor=release --new-version "${VERSION}" ${VERSION_PARAMS}
