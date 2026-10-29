"""Rebuild every report figure and table: python code/figures/make_all.py

Inputs: data/glambie (override with GLAMBIE_DATA) and experiment-repo's results
in outputs/reconciliation and outputs/validation (python code/run_all.py).
Outputs: report/images/fig*.png and outputs/tables/*.{csv,md}.
Requires numpy, pandas, matplotlib only.
"""
import fig01_data_overview
import fig02_regional_series
import fig03_global_series
import fig04_regional_contributions
import fig05_group_agreement
import fig06_validation
import fig07_sensitivity
import tables

if __name__ == "__main__":
    for mod in (fig01_data_overview, fig02_regional_series, fig03_global_series,
                fig04_regional_contributions, fig05_group_agreement,
                fig06_validation, fig07_sensitivity, tables):
        print(mod.main())
