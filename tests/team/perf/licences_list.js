// Area 3b - performance test (k6) for GET /api/licences/?limit=20
//
// Why this operation: the licence list computes used/free seats with
// sub-queries for every row, so it is the read most likely to slow down as
// licences and assignments grow. Clerks and managers open it constantly.
//
// Targets, set BEFORE running (justification in the report):
//   p95 response time <= 500 ms   (an interactive list should feel instant)
//   unexpected failures < 1 %     (fewer than 1 in 100 requests may fail)
//
// Run (same build, machine and freshly reset/seeded DB for every run):
//   k6 run -e VUS=1 tests/team/perf/licences_list.js
//   k6 run -e VUS=5 tests/team/perf/licences_list.js
// Each configuration twice. Optional: -e BASE_URL=http://127.0.0.1:8000
import http from 'k6/http';
import { check, sleep } from 'k6';

const BASE = __ENV.BASE_URL || 'http://127.0.0.1:8000';
const VUS = Number(__ENV.VUS || 1);
const RUN = __ENV.RUN || '1';

export const options = {
  scenarios: {
    licences: {
      executor: 'ramping-vus',
      startVUs: 0,
      stages: [
        { duration: '10s', target: VUS }, // ramp-up (not counted in the 60 s)
        { duration: '60s', target: VUS }, // steady load: the measured window
        { duration: '5s', target: 0 },
      ],
      gracefulRampDown: '5s',
    },
  },
  thresholds: {
    http_req_duration: ['p(95)<=500'],
    http_req_failed: ['rate<0.01'],
  },
  summaryTrendStats: ['avg', 'min', 'med', 'p(90)', 'p(95)', 'max'],
};

export function setup() {
  const res = http.post(`${BASE}/api-token-auth/`, {
    username: 'sqe_manager',
    password: 'Sqe-Manager-1',
  });
  check(res, { 'login 200': (r) => r.status === 200 });
  return { token: res.json('token') };
}

export default function (data) {
  const res = http.get(`${BASE}/api/licences/?limit=20`, {
    headers: { Authorization: `Token ${data.token}` },
    tags: { name: 'GET /api/licences/' },
  });
  check(res, {
    'status 200': (r) => r.status === 200,
    'has results': (r) => Array.isArray(r.json('results')),
  });
  sleep(1); // think time: one request per user per second
}

export function handleSummary(data) {
  const m = data.metrics;
  const row = {
    vus: VUS,
    run: RUN,
    p95_ms: m.http_req_duration.values['p(95)'],
    avg_ms: m.http_req_duration.values.avg,
    rps: m.http_reqs.values.rate,
    failed_pct: 100 * m.http_req_failed.values.rate,
    requests: m.http_reqs.values.count,
  };
  return {
    stdout: `\nRESULT vus=${row.vus} run=${row.run} p95=${row.p95_ms.toFixed(1)}ms ` +
      `rps=${row.rps.toFixed(2)} failed=${row.failed_pct.toFixed(2)}% requests=${row.requests}\n`,
    [`tests/team/reports/k6_vus${VUS}_run${RUN}.json`]: JSON.stringify(data, null, 2),
  };
}
