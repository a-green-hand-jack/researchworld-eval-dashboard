"""Dataset descriptors for Table 1 / scree plot (claim C0, C5): size, observed fraction, spectrum of the standardised matrix
(mean-imputed after per-benchmark standardisation; participation-ratio effective rank, components for 80/90% variance), FA rank chosen by
hold-out CV (median over folds of the B_* run) and, when available, the measurement-noise reference.
usage: python describe_data.py  -> results/summary/datasets.csv, results/summary/scree.csv
"""
import os, glob
import numpy as np, pandas as pd

HERE = os.path.dirname(__file__)
MAT = os.path.join(HERE, '..', 'data', 'matrices'); RAW = os.path.join(HERE, '..', 'results', 'raw'); OUT = os.path.join(HERE, '..', 'results', 'summary')

rows, scree = [], []
for f in sorted(glob.glob(os.path.join(MAT, '*.npz'))):
    name = os.path.basename(f)[:-4]
    if name.endswith('_truth'):
        continue
    Y = np.load(f, allow_pickle=True)['Y']
    M, N = Y.shape
    obs = ~np.isnan(Y)
    Z = (Y - np.nanmean(Y, 0)) / (np.nanstd(Y, 0) + 1e-12)
    Z = np.where(obs, Z, 0.0)
    ev = np.linalg.eigvalsh(np.corrcoef(Z.T) if N > 1 else np.eye(1))[::-1]
    ev = np.clip(ev, 0, None); sh = ev / ev.sum()
    cs = np.cumsum(sh)
    r_fa = np.nan
    fo = os.path.join(RAW, f'B_{name}_folds.parquet')
    if os.path.exists(fo):
        r_fa = float(np.median(pd.read_parquet(fo)['rank']))
    nz = None
    nf = os.path.join(HERE, '..', 'data', f'noise_cells_{name}.csv')
    cov_noise = nmse_noise = np.nan
    if os.path.exists(nf):
        nd = pd.read_csv(nf)
        sdj = pd.Series(np.nanstd(Y, 0), index=np.load(f, allow_pickle=True)['benches'].astype(str))
        nd['z2'] = nd.var_cell / (nd.task.map(sdj) ** 2)
        cov_noise = len(nd) / obs.sum(); nmse_noise = nd.z2.mean()
    rows.append(dict(dataset=name, M=M, N=N, observed_frac=obs.mean(), models_per_bench_median=np.median(obs.sum(0)), benches_per_model_median=np.median(obs.sum(1)),
                     share_pc1=sh[0], pc_for_80=int(np.searchsorted(cs, .8) + 1), pc_for_90=int(np.searchsorted(cs, .9) + 1),
                     eff_rank_pr=ev.sum() ** 2 / (ev ** 2).sum(), fa_rank_cv_median=r_fa,
                     noise_cell_coverage=cov_noise, noise_nmse_z_covered=nmse_noise))
    for i in range(min(N, 30)):
        scree.append((name, i + 1, sh[i], cs[i]))
pd.DataFrame(rows).to_csv(os.path.join(OUT, 'datasets.csv'), index=False)
pd.DataFrame(scree, columns=['dataset', 'component', 'var_share', 'cum_share']).to_csv(os.path.join(OUT, 'scree.csv'), index=False)
print(pd.DataFrame(rows).round(3).to_string())
