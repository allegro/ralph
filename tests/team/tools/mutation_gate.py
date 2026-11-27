"""Mutation-score gate for CI.

Reads mutmut's results (``mutmut junitxml > mutmut.xml``) and computes:
  * module score   = killed / (killed + survived)   over the whole module
  * rule score     = same, restricted to the business-rule functions
                     (line ranges from tools/function_coverage.py SCOPE)
Fails (exit 1) when the rule score is below --min-rule-score.

Mutants mutmut marks as "skipped"/"suspicious"/"timeout" are reported but
counted as killed for timeouts (the test run did not pass), as mutmut does.
"""

import argparse
import ast
import sys
import xml.etree.ElementTree as ET
from pathlib import Path

REPO = Path(__file__).resolve().parents[3]
RULE_FUNCS = {
    "src/ralph/licences/models.py": [
        "Licence.used",
        "Licence.free",
        "Licence.get_autocomplete_queryset",
        "BaseObjectLicence.clean",
        "BaseObjectLicence._validate_seat_limit",
    ],
}


def ranges(rel, names):
    tree = ast.parse((REPO / rel).read_text())
    found = {}

    def visit(node, prefix=""):
        for ch in ast.iter_child_nodes(node):
            if isinstance(ch, (ast.FunctionDef, ast.ClassDef)):
                name = prefix + ch.name
                if isinstance(ch, ast.FunctionDef):
                    found[name] = (ch.lineno, ch.end_lineno)
                visit(ch, name + ".")

    visit(tree)
    return [found[n] for n in names if n in found]


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("junit")
    ap.add_argument("--min-rule-score", type=float, default=0)
    a = ap.parse_args()
    root = ET.parse(a.junit).getroot()
    rows = []
    for tc in root.iter("testcase"):
        file_, line = tc.get("file"), int(tc.get("line"))
        survived = tc.find("failure") is not None
        skipped = tc.find("skipped") is not None
        rows.append((file_, line, survived, skipped))
    rule_ranges = {f: ranges(f, n) for f, n in RULE_FUNCS.items()}

    def score(sel):
        tested = [r for r in sel if not r[3]]
        killed = sum(1 for r in tested if not r[2])
        return killed, len(tested)

    def in_rule(r):
        return any(lo <= r[1] <= hi for lo, hi in rule_ranges.get(r[0], []))

    mk, mt = score(rows)
    rk, rt = score([r for r in rows if in_rule(r)])
    print(f"Module mutation score : {mk}/{mt} = {100 * mk / max(mt, 1):.1f}%")
    print(f"Rule-function score   : {rk}/{rt} = {100 * rk / max(rt, 1):.1f}%")
    for r in rows:
        if r[2] and in_rule(r):
            print(f"  SURVIVED in rule code: {r[0]}:{r[1]}")
    if 100 * rk / max(rt, 1) < a.min_rule_score:
        print(f"FAIL: rule-function score below {a.min_rule_score}%")
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
