#!/bin/bash
# Reproduce everything (final seed space, R=2000 per cell). Expected wall-clock ~4-6 h on 2 CPUs.
# Data must be present in ./data (see README). Dev runs (calibrator choice): src/sim.py --space dev (see README).
set -e
cd "$(dirname "$0")"
python3 -u src/theory.py > /dev/null
for g in real_primary shift forest_wor real_nsweep real_appendix synth; do
  python3 -u src/sim.py --grid $g --space final
done
python3 -u src/sim_boot.py
python3 -u src/analyze.py final
python3 -u src/theory_check.py final > /dev/null
python3 -u src/full_data.py > /dev/null
