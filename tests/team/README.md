# SQE team tests (SE3002) – Ralph licence workflows

Our own tests live here. Upstream tests in `src/ralph/**/tests` earn no marks.

| Path | Owner | What |
|---|---|---|
| `unit/` | Roshail | White-box unit tests for BR1–BR4 (pytest + pytest-django) |
| `tools/function_coverage.py` | Roshail | Coverage of the business-logic scope + gate |
| `tools/mutation_gate.py`, `tools/custom_mutants.py` | Roshail | Mutation score gate, 4 custom operators |
| `tools/sonar_ci.sh`, `tools/make_sonar_coverage.py` | Roshail | SonarQube in CI, coverage.xml for Sonar |
| `docs/` | Roshail | CFG of `BaseObjectLicence.clean` |
| `seed/seed_sqe.py` | Both | Deterministic synthetic data |
| `api/`, `openapi/`, `generator/` | Mehak | (to add) API suite, spec, generator |
| `e2e/` | Mehak + Roshail | (to add) Playwright use cases, a11y, role checks |

## Run

```bash
source tests/team/env.sh            # DB settings (Postgres ralph_ng/ralph_ng)
cd tests/team
../../.venv/bin/pytest --create-db  # first time (builds test DB from migrations, ~1 min)
../../.venv/bin/pytest              # later runs reuse it (~5 s)

# coverage of the business-logic scope
../../.venv/bin/coverage run --rcfile=.coveragerc -m pytest
../../.venv/bin/coverage json --rcfile=.coveragerc -o coverage.json
../../.venv/bin/python tools/function_coverage.py coverage.json --fail-under 99
../../.venv/bin/python tools/make_sonar_coverage.py          # coverage.xml for SonarQube

# mutation (repo root)
cd ../.. && export PYTHONPATH=$PWD/src
.venv/bin/mutmut run --paths-to-mutate src/ralph/licences/models.py --tests-dir tests/team \
  --runner "bash -c 'cd tests/team && ../../.venv/bin/pytest -x -q -W ignore'"
.venv/bin/mutmut junitxml > tests/team/reports/mutmut.xml
.venv/bin/python tests/team/tools/mutation_gate.py tests/team/reports/mutmut.xml --min-rule-score 90
.venv/bin/python tests/team/tools/custom_mutants.py
```

Known defects pinned by strict xfail tests: SQE-D02 (Software.licences), SQE-D03
(transition bypasses region/seat rules). Defect SQE-D01 (seat limit) is fixed by
`0001-fix-sqe-d01-enforce-licence-seat-limit.patch` together with
`unit/test_br1_seat_limit_enforcement.py` (added in the fix PR).
