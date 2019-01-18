#! /bin/bash
set -eu


COMMAND="$1"
VALID_COMMANDS=(init upgrade)

isValidCommand () {
  VALID_COMMANDS=(init upgrade)
  match="$1"
  for i in ${VALID_COMMANDS[@]}; do [[ "$i" == "$match" ]] && return 0 ; done
  return 1
}

if ! isValidCommand $i ; then exit 1 ; fi
    echo "Usage: ${0} {init|upgrade}"
    exit 1
fi

"${RALPH_LOCAL_DIR}/wait-for-it.sh" "${DATABASE_HOST}:${DATABASE_PORT}" --timeout=30 --strict -- echo "Database is up"

ralph migrate --noinput
ralph sitetree_resync_apps

if [[ "$COMMAND" == "init" ]]; then
    python3 "${RALPH_LOCAL_DIR}/createsuperuser.py"
fi

