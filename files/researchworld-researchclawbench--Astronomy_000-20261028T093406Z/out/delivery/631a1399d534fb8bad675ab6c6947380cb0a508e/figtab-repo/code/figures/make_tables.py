"""Markdown tables for the report (summary of limits, point estimate vs posterior, sensitivity, self-interaction, rate validation,
literature comparison). Reads outputs/*.json|csv; writes the markdown to stdout and to the path given as argv[1], if any."""
import sys, pandas as pd
from common import *

SL, SD = summary('leaver'), summary('detweiler')
lit = json.load(open(os.path.join(OUTPUTS, 'literature_windows.json')))
names = {'M33_X-7': 'M33 X-7', 'IRAS_09149-6206': 'IRAS 09149-6206', 'combined': 'Combined'}

def e(x): return f'{x:.2e}'.replace('e-0', 'e-').replace('e+0', 'e+')
def win(ws): return '; '.join(f'[{e(a)}, {e(b)}]' for a, b in ws) if ws else 'none'

out = []
out.append('**Table 1.** Boson-mass windows (eV) excluded at the stated posterior probability, headline Leaver-calibrated rate, '
           f"t_BH = 4.5e7 yr, scalar boson, l = m = 1–5, no self-interaction ({SL['n_samples']['M33_X-7']} and {SL['n_samples']['IRAS_09149-6206']} posterior samples; "
           'bootstrap = 200 resamples of the posterior).\n')
out.append('| source | 50% | 68% | 95% | 99.7% | 95% edges, bootstrap 16–84% |\n|---|---|---|---|---|---|')
for k, n in names.items():
    W = SL['windows_baseline_eV'][k]
    b = SL['bootstrap_95_edges'].get(k, {}).get('0.95') if k != 'combined' else None
    bs = f"lo {e(b['lo_16_50_84'][0])}–{e(b['lo_16_50_84'][2])}; hi {e(b['hi_16_50_84'][0])}–{e(b['hi_16_50_84'][2])}" if b and b['lo_16_50_84'] else 'no window'
    if k == 'combined': bs = 'as M33 X-7'
    out.append(f"| {n} | {win(W['50%'])} | {win(W['68%'])} | {win(W['95%'])} | {win(W['99.7%'])} | {bs} |")
out.append('\nWindow edges are linearly interpolated in (log μ, P_ex). Detweiler-rate 95% windows: ' +
           '; '.join(f"{names[k]}: {win(SD['windows_baseline_eV'][k]['95%'])}" for k in ('M33_X-7', 'IRAS_09149-6206')) + '.\n')

out.append('**Table 2.** Point estimate (median M, a*) versus full posterior (Leaver-calibrated rate; eV).\n')
out.append('| source | median M [Msun], a* | point-estimate window(s), median (M, a*) | window(s) with a* at 16% / 84% marginal value | posterior 95% window |\n|---|---|---|---|---|')
for k in ('M33_X-7', 'IRAS_09149-6206'):
    p = SL['point_estimate'][k]
    out.append(f"| {names[k]} | {p['median_M']:.4g}, {p['median_a']:.3f} | {win(p['windows_point_estimate'])} | {win(p['windows_point_a_lo'])} / {win(p['windows_point_a_hi'])} | {win(SL['windows_baseline_eV'][k]['95%'])} |")

out.append('\n**Table 3.** Sensitivity of the 95% exclusion windows (eV). L = Leaver-calibrated, D = Detweiler rate.\n')
out.append('| variation | M33 X-7 (L) | M33 X-7 (D) | IRAS 09149-6206 (L) | IRAS 09149-6206 (D) |\n|---|---|---|---|---|')
for k in SL['sensitivity_95']:
    out.append(f"| {k} | {win(SL['sensitivity_95'][k]['M33_X-7'])} | {win(SD['sensitivity_95'][k]['M33_X-7'])} | "
               f"{win(SL['sensitivity_95'][k]['IRAS_09149-6206'])} | {win(SD['sensitivity_95'][k]['IRAS_09149-6206'])} |")

F = pd.read_csv(os.path.join(OUTPUTS, 'fa_min_95_vs_mu_leaver.csv'))
out.append('\n**Table 4.** Self-interaction: smallest decay constant f_a excluded at 95% (the excluded region is f_a ≥ f_a,min, i.e. λ = μ²/f_a² ≤ μ²/f_a,min²), '
           'bosenova factor κ = 1 (0.1, 10 in brackets), M33 X-7 (IRAS 09149-6206 has no 95% limit). Leaver-calibrated rate.\n')
out.append('| μ [eV] | f_a,min [GeV], κ = 1 (0.1 / 10) | λ_max = μ²/f_a,min², κ = 1 |\n|---|---|---|')
c1, c01, c10 = (F[f'fa_min95_GeV_{k}_M33_X-7'].values for k in ('kappa1', 'kappa0.1', 'kappa10'))
mu = F['mu_eV'].values
sel = [i for i in np.where(np.isfinite(c1))[0] if np.isclose(np.log10(mu[i]) % 0.5, 0, atol=0.03) or np.isclose(np.log10(mu[i]) % 0.5, 0.5, atol=0.03)]
for i in sel:
    out.append(f'| {e(mu[i])} | {e(c1[i])} ({e(c01[i])} / {e(c10[i])}) | {e((mu[i]/(c1[i]*1e9))**2)} |')
imin = np.nanargmin(c1)
out.append(f"\nSmallest f_a,min over μ: κ = 1: {e(np.nanmin(c1))} GeV at μ = {e(mu[imin])} eV; κ = 0.1: {e(np.nanmin(c01))} GeV; κ = 10: {e(np.nanmin(c10))} GeV "
           '(grid step 0.125 dex in f_a).\n')

V = pd.read_csv(os.path.join(OUTPUTS, 'rate_validation.csv'))
out.append('**Table 5.** Growth-rate validation: Γ r_g from the Leaver continued-fraction solver and the analytic Detweiler rate (eq. 18 of paper_000). '
           'The first row is the benchmark of Witek et al. 2012, Table II (Im ω r_g = 1.504e-7).\n')
out.append('| α | a* | l = m | Γ_Leaver r_g | Γ_Detweiler r_g | ratio |\n|---|---|---|---|---|---|')
for _, r in V.iterrows():
    out.append(f"| {r['alpha']:g} | {r['a_star']:g} | {int(r['l=m'])} | {r['Gamma_Leaver_rg']:.3e} | {r['Gamma_Detweiler_rg']:.3e} | {r['ratio']:.3g} |")

st, sm = lit['Stott2018_excluded_mu_eV']['stellar_BHs'], lit['Stott2018_excluded_mu_eV']['SMBHs']
out.append('\n**Table 6.** Comparison with the windows quoted in Stott (2018) (paper_001; τ_Salpeter = 4.5e7 yr; union over many black holes, not a single source).\n')
out.append('| class | Stott 2018 [eV] | this work, one black hole each [eV] |\n|---|---|---|')
out.append(f"| stellar-mass BHs | [{e(st[0])}, {e(st[1])}] | M33 X-7, 95%: {win(SL['windows_baseline_eV']['M33_X-7']['95%'])} |")
out.append(f"| supermassive BHs | [{e(sm[0])}, {e(sm[1])}] | IRAS 09149-6206, 68%: {win(SL['windows_baseline_eV']['IRAS_09149-6206']['68%'])}; 95%: none |")
txt = '\n'.join(out) + '\n'
print(txt)
if len(sys.argv) > 1: open(sys.argv[1], 'w').write(txt)
