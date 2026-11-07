"""Pairwise-comparison data container, loaders for real files, synthetic stand-ins.

Real-data loaders look for files in ./data. If a file is missing the dataset is
reported UNAVAILABLE; synthetic simulators (clearly labelled, group='SYNTH') are
used as a fallback so the pipeline can be validated. Synthetic and real results
are NEVER pooled downstream.
"""
import os
import csv
import numpy as np

from experiment_config import SYNTH_SPECS


class DatasetUnavailable(Exception):
    """Raised when a real dataset cannot be loaded. Carries the dataset name/reason."""

    def __init__(self, reason, dataset=None):
        self.dataset = dataset
        self.reason = reason
        prefix = '[%s] ' % dataset if dataset else ''
        super().__init__(prefix + str(reason))


class PairData:
    def __init__(self, name, kind, models, ia, ib, y, cluster, synthetic=False, home=None):
        self.name = name
        self.kind = kind
        self.models = list(models)
        self.ia = np.asarray(ia, dtype=np.int64)
        self.ib = np.asarray(ib, dtype=np.int64)
        self.y = np.asarray(y, dtype=np.float64)
        self.cluster = np.asarray(cluster, dtype=np.int64)
        self.synthetic = synthetic
        self.home = (np.zeros(len(self.y)) if home is None
                     else np.asarray(home, dtype=np.float64))
        assert np.all(self.ia != self.ib)
        assert np.all(np.isin(self.y, [0.0, 0.5, 1.0]))
        self.tie_rate = float(np.mean(self.y == 0.5)) if len(self.y) else 0.0

    @property
    def group(self):
        return 'SYNTH' if self.synthetic else 'REAL'

    @property
    def M(self):
        return len(self.models)

    @property
    def N(self):
        return len(self.y)

    def with_labels(self, y, name=None, kind=None):
        """Same records with different labels (used by H3)."""
        return PairData(name or self.name, kind or self.kind, self.models, self.ia,
                        self.ib, y, self.cluster, self.synthetic, self.home)

    def to_counts(self, idx=None, y=None):
        """W[i, j] = (fractional) number of wins of i over j."""
        W = np.zeros((self.M, self.M))
        ia, ib = self.ia, self.ib
        yy = self.y if y is None else y
        if idx is not None:
            ia, ib, yy = ia[idx], ib[idx], yy[idx]
        np.add.at(W, (ia, ib), yy)
        np.add.at(W, (ib, ia), 1.0 - yy)
        return W

    def subset(self, mask_or_idx, min_cmp=0):
        sel = np.asarray(mask_or_idx)
        idx = np.arange(self.N)[sel] if sel.dtype == bool else sel
        ia, ib, y, cl, hm = (self.ia[idx], self.ib[idx], self.y[idx],
                             self.cluster[idx], self.home[idx])
        deg = np.bincount(ia, minlength=self.M) + np.bincount(ib, minlength=self.M)
        keep = np.where(deg >= max(min_cmp, 1))[0]
        remap = -np.ones(self.M, dtype=np.int64)
        remap[keep] = np.arange(len(keep))
        ok = (remap[ia] >= 0) & (remap[ib] >= 0)
        return PairData(self.name, self.kind, [self.models[k] for k in keep],
                        remap[ia[ok]], remap[ib[ok]], y[ok], cl[ok], self.synthetic, hm[ok])

    def cluster_stats(self):
        uc, cnt = np.unique(self.cluster, return_counts=True)
        return dict(n_clusters=int(len(uc)),
                    singleton_frac=float(np.mean(cnt == 1)),
                    mean_cluster_size=float(cnt.mean()))

    def summary(self):
        W = self.to_counts()
        n = W + W.T
        iu = np.triu_indices(self.M, 1)
        nij = n[iu]
        deg = n.sum(1)
        g = np.sort(deg)
        k = len(g)
        gini = float((2 * np.arange(1, k + 1) - k - 1).dot(g) / (k * g.sum() + 1e-12))
        s = dict(N=self.N, M=self.M, tie_rate=round(self.tie_rate, 4),
                 density=round(float(np.mean(nij > 0)), 4),
                 median_n_per_pair=float(np.median(nij[nij > 0])) if np.any(nij > 0) else 0.0,
                 gini_degree=round(gini, 4), synthetic=self.synthetic, group=self.group)
        s.update(self.cluster_stats())
        return s


def subsample_fraction(data, frac, rng, min_cmp=10):
    n = max(int(frac * data.N), 50)
    n = min(n, data.N)
    idx = np.sort(rng.choice(data.N, size=n, replace=False))
    return data.subset(idx, min_cmp=min_cmp)


def thin_to_size(data, target_n, rng, min_cmp=10):
    n = min(int(target_n), data.N)
    idx = np.sort(rng.choice(data.N, size=n, replace=False))
    return data.subset(idx, min_cmp=min_cmp)


# ---------------------------------------------------------------- real loaders
def _need(path, dataset):
    if not os.path.exists(path):
        raise DatasetUnavailable('missing file: ' + path, dataset)
    return path


def load_nba_real(data_dir, min_cmp, year_min=2005, year_max=2015, home_adv=True):
    """One record per game, restricted to a single era.

    nbaallelo.csv has two rows per game (one per team). We keep the row with
    _iscopy == 0 (one orientation per game). 'game_location' is H/A/N from the
    perspective of the row's team, so home = +1 / -1 / 0 is modelled explicitly.
    Participants are keyed by franchise_id (stable across relocations) and the
    window [year_min, year_max] keeps 'strength' approximately a single latent.
    """
    path = _need(os.path.join(data_dir, 'nbaallelo.csv'), 'nba')
    seen, rows = set(), []
    with open(path, newline='') as fh:
        for r in csv.DictReader(fh):
            if r.get('_iscopy', '0') != '0':
                continue
            try:
                yr = int(r['year_id'])
            except (KeyError, ValueError):
                continue
            if yr < year_min or yr > year_max:
                continue
            key = r['gameorder']
            if key in seen:
                continue
            seen.add(key)
            rows.append(r)
    if not rows:
        raise DatasetUnavailable('no rows parsed in era window', 'nba')
    fr_key = 'fran_id' if 'fran_id' in rows[0] else 'team_id'
    opp_key = 'opp_fran' if 'opp_fran' in rows[0] else 'opp_id'
    names = sorted({r[fr_key] for r in rows} | {r[opp_key] for r in rows})
    ix = {n: i for i, n in enumerate(names)}
    ia, ib, y, cl, hm = [], [], [], [], []
    for r in rows:
        a, b = ix[r[fr_key]], ix[r[opp_key]]
        if a == b:
            continue
        ia.append(a)
        ib.append(b)
        y.append(1.0 if r['game_result'] == 'W' else 0.0)
        cl.append(int(r['year_id']))
        loc = r.get('game_location', 'N')
        hm.append((1.0 if loc == 'H' else (-1.0 if loc == 'A' else 0.0)) if home_adv else 0.0)
    d = PairData('nba', 'sports', names, ia, ib, y, cl, home=hm)
    return d.subset(np.arange(d.N), min_cmp=min_cmp)


def load_arena_real(data_dir, min_cmp):
    path = _need(os.path.join(data_dir, 'train.csv'), 'arena')
    rows = []
    with open(path, newline='') as fh:
        for r in csv.DictReader(fh):
            rows.append(r)
    if not rows:
        raise DatasetUnavailable('no rows parsed', 'arena')
    names = sorted({r['model_a'] for r in rows} | {r['model_b'] for r in rows})
    ix = {n: i for i, n in enumerate(names)}
    ia, ib, y, cl = [], [], [], []
    prompt_ids = {}
    for r in rows:
        if r['model_a'] == r['model_b']:
            continue
        ia.append(ix[r['model_a']])
        ib.append(ix[r['model_b']])
        if r['winner_model_a'] == '1':
            y.append(1.0)
        elif r['winner_model_b'] == '1':
            y.append(0.0)
        else:
            y.append(0.5)
        # full prompt string as cluster key (no truncation => no collisions)
        cl.append(prompt_ids.setdefault(r['prompt'], len(prompt_ids)))
    d = PairData('arena', 'crowd', names, ia, ib, y, cl)
    return d.subset(np.arange(d.N), min_cmp=min_cmp)


def load_mtbench_real(data_dir, min_cmp):
    """MT-Bench human judgments. CSV export is supported (stdlib only);
    parquet is not readable without pyarrow and is reported UNAVAILABLE."""
    for fn in ('mt_bench_human_judgments.csv', 'mtbench_human.csv'):
        path = os.path.join(data_dir, fn)
        if os.path.exists(path):
            rows = []
            with open(path, newline='') as fh:
                for r in csv.DictReader(fh):
                    rows.append(r)
            if not rows:
                raise DatasetUnavailable('no rows parsed', 'mtbench_human')
            names = sorted({r['model_a'] for r in rows} | {r['model_b'] for r in rows})
            ix = {n: i for i, n in enumerate(names)}
            ia, ib, y, cl = [], [], [], []
            qid = {}
            for r in rows:
                if r['model_a'] == r['model_b']:
                    continue
                w = r.get('winner', '')
                if w == 'model_a':
                    yy = 1.0
                elif w == 'model_b':
                    yy = 0.0
                else:
                    yy = 0.5
                ia.append(ix[r['model_a']])
                ib.append(ix[r['model_b']])
                y.append(yy)
                cl.append(qid.setdefault(r.get('question_id', str(len(qid))), len(qid)))
            d = PairData('mtbench_human', 'expert', names, ia, ib, y, cl)
            return d.subset(np.arange(d.N), min_cmp=min_cmp)
    raise DatasetUnavailable('MT-Bench CSV not found (parquet needs pyarrow, unavailable)',
                             'mtbench_human')


REAL_LOADERS = {'arena': load_arena_real, 'nba': load_nba_real, 'mtbench_human': load_mtbench_real}


# ---------------------------------------------------------------- synthetic stand-ins
def _latent(M, spread, rng):
    th = np.sort(rng.normal(0, spread, M))[::-1]
    return th - th.mean()


def _sample_pairs(M, N, density, rng):
    """Sample (ia, ib) with ia != ib."""
    pop = np.full(M, 1.0 / M)
    if density < 1.0:
        pop = rng.dirichlet(np.ones(M) * 2.0)
    ia = rng.choice(M, N, p=pop)
    ib = rng.choice(M, N, p=pop)
    bad = ia == ib
    while np.any(bad):
        ib[bad] = rng.choice(M, int(bad.sum()), p=pop)
        bad = ia == ib
    return ia, ib


def synth_comparisons(name, spec, rng, theta=None, cluster_effects=True):
    """Bradley-Terry data with user/prompt clusters (common-mode cluster effects)."""
    M, N = spec['M'], spec['N']
    th = _latent(M, spec['spread'], rng) if theta is None else theta
    nc = spec['n_clusters']
    cl = rng.integers(0, nc, N)
    cl_eff = rng.normal(0, spec['cluster_sd'], (nc, M)) if cluster_effects else np.zeros((nc, M))
    ia, ib = _sample_pairs(M, N, spec['density'], rng)
    s = (th[ia] + cl_eff[cl, ia]) - (th[ib] + cl_eff[cl, ib])
    p = 1.0 / (1.0 + np.exp(-s))
    y = (rng.random(N) < p).astype(np.float64)
    tie = rng.random(N) < spec['tie_rate']
    y[tie] = 0.5
    models = ['%s_m%02d' % (name, i) for i in range(M)]
    return PairData(name, spec['kind'], models, ia, ib, y, cl, synthetic=True), th


def synth_judge_pair(spec, jspec, rng):
    """Aligned human / LLM-judge labels on the same records (SYNTHETIC).

    Judge = human label corrupted by per-model bias b_m (systematic, structured)
    plus iid noise, giving a real structured disagreement vector.
    """
    d, th = synth_comparisons('mtbench', spec, rng)
    M = d.M
    bias = rng.normal(0, jspec['bias_sd'], M)
    s = (th[d.ia] + bias[d.ia]) - (th[d.ib] + bias[d.ib])
    p = 1.0 / (1.0 + np.exp(-s))
    yj = (rng.random(d.N) < p).astype(np.float64)
    yj[d.y == 0.5] = 0.5
    judge = PairData('mtbench_gpt4', 'llm_judge', d.models, d.ia, d.ib, yj, d.cluster, synthetic=True)
    human = PairData('mtbench_human', 'expert', d.models, d.ia, d.ib, d.y, d.cluster, synthetic=True)
    return human, judge, bias


def load_all(hp, rng):
    """Returns (datasets, status). Real and synthetic stand-ins are kept under
    distinct keys (synthetic ones suffixed '_SYNTH') and carry synthetic=True."""
    out, status = {}, {}
    synth_key = {'arena': 'arena_synth', 'mtbench_human': 'mtbench_human', 'nba': 'nba_synth'}
    for nm in ['arena', 'mtbench_human', 'nba']:
        real_ok = False
        if hp['use_real_data']:
            try:
                if nm == 'nba':
                    out[nm] = load_nba_real(hp['data_dir'], hp['min_comparisons_per_model'],
                                            hp['nba_year_min'], hp['nba_year_max'],
                                            hp['nba_home_advantage'])
                else:
                    out[nm] = REAL_LOADERS[nm](hp['data_dir'], hp['min_comparisons_per_model'])
                status[nm] = 'REAL'
                real_ok = True
            except DatasetUnavailable as e:
                status[nm] = 'UNAVAILABLE(%s)' % e
            except Exception as e:  # malformed file etc.
                status[nm] = 'UNAVAILABLE(load error %s)' % e
        if not real_ok:
            d, _ = synth_comparisons(nm + '_SYNTH', SYNTH_SPECS[synth_key[nm]], rng)
            out[nm + '_SYNTH'] = d
            status[nm + '_SYNTH'] = 'SYNTHETIC_STANDIN'
    return out, status