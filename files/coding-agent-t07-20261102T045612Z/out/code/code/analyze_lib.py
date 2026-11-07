"""Loading + clustered-bootstrap aggregation of the main experiment."""
import glob, pickle, numpy as np, pandas as pd

BENCH_LABEL = {'arc_challenge': 'ARC-C', 'bbh': 'BBH', 'gpqa': 'GPQA', 'ifeval': 'IFEval', 'mmlu_pro': 'MMLU-Pro',
               'musr': 'MuSR', 'openllm_math': 'MATH-L5', 'commonsense': 'H:Commonsense', 'gsm': 'H:GSM8K',
               'legalbench': 'H:LegalBench', 'math': 'H:MATH', 'med_qa': 'H:MedQA', 'mmlu': 'H:MMLU'}


def load_rows(tag='main2'):
    rows, infos = [], []
    for f in sorted(glob.glob(f'/work/results/raw_{tag}/*.pkl')):
        d = pickle.load(open(f, 'rb'))
        rows += d['rows']; infos.append(d['info'])
    df = pd.DataFrame(rows); df['combo'] = df['sel'] + '/' + df['est']
    for c in ['mae', 'rmse', 'bias']:
        df[c] = df[c] * 100
    return df, pd.DataFrame(infos)


def cube(df, regime, k, combos, metric):
    """array [bench, rep, combo] (only reps present for every bench)."""
    d = df[(df.regime == regime) & (df.k == k) & (df.combo.isin(combos))]
    benches = sorted(d.bench.unique())
    nrep = min(d[d.bench == b].rep.nunique() for b in benches)
    A = np.full((len(benches), nrep, len(combos)), np.nan)
    for bi, b in enumerate(benches):
        db = d[(d.bench == b) & (d.rep < nrep)]
        piv = db.pivot_table(index='rep', columns='combo', values=metric)
        A[bi] = piv.reindex(columns=combos).values
    return benches, A


def boot(A, stat, B=2000, seed=0):
    """two-level bootstrap (benchmarks, then replicates within benchmark). stat: f(A[bench, rep, ...]) -> array.
    Returns point estimate, lo, hi (95 percentile)."""
    rng = np.random.default_rng(seed)
    nb, nr = A.shape[:2]
    pt = stat(A)
    out = []
    for _ in range(B):
        bi = rng.integers(0, nb, nb)
        ri = rng.integers(0, nr, (nb, nr))
        out.append(stat(A[bi[:, None], ri]))
    out = np.array(out)
    return pt, np.nanpercentile(out, 2.5, 0), np.nanpercentile(out, 97.5, 0)


def stat_mean(A):          # mean over reps then benchmarks
    return np.nanmean(np.nanmean(A, 1), 0)


def make_rel(base_idx):    # geometric mean over benchmarks of ratio of rep-averaged values to baseline
    def f(A):
        m = np.nanmean(A, 1)            # bench x combo
        return np.exp(np.nanmean(np.log(m / m[:, [base_idx]]), 0))
    return f


def make_diff(base_idx):
    def f(A):
        m = np.nanmean(A, 1)
        return np.nanmean(m - m[:, [base_idx]], 0)
    return f
