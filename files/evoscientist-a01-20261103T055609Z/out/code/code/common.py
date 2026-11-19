"""Dataset loaders and the rule registry shared by all experiment scripts."""
import os, warnings, numpy as np, pandas as pd
import core as C
warnings.filterwarnings('ignore')
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
PROC = os.path.join(ROOT, 'data', 'processed')
RES = os.path.join(ROOT, 'results')
os.makedirs(RES, exist_ok=True)
OLL6 = ['IFEval', 'BBH', 'MATH Lvl 5', 'GPQA', 'MUSR', 'MMLU-PRO']

# approximate number of test items per OLL-6 task (sum of leaf n-samples; see data_prep.py / oll_leaf_neval.csv)
def _oll6_n():
    ne = pd.read_csv(os.path.join(PROC, 'oll_leaf_neval.csv'), index_col=0)['n_eval']
    g = lambda pre: float(ne[[k for k in ne.index if k.startswith(pre)]].sum())
    return np.array([g('leaderboard_ifeval'), g('leaderboard_bbh_'), g('leaderboard_math_'),
                     g('leaderboard_gpqa_'), g('leaderboard_musr_'), g('leaderboard_mmlu_pro')])
OLL6_SLOPE = np.array([1.0, 1.3337, 1.0, 1.3333, 1.2593, 1.1111])   # d normalised / d raw (fit in data_prep audit)

def load(name, pool=None):
    """Return dict(S, models, tasks, n, kind). S in [0,1]; rows sorted by descending mean (baseline leaderboard)."""
    if name == 'helm57':
        df = pd.read_csv(os.path.join(PROC, 'helm_mmlu_scores.csv'), index_col=0)
        n = pd.read_csv(os.path.join(PROC, 'helm_mmlu_neval.csv'), index_col=0)['n_eval'].reindex(df.columns).values
    elif name == 'oll6':
        o = pd.read_csv(os.path.join(PROC, 'oll6.csv'))
        o = o.drop_duplicates('fullname', keep='last').set_index('fullname')   # duplicates = precision variants
        df = o[OLL6] / 100.0; n = _oll6_n()
    elif name == 'oll39':
        df = pd.read_csv(os.path.join(PROC, 'oll_leaf_scores.csv'), index_col=0)
        ne = pd.read_csv(os.path.join(PROC, 'oll_leaf_neval.csv'), index_col=0)['n_eval']
        n = ne.reindex(df.columns).values
    else: raise ValueError(name)
    order = df.mean(axis=1).sort_values(ascending=False, kind='stable').index
    df = df.loc[order]
    if pool is not None: df = df.iloc[:pool]
    return dict(S=df.values.astype(float), models=list(df.index), tasks=list(df.columns), n=np.asarray(n, float), kind=name)

# ---------------------------------------------------------------- rule registry
def rule_specs(m):
    t25 = int(0.25 * m); tmed = C.median_t(m)
    return ['mean', 'trim25', 'median', 'max', 'min', 'geomean', 'harmonic', 'borda', 'condorcet', 'plurality']

def scalar_agg(rule, m):
    if rule == 'mean': return lambda S: C.trimmed_mean(S, 0)
    if rule == 'trim25': return lambda S: C.trimmed_mean(S, int(0.25 * m))
    if rule == 'median': return lambda S: C.trimmed_mean(S, C.median_t(m))
    if rule == 'max': return lambda S: C.kth_largest(S, 1)
    if rule == 'min': return lambda S: C.kth_largest(S, m)
    if rule == 'geomean': return lambda S: C.power_mean(S, 0)
    if rule == 'harmonic': return lambda S: C.power_mean(S, -1)
    return None

PM_SHIFT = 0.01   # geometric/harmonic means are evaluated on (score + 0.01) so that zero scores do not annihilate the mean

def min_cost(S, i, rule, ceil=None, kmax=None, p=1, cw=None):
    """Minimal cost for row i to be weakly first under `rule`.
    cost = sum_j cw_j * d_j^p (p in {1,2}; p=2 only for mean/max/min). Returns dict(cost,d,touched,feasible,l1)."""
    n, m = S.shape
    if ceil is None: ceil = np.ones(m)
    zero = dict(cost=0.0, d=np.zeros(m), touched=0, feasible=True, l1=0.0)
    if rule in ('geomean', 'harmonic'):
        S = S + PM_SHIFT; ceil = ceil + PM_SHIFT
    s = S[i]
    f = scalar_agg(rule, m)
    if f is not None:
        a = f(S); tau = float(np.max(np.delete(a, i)))
        if a[i] >= tau - 1e-15: return zero
        if p == 2:
            assert cw is None and rule in ('mean', 'max', 'min')
            if rule == 'mean': r = C.cost_wmean(s, tau, np.ones(m), ceil, 2)
            elif rule == 'max': r = C.cost_kth(s, tau, 1, ceil, 2)
            else: r = C.cost_kth(s, tau, m, ceil, 2)
            if r['feasible']: r['l1'] = float(r['d'].sum())
            return r
        if rule == 'mean':
            if kmax is None: return C.cost_wmean(s, tau, np.ones(m), ceil, 1, cw=cw)
            return C.cost_trimmed_milp(s, tau, 0, ceil, kmax=kmax, cw=cw)
        if rule in ('trim25', 'median'):
            t = int(0.25 * m) if rule == 'trim25' else C.median_t(m)
            return C.cost_trimmed_milp(s, tau, t, ceil, kmax=kmax, cw=cw)
        if rule == 'max': return C.cost_kth(s, tau, 1, ceil, 1, cw=cw)
        if rule == 'min': return C.cost_kth(s, tau, m, ceil, 1, cw=cw)
        if rule == 'geomean': return C.cost_powermean_floor(s, tau, 0, ceil, cw=cw)
        if rule == 'harmonic': return C.cost_powermean_floor(s, tau, -1, ceil, cw=cw)
    if rule == 'borda': return C.cost_borda(S, i, ceil, kmax=kmax, cw=cw)
    if rule == 'condorcet': return C.cost_condorcet(S, i, ceil, kmax=kmax, cw=cw)
    if rule == 'plurality': return C.cost_plurality(S, i, ceil, cw=cw)
    raise ValueError(rule)

def rank_under(S, i, d, rule):
    """Rank (1 = best, ties broken against the target i.e. pessimistic... we use optimistic-with-eps) of row i after applying d."""
    n, m = S.shape
    S2 = S.copy(); S2[i] = C.apply_investment(S[i], d)
    if rule in ('geomean', 'harmonic'): S2 = S2 + PM_SHIFT
    f = scalar_agg(rule, m)
    if f is not None:
        a = f(S2); return 1 + int((np.delete(a, i) > a[i] + 1e-12).sum())
    if rule == 'borda':
        B = C.borda_scores(S2); return 1 + int((np.delete(B, i) > B[i] + 1e-12).sum())
    if rule == 'condorcet':
        # Copeland-style rank: number of models that pairwise-beat i by task majority (i is Condorcet-first iff 0 such)
        wins = (S2[i][None, :] > S2).sum(1); loss = (S2[i][None, :] < S2).sum(1)
        return 1 + int((np.delete(loss > wins, i)).sum())
    if rule == 'plurality':
        W = C.plurality_counts(S2); return 1 + int((np.delete(W, i) > W[i] + 1e-12).sum())

def baseline_rank(S, i, rule):
    return rank_under(S, i, np.zeros(S.shape[1]), rule)

def eq_points(res, m):
    """Mean-equivalent points: total raise in percentage points divided by m."""
    return 100.0 * res['cost'] / m if res['feasible'] else np.nan

DATASETS = {'helm57': dict(pool=None), 'oll6': dict(pool=500), 'oll39': dict(pool=300)}
TARGET_RANKS = list(range(2, 12))     # runner-up .. 11th under the baseline mean ranking
RULES = ['mean', 'trim25', 'median', 'max', 'min', 'geomean', 'harmonic', 'borda', 'condorcet', 'plurality']
