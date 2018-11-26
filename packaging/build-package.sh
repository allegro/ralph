#!/bin/bash

set -eu
DIR=$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )
# ignore warnings about python librariers deps
export DEB_DH_SHLIBDEPS_ARGS_ALL="--dpkg-shlibdeps-params=--ignore-missing-info"
SRC_DIR="$DIR/.."
VERSION=$($SRC_DIR/get_version.sh)

function build_package {
	cd $SRC_DIR
	if [ ! -z "$TRAVIS" ]; then
		if [ -z "$NEW_TAG" ]; then
			RALPH_VERSION=`cat ${SRC_DIR}/VERSION`
			VERSION=snapshot-$RALPH_VERSION-$(date "+%Y%m%d")
		else
			VERSION=${NEW_TAG}
		fi
		dch --newversion="$VERSION" -- 'travis'
	else
		dch --team "ralph pre-release test build"
	fi
	dpkg-buildpackage -us -uc
}


build_package
