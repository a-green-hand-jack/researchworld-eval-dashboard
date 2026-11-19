"""LaTeX tables + numbers.tex for the paper. Usage: python make_tables.py"""
import sys, os
sys.path.insert(0, "/work/code")
import numpy as np, pandas as pd
from analysis_lib import *
from make_figs import SIM, TAB, world_Y, world_stats, WN, conclusions_tables
WORLDS = [w for w in ('q15', 'b05', 'mix') if os.path.exists(f"{SIM}/gap_{w}.parquet")]
EXTRA = [w for w in ('b15', 's17') if os.path.exists(f"{SIM}/gap_{w}.parquet")]
SFX = ''; CUR = WORLDS
SHORT = dict(q15='A: Qwen2.5-1.5B, prompt/demo grid ($K{=}40$)', b05='B: Qwen2.5-0.5B, format/demo grid ($K{=}40$)', b15='C: Qwen2.5-1.5B, format/demo grid ($K{=}40$)', s17='D: SmolLM2-1.7B, format/demo grid ($K{=}40$)', mix='A$\\cup$B: union ($K{=}80$)')
OPTN = dict(grid='Exhaustive', random='Random-8', sh='Succ. halving', minibatch='Minibatch (MIPRO-like)', greedy='Greedy coord.')
NUM = {}
HDR = dict(worlds=("lrrrrrr", "World & $K$ & mean & range & sd & $\\bar\\rho$ & reliab."),
           gap=("lrrrr", " & $n{=}50$ & 100 & 200 & 400"),
           concl=("rrrrrrr", "$n$ & false claim & (holdout) & lift & holdout lift & A$-$B & (holdout)"),
           protocols=("lrrrr", "Protocol & bias & RMSE & coverage & width"),
           split=("lrrrrr", "Protocol & cost & bias & RMSE & cover. & width"),
           allopt=("lrrrrrrrr", "\\multicolumn{1}{l}{} & \\multicolumn{2}{c}{naive} & hold. & \\multicolumn{2}{c}{replay boot.} & \\multicolumn{3}{c}{emp.\\ Bayes} \\\\\n & bias & RMSE & RMSE & bias & RMSE & bias & RMSE & cov."),
           norepl=("lrrr", " & i.i.d.\\ (main) & w/o repl., vs pool & w/o repl., vs fresh"),
           optsens=("lrrr", "setting & effort & gap & regret"),
           poolboot=("lrrr", "world, $n$ & main design & pool-bootstrap mean & 95\\% range"))
def wr(path, rows):
    """writes a complete tabular environment (so that the manuscript can \\input it outside any alignment)"""
    key = os.path.basename(path).split('_')[0].split('.')[0]; spec, head = HDR[key]
    txt = "\n".join(rows).rstrip(); assert txt.endswith('\\\\')
    open(path, 'w').write("\\begin{tabular}{%s}\\toprule\n%s \\\\\\midrule\n%s\n\\bottomrule\n\\end{tabular}\n" % (spec, head, txt[:-2].rstrip() + " \\\\"))

def split_half(Y, reps=200, seed=0):
    rng = np.random.default_rng(seed); r = []
    for _ in range(reps):
        p = rng.permutation(Y.shape[1]); h = Y.shape[1] // 2
        a, b = Y[:, p[:h]].mean(1), Y[:, p[h:]].mean(1); r.append(np.corrcoef(a, b)[0, 1])
    return float(np.mean(r))

def t_worlds():
    rows = []
    for w in CUR:
        Y = world_Y(w); th = Y.mean(1); st = world_stats(w)
        rows.append(f"{SHORT[w]} & {st['K']} & {st['mean']*100:.1f} & {th.min()*100:.1f}--{th.max()*100:.1f} & {th.std()*100:.2f} & {st['rho']:.2f} & {split_half(Y):.2f} \\\\")
        NUM[f'sd_{w}'] = f"{th.std()*100:.1f}"; NUM[f'rho_{w}'] = f"{st['rho']:.2f}"; NUM[f'acc_{w}'] = f"{st['mean']*100:.1f}"
    wr(f"{TAB}/worlds{SFX}.tex", rows)

def t_gap(ns=(50, 100, 200, 400)):
    out = []
    for w in CUR:
        d = pd.read_parquet(f"{SIM}/gap_{w}.parquet"); d['gap'] = (d.naive - d.theta) * 100
        out.append(f"\\multicolumn{{{len(ns)+1}}}{{l}}{{\\emph{{{SHORT[w]}}}}} \\\\")
        for o in OPTN:
            g = d[d.opt == o].groupby('n').gap.agg(['mean', 'sem'])
            out.append(f"{OPTN[o]} & " + " & ".join(f"{g.loc[n,'mean']:.1f}$\\pm${1.96*g.loc[n,'sem']:.1f}" for n in ns) + " \\\\")
            if o == 'grid':
                for n in ns: NUM[f'gap_{w}_grid_{n}'] = f"{g.loc[n,'mean']:.1f}"
        # true accuracy of grid-selected config and oracle
        x = d[(d.opt == 'grid') & (d.n == 100)]; NUM[f'dep_{w}'] = f"{x.theta.mean()*100:.1f}"; NUM[f'star_{w}'] = f"{x.theta_star.mean()*100:.1f}"
        NUM[f'naive100_{w}'] = f"{x.naive.mean()*100:.1f}"
    wr(f"{TAB}/gap{SFX}.tex", out)

def t_protocols(n=100, opt='grid'):
    out = []
    for w in CUR:
        d = pd.read_parquet(f"{SIM}/gap_{w}.parquet"); d = d[(d.opt == opt) & (d.n == n)]
        T = method_table(d); out.append(f"\\multicolumn{{5}}{{l}}{{\\emph{{{SHORT[w]}}}}} \\\\")
        for _, r in T.iterrows():
            cov = f"{r.cover:.2f}" if 'cover' in r and not np.isnan(r.cover) else "--"
            wid = f"{r.width*100:.1f}" if 'width' in r and not np.isnan(r.width) else "--"
            out.append(f"{r.method} & {r.bias*100:+.1f} & {r.rmse*100:.1f} & {cov} & {wid} \\\\")
            NUM[f"{w}_{r.method}_bias"] = f"{r.bias*100:+.1f}"; NUM[f"{w}_{r.method}_rmse"] = f"{r.rmse*100:.1f}"
    wr(f"{TAB}/protocols_{opt}_{n}{SFX}.tex", out)

def t_split(n=100):
    out = []
    for w in CUR:
        d = pd.read_parquet(f"{SIM}/gap_{w}.parquet"); d = d[(d.opt == 'grid') & (d.n == n)]
        out.append(f"\\multicolumn{{6}}{{l}}{{\\emph{{{SHORT[w]}}}}} \\\\")
        out.append(f"no split (naive) & 0.0 & {(d.naive-d.theta).mean()*100:+.1f} & {np.sqrt(((d.naive-d.theta)**2).mean())*100:.1f} & {((d.naive_lo<=d.theta)&(d.theta<=d.naive_hi)).mean():.2f} & {(d.naive_hi-d.naive_lo).mean()*100:.1f} \\\\")
        for f in (0.3, 0.5, 0.7):
            e = d[f'split{f}_est'] - d[f'split{f}_k_theta']; cost = (d.theta - d[f'split{f}_k_theta']).mean() * 100
            cov = ((d[f'split{f}_lo'] <= d[f'split{f}_k_theta']) & (d[f'split{f}_k_theta'] <= d[f'split{f}_hi'])).mean()
            out.append(f"select on {int(f*100)}\\% / report on {100-int(f*100)}\\% & {cost:.2f} & {e.mean()*100:+.1f} & {np.sqrt((e**2).mean())*100:.1f} & {cov:.2f} & {(d[f'split{f}_hi']-d[f'split{f}_lo']).mean()*100:.1f} \\\\")
    wr(f"{TAB}/split_{n}{SFX}.tex", out)

def t_concl():
    out = []
    for w in CUR:
        l, b = conclusions_tables(w)
        out.append(f"\\multicolumn{{7}}{{l}}{{\\emph{{{SHORT[w]}}}}} \\\\")
        for n in (50, 100, 200, 400):
            x = l[l.n == n]; y = x[x.rb.isin(['best', 'top 12%'])]; z = x[x.rb == 'top 50%']
            bb = b[(b.n == n) & (b.KA == 32) & (b.KB == 4)]
            out.append(f"{n} & {y.false.mean():.2f} & {y.false_s.mean():.2f} & {z.naive_lift.mean()*100:.1f} / {z.true_lift.mean()*100:.1f} & {z.split_lift.mean()*100:.1f} & {bb.naive_diff.mean()*100:.1f} / {bb.true_diff.mean()*100:.1f} & {bb.split_diff.mean()*100:.1f} \\\\")
    wr(f"{TAB}/concl{SFX}.tex", out)

def t_optsens(n=100):
    from make_figs import optsens_table
    out = []
    for w in CUR:
        g = optsens_table(w, n); out.append(f"\\multicolumn{{4}}{{l}}{{\\emph{{{SHORT[w]}}}}} \\\\")
        for _, r in g.sort_values(['opt', 'budget']).iterrows():
            out.append(f"{r.opt} {r.kw.replace('{','').replace('}','').replace(chr(39),'')} & {r.budget:.1f} & {r.gap:.1f}$\\pm${1.96*r.se:.1f} & {r.regret:.1f} \\\\")
    wr(f"{TAB}/optsens{SFX}.tex", out)

def t_allopt(n=100):
    out = []
    for w in CUR:
        d = pd.read_parquet(f"{SIM}/gap_{w}.parquet"); out.append(f"\\multicolumn{{9}}{{l}}{{\\emph{{{SHORT[w]}}}}} \\\\")
        for o in OPTN:
            T = method_table(d[(d.opt == o) & (d.n == n)]).set_index('method'); g = lambda m, c: T.loc[m, c] if m in T.index else np.nan
            f = lambda v, k=100, fmt="{:.1f}": "--" if np.isnan(v) else fmt.format(v * k)
            out.append(f"{OPTN[o]} & {f(g('Naive (dev score)','bias'))} & {f(g('Naive (dev score)','rmse'))} & {f(g('Holdout split (50/50)','rmse'))} & {f(g('Replay bootstrap (opt.)','bias'))} & {f(g('Replay bootstrap (opt.)','rmse'))} & {f(g('Empirical Bayes','bias'))} & {f(g('Empirical Bayes','rmse'))} & {f(g('Empirical Bayes','cover'),1,'{:.2f}')} \\\\")
    wr(f"{TAB}/allopt_{n}{SFX}.tex", out)

def t_poolboot():
    d = pd.read_csv(f"{SIM}/poolboot.csv"); out = []
    for w in CUR:
        for n in (50, 100, 400):
            x = d[(d.world == w) & (d.n == n)].gap; g = pd.read_parquet(f"{SIM}/gap_{w}.parquet"); g = g[(g.opt == 'grid') & (g.n == n)]
            out.append(f"{SHORT[w].split(':')[0]}, $n{{=}}{n}$ & {(g.naive-g.theta).mean()*100:.1f} & {x.mean():.1f} & {np.percentile(x,2.5):.1f}--{np.percentile(x,97.5):.1f} \\\\")
    wr(f"{TAB}/poolboot{SFX}.tex", out)

def t_norepl():
    out = []
    for w in CUR:
        d = pd.read_parquet(f"{SIM}/norepl_{w}.parquet"); d['gp'] = (d.naive - d.theta) * 100; d['gf'] = (d.naive - d.theta_fresh) * 100
        g = pd.read_parquet(f"{SIM}/gap_{w}.parquet"); g['gi'] = (g.naive - g.theta) * 100
        out.append(f"\\multicolumn{{4}}{{l}}{{\\emph{{{SHORT[w]}}}}} \\\\")
        for o in ('grid', 'minibatch'):
            for n in (50, 100, 200):
                x = d[(d.opt == o) & (d.n == n)]; y = g[(g.opt == o) & (g.n == n)]
                out.append(f"{OPTN[o]}, $n{{=}}{n}$ & {y.gi.mean():.1f} & {x.gp.mean():.1f} & {x.gf.mean():.1f}$\\pm${1.96*x.gf.sem():.1f} \\\\")
    wr(f"{TAB}/norepl{SFX}.tex", out)

if __name__ == "__main__":
    for CUR, SFX in ((WORLDS, ''), (EXTRA, '_extra')):
        if not CUR: continue
        t_worlds(); t_gap(); t_protocols(); t_split(); t_concl(); t_allopt(100)
        t_poolboot()
        if SFX == '': t_protocols(100, 'minibatch'); t_optsens(); t_allopt(50); t_norepl()
