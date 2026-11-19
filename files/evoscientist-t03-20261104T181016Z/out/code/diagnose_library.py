"""Read-only, local-only numerical diagnosis of stored official KernelExplainer runs.

Run: python /work/diagnose_library.py
Writes diagnostic artifacts only; never rewrites results/, analysis/, or estimator code.
"""
import os
for _k in ('OMP_NUM_THREADS', 'OPENBLAS_NUM_THREADS', 'MKL_NUM_THREADS', 'NUMEXPR_NUM_THREADS'):
    os.environ[_k] = '1'

import argparse
import ast
from collections import Counter
from fractions import Fraction
import hashlib
import inspect
import json
from pathlib import Path
import sys
import warnings

import numpy as np
import pandas as pd
from scipy.linalg import null_space
import scipy
import shap
import sklearn

from diagnostics import load_cache
from run_experiments import rng_for
from shap_audit import bits, exact_phi, full_kernel_phi, maskint, metrics

ROOT = Path(__file__).resolve().parent
ART = ROOT / 'artifacts'
HUGE = 1e6  # Descriptive threshold on the existing normalized L1 error, not a new outcome.
RCOND = 1e-10


def snapshot():
    files = [f for directory in ('results', 'analysis')
             for f in (ROOT / directory).rglob('*') if f.is_file()]
    files += [ROOT / f for f in ('diagnostics.py', 'shap_audit.py',
                                'run_experiments.py', 'analyze_results.py',
                                'requirements-lock.txt', 'research_request.md')]
    return {str(f.relative_to(ROOT)): hashlib.sha256(f.read_bytes()).hexdigest()
            for f in sorted(files)}


def native(x):
    if isinstance(x, np.ndarray):
        return x.tolist()
    if isinstance(x, np.generic):
        return x.item()
    if isinstance(x, Path):
        return str(x)
    raise TypeError(type(x).__name__)


def rational_rank(x):
    """Exact rank for the small integer eliminated-coordinate design."""
    a = [[Fraction(int(v)) for v in row] for row in x]
    row = 0
    for col in range(x.shape[1]):
        pivot = next((i for i in range(row, len(a)) if a[i][col]), None)
        if pivot is None:
            continue
        a[row], a[pivot] = a[pivot], a[row]
        val = a[row][col]
        a[row] = [v / val for v in a[row]]
        for i in range(row + 1, len(a)):
            val = a[i][col]
            if val:
                a[i] = [v - val * w for v, w in zip(a[i], a[row])]
        row += 1
        if row == len(a):
            break
    return row


def spectrum(x):
    sv = np.linalg.svd(x, compute_uv=False)
    rank = int(np.linalg.matrix_rank(x))
    return dict(shape=list(x.shape), rank=rank, singular_values=sv,
                condition=float(np.linalg.cond(x)))


def phi_stats(phi, ref, z, weights, values, f0, delta):
    residual = z @ phi - (values - f0)
    return dict(phi=phi, error=float(metrics(phi, ref)['error'][0]),
                max_abs=float(np.abs(phi).max()),
                efficiency_residual=float(abs(phi.sum() - delta)),
                weighted_residual_norm=float(np.linalg.norm(np.sqrt(weights) * residual)),
                finite=bool(np.isfinite(phi).all()))


def run_case(row, matched_seed=None):
    ds, model = row['dataset'], row['model']
    slot, p, rep = int(row['slot']), int(row['p']), int(row['rep'])
    mode = row['mode']
    library_path = ROOT / 'results/library' / f'{ds}_{model}_11_{slot:02d}.npz'
    with np.load(library_path) as raw:
        records = json.loads(str(raw['records']))
        idx = next(i for i, r in enumerate(records)
                   if (r['mode'], r['p'], r['rep']) == (mode, p, rep))
        stored_phi = raw['attributions'][idx].copy()
        stored_ref = raw['reference'].copy()
        library_keys, library_values = raw['cache_masks'].copy(), raw['cache_values'].copy()
    c, ref, qualified = load_cache(ds, model, slot)
    d = c.d
    assert d <= 10, 'This diagnosis requires an exact finite-game reference.'
    all_masks = np.arange(1 << d, dtype=np.uint32)
    assert np.array_equal(c.keys, all_masks)
    assert np.array_equal(library_keys, all_masks)
    assert np.array_equal(c.vals, library_values)
    assert np.array_equal(ref, stored_ref)
    fresh_values = c.game.evaluate(all_masks)
    assert np.allclose(c.vals, fresh_values, rtol=0, atol=1e-12)
    recomputed_ref = exact_phi(c.vals, d)
    assert np.allclose(ref, recomputed_ref, rtol=0, atol=1e-12)
    assert np.allclose(ref, full_kernel_phi(c.vals, d), rtol=0, atol=1e-12)
    trace = []
    adapter_masks, adapter_values = [], []

    def fun(z):
        z = np.asarray(z)
        assert z.ndim == 2 and z.shape[1] == d
        assert np.isfinite(z).all() and np.all((z == 0) | (z == 1))
        masks = maskint(z)
        assert np.array_equal(bits(masks, d), z)
        values = c(masks)
        adapter_masks.extend(masks.tolist())
        adapter_values.extend(values.tolist())
        return values

    code = shap.KernelExplainer.solve.__code__

    def capture(frame, event, arg):
        if event == 'return' and frame.f_code is code:
            trace.append({k: np.array(frame.f_locals[k], copy=True)
                          for k in ('nonzero_inds', 'X', 'y', 'WX', 'w', 'phi')})

    seed = int(rng_for(ds, model, 11, slot, 5, mode == 'no_l1', p, rep)
               .integers(0, 2**31 - 1)) if matched_seed is None else int(matched_seed)
    np.random.seed(seed)
    old_profile = sys.getprofile()
    with warnings.catch_warnings(record=True) as ww:
        warnings.simplefilter('always')
        sys.setprofile(capture)
        try:
            explainer = shap.KernelExplainer(fun, np.zeros((1, d)), link='identity')
            kw = {} if mode == 'default' else dict(l1_reg=0)
            phi = np.asarray(explainer.shap_values(np.ones((1, d)),
                             nsamples=2 * (d - 1) * p, silent=True, **kw)).reshape(d)
        finally:
            sys.setprofile(old_profile)
    assert len(trace) == 1
    loc = trace[0]
    z = explainer.maskMatrix[:explainer.nsamplesAdded].copy()
    weights = explainer.kernelWeights[:explainer.nsamplesAdded].copy()
    values = np.asarray(explainer.ey)[:explainer.nsamplesAdded, 0].copy()
    masks = maskint(z)
    f0, fx = float(explainer.fnull[0]), float(explainer.fx[0])
    delta = fx - f0
    assert explainer.M == d and explainer.N == 1
    assert np.array_equal(explainer.varyingInds, np.arange(d))
    assert np.isfinite(z).all() and np.all((z == 0) | (z == 1))
    assert np.array_equal(np.asarray(adapter_masks, dtype=np.uint32),
                          np.concatenate(([0, (1 << d) - 1], masks)))
    assert np.array_equal(np.asarray(adapter_values), c.vals[np.asarray(adapter_masks)])
    assert np.array_equal(values, c.vals[masks])
    assert f0 == c.vals[0] and fx == c.vals[-1]
    assert np.isfinite(weights).all() and (weights > 0).all()
    selected = loc['nonzero_inds'].astype(int)
    x, y, wx = loc['X'], loc['y'], loc['WX']
    assert np.array_equal(x, z[:, selected[:-1]] - z[:, selected[-1], None])
    assert np.array_equal(y, values - f0 - z[:, selected[-1]] * delta)
    normal, rhs = x.T @ wx, wx.T @ y
    aw, bw = np.sqrt(weights)[:, None] * x, np.sqrt(weights) * y
    normal_raised = False
    try:
        w_normal = np.linalg.solve(normal, rhs)
        normal_difference = float(np.max(np.abs(w_normal - loc['w'])))
    except np.linalg.LinAlgError:
        normal_raised, normal_difference = True, None
    w_svd = np.linalg.lstsq(aw, bw, rcond=RCOND)[0]
    w_svd_default = np.linalg.lstsq(aw, bw, rcond=None)[0]
    eliminated_phi = np.zeros(d)
    eliminated_phi[selected[:-1]] = w_svd
    eliminated_phi[selected[-1]] = delta - sum(w_svd)
    u = null_space(np.ones((1, d)))
    base = np.full(d, delta / d)
    constrained_a = np.sqrt(weights)[:, None] * (z @ u)
    constrained_b = np.sqrt(weights) * (values - f0 - z @ base)
    coef, _, rank, sv = np.linalg.lstsq(constrained_a, constrained_b, rcond=RCOND)
    constrained_phi = base + u @ coef
    same_seed = matched_seed is None
    result = dict(dataset=ds, model=model, slot=slot, p=p, mode=mode, rep=rep,
                  d=d, rng_seed=seed, matched_seed_control=not same_seed,
                  requested_interior=2 * (d - 1) * p,
                  actual_interior=int(explainer.nsamplesAdded),
                  adapter_calls=len(adapter_masks), adapter_unique=len(set(adapter_masks)),
                  library_path=library_path, stored_index=idx, qualified=bool(qualified),
                  stored_error=float(records[idx]['error']),
                  bitwise_stored_match=bool(np.array_equal(phi, stored_phi)) if same_seed else None,
                  max_stored_phi_difference=float(np.max(np.abs(phi - stored_phi))) if same_seed else None,
                  warning_match=([str(w.message) for w in ww] == records[idx]['warnings']) if same_seed else None,
                  warnings=[dict(category=w.category.__name__, message=str(w.message)) for w in ww],
                  l1_reg=explainer.l1_reg, selected_indices=selected,
                  eliminated_index=int(selected[-1]), varying_indices=explainer.varyingInds,
                  f0=f0, fx=fx, delta=delta, reference=ref,
                  cache_complete=True, cache_library_main_bitwise_equal=True,
                  model_cache_max_difference=float(np.max(np.abs(fresh_values - c.vals))),
                  reference_recomputed_max_difference=float(np.max(np.abs(ref - recomputed_ref))),
                  binary_adapter_roundtrip_exact=True, adapter_values_cache_exact=True,
                  library_ey_cache_exact=True, endpoints_cache_exact=True,
                  adapter_extra_model_rows=int(c.game.actual_rows - len(all_masks) * c.game.b),
                  game_min=float(c.vals.min()), game_max=float(c.vals.max()),
                  masks=masks, mask_matrix=z, weights=weights, weight_sum=float(weights.sum()),
                  identical_mask_columns=[(i, j) for i in range(d) for j in range(i + 1, d)
                                          if np.array_equal(z[:, i], z[:, j])],
                  lstsq_default_rcond_w_max_difference=float(np.max(np.abs(w_svd_default - w_svd))),
                  weight_min=float(weights.min()), weight_max=float(weights.max()),
                  values=values, selected_design=spectrum(aw), exact_integer_design_rank=rational_rank(x),
                  normal=spectrum(normal), normal_solve_raised=normal_raised,
                  normal_recomputed_w_max_difference=normal_difference,
                  constrained_design=spectrum(constrained_a), constrained_rank=int(rank),
                  constrained_singular_values=sv,
                  library=phi_stats(phi, ref, z, weights, values, f0, delta),
                  eliminated_svd=phi_stats(eliminated_phi, ref, z, weights, values, f0, delta),
                  constrained_svd=phi_stats(constrained_phi, ref, z, weights, values, f0, delta),
                  normal_matrix=normal, normal_rhs=rhs)
    if same_seed:
        assert result['bitwise_stored_match'], 'Stored output did not reproduce bitwise.'
        assert result['warning_match'], 'Stored warnings did not reproduce.'
    return result


def warning_counts(records):
    out = []
    for (mode, p), group in records.groupby(['mode', 'p'], sort=True):
        messages = [m for ws in group.warning_list for m in ws]
        out.append(dict(mode=mode, p=int(p), n=len(group),
                        huge=int((group.error > HUGE).sum()),
                        warning_records=int(group.warning_list.map(bool).sum()),
                        warning_events=len(messages),
                        singular_records=int(group.warning_list.map(lambda ws: any('equation is singular' in m for m in ws)).sum()),
                        degenerate_records=int(group.warning_list.map(lambda ws: any('active set degenerate' in m for m in ws)).sum()),
                        max_error=float(group.error.max())))
    return out


def markdown_table(rows, columns):
    return '\n'.join(['| ' + ' | '.join(columns) + ' |',
                      '| ' + ' | '.join(['---'] * len(columns)) + ' |'] +
                     ['| ' + ' | '.join(str(row[c]) for c in columns) + ' |' for row in rows])


def write_report(data):
    primary = data['reproductions'][0]
    f = lambda x: f'{x:.9g}'
    table = []
    for r in data['reproductions'] + data['controls']:
        table.append(dict(case=f"{r['dataset']}/{r['model']}/s{r['slot']}/r{r['rep']}" +
                          (' matched seed' if r['matched_seed_control'] else ''),
                          mode=r['mode'], P=r['p'], seed=r['rng_seed'],
                          rank=f"{r['exact_integer_design_rank']}/{r['selected_design']['shape'][1]}",
                          cond_normal=f(r['normal']['condition']),
                          library_error=f(r['library']['error']),
                          same_design_SVD_error=f(r['constrained_svd']['error']),
                          warnings=len(r['warnings'])))
    zrows = [dict(mask=int(m), binary=''.join(str(int(b)) for b in z),
                  weight=f(w), value=f(v)) for m, z, w, v in
             zip(primary['masks'], primary['mask_matrix'], primary['weights'], primary['values'])]
    phirows = [dict(j=j, reference=f(a), library=f(b), eliminated_SVD=f(c), constrained_SVD=f(d))
               for j, (a, b, c, d) in enumerate(zip(primary['reference'], primary['library']['phi'],
                   primary['eliminated_svd']['phi'], primary['constrained_svd']['phi']))]
    control = data['controls'][0]
    text = f"""# Official KernelExplainer low-budget numerical diagnosis

## Scope and reproducibility

Diagnostic only: **no experimental design, reported library output, main result, or estimator source was changed**. No network, web, literature, or topic discovery was used. Read the request, adapter, runner, estimator, existing CSV/NPZ records, and installed SHAP source only. Followed experiment-craft's five-step diagnostic. Huge means the existing normalized L1 error `> {HUGE:g}`; thresholds from 100 through 1e12 select the same four rows. Error is `sum(abs(phi-reference))/max(sum(abs(reference)),0.02)`, not absolute attribution magnitude.

Exact command (single-thread CPU; no arguments or inputs to tune):

```sh
python /work/diagnose_library.py
```

Environment: Python {data['python']}; SHAP {shap.__version__}; NumPy {np.__version__}; SciPy {scipy.__version__}; scikit-learn {sklearn.__version__}. The helper asserts bitwise stored-output reproduction for all four huge cases and the two stored controls, warning equality, cache/reference identities, and unchanged protected-file SHA256 hashes. Full precision arrays, singular values, weights, warnings, source excerpts, and hashes are in `artifacts/library_numerics_diagnosis.json`. Local source: `{data['source_path']}`, SHA256 `{data['source_sha256']}`. Results can depend on numerical-library/platform rounding; exact reproduction assertions intentionally fail on drift instead of silently replacing a run.

## 1. Collect actual failure cases

All {data['raw_records']} CSV rows were checked against corresponding original NPZ JSON records (same ordered run keys, errors and warning lists). No rows were discarded. Only four pass the descriptive huge threshold; all four were separately reproduced without saving over any result.

{markdown_table(data['counts'], ['mode', 'p', 'n', 'huge', 'warning_records', 'warning_events', 'singular_records', 'degenerate_records', 'max_error'])}

Warning-record counts count runs with >=1 warning; event counts include repeated warnings. Singular and degenerate categories are text classifications of the stored warning messages, not inferred failures. **All four huge-error records have no warnings.** No inference that absence of a warning means a well-conditioned solve.

Dataset breakdown (all raw records, not just reproduced cases):

{markdown_table(data['dataset_counts'], ['dataset', 'mode', 'p', 'n', 'huge', 'warning_records', 'warning_events'])}

First huge run in existing CSV order: `{primary['library_path']}`, attributions index {primary['stored_index']}; ACS/HGB seed 11, slot 0, P=1, no_l1, repeat 12. The seed is produced exactly by `int(rng_for('acs','hgb',11,0,5,True,1,12).integers(0,2**31-1)) = {primary['rng_seed']}`. It requests 18 interior samples for 10 players; the analogous Pima cases request 14 for 8 players.

## 2. Find a working version (diagnostic controls only)

The original default and P=16 runs for the first point/repeat reproduce bitwise. A same-seed default control also runs on **identical masks, weights and finite-game values** to the failing no_l1 case; only `l1_reg` changes. It selects `{control['selected_indices']}` and yields rank {control['exact_integer_design_rank']}/{control['selected_design']['shape'][1]}. The two stored modes use different `rng_for` method streams, so their reported errors are not treated as a paired seed comparison. Default `num_features(10)` is feature selection, not necessarily shrinkage; it may select fewer than ten features on a degenerate design.

{markdown_table(table, ['case', 'mode', 'P', 'seed', 'rank', 'cond_normal', 'library_error', 'same_design_SVD_error', 'warnings'])}

SVD columns are **new diagnosis-only reconstructions**, not corrected reported library outputs. They remain nonzero-error estimates, and rank deficiency still entails non-identifiability.

## 3. Bridge the gap: verify the adapter and expose the actual system

For every reproduced case, assertions confirmed:
- Inputs to the adapter are finite, exactly binary, shape `(n,d)`, with a lossless integer-mask round trip. All `d` players vary; one zero background row and the all-one query are the intended finite-game adapter, not raw model-feature inputs.
- Library and main caches contain the entire game (`2**d` sorted masks), with **bitwise equal cache values**. The adapter's outputs and SHAP's `ey` equal the cached values exactly. No uncached model rows are evaluated during the explanation.
- Independent evaluation of the actual frozen model on all finite-game masks differs from the cache by at most {max(r['model_cache_max_difference'] for r in data['reproductions']):.9g}. Exact Shapley references recomputed by exhaustive marginal sums equal the stored references; full weighted constrained-kernel references agree to 1e-12.
- For the first case, `v(empty)={primary['f0']:.17g}`, `v(full)={primary['fx']:.17g}`, delta={primary['delta']:.17g}; the entire game's value range is [{primary['game_min']:.9g}, {primary['game_max']:.9g}]. Both endpoint/library/cache comparisons are exact.

First case actual design: {primary['actual_interior']} unique interior rows; {primary['adapter_calls']} adapter rows including two endpoints. Selected indices (zero-based) `{primary['selected_indices']}`; eliminated feature index **{primary['eliminated_index']}**. These indices were captured from the original installed `solve` frame at return using Python profiling, without changing solver arithmetic. No warnings: `{primary['warnings']}`. **Identical sampled column pair: `{primary['identical_mask_columns']}`.** Thus features 4 and 6 cannot be distinguished by these samples: their contrast is an exact null direction compatible with the efficiency constraint. The huge output assigns them approximately +1.377e15 and -1.377e15. The same-seed default removes feature 6 and its selected normal system has condition estimate {control['normal']['condition']:.9g}.

Let `Z` be the actual library mask matrix and `w` its actual kernel weights. SHAP eliminates the final selected feature `j`, using `X = Z[:,selected[:-1]] - Z[:,j,None]`, `y = v - v0 - Z[:,j]*delta`, and solves `(X.T @ W @ X) beta = (W*X).T @ y`.

- `sqrt(W) X`: shape {primary['selected_design']['shape']}; numerical rank {primary['selected_design']['rank']}; **exact rational rank of integer X = {primary['exact_integer_design_rank']} < {primary['selected_design']['shape'][1]}**; floating condition estimate {primary['selected_design']['condition']:.9g} (mathematically singular). Its singular values are `{np.array2string(primary['selected_design']['singular_values'], precision=9, max_line_width=1000)}`.
- `X.T W X`: numerical rank {primary['normal']['rank']}; floating condition estimate {primary['normal']['condition']:.9g}. Singular-design condition estimates are finite floating approximations, not evidence of invertibility.
- Weights: all positive/finite; sum {primary['weight_sum']:.17g}; min {primary['weight_min']:.17g}; max {primary['weight_max']:.17g}. Rows and values below are the **library** samples, not the main estimator's distinct random design. Binary strings list features 0..d-1 left to right (little-endian integer encoding).

{markdown_table(zrows, ['mask', 'binary', 'weight', 'value'])}

## 4. Hypothesize and verify

**Confirmed on the four selected failures:** rank-deficient subset systems enter the installed normal-equation solve; it returns enormous finite coefficients rather than raising `LinAlgError`. Recomputing that exact normal system reproduces the captured coefficients (max difference for the first case: {primary['normal_recomputed_w_max_difference']}). In installed SHAP 0.49.1, `KernelExplainer.solve` only invokes the weighted `lstsq` fallback and singularity warning after an exception. Thus the successful return from a numerically singular solve bypasses both safeguards. Forming a Gram matrix worsens conditioning and floating-point perturbations can make exact rank deficiency appear solvable. It is not evidence that the original statistical estimation problem has a huge optimum or that the adapter passed a different game.

Competing explanations were checked: binary-mask mapping, endpoint handling, cached model values, changed reference, and failed seed reproduction were excluded by the assertions above. Rank deficiency **alone** does not imply huge output: some systems can trigger the existing fallback, and a default feature-selected subproblem may be smaller and well-conditioned. The original main constrained-SVD estimator uses a different design and does not form these normal equations; its P1 rank deficiency is an identifiability/variance limitation, not this particular numerical blow-up.

## 5. Minimal diagnostic remedy and verification (not applied to main runs)

On **exactly the same Z, W and v**:
1. Replace only the normal-equation solve with `np.linalg.lstsq(sqrt(w)[:,None]*X, sqrt(w)*y, rcond=1e-10)`, then recover the eliminated coefficient by efficiency.
2. Independently reconstruct the full efficiency-constrained orthonormal solution: `phi = delta/d + U @ lstsq(sqrt(w)[:,None]*(Z@U), sqrt(w)*(v-v0-Z@base), rcond=1e-10)[0]`, where `ones.T @ U = 0` and U is orthonormal (the same constraint mechanism as the main kernel, but **library masks and weights**).

The first solution minimizes the norm of the retained eliminated-coordinate coefficients; the second minimizes the full attribution's deviation from the equal-allocation base. On a rank-deficient design they can legitimately differ, while both avoid the pathological normal solve. Neither identifies the exact reference uniquely from these few samples. Using `rcond=None` as in the installed fallback gives the same retained SVD coefficients as `rcond=1e-10` on all four failures (maximum difference {max(r['lstsq_default_rcond_w_max_difference'] for r in data['reproductions']):.9g}); the improvement is not an artifact of a specially tuned cutoff. On all three working controls, changing only the selected-system normal solve to weighted SVD preserves library attributions to 1e-12. The full-feature constrained reconstruction is a different diagnostic from default feature selection, not a purported replacement for its selected-subproblem solution.

First-case normalized error: library **{primary['library']['error']:.9g}**, eliminated-coordinate SVD **{primary['eliminated_svd']['error']:.9g}**, constrained orthonormal SVD **{primary['constrained_svd']['error']:.9g}**. Weighted fit residual norms: {primary['library']['weighted_residual_norm']:.9g}, {primary['eliminated_svd']['weighted_residual_norm']:.9g}, {primary['constrained_svd']['weighted_residual_norm']:.9g}, respectively. Efficiency residuals: {primary['library']['efficiency_residual']:.9g}, {primary['eliminated_svd']['efficiency_residual']:.9g}, {primary['constrained_svd']['efficiency_residual']:.9g}. Efficiency alone is not a sufficient numerical check. Constrained weighted design rank is {primary['constrained_rank']}/{primary['d']-1}.

{markdown_table(phirows, ['j', 'reference', 'library', 'eliminated_SVD', 'constrained_SVD'])}

**Fix summary:** add only `/work/diagnose_library.py` and these diagnosis artifacts. No patch to the installed library, adapter, experimental design, analyses, paper, or reported results. A weighted rank-revealing least-squares solve is a demonstrated diagnostic remedy; adopting it as a baseline would be a separate protocol decision and is explicitly not done here.

**Verification:** rerun the command above. It checks deterministic matches, same-game identities, identical-design control, finite and bounded reconstruction assertions, all raw-record counts, and SHA256 invariance of {len(data['protected_hashes'])} protected files. Protected hashes are identical before/after this diagnostic run: `{data['protected_unchanged']}`.

**Bounded conclusion:** the four extreme records in this frozen limited library audit are reproduced numerical failures of this version/environment's unregularized low-budget normal-equation path on rank-deficient sampled designs. This does not condemn KernelExplainer generally, predict failure in all rank-deficient systems, establish every low-budget error's cause, or generalize to other SHAP versions, backgrounds, links, models or budgets. Original default and P16 results remain as recorded; all original huge values and warning-free failures are retained.
"""
    (ART / 'library_numerics_diagnosis.md').write_text(text)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.parse_args()
    ART.mkdir(exist_ok=True)
    before = snapshot()
    raw = pd.read_csv(ROOT / 'analysis/library_raw.csv')
    raw['warning_list'] = raw.warnings.map(ast.literal_eval)
    stored = []
    for path in sorted((ROOT / 'results/library').glob('*.npz')):
        with np.load(path) as z:
            assert str(z['shap_version']) == shap.__version__
            stored.extend(json.loads(str(z['records'])))
    assert len(raw) == len(stored)
    for csv, record in zip(raw.to_dict('records'), stored):
        for key in ('dataset', 'model', 'slot', 'p', 'mode', 'rep'):
            assert csv[key] == record[key]
        assert np.isclose(csv['error'], record['error'], rtol=5e-15, atol=1e-15)
        assert csv['warning_list'] == record['warnings']
    huge = raw[raw.error > HUGE]
    assert len(huge) > 0
    reproductions = [run_case(r) for r in huge.to_dict('records')]
    first = huge.iloc[0].to_dict()
    matched = run_case(dict(first, mode='default'), matched_seed=reproductions[0]['rng_seed'])
    for key in ('mask_matrix', 'weights', 'values'):
        assert np.array_equal(reproductions[0][key], matched[key]), key
    controls = [matched, run_case(dict(first, mode='default')), run_case(dict(first, p=16))]
    for r in controls:
        assert np.allclose(r['library']['phi'], r['eliminated_svd']['phi'], rtol=0, atol=1e-12)
    for r in reproductions:
        assert r['lstsq_default_rcond_w_max_difference'] < 1e-12
        assert r['exact_integer_design_rank'] < r['selected_design']['shape'][1]
        assert not r['normal_solve_raised'] and not r['warnings']
        assert r['normal_recomputed_w_max_difference'] == 0
        for method in ('eliminated_svd', 'constrained_svd'):
            assert r[method]['finite'] and r[method]['max_abs'] < 1
            assert r[method]['error'] < 2
            assert r[method]['efficiency_residual'] < 1e-12
    counts = warning_counts(raw)
    dataset_counts = []
    for ds, group in raw.groupby('dataset', sort=True):
        dataset_counts.extend(dict(dataset=ds, **r) for r in warning_counts(group))
    source_path = Path(inspect.getsourcefile(shap.KernelExplainer.solve))
    data = dict(raw_records=len(raw), huge_threshold=HUGE,
                threshold_counts={str(t): int((raw.error > t).sum()) for t in (100, 1e3, 1e6, 1e9, 1e12)},
                counts=counts, dataset_counts=dataset_counts,
                warning_message_counts=dict(Counter(m for ws in raw.warning_list for m in ws)),
                reproductions=reproductions, controls=controls,
                python=sys.version.split()[0],
                versions=dict(shap=shap.__version__, numpy=np.__version__, scipy=scipy.__version__, sklearn=sklearn.__version__),
                source_path=source_path, source_sha256=hashlib.sha256(source_path.read_bytes()).hexdigest(),
                solve_source=inspect.getsource(shap.KernelExplainer.solve),
                solve_source_start_line=inspect.getsourcelines(shap.KernelExplainer.solve)[1],
                explain_source=inspect.getsource(shap.KernelExplainer.explain),
                protected_hashes=before, protected_unchanged=before == snapshot())
    assert data['protected_unchanged'], 'A protected artifact changed during diagnosis.'
    (ART / 'library_numerics_diagnosis.json').write_text(json.dumps(data, default=native, indent=2, allow_nan=False) + '\n')
    write_report(data)
    assert snapshot() == before
    print(markdown_table(counts, ['mode', 'p', 'n', 'huge', 'warning_records', 'warning_events']))
    for r in reproductions:
        print(r['dataset'], r['model'], r['slot'], r['rep'], 'seed', r['rng_seed'],
              'rank', r['exact_integer_design_rank'], 'condition', r['normal']['condition'],
              'errors', r['library']['error'], r['eliminated_svd']['error'], r['constrained_svd']['error'])
    print('Protected artifacts unchanged:', len(before))
    print(ART / 'library_numerics_diagnosis.md')


if __name__ == '__main__':
    main()
