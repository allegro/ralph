#!/bin/bash

set -eu


# NOTE(romcheg): In order to have the same command syntax
if [[ "$OSTYPE" == "darwin"* ]]; then
    SED="gsed"
else
    SED="sed"
fi

ACTION=${1:-"show"}
MAIN_BRANCH=${MAIN_BRANCH:-"ng"}
CURRENT_BRANCH=$(git rev-parse --abbrev-ref HEAD)
LATEST_TAG=$(git describe --abbrev=0)
CURRENT_TAG=$(git describe)

die() {
    echo "$1"
    exit 2
}


generate_next_version() {
    current_dateversion=$(echo "${LATEST_TAG}" | cut -d '.' -f1)
    current_path_number=$(echo "${LATEST_TAG}" | cut -d '.' -f2)

    new_dateversion=$(date +"%Y%m%d")

    if [[ $current_dateversion ==  $new_dateversion ]]; then
        incremented_patch=$((current_path_number+1))
    else
        incremented_patch="1"
    fi

    echo "${new_dateversion}.${incremented_patch}"
}

show_current_version() {
    local changes_above_tag=$(echo $CURRENT_TAG | \
        $SED -r '/^.*-[0-9]+-[a-z0-9].*/p'      | \
        wc -l                                   | \
        xargs)
    local sanitized_branch_name=$(echo ${CURRENT_BRANCH} | $SED 's/[^a-zA-Z0-9]/-/g')
    
    if [[ "$changes_above_tag" -eq 1 ]] && [[ "$CURRENT_BRANCH" == "$MAIN_BRANCH" ]]; then
        echo "${LATEST_TAG}"
    else
        local next_tag=$(generate_next_version)
        echo "${next_tag}-${sanitized_branch_name}-SNAPSHOT"
    fi
}


case "$ACTION" in
    show)
        show_current_version
        ;;
    generate)
        generate_next_version
        ;;
    *)
    echo $"Usage: $0 {show|generate}"
esac
