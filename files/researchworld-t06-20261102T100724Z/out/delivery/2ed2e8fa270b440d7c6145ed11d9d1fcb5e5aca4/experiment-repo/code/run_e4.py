"""E4: cross-design summary tables, paired M-h vs M-g contrast, scaling of k* with z and local sample size.
Reads results/*.csv written by run_full/run_units/run_matched; writes results/summary_claims.csv,
results/paired_mt.csv, results/scaling_fit.csv.  All intervals: percentile over replicate units (stated per row)."""
import sys, os
import numpy as np, pandas as pd
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import provenance as pv

RES = pv.RES
SEED = 20261107
rng = np.random.default_rng(SEED)


def load():
    fs = []
    for f in ("kstar_full.csv", "kstar_units.csv", "matched_arena.csv", "kstar_judges.csv"):
        p = os.path.join(RES, f)
        if os.path.exists(p):
            d = pd.read_csv(p); d["source_file"] = f; fs.append(d)
    return pd.concat(fs, ignore_index=True)


def q(x, p):
    return float(np.nanpercentile(x, p)) if len(x) else np.nan


def summary(d):
    d = d.copy()
    d["k_over_N"] = d.k_star / d.N
    d["k_over_Nlocal"] = d.k_star / d.N_local
    # C1 / C3 are one row per unit; C2/C4 pooled over pairs r<=10 (rank-specific numbers are in the unit files)
    g = d.groupby(["board", "design", "unit_type", "claim", "pert"])
    out = g.agg(n_rows=("k_star", "size"), n_units=("unit_id", "nunique"), frac_found=("found", "mean"),
                k_median=("k_star", "median"), k_q025=("k_star", lambda x: q(x, 2.5)), k_q975=("k_star", lambda x: q(x, 97.5)),
                kN_median=("k_over_N", "median"), kN_q025=("k_over_N", lambda x: q(x, 2.5)), kN_q975=("k_over_N", lambda x: q(x, 97.5)),
                kNloc_median=("k_over_Nlocal", "median"), z_median=("z", "median"),
                z_q025=("z", lambda x: q(x, 2.5)), z_q975=("z", lambda x: q(x, 97.5)),
                n_resolved=("z", lambda x: int(np.sum(np.abs(x) >= 1.96))),
                frac_z_lt_196=("z", lambda x: float(np.mean(np.abs(x) < 1.96))), N_median=("N", "median"),
                n_part=("n_part", "median")).reset_index()
    # median k* split by whether the unperturbed claim was already unresolved (|z| < 1.96) or resolved (|z| >= 1.96)
    for lab, m in (("unresolved", d.z.abs() < 1.96), ("resolved", d.z.abs() >= 1.96)):
        k = d[m].groupby(["board", "design", "unit_type", "claim", "pert"]).k_star.median().rename("k_median_" + lab)
        out = out.merge(k.reset_index(), how="left", on=["board", "design", "unit_type", "claim", "pert"])
    return out


def paired(d):
    u = d[(d.unit_type.isin(["qboot", "boot"])) & (d.pert.isin(["P1", "P2", "P3"]))]
    rows = []
    for a, b in (("mtbench_human", "mtbench_gpt4"), ("mtmatched_h", "mtmatched_g"), ("mtmatched_h1", "mtmatched_g")) + tuple(
            ("arena49k_h", "arena49k_" + j) for j in ("Meta-Llama-3-70B-Instruct", "Athene-70B", "Qwen2-72B-Instruct")):
        for (claim, cid, pert), _ in u.groupby(["claim", "claim_id", "pert"]):
            x = u[(u.board == a) & (u.claim == claim) & (u.claim_id == cid) & (u.pert == pert)].set_index("unit_id")
            y = u[(u.board == b) & (u.claim == claim) & (u.claim_id == cid) & (u.pert == pert)].set_index("unit_id")
            j = x.join(y, lsuffix="_a", rsuffix="_b", how="inner").dropna(subset=["k_star_a", "k_star_b"])
            if len(j) < 20:
                continue
            lr = np.log(j.k_star_b / j.k_star_a)
            lrN = np.log((j.k_star_b / j.N_b) / (j.k_star_a / j.N_a))
            dz = j.z_b - j.z_a
            rows.append(dict(a=a, b=b, claim=claim, claim_id=cid, pert=pert, n_units=len(j),
                             logratio_k_median=lr.median(), logratio_k_q025=q(lr, 2.5), logratio_k_q975=q(lr, 97.5),
                             logratio_kN_median=lrN.median(), logratio_kN_q025=q(lrN, 2.5), logratio_kN_q975=q(lrN, 97.5),
                             dz_median=dz.median(), dz_q025=q(dz, 2.5), dz_q975=q(dz, 97.5)))
    return pd.DataFrame(rows)


def ols(X, y):
    beta, *_ = np.linalg.lstsq(X, y, rcond=None)
    return beta


def dataset_cluster(r):
    """Independent-data cluster of a row: NBA seasons are independent data; every Arena board derives from one
    55k-vote sample and every MT-Bench-human / GPT-4 board from one judgment set, so those are single clusters."""
    if r.board == "nba_season":
        return "nba|" + str(r.unit_id)
    if r.board.startswith("nba_"):
        return "nba|" + r.board[4:]
    if r.board.startswith("arena"):
        return "arena"
    return "mt_g" if r.board.endswith("gpt4") or r.board.endswith("_g") else "mt_h"


def scaling(d, B=2000):
    """log k* = a + b1 log z + b2 log N_local (+ design dummies).  Two bootstrap schemes per fit:
    `unit`    resamples replicate units (within-dataset sampling variation only; replicates of one dataset are
              dependent, so this CI is conditional on the dataset and too narrow for generalisation);
    `dataset` resamples independent datasets (NBA seasons + the Arena / MT-human / MT-GPT-4 data as one cluster each);
              used for M0 only: in M1 the crowd/expert/judge dummies are single-dataset contrasts, so only the `unit` CI
              (conditional on the datasets used) is reported for them."""
    out = []
    for claim in ("C2", "C1", "C4"):
        for pert in ("P1", "P2", "P3"):
            x = d[(d.claim == claim) & (d.pert == pert) & d.found & (d.z > 0.02) & (d.k_star >= 1)].copy()
            x["cl_unit"] = x.board + "|" + x.unit_type + "|" + x.unit_id.astype(str)
            x["cl_dataset"] = x.apply(dataset_cluster, axis=1)
            x = x.reset_index(drop=True)
            if len(x) < 30:
                continue
            designs = sorted(x.design.unique())
            def design_matrix(z):
                cols = [np.ones(len(z)), np.log(z.z.values), np.log(z.N_local.values)]
                return np.column_stack(cols)
            def design_matrix_d(z):
                cols = [np.ones(len(z)), np.log(z.z.values), np.log(z.N_local.values)]
                cols += [(z.design.values == s).astype(float) for s in designs[1:]]
                return np.column_stack(cols)
            for model, dm, names in (("M0", design_matrix, ["const", "log_z", "log_Nlocal"]),
                                     ("M1", design_matrix_d, ["const", "log_z", "log_Nlocal"] + [f"design_{s}" for s in designs[1:]])):
                y = np.log(x.k_star.values)
                b0 = ols(dm(x), y)
                res = y - dm(x) @ b0
                for scheme in ("unit", "dataset"):
                    if model == "M1" and scheme == "dataset":
                        continue  # crowd / expert / judge are one dataset each: design dummies not identified across clusters
                    cl = x.groupby("cl_" + scheme).indices
                    keys = list(cl)
                    bs = []
                    for _ in range(B):
                        pick = rng.integers(0, len(keys), len(keys))
                        idx = np.concatenate([cl[keys[p]] for p in pick])
                        z = x.iloc[idx]
                        if model == "M1" and z.design.nunique() < len(designs):
                            continue
                        bs.append(ols(dm(z), np.log(z.k_star.values)))
                    bs = np.array(bs)
                    for n_, v, lo, hi in zip(names, b0, np.percentile(bs, 2.5, axis=0), np.percentile(bs, 97.5, axis=0)):
                        out.append(dict(claim=claim, pert=pert, model=model, term=n_, coef=v, ci_lo=lo, ci_hi=hi,
                                        scheme=scheme, n_boot_ok=len(bs), n_rows=len(x), n_clusters=len(keys),
                                        resid_sd=float(res.std()), r2=float(1 - res.var() / y.var())))
    return pd.DataFrame(out)


if __name__ == "__main__":
    d = load()
    inputs = [os.path.join(RES, f) for f in ("kstar_full.csv", "kstar_units.csv", "matched_arena.csv", "kstar_judges.csv") if os.path.exists(os.path.join(RES, f))]
    pv.save(summary(d), "summary_claims.csv", "run_e4.py", SEED, inputs)
    pv.save(paired(d), "paired_mt.csv", "run_e4.py", SEED, inputs)
    pv.save(scaling(d), "scaling_fit.csv", "run_e4.py", SEED, inputs, note="bootstrap B=2000, schemes unit / dataset (see run_e4.dataset_cluster)")
