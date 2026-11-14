"""Regenerate every figure and table from experiment-repo's results. python make_all.py  (see ../README.md)"""
import fig_curves, fig_width_trends, fig_grok_survival, fig_regimes, fig_mechanism, fig_wd_alpha, fig_frac, fig_scope, fig_budget, tables
for m in (fig_curves, fig_width_trends, fig_grok_survival, fig_regimes):
    m.main()
for m in (fig_mechanism, fig_wd_alpha, fig_frac, fig_scope, fig_budget, tables):
    m.main()
