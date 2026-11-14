import sys
p = "paper/main.tex"
s = open(p).read()
pairs = [
(r"agrees with Prop.~\ref{prop:zero} within $0.4$--$1.6\%$ in all six", r"agrees with Prop.~\ref{prop:zero} to within $1.6\%$ (range $0.05$--$1.6\%$) in all six"),
(r"(95\% bootstrap half-width $\le 0.005$). Coverage of every row is within $0.898$--$0.909$ (App.~\ref{app:tables})", r"(95\% bootstrap half-width $\le 0.006$). Coverage of every row is within $0.898$--$0.908$ (App.~\ref{app:tables})"),
(r"(exact zeros in 72\% of the $K{=}5$ targets)", r"(exact zeros in 64\% of the $K{=}5$ targets)"),
(r"The best score is the same for $n_{\rm train}\in[30,3000]$ in each noise family (App.~\ref{app:tables}); the log-ratio advantage on LN data does not depend on predictor quality in this range.", r"With a weaker or stronger predictor ($n_{\rm train}\in[30,3000]$, $K{=}5$) the winners are unchanged: Aitchison for both LN families, KL or Hellinger (near-tied) for Dirichlet and KL for multinomial targets (App.~\ref{app:tables})."),
(r"95\% CI half-widths: coverage $\le0.003$, size $\le 0.003$, ent.-gap $\le0.008$.}", r"95\% CI half-widths: coverage $\le0.003$, size $\le 0.006$, ent.-gap and arg-gap $\le0.008$.}"),
(r"since its population average equals $1-\alpha$, $c<1-\alpha$", r"since its average over $f_1(X)$ equals $1-\alpha$ for the population threshold, $c<1-\alpha$"),
(r"and is above $50\%$ at $n=100$ for every $m$", r"and is $50\%$ or more at $n=100$ for every $m$"),
]
for a, b in pairs:
    if a not in s:
        print("NOT FOUND:", a[:60]); continue
    s = s.replace(a, b)
open(p, "w").write(s)
print("ok")
