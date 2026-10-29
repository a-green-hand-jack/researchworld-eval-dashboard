# Review: paper-repo PR #8 "Version 1" (into `release`)

Head inspected: `4ee06fec822069d515b8dea168b729c864fc6a52` (paper-repo `main`).
Standard: commitment internal-review-repo#2 (objective `/initial-state/inputs/0/INSTRUCTIONS.md`, `guidelines.md`).

## What I did
- `git archive` of the head into a clean dir, deleted the shipped `template.pdf`, rebuilt with `latexmk -pdf` (pdflatex+bibtex). rc=0; no undefined references/citations, no overfull boxes, 0 BibTeX warnings; 13 pages, same as the shipped PDF.
- `cmp` of the five style/math files and six figures against `/initial-state/inputs/*`: all byte-identical.
- Read the full PDF text; rendered every page and opened every figure at print size (pages 2, 4, 5, 7, 8, 9; zoomed Fig. 1 and Fig. 5).
- Cited keys vs `references.bib`: 43 cited = 43 entries, none missing, none unused. Titles/dates of the 2023–2024 arXiv entries checked against the arXiv API (Dagan 2402.01035, Athiwaratkun 2403.08688, Yu/GaC 2406.12585, Huang/DeePEn 2404.12715, Gastaldi 2407.11606, Minixhofer 2405.07883, Schmidt 2402.18376, Singh 2402.14903, Chirkova 2306.17757, Ali 2310.08754): all exist, all before 2024-10. The remaining entries are standard venue papers.

## Checks against the standard
1. Deliverables: `template.tex`, `references.bib`, `template.pdf` at root, nonempty; PDF matches a fresh build. OK.
2. Template: ICLR 2025 preamble kept, author placeholder exact, section order kept, bibliography commands kept; no identifying information. OK.
3. Length: main text ends on p. 10, references on pp. 11–13; abstract is one paragraph; title is two lines; figure captions below, table captions above. OK.
4. Numbers: every value in Tables 1–3, Fig. 6 discussion, abstract and conclusion matches the log. Derived quantities recomputed: SPM +18.9 / +17.8 pts; within 1.8 of byte PSM; margins over healing/alignment 0.5–1.4; 21 pairs = 7 higher / 4 equal / 10 lower, range −3.6…+1.8; ensemble deltas (65.4 vs 63.4, 30.0 vs 28.8, 80.7 vs 80.3, 64.2 vs 63.6, 42.1 vs 38.4 = +3.7, vs 36.5 = +5.6); GSM8K 61.5 vs 39.0 (>20 pts), ensemble 55.8 below; beam +2.0 PSM / +2.9 SPM. All correct, stated in points. Negative results (HumanEval byte < token for all three code models, Llama2 NQ/GSM8K, GSM8K ensemble, MBPP tie) are reported plainly. Missing variance and possible test-set top-2 selection are disclosed. OK.
5. Method: Definitions 1–2, Assumption 1, Lemma 1 with proof (disjointness argument holds), cover-encoding characterization, Algorithm 1, Proposition 1 with proof, Eq. 5, ensembling Eq. 6. Enough to reimplement; the exactness claim is tied to Assumption 1, and the limitations say it holds only approximately. OK.
6. Figures: all six supplied figures used with the `figures/` prefix and referenced in the text; captions are rewritten to this paper's numbering (supplied "Figure 4/Section 4.1/Algorithm 1" now resolve). Content checked against each image: Fig. 1 (prompt "return 5 + a", token a = 0.0, byte a = 0.9; ensemble average 0.4/0.6 is correct); Fig. 2 (vocab {A,B,AA}, red 0.0/1.0 edges); Fig. 3 (yummy, 8-token vocabulary, termination at 3 chars); Fig. 5 (biased estimate is ~0 for 6 of 8 contexts, nonzero only for BAA and AAA; corrected bars match ground truth); Fig. 6 (left panel table equals log Table 1; right panel byte PSM/SPM curves coincide, token SPM below). All legible at print size. OK.
7. Citations: natbib `\citet`/`\citep` used correctly; nothing after the cutoff. OK.
8. Referee view: the contributions match the evidence; related work covers tokenization effects, marginal-likelihood work, token healing/alignment, FIM, token-free models and heterogeneous ensembles; the limitations are frank.

## Non-blocking findings (for the next version)
- N1 (report, `template.tex` intro, p. 2 l. 042): "whose correct continuation is `aa`". Per Fig. 1 and its caption, the prompt already ends in `a`; the correct continuation is `a` (completing `aa`). The intro contradicts the caption.
- N2 (build): loading `algorithm` (float) after `hyperref` causes 9 pdfTeX "destination with the same identifier (figure.N / table.N)" warnings. I checked that links still resolve to the same pages, so this is cosmetic. Moving `\usepackage{hyperref}\usepackage{url}` after `algpseudocode` removes all of them (tested). The PR body's "no warnings" claim is therefore inaccurate.

## Conclusion
APPROVE. The version meets the objective and supports its claims. N1–N2 should be fixed before `final`.

## Update: head moved to `c76bc2b844ad0a4dc6b28cdf0b509201d1b97616` before approval
Diff `4ee06fe..c76bc2b` (paper-repo #9, answering story-repo #6) touches only `template.tex` and `template.pdf`. Style files, figures and `references.bib` are unchanged.
- New title "Removing Tokenization Bias at Inference Time with Cover Encodings" (two lines). OK.
- **N1 fixed**: the intro now says the correct continuation is the character `a`, completing `aa`, which matches Fig. 1.
- Sec. 3.4: the cost note now says each history `encode(x_1^{n-i})` needs its own forward pass and shares the KV cache of common leading tokens. This is correct and fixes an earlier overstatement.
- Sec. 3.5 and Setup: beam search is framed as an extension ("our logs record only the beam widths used"); the GPT-2 is now described as "trained on synthetic data from the third-order chain", per the log; voting is limited to "where it was evaluated". OK.
- New Appendix A (implementation). It has no measurements and says so. I checked the derivations. Validity test `encode(x_1^j t) = (encode(x_1^j), t)` is Definition 1. The claim that `encode(x_1^n)` = canonical history + one token holds under Assumption 1 (a positive-probability prefix is valid). Normalizing by `P(x_1^{n+1})` is correct. The beam/ensemble description is consistent with Eqs. 5–6.
- Fresh build from a clean archive: rc=0, no undefined refs or overfull boxes, 14 pages. Main text ends on p. 10, references on pp. 11–13, appendix on p. 14. Text of the shipped PDF = text of the fresh build (md5 of pdftotext equal). Pages 1 and 14 inspected as rendered.
- **N2 still open** (non-blocking): the 9 cosmetic hyperref duplicate-destination warnings remain.

Conclusion at `c76bc2b`: **APPROVE**. N2 is left for the next version.

## Update: head moved to `ea1dc1576db2fec05729cffceb7fd03b0ef8e401` before approval
Diff `c76bc2b..ea1dc15` (paper-repo #12, answering experiment-repo #11 and figtab-repo #10) touches `template.tex` and `template.pdf` only.
- Sec. 3.3: "a cover encoding of positive probability satisfies P(t_1^{k-1}) ≥ P(t_1^k) > 0". This is a correct tightening; zero-probability covers are explicitly ignored.
- Algorithm 1 now returns "all cover encodings of x_1^n with positive probability". This is consistent with the lemma.
- Fig. 3 caption: "The figure counts iterations from zero". I checked this against the image, whose right panel uses x_{n-i}^n and encode(x_1^{n-i-1}). It is accurate.
- Fresh build: rc=0, no undefined refs or overfull boxes, 14 pages; main text ends on p. 10, references start on p. 11; the shipped PDF text equals the fresh build.

Conclusion at `ea1dc15`: **APPROVE**. N2 (cosmetic hyperref warnings) is still open and non-blocking.
