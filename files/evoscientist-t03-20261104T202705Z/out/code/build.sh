#!/bin/sh
# All paths resolve relative to this artifact root.
set -eu
exec python "$(dirname "$0")/build_paper.py"
