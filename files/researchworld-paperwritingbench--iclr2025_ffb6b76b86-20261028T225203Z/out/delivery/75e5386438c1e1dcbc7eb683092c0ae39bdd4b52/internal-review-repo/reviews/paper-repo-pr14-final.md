# Review: paper-repo PR #14 "Final version" (into `final`)

Head inspected: `ae9207be069e44319a10a279c6e0c30e50dc0365`. Base for comparison: `ea1dc1576db2fec05729cffceb7fd03b0ef8e401`, which I approved as Version 1 (record: `reviews/paper-repo-pr8-version1.md`).
Standard: commitment internal-review-repo#2.

## What changed since the approved version
`ea1dc15..ae9207b` (paper-repo #13) touches `template.tex` and `template.pdf` only. In `template.tex` it just moves `\usepackage{hyperref}\usepackage{url}` after `algorithm`/`algpseudocode`. This is the fix I asked for as N2. `references.bib`, the figures and the style files are unchanged.

## Checks at `ae9207b`
- Clean `git archive` build with `latexmk -pdf`: rc=0. 0 undefined references, 0 overfull boxes, 0 duplicate-destination warnings (**N2 fixed**). 14 pages: main text pp. 1–10, references pp. 11–13, appendix p. 14.
- Style files and the six figures are byte-identical to `/initial-state/inputs`.
- The shipped `template.pdf` text equals the fresh build. The PDF text is also identical to the approved `ea1dc15` build (`diff` of pdftotext is empty), so every content check in the Version 1 record carries over unchanged. Those checks cover numbers vs. log, derived margins, honesty of the negative results, the 43 real pre-cutoff citations, the six figures inspected against their captions, page limit, anonymity, and method correctness.
- I reran experiment-repo `analysis/method_check.py` (commit 7fc7803) with `python3 -I`. Output: "ALL CHECKS PASS". Algorithm 1 equals the brute-force Lemma 1 sum, and the Proposition 1 recursion is consistent, for MPE and BPE. Valid encodings are prefix-closed, which supports the "positive probability → valid prefix" step in §3.3. Histories are not always prefixes of `encode(x_1^n)`, which matches the §3.4 wording.

## Open findings
None.

## Conclusion
**APPROVE** `ae9207b` for `final`.
