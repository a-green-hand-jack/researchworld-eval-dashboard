# Restricted source verification

Verified 2026-11-04 UTC. Scope: only the five supplied arXiv papers, the supplied JMLR paper and its direct PDF, and relevant official NeurIPS 2026 author/style resources. No literature search, aggregator, citation traversal, related-paper navigation, recommendation service, or experiment implementation was used. Bibliographic mentions inside permitted PDFs were not followed. No known prohibited-content encounter was identified; no identity was inferred or guessed.

## Retrieval and reading record

All ten HTTP requests returned 200 without redirects. Every requested URL, purpose, UTC time, status, content type, byte count, SHA-256 and destination is in `/work/artifacts/literature_access.tsv`. No external assets in HTML were loaded. All six starter PDFs are saved in `/work/literature/`.

The PDF attachment reader rendered `1705.07874.pdf` earlier, but repeatedly truncated `2202.01602.pdf` without delivering readable content. Those failed reading attempts are not counted. Required reading was completed using text extracted **offline from the downloaded PDF content streams**, including compressed objects, page-tree ordering and font ToUnicode maps. These are actual PDF texts, not abstract-page metadata. The local `.txt` files retain PDF page markers. Extraction does not faithfully reconstruct equations, tables, figure geometry, all font glyphs or reading order; precise mathematical claims/proofs were not audited. Extraction of a whole PDF is not a claim that its whole text was read. Read extents below are deliberately bounded.

### [1] arXiv 1705.07874
- Source accessed: https://arxiv.org/pdf/1705.07874
- Files: `/work/literature/1705.07874.pdf`, `/work/literature/1705.07874.txt` (10 PDF pages).
- Title/authors from actual text: **A Unified Approach to Interpreting Model Predictions**, Scott M. Lundberg and Su-In Lee. PDF identifies NIPS 2017.
- Read extent: earlier PDF render supplied all 10 pages; current verifiable substantive notes use selected text in PDF pp. 1–6: title/abstract/introduction, additive attribution definition, Sections 3 and 4, and opening Kernel SHAP derivation. The local text was read at lines 1–270 and 301–555; the intervening portion of p. 3 was not reread. No full proof or experiment reproduction claimed.
- Supported summary: defines additive feature attribution models; presents uniqueness under local accuracy, missingness and consistency for a **given simplified-input mapping** (Section 3); defines SHAP through conditional expectations and derives Kernel SHAP as weighted regression (Section 4).
- Important boundary: axiomatic consistency is a particular monotonicity requirement under model changes, not a general guarantee of reproducibility under resampling. Section 4, equations 9–12 distinguish conditional expectation from a feature-independence approximation and a further model-linearity approximation. Do not silently equate these value functions.
- Code: the PDF reports `https://github.com/slundberg/shap`; not visited or verified. Dataset splits/calibration and empirical results were not checked for these notes.

### [2] arXiv 2202.01602
- Source accessed: https://arxiv.org/pdf/2202.01602
- Files: `/work/literature/2202.01602.pdf`, `/work/literature/2202.01602.txt` (34 PDF pages).
- Title/authors: **The Disagreement Problem in Explainable Machine Learning: A Practitioner's Perspective**, Satyapriya Krishna, Tessa Han, Alex Gu, Steven Wu, Shahin Jabbari, Himabindu Lakkaraju. Downloaded PDF says TMLR 06/2024; do not describe its contents as necessarily the original 2022 version.
- Read extent: PDF pp. 1–9 and opening of p. 10, local text lines 1–526: abstract/introduction, related-work text encountered within the starter, practitioner study, metric definitions, empirical setup, tabular findings and opening text-data findings. References and appendix protocols were not inspected.
- Supported summary: studies disagreement **between different explanation methods for the same prediction**, not a universal correctness test. First interviews involve 25 data scientists; the paper also reports a separate 25-person online study. The interviewed sample is drawn from three US technology/financial-services companies; it is not a population-wide prevalence estimate.
- Six metrics (Section 3.2): top-k feature overlap, exact rank agreement, sign agreement, signed rank agreement, Spearman rank correlation, and pairwise rank agreement. Top-k is generally based on attribution magnitude; lower agreement indicates stronger disagreement. Distinguish strict position matching from rank correlation. Agreement alone does not establish correctness.
- Datasets reported in Section 4.1: COMPAS (4,937 defendants, seven features; target here is COMPAS risk category), German Credit (1,000 applicants, 20 features), AG_News and ImageNet-1k. The paper says it uses PASCAL VOC 2012 segmentation maps for superpixels; the mapping/preprocessing was not independently validated.
- Models: logistic regression, feed-forward neural network, random forest and gradient-boosted trees for tabular data; LSTM for text; pretrained ResNet-18 for images.
- Explainers: LIME, KernelSHAP, Vanilla Gradient, Gradient times Input, Integrated Gradients and SmoothGrad. Sampling-based explainers are run to stated convergence or with substantially enlarged sample counts. Image comparisons must respect superpixel versus pixel granularity.
- Evaluation: metrics averaged over test points; COMPAS example uses k=5 of seven features; AG_News example uses k=11. Figure 1 describes non-trivial disagreement thresholds of <0.75 for agreement fractions and <0.50 for rank correlation; these are the authors' interpretation thresholds, not calibrated probabilities. Figure 1 reports standard errors 0–0.01. Exact train/test proportions, seed schedule, background/baseline details, model calibration and code availability were not verified in the read extent.

### [3] arXiv 2006.16234
- Source accessed: https://arxiv.org/pdf/2006.16234
- Files: `/work/literature/2006.16234.pdf`, `/work/literature/2006.16234.txt` (7 PDF pages).
- Title/authors: **True to the Model or True to the Data?**, Hugh Chen, Joseph D. Janizek, Scott Lundberg, Su-In Lee.
- Read extent: PDF pp. 1–4 and beginning of p. 5, local text lines 1–595: abstract, value-function distinction, linear-model method, correlation experiments, NHANES illustration and opening lending example. Later biological example and conclusions were not read.
- Supported summary: argues that observational versus interventional value functions are application-dependent choices. Observational conditioning can give credit to correlated features unused by the model; breaking dependence can evaluate off-manifold inputs. Neither is uniformly preferable.
- Linear method: observational estimation assumes multivariate normal inputs and estimates conditional expectations using a mean/covariance model; interventional attributions reduce to coefficient times deviation from feature mean. Exact matrix formulas are not transcribed because extraction degrades mathematical layout.
- Protocol inspected: three-feature Gaussian simulation with model coefficients 1, 2, 3 and explained input [1,1,1]; independence, pair-correlation and common off-diagonal-correlation settings. Figure 1 reports standard deviations from **20 estimates** at each fixed combination-sample count. Higher correlation is reported to slow convergence in these simulations, not proved here as a universal rule.
- NHANES example: 25,535 individuals, 1999–2014 data, five-year mortality with status collected in 2015 and unknown-status cases excluded. Includes/excludes BMI in explanations while the example model uses four other features. LendingClub example evaluates changes in model-predicted log odds when features are set to their means; that is not verified real-world causal recourse.
- Code: footnote reports `https://github.com/slundberg/shap/blob/master/shap/explainers/linear.py`; not visited or verified. Exact splits, random-seed schedule and probability calibration were not verified.

### [4] arXiv 2410.01917
- Source accessed: https://arxiv.org/pdf/2410.01917
- Files: `/work/literature/2410.01917.pdf`, `/work/literature/2410.01917.txt` (29 PDF pages).
- Title/authors: **Provably Accurate Shapley Value Estimation via Leverage Score Sampling**, Christopher Musco and R. Teal Witter. PDF identifies ICLR 2025; this is the current response at the unversioned URL, not necessarily the original 2024 submission.
- Read extent: PDF pp. 1–4, plus Section 5 on p. 9, p. 10 and opening of p. 11; local text lines 1–245 and 641–825. Middle algorithm/proof sections and appendices were not read; the read at line 641 includes the preceding paragraph tail. No theorem proof audit claimed.
- Supported summary: Leverage SHAP modifies Kernel SHAP sampling using leverage scores. For the projected design, the paper gives subset probability proportional to the inverse binomial coefficient, realized by sampling subset size uniformly and then a subset uniformly at that size. It also combines paired sampling and sampling without replacement.
- Guarantee boundary: the near-linear evaluation statement suppresses accuracy/failure-probability dependence. Theorem 1.1 is primarily a regression-objective guarantee, with a separate attribution-error discussion; it is not an unconditional relative-error guarantee for every attribution or for a changing value function/background. The work fixes the value function v.
- Evaluation (Section 5): relative squared l2 error between estimated and ground-truth attribution vectors; exact Tree SHAP ground truth for XGBoost models with 100 estimators and max depth 4 (other parameters default). Need match the same value function/baseline semantics when using such ground truth.
- Datasets named in Table 1: IRIS, California, Diabetes, Adult, Correlated, Independent, NHANES, Communities. Compared with plain Kernel SHAP and the optimized SHAP-library Kernel SHAP; permutation and ablations are reported in appendices but were not inspected directly.
- Budgets m=5n,10n,20n,...,160n; Figure 3 uses median and first/third quartiles over **100 random runs**. Table 1 is at m=10n. Authors report approximately 50% average error reduction versus optimized Kernel SHAP; treat this as a result of their reported benchmark, not a universal performance guarantee. Their warning about negative mean-minus-standard-deviation intervals motivates median/quantile reporting for nonnegative errors.
- Code: PDF footnote reports `github.com/rtealwitter/leverageshap`; not visited or execution-verified. Exact dataset splits, explained-point selection, library versions and calibration were not verified in the read extent.

### [5] arXiv 2204.11351 — additional bounded reading
- Source accessed: https://arxiv.org/pdf/2204.11351
- Files: `/work/literature/2204.11351.pdf`, `/work/literature/2204.11351.txt` (8 PDF pages).
- Title/authors: **An Empirical Study of the Effect of Background Data Size on the Stability of SHapley Additive exPlanations (SHAP) for Deep Learning Models**, Han Yuan, Mingxuan Liu, Lican Kang, Chenkui Miao, Ying Wu. PDF identifies a Tiny Paper at ICLR 2023.
- Read extent: PDF p. 1 and beginning of p. 2 through opening Section 2.1, local text lines 1–125; experiment tables/appendices were not read.
- Bounded summary: abstract reports background-resampling effects for DeepExplainer/ANNs on MIMIC-III, smaller fluctuations with larger background size, and more stable extreme than middle ranks in its setting. Intro names BLEU and Jaccard ranking assessments. These claims have not been independently reproduced and must not be generalized to all explainers or datasets. A background-size change can also change the reference expectation/estimand.
- Code: PDF reports `https://github.com/Han-Yuan-Med/shap-bg-size`; not visited. No numerical optimal background size, split or calibration claim verified. A broken Appendix reference is visible in the text.

### [6] supplied JMLR paper — additional bounded reading
- Sources accessed: https://jmlr.org/papers/v18/17-514.html and its direct same-paper link https://jmlr.org/papers/volume18/17-514/17-514.pdf
- Files: `/work/literature/jmlr_17-514.html`, `/work/literature/jmlr_17-514.pdf`, `/work/literature/jmlr_17-514.txt` (54 PDF pages).
- Title/authors: **On the Stability of Feature Selection Algorithms**, Sarah Nogueira, Konstantinos Sechidis, Gavin Brown. HTML and PDF identify JMLR 18(174):1–54, 2018.
- Read extent: supplied HTML title/abstract and direct PDF link; actual PDF pp. 1–2 and opening of p. 3 (lines 1–155). Later estimators, proofs, experiments and code were not read/verified.
- Bounded summary: studies feature-**subset** selection under data/stochastic perturbations; proposes a property-based statistical treatment permitting confidence intervals and hypothesis tests. It explicitly leaves weighting/ranking representations beyond thresholded subsets for future work. Do not claim its inference automatically transfers to attribution magnitudes, dependent repeated runs or arbitrary rank metrics. No formula, finite-sample coverage or significance calibration is verified here.

## [7–9] Official NeurIPS 2026 style and requirements

### Official provenance and files
1. Accessed official Call for Papers: https://neurips.cc/Conferences/2026/CallForPapers
   - Saved original `/work/paper/style/neurips2026_call_for_papers.html`.
   - Page identifies the Fortieth Annual Conference, NeurIPS 2026 and directly links the ZIP below and Main Track Handbook. No guessed template URL was needed.
2. Followed its official **Paper template** link: https://media.neurips.cc/Conferences/NeurIPS2026/Formatting_Instructions_For_NeurIPS_2026.zip
   - Saved `/work/paper/style/Formatting_Instructions_For_NeurIPS_2026.zip`.
   - ZIP SHA-256: `82473931e3ef710fcd3f4a8cd4119b9de32e56825f90f9e5a6d55f2d01b817d9`.
   - Safe extraction yielded exactly `neurips_2026.tex`, `neurips_2026.sty`, `checklist.tex`, directly under `/work/paper/style/`. Extracted bytes were checked identical to the ZIP members; official files have not been edited.
   - Style declares `\ProvidesPackage{neurips_2026}[2026-01-29 NeurIPS 2026 submission/camera-ready style file]` and comments “last revision: January 2026”. This is the currently linked official 2026 bundle as retrieved, not an assertion about unpublished revisions.
3. Followed the Call for Papers' official Main Track Handbook link: https://neurips.cc/Conferences/2026/MainTrackHandbook
   - Original `/work/paper/style/neurips2026_main_track_handbook.html`; local text derivative with the same stem.
4. NeurIPS bundle was available; **no ICML fallback was accessed**.

### Verified requirements
- **Submission main text: nine content pages including figures and tables.** Handbook, Authors → Paper Formatting Instructions: “The main text of a submitted paper is limited to nine content pages, including all figures and tables.” Local handbook text lines 187–195; `neurips_2026.tex` lines 127–136 independently specify nine pages including figures.
- **Camera-ready: one additional content page (ten total).** Same handbook paragraph; do not confuse the camera-ready allowance with the submission limit.
- **One PDF**, suggested order: main content → references → optional textual appendices → paper checklist. Handbook local text lines 189–194.
- **Checklist mandatory and outside the content-page limit**, placed **after references and after optional supplementary material**. `checklist.tex` lines 3–5: “The checklist should follow the references and follow the (optional) supplemental material. The checklist does NOT count towards the page limit.” Missing checklist is stated to cause desk rejection.
- Template confirms placement: references, `\appendix`, optional technical material, then `\newpage` and `\input{checklist.tex}` (`neurips_2026.tex`, final lines 478–496). Technical appendices have no page limit; main claims must stand alone without them. Do not upload textual appendices as a separate PDF.
- `neurips_2026.tex` excludes extra pages containing acknowledgments, references, checklist and optional technical appendices from content pages. However **omit acknowledgments in anonymous submission**; include them only in final paper, before references.
- Use the current year style without margin/font tweaks. Default `\usepackage{neurips_2026}` equals anonymous main-track mode; `[main]` is explicit; add `[main, final]` only after acceptance.
- Checklist answers use `\answerYes{}`, `\answerNo{}`, `\answerNA{}` with short justifications; remove the instruction block when authoring but preserve questions and guidelines. Original retrieved checklist remains unchanged here.
- Maximum submission PDF size: 50 MB, per handbook.
- Compilation was not attempted; this task verifies official files and instructions, not a local TeX installation or rendered manuscript.

## Access errors and limits
- **Source-access errors: none.** All ten allowlisted HTTP requests returned 200, and all successful saved-body SHA-256 values match the access log.
- Local tooling issues only: PDF attachment read truncation; unavailable third-party PDF extraction tools/packages; workspace shell path restrictions; one exploratory command quoting error; malformed tool calls rejected before execution. No extra URL was accessed by those failures. Offline source-reading helpers were used instead; no dependencies were downloaded.
- The unversioned arXiv requests are archived by exact bytes/SHA-256 in the log; PDF-declared venue/year may postdate an identifier's first submission year.
- Code/dataset links mentioned inside papers were **not followed**. Their existence in PDF text is not a verification that repositories are live, usable, licensed or reproducible.
- No experiments were implemented or run. The Python helpers perform restricted downloading, offline document decoding and verification only. No broad claim about SHAP reliability/stability is supported by this bounded source check.
