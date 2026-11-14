p = "paper/main.tex"
s = open(p).read()
pairs = [
(r"Let $f$ be fixed and the scores $S_1,\dots,S_{n+1}$ exchangeable with continuous cdf $F$.", r"Let $f$ be fixed and the scores $S_1,\dots,S_{n+1}$ i.i.d.\ with continuous cdf $F$."),
(r"as Prop.~\ref{prop:zero} predicts once $\varepsilon$ is below the smallest predicted probabilities; no $\varepsilon$ reaches the Euclidean size.", r"as Prop.~\ref{prop:zero} predicts once $\varepsilon$ is below the smallest predicted probabilities. For the raw softmax no $\varepsilon$ reaches the Euclidean size (best $0.126$ vs.\ $0.094$); after temperature scaling the best value ($\varepsilon=10^{-3}$) gives $0.097$, comparable to $\ell_2$, but the size rises to $0.213$ and $0.529$ at $\varepsilon=10^{-6},10^{-8}$."),
(r"""\begin{figure}[t]
\centering
\includegraphics[width=\columnwidth]{fig_relsize.pdf}""", r"""\begin{figure*}[t]
\centering
\includegraphics[width=0.85\textwidth]{fig_relsize.pdf}"""),
(r"""\caption{Pool size relative to $\ell_2$ ($n_{\rm cal}=200$; numbers are ratios; blue: smaller than $\ell_2$).}
\label{fig:relsize}
\end{figure}""", r"""\caption{Pool size relative to $\ell_2$ ($n_{\rm cal}=200$; entries are ratios; blue: smaller than $\ell_2$, red: larger).}
\label{fig:relsize}
\end{figure*}"""),
]
for a, b in pairs:
    if a not in s:
        print("NOT FOUND:", a[:60]); continue
    s = s.replace(a, b)
open(p, "w").write(s)
p = "paper/appendix.tex"
s = open(p).read()
a = r"""Condition on $f$ (trained on independent data). Since $F$ is continuous, $U_i=F(S_i)$ are exchangeable $\mathrm{Unif}(0,1)$; for i.i.d.\ data they are i.i.d. (for merely exchangeable data the marginal statement below holds for the order statistic of the $n$ calibration scores and an independent test score; we use i.i.d.\ sampling as in the experiments). The coverage"""
b = r"""Condition on $f$ (trained on independent data). Since $F$ is continuous and the data are i.i.d., $U_i=F(S_i)$ are i.i.d.\ $\mathrm{Unif}(0,1)$ (for merely exchangeable data only the marginal statement $\E C_{\rm cal}=k/(n+1)$ survives). The coverage"""
print(a in s)
s = s.replace(a, b)
open(p, "w").write(s)
