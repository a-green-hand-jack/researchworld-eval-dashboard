# Figure / table generators (presentation)

Run from this directory: `python3 fig_data_overview.py` (reads `$GLAMBIE_DATA`, default `/initial-state/inputs/2/glambie`).

| Script | Outputs | Inputs |
|---|---|---|
| `fig_data_overview.py` | `report/images/fig01_input_inventory.png`, `fig02_input_coverage.png`; `code/figures/tables/T1_inventory_region_by_method.{csv,md}`, `input_inventory_files.csv` | `glambie/input/*/*.csv` (257 files) |

`common.py` fixes region names/order, method labels and the Okabe–Ito method palette used by every figure.
| `fig_results.py` | `report/images/fig03`–`fig08_*.png`; `code/figures/tables/T2`–`T4` (`.csv`,`.md`), `group_agreement_common_period.csv` | `outputs/*.csv` of experiment-repo (set `RECON_OUTPUTS` to override) and published `glambie/results/calendar_years` (benchmark overlay) |

Figures: 3 regional series vs published; 4 global annual + cumulative (SLE axis); 5 validation vs published; 6 regional ranking / halves / change in rate; 7 data-group agreement (mean annual 1σ as conservative bar); 8 robustness of the global rate.
