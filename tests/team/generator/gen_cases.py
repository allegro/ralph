"""SQE Module 2 - test data generator.

Reads the OpenAPI spec and derives, for every request-body property:
  * Equivalence Partitioning (EP): one valid class + invalid classes
    (below range, above range, wrong type, null, missing when required)
  * 3-point Boundary Value Analysis (BVA) on every limit:
    just below, exactly at, just above (min and max; string lengths too)

Usage:
    python tests/team/generator/gen_cases.py                       # default spec
    python tests/team/generator/gen_cases.py --spec other.yaml --out out/v2.json

Each generated case changes ONE field of an otherwise valid payload, so a
test that fails points at exactly one input. The API tests load the JSON.
"""

import argparse
import json
from collections import Counter
from pathlib import Path

import yaml

HERE = Path(__file__).resolve().parent
DEFAULT_SPEC = HERE.parent / "openapi" / "ralph-licences.yaml"
DEFAULT_OUT = HERE / "out" / "cases.json"

# request bodies under test -> endpoint they are POSTed to
SCHEMAS = {
    "LicenceInput": "/api/licences/",
    "AssignmentInput": "/api/base-objects-licences/",
    "LicenceUserInput": "/api/licence-users/",
}
# integer properties that are references to other records (ids): EP only,
# because "id + 1" is not a meaningful boundary.
REFERENCE_FIELDS = {"region", "licence_type", "software", "licence", "base_object", "user"}


def resolve(spec, node):
    """Follow $ref and merge allOf into one schema dict."""
    if "$ref" in node:
        path = node["$ref"].lstrip("#/").split("/")
        target = spec
        for part in path:
            target = target[part]
        return resolve(spec, target)
    if "allOf" in node:
        merged = {"type": "object", "properties": {}, "required": []}
        for part in node["allOf"]:
            p = resolve(spec, part)
            merged["properties"].update(p.get("properties", {}))
            merged["required"] += p.get("required", [])
        return merged
    return node


def case(schema, field, technique, cls, value, valid, why):
    return {
        "schema": schema,
        "endpoint": SCHEMAS[schema],
        "field": field,
        "technique": technique,
        "class": cls,
        "value": value,
        "expect_valid": valid,
        "why": why,
    }


def integer_cases(schema, field, prop, required):
    out = []
    lo, hi = prop.get("minimum"), prop.get("maximum")
    if field in REFERENCE_FIELDS:
        out.append(case(schema, field, "EP", "existing id", "@existing", True, "valid reference"))
        out.append(case(schema, field, "EP", "unknown id", 999999, False, "no such record"))
        out.append(case(schema, field, "EP", "zero id", 0, False, "ids start at 1"))
    else:
        mid = lo + 1 if lo is not None else 1
        out.append(case(schema, field, "EP", "valid in range", mid, True, "inside [min, max]"))
        if lo is not None:
            out.append(case(schema, field, "EP", "below range", lo - 10, False, f"< min {lo}"))
            for v, ok, where in [
                (lo - 1, False, "just below"),
                (lo, True, "at"),
                (lo + 1, True, "just above"),
            ]:
                out.append(case(schema, field, "BVA", f"min {where}", v, ok, f"min = {lo}"))
        if hi is not None:
            out.append(case(schema, field, "EP", "above range", hi + 10, False, f"> max {hi}"))
            for v, ok, where in [
                (hi - 1, True, "just below"),
                (hi, True, "at"),
                (hi + 1, False, "just above"),
            ]:
                out.append(case(schema, field, "BVA", f"max {where}", v, ok, f"max = {hi}"))
    out.append(case(schema, field, "EP", "wrong type", "abc", False, "not an integer"))
    out.append(case(schema, field, "EP", "null", None, False, "null not allowed"))
    if required:
        out.append(case(schema, field, "EP", "missing", "@missing", False, "required field"))
    return out


def string_cases(schema, field, prop, required):
    out = []
    fmt = prop.get("format")
    if fmt == "date":
        out.append(case(schema, field, "EP", "valid date", "2026-01-15", True, "ISO date"))
        out.append(case(schema, field, "EP", "impossible date", "2026-13-40", False, "month 13"))
        out.append(case(schema, field, "EP", "wrong type", 12345, False, "not a date string"))
        return out
    lo, hi = prop.get("minLength", 0), prop.get("maxLength")
    out.append(
        case(
            schema, field, "EP", "valid length", "@len:" + str(min(10, hi or 10)), True, "typical"
        )
    )
    if lo > 0:
        for n, ok, where in [
            (lo - 1, False, "just below"),
            (lo, True, "at"),
            (lo + 1, True, "just above"),
        ]:
            out.append(
                case(
                    schema,
                    field,
                    "BVA",
                    f"minLength {where}",
                    "@len:" + str(n),
                    ok,
                    f"minLength = {lo}",
                )
            )
    if hi is not None:
        out.append(
            case(
                schema, field, "EP", "too long", "@len:" + str(hi + 50), False, f"> maxLength {hi}"
            )
        )
        for n, ok, where in [
            (hi - 1, True, "just below"),
            (hi, True, "at"),
            (hi + 1, False, "just above"),
        ]:
            out.append(
                case(
                    schema,
                    field,
                    "BVA",
                    f"maxLength {where}",
                    "@len:" + str(n),
                    ok,
                    f"maxLength = {hi}",
                )
            )
    if required:
        out.append(case(schema, field, "EP", "missing", "@missing", False, "required field"))
    return out


def generate(spec_path):
    spec = yaml.safe_load(Path(spec_path).read_text())
    cases = []
    for name in SCHEMAS:
        schema = resolve(spec, spec["components"]["schemas"][name])
        required = set(schema.get("required", []))
        for field, raw in schema["properties"].items():
            prop = resolve(spec, raw)
            if prop.get("type") == "integer":
                cases += integer_cases(name, field, prop, field in required)
            elif prop.get("type") == "string":
                cases += string_cases(name, field, prop, field in required)
    for i, c in enumerate(cases, 1):
        c["id"] = f"{c['schema']}.{c['field']}.{c['technique']}.{i:03d}"
    return cases


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--spec", default=str(DEFAULT_SPEC))
    ap.add_argument("--out", default=str(DEFAULT_OUT))
    a = ap.parse_args()
    cases = generate(a.spec)
    Path(a.out).parent.mkdir(parents=True, exist_ok=True)
    Path(a.out).write_text(json.dumps(cases, indent=2))
    by = Counter((c["schema"], c["technique"]) for c in cases)
    print(f"{len(cases)} cases -> {a.out}")
    for (s, t), n in sorted(by.items()):
        print(f"  {s:18} {t:4} {n}")


if __name__ == "__main__":
    main()
