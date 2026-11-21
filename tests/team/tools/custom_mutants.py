"""Custom, business-rule mutation operators (in addition to mutmut's built-ins).

mutmut's operators are generic (swap < for <=, change strings, ...). These
four operators encode how a developer is most likely to break OUR rules:

  OP-SEAT   Seat-boundary shift   : move the seat limit by one (BR1)
  OP-COND   Condition drop/negate : remove or negate one condition of the
                                    region decision (BR2)
  OP-ACCT   Seat-source omission  : forget one source of used seats or the
                                    "exclude myself" rule when counting (BR1)
  OP-IDEM   Idempotency removal   : get_or_create -> create (BR4)

Each mutant is applied to a pristine copy of the file, the team suite runs,
and the file is restored. Exit code 1 if any killable mutant survives.

Usage (repo root, env sourced):  python tests/team/tools/custom_mutants.py
"""
import json
import subprocess
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[3]
LIC = "src/ralph/licences/models.py"
BO = "src/ralph/back_office/models.py"

MUTANTS = [
    # id, operator, file, original, mutated, rule
    ("C01", "OP-SEAT", LIC, "if self.quantity > available:", "if self.quantity >= available:", "BR1"),
    ("C02", "OP-SEAT", LIC, "self.quantity < 1:", "self.quantity < 0:", "BR1"),
    ("C03", "OP-SEAT", LIC, "if licence.free > 0", "if licence.free >= 0", "BR1"),
    ("C04", "OP-SEAT", LIC, "return self.number_bought - self.used",
     "return self.number_bought - self.used + 1", "BR1"),
    ("C05", "OP-COND", LIC,
     "if bo_asset and self.licence and self.licence.region_id != bo_asset.region_id:",
     "if bo_asset and self.licence:", "BR2"),
    ("C06", "OP-COND", LIC,
     "if bo_asset and self.licence and self.licence.region_id != bo_asset.region_id:",
     "if self.licence and self.licence.region_id != bo_asset.region_id:", "BR2"),
    ("C07", "OP-COND", LIC, "self.licence.region_id != bo_asset.region_id",
     "self.licence.region_id == bo_asset.region_id", "BR2"),
    ("C08", "OP-ACCT", LIC, "others = others.exclude(pk=self.pk)", "others = others", "BR1"),
    ("C09", "OP-ACCT", LIC, "return sum(map(get_sum, [base_objects_qs, users_qs]))",
     "return sum(map(get_sum, [base_objects_qs]))", "BR1"),
    ("C10", "OP-ACCT", LIC, "return (self.user_count or 0) + (self.baseobject_count or 0)",
     "return self.baseobject_count or 0", "BR1"),
    ("C11", "OP-IDEM", BO, "BaseObjectLicence.objects.get_or_create(",
     "BaseObjectLicence.objects.create(", "BR4"),
]

TEST_CMD = [str(REPO / ".venv/bin/pytest"), "-x", "-q", "-W", "ignore", "-p", "no:cacheprovider"]


def run_suite():
    return subprocess.run(TEST_CMD, cwd=REPO / "tests/team",
                          stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL).returncode


def main():
    if run_suite() != 0:
        print("Suite is not green on unmutated code; aborting.")
        return 2
    results = []
    for mid, op, rel, orig, mut, rule in MUTANTS:
        path = REPO / rel
        src = path.read_text()
        if src.count(orig) != 1:
            results.append({"id": mid, "operator": op, "rule": rule, "status": "NOT_APPLICABLE"})
            continue
        try:
            path.write_text(src.replace(orig, mut))
            status = "KILLED" if run_suite() != 0 else "SURVIVED"
        finally:
            path.write_text(src)
        results.append({"id": mid, "operator": op, "rule": rule, "file": rel,
                        "from": orig, "to": mut, "status": status})
        print(f"{mid} {op:8} {rule}  {status}")
    (REPO / "tests/team/reports").mkdir(exist_ok=True)
    (REPO / "tests/team/reports/custom_mutants.json").write_text(json.dumps(results, indent=2))
    killed = sum(r["status"] == "KILLED" for r in results)
    applicable = sum(r["status"] != "NOT_APPLICABLE" for r in results)
    print(f"\nCustom operators: {killed}/{applicable} killed")
    return 0 if killed == applicable else 1


if __name__ == "__main__":
    sys.exit(main())
