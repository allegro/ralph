#!/bin/bash

# designed to be run in travis after successfull build of not-PR
# required env variabled set in travis:
# DOCKER_IMAGE
# DOCKER_EMAIL
# DOCKER_USERNAME
# DOCKER_PASSWORD

set -e

DIR=$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )
SRC_DIR="$DIR/.."

# run this only for main build
echo "deploying docker image"
docker login -e="$DOCKER_EMAIL" -u="$DOCKER_USERNAME" -p="$DOCKER_PASSWORD"
docker build -t $DOCKER_IMAGE:$NEW_TAG .
docker tag $DOCKER_IMAGE:$NEW_TAG $DOCKER_IMAGE:snapshot_latest
echo "pushing docker images: $DOCKER_IMAGE:$NEW_TAG and $DOCKER_IMAGE:snapshot_latest"
docker push $DOCKER_IMAGE:$NEW_TAG
docker push $DOCKER_IMAGE:snapshot_latest
