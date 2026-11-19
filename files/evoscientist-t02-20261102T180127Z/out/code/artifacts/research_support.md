# Research support for an autonomous grokking-size experiment

**Verified on 2026-11-02 UTC. Research only; no experiment implementation or delegation.**

## Scope, independence and evidence

Only the seven specified arXiv papers and direct official NeurIPS 2026 author/style instructions were fetched. No topical/keyword web search, citation-graph traversal, recommendations, aggregators, unrelated paper downloads, or repository inspection was performed. The internal memory preflight found no observations and supplied no research information. Abstract HTML for the seven allowlisted IDs was archived but not rendered/read; paper evidence below comes from their PDFs. Author-reported code availability is distinguished from independently checked code.

**Accidental embedded-material exposure is disclosed, not concealed:** an allowlisted-paper bibliography, an official handbook further-reading list, template example bibliography entries, and an incidental official-navigation URL appeared in broad text excerpts. Reading of those sections stopped upon recognition; no destination was followed and none was used for evidence or forbidden-paper identity inference. Embedded related-work citations and author code URLs were not treated as additional consulted sources. Details, source URLs and extent: `/work/artifacts/literature/independence_audit.md`. No forbidden-paper identity was guessed.

All seven PDF originals, verbatim extracted texts and bibliography-filtered reading copies are saved under `/work/artifacts/literature/`. Extraction is text-based; pypdf reported skipped excessive form-XObject content, so plots have not been quantitatively digitized. The original PDFs remain authoritative. These are focused methods/results readings, not exhaustive proof audits. Novelty claims below are bounded by this restricted source set.

## Key findings

### 1. A generic size-dependent grokking result is already prior work

- **Training-dataset size:** the original paper already measures data-efficiency curves and steps to 99% generalization. Smaller train sets can require dramatically longer optimization. A finite-budget failure cannot establish a true impossibility threshold [1, pp. 1–3, 6–7].
- **Model size:** *Unifying Grokking and Double Descent* explicitly demonstrates **model-wise grokking** using embedding-width-by-training-step heatmaps and long-training cross-sections [6, pp. 4, 8]. A width sweep or a model-size grokking transition by itself is not novel even within this allowlist.
- **Critical dataset size and history:** circuit-efficiency work already studies a generalization/memorization-efficiency crossover, semi-grokking and ungrokking. Its appendix also cautions that apparent boundaries depend on initialization and training history [4, pp. 6–10, 17].

A defensible experiment must distinguish **parameter count/width**, **training-example count**, **parameter norm**, and **optimization/compute budget**. The allowlisted papers do not establish a universal single critical size, nor certify novelty for any proposed extension against unconsulted work.

### 2. Keep the baseline recipes separate

| Source | Dataset and split | Architecture | Optimization and budget | Important caveat |
|---|---|---|---|---|
| Original grokking [1] | Symbolic binary tables, commonly p=97; random train fraction, all remaining equations validation; modular division excludes zero denominators | Causal decoder-only, 2 layers, width 128, 4 heads; about 400k non-embedding parameters | Typical AdamW: LR 1e-3, decay 1, betas .9/.98; 10-update warmup; batch min(512, half train set); 100k updates | Famous very-late division example instead uses Adam/no decay and 1M updates; learning-time curves use 500k updates and 7 seeds |
| Mechanistic baseline [2] | Addition mod 113: 12,769 ordered pairs; 30% train, remaining pairs test; input `a b =` | 1-layer ReLU transformer, width 128, 4 heads of size 32, MLP 512; learned positions; no LayerNorm; untied embed/unembed | Full-batch AdamW, LR 1e-3, decay 1; 40k epochs/updates; displayed learning curves over 5 seeds | Useful compact baseline; missing details must be explicitly fixed rather than silently attributed to the paper |
| Circuit efficiency [4] | Addition mod 113; random train fraction; Appendix A input `a op b =`, final-answer CE | 1 layer, width 128, 4 heads of size 32, MLP 512; learned positions, untied embed/unembed | Full-batch AdamW, LR 1e-3, decay 1, betas .9/.98 unless varied | Operator token makes input format different from [2]; do not call a hybrid an exact reproduction |
| Model-wise grokking [6] | Division mod 97, answer-only loss/accuracy | 2 layers, default width 128 unless swept, **1 head** | AdamW, LR 1e-3, decay **1e-5**, betas .9/.98; typically 400k updates | Appendix as read does not specify all split/batch/seed details; text sometimes says epochs while appendix says updates |

The source PDFs, not external code, support these recipes. P=97 division has 97×96=9,312 valid ordered inputs; p=113 addition has 113²=12,769. Training only a subset and evaluating the complement is interpolation in a finite operation table, not evidence of generalization to a new modulus or arbitrary algorithms.

### 3. Accuracy alone can hide or manufacture a transition

- Fourier restricted/excluded loss, Fourier sparsity and weight norms can expose gradual circuit formation before the apparent accuracy jump [2, pp. 8–9]. Restricting to final-model frequencies is **retrospective**; an online prediction claim needs a training-only/frozen frequency-selection rule.
- Circuit-efficiency projections are imperfect: memorization/generalization logits can correlate, and raw correct logits omit wrong-class logits [4, p. 22]. Prefer reporting complete held-out CE plus gauge-invariant margins and carefully controlled norm–loss comparisons, not a raw correct-logit/norm ratio as decisive proof.
- Regression 'accuracy' depends on arbitrary tolerance and can look sharply grokking even when continuous loss is less dramatic [5, p. 3]. Always retain continuous held-out loss.
- Semi-grokking may be a transient plateau lasting millions of full-batch epochs. [4] uses 200 runs around training sizes 1,500–2,050 and reports at least six clear examples at its finite horizon; this is not a cheap default size-sweep baseline [4, pp. 9–10].

**Recommended evaluation protocol (our proposal, not a claim the papers all used it):**

1. Save train/validation/test membership and initialization seeds; match splits across widths. Historical reproduction may evaluate the train complement, but autonomous selection on that complement makes it validation data. For new adaptive experimentation, reserve a genuinely untouched final test before tuning (e.g. 30/10/60% train/validation/test, explicitly distinguished from the historical 30/70% split).
2. Record train and held-out CE/accuracy, parameter norms, update count, full-batch-equivalent epochs, examples processed, wall time and compute. Use both update-matched and compute-matched width comparisons.
3. Predeclare first and sustained train/validation threshold events, for example ≥99% accuracy sustained for three scheduled evaluations. Report delay, successes/total seeds, final losses, per-seed trajectories and censored times. Report final test trajectories only under a frozen, nonadaptive protocol. Do not discard non-grokking seeds or average their curves into a fictitious gradual transition.
4. Use a fixed maximum budget and evaluation cadence; record 'not reached by T' as **right-censored**, not infinite grokking time or a proven critical boundary. No train-loss early stopping for this question.
5. Keep confidence calibration separate. No temperature-fitting/ECE/Brier evaluation protocol was established in the sections read. If added, fit any temperature only on validation, predefine ECE bins or another metric, and retain raw uncalibrated CE. Accuracy and CE should not be mislabeled as full calibration analysis.
6. Fixed-width or fixed-norm does not mean fixed compute, and fixed initial norm does not ensure equal feature-learning dynamics. Report actual parameter counts, initialization/output scales and optimizer conventions.

### 4. Weight decay is useful, not a universal necessary mechanism

Omnigrok studies initialization scaling and LU reduced-loss landscapes, and induces weaker grokking on MNIST/IMDb/QM9 with specific modified protocols [3]. However, lazy-to-rich work demonstrates delayed generalization under vanilla GD, **zero decay and increasing norm** [5]. Therefore an account relying universally on shrinking norm is unsupported.

For a laziness control, [5, Appendix 8.1] uses the centered predictor

`f_tilde(theta,x) = alpha * (f(theta,x) - f(theta_initial,x))`

and **GD** LR `eta0 / alpha²` to match initial timescales. Applying output scale without centering/LR control confounds the mechanism. The same paper explicitly calls its AdamW analysis more speculative and describes lazy-to-rich transition as sufficient, not necessary in general settings [5, p. 20]. Do not transplant the GD LR law to AdamW as an established identity.

AdamW matters independently: adaptive-gradient L2 regularization and decoupled shrinkage are not equivalent [7, pp. 1–3]. Record the actual update equation, betas/epsilon, schedule and decayed parameter groups. The paper's coefficient convention is not automatically identical to a framework `weight_decay` keyword. For an implementation defined by shrinkage `theta <- (1 - eta_t*lambda)*theta`, report cumulative decay `product_t(1-eta_t*lambda)` or its log in addition to nominal lambda. That convention is an explicit example, not a claim that every paper/API uses it.

## Recommended next experiments

These are **planning recommendations**, not completed experiments or certified novel contributions.

1. **Anchor reproduction, then width-by-time pilot.** Use [2]'s one-layer mod-113 setup at width 128, MLP 512, four heads, no LayerNorm, untied embeddings, full-batch AdamW LR 1e-3/decay 1/40k updates. Declare any additionally chosen optimizer settings. Then pilot widths 64/128/256 with MLP=4×width and four heads, three matched seeds; head dimensions consequently change. Log initialization/output/kernel diagnostics rather than assuming width isolates capacity. Freeze selection rules before expanding to at least five seeds for key comparisons. Expected use: establish whether an apparent size effect persists beyond budget/split/initialization variability. This reproduces/extends existing model-wise work, not a novelty claim.
2. **Disambiguate mechanism from width-induced laziness.** Compare nonlinear models to a frozen-feature/linearized baseline on a fixed small diagnostic subset; track relative parameter movement, Fourier progress and kernel–target alignment. Add a separately controlled, centered-output/GD-scale experiment based on [5] if feasible. Expected use: distinguish slower feature learning from an absolute lack of representational capacity. A scalar-output dense NTK over all 12,769 inputs already contains ~163M entries (~0.65 GB float32), before Jacobian/multiclass overhead; subset diagnostics must be labeled as such.
3. **Only after the anchor works, vary train-set size and training history.** Keep a fixed final test outside a nested training pool, vary training counts at fixed model sizes, and extend selected near-boundary runs under a predeclared budget. Keep any full-table-pretraining ungrokking experiment separate: its later 'test' points were already seen, so it measures retention, not fresh held-out generalization. Expected use: expose right-censoring/history effects rather than overclaiming a unique critical size [1,4].

## Official conference template: verified preferred release

**Selected: current official NeurIPS 2026 package linked by the 2026 CFP on 2026-11-02.** The requested `/PaperInformation/StyleFiles` URL returned HTTP 404, but the direct official CFP supplied a working official media ZIP. Thus no older template or unofficial mirror was substituted and the ICLR fallback was unnecessary. This establishes the currently served preferred release; no claim is made about release-order comparisons with uninspected conference editions.

### Exact provenance and local paths

- Official author instructions: https://neurips.cc/Conferences/2026/CallForPapers [8].
- Exact package: https://media.neurips.cc/Conferences/NeurIPS2026/Formatting_Instructions_For_NeurIPS_2026.zip [9].
- Download completed **2026-11-02T18:07:41.522938+00:00**; 20,259 bytes; SHA256 **`82473931e3ef710fcd3f4a8cd4119b9de32e56825f90f9e5a6d55f2d01b817d9`**.
- Preserved original ZIP: `/work/official_template/Formatting_Instructions_For_NeurIPS_2026.zip`.
- Original extracted files: `/work/official_template/original_package/neurips_2026.sty`, `neurips_2026.tex`, **`checklist.tex`**. All three were checked byte-for-byte against their archive members; none was edited. Style internally identifies `2026-01-29`; that is its declared style version, not an independently verified release timestamp.
- Independent official policy cross-check: https://neurips.cc/Conferences/2026/MainTrackHandbook [10], Authors → Paper Formatting Instructions.
- Full URL/UTC/status/response-header/hash records: `/work/official_template/download_manifest.json`. Extracted hashes: `package_inventory.json`. Detailed requirement notes: `requirements.md`. No compiled template PDF was provided in this ZIP or generated here.

### Requirements verified from package and official handbook

| Requirement | Verified rule |
|---|---|
| **Main-page limit** | **9 content pages at submission, including figures and tables.** Handbook allows **one additional content page after acceptance**, i.e. 10 for camera-ready; do not use that at submission. |
| Exempt pages | References, optional technical appendices and mandatory checklist. General template mentions acknowledgments as exempt, but handbook prohibits them at anonymous submission. |
| PDF packaging | Single PDF, maximum **50 MB**; suggested order content → references → appendices → checklist. No separate appendix PDF. Appendices have no page limit, but core paper must stand alone. |
| Style | Current unmodified `neurips_2026.sty`; default/main for anonymous submission; omit `final` and `preprint`. Do not shrink margins or fonts. |
| **Checklist** | **Mandatory; omission causes desk rejection.** Outside content-page limit, after references and optional appendices; template uses `\input{checklist.tex}`. |
| Checklist completion | All 16 questions: Yes/No/NA using official macros, each with **1–2-sentence justification**, including NA. Remove introductory instruction block in a working copy; keep heading, questions and guidelines; do not rewrite questions. Include revised checklist in final paper. |
| Autonomous-research relevance | Question 16 requires declaring important/original/nonstandard core-method LLM use. Writing/editing/formatting-only use without methodological impact is exempt. Assess autonomous experimentation explicitly. |

The checklist also calls for experimental reproducibility, exact split/hyperparameter choices, defined error bars, hardware/runtime/memory, and compute including preliminary/failed experiments. It encourages code release but does not universally require it; some reasonable avenue for reproducibility is required. Preserve the downloaded originals and create a separate working manuscript when writing begins.

## Artifact inventory and paper provenance

- **This self-contained report:** `/work/artifacts/research_support.md`.
- **Detailed per-paper notes:** `/work/artifacts/literature/reading_notes.md`.
- **Originals and texts:** `/work/artifacts/literature/{arxiv_id}.pdf`, `.txt`, `.reading.txt`, `.abs.html` for all seven IDs.
- **Literature provenance:** `/work/artifacts/literature/download_manifest.json` includes exact requested/final URLs, UTC times, SHA256, sizes and PDF page counts. All seven PDFs downloaded successfully on 2026-11-02 between 18:04:50 and 18:05:14 UTC.
- **Independence/extraction audit:** `/work/artifacts/literature/independence_audit.md`.
- **Official originals, instructions and manifests:** `/work/official_template/` as above.
- **Offline integrity validation:** `/work/artifacts/validation_result.json` (PASS); `/work/artifacts/artifact_checksums.json` records file hashes. All 14 literature downloads and official successful downloads match their provenance hashes; the three extracted package members match the original ZIP.
- Acquisition/extraction helper scripts are retained for provenance only; no model/training implementation was written.

| Paper | PDF version observed | SHA256 of original PDF |
|---|---|---|
| 2201.02177 | v1, 2022-01-06 | `305dbd1256e1ac198dde517dda42b4f0a7eb9a9d3f4c03527c125b03eb9c62fc` |
| 2301.05217 | v3, 2023-10-19 | `93dcdafc2ecf75d31ab2e32e74cdc11e2e488fec42edfef58ad3d4b6515bcd5f` |
| 2210.01117 | v2, 2023-03-23 | `b13aa4d19d7dedfac98a79f7918535e9cd34b0bc9f565322bd2df56fff8e7b3f` |
| 2309.02390 | v1, 2023-09-05 | `7472d0dc38f9fef0039e984f32c952600dd71fbb2299cc79ce0e7a5af6b89eb0` |
| 2310.06110 | v3, 2024-04-11 | `dcea3e477ab35167281ae310983a2a0ed8cd50b3fd725c8d6747aecd05bef348` |
| 2303.06173 | v1, 2023-03-10 | `bc6be2681ccd0e0c39d3b4eb640af727011aa8f30a2ede233356b61ceb7e033c` |
| 1711.05101 | v3, 2019-01-04 | `9d5af48931e773d6983d167e15c06ef594475b751c1f263827f5ed3c7a00d0d8` |

### Sources actually consulted

Only the following paper PDFs and official author/style documents support this report. No bibliography entries or author-linked code destinations count as additional consulted sources.

[1] Power et al., *Grokking: Generalization Beyond Overfitting on Small Algorithmic Datasets*: https://arxiv.org/pdf/2201.02177

[2] Nanda et al., *Progress Measures for Grokking via Mechanistic Interpretability*: https://arxiv.org/pdf/2301.05217

[3] Liu, Michaud and Tegmark, *Omnigrok: Grokking Beyond Algorithmic Data*: https://arxiv.org/pdf/2210.01117

[4] Varma et al., *Explaining grokking through circuit efficiency*: https://arxiv.org/pdf/2309.02390

[5] Kumar et al., *Grokking as the transition from lazy to rich training dynamics*: https://arxiv.org/pdf/2310.06110

[6] Davies, Langosco and Krueger, *Unifying Grokking and Double Descent*: https://arxiv.org/pdf/2303.06173

[7] Loshchilov and Hutter, *Decoupled Weight Decay Regularization*: https://arxiv.org/pdf/1711.05101

[8] Official *NeurIPS 2026 Call for Papers*: https://neurips.cc/Conferences/2026/CallForPapers

[9] Official *Formatting Instructions For NeurIPS 2026*, ZIP containing style, template and checklist: https://media.neurips.cc/Conferences/NeurIPS2026/Formatting_Instructions_For_NeurIPS_2026.zip

[10] Official *NeurIPS 2026 Main Track Handbook*, author formatting section: https://neurips.cc/Conferences/2026/MainTrackHandbook

Failed direct endpoint (not substantive evidence): https://neurips.cc/Conferences/2026/PaperInformation/StyleFiles — 404; error body/hash archived.
