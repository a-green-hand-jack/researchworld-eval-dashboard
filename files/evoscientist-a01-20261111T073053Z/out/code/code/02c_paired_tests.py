"""Paired comparisons across rules on common targets (ranks 2..31 by arithmetic mean; results/common_<bench>.csv).
For each benchmark x metric: Wilcoxon signed-rank test of (rule - mean) over targets, Holm correction over the 7 rules, plus
bootstrap 95% CI (10k resamples of targets) for the median paired ratio.  Targets that are already #1 under the rule or under
the mean rule are excluded from that pair (their requirement is 0 by definition)."""
import numpy as np, pandas as pd
from scipy.stats import wilcoxon
from lib import RULES
rng = np.random.default_rng(0); out = []
for b in ['helm', 'ollb6', 'bbh24']:
    df = pd.read_csv(f'results/common_{b}.csv'); name = df['bench'].iloc[0]
    for metric in ['gstar', 'K_100', 'L1_100']:
        W = df.pivot(index='rank', columns='rule', values=metric); AF = df.pivot(index='rank', columns='rule', values='already_first')
        res = []
        for r in RULES:
            if r == 'mean': continue
            ok = ~(AF[r] | AF['mean']); x = W.loc[ok, r]; y = W.loc[ok, 'mean']; m = x.notna() & y.notna(); x, y = x[m].values, y[m].values
            d = x - y
            try: p = wilcoxon(d).pvalue if (d != 0).any() else 1.0
            except ValueError: p = 1.0
            ratio = x / np.where(y == 0, np.nan, y); ratio = ratio[np.isfinite(ratio)]
            bs = [np.median(rng.choice(ratio, len(ratio))) for _ in range(10000)] if len(ratio) > 1 else [np.nan, np.nan]
            res.append(dict(bench=name, metric=metric, rule=r, n_pairs=len(d), median_rule=float(np.median(x)), median_mean=float(np.median(y)),
                            median_ratio=float(np.median(ratio)), ratio_lo=float(np.percentile(bs, 2.5)), ratio_hi=float(np.percentile(bs, 97.5)),
                            frac_rule_lower=float(np.mean(d < 0)), frac_rule_higher=float(np.mean(d > 0)), p_raw=p))
        R = pd.DataFrame(res).sort_values('p_raw').reset_index(drop=True); m = len(R)
        R['p_holm'] = np.minimum(1, np.maximum.accumulate((m - np.arange(m)) * R['p_raw'].values)); out.append(R)
T = pd.concat(out); T.to_csv('results/common_tests.csv', index=False)
pd.set_option('display.width', 250); print(T.round(3).to_string())
