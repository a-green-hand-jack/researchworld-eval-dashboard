# Restricted starter-paper reading notes

Prepared 2026-11-03 UTC. **Evidence boundary: the seven user-supplied original papers only.** No topical web search, citation/recommendation service, citing page, repository, or unsupplied paper was accessed. Venue guidelines/templates were obtained separately; see `template/PROVENANCE.md`. No experiment implementation or execution was performed.

## Reading and provenance conventions

- `[1]`–`[7]` below refer only to the supplied papers. Page numbers are **1-indexed PDF pages**, not arXiv HTML locations. Claims below are readings of the originals, not independent reproductions.
- Original downloaded PDFs are `literature/<arxiv-id>.pdf`; `literature/downloads.json` records retrieval URL/time, byte count, and SHA-256. The unversioned allowed PDF endpoints returned the versions recorded below; those bytes, not a presumed first arXiv version, define this reading.
- `literature/<arxiv-id>.pages.json` preserves per-page text extraction. All seven title-page abstracts and the method/results pages indicated below were actually read. Extraction warned that some highly complex graphic content was skipped; figure curves were not digitized. Mathematical typography in extracted text is imperfect, so no precise scaling-law coefficient is inferred from it.
- Bibliographies and related-work passages embedded in the allowed originals were encountered during extraction/reading, but were not used as an expanded source set and **no reference was followed**. No known forbidden external-content exposure occurred. Because the excluded paper is undisclosed, this is an access-boundary audit, not a claim to have identified that paper.

## Key Findings

1. **A width effect/model-wise grokking is already a reported original result.** Davies, Langosco, and Krueger vary transformer embedding dimension on modular division and show train/test loss over width and training steps, including a 400k-step width cross-section. A proposed width study must not claim the first observation of model-wise grokking. Their pattern-speed interpretation is a conceptual framework plus empirical evidence, not a universal quantitative width law [6, pp. 1–5, 8–9].
2. **Accuracy alone hides important dynamics.** Power et al. demonstrate extremely delayed held-out generalization; Nanda et al. show that Fourier-based progress measures reveal circuit formation before test accuracy improves; Kumar et al. show that regression “accuracy” can be made to look like grokking by selecting an error threshold. Log train/held-out loss and accuracy, and do not terminate when train loss first becomes small [1, pp. 1–4, 7; 2, pp. 7–9; 5, pp. 3, 24].
3. **Weight decay is useful but not universally necessary.** Power et al. include Adam/no-decay examples; Varma et al. explicitly identify the absence of decay as a limitation of their explanation; Kumar et al. provide vanilla-GD/no-decay examples with increasing parameter norm. Do not turn the successful decay-based account of one setting into a necessary condition for all grokking [1, p. 7; 4, p. 12; 5, pp. 2–4, 13–14].
4. **Width is confounded with parameterization, optimization, and compute.** The supplied sources motivate tracking initial scale/norm, feature-learning speed, and learning-rate conventions, not merely parameter count. They do not establish a universal monotonic relation between width and grokking time [3, pp. 2–6; 5, pp. 4–7, 13; 6, pp. 4–5].

## Source-by-source supported claims and settings

### [1] Power et al. — small algorithmic tables

**Full citation:** Alethea Power, Yuri Burda, Harri Edwards, Igor Babuschkin, and Vedant Misra. *Grokking: Generalization Beyond Overfitting on Small Algorithmic Datasets*. arXiv:2201.02177, 2022. Read version **v1, 6 January 2022**.

**Provenance:** supplied record https://arxiv.org/abs/2201.02177 ; retrieved original https://arxiv.org/pdf/2201.02177 . **Pages read:** 1–4; concluding paragraph of 5; methods/experimental details on 6–7. Bibliography text on 5–6 was incidentally included in extraction, not followed or used as evidence.

**Original contribution and evidence.** Binary-operation tables give a controlled data-limited test bed. The modular-division example with modulus 97 and 50% training data fits training in under about 1,000 steps, while held-out accuracy approaches perfection only near one million steps. The original abstract describes improvement “well past the point of overfitting.” Smaller datasets can need much longer optimization; a failure within a fixed budget is not an impossibility theorem [pp. 1–3].

**Reproduction settings reported in the original:**
- Each operand/result is an abstract token, not a decimal representation. Sequences are `a op b = c`; causal decoder-only transformer; loss/accuracy only on the answer token. Most modular tasks use prime 97; division excludes zero divisors. Other tasks include permutations in S5 and polynomial operations [pp. 2, 6].
- Randomly choose a training fraction of the finite table; **all remaining equations form validation**. This is a two-way split, not a separately protected test set [p. 6].
- Two layers, width 128, four attention heads, approximately 400,000 non-embedding parameters [p. 6].
- Default AdamW: learning rate 1e-3, decay 1, beta1=0.9, beta2=0.98; 10-update linear warmup; batch size min(512, half the training set); 100k updates [p. 6].
- **Important exceptions:** learning-time study uses 500k steps and seven seeds; the especially delayed-generalization examples use **Adam without weight decay and a one-million-update budget**. Most other dataset-size experiments use three seeds [p. 7]. Do not attach default AdamW settings to that exceptional million-step figure.
- Metrics include answer accuracy/loss, best validation accuracy within the budget, and time to first reach 99% validation accuracy. Some figures report mean accuracy over three runs; learning-time curves use a median [pp. 1, 3, 7].

**Pitfalls / width relevance:** Hyperparameters were tuned on modular addition and S5, with learning rate requiring a relatively narrow window. Some operations do not generalize even at 95% training data within the allotted budget. Changing width while retaining one learning rate tests a combined architecture/optimization choice, not width in isolation [pp. 3–4, 6]. This paper's principal sweeps are over data fraction and training details, not a claimed universal width law.

**Code availability:** no availability claim established from the method pages above; no repository lookup performed.

### [2] Nanda et al. — mechanistic progress measures

**Full citation:** Neel Nanda, Lawrence Chan, Tom Lieberum, Jess Smith, and Jacob Steinhardt. *Progress Measures for Grokking via Mechanistic Interpretability*. International Conference on Learning Representations (ICLR), 2023; arXiv:2301.05217. Read version **v3, 19 October 2023**.

**Provenance:** https://arxiv.org/abs/2301.05217 ; original https://arxiv.org/pdf/2301.05217 . **Pages read:** 1–9, 19, 23–27 (including Section 3, Sections 4–5, robustness/data-fraction and regularization appendices). Other appendix page headers were inspected only to locate relevant material.

**Original result.** For the studied small modular-addition transformers, the recovered algorithm uses sparse Fourier features and trigonometric composition; causal ablations support this account. The abstract names “memorization, circuit formation, and cleanup.” Restricted and excluded losses expose gradual progress before held-out accuracy changes [pp. 1–9]. This is evidence for these learned circuits, not proof that all widths or tasks use exactly the same circuit.

**Mainline protocol:**
- Addition mod 113; input `a b =`; one layer; ReLU MLP; embedding/residual dimension 128; four heads of dimension 32; 512 MLP hidden units; learned positional embeddings; **no LayerNorm and untied embedding/unembedding** [p. 3].
- Train on 30% of 113² ordered pairs; evaluate loss and accuracy on **every unused pair**. Full-batch AdamW, learning rate 0.001, decay 1, 40,000 epochs/updates. Figure 2 shows five seeds. Beta/epsilon values are not established by the pages read; do not silently import them from another paper [p. 3].
- Restricted loss: Fourier-transform logits over both input axes and retain selected task-relevant components (and the constant). Excluded loss: remove key components; evaluate on training data to track departure from memorization. Also track Fourier sparsity via Gini coefficients and parameter norms [pp. 7–9].
- Frequencies are seed-dependent: the mainline model's five frequencies are **not** a fixed universal target [pp. 4–6, 19, 27]. Selecting frequencies from a final model makes the corresponding early-training diagnostic retrospective; it is not automatically an ex-ante predictor [pp. 8–9].
- Within the reported 40k-epoch setting, 10–20% data does not grok, 30–50% shows grokking, and at least 60% generalizes immediately. The modulus-401 experiment also illustrates that changing modulus while holding the fraction fixed changes absolute training size substantially [pp. 23–26].

**Important source inconsistency:** p. 26 states that smaller decay slows grokking, but its subsequent numeric examples assign roughly 3k epochs to decay 0.3 and 20k to decay 3.0, contradicting that direction. Do not use those numeric pairings as a quantitative target. The independent Omnigrok experiment reports its own decay sweep [3, pp. 13–14].

**Width distinction:** Section 3 explicitly mentions varying depth and dimension. A new study should identify its controlled width definition and mechanistic question rather than imply dimension variation has never been considered [p. 3].

**Code availability:** p. 1 advertises code and interactive figures at an author site; this claim was read in the PDF only. No author site/repository was visited.

### [3] Liu, Michaud, and Tegmark — Omnigrok

**Full citation:** Ziming Liu, Eric J. Michaud, and Max Tegmark. *Omnigrok: Grokking Beyond Algorithmic Data*. ICLR, 2023; arXiv:2210.01117. Read version **v2, 23 March 2023**.

**Provenance:** https://arxiv.org/abs/2210.01117 ; original https://arxiv.org/pdf/2210.01117 . **Pages read:** 1–6, 13–14, including reduced-loss method, teacher–student setup, realistic-task protocols and decay sweeps.

**Original account.** Reduced training/test losses as functions of parameter norm often have “L”/“U” shapes in their setups. Angular optimization at fixed norm is approximated by rescaling the weights back to the designated norm after every update. Initialization scale alpha multiplies default initialization. These landscapes and enlarged initialization motivate induced grokking beyond algorithmic tasks [pp. 2–6]. This is a proposed mechanism and empirical construction, not a general equivalence theorem between norm and generalization. A numerically converged constrained optimizer is treated as a reduced minimum; global optimality is not independently established [pp. 2, 4].

**Reported settings and evaluation:**
- Teacher/student: both 5–100–100–5 tanh MLPs, distinct seeds; 100 training and 100 test standard-Gaussian inputs; outputs from the standard-initialized teacher. Student Adam learning rate 3e-4 for 100k steps; compare initialization alpha=0.5 versus 2, decay 0/0.03/1. Regression “accuracy” is defined using an error threshold 0.01; time to 95% such accuracy is reported [pp. 3–4].
- MNIST: random subset of 1,000 of the usual 60,000 training points to induce grokking, larger Kaiming-uniform initialization, depth-3 width-200 ReLU MLP, one-hot targets and MSE, AdamW learning rate .001, batch size 200. Metrics include test accuracy and finite-budget threshold times; thresholds differ across figures (60% in Fig. 3e, 70% in Fig. 10b), so they cannot be pooled as the same event [pp. 5, 13–14]. The read MNIST method paragraph does not fully specify all split/normalization details.
- IMDb: two-layer LSTM, embedding dimension 64, hidden dimension 128; 1,000 most frequent words; pad reviews to length 500 and ignore less frequent words; Adam learning rate .001 and binary cross-entropy; 25% of the 50k reviews held back for testing. The illustrative small-data run uses 1k examples, initialization alpha=6 and decay 1; the comparison with alpha=1 also changes decay, so it is not a pure one-factor intervention [pp. 5–6, 13].
- QM9: isotropic polarizability regression; two graph-convolution layers with ReLU then a linear layer; Adam .001, MSE; 50/50 train/test split, with an illustrative 200-training-example run at alpha=3. Zero weight decay in both illustrated initialization cases; authors invoke possible implicit regularization [pp. 6, 13]. No dataset/repository was retrieved.
- Their transformer decay experiment fixes addition mod 113, 30% train, width 128, four heads, MLP width 512, AdamW .001. Time to 100% test accuracy approximately scales inversely with decay over the tested range, with seed effects. The MNIST inverse relation is limited in range; very large decay impairs optimization and very small decay departs from the simple fit [pp. 13–14].

**Width distinction / pitfall:** Their alpha is an **initial-weight scaling**, not Kumar et al.'s output scaling. Raw total norm changes mechanically with parameter count; a width study must specify whether it controls initial per-parameter variance, layer norms, output variance, or total norm. Do not compare unnormalized norms as if they mean identical capacity.

**Code availability:** the original states code is available on p. 2; the repository was not accessed.

### [4] Varma et al. — circuit efficiency

**Full citation:** Vikrant Varma, Rohin Shah, Zachary Kenton, János Kramár, and Ramana Kumar. *Explaining Grokking Through Circuit Efficiency*. arXiv:2309.02390, 2023. Read version **v1, 5 September 2023**. No later venue attribution was sought.

**Provenance:** https://arxiv.org/abs/2309.02390 ; original https://arxiv.org/pdf/2309.02390 . **Pages read:** 1–10, 12, 16–17, 21–22: main model/predictions, experiment setup, limitations, transformer details and logit decomposition.

**Original result.** Their explanation combines a generalizing circuit, greater logit-per-norm efficiency than a memorizing circuit, and slower learning. A deliberately constructed lookup-table simulation demonstrates sufficiency of these ingredients, not quantitative dynamics of a trained transformer [pp. 3–5]. Predictions concerning critical dataset size are tested using efficiency comparisons, ungrokking, and semi-grokking [pp. 5–10].

**Reported neural-network settings:**
- One-layer decoder-only transformer; learned positional embeddings, untied embeddings/unembeddings; residual width 128; four 32-dimensional heads; MLP width 512. Full-batch AdamW with beta1=.9, beta2=.98, learning rate 1e-3, default decay 1 [p. 16].
- Binary operation input `x op y =`, predict the final result token with cross-entropy. Modulus 113 for modular tasks; full addition table has 12,769 examples; vocabulary size 115. Random training fraction and remaining examples as test [pp. 7, 16]. This four-input-token protocol is not identical to Nanda's three-token `a b =` protocol.
- Memorization-only proxy: randomize labels. Generalization-only proxy: train on large datasets and check that over 95% of logit norm lies in the trigonometric subspace. Compare correct-class logits against parameter norm and dataset size, controlling seeds when interpreting noisy scatter plots [pp. 7–8].
- Ungrokking: first train on the full table, then continue on a smaller subset. Semi-grokking: ten seeds at each of twenty dataset sizes from 1,500 to 2,050, with plateaus sometimes lasting millions of epochs; at least six of 200 runs show clear partial generalization at the end of the displayed budget [pp. 9–10, 16–17].

**Failure modes / qualifications:**
- “Test” examples after full-table pretraining in ungrokking have previously been seen. This protocol measures loss of an acquired solution, **not clean never-seen generalization**; retain it as a separate continuation/forgetting intervention [pp. 9, 16–17; methodological implication of the stated protocol].
- A critical dataset size is not a universal constant: initialization and training trajectory influence which circuit is found; thresholds differ between training-from-scratch and continuation [p. 17].
- Residual nontrigonometric logits are only an imperfect memorization proxy. Correlation can overestimate the generalizing part; raw correct-class logit size ignores competing logits and softmax shift invariance. Do not label residual norm as ground-truth circuit size [pp. 21–22].
- The authors explicitly state that dependence on weight decay makes the account incomplete for no-decay grokking [p. 12].

**Width distinction:** Relative circuit efficiency could change with width, but the reported critical-data experiments at width 128 do not establish a width scaling law. Testing that dependence would be a new experiment, not an original result to cite as already established.

**Code availability:** not established from the pages read; repositories not queried.

### [5] Kumar et al. — lazy-to-rich dynamics

**Full citation:** Tanishq Kumar, Blake Bordelon, Samuel J. Gershman, and Cengiz Pehlevan. *Grokking as the Transition from Lazy to Rich Training Dynamics*. ICLR, 2024; arXiv:2310.06110. Read version **v3, 11 April 2024**.

**Provenance:** https://arxiv.org/abs/2310.06110 ; original https://arxiv.org/pdf/2310.06110 . **Pages read:** 1–9, 13–14, 24 (theory/setup, loss decomposition, broader examples, implementation normalization, threshold warning).

**Original result.** The abstract reports grokking “without regularization.” A polynomial-regression committee machine initially follows a poorly generalizing fixed-feature/kernel solution before useful features develop. Output scale alpha controls learning laziness, initial kernel–target alignment controls the need for feature learning, and an intermediate sample-size range supports delayed rather than immediate/impossible generalization [pp. 2–8]. These are explanations and demonstrations, not a sharp finite-width theorem for grokking time [p. 9].

**Actionable method details:**
- Toy model: two-layer network with fixed unit readout weights, output proportional to alpha/N times a sum of activations; activation has linear plus quadratic terms; quadratic target in one input direction; Gaussian inputs with covariance I/D. Weight mean and second moment summarize the toy predictor, allowing decomposition of test MSE into variance, alignment, and unwanted linear-mode contributions [pp. 5–7]. Precise N/D/sample-count settings for every main figure were not established from the read pages; do not fabricate them.
- Main diagnostics include MSE, fixed-initial-NTK regression/linearized-network comparison, kernel–target alignment, relative parameter displacement, and norm. A model can grok while total norm **increases**, so norm reduction is not a necessary universal criterion [pp. 2–7, 13].
- To sweep output scale stably, use the centered predictor `alpha * [f(theta,x) - f(theta_initial,x)]`. Appendix 8.1 rescales vanilla-GD learning rate by 1/alpha² to keep initial output dynamics comparable. This is a GD convention; it is **not automatically a valid AdamW tuning law** [p. 13].
- No-decay modular-addition counterexample: concatenate two p-dimensional one-hot operands; hidden width 100, p-dimensional outputs, MSE against one-hot targets; p=23 in displayed example, 90% of pairs train and remainder test; vanilla GD learning rate 100, no weight decay. A range of moduli and widths also show the phenomenon [pp. 3, 13–14]. A high GD learning rate here must not be copied to an unrelated transformer/AdamW setup.
- For arbitrary tasks, the stated alignment diagnostic uses a kernel Gram matrix and labels, including test labels in their diagnostic description. If adapted for hyperparameter selection, move the diagnostic to a designated development/probe set; otherwise it becomes test leakage [p. 6; proposed safeguard].

**Failure modes / width relevance:** Larger width tends toward a lazy approximation only under the relevant parameterization assumptions [p. 4]. Width, initialization scale, and output scale are not interchangeable interventions without an explicit normalization convention. Regression accuracy thresholds can turn the *same run* into dramatically different plots; MSE should remain primary [p. 24]. The paper leaves adaptive-optimizer dynamics and sharp sample/time thresholds unresolved [p. 9].

**Code availability:** not established from the pages read; no external lookup.

### [6] Davies, Langosco, and Krueger — existing model-wise grokking

**Full citation:** Xander Davies, Lauro Langosco, and David Krueger. *Unifying Grokking and Double Descent*. ML Safety Workshop, 36th Conference on Neural Information Processing Systems (NeurIPS 2022); arXiv:2303.06173, posted 2023. Read version **v1, 10 March 2023**. Workshop attribution is printed on the original title page; do not mislabel it as a NeurIPS main-track paper.

**Provenance:** https://arxiv.org/abs/2303.06173 ; original https://arxiv.org/pdf/2303.06173 . **Pages read:** 1–5, experimental-details paragraph of 8, figure/captions on 9. Acknowledgments/reference portions on 6–7 were included in extraction but not used as evidence or followed.

**Original result and setting:**
- An abstract pattern-learning model assigns different learning speeds and generalization parameters to fast heuristics, memorization, and slower useful patterns. It is a conceptual model capable of producing both double descent and grokking, not an identified microscopic decomposition of every network [pp. 2–3].
- Decoder-only causal transformers learn division mod 97, abstract residue symbols, answer-token-only loss/accuracy. Unless otherwise stated, two layers, width 128, one attention head; AdamW beta1=.9, beta2=.98, learning rate 1e-3, decay **1e-5**, typically 400k updates [pp. 4, 8]. This decay is substantially different from the decay-1 addition setups; do not silently merge the recipes.
- Figure 4 gives train/test-loss heatmaps over transformer embedding dimension and training steps; Figure 5 plots width-wise loss/accuracy after 400k optimization steps, **smoothed using a Gaussian filter**; Figure 6 shows accuracy heatmaps. The text uses “epochs” in one place and “optimization steps” in the figure caption/appendix; preserve update counts explicitly in a new study [pp. 4–5, 8–9].
- Figure 7 explicitly uses 50% of modular-division data and isolates the early `0/b=0` heuristic. The inspected experiment details do not fully state every width heatmap's split-generation rule, batch size, width-grid step, split seed, MLP scaling, or smoothing bandwidth. Do not assume those missing settings from another paper [pp. 8–9].

**Width distinction:** The abstract explicitly claims a “first demonstration of model-wise grokking.” The defensible opportunity is a **controlled, replicated mechanism/parameterization study**, not first width-wise observation. Smoothing must not substitute for per-seed raw points, uncertainty, and censored runs.

**Code availability:** p. 3 states that replication code and an interactive notebook are available; repository not visited.

### [7] Loshchilov and Hutter — optimizer semantics

**Full citation:** Ilya Loshchilov and Frank Hutter. *Decoupled Weight Decay Regularization*. ICLR, 2019; arXiv:1711.05101, initially posted 2017. Read version **v3, 4 January 2019**.

**Provenance:** https://arxiv.org/abs/1711.05101 ; original https://arxiv.org/pdf/1711.05101 . **Pages read:** 1–6, especially Section 2 and Algorithms 1–2.

**Original result.** L2 loss regularization and multiplicative weight decay are equivalent for standard SGD after the appropriate learning-rate-dependent coefficient conversion, but generally not for adaptive preconditioning. AdamW decouples shrinkage from the adaptive loss-gradient step [pp. 1–4]. This is an optimizer result; **this paper does not study grokking**.

**Evidence setting:** Image-classification experiments use CIFAR-10 and ImageNet32x32 with residual networks, batch size 128, learning-rate schedules, and sweeps of rate/regularization. Figure 1 compares schedules after 100 epochs; the paper reports improved test error and more separable hyperparameter choices for decoupled decay [pp. 2, 5–6]. A separate calibration or development-split protocol was not established from the pages read; no benchmark results were reproduced.

**Planning implication:** Record the actual shrinkage update and which parameter groups are decayed. The paper's Algorithm 2 writes a scheduled shrinkage coefficient separately from the base adaptive learning rate; numerical coefficients must not be assumed interchangeable with a library's convention. If a chosen implementation uses shrinkage `(1 - eta_t * lambda)`, report that explicitly and track its cumulative product; this conditional bookkeeping recommendation is not a claim about a library inspected here. Do not implement both an L2 loss term and AdamW decay unintentionally. Training budget also changes the empirically best decay [pp. 2–3].

**Code availability:** the original abstract advertises complete experiment code; no repository was accessed.

## Recommended Next Experiments — proposals, not original results

The following is an unimplemented planning sketch. **None of the numerical grids, expected mechanisms, or success criteria below is a completed result. No novelty claim beyond this closed starter set is justified.**

### 1. Establish one transparent addition baseline

Use [2]'s addition-mod-113, one-layer, 30%-train, width-128, four-head, MLP-512, no-LayerNorm, full-batch AdamW recipe as the primary architecture anchor. Keep its three-token input convention distinct from [4]'s four-token convention. Fill remaining optimizer/initialization details with explicitly declared choices rather than pretending the PDF specified them. Use five paired seeds as a *proposed* minimum pilot. Record loss/accuracy trajectories through 40k updates; predeclare an extension budget if needed. Do not stop when training first interpolates [2, p. 3].

**Expected payoff:** establish whether the chosen implementation actually produces delayed generalization before interpreting any width trend. No delay, immediate generalization, or censored generalization are all valid outcomes to retain.

### 2. Separate residual width, MLP width, and parameterization

A possible geometric residual-width grid is 32, 64, 128, 256, with four heads and MLP width 4d. This changes per-head dimension; state that intervention. A separate fixed-residual-width MLP-only sweep and, if feasible, a fixed-head-dimension sweep distinguish these confounds. Hold modulus, task, data membership and split seed fixed across width. Pair initialization seeds statistically without claiming different-width initializations are identical.

Run both a literal fixed-hyperparameter replication arm and a declared development-tuned/initial-output-scale-controlled sensitivity arm. Report parameter count, initial logit variance, per-layer RMS/total norms, update-to-weight ratios, and rate/decay semantics. Compare fixed **updates**, and separately measured wall time/compute; these answer different questions. These are proposed controls motivated by [3], [5], [6], and [7], not proven invariances.

**Hypothesis to test, not assume:** apparent width dependence could reflect changed feature-learning speed or optimizer scale. It may accelerate, delay, eliminate, or make grokking unobservable within budget; no monotonic prediction is established by these readings.

### 3. Measure mechanisms alongside outcomes

For modular addition, log restricted/excluded loss, Fourier energy/sparsity, and both raw and normalized parameter movement. Determine frequency sets per run; distinguish final-checkpoint retrospective selection from a predefined task-wide trigonometric projection. Use ablations to check whether a Fourier summary is faithful at each width. Treat residual logits as a proxy, not an identified memorization circuit [2, pp. 7–9; 4, pp. 21–22]. Kernel diagnostics should use a fixed development/probe subset to bound cost and prevent selection on test labels [5, pp. 4–7].

**Expected payoff:** distinguish earlier circuit formation from later cleanup or a different learned mechanism; accuracy timing alone cannot do this.

### 4. Include minimal negative and robustness controls

- High-data arm (e.g. 60% under [2]'s setting): tests whether delayed generalization becomes immediate.
- Low-data arm (e.g. 20%): tests censoring versus a true successful transition; do not label nontransition by 40k updates “never groks.”
- No-decay arm plus a separately specified no-decay MLP/GD counterexample [5]: tests whether a decay-based interpretation is being overgeneralized.
- A small output-scale sensitivity arm with the appropriate optimizer-specific rate control; do not apply [5]'s GD alpha^-2 rule blindly to AdamW.

All control choices are proposals. Keep ungrokking/full-data-pretrained continuation separate from fresh-split generalization [4].

## Evaluation protocol to predeclare

1. **Splits:** originals commonly use one random training subset and its entire complement as “validation/test.” For faithful replication, reproduce that protocol and call it a two-way split. For tuning a width study, add a fixed development subset and a protected final test subset (or separate development splits); label this explicitly as a protocol change. Do not tune on repeatedly observed final-test curves, post-hoc select the most dramatic seeds, or use test-label kernel alignment for selection.
2. **Metrics:** report per-seed train/development/test cross-entropy and accuracy for classification; MSE for regression. Predeclare threshold-based times such as `t_train(99%)` and `t_eval(99%)`, their difference and ratio, plus loss trajectories. Threshold choice and persistence requirements are study choices, not a universal definition of grokking. A run that misses a threshold is **right-censored at budget**, not discarded or assigned an invented time. Report success fraction and nontransition categories alongside medians/intervals; show raw width points, not just smoothed lines.
3. **Uncertainty:** separate split-seed variability from initialization-seed variability. Use paired comparisons where split membership matches. Report what confidence/error bars summarize. More than a handful of seeds may be needed near transitions; [4] shows large seed effects.
4. **Calibration:** no dedicated ECE, Brier score, reliability diagram, or post-hoc temperature-fitting protocol was established in the pages read. Do not attribute a calibration result to these sources. If studying confidence across width, raw cross-entropy is mandatory and optional calibration metrics should have predefined bins and any temperature fit restricted to development data. Fourier/logit diagnostics are not themselves calibrated confidence.
5. **Budget and bookkeeping:** log actual gradient-update counts, processed examples, evaluation cadence, wall time, parameter count, optimizer betas/epsilon, warmup/schedule, parameter-group decay masks, initialization and numerical precision. Count evaluation/diagnostic overhead separately. A fixed-step comparison is not fixed-compute.
6. **Claims:** distinguish observational width curves, mechanistic intervention evidence, and theory. These seven papers cannot establish novelty relative to an undisclosed excluded work or the rest of the field. Do not infer or seek that work.

## Access audit and deliverables

- All original PDF downloads succeeded directly, without followed redirects. Hashes and version/page counts are in `literature/downloads.json` and `literature/pdf_metadata.json`.
- No topical web searches, paper listings, repositories, citation pages, or external discussions were visited. Official venue pages contained routine navigation links and template sample references, but those links were not followed.
- No known accidental forbidden external-content incident occurred; `literature/ACCESS_AUDIT.md` records the boundary and stop procedure. If future access exposes prohibited content, stop before further reading or experimentation and record URL/time/scope; do not summarize it into these notes.
- Selected official template: **ICLR 2027**, whose official released ZIP was verified; see `template/PROVENANCE.md`. The also-verified NeurIPS 2026 package and required checklist are preserved in `template/neurips2026_fallback/`, not mixed into the ICLR format.
