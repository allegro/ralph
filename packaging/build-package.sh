#!/bin/bash

set -e
DIR=$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )

function install_dh_virtualenv {
	# in ubuntu 14.04 provided by system - just for another systems
	# compile and install dh_virtualenv in travis sandbox - we need sudo here
	sudo apt-get update
	sudo apt-get install devscripts python-virtualenv git equivs
	git clone https://github.com/spotify/dh-virtualenv.git
	cd dh-virtualenv
	sudo mk-build-deps -ri
	dpkg-buildpackage -us -uc -b
	sudo dpkg -i ../dh-virtualenv_*.deb
}

function build_package {
	RALPH_VERSION=`cat ${SRC_DIR}/VERSION`
	VERSION="${RALPH_VERSION}-${TRAVIS_BUILD_NUMBER}"
	cd $SRC_DIR
	dch --team "ralph pre-release test build"
	dpkg-buildpackage -us -uc
}


# ignore warnings about python librariers deps
export DEB_DH_SHLIBDEPS_ARGS_ALL="--dpkg-shlibdeps-params=--ignore-missing-info"

SRC_DIR="$DIR/.."

build_package

