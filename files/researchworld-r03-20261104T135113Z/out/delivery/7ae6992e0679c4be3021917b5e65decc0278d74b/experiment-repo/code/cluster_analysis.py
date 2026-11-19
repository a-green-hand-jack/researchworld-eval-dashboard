"""Dependence-robust uncertainty for the main contrasts (review items 1-3).

For a primary run B_<data> (and its floor F_<data>) this script re-computes with a CLUSTER bootstrap over organisations ('org') and over strict
families ('family', lib.family_labels) in addition to the model bootstrap used elsewhere:
  cluster_paired_<run>.csv : selector A minus selector B in nMSE (krr, fa; every k): informed selectors vs random and `central` vs gv_fa / dopt;
                             columns diff, lo, hi per `cluster` in {model, org, family}
  cluster_kstar_<run>.csv  : k*(g) of the pre-fixed criterion (G_own, g in {0.8, 0.9}): by CI lower bound under each clustering, bootstrap
                             distribution of the point-estimate k* (median, 2.5%, 97.5%; NaN share = never reached) and k* per repetition
  family_stats_<run>.csv   : clusters, size of the largest cluster, and the share of held-out models whose organisation / family has >= 2 members
                             among the training models of its fold (random folds: recomputed from the run's seeds)
  cluster_curves_<run>.csv : nMSE of random / gv_fa / dopt / central with the 95% interval under each clustering (Fig. 1 intervals)
  cluster_gk_<run>.csv     : G(k) with its CI lower bound at every k, both floors (G_own, G_best), each clustering (so that k* can be drawn)
  cluster_perrep_<run>.csv : nMSE per repetition (= target draw) of random / gv_fa / dopt at k = 2, 4, 8, 16
  group_counts.csv         : (separate entry, `python cluster_analysis.py --groups`) share of held-out models whose organisation / strict family still has >= 2 members
                             among the training models, for the group-split runs
HELM-MMLU has no organisation table: 'org' = first word of the model name and 'family' = name without the parenthesised size (both are proxies).
usage: python cluster_analysis.py <data> [<data> ...]       e.g. mteb_dense56 mteb_dense
"""
import os, sys, json
import numpy as np, pandas as pd
import lib
from analysis_lib import per_model, boot_metric, paired_diff, paired_diff_cl, gap_closed
from run_cv import make_folds

HERE = os.path.dirname(__file__)
RAW = os.path.join(HERE, '..', 'results', 'raw'); OUT = os.path.join(HERE, '..', 'results', 'summary')
SEL = ['gv_fa', 'dopt', 'gv_emp', 'central', 'kcenter', 'popular', 'lev', 'qr', 'rawvar']
METH = ['krr', 'fa']
KS = [1, 2, 3, 4, 5, 6, 8, 10, 12, 16, 20, 24, 32]


def kstar_from(G, thr, col):
    ok = G[G[col] >= thr]
    return int(ok.k.min()) if len(ok) else np.nan


def cluster_labels(data):
    z = np.load(os.path.join(HERE, '..', 'data', 'matrices', data + '.npz'), allow_pickle=True)
    ids = [str(m) for m in z['models']]
    mp = os.path.join(HERE, '..', 'data', 'matrices', data + '_models.csv')
    if not os.path.exists(mp):      # HELM-MMLU: name-based proxies
        import re
        stem = [re.sub(r'\s*\(.*\)\s*$', '', m).strip() for m in ids]
        return ids, np.array([s.split()[0] for s in stem]), np.array(stem)
    meta = pd.read_csv(mp, index_col=0)
    org = meta['org'].fillna('NA').astype(str).values
    org = np.array([f'single_{i}' if o in ('NA', 'Removed', '', 'nan') else o for i, o in enumerate(org)])
    fam = lib.family_labels(meta['org'].fillna('NA').astype(str).values, meta['adapted_from'].values, meta['name'].values)
    return ids, org, fam


def run(data, n_boot=1000):
    ids, org, fam = cluster_labels(data)
    lab = {'org': dict(enumerate(org)), 'family': dict(enumerate(fam))}
    name = 'B_' + data
    d = pd.read_parquet(os.path.join(RAW, name + '.parquet'))
    df = pd.read_parquet(os.path.join(RAW, 'F_' + data + '.parquet'))
    g = per_model(d); gf = per_model(df)
    labels = {'model': {m: m for m in g.model.unique()}, **{c: lab[c] for c in lab}}
    g = g[g.method.isin(METH + ['mean']) & g.k.isin(KS)]
    # ---- paired contrasts
    pairs = [(s, 'random') for s in SEL if s in set(g.selector)] + [('central', 'gv_fa'), ('central', 'dopt'), ('gv_fa', 'dopt')]
    rows = []
    for a, b in pairs:
        if a not in set(g.selector) or b not in set(g.selector):
            continue
        for cl in ('model', 'org', 'family'):
            if cl == 'model':
                p = paired_diff(g[g.method.isin(METH)], a, b, n_boot=n_boot)
            else:
                p = paired_diff_cl(g[g.method.isin(METH)], a, b, labels[cl], n_boot=n_boot)
            p.insert(0, 'cluster', cl); p.insert(0, 'b', b); p.insert(0, 'a', a)
            rows.append(p)
    pd.concat(rows).to_csv(os.path.join(OUT, f'cluster_paired_{name}.csv'), index=False)
    # ---- curves with cluster intervals
    gg_ = g[g.selector.isin(['random', 'gv_fa', 'dopt', 'central']) | (g.method == 'mean')]
    cr = []
    for cl in ('model', 'org', 'family'):
        b = boot_metric(gg_, ['selector', 'method', 'k'], n_boot=n_boot, labels=None if cl == 'model' else labels[cl])
        b.insert(0, 'cluster', cl); cr.append(b)
    pd.concat(cr).rename(columns={'est': 'nmse', 'lo': 'nmse_lo', 'hi': 'nmse_hi'}).to_csv(os.path.join(OUT, f'cluster_curves_{name}.csv'), index=False)
    # ---- nMSE per repetition
    pr = []
    for rep in sorted(d.rep.unique()):
        gr = per_model(d[d.rep == rep]); gr = gr[gr.method.isin(METH) & gr.selector.isin(['random', 'gv_fa', 'dopt']) & gr.k.isin([2, 4, 8, 16])]
        b = boot_metric(gr, ['selector', 'method', 'k'], n_boot=200); b.insert(0, 'rep', rep); pr.append(b)
    pd.concat(pr).rename(columns={'est': 'nmse', 'lo': 'nmse_lo', 'hi': 'nmse_hi'}).to_csv(os.path.join(OUT, f'cluster_perrep_{name}.csv'), index=False)
    # ---- k*
    krows = []; grows = []
    for cl in ('model', 'org', 'family'):
        G, fl, boots = gap_closed(g, gf, n_boot=n_boot, labels=None if cl == 'model' else labels[cl], return_boot=True)
        for (s, m), sub in G.groupby(['selector', 'method']):
            if s not in ('random', 'gv_fa', 'dopt', 'central') or m not in METH:
                continue
            sub = sub.sort_values('k')
            grows.append(sub.assign(cluster=cl))
            for gg in (0.8, 0.9):
                ks_ = sub.k.values
                kb = []
                for b in range(n_boot):
                    Gb = np.array([boots[(s, m, k, 'own')][b] for k in ks_])
                    ok = np.where(Gb >= gg)[0]
                    kb.append(ks_[ok[0]] if len(ok) else np.nan)
                kb = np.array(kb, float)
                krows.append(dict(cluster=cl, selector=s, method=m, g=gg, kstar_ci=kstar_from(sub, gg, 'G_own_lo'), kstar_point=kstar_from(sub, gg, 'G_own'),
                                  boot_median=np.nanmedian(kb) if (~np.isnan(kb)).any() else np.nan,
                                  boot_lo=np.nanpercentile(kb, 2.5) if (~np.isnan(kb)).any() else np.nan,
                                  boot_hi=np.nanpercentile(kb, 97.5) if (~np.isnan(kb)).any() else np.nan, boot_never=float(np.isnan(kb).mean())))
    pd.concat(grows).to_csv(os.path.join(OUT, f'cluster_gk_{name}.csv'), index=False)
    # per repetition (point estimates, same folds / targets per rep)
    for rep in sorted(d.rep.unique()):
        gr = per_model(d[d.rep == rep]); gfr = per_model(df[df.rep == rep])
        Gr, _ = gap_closed(gr[gr.method.isin(METH + ['mean']) & gr.k.isin(KS)], gfr, n_boot=20)
        for (s, m), sub in Gr.groupby(['selector', 'method']):
            if s not in ('random', 'gv_fa', 'dopt', 'central') or m not in METH:
                continue
            sub = sub.sort_values('k')
            for gg in (0.8, 0.9):
                krows.append(dict(cluster=f'rep{rep}', selector=s, method=m, g=gg, kstar_point=kstar_from(sub, gg, 'G_own')))
    pd.DataFrame(krows).to_csv(os.path.join(OUT, f'cluster_kstar_{name}.csv'), index=False)
    # ---- family statistics of the random 10-fold splits and of the group splits
    cfg = json.load(open(os.path.join(RAW, name + '.json')))
    st = [dict(kind='matrix', n_models=len(ids), n_org=len(set(org)), n_family=len(set(fam)), largest_org=pd.Series(org).value_counts().iloc[0],
               largest_family=pd.Series(fam).value_counts().iloc[0])]
    shares = {'org': [], 'family': []}
    for rep in range(cfg['reps']):
        rng = np.random.default_rng(cfg['seed'] * 1000 + rep)
        for tr, te in make_folds(cfg['split'], len(ids), cfg['K'], rng):
            for c, lb in (('org', org), ('family', fam)):
                trl = set(lb[tr]); cnt = pd.Series(lb[tr]).value_counts()
                shares[c] += [bool(cnt.get(lb[i], 0) >= 2) for i in te]
    for c in shares:
        st.append(dict(kind=f'random_folds_{c}', share_heldout_with_ge2_train_members=float(np.mean(shares[c])), n_heldout=len(shares[c])))
    pd.DataFrame(st).to_csv(os.path.join(OUT, f'family_stats_{name}.csv'), index=False)
    print(data, 'ok')


def group_counts():
    rows = []
    for run_, data in (('d56_group', 'mteb_dense56'), ('d56_famgroup', 'mteb_dense56'), ('d275_group', 'mteb_dense'), ('d275_famgroup', 'mteb_dense')):
        ids, org, fam = cluster_labels(data)
        cfg = json.load(open(os.path.join(RAW, run_ + '.json')))
        meta = pd.read_csv(os.path.join(HERE, '..', 'data', 'matrices', data + '_models.csv'), index_col=0)
        gl = fam if cfg['group_col'] == 'family' else np.array([f'single_{i}' if g in ('NA', 'Removed', '', 'nan') else g for i, g in enumerate(meta[cfg['group_col']].fillna('NA').astype(str).values)])
        sh = {'org': [], 'family': []}
        for rep in range(cfg['reps']):
            rng = np.random.default_rng(cfg['seed'] * 1000 + rep)
            for tr, te in make_folds('group', len(ids), cfg['K'], rng, gl):
                for c, lb in (('org', org), ('family', fam)):
                    cnt = pd.Series(lb[tr]).value_counts()
                    sh[c] += [bool(cnt.get(lb[i], 0) >= 2) for i in te]
        rows.append(dict(run=run_, group_col=cfg['group_col'], n_heldout=len(sh['org']), share_org_ge2_in_train=np.mean(sh['org']), share_family_ge2_in_train=np.mean(sh['family'])))
    pd.DataFrame(rows).to_csv(os.path.join(OUT, 'group_counts.csv'), index=False)
    print(pd.DataFrame(rows).round(3).to_string())


if __name__ == '__main__':
    if sys.argv[1:] == ['--groups']:
        group_counts()
    else:
        for n in sys.argv[1:]:
            run(n)
