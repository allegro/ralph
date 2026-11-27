"""EP + 3-point BVA on every request-body input, driven by the generator.

Cases come from tests/team/generator/out/cases.json (made from the OpenAPI
spec by gen_cases.py). Each case changes ONE field of an otherwise valid
request: valid cases must give 201, invalid ones 400.
"""

import json
import os
from pathlib import Path

import pytest
from conftest import unique

# SQE_CASES lets the regeneration demo point the suite at another generated file.
CASES_FILE = os.environ.get(
    "SQE_CASES", str(Path(__file__).resolve().parents[1] / "generator" / "out" / "cases.json")
)
CASES = json.loads(Path(CASES_FILE).read_text())

# Where Ralph is looser than our test basis -> documented defects.
# A strict xfail turns red as soon as the defect is fixed.
KNOWN_DEFECTS = {
    ("LicenceInput", "number_bought", "below range"): "SQE-D04: licence with <= 0 seats accepted",
    ("LicenceInput", "number_bought", "min just below"): "SQE-D04: licence with 0 seats accepted",
    (
        "LicenceUserInput",
        "quantity",
        "min just below",
    ): "SQE-D05: user assignment of 0 seats accepted",
}


def apply(body, case):
    v = case["value"]
    if v == "@missing":
        body.pop(case["field"], None)
    elif v == "@existing":
        pass
    elif isinstance(v, str) and v.startswith("@len:"):
        body[case["field"]] = unique("SQE", int(v[5:]))
    else:
        body[case["field"]] = v
    return body


def base_body(case, make):
    schema = case["schema"]
    r = make.refs
    if schema == "LicenceInput":
        return {
            "number_bought": 5,
            "region": r["region_pk"],
            "licence_type": r["licence_type"],
            "software": r["software"],
            "niw": unique(),
        }
    if schema == "AssignmentInput":
        # enough seats that only the field under test can cause a rejection
        lic = make.licence(seats=2147483647)
        return {"licence": lic["id"], "base_object": make.asset()["id"], "quantity": 1}
    if schema == "LicenceUserInput":
        lic = make.licence(seats=2147483647)
        return {"licence": lic["id"], "user": r["user_clerk"], "quantity": 1}
    raise AssertionError(schema)


def params():
    for c in CASES:
        reason = KNOWN_DEFECTS.get((c["schema"], c["field"], c["class"]))
        marks = [pytest.mark.xfail(strict=True, reason=reason)] if reason else []
        yield pytest.param(c, id=c["id"], marks=marks)


@pytest.mark.parametrize("case", list(params()))
def test_input_partition(case, make):
    body = apply(base_body(case, make), case)
    r = make.api.post(case["endpoint"], body)
    if r.status_code == 201:
        make.track(case["endpoint"], r.json()["id"])
    expected = 201 if case["expect_valid"] else 400
    assert r.status_code == expected, (
        f"{case['field']}={str(case['value'])[:40]!r} ({case['class']}): "
        f"expected {expected}, got {r.status_code} {r.text[:200]}"
    )
