#!/usr/bin/env python3
"""Build the integrated manuscript from the delivery root."""
from pathlib import Path
import argparse
import os
import shutil
import subprocess
import sys

ROOT = Path(__file__).resolve().parents[1]
SOURCE = ROOT / "manuscript" / "main.tex"
BUILD = ROOT / "manuscript" / ".build"
STYLE = ROOT / "venue" / "neurips2026" / "neurips_2026.sty"


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--clean", action="store_true", help="remove only generated manuscript build files")
    args = parser.parse_args()
    if args.clean:
        if BUILD.exists():
            shutil.rmtree(BUILD)
        return 0
    missing = [str(p.relative_to(ROOT)) for p in (SOURCE, STYLE) if not p.is_file()]
    if missing:
        parser.error("required authored/template inputs are not yet present: " + ", ".join(missing))
    if not shutil.which("latexmk"):
        parser.error("latexmk is required; see venue requirements and manuscript/BUILD.md")
    BUILD.mkdir(parents=True, exist_ok=True)
    env = os.environ.copy()
    # A trailing empty component retains the TeX installation's standard paths.
    for key in ("TEXINPUTS", "BIBINPUTS"):
        env[key] = os.pathsep.join((str(ROOT), str(ROOT / "venue" / "neurips2026"),
                                    str(ROOT / "manuscript"),
                                    env.get(key, ""), ""))
    subprocess.run(["latexmk", "-pdf", "-interaction=nonstopmode", "-halt-on-error",
                    "-file-line-error", "-outdir=" + str(BUILD), str(SOURCE)],
                   cwd=ROOT, env=env, check=True)
    log = (BUILD / "main.log").read_text(errors="replace")
    unresolved = ("There were undefined references", "There were undefined citations",
                  "Citation `", "Reference `", "Label(s) may have changed")
    if any(marker in log for marker in unresolved):
        print("Unresolved references or citations; inspect manuscript/.build/main.log", file=sys.stderr)
        return 1
    pdf = BUILD / "main.pdf"
    if not pdf.is_file():
        raise RuntimeError("latexmk returned without producing main.pdf")
    shutil.copyfile(pdf, ROOT / "paper.pdf")
    print("Built paper.pdf; inspect layout and main-text page count before committing.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
