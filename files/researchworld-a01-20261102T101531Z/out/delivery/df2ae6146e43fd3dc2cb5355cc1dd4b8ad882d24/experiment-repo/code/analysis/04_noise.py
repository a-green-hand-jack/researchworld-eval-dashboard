"""Uncertainty from evaluation noise: parametric bootstrap of the score
matrix.  Each cell is redrawn  Binomial(n_eval, p_hat)/n_eval  (HELM: per
subject n_eval from the release; OLB: published test-set sizes, applied to the
raw accuracy and the normalised score is shifted by slope*(draw-raw), slope = least-squares
slope of normalised on raw; exact for IFEval/MATH/MMLU-PRO, approximate for
BBH/GPQA/MUSR whose normalisation is per-subtask).  For selected targets we recompute, on each draw,
the rank under each rule and k* (delta=ceiling and 20).  Targets are fixed
models, whose initial ranks vary with the draw.
  python 04_noise.py {helm|olb} B   -> results/noise_<board>.csv"""
import sys, time
from common import *
board, B = sys.argv[1], int(sys.argv[2])
rng = np.random.default_rng(12345)
if board == "helm":
    df = load_helm(); S0 = df.values; names = df.index.values
    N = pd.read_csv(f"{ROOT}/data/processed/helm_mmlu_neval.csv", index_col=0).loc[df.index].values.astype(float)
    def draw():
        p = np.clip(S0 / 100, 0, 1)
        return 100 * rng.binomial(N.astype(int), p) / N
else:
    o, S0 = load_olb("main"); names = o["fullname"].values
    Sraw, _ = load_olb("main", raw=True)[1], None
    Sraw = Sraw / 100
    nq = np.array([541, 6511, 1324, 448, 756, 12032])  # IFEval, BBH, MATH L5, GPQA, MUSR, MMLU-PRO
    ab = [np.polyfit(Sraw[:, j], S0[:, j], 1) for j in range(6)]
    def draw():
        out = np.empty_like(S0)
        for j in range(6):
            r = rng.binomial(nq[j], np.clip(Sraw[:, j], 0, 1)) / nq[j]
            out[:, j] = np.clip(S0[:, j] + ab[j][0] * (r - np.clip(Sraw[:, j], 0, 1)), 0, 100)
        return out
order = np.argsort(-S0.mean(1))
ranks = [0, 1, 2, 3, 4, 5, 7, 9, 14, 19, 29, 49] + ([99, 199, 499, 999] if board == "olb" else [])
tg = [int(order[r]) for r in ranks if r < len(S0)]
rows = []; t0 = time.time()
for b in range(B):
    S = S0 if b < 0 else draw()
    br = {r: initial_ranks(S, r) for r in R.RULES}
    for t in tg:
        for rule in R.RULES:
            for d in [20.0, 100.0]:
                rows.append((b, names[t], int(np.where(order == t)[0][0]) + 1, rule, d, V.min_k(S, t, rule, d), int(br[rule][t])))
    if b % 10 == 0: print(b, round(time.time() - t0), flush=True)
pd.DataFrame(rows, columns=["draw", "model", "rank_obs_mean", "rule", "delta", "k", "rank_draw"]).to_csv(f"{ROOT}/results/noise_{board}.csv", index=False)
