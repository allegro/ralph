#! /bin/bash

set -uex

SNAPSHOT=${SNAPSHOT:-"0"}
KEY_ID=${KEY_ID:-"E2D0F3764B54797F"}


move_scripts() {
    local files_to_move=" \
        docker-entrypoint.sh \
        createsuperuser.py \
        start-ralph.sh \
        wait-for-it.sh \
        init-ralph.sh \
    "

    for f in $files_to_move; do
        mv "${RALPH_IMAGE_TMP_DIR}/${f}" "${RALPH_LOCAL_DIR}/"
    done
}


install_release() {
    apt-key adv --keyserver "hkp://keyserver.ubuntu.com:80" --recv-keys "${KEY_ID}"
    mv "${RALPH_IMAGE_TMP_DIR}/ralph.list" /etc/apt/sources.list.d/ralph.list

    apt-get update
    apt-get -y install ralph-core="${RALPH_VERSION}"
}


install_snapshot() {
    local deb_file=$(ls -t ${RALPH_IMAGE_TMP_DIR}/*${RALPH_VERSION}*.deb | head -1)
    apt-get update
    apt-get -y install "${deb_file}"
}


cleanup() {
    rm -rf /var/lib/apt/lists/*
    rm -f "${RALPH_IMAGE_TMP_DIR}/ralph.list"
    rm -f "${RALPH_IMAGE_TMP_DIR}/*.deb"
    rm -- "$0"
}


if [[ "$SNAPSHOT" == "1" ]]; then
    install_snapshot
else
    install_release
fi

move_scripts
cleanup
