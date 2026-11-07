"""Concatenate per-unit parts of stage 1 into results/budgets_remove.csv and results/random_all.csv and add the scale columns.

Scale columns (all derived from the verified budget k, the data size N and the claim pair (a, b)):
  frac_N        = k / N                       fraction of all comparisons
  frac_pairinv  = k / (n_a + n_b - n_ab)      fraction of the comparisons involving a or b
  k_per_sqrtN   = k / sqrt(N)
  leverage      = gap / SD(shift of gap under random removal of k comparisons)   [noise-equivalent scale]
Usage: python code/s2_collect.py"""
import glob
import os
import re

import numpy as np
import pandas as pd

from btlib import prov

OUT = os.path.join(os.path.dirname(__file__), "..", "results")


def natural(path):
    return [int(t) if t.isdigit() else t for t in re.split(r"(\d+)", path)]


def main():
    adv = pd.concat([pd.read_csv(f) for f in sorted(glob.glob(f"{OUT}/parts/s1_adv_*.csv"), key=natural)], ignore_index=True)
    adv["frac_N"] = adv.budget / adv.N
    adv["frac_pairinv"] = adv.budget / adv.n_a_or_b
    adv["k_per_sqrtN"] = adv.budget / np.sqrt(adv.N)
    adv["leverage"] = adv.gap / adv.rand_shift_sd_at_k
    adv["season"] = adv.unit.str.extract(r"^nba(\d{4})$")[0].astype(float)
    adv.to_csv(f"{OUT}/budgets_remove.csv", index=False, float_format="%.6g")
    rnd = pd.concat([pd.read_csv(f) for f in sorted(glob.glob(f"{OUT}/parts/s1_random_*.csv"), key=natural)], ignore_index=True)
    rnd.to_csv(f"{OUT}/random_all.csv", index=False, float_format="%.6g")
    print(adv.groupby("design").size().to_dict(), "units:", adv.unit.nunique(), "| random rows:", len(rnd))
    prov.write_meta(f"{OUT}/s2_collect.meta.json", script="code/s2_collect.py")


if __name__ == "__main__":
    main()
