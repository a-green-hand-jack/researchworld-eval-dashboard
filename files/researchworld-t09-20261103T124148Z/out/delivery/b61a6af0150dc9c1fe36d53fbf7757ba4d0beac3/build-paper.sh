#!/usr/bin/env bash
set -euo pipefail
cd "$(dirname "$0")"
# Keep the official style unchanged; locate it without copying or editing it.
sha256sum --check --status venue/sources/file-manifest.sha256
export TEXINPUTS="venue/official//:${TEXINPUTS:-}"
latexmk -pdf -interaction=nonstopmode -halt-on-error -jobname=paper main.tex
