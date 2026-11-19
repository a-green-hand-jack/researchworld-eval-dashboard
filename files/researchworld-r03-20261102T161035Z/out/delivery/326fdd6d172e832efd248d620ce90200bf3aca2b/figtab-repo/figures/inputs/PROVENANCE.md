# Provenance of figures/inputs/
Copied unmodified from `world/experiment-repo` at commit b101927e6a39 and refreshed to experiment delivery v2 (`results/ct_*.csv`, `theory_fit.csv`, `rank_corr.csv`, `lowsd_check.csv` as merged in paper-repo main 1305ae1; the v1 rows are unchanged, bootstrap interval ends differ in the 3rd digit):
- protocol B (common target set, full-information reference): `results/{ct_curves,ct_paired,ct_reference,ct_k_needed}.csv`; `results/spectrum.csv`; `results/{theory_fit,theory_real_params,theory_real_curve}.csv`; `results/{theory_synth,theory_summary}.csv` (synthetic check).
- protocol A `results/curves.csv` is no longer used by any figure (Fig. 6b now uses `mteb_ntrain30/60` of `ct_curves.csv`); the copy is kept only for provenance.
- data: `data/{mteb_matrix,olb_matrix,olb_meta,helm_lite_matrix}.csv`.
Regenerate everything: `python3 figures/src/make_figs.py` from the repository root (~40 s on 2 CPUs; matplotlib 3.11.2, pandas 3.0.6, numpy 2.4.6). The raw per-split results (`results/raw_gz`, 65 MB) are not needed.
