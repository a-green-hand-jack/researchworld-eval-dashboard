"""(A) NBA single-season leaderboards (regular season, home term) and (B) common-size controls: subsample every dataset to
N0 comparisons (control 'N') and additionally to p0 participants (control 'N+p'). Worst-case budgets for top1 (drop, flip,
add) and the cheapest adjacent swap (drop, flip) per replicate. Usage: 04_seasons_commonN.py {seasons|commonN} [R]
->  results/nba_seasons.csv | results/commonN.csv (tidy)"""
import sys, time, numpy as np, pandas as pd, os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import rsens
res = os.path.dirname(os.path.abspath(__file__)) + "/../results/"; which = sys.argv[1]; t0 = time.time()
DESIGN = {"arena55k": "crowd", "mtbench_human": "expert", "mtbench_gpt4": "model_judge", "nba": "sports"}


def metrics(c, th):
    r = rsens.ranking(th, c.p); H = np.linalg.inv(rsens.hess(c, th)); out = {"n_components": int(rsens.n_components(c))}
    q = rsens.qvec(c, r[0], r[1]); out["z_top"] = (th[r[0]] - th[r[1]]) / np.sqrt(q @ H @ q)
    for mode in ("drop", "flip"):
        ks = [rsens.worst_case(c, r[0], r[j], mode, th0=th)["k"] for j in (1, 2, 3) if j < c.p]
        out[f"top1_{mode}"] = np.nanmin(ks) if np.isfinite(ks).any() else np.nan
        ks = [rsens.worst_case(c, r[i], r[i + 1], mode, th0=th)["k"] for i in range(c.p - 1)]
        out[f"adjmin_{mode}"] = np.nanmin(ks) if np.isfinite(ks).any() else np.nan
    ks = [rsens.inject_case(c, r[j], r[0], "a_wins", th0=th)["k"] for j in (1, 2, 3) if j < c.p]
    out["top1_add_a_wins"] = np.nanmin(ks) if np.isfinite(ks).any() else np.nan
    return out


rows = []
if which == "seasons":
    for y, lg in [(y, "NBA") for y in range(1947, 2016)] + [(y, "ABA") for y in range(1968, 1977)]:
        c = rsens.load(f"nba:{y}" + (":ABA" if lg == "ABA" else ""))
        if c.p < 8: continue
        th = rsens.fit(c); m = metrics(c, th)
        rows.append(dict(dataset="nba_season", eval_design="sports", unit=f"{y}-{lg}", lg_id=lg, replicate=-1, N=c.n, p=c.p, **m))
        print(y, round(time.time() - t0), flush=True)
    pd.DataFrame(rows).to_csv(res + "nba_seasons.csv", index=False)
elif which == "arena_controls":
    # plan v2 fixed controls: Arena subsampled to the N of MT-Bench (all 64 models); Arena restricted to its top-6 models
    # (by BT rank on the full data) with all comparisons among them, and subsampled to the same Ns.
    R = int(sys.argv[2]); rng = np.random.default_rng(78); c = rsens.load("arena55k"); th0 = rsens.fit(c); top6 = np.sort(rsens.ranking(th0, c.p)[:6])
    keep = np.flatnonzero(np.isin(c.I, top6) & np.isin(c.J, top6)); mp = {s: i for i, s in enumerate(top6)}
    c6 = rsens.Comp([c.names[s] for s in top6], [mp[i] for i in c.I[keep]], [mp[j] for j in c.J[keep]], c.Y[keep], "arena_top6")
    print("top6", c6.names, c6.n, flush=True)
    for ctrl, cc, N0 in [x for x in [("subN_all64", c, 2400), ("subN_all64", c, 3355), ("top6_full", c6, None), ("top6_subN", c6, 2400), ("top6_subN", c6, 3355)] if x[2] is None or x[2] <= x[1].n]:   # skip Ns larger than the restricted set
        print("control", ctrl, N0, flush=True)
        for rep in range(1 if N0 is None else R):
            cs = cc if N0 is None else cc.subset(rng.choice(cc.n, N0, replace=False))
            th = rsens.fit(cs); m = metrics(cs, th)
            rows.append(dict(dataset="arena55k", eval_design="crowd", control=ctrl, replicate=rep, seed=78, N=cs.n, p=cs.p, tie_rate=float((cs.Y == .5).mean()), **m))
        print(ctrl, N0, round(time.time() - t0), flush=True); pd.DataFrame(rows).to_csv(res + "arena_controls.csv", index=False)
else:
    R = int(sys.argv[2]); rng = np.random.default_rng(77); N0, p0 = 2000, 6
    for ds in DESIGN:
        c = rsens.load(ds)
        for ctrl in ("N", "N+p"):
            done = 0; tries = 0
            while done < R and tries < 20 * R:
                tries += 1
                if ctrl == "N":
                    if c.n < N0: break
                    idx = rng.choice(c.n, N0, replace=False); cs = c.subset(idx)
                else:
                    cnt = np.bincount(np.r_[c.I, c.J], minlength=c.p); pool = np.argsort(-cnt)[:20] if c.p > p0 else np.arange(c.p)
                    S = np.sort(rng.choice(pool, p0, replace=False)) if c.p > p0 else np.arange(c.p)
                    keep = np.flatnonzero(np.isin(c.I, S) & np.isin(c.J, S))
                    if len(keep) < N0: continue
                    cs = c.subset(rng.choice(keep, N0, replace=False))
                    pc = pd.crosstab(cs.I, cs.J); 
                    if len(set(cs.I) | set(cs.J)) < p0: continue
                    # re-index to the p0 participants
                    mp = {s: i for i, s in enumerate(S)}
                    cs = rsens.Comp([c.names[s] for s in S], [mp[i] for i in cs.I], [mp[j] for j in cs.J], cs.Y, ds, cs.x)
                th = rsens.fit(cs); m = metrics(cs, th)
                rows.append(dict(dataset=ds, eval_design=DESIGN[ds], control=ctrl, replicate=done, seed=77, N=cs.n, p=cs.p, tie_rate=float((cs.Y == .5).mean()), **m)); done += 1
            print(ds, ctrl, done, round(time.time() - t0), flush=True)
            pd.DataFrame(rows).to_csv(res + "commonN.csv", index=False)
