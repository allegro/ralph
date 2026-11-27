# Source this before running team tests:  source tests/team/env.sh
export DJANGO_SETTINGS_MODULE=ralph.settings.test
export TEST_DB_ENGINE=psql
export DATABASE_ENGINE=django.db.backends.postgresql
export DATABASE_HOST=${DATABASE_HOST:-127.0.0.1}
export DATABASE_PORT=${DATABASE_PORT:-5432}
export DATABASE_USER=${DATABASE_USER:-ralph_ng}
export DATABASE_PASSWORD=${DATABASE_PASSWORD:-ralph_ng}
export DATABASE_NAME=${DATABASE_NAME:-ralph_ng}
export DATABASE_OPTIONS='{}'          # Ralph defaults are MySQL-only (sql_mode)
