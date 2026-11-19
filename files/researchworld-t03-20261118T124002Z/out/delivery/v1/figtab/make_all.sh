#!/bin/sh
# Rebuild every delivered figure and table from ../results/ (or $FIGTAB_RESULTS). Run from anywhere.
# ~10 min on 2 CPUs on a loaded host, dominated by the cluster bootstraps (fig1, fig4, tab1).
set -e
cd "$(dirname "$0")"
for s in fig1_tail fig2_yardstick fig3_certificates fig4_budget tab1_reliable_fraction tab2_certificates tabA_certificates figA_bstar figA_ecdf_x16 figA_c5_split; do python3 "$s.py"; done
python3 fig2_yardstick.py --perm
python3 fig3_certificates.py --appendix
python3 fig4_budget.py --by-model
for f in *.pdf; do pdffonts "$f" | grep -q "Type 3" && { echo "Type 3 font in $f"; exit 1; }; done
echo done
