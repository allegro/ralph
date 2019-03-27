#!/bin/bash
set -e

ARG=${1:-start}

DB_ENV_VARIABLES=(
    DATABASE_NAME
    DATABASE_USER
    DATABASE_PASSWORD
    DATABASE_HOST
    DATABASE_PORT
    DATABASE_ENGINE
)
DB_CONF_PATH="${RALPH_CONF_DIR}/conf.d/database.conf"

REDIS_ENV_VARIABLES=(
    REDIS_HOST
    REDIS_PORT
    REDIS_DB
    REDIS_PASSWORD
)
REDIS_CONF_PATH="${RALPH_CONF_DIR}/conf.d/redis.conf"

function push_env_vars_to_config() {
    local conf_path=$1
    shift
    local env_variables=("$@")
    for env_var in "${env_variables[@]}"
    do
        if [[ ! -z "${!env_var}" ]]; then
            sed -ri "s/(${env_var} ?= ?).*/\1${!env_var}/" ${conf_path}
        fi
    done
}

push_env_vars_to_config "$DB_CONF_PATH" "${DB_ENV_VARIABLES[@]}"
push_env_vars_to_config "$REDIS_CONF_PATH" "${REDIS_ENV_VARIABLES[@]}"

set -a
export DJANGO_SETTINGS_MODULE="ralph.settings"
source ${RALPH_CONF_DIR}/ralph.conf
for f in ${RALPH_CONF_DIR}/conf.d/*.conf; do source $f; done

case "$ARG" in
    start)
        "${RALPH_LOCAL_DIR}/start-ralph.sh"
        ;;
    init)
        "${RALPH_LOCAL_DIR}/init-ralph.sh" init
        ;;
    upgrade)
        "${RALPH_LOCAL_DIR}/init-ralph.sh" upgrade
        ;;
    *)
        echo "Usage: ${0} {start|init|upgrade}"
        exit 1
esac
