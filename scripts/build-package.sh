#!/bin/bash

set -eux

# ignore warnings about python librariers deps
export DEB_DH_SHLIBDEPS_ARGS_ALL="--dpkg-shlibdeps-params=--ignore-missing-info"

SCRIPT_DIR=$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )
SRC_DIR="${SCRIPT_DIR}/.."
VERSION=$("${SRC_DIR}/get_version.sh")

cd "${SRC_DIR}"

if [[ "${VERSION}" == *"SNAPSHOT"* ]]; then
    VERSION_PARAMS="--spawn-editor=release -S"
else
    VERSION_PARAMS="--spawn-editor=snapshot --release"
fi

echo ${VERSION}
gbp dch --ignore-branch --new-version "${VERSION}" ${VERSION_PARAMS}

dpkg-buildpackage -us -uc

