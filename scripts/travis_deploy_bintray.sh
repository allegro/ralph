#!/bin/bash

# designed to be run in travis after successfull build of not-PR
# required env variabled set in travis:
# BINTRAY_USER
# BINTRAY_APIKEY
# BINTRAY_REPO_NAME
# BINTRAY_PACKAGE_NAME

set -e

DIR=$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )
SRC_DIR="$DIR/.."

cd $SRC_DIR

DEB_NAME=$(ls $SRC_DIR/../*.deb | sort -Vr | head -1)
GENERIC_DEB_NAME=`basename $DEB_NAME`
echo "Uploading $GENERIC_DEB_NAME"
curl -T $DEB_NAME -u $BINTRAY_USER:$BINTRAY_APIKEY "https://api.bintray.com/content/$BINTRAY_USER/$BINTRAY_REPO_NAME/$BINTRAY_PACKAGE_NAME/$NEW_TAG/dists/wheezy/main/binary-amd64/$GENERIC_DEB_NAME;deb_distribution=wheezy;deb_component=main;deb_architecture=amd64?publish=1"
