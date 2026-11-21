#!/usr/bin/env bash
# Runs a SonarQube Community analysis against the service container started by
# the workflow and FAILS if the quality gate is not OK. No escape hatches.
set -euo pipefail
SONAR_URL="${SONAR_URL:-http://localhost:9000}"
NEW_PASS="${SONAR_ADMIN_PASSWORD:-SqeCi-Passw0rd!}"

echo "Waiting for SonarQube..."
for i in $(seq 1 90); do
  status=$(curl -s "$SONAR_URL/api/system/status" | python3 -c 'import sys,json;print(json.load(sys.stdin).get("status",""))' 2>/dev/null || true)
  [ "$status" = "UP" ] && break; sleep 5
done
[ "$status" = "UP" ] || { echo "SonarQube did not start"; exit 1; }

# Fresh container: change default admin password, then create a token.
curl -sf -u admin:admin -X POST "$SONAR_URL/api/users/change_password" \
  -d "login=admin&previousPassword=admin&password=$NEW_PASS" >/dev/null
TOKEN=$(curl -sf -u "admin:$NEW_PASS" -X POST "$SONAR_URL/api/user_tokens/generate" \
  -d "name=ci-$(date +%s)" | python3 -c 'import sys,json;print(json.load(sys.stdin)["token"])')

# Team quality gate on OVERALL code (a fresh CI container has no previous
# analysis, so "new code" conditions would never be evaluated).
# Set the thresholds from your first local SonarQube run (report section 4.4):
#   ratings 1=A .. 5=E ; fail if WORSE than the baseline rating.
curl -sf -u "admin:$NEW_PASS" -X POST "$SONAR_URL/api/qualitygates/create" -d "name=SQE-Gate" >/dev/null
for cond in "coverage:LT:${SONAR_MIN_COVERAGE:-95}" \
            "reliability_rating:GT:${SONAR_MAX_RELIABILITY_RATING:-3}" \
            "security_rating:GT:${SONAR_MAX_SECURITY_RATING:-3}" \
            "duplicated_lines_density:GT:${SONAR_MAX_DUPLICATION:-5}"; do
  IFS=: read -r metric op err <<< "$cond"
  curl -sf -u "admin:$NEW_PASS" -X POST "$SONAR_URL/api/qualitygates/create_condition" \
    -d "gateName=SQE-Gate&metric=$metric&op=$op&error=$err" >/dev/null
done
curl -sf -u "admin:$NEW_PASS" -X POST "$SONAR_URL/api/projects/create" \
  -d "project=sqe-ralph&name=SQE Ralph" >/dev/null
curl -sf -u "admin:$NEW_PASS" -X POST "$SONAR_URL/api/qualitygates/select" \
  -d "gateName=SQE-Gate&projectKey=sqe-ralph" >/dev/null

set +e
docker run --rm --network host -e SONAR_HOST_URL="$SONAR_URL" -e SONAR_TOKEN="$TOKEN" \
  -v "$PWD:/usr/src" sonarsource/sonar-scanner-cli:latest -Dsonar.qualitygate.wait=true \
  -Dsonar.qualitygate.timeout=600
scan_rc=$?
set -e
python3 tests/team/tools/sonar_report.py "$SONAR_URL" "$NEW_PASS"
exit $scan_rc
