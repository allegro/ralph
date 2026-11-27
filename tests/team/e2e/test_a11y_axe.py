"""Accessibility scan (axe-core) of the UC-1 / UC-2 screens.

This is a measurement, not a pass/fail gate: it saves every axe violation per
screen to tests/team/reports/axe_<screen>_<AXE_TAG>.json and prints a summary.
Run once with AXE_TAG=before, fix a screen, run again with AXE_TAG=after.

Needs axe-core:  npm install --prefix tests/team/e2e axe-core
"""

import json
import os
from pathlib import Path

import pytest
from conftest import BASE_URL, login

HERE = Path(__file__).resolve().parent
AXE_JS = HERE / "node_modules" / "axe-core" / "axe.min.js"
REPORTS = HERE.parent / "reports"
TAG = os.environ.get("AXE_TAG", "before")

SCREENS = {
    "licence_add": lambda ids: "/licences/licence/add/",
    "licence_assignments": lambda ids: f"/licences/licence/{ids['lic_pk']}/assignments/",
    "asset_licence_tab": lambda ids: (
        f"/back_office/backofficeasset/{ids['asset_new']}/back_office_asset_licence/"
    ),
}


@pytest.mark.parametrize("screen", list(SCREENS))
def test_axe_scan(page, ids, screen):
    assert AXE_JS.exists(), "run: npm install --prefix tests/team/e2e axe-core"
    login(page, "manager")
    page.goto(BASE_URL + SCREENS[screen](ids))
    page.wait_for_load_state("networkidle")
    page.wait_for_timeout(1500)  # let the Polymer widgets render
    page.add_script_tag(path=str(AXE_JS))
    result = page.evaluate(
        """async () => await axe.run(
             {exclude: [['#djDebug']]},
             {resultTypes: ['violations']})"""
    )
    violations = result["violations"]
    REPORTS.mkdir(parents=True, exist_ok=True)
    out = REPORTS / f"axe_{screen}_{TAG}.json"
    out.write_text(json.dumps(violations, indent=2))

    print(f"\n=== {screen} ({TAG}): {len(violations)} rule(s) violated ===")
    for v in sorted(violations, key=lambda v: v["impact"] or ""):
        print(f"  [{v['impact']}] {v['id']}: {len(v['nodes'])} element(s) - {v['help']}")
