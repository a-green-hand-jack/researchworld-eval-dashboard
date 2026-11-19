"""Build the result tables read by the figure/table scripts (schema: DATA_CONTRACT.md of figtab-repo) from the raw run files.
usage: make_results.py OUTDIR [table ...]   raw runs are read from $RAW (default results/ (E1/E2/frontier CSVs written by scripts/run_*.py)."""
import sys, os, json, glob, subprocess, datetime
import numpy as np, pandas as pd
RAW = os.environ.get("RAW", "results")
out = sys.argv[1]; want = set(sys.argv[2:]); os.makedirs(out, exist_ok=True)
BOARD = {"helm": "helm_mmlu", "m6": "ollb_bench", "m6raw": "ollb_bench_raw", "m39": "ollb_sub"}
commit = subprocess.run(["git", "rev-parse", "HEAD"], capture_output=True, text=True).stdout.strip()
HELM_ORG = {"Amazon": "Amazon", "Arctic": "Snowflake", "Claude": "Anthropic", "Command": "Cohere", "DBRX": "Databricks", "DeepSeek": "DeepSeek",
            "GPT": "OpenAI", "Gemini": "Google", "Gemma": "Google", "PaLM": "Google", "Jamba": "AI21", "Llama": "Meta", "Mistral": "Mistral",
            "Mixtral": "Mistral", "OLMo": "AI2", "Palmyra": "Writer", "Phi": "Microsoft", "Qwen": "Alibaba", "Solar": "Upstage", "Yi": "01.AI"}
def helm_family(name): return HELM_ORG.get(name.split()[0].split("-")[0], name.split()[0])
def write(name, df, script, snapshot, seed=None):
    df.to_csv(f"{out}/{name}.csv", index=False)
    json.dump(dict(script=script, git_commit=commit, snapshot=snapshot, seed=seed, rows=len(df),
                   created=datetime.datetime.now(datetime.timezone.utc).isoformat(timespec="seconds")), open(f"{out}/{name}.meta.json", "w"), indent=1)
    print("wrote", name, len(df))
SNAP = dict(helm="HELM MMLU v1.13.0 (data_meta/helm_v1.13.0_manifest.json)",
            ollb="Open LLM Leaderboard results + contents snapshots (see code/README.md)")
def frontier():
    fs = []
    for f in sorted(glob.glob(f"{RAW}/frontier_*.csv")):
        d = pd.read_csv(f); d["board"] = d.board.map(BOARD); fs.append(d)
    d = pd.concat(fs); d["unit"] = "points"
    d["m"] = d.board.map({"helm_mmlu": 57, "ollb_bench": 6, "ollb_bench_raw": 6, "ollb_sub": 39})
    write("frontier", d[["board", "m", "target", "model", "rule", "incumbent", "unit", "B", "k", "depth", "feasible"]], "scripts/run_frontier.py", SNAP["helm"] + "; " + SNAP["ollb"], None)
def m_effect():
    def tab(regime, d, m_col, draw_col):
        rows = []
        for b, g in d.groupby("b"):
            rows.append(pd.DataFrame(dict(regime=regime, m=g[m_col], draw=g[draw_col], target=g.target, rule=g.rule, B_sigma=b, k_frac=g.k_breadth / g[m_col], depth_per_task=g.cost_depth / g[m_col],
                                          B_star_sigma=g.Bstar, feasible=g.feas_breadth, gap0=g.gap0, board=g.board)))
        g = d[d.b == d.b.min()]
        rows.append(pd.DataFrame(dict(regime=regime, m=g[m_col], draw=g[draw_col], target=g.target, rule=g.rule, B_sigma=np.inf, k_frac=g.k_inf / g[m_col], depth_per_task=g.depth_inf / g[m_col],
                                      B_star_sigma=g.Bstar, feasible=g.feas_inf, gap0=g.gap0, board=g.board)))
        return pd.concat(rows)
    parts = []
    h = pd.concat([pd.read_csv(f) for f in sorted(glob.glob(f"{RAW}/e2_helm_s*.csv") + glob.glob(f"{RAW}/e2_helmbig_s*.csv"))])
    h = h.drop_duplicates(["m_sub", "draw", "target", "rule", "b"]); h["board"] = "helm_mmlu"  # the m=25 draw of the first jobs repeats in the big-m shards
    parts.append(tab("helm_subset", h, "m_sub", "draw"))
    for f in glob.glob(f"{RAW}/e2_full_helm.csv"):
        d = pd.read_csv(f); d["draw"] = 0; parts.append(tab("helm_full", d, "m", "draw"))
    o = glob.glob(f"{RAW}/e2_ollb_s*.csv")
    if o:
        d = pd.concat([pd.read_csv(f) for f in sorted(o)]); d["draw"] = 0
        for bd, reg in (("m6raw", "ollb_bundled"), ("m39", "ollb_free")):
            g = d[d.board == bd].copy(); g["board"] = BOARD[bd]; parts.append(tab(reg, g, "m", "draw"))
    write("m_effect", pd.concat(parts), "scripts/run_e2_helm.py, scripts/run_e2_ollb.py", SNAP["helm"] + "; " + SNAP["ollb"], 20260101)
def _family(board, names):
    if board == "helm_mmlu": return [helm_family(n) for n in names]
    sys.path.insert(0, os.getcwd())
    from lbprice.boards import load_ollb, ollb_family
    b = load_ollb({"ollb_bench": "m6", "ollb_bench_raw": "m6raw", "ollb_sub": "m39"}[board]); fam = dict(zip(b["names"], ollb_family(b["meta"])[1]))
    return [fam.get(n, str(n).split("/")[0].lower()) for n in names]
def _names(board):
    sys.path.insert(0, os.getcwd())
    from lbprice.boards import load_helm, load_ollb
    return load_helm()["names"] if board == "helm_mmlu" else load_ollb({"ollb_bench": "m6", "ollb_bench_raw": "m6raw", "ollb_sub": "m39"}[board])["names"]
def price():
    fs = []
    for f in sorted(glob.glob(f"{RAW}/e1_*.csv")):
        d = pd.read_csv(f); d["board"] = d.board.map(BOARD); fs.append(d)
    d = pd.concat(fs, ignore_index=True)
    key = ["board", "target", "model", "rule", "mode", "unit", "B"]
    br = d[d.objective == "breadth"].set_index(key); de = d[d.objective == "depth"].set_index(key)
    p = pd.DataFrame(dict(k_star=br.breadth, depth_at_kstar=br.depth, cost_at_kstar=br.cost, feasible=br.feasible, depth_star=de.depth, cost_star=de.cost, feasible_depth=de.feasible,
                          B_star=br.Bstar, init_rank=br.rank_official, rank_rule=br.rank_rule, gap=br.gap0, leader=br.leader, uniform_depth=br.uniform_depth,
                          targeting_mult=br.mult, solver=np.where(br.index.get_level_values("rule").isin(["plurality", "borda", "copeland"]), "milp", "exact"), opt_gap=br.mip_gap, verified=br.verified)).reset_index()
    p["incumbent_id"] = [_names(b)[int(l)] for b, l in zip(p.board, p.leader)] if False else None
    nm = {b: _names(b) for b in p.board.unique()}; p["incumbent_id"] = [nm[b][int(l)] for b, l in zip(p.board, p.leader)]
    p = p.drop(columns="leader").rename(columns={"mode": "incumbent"}); p["m"] = p.board.map({"helm_mmlu": 57, "ollb_bench": 6, "ollb_bench_raw": 6, "ollb_sub": 39})
    fam = {}
    for b, g in p.groupby("board"): fam[b] = dict(zip(g.model, _family(b, g.model)))
    p["family"] = [fam[b][m_] for b, m_ in zip(p.board, p.model)]
    write("price", p, "scripts/run_e1_helm.py, scripts/run_e1_ollb.py", SNAP["helm"] + "; " + SNAP["ollb"], None)
def boards():
    sys.path.insert(0, os.getcwd())
    import hashlib
    from lbprice.boards import load_helm, load_ollb
    sha = lambda f: hashlib.sha256(open(f, "rb").read()).hexdigest()[:16]
    h = load_helm(); b6 = load_ollb("m6"); b6r = load_ollb("m6raw"); b39 = load_ollb("m39"); b6all = load_ollb("m6", slice_="all")
    man = json.load(open("data_meta/helm_v1.13.0_manifest.json"))
    rows = [dict(board="helm_mmlu", snapshot="HELM MMLU release v1.13.0 (2025-01-10)", sha="manifest of %d files, data_meta/helm_v1.13.0_manifest.json; data_proc/helm_mmlu_em.csv sha256 %s" % (len(man), sha("data_proc/helm_mmlu_em.csv")),
                date="2025-01-10", m=h["S"].shape[1], N=h["S"].shape[0], noise_source="binomial from the number of evaluated items per subject (data_proc/helm_mmlu_neval.csv)", n_targets=h["S"].shape[0],
                exclusions="none (all models are targets)"),
            dict(board="ollb_bench", snapshot="Open LLM Leaderboard `contents` (commit 9c09a7cae43334062a82cb164f2ef255013dafa2, updated 2025-03-20)", sha="data_proc/ollb_m6_contents.csv sha256 " + sha("data_proc/ollb_m6_contents.csv"),
                date="2025-03-20", m=6, N=b6["S"].shape[0], noise_source="none in `contents` (noise-free, or the `results` stderr join for E6)", n_targets=30,
                exclusions="main slice: merged, flagged and not-on-hub models removed (all-rows board: N=%d)" % b6all["S"].shape[0]),
            dict(board="ollb_bench_raw", snapshot="Open LLM Leaderboard `results` (commit aa81ecc38fdc5708254b833923368970efdf5ef5, updated 2025-03-15), benchmark means of the sub-task scores", sha="data_proc/ollb_sub_scores.csv sha256 " + sha("data_proc/ollb_sub_scores.csv"),
                date="2025-03-15", m=6, N=b6r["S"].shape[0], noise_source="stderr from `results` (data_proc/ollb_sub_se.csv)", n_targets=30, exclusions="main slice; models whose `results` file reproduces the `contents` row"),
            dict(board="ollb_sub", snapshot="Open LLM Leaderboard `results` (commit aa81ecc38fdc5708254b833923368970efdf5ef5, updated 2025-03-15), sub-task level (BBH 24, GPQA 3, MuSR 3, MATH 7, IFEval 1, MMLU-Pro 1 task)", sha="data_proc/ollb_sub_scores.csv sha256 " + sha("data_proc/ollb_sub_scores.csv"),
                date="2025-03-15", m=39, N=b39["S"].shape[0], noise_source="stderr per sub-task from `results` (data_proc/ollb_sub_se.csv)", n_targets=30, exclusions="main slice; the `results` files carry no MMLU-Pro subjects, so m=39 (not 45-50)")]
    write("boards", pd.DataFrame(rows), "scripts/make_results.py (boards)", SNAP["helm"] + "; " + SNAP["ollb"], None)
def solver_check():
    d = pd.read_csv(f"{RAW}/solver_check_tests.csv")
    p = pd.read_csv(f"{out}/price.csv") if os.path.exists(f"{out}/price.csv") else None
    if p is not None:
        size = {"helm_mmlu": "N=79, m=57", "ollb_bench": "N=%d, m=6", "ollb_bench_raw": "N=%d, m=6", "ollb_sub": "N=%d, m=39"}
        sys.path.insert(0, os.getcwd())
        from lbprice.boards import load_ollb
        N = {"ollb_bench": len(load_ollb("m6")["S"]), "ollb_bench_raw": len(load_ollb("m6raw")["S"]), "ollb_sub": len(load_ollb("m39")["S"])}
        rows = []
        for (rule, board), g in p.groupby(["rule", "board"]):
            rows.append(dict(rule=rule, instance_class=f"real-board plans re-verified with rules.is_first; board {board}", n_instances=len(g), n_agree=int(g.verified.sum()),
                             max_size=(size[board] % N[board]) if "%d" in size[board] else size[board], max_opt_gap=float(g.opt_gap.max()), n_opt_gap_gt_1e_4=int((g.opt_gap > 1e-4).sum())))
        d = pd.concat([d, pd.DataFrame(rows)], ignore_index=True)
    write("solver_check", d, "scripts/run_checks.py (tests/), scripts/make_results.py", "synthetic instances (seeded) and the E1 runs", 0)
def calibration():
    import subprocess as sp
    sp.run([sys.executable, "scripts/run_calibration.py", out], check=True, capture_output=True)
    for n in ("calibration", "calibration_summary"):
        json.dump(dict(script="scripts/run_calibration.py", git_commit=commit, snapshot=SNAP["ollb"] + " (`contents`)", seed=20260102, rows=len(pd.read_csv(f"{out}/{n}.csv")),
                       created=datetime.datetime.now(datetime.timezone.utc).isoformat(timespec="seconds")), open(f"{out}/{n}.meta.json", "w"), indent=1)
def analysis_meta():
    """sidecars for the files written directly by analysis/*.py into the tables directory"""
    src = {"paired": "analysis/run_analysis.py", "rule_order": "analysis/run_analysis.py", "m_effect_fit": "analysis/r4.py", "units": "analysis/units.py", "units_tau": "analysis/units.py",
           "predictors": "analysis/predictors.py", "verdicts": "analysis/verdicts.py", "r1_detail": "analysis/verdicts.py", "e6_summary": "analysis/e6.py", "e6_confidence": "analysis/e6.py", "e6_topnoise": "analysis/e6.py", "e5_summary": "analysis/e5.py", "e7_margin_slice": "analysis/e7.py", "e7_totalcap": "analysis/e7.py", "spillover_matrix": "analysis/spillover.py", "spillover_price": "analysis/spillover.py", "predictors_hl": "analysis/hl.py", "predictors_within": "analysis/predictors_within.py", "price_magnitude": "analysis/magnitude.py", "flip_profile": "analysis/flip.py", "flip_summary": "analysis/flip.py", "flip_proxy": "analysis/flip.py", "flip_N": "analysis/flip.py", "bx_curve": "analysis/bx.py", "bx_crossing": "analysis/bx.py", "predictors_norm": "analysis/predictors_norm.py", "e6b_confidence": "analysis/e6b.py", "e6b_curve": "analysis/e6b.py"}
    for n, sc in src.items():
        f = f"{out}/{n}.csv"
        if os.path.exists(f):
            json.dump(dict(script=sc, git_commit=commit, snapshot=SNAP["helm"] + "; " + SNAP["ollb"], seed="fixed in the script (see code/README.md)", rows=len(pd.read_csv(f)),
                           created=datetime.datetime.now(datetime.timezone.utc).isoformat(timespec="seconds")), open(f"{out}/{n}.meta.json", "w"), indent=1)
for name, fn in [("frontier", frontier), ("price", price), ("m_effect", m_effect), ("boards", boards), ("calibration", calibration), ("solver_check", solver_check), ("analysis_meta", analysis_meta)]:
    if not want or name in want: fn()
