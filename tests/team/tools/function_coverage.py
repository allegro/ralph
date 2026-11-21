"""Per-function statement + branch coverage for the business-logic scope.

coverage.py reports per file. back_office/models.py and
lib/transitions/models.py are large shared files, and only some of their
functions belong to our two licence workflows. This script reads
coverage.json (``coverage json``) and reports coverage for exactly the
functions listed in SCOPE, so the 100% target can be checked (and gated in CI).

Usage:
    coverage json --rcfile=.coveragerc -o coverage.json
    python tools/function_coverage.py coverage.json [--fail-under 100]
"""

import ast
import json
import sys
from pathlib import Path

SRC = Path(__file__).resolve().parents[3] / "src" / "ralph"

# file -> functions (Class.method or function) in the business-logic scope
SCOPE = {
    "licences/models.py": "*",  # whole module
    "licences/api.py": ["BaseObjectLicenceSerializer.validate"],
    "back_office/models.py": [
        "_check_assets_owner",
        "_check_assets_user",
        "_check_user_assigned",
        "autocomplete_user",
        "BackOfficeAsset.assign_user",
        "BackOfficeAsset.assign_licence",
        "BackOfficeAsset.unassign_user",
        "BackOfficeAsset.unassign_licences",
    ],
    "lib/transitions/models.py": ["_check_instances_for_transition", "_prepare_action_data"],
}


def function_ranges(path):
    tree = ast.parse(path.read_text())
    out = {}

    def visit(node, prefix=""):
        for child in ast.iter_child_nodes(node):
            if isinstance(child, (ast.FunctionDef, ast.AsyncFunctionDef)):
                out[prefix + child.name] = (child.body[0].lineno, child.end_lineno)
                visit(child, prefix + child.name + ".")
            elif isinstance(child, ast.ClassDef):
                visit(child, prefix + child.name + ".")

    visit(tree)
    return out


def main(argv):
    data = json.loads(Path(argv[1]).read_text())
    fail_under = float(argv[argv.index("--fail-under") + 1]) if "--fail-under" in argv else None
    files = {k.split("src/ralph/")[-1]: v for k, v in data["files"].items()}
    tot_s = tot_ms = tot_b = tot_mb = 0
    print(f"{'function':62} {'stmts':>5} {'miss':>4} {'br':>4} {'brmiss':>6}  missing")
    for rel, funcs in SCOPE.items():
        f = files[rel]
        executed, missing = set(f["executed_lines"]), set(f["missing_lines"])
        missing_br = [tuple(b) for b in f.get("missing_branches", [])]
        all_br = [tuple(b) for b in f.get("executed_branches", [])] + missing_br
        ranges = function_ranges(SRC / rel)
        names = [None] if funcs == "*" else funcs
        for name in names:
            lo, hi = (1, 10**9) if name is None else ranges[name]
            s = {ln for ln in executed | missing if lo <= ln <= hi}
            ms = {ln for ln in missing if lo <= ln <= hi}
            b = [x for x in all_br if lo <= x[0] <= hi]
            mb = [x for x in missing_br if lo <= x[0] <= hi]
            tot_s, tot_ms, tot_b, tot_mb = (
                tot_s + len(s),
                tot_ms + len(ms),
                tot_b + len(b),
                tot_mb + len(mb),
            )
            label = f"{rel}::{name or '(whole module)'}"
            print(
                f"{label:62} {len(s):5} {len(ms):4} {len(b):4} {len(mb):6}  "
                f"{sorted(ms) or ''} {mb or ''}"
            )
    pct = 100.0 * ((tot_s - tot_ms) + (tot_b - tot_mb)) / max(1, tot_s + tot_b)
    print(
        f"\nSCOPE TOTAL: statements {tot_s - tot_ms}/{tot_s}, branches {tot_b - tot_mb}/{tot_b}, "
        f"combined {pct:.1f}%"
    )
    if fail_under is not None and pct < fail_under:
        print(f"FAIL: combined coverage {pct:.1f}% < {fail_under}%")
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv))
