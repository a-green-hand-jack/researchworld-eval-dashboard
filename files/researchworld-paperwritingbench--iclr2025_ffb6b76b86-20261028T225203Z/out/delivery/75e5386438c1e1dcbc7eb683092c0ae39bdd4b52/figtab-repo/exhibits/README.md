# Exhibits for the paper (presentation, `figtab-repo`)

The paper's `template.tex` belongs to `paper-repo`. These blocks are written to be pasted into it
verbatim. Story-repo's PLAN.md asks for a self-contained `template.tex`, so paste the blocks instead of `\input`-ing them.

| file | contents | generator |
|---|---|---|
| `figures.tex` | six `figure` floats with rewritten captions and labels | hand-written (captions checked against the log and the images) |
| `tables.tex` | `tab:general` (log Table 2); `tab:code` + `tab:beam` side by side in one float (log Tables 3, 4) | `python3 scripts/make_tables.py` from `data/*.csv` |
| `table_fim_fallback.tex` | `tab:fim` (log Table 1), **only if Figure 6 is not used**: `figure_6.png` already prints the same numbers | same script |
| `claims.md` | which claim each exhibit supports, numbers checked, wording flags | — |
| `../preview/preview.pdf` | all exhibits compiled with `iclr2025_conference.sty` (layout check only, not the paper) | `scripts/build_preview.sh` |

## Preamble additions (after `\usepackage{url}`)
```latex
\usepackage{graphicx}
\usepackage{booktabs}
```
(`iclr2025_conference.sty` loads neither. booktabs matches the rules drawn inside `figure_6.png`.)

## Placement (outline of story-repo PLAN.md §3; method = Section 3, experiments = Section 4)
| label | file | where | width / footprint |
|---|---|---|---|
| `fig:overview` | figure_1.png | Introduction, first float (top of p. 1–2) | `\linewidth`, ~0.45 page with caption |
| `fig:markov1` | figure_2.png | 3.1, where tokenization bias is defined | `\linewidth`, ~0.4 page |
| `fig:cover` | figure_4.png | Method, next to the valid/cover-encoding definitions and Algorithm 1 | `\linewidth`, ~0.5 page |
| `fig:sampling` | figure_5.png | Method, next-byte sampling subsection | `\linewidth`, ~0.4 page |
| `fig:markov3` | figure_3.png | 4.1 synthetic experiments | 0.33\linewidth, caption below (paper-repo#4), ~0.45 page |
| `fig:fim` | figure_6.png | 4.2 FIM | `\linewidth`, ~0.3 page |
| `tab:general` | tables.tex | 4.3 token vs byte and ensembling | full width, ~0.3 page |
| `tab:code`, `tab:beam` | tables.tex (one float) | 4.3 / 4.4 | full width, ~0.3 page |

Total footprint ≈ 3.3 pages of the 10. Keep each float's first `\ref` in the text before (or on the
same page as) the float. LaTeX numbers figures in order of appearance, so `figure_4.png` must come before
`figure_5.png` (the caption of `fig:sampling` refers to `fig:cover`).

## Labels and keys the paper must define
- `\label{sec:method}` (exists in the template), `\label{def:valid}` (the definition of valid / invalid
  encodings), `\label{alg:cover}` (cover-encoding search). `figure_4.png` prints "Algorithm 1", so the
  search must be the paper's **first** `algorithm` float (`algorithm` + `algorithmic` packages).
- Citation keys in the Figure 6 caption: `bavarian2022fim` (FIM / HumanEval Random Span),
  `dagan2024tokenizer` (token healing), `athiwaratkun2024alignment` (token alignment), the keys
  of paper-repo's `references.bib`.

## Rendering choices
- Captions: lower case after the first word; figure captions below and table captions above (ICLR). The `Figure N:` prefixes and
  foreign cross-references ("Section 4.1", "Definition 3", "Figure 4") in `info.json` are replaced
  by `\ref`. The garbled text of the supplied captions is rewritten, e.g. Figure 2's "will never sample
  ... rather than with probability 1 − α".
- `figure_1/2/5.png` contain a stray horizontal rule (and a blank band) at the top, left over from cropping.
  `trim={0 0 0 N},clip` removes it at inclusion; the files themselves are not changed (PNG without dpi:
  1 px = 1 bp).
- Tables: "--" where the log has N/A; one bolding rule, stated in each caption: best score per
  benchmark over all cells of that benchmark. This reproduces every bold mark in the log and
  replaces its inconsistent use. Ensemble/voting rows sit below a rule and are reported in the byte
  columns, as in the log.
- No new figures: the objective allows only figures from the supplied list.
