"""Write tests/team/coverage.xml with paths relative to the repo root.

coverage.py records absolute paths of the machine that ran the tests. The
SonarQube scanner (often in Docker, mounted at /usr/src) cannot match those,
and coverage then shows as 0%. This rewrites <source> to the repo-relative
path so the same file works locally, in Docker and in GitHub Actions.

Usage (from tests/team, after `coverage run`):
    ../../.venv/bin/python tools/make_sonar_coverage.py
"""
import subprocess
import sys
import xml.etree.ElementTree as ET
from pathlib import Path

HERE = Path(__file__).resolve().parents[1]          # tests/team
REPO = HERE.parents[1]
out = HERE / "coverage.xml"
subprocess.run([sys.executable, "-m", "coverage", "xml", "--rcfile", str(HERE / ".coveragerc"),
                "-o", str(out), "-q"], check=True, cwd=HERE)
tree = ET.parse(out)
root = tree.getroot()


def rel(path_text):
    p = Path(path_text)
    return str(p.resolve().relative_to(REPO)) if p.is_absolute() and p.resolve().is_relative_to(REPO) else path_text


for cls in root.iter("class"):                     # absolute file paths live here
    cls.set("filename", rel(cls.get("filename")))
for src in root.iter("source"):
    src.text = "."                                 # resolve against the repo root
tree.write(out, xml_declaration=True, encoding="utf-8")
print("coverage.xml files:", sorted({c.get("filename") for c in root.iter("class")}))
