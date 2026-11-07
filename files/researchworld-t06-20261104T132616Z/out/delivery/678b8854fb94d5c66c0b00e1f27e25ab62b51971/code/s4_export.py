"""Tidy result tables for the figures/tables and the paper (schemas in results/README.md). Pure post-processing of the
stage 0-3 outputs; no resampling here except cheap percentile / Wilson / claim-level bootstrap summaries.
Usage: python code/s4_export.py"""
import json
import os

import numpy as np
import pandas as pd

from btlib import data, prov

OUT = os.path.join(os.path.dirname(__file__), "..", "results")
RNG = np.random.default_rng(5)


def rd(name):
    return pd.read_csv(f"{OUT}/{name}")


def rev(meta):
    return json.load(open(f"{OUT}/{meta}"))["code_rev"]


def dver(unit):
    key = {"arena55k": "arena55k.csv", "mt_human": "mt_human.parquet", "mt_gpt4": "mt_gpt4.parquet"}.get(unit, "nbaallelo.csv")
    return data.SOURCES[key]


def wilson(p, n, z=1.959964):
    d = 1 + z * z / n
    c = (p + z * z / (2 * n)) / d
    h = z * np.sqrt(p * (1 - p) / n + z * z / (4 * n * n)) / d
    return np.clip(c - h, 0, 1), np.clip(c + h, 0, 1)


def claim_cols(df):
    t = df.claim.str.extract(r"^(c\d)(?:_(\d+))?$")
    df["claim_type"] = t[0].str.upper()
    num = t[1].astype(float)
    df["claim_id"] = df.claim
    df["rank"] = np.where(df.claim_type == "C2", num + 1, np.where(df.claim_type == "C3", num, 1)).astype(float)
    return df


def summary_datasets():
    s = rd("dataset_summary.csv")
    s["n_tie"] = (s.tie_frac * s.N).round().astype(int)
    s["frac_pairs_unobserved"] = 1 - s.n_pairs_compared / s.n_pairs_possible
    s["data_version"] = s.unit.map(dver)
    s["code_rev"] = rev("s0_base.meta.json")
    s = s.rename(columns={"unit": "dataset", "pair_count_median": "pair_count_median", "bootstrap_B": "bootstrap_B"})
    s["claim_set"] = np.where(s.K_eligible < s.K, "C2/C4 over the top-" + s.K_eligible.astype(str) + " ranks; C1/C3 challengers: all participants",
                              "all participants")
    s.to_csv(f"{OUT}/summary_datasets.csv", index=False, float_format="%.6g")


def base_scores():
    parts = []
    for u in ["arena55k", "mt_human", "mt_gpt4", "nba_all"]:
        b = rd(f"base_{u}.csv")
        b.insert(0, "dataset", u)
        parts.append(b)
    b = pd.concat(parts)
    b = b.rename(columns={"score_elo": "score", "ci_lo_elo": "ci_lo", "ci_hi_elo": "ci_hi", "se_elo": "se"})
    b["score_scale"] = "Elo-scale = theta * 400/ln(10), sum-free (L2-regularised), eligible participants only"
    b["ci_level"] = "95% percentile bootstrap over comparisons, B=1000"
    b["code_rev"] = rev("s0_base.meta.json")
    b["seed"] = 0
    b.to_csv(f"{OUT}/base_scores.csv", index=False, float_format="%.6g")


def random_survival():
    r = rd("random_all.csv")
    long, tau = [], []
    for _, x in r.iterrows():
        n = int(x.seeds)
        base = dict(dataset=x.unit, design=x.design, perturbation=x.kind, f=x.frac, m=x.m, n_seeds=n, N=int(x.N), seed=1)
        ps = [("C1", "c1", 1, x.c1_survive)]
        for k in (3, 5, 10):
            if f"c3_{k}_survive" in r and not pd.isna(x.get(f"c3_{k}_survive")):
                ps.append(("C3", f"c3_{k}", k, x[f"c3_{k}_survive"]))
        for i, p in enumerate(str(x.c2_survive_each).split(";")):
            ps.append(("C2", f"c2_{i}", i + 1, float(p)))
        for ct, cid, rk, p in ps:
            lo, hi = wilson(p, n)
            long.append(dict(base, claim_type=ct, claim_id=cid, rank=rk, p_survive=p, ci_lo=lo, ci_hi=hi))
        tau.append(dict(base, tau_mean=x.tau_mean, tau_p05=x.tau_p05))
    L = pd.DataFrame(long)
    L["code_rev"] = rev("s1_random.meta.json")
    L.to_csv(f"{OUT}/random_survival.csv", index=False, float_format="%.6g")
    pd.DataFrame(tau).to_csv(f"{OUT}/random_tau.csv", index=False, float_format="%.6g")


def adv_budgets():
    d = rd("budgets_remove.csv")
    d = claim_cols(d)
    d["dataset"] = d.unit
    d["exact_tie"] = d.gap < 1e-9
    d["verified"] = d.flipped
    d["search_status"] = np.where(d.flipped, "found", "not_found_exhausted_all_comparisons")
    d["search_cap"] = d.N
    d["method"] = "greedy_relinearised_polished"
    d["budget_frac_pair"] = d.frac_pairinv
    d["budget_noise_units"] = d.leverage
    d["leverage_identity"] = d.z * np.sqrt((d.N - d.budget) / d.budget.where(d.budget >= 1))
    d["z_gap"] = d.z
    d["n_pair_comparisons"] = d.n_ab
    d["n_pair_involving"] = d.n_a_or_b
    d["n_min_participant"] = np.minimum(d.n_a, d.n_b)
    d["sparse_pair"] = d.n_min_participant < 200  # one of the two participants has fewer than 200 comparisons (descriptive flag)
    d["budget_frac_N"] = d.frac_N
    d["pair_hi"], d["pair_lo"] = d.a, d.b
    d["seed"] = 2
    d["code_rev"] = rev("s1_adv.meta.json")
    d["data_version"] = d.unit.map(dver)
    try:
        u = rd("s3_uncert.csv")
        u = u[u.flipped & (u.gap > 1e-9)]
        g = u.groupby(["unit_base", "claim"]).budget.agg(budget_lo=lambda s: np.percentile(s, 2.5),
                                                          budget_hi=lambda s: np.percentile(s, 97.5),
                                                          budget_resample_median="median", n_resamples="size").reset_index()
        d = d.merge(g.rename(columns={"unit_base": "dataset"}), on=["dataset", "claim"], how="left")
        d["budget_interval"] = "2.5-97.5 percentile of the budget of the same-named claim (claim at that rank) over dataset-bootstrap resamples"
    except FileNotFoundError:
        pass
    cols = ["dataset", "design", "season", "claim_type", "claim_id", "rank", "pair_hi", "pair_lo", "gap", "exact_tie", "budget",
            "budget_frac_N", "budget_frac_pair", "budget_noise_units", "leverage_identity", "k_per_sqrtN", "z_gap", "se_gap", "p_boot_pair_holds",
            "n_pair_comparisons", "n_pair_involving", "n_a", "n_b", "n_min_participant", "sparse_pair", "N", "K", "method", "verified", "search_status", "search_cap",
            "lin_est", "rand_shift_sd_at_k", "rand_shift_mean_at_k", "rand_flip_prob_at_k", "data_version", "code_rev", "seed"]
    cols += [c for c in ("budget_lo", "budget_hi", "budget_resample_median", "n_resamples", "budget_interval") if c in d]
    d[cols].to_csv(f"{OUT}/adv_budgets.csv", index=False, float_format="%.6g")
    return d


def method_validity(d):
    b = d[d.unit.isin(["arena55k", "mt_human", "mt_gpt4", "nba_all"]) & d.claim_type.isin(["C2"])]
    rows = []
    for _, x in b.iterrows():
        for m, col in [("influence_linearised_estimate", "lin_est"), ("one_shot_top_k_verified", "budget_oneshot"),
                       ("greedy_verified_unpolished", "budget_greedy_raw"), ("greedy_polished_verified", "budget"),
                       ("heuristic_direct_pair_removal", "budget_heur_direct"), ("heuristic_own_wins_removal", "budget_heur_own_wins")]:
            rows.append(dict(dataset=x.unit, claim_id=x.claim, rank=x["rank"], method=m, budget=x[col],
                             verified=m != "influence_linearised_estimate", N=x.N))
    M = pd.DataFrame(rows)
    best = M[M.verified].groupby(["dataset", "claim_id"]).budget.min().rename("best_verified")
    M = M.merge(best.reset_index(), on=["dataset", "claim_id"])
    M["ratio_to_best_verified"] = M.budget / M.best_verified.replace(0, np.nan)
    M["code_rev"] = rev("s1_adv.meta.json")
    M.to_csv(f"{OUT}/method_validity.csv", index=False, float_format="%.6g")
    if os.path.exists(f"{OUT}/s1_exhaustive.csv"):
        e = rd("s1_exhaustive.csv")
        e["greedy_polish_equals_exact"] = e.greedy_polish == e.exact
        e["code_rev"] = rev("s1_exhaustive.meta.json")
        e.to_csv(f"{OUT}/method_validity_exhaustive.csv", index=False, float_format="%.6g")


def boot_median(x, B=2000):
    x = np.asarray(x, float)
    x = x[~np.isnan(x)]
    if len(x) == 0:
        return np.nan, np.nan, np.nan
    m = np.median(x[RNG.integers(0, len(x), (B, len(x)))], axis=1)
    return np.median(x), *np.percentile(m, [2.5, 97.5])


def ablations(d):
    a = rd("s3_ablations.csv")
    base = d[d.claim.str.startswith("c2") & d.flipped].copy()
    base["variant"] = "baseline"
    base["dataset"] = base.unit
    a = a[a.claim.str.startswith("c2")].copy()
    a["dataset"] = a.unit
    a["frac_N"] = a.budget / a.N
    a["synthetic"] = False
    cols = ["variant", "dataset", "design", "claim", "gap", "budget", "frac_N", "N", "z", "flipped"]
    allr = pd.concat([base[cols[:1] + cols[1:]], a[cols]], ignore_index=True)
    allr["synthetic"] = False
    allr["exact_tie"] = allr.gap < 1e-9
    allr.to_csv(f"{OUT}/ablations.csv", index=False, float_format="%.6g")
    rows = []
    # NBA seasons pooled: variants with per-season rows are summarised over seasons
    allr["group"] = np.where(allr.dataset.str.match(r"^nba\d{4}$"), "nba_seasons", allr.dataset)
    for (v, g), s in allr[(allr.flipped) & (~allr.exact_tie)].groupby(["variant", "group"]):
        med, lo, hi = boot_median(s.frac_N)
        rows.append(dict(variant=v, dataset=g, n_claims=len(s), median_frac_N=med, ci_lo=lo, ci_hi=hi,
                         median_budget=s.budget.median(), synthetic=False,
                         interval="95% percentile of claim-level bootstrap of the median (B=2000); claims within a season are not independent"))
    pd.DataFrame(rows).to_csv(f"{OUT}/ablations_summary.csv", index=False, float_format="%.6g")


def additions(d):
    r = rd("s3_rigging.csv")
    r = claim_cols(r)
    rem = d[["unit", "claim", "budget", "flipped", "gap"]].rename(columns={"budget": "budget_remove", "flipped": "flipped_remove"})
    out = []
    for mode in ("add", "relabel"):
        x = r[r["mode"] == mode][["unit", "claim", "claim_type", "rank", "design", "N", "gap", "budget", "flipped", "z", "n_a_or_b"]]
        x = x.rename(columns={"budget": f"budget_{mode}", "flipped": f"flipped_{mode}"})
        out.append(x)
    m = out[0].merge(out[1][["unit", "claim", "budget_relabel", "flipped_relabel"]], on=["unit", "claim"]).merge(rem[["unit", "claim", "budget_remove", "flipped_remove"]], on=["unit", "claim"])
    m = m.rename(columns={"unit": "dataset"})
    m["ratio_add_over_remove"] = m.budget_add / m.budget_remove.replace(0, np.nan)
    m["ratio_relabel_over_remove"] = m.budget_relabel / m.budget_remove.replace(0, np.nan)
    m["frac_N_add"] = m.budget_add / m.N
    m["frac_N_remove"] = m.budget_remove / m.N
    m["frac_N_relabel"] = m.budget_relabel / m.N
    m["exact_tie"] = m.gap < 1e-9
    m["synthetic"] = False
    m.to_csv(f"{OUT}/additions.csv", index=False, float_format="%.6g")


def controls(d):
    fn = "s2_controls_syn_sub_arena6.csv"
    if not os.path.exists(f"{OUT}/{fn}"):
        return
    c = claim_cols(rd(fn))
    c["synthetic"] = c.kind == "syn"
    c["frac_N"] = c.budget / c.N
    c["frac_pairinv"] = c.budget / c.n_a_or_b
    c["code_rev"] = rev(fn.replace(".csv", ".meta.json"))
    c.to_csv(f"{OUT}/controls.csv", index=False, float_format="%.6g")
    real = d[d.claim.str.startswith("c2") & d.flipped & (d.gap > 1e-9)].copy()
    real["group"] = real.unit.where(~real.unit.str.match(r"^nba\d{4}$"), real.unit)
    rows = []

    def summ(df, label, base, kind, N):
        df = df[df.flipped & (df.gap > 1e-9) & (df.budget >= 1)]
        if len(df) == 0:
            return
        X = np.column_stack([np.ones(len(df)), np.log(df.z), np.log(df.n_a_or_b.clip(lower=1))])
        beta = np.linalg.lstsq(X, np.log(df.budget), rcond=None)[0] if len(df) > 5 else [np.nan] * 3
        rows.append(dict(label=label, base=base, kind=kind, N=N, n_claims=len(df), median_budget=df.budget.median(),
                         median_frac_N=(df.budget / df.N).median(), median_z=df.z.median(), median_n_pair_involving=df.n_a_or_b.median(),
                         median_log_budget_minus_log_z=(np.log(df.budget) - np.log(df.z)).median(),
                         M1_const=beta[0], M1_log_z=beta[1], M1_log_n_pair=beta[2], synthetic=kind == "syn"))

    for u in ["arena55k", "mt_human", "mt_gpt4", "nba_all"]:
        summ(real[real.unit == u], f"real {u}", u, "real", int(real[real.unit == u].N.iloc[0]))
    summ(real[real.unit.str.match(r"^nba\d{4}$")], "real nba seasons", "nba_seasons", "real", np.nan)
    c2 = c[c.claim.str.startswith("c2")]
    for (k, base, N), s in c2.groupby(["kind", "base", "N_target"]):
        s2 = s[~s.base.str.match(r"^nba\d{4}$")]
        summ(s, f"{k} {base} N={N}", base, k, N)
    pd.DataFrame(rows).to_csv(f"{OUT}/control_comparison.csv", index=False, float_format="%.6g")


def matched():
    b = rd("s2_matched_budgets.csv")
    b = claim_cols(b) if b.claim.str.match(r"^c\d").any() else b
    b.to_csv(f"{OUT}/matched_labeller.csv", index=False, float_format="%.6g")
    P = b[b.claim_set == "all_pairs"].copy()
    P["pair"] = [" | ".join(sorted([x, y])) for x, y in zip(P.a, P.b)]
    rows = []

    def add(comp, ref, alts, pr):
        R = pr[pr.variant == ref].set_index("pair")
        A = pr[pr.variant.isin(alts)]
        for pair, g in A.groupby("pair"):
            if pair not in R.index:
                continue
            r = R.loc[pair]
            rows.append(dict(comparison=comp, pair=pair, ref_variant=ref, alt_variants=len(alts), ref_hi=r.a, ref_gap=r.gap, ref_budget=r.budget,
                             ref_z=r.z, ref_N=r.N, alt_hi_same_share=float((g.a == r.a).mean()),
                             alt_gap_median=g.gap.where(g.a == r.a, -g.gap).median(), alt_budget_median=g.budget.median(),
                             alt_budget_min=g.budget.min(), alt_budget_max=g.budget.max(), alt_z_median=g.z.median(), alt_N=g.N.median()))

    mt = P[P.variant.str.startswith("mt_")]
    add("mt_human_matched_all_vs_gpt4", "mt_human_matched_all", ["mt_gpt4_matched"], mt)
    add("mt_human_ordmatched_vs_gpt4_ordmatched_1232keys", "mt_human_ordmatched", ["mt_gpt4_ordmatched"], mt)
    add("mt_human_1perkey_draws_vs_gpt4", "mt_gpt4_matched", [v for v in mt.variant.unique() if "1per_key" in v], mt)
    out = pd.DataFrame(rows)
    out["code_rev"] = rev("s2_matched.meta.json")
    out.to_csv(f"{OUT}/matched_pairs.csv", index=False, float_format="%.6g")


def regression():
    c = rd("s3_models_coef.csv")
    c["code_rev"] = rev("s3_models.meta.json")
    c.to_csv(f"{OUT}/regression_coef.csv", index=False, float_format="%.6g")


def main():
    summary_datasets()
    base_scores()
    random_survival()
    d = adv_budgets()
    for f, args in [(method_validity, (d,)), (ablations, (d,)), (additions, (d,)), (controls, (d,)), (matched, ()), (regression, ())]:
        try:
            f(*args)
        except FileNotFoundError as e:
            print("skipped", f.__name__, e)
    prov.write_meta(f"{OUT}/s4_export.meta.json", script="code/s4_export.py")


if __name__ == "__main__":
    main()
