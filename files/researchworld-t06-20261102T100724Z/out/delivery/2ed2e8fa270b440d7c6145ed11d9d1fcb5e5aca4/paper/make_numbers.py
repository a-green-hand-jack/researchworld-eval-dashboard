"""Write numbers.tex: every number quoted in the running text of main.tex, read from ../results/*.csv.

Run: python3 -I make_numbers.py   (from paper/). Inputs: results/{data_summary,kstar_full,summary_claims,
random_curve,boot_flip,kstar_judges,exact_check,approx_check,scaling_fit,paired_mt,matched_arena,sensitivity,elo_order,
sanity_fit,se_check}.csv as committed by experiment-repo.
"""
import os
import pandas as pd
import numpy as np

R = os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', 'results')
rd = lambda f: pd.read_csv(os.path.join(R, f))
out = []


def m(name, val):
    # read in the text as \N{name}; \csname allows digits in the key
    out.append('\\expandafter\\def\\csname N@%s\\endcsname{%s}' % (name, val))


def i(x):
    return '{:,}'.format(int(round(x))).replace(',', '\\,')


def f(x, d=2):
    return ('{:.%df}' % d).format(x)


def pct(x, d=2):
    return ('{:.%df}\\%%' % d).format(100 * x)


ds = rd('data_summary.csv').set_index('board')
kf = rd('kstar_full.csv')
sm = rd('summary_claims.csv')
bf = rd('boot_flip.csv')
rc = rd('random_curve.csv')
sf = rd('scaling_fit.csv')
pm = rd('paired_mt.csv')
ma = rd('matched_arena.csv')
se = rd('sensitivity.csv')
ex = rd('exact_check.csv')
ap = rd('approx_check.csv')
eo = rd('elo_order.csv')
sn = rd('sanity_fit.csv')
sc = rd('se_check.csv')

tag = {'arena55k': 'A', 'mtbench_human': 'MH', 'mtbench_gpt4': 'MG', 'nba_2015': 'NB'}
for b, t in tag.items():
    m(t + 'N', i(ds.loc[b, 'N']))
    m(t + 'P', i(ds.loc[b, 'n_participants']))
    m(t + 'tie', pct(ds.loc[b, 'tie_rate'], 0))
    m(t + 'cpp', i(ds.loc[b, 'cmp_per_participant']))
    for p in ['P1', 'P2', 'P3']:
        for cl, ci in [('C1', 0), ('C2', 1), ('C2', 2)]:
            r = kf[(kf.board == b) & (kf.claim == cl) & (kf.claim_id == ci) & (kf.pert == p)].iloc[0]
            nm = '%s%s%s%d' % (t, cl, p, ci)
            m(nm + 'k', i(r.k_star))
            m(nm + 'kN', pct(r.k_star / r.N, 3 if r.k_star / r.N < 0.001 else 2))
            m(nm + 'z', f(r.z, 2))
            m(nm + 'klin', f(r.k_lin, 1))

# replicate-unit summaries: median [2.5, 97.5] of k* over replicate units
unit = {'A': ('arena55k', 'boot'), 'MH': ('mtbench_human', 'qboot'), 'MG': ('mtbench_gpt4', 'qboot'),
        'NS': ('nba_season', 'nba_season'), 'MMH': ('mtmatched_h', 'qboot'), 'MMG': ('mtmatched_g', 'qboot')}
for t, (b, u) in unit.items():
    for cl in ['C1', 'C2', 'C3', 'C4']:
        for p in ['P1', 'P2']:
            rr = sm[(sm.board == b) & (sm.unit_type == u) & (sm.claim == cl) & (sm.pert == p)]
            if rr.empty:
                continue
            r = rr.iloc[0]
            nm = 'U%s%s%s' % (t, cl, p)
            m(nm + 'med', f(r.k_median, 0))
            m(nm + 'lo', f(r.k_q025, 0))
            m(nm + 'hi', f(r.k_q975, 0))
            m(nm + 'kN', pct(r.kN_median, 2 if r.kN_median > 0.001 else 3))
            m(nm + 'kNloc', pct(r.kNloc_median, 1))
            m(nm + 'z', f(r.z_median, 1))
            m(nm + 'fz', pct(r.frac_z_lt_196, 0))
            m(nm + 'n', i(r.n_units))

# bootstrap flip probabilities (full-size bootstrap)
for b, t in tag.items():
    for cl, ci in [('C1', 0), ('C2', 1), ('C2', 2), ('C2', 3)]:
        r = bf[(bf.board == b) & (bf.claim == cl) & (bf.claim_id == ci) & (bf.frac == 1.0)].iloc[0]
        m('BF%s%s%d' % (t, cl, ci), pct(r.n_changed / r.n_rep, 0))
        m('BFn%s' % t, i(r.n_rep))

# random removal: largest k tried, and flip probability there (C1)
for b, t in tag.items():
    d = rc[(rc.board == b) & (rc.kind == 'remove') & (rc.claim == 'C1')]
    top = d[d.k == d.k.max()].iloc[0]
    m('RR%skmax' % t, i(top.k))
    m('RR%sp' % t, pct(top.n_changed / top.n_rep, 0))
    m('RRn%s' % t, i(top.n_rep))
    for k_ in [100, 200]:
        dd = d[d.k == k_]
        if len(dd):
            m('RR%sp%d' % (t, k_), pct(dd.iloc[0].n_changed / dd.iloc[0].n_rep, 0))

# random removal vs worst case for the weakest significant adjacent pair (C2, rank 2) and ratio kmax/k*
for b, t in tag.items():
    d = rc[(rc.board == b) & (rc.kind == 'remove') & (rc.claim == 'C2') & (rc.claim_id == 2)]
    top = d[d.k == d.k.max()].iloc[0]
    m('RW%skmax' % t, i(top.k)); m('RWn%s' % t, i(top.n_rep)); m('RW%sp' % t, pct(top.n_changed / top.n_rep, 0))
    k1 = kf[(kf.board == b) & (kf.claim == 'C2') & (kf.claim_id == 2) & (kf.pert == 'P1')].iloc[0].k_star
    m('RW%sratio' % t, f(top.k / k1, 1))
    d1 = rc[(rc.board == b) & (rc.kind == 'remove') & (rc.claim == 'C1')]
    t1 = d1[d1.k == d1.k.max()].iloc[0]
    k1 = kf[(kf.board == b) & (kf.claim == 'C1') & (kf.pert == 'P1')].iloc[0].k_star
    m('RR%sratio' % t, f(t1.k / k1, 1))
# crowd vs LLM judges on identical Arena battles (kstar_judges.csv, paired_mt.csv rows a = arena49k_h)
kj = rd('kstar_judges.csv')
kjf = kj[(kj.unit_type == 'full') & (kj.pert == 'P1')]
m('JHtie', pct(kjf[kjf.board == 'arena49k_h'].tie_rate.iloc[0], 0)); m('JN', i(kjf.N.iloc[0]))
for cl, ci in [('C1', 0), ('C2', 2)]:
    r = kjf[(kjf.board == 'arena49k_h') & (kjf.claim == cl) & (kjf.claim_id == ci)].iloc[0]
    m('JH%s%dk' % (cl, ci), i(r.k_star)); m('JH%s%dz' % (cl, ci), f(r.z, 1))
for jn, t in [('Meta-Llama-3-70B-Instruct', 'L'), ('Athene-70B', 'T'), ('Qwen2-72B-Instruct', 'Q')]:
    b = 'arena49k_' + jn
    m('J%stie' % t, pct(kjf[kjf.board == b].tie_rate.iloc[0], 0))
    for cl, ci in [('C1', 0), ('C2', 2)]:
        r = kjf[(kjf.board == b) & (kjf.claim == cl) & (kjf.claim_id == ci)].iloc[0]
        m('J%s%s%dk' % (t, cl, ci), i(r.k_star)); m('J%s%s%dz' % (t, cl, ci), f(r.z, 1))
        p = pm[(pm.a == 'arena49k_h') & (pm.b == b) & (pm.claim == cl) & (pm.claim_id == ci) & (pm.pert == 'P1')].iloc[0]
        m('JR%s%s%d' % (t, cl, ci), '%s [%s, %s]' % (f(np.exp(p.logratio_k_median), 2), f(np.exp(p.logratio_k_q025), 2), f(np.exp(p.logratio_k_q975), 2)))
        m('JRn%s%s%d' % (t, cl, ci), i(p.n_units))
# resolved (|z| >= 1.96 before any edit) versus unresolved claims: median k* (adjacent order, removals)
sc_ = rd('summary_claims.csv')
for b, u, t in [('nba_season', 'nba_season', 'NS'), ('arena55k', 'boot', 'A'), ('mtbench_human', 'qboot', 'MH'), ('mtbench_gpt4', 'qboot', 'MG')]:
    r = sc_[(sc_.board == b) & (sc_.unit_type == u) & (sc_.claim == 'C2') & (sc_.pert == 'P1')].iloc[0]
    m('RS%sres' % t, f(r.k_median_resolved, 0)); m('RS%sunres' % t, f(r.k_median_unresolved, 0))
    m('RS%snres' % t, i(r.n_resolved)); m('RS%snrows' % t, i(r.n_rows))
al = rd('alignment.csv').set_index('item').n
m('ALkeys', i(al['keys_common'])); m('ALdrop', i(al['gpt4_rows_dropped_no_human'])); m('ALh', i(al['human_rows_total'])); m('ALg', i(al['gpt4_rows_total']))
# exact check
d = ex[~ex.exact_capped]
m('EXn', i(len(d)))
m('EXagree', i((d.k_greedy == d.k_exact).sum()))
m('EXcap', i(ex.exact_capped.sum()))
m('EXall', i(len(ex)))
# linearisation error at an edit budget equal to k*
ap = ap.assign(rel=(ap.pred_change - ap.actual_change) / ap.actual_change.abs())
for fr, nm in [(0.25, 'a'), (1.0, 'b'), (2.0, 'c')]:
    x = ap[ap.frac_of_kstar_P1 == fr].rel
    m('AP%smed' % nm, pct(x.abs().median(), 1))
    m('AP%smax' % nm, pct(x.abs().max(), 0))
m('APn', i((ap.frac_of_kstar_P1 == 1.0).sum()))

# scaling regression (unit-bootstrap CI; dataset-cluster CI)
for cl in ['C1', 'C2', 'C4']:
    for sch, s_ in [('unit', 'u'), ('dataset', 'd')]:
        for term, tn in [('log_z', 'z'), ('log_Nlocal', 'N')]:
            r = sf[(sf.claim == cl) & (sf.pert == 'P1') & (sf.model == 'M0') & (sf.term == term) & (sf.scheme == sch)].iloc[0]
            m('SC%s%s%s' % (cl, s_, tn), f(r.coef, 2))
            m('SC%s%s%slo' % (cl, s_, tn), f(r.ci_lo, 2))
            m('SC%s%s%shi' % (cl, s_, tn), f(r.ci_hi, 2))
    r = sf[(sf.claim == cl) & (sf.pert == 'P1') & (sf.model == 'M0')].iloc[0]
    m('SC%sr2' % cl, f(r.r2, 2))
    m('SC%sres' % cl, f(r.resid_sd, 2))
    m('SC%srows' % cl, i(r.n_rows))
for term in ['design_expert', 'design_model-judge', 'design_sports']:
    r = sf[(sf.claim == 'C2') & (sf.pert == 'P1') & (sf.model == 'M1') & (sf.term == term)].iloc[0]
    m('SM%s' % term.split('_')[1].split('-')[0], '%s [%s, %s]' % (f(r.coef, 2), f(r.ci_lo, 2), f(r.ci_hi, 2)))
    m('SF%s' % term.split('_')[1].split('-')[0], f(np.exp(r.coef), 2))
dc = sf[(sf.model == 'M1') & (sf.scheme == 'unit') & sf.term.str.startswith('design_')]
m('SDmin', f(dc.coef.min(), 2)); m('SDmax', f(dc.coef.max(), 2))
m('SDfmin', f(np.exp(dc.coef.min()), 2)); m('SDfmax', f(np.exp(dc.coef.max()), 2))
m('SDn', i(len(dc)))
m('SM1r2', f(sf[(sf.claim == 'C2') & (sf.pert == 'P1') & (sf.model == 'M1')].r2.iloc[0], 3))
m('SM0r2', f(sf[(sf.claim == 'C2') & (sf.pert == 'P1') & (sf.model == 'M0')].r2.iloc[0], 3))

# paired MT-Bench human vs GPT-4 (log ratio of k*/N, P1)
def pr(a, b, cl, ci):
    r = pm[(pm.a == a) & (pm.b == b) & (pm.claim == cl) & (pm.claim_id == ci) & (pm.pert == 'P1')].iloc[0]
    return r
for (a, b, t) in [('mtbench_human', 'mtbench_gpt4', 'PA'), ('mtmatched_h1', 'mtmatched_g', 'PB')]:
    for cl, ci in [('C1', 0), ('C2', 2), ('C2', 3)]:
        r = pr(a, b, cl, ci)
        m('%s%s%d' % (t, cl, ci), '%s [%s, %s]' % (f(np.exp(r.logratio_k_median), 1), f(np.exp(r.logratio_k_q025), 1), f(np.exp(r.logratio_k_q975), 1)))
        m('%sN%s%d' % (t, cl, ci), '%s [%s, %s]' % (f(np.exp(r.logratio_kN_median), 1), f(np.exp(r.logratio_kN_q025), 1), f(np.exp(r.logratio_kN_q975), 1)))
        m('%sdz%s%d' % (t, cl, ci), '%s [%s, %s]' % (f(r.dz_median, 1), f(r.dz_q025, 1), f(r.dz_q975, 1)))

# matched Arena subsets
for u in ['mt_dense', 'mt_random6', 'nba_like', 'sizecurve']:
    for cl in ['C2', 'C4']:
        r = sm[(sm.board == 'arena55k_sub') & (sm.unit_type == u) & (sm.claim == cl) & (sm.pert == 'P1')].iloc[0]
        nm = 'MA%s%s' % (u.replace('_', ''), cl)
        m(nm + 'med', f(r.k_median, 0)); m(nm + 'lo', f(r.k_q025, 0)); m(nm + 'hi', f(r.k_q975, 0))
        m(nm + 'kN', pct(r.kN_median, 2 if r.kN_median > 0.001 else 3)); m(nm + 'z', f(r.z_median, 1)); m(nm + 'n', i(r.n_units))

# sensitivity (P1, full-data fits)
def sv(board, var, cl, ci):
    return se[(se.board == board) & (se.variant == var) & (se.claim == cl) & (se.claim_id == ci) & (se.pert == 'P1')].iloc[0]
for t, b in [('A', 'arena55k'), ('MH', 'mtbench_human'), ('MG', 'mtbench_gpt4')]:
    for v in ['tie_half', 'tie_dropped']:
        for ci in [0, 2]:
            cl = 'C1' if ci == 0 else 'C2'
            r = sv(b, v, cl, ci)
            m('SE%s%s%d' % (t, v.replace('_', ''), ci), i(r.k_star))
for v in ['pooled_5', 'pooled_10', 'pooled_20']:
    r = sv('nba_pooled', v, 'C1', 0)
    m('SEnba%s' % v.replace('_', ''), '%s of %s' % (i(r.k_star), i(r.N)))
nb = se[(se.board == 'nba_season') & (se.pert == 'P1') & (se.claim == 'C1')]
for v in ['no_home', 'with_playoffs']:
    x = nb[nb.variant == v]
    m('SENB%s' % v.replace('_', ''), f(x.k_star.median(), 0))
    m('SENBn%s' % v.replace('_', ''), i(len(x)))

# Elo vs BT
for _, r in eo.iterrows():
    nm = 'EL%s%d' % (tag.get(r.board, r.board).replace('mtbench_human', 'MH').replace('nba_', 'NB'), r.K)
    m(nm + 'tau', f(r.tau_elo_vs_bt_mean, 2)); m(nm + 'top', pct(r.p_top1_same_as_ref, 0)); m(nm + 'perm', f(r.tau_perm_vs_ref_mean, 2))
m('SNtau', f(sn.tau_bt_vs_538elo.mean(), 2)); m('SNtauwr', f(sn.tau_bt_vs_winrate.mean(), 2))
m('SNsame', pct(sn.same_top1.mean(), 0)); m('SNn', i(sn.tau_bt_vs_538elo.notna().sum()))
m('SEratiomin', f(sc.se_ratio_wald_over_boot.min(), 2)); m('SEratiomax', f(sc.se_ratio_wald_over_boot.max(), 2))

with open(os.path.join(os.path.dirname(os.path.abspath(__file__)), 'numbers.tex'), 'w') as fh:
    fh.write('% generated by make_numbers.py from results/*.csv; do not edit\n' + '\n'.join(out) + '\n')
print(len(out), 'macros')
