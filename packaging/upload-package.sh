#!/bin/bash

set -e

DIR=$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )
SRC_DIR="$DIR/.."

cd $SRC_DIR

if [ ! -z "$BINTRAY_APIKEY" ]; then
	DEB_NAME=$(ls $SRC_DIR/../*.deb | sort -Vr  | head -1)
	echo "Uploading $DEB_NAME"
	GENERIC_DEB_NAME=`basename $DEB_NAME`
	curl -T $DEB_NAME -uvi4m:$BINTRAY_APIKEY "https://api.bintray.com/content/vi4m/ralph/ralph/3-snapshot/dists/wheezy/main/binary-amd64/$GENERIC_DEB_NAME;deb_distribution=wheezy;deb_component=main;deb_architecture=amd64?publish=1"
else
	echo "Error. BINTRAY_APIKEY is missing"
	exit 1
fi
