p = "paper/main.tex"
s = open(p).read()
pairs = [
(r"as a Beta--Binomial law we derive and verify predicts;", r"as the (known) Beta--Binomial law of one-run coverage, which we verify, predicts;"),
(r"the Beta--Binomial law of one-run coverage and its consequence for evaluation;", r"the Beta--Binomial law of one-run coverage (a consequence of known results~\citep{vovk2012conditional}, used here as an evaluation tool);"),
]
for a, b in pairs:
    if a not in s:
        print("NOT FOUND:", a[:60]); continue
    s = s.replace(a, b)
open(p, "w").write(s)
p = "code/analyze_theory.py"
s = open(p).read()
a = 'ax.legend(frameon=False, loc="upper center", ncol=2)'
print(a in s)
s = s.replace(a, 'ax.legend(frameon=False, loc="upper center", ncol=2, fontsize=5.5, columnspacing=0.6, handlelength=1.2)')
open(p, "w").write(s)
