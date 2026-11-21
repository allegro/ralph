"""Print why the SonarQube quality gate passed/failed, plus baseline measures."""

import base64
import json
import sys
import urllib.request

url, password = sys.argv[1], sys.argv[2]
auth = "Basic " + base64.b64encode(f"admin:{password}".encode()).decode()


def get(path):
    req = urllib.request.Request(url + path, headers={"Authorization": auth})
    return json.load(urllib.request.urlopen(req))


st = get("/api/qualitygates/project_status?projectKey=sqe-ralph")["projectStatus"]
print("================ SQE-Gate result ================")
print("Gate:", st["status"])
for c in st.get("conditions", []):
    print(
        f"  {c['status']:5} {c['metricKey']:28} actual={c.get('actualValue')}"
        f"  fails if {c['comparator']} {c.get('errorThreshold')}"
    )
keys = (
    "reliability_rating,security_rating,sqale_rating,coverage,duplicated_lines_density,"
    "bugs,vulnerabilities,code_smells,complexity,ncloc"
)
print("================ Project measures ================")
for m in get(f"/api/measures/component?component=sqe-ralph&metricKeys={keys}")["component"][
    "measures"
]:
    print(f"  {m['metric']:28} {m.get('value')}")
print("(ratings: 1=A 2=B 3=C 4=D 5=E)")
