#!/bin/bash

set -e
DIR=$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )
# ignore warnings about python librariers deps
export DEB_DH_SHLIBDEPS_ARGS_ALL="--dpkg-shlibdeps-params=--ignore-missing-info"
SRC_DIR="$DIR/.."

function install_dh_virtualenv {
	# in ubuntu 14.04 provided by system - just for another systems
	# compile and install dh_virtualenv in travis sandbox - we need sudo here
	sudo apt-get update
	sudo apt-get install -y devscripts python-virtualenv git equivs
	git clone https://github.com/spotify/dh-virtualenv.git
	cd dh-virtualenv
	sudo mk-build-deps -ri
	dpkg-buildpackage -us -uc -b
	sudo dpkg -i ../dh-virtualenv_*.deb
}

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
