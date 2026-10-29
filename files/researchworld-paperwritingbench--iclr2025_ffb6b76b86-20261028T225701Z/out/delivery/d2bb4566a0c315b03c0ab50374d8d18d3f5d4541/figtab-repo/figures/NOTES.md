# Figure notes (figtab-repo)

figure_1..6.png are the supplied files, byte-identical. No other file in `figures/` is supplied; `fig_deltas.pdf` is new (generator `gen/make_delta_figure.py`, data `gen/data.py`).

| file | pixels | shows | consistent with caption? | suggested width |
|---|---|---|---|---|
| figure_1.png | 827x275 | left: prompt `def add5(aa): return 5 + a`, token-level P("a")=0.0 -> wrong completion; byte-level P("a")=0.9. Right: two LMs (A/B/AA and A/B/BB vocabularies) mapped to next-byte tables and averaged (A 0.4, B 0.6) | yes | `\linewidth` (text legible) |
| figure_2.png | 827x231 | 1st-order Markov chain, vocab {A,B,AA}, BPE of "AABABAA" = AA\|B\|A\|B\|AA; red edges: after token A the model gives probability 0.0 to A (and 0.0 self loop), 1.0 to B | yes (caption: from token "A" never sample "A") | `\linewidth` |
| figure_3.png | 281x314 (low resolution) | bars of P(next byte = A) for 8 last-3-byte contexts: ground truth, bias-correction method, biased estimate | yes; biased bar visible only for AAA (~0.12 vs ~0.3 truth) and BAA (~0.77, matches truth); biased estimate is ~0 for the other six contexts, where its bar is not visible | at most ~0.45\linewidth (about 2.5 in, ~110 dpi); at full width it is blurry. Cannot be re-rendered: no underlying data supplied |
| figure_4.png | 802x329 | left: cover encodings of "yumm y" and accept/reject criterion; right: Algorithm 1 backward search | yes | `\linewidth`; text ~5-6 pt at 5.5 in, marginal but legible |
| figure_5.png | 827x252 | five-step sampling procedure for x_{n+1} | yes | `\linewidth`; smallest text of the set, ~5 pt |
| figure_6.png | 819x160 | left: Table 1 as an image; right: pass@10 vs temperature, byte-level (PSM, SPM, SPM+healing curves overlap) vs token-level (SPM clearly lower) | left panel matches log Table 1 cell for cell; right panel has no numeric data in the log | `\linewidth`; Table 1 is duplicated by tables/table_1.tex -- use one of them, not both, in the main text |

Caption wording in the objective's list (e.g. "Figure 6 ... Bavarian et al. (2022)", Dagan et al. (2024), Athiwaratkun et al. (2024)) is the supplied text; its citations must exist in references.bib (paper-repo).
