"""Generate tables/*.tex from numbers transcribed from the supplied tables
(/initial-state/inputs/9/table_{le,rr,im}.tex). Bold/underline/delta rows are
computed from the cells so text, bold and deltas cannot disagree.

Rule (agreed with paper-repo, paper-repo#3): bold = best entry in the column over all rows
(proprietary included); underline = strongest non-ours open-source model (the reference of
the Delta row); Delta = ours - underlined entry.  '-' = not reported.
"""
import os, sys
OUT = os.path.dirname(os.path.abspath(__file__))
COLS = ['MathVista', 'MathVerse', 'MathVision', 'MMMU-Pro', 'MMMU', 'EMMA', 'MEGA']
HEAD = r'''\toprule
\textbf{Model}&\multicolumn{3}{c}{\textbf{Math-Related}}&\multicolumn{3}{c}{\textbf{Multi-Discipline}}&\multicolumn{1}{c}{\textbf{Real-World}}\\
\cmidrule(lr){2-4}\cmidrule(lr){5-7}\cmidrule(lr){8-8}
&MathVista&MathVerse&MathVision&MMMU-Pro&MMMU&EMMA&MEGA\\
&testmini&testmini&test&overall&val&full&core\\
\midrule'''
N = None
# (name, values, flags) flags: 'dag{k}' -> dagger on column k
G7 = [
 ('InternVL2-8B', [58.3, N, 17.4, 29.0, 51.2, 19.8, 26.0], ''),
 ('InternVL2.5-8B', [64.4, 39.5, 19.7, 34.3, 56.0, N, 30.4], ''),
 ('QwenVL2-7B', [58.2, N, 16.3, 30.5, 54.1, 20.2, 34.8], ''),
 ('QwenVL2.5-7B', [68.2, 46.3, 25.1, 36.9, 54.3, 21.5, 35.0], 'd4'),
 ('Llava-OV-7B', [63.2, 26.2, N, 24.1, 48.8, 18.3, 22.9], ''),
 ('Kimi-VL-16B', [68.7, 44.9, 21.4, N, 55.7, N, N], 'd4'),
]
R7 = [
 ('MM-Eureka-8B (Intern)', [67.1, 40.4, 22.2, 27.8, 49.2, N, N], ''),
 ('MM-Eureka-7B (Qwen)', [73.0, 50.3, 26.9, N, N, N, N], ''),
 ('R1-VL-7B', [63.5, 40.0, 24.7, 7.8, 44.5, 8.3, 29.9], ''),
 ('R1-Onevision-7B', [64.1, 46.4, 29.9, 21.6, N, 20.8, 27.1], ''),
 ('OpenVLThinker-7B', [70.2, 47.9, 25.3, 37.3, 52.5, 26.6, 12.0], ''),
]
OURS7 = ('\\model-7B', [74.9, 54.2, 32.3, 41.7, 56.7, 29.7, 37.2], '')
PROP = [
 ('OpenAI-o1', [73.9, 57.0, 60.3, 62.4, 78.2, 45.7, 56.2], ''),
 ('OpenAI-GPT-4o', [60.0, 41.2, 30.6, 51.9, 69.1, 32.7, 52.7], ''),
 ('Claude-3.5-Sonnet', [67.7, 47.8, 33.5, 51.5, 68.3, 35.1, 52.3], ''),
 ('Gemini-2.0-Flash', [73.4, 54.6, 41.3, 51.7, 70.7, 33.6, 54.1], ''),
]
OPEN = [
 ('Llama4-Scout-109B', [70.7, N, N, 52.2, 69.4, 24.6, 31.8], ''),
 ('InternVL-2.5-78B', [72.3, 51.7, 34.9, 48.6, 61.8, 27.1, 44.1], ''),
 ('QvQ-72B', [71.4, 48.6, 35.9, 51.5, 70.3, 32.0, 8.8], ''),
 ('LLava-OV-72B', [67.5, 39.1, 30.1, 31.0, 56.8, 23.8, 29.7], ''),
 ('Qwen-2.5-VL-32B', [74.7, 48.5, 38.4, 49.5, 59.4, 31.1, 13.3], 'd4'),
 ('Qwen-2.5-VL-72B', [74.8, 57.2, 38.1, 51.6, 67.0, 34.1, 49.0], 'd4'),
]
O32 = ('\\model-32B', [78.8, 56.9, 40.5, 50.6, 65.6, 37.9, 19.9], '')
O72 = ('\\model-72B', [80.4, 63.5, 44.9, 55.9, 68.8, 38.5, 51.3], '')

def fmt(v, bold=False, ul=False, dag=False):
    if v is None: return '-'
    s = f'{v:.1f}'
    if bold: s = r'\textbf{%s}' % s
    if ul: s = r'\underline{%s}' % s
    return (r'$^\dagger$' + s) if dag else s

def row(name, vals, flags, best, prior_best, show_ul=True):
    cells = []
    for j, v in enumerate(vals):
        cells.append(fmt(v, bold=(v is not None and v == best[j]),
                         ul=(show_ul and v is not None and prior_best[j] is not None and v == prior_best[j]),
                         dag=('d%d' % j in flags)))
    return name + '&' + '&'.join(cells) + r'\\'

def colmax(rows):
    return [max([r[1][j] for r in rows if r[1][j] is not None]) for j in range(7)]

def delta_row(ours, prior_best):
    ds = []
    for o, p in zip(ours[1], prior_best):
        d = round(o - p, 1)
        ds.append(f'{d:+.1f}'.replace('-', '$-$'))
    return r'\rowcolor{cyan!20}' + '\n' + r'$\Delta$ (Ours $-$ underlined)&' + '&'.join(ds) + r'\\'

def wrap(body, caption, label):
    return ('\\begin{table*}[t]\n\\centering\n\\small\n\\setlength{\\tabcolsep}{5pt}\n'
            '\\resizebox{\\textwidth}{!}{\n\\begin{tabular}{lccccccc}\n' + body +
            '\n\\bottomrule\n\\end{tabular}\n}\n\\caption{' + caption + '}\n\\label{' + label + '}\n\\end{table*}\n')

def table_le():
    base = G7 + R7
    prior = colmax(base)
    allm = base + [OURS7]
    best = colmax(allm)
    L = [HEAD, r'\multicolumn{8}{c}{\textit{General Vision-Language Models}}\\', r'\midrule']
    L += [row(*r, best, prior) for r in G7]
    L += [r'\midrule', r'\multicolumn{8}{c}{\textit{Vision-Language Reasoning Models}}\\', r'\midrule']
    L += [row(*r, best, prior) for r in R7]
    L += [r'\midrule', row(*OURS7, best, prior), delta_row(OURS7, prior)]
    cap = (r'Comparison of \model-7B with general and reasoning vision-language models of $\sim$7B scale (accuracy, \%). '
           r'\textbf{Bold}: best in column; \underline{underline}: strongest non-ours model in the column. $\Delta$ = ours minus the underlined entry. '
           r'\texttt{-}: not reported. $^\dagger$: reproduced by us.')
    return wrap('\n'.join(L), cap, 'table:7b_results')

def table_rr():
    prior = colmax(OPEN)
    best = colmax(PROP + OPEN + [O32, O72])
    L = [HEAD, r'\multicolumn{8}{c}{\textit{Proprietary Models}}\\', r'\midrule']
    L += [row(*r, best, prior) for r in PROP]
    L += [r'\midrule', r'\multicolumn{8}{c}{\textit{Open-Source Models}}\\', r'\midrule']
    L += [row(*r, best, prior) for r in OPEN]
    L += [r'\midrule', row(*O32, best, prior), row(*O72, best, prior), delta_row(O72, prior)]
    cap = (r'Comparison of \model-72B and \model-32B (both ours) with proprietary and open-source models (accuracy, \%). '
           r'\textbf{Bold}: best in column over all rows, proprietary included (ours is not bold where it is not best, e.g.\ MMMU val). '
           r'\underline{Underline}: strongest non-ours open-source model in the column. '
           r'$\Delta$ = \model-72B minus the underlined entry (the strongest non-ours open-source model per column). '
           r'\texttt{-}: not reported. $^\dagger$: reproduced by us with our evaluation protocol.')
    return wrap('\n'.join(L), cap, 'table:main_results')

ABL = [
 ('\\model-7B', 'SSR', '16K', [32.3, 74.9, 54.2, 41.7, 29.7]),
 ("w/o `Forced-Rethinking'", 'SSR', '16K', [29.8, 72.4, 53.2, 40.9, 29.5]),
 ('- no SSR', 'Filter', '16K', [28.5, 72.0, 50.0, 40.0, 26.9]),
 ('- no SSR \\& Filter', 'GRPO', '16K', [26.0, 70.9, 51.4, 38.8, 26.2]),
 ('- no Text', 'SSR', '13K', [29.1, 73.5, 53.5, 41.1, 28.7]),
 ('- no Science \\& Text', 'SSR', '11K', [28.0, 71.6, 50.3, 39.7, 28.0]),
]
def table_im():
    full = ABL[0][3]
    cols = list(zip(*[a[3] for a in ABL]))
    best = [max(c) for c in cols]
    L = [r'\toprule',
         r'\textbf{Model}&RL-Algo&Data&MathVision&MathVista&MathVerse&MMMU-Pro&EMMA\\', r'\midrule']
    for i, (n, alg, d, v) in enumerate(ABL):
        if i in (1, 2, 4): L.append(r'\midrule')
        cells = []
        for j, x in enumerate(v):
            c = fmt(x, bold=(x == best[j]))
            if i: c += r'~{\scriptsize(' + f'{x - full[j]:+.1f}'.replace('-', '$-$') + ')}'
            cells.append(c)
        L.append(f'{n}&{alg}&{d}&' + '&'.join(cells) + r'\\')
    cap = (r'Ablation of \model-7B (accuracy, \%). Rows below the full model remove Forced Rethinking, '
           r'then replace SSR by filtering (Filter) and by plain GRPO, and then (last block) remove the Text or the Science \& Text training data '
           r'(16K $\rightarrow$ 13K $\rightarrow$ 11K queries). Smaller numbers in brackets: difference to the full model. '
           r'\textbf{Bold}: best in column.')
    body = '\n'.join(L)
    return ('\\begin{table*}[t]\n\\centering\n\\small\n\\resizebox{\\textwidth}{!}{\n\\begin{tabular}{lcc' + 'c' * 5 + '}\n' + body +
            '\n\\bottomrule\n\\end{tabular}\n}\n\\caption{' + cap + '}\n\\label{table:ablation_results}\n\\end{table*}\n')

if __name__ == '__main__':
    for name, f in [('table_le', table_le), ('table_rr', table_rr), ('table_im', table_im)]:
        open(os.path.join(OUT, name + '.tex'), 'w').write(f())
        print('wrote', name)
