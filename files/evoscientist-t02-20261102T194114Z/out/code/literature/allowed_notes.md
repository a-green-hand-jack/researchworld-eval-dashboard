# Allowed-original notes: model scale, grokking, and a CPU modular-addition pilot

## 1. Boundary status — read this first

**Evidence gathering was stopped after an accidental bibliography exposure.** A batch intended to retrieve appendix details displayed PDF page 12 of `2310.06110v3`, which is a bibliography continuation. Page 13 was also displayed in that same completed tool response before the incident could be recognized. The forbidden work was not identified, inferred, or looked up. Because its identity is unspecified, whether that page actually contains forbidden material is **unknown**, not certified safe. Exact page-12 exposure is archived in `exposure_log.md`; `viewed_passages.md` reconstructs all displayed source-text passages, including earlier related-work text inside allowed originals. These logs are audit artifacts, not recommended reading.

Only the seven allowlisted original PDFs were requested. No topical searches, citation-graph requests, article recommendations, external metadata services, linked repositories, or cited originals were fetched. The initial memory preflight was boundary-neutral, returned no results, and exposed no literature. The paper-reading skill was used only for direct-original reading principles, not its search or metadata scripts. No experiment code was implemented and no experiments ran.

**Important limitation:** an allowlist for documents does not establish that all their text is semantically clear of an unidentified forbidden work. In hindsight, page-number guesses were an inadequate way to avoid bibliographies. This report cannot claim a clean forbidden-content boundary. No new source reading occurred after the incident; the remaining work was archiving already displayed material and writing this qualified synthesis.

## 2. Retrieval and actual reading ledger

All seven originals were downloaded successfully from `https://arxiv.org/pdf/<exact-ID>`, without an off-allowlist redirect. Local originals are `<ID>.pdf`. `retrieval_log.json` records requested/final URLs, sizes, and status. `manifest.json` records SHA-256 hashes. The entire PDFs were mechanically text-extracted to `<ID>.pages.json`; **extraction/download is not full reading**. No abstract landing-page widgets were displayed.

Page numbers below are **PDF page indices starting at 1**. The first 5,000 extracted characters of page 1 were displayed for each original, including its title/author/abstract/version stamp and some introduction. Other listed pages were displayed in full except the stated truncation. Neither figures as images nor their visual details were inspected; figure captions/extracted labels were read as text. Text extraction warned that some form content was skipped; equations, figure labels, and hyphenation may be imperfect. No complete-paper reading or visual verification is claimed.

| Citation | Exact downloaded version | Additional displayed PDF pages | Basis used here |
|---|---|---|---|
| [1] `2201.02177` | v1, 6 Jan 2022 | 2–4; 5 only before References; 8–9 | Original task setup, delay/data-size effects, regularization. Pages 8–9 also exposed unrelated discussion; not used as evidence for external papers. |
| [2] `2301.05217` | v3, 19 Oct 2023 | 2–4 | Modular-addition transformer configuration, Fourier interpretation and progress measures; includes related-work text. |
| [3] `2210.01117` | v2, 23 Mar 2023 | 2–6 | Initialization/norm mechanism, teacher–student example, and MNIST MLP; not a modular-addition MLP reproduction. |
| [4] `2309.02390` | v1, 5 Sep 2023 | 2–5, 7–9 | Efficiency ingredients, seed variability, ungrokking and semi-grokking protocols. |
| [5] `2310.06110` | v3, 11 Apr 2024 | 2–5, 12–13 | Feature-learning alternative; Appendix 8.1 scaling prescription. Page 12 accidental bibliography exposure. Appendix 8.3 starts on page 13 but its architecture details continue onto an **unread** page. |
| [6] `2303.06173` | v1, 10 Mar 2023 | 2–5, 8–9 | Model-wise result and Appendix B hyperparameters; includes related-work/discussion text. |
| [7] `1711.05101` | v3, 4 Jan 2019 | 2–3 | AdamW versus L2 distinction and update conventions. |

Bibliographic metadata in `references.bib` comes from the downloaded title pages and arXiv stamps, not from the accidentally displayed bibliography. Entries use the initial arXiv year and separately note later viewed versions/conference labels. The PDF text does not provide a machine-readable BibTeX export; these are faithfully transcribed BibTeX records, not a claimed official export. No DOI, citation count, or unverified venue was added.

## 3. Grounded baselines and what they do NOT establish

### 3.1 Closest fully specified modular-addition baseline: transformer, not MLP [2]

Section 3, PDF page 3: prime modulus **113**, 30% of all ordered input pairs for training, all remaining pairs for test, one-layer ReLU transformer, token dimension 128, four heads of dimension 32, MLP hidden size 512, no LayerNorm, untied input/output embeddings. Full-batch AdamW, learning rate 0.001, decay parameter 1, 40,000 epochs/updates. Figure 2 describes five random seeds; the text reports generalization after around 10,000 epochs in this setting.

This supplies a task/split/optimizer anchor, **not evidence that a much smaller CPU ReLU MLP at p=31 will grok on that schedule**. Its detailed appendix/optimizer implementation was not inspected. Do not import five key frequencies, exact training times, or its attention-mediated multiplication circuit into an MLP as established facts.

### 3.2 Direct model-scale evidence has narrower scope [6]

Section 3 and Figures 4–5 report model-wise behavior while varying **transformer embedding dimension**, on **division modulo 97**, with 400,000 optimization steps in the cross-section. Figure 5 explicitly uses Gaussian-smoothed lines. Appendix B states a default two-layer, width-128, single-head decoder-only transformer, AdamW beta=(0.9,0.98), learning rate 1e-3, and weight decay 1e-5. These differ markedly from [2]'s task and decay setting. No exact width grid, complete split specification for the model-wise sweep, or per-width raw-run uncertainty was verified in the passages read. Figure 7 labels a modular-division run with 50% training data; do not assume that establishes the split of every model-wise experiment.

This is evidence of a reported **finite-training-budget size-associated phenomenon**, not a proof that hidden width alone causes a particular grokking mechanism in an addition MLP.

### 3.3 Complementary mechanisms, not a universal winner [1,3–5]

- [1] reports strong dataset-size dependence of delay and improved data efficiency from weight decay. Its original networks were transformers. It also notes failures to generalize within the allotted budget on some operations.
- [3] studies loss landscapes reduced at fixed weight norm, and enlarged initialization scales. Its MNIST result uses a depth-3 width-200 ReLU MLP, MSE on one-hot targets, and only 1,000 training images. Its teacher–student Adam setup and regularized loss should not be silently treated as the same optimizer/objective as [2]. The reduced landscape is a constrained optimization construction, not merely loss evaluated along a training trajectory.
- [4] proposes competing circuits: a slower generalizing circuit can displace a faster memorizing circuit if it is more parameter-efficient. The toy construction establishes sufficiency within that construction, not necessity for all networks. Real experiments are one-layer transformers at p=113; the reported semi-grokking examples can require **millions to tens of millions** of epochs, not a practical CPU baseline. Its norm/logit scatter has substantial seed variance. Random-label runs are used as a proxy for memorization-only circuits, an assumption rather than a universal identification result.
- [5] supplies no-weight-decay counterexamples, including modular arithmetic with **increasing** parameter norm, and a tractable polynomial model. Thus shrinking norm, Adam-specific anomalies, and explicit weight decay cannot be universal requirements. Appendix 8.1 specifically centers the predictor at initialization and rescales learning rate for its output-scale intervention. The full modular-addition MLP architecture/initialization/learning-rate details were **not** reached before stopping; no exact reproduction configuration is claimed.

## 4. Proposed small CPU experiment — a new pilot, not a published recipe

The values below are **planning recommendations**, grounded in the task and diagnostics above but not claimed to have succeeded. No run-time or outcome measurements exist.

### 4.1 Primary configuration: inexpensive classification pilot

| Component | Proposed value |
|---|---|
| Data | Enumerate all ordered (a,b) in {0,...,30}²; y=(a+b) mod 31. Exactly 961 examples; chance accuracy 1/31≈3.23%. |
| Input | Concatenate two independent one-hot vectors: 62 dimensions. No integer-valued scalar representation or hand-coded Fourier features. |
| Model | Bias-free 62 → h → 31 MLP, one ReLU hidden layer. Start h=64. Width screen h∈{32,64,128}. No normalization, dropout, skip connection, or weight tying. |
| Parameters | 3ph = 93h: 2,976 / 5,952 / 11,904 trainable parameters at these widths. Even h=32 is already parameter-rich relative to 961 examples; this screen need not cross an interpolation threshold. |
| Initialization | Fan-in-scaled Kaiming-uniform for W1; explicitly specify W2 uniform[-1/sqrt(h),1/sqrt(h)]. Record actual per-layer norms and initial logit RMS. Hold this rule fixed within the basic width sweep. Do not describe fan-in scaling as matching every notion of initialization scale across widths. |
| Split | Fixed seeded uniform shuffle of the 961 ordered pairs: train 288 (floor 30%), validation 192 (floor 20%), untouched test 481. Store exact indices. Use the same split across widths. This adds a validation set, so it is **not** [2]'s 30/70 protocol. |
| Loss | Mean softmax cross-entropy over examples. Log this unregularized data loss separately from any explicit penalty. |
| Optimizer | Full-batch AdamW: lr=1e-3, beta=(0.9,0.98), eps=1e-8, constant schedule. Apply decay to both weight matrices; no biases exist. Decay screen {0,0.1,1}, beginning at 1. This combines allowed-source choices, not a verbatim single-paper baseline. |
| Budget | Time 1,000 warm-up/pilot updates on the actual CPU. If viable, preregister 50,000 updates, with a possible **common** extension to 200,000 for all censored widths. Evaluate train/validation every 100 updates, and more densely around an observed transition. Never stop merely because train accuracy is perfect. |
| Replication | One smoke seed first; then 3 initialization seeds at h=64 for the decay screen. Freeze a viable regime using validation only, then compare three widths with ≥3, preferably 5, paired seeds. Use a second split seed only after this first screen is informative. |

Full-batch training avoids batch-noise confounds and needs little memory. The full input grid is only 961 examples and the h=64 model has fewer than 6,000 parameters. Nevertheless, many tiny CPU updates can be slow because of framework overhead. Measure updates/second before choosing the total run matrix; do not promise 200,000 steps are cheap. Avoid dense full-output NTKs over the complete grid. Freeze CPU thread count and report wall-clock, updates, examples processed, and estimated FLOPs separately.

**If no delayed generalization appears:** first distinguish (i) train never fits, (ii) immediate generalization, and (iii) fit without generalization by the budget. For (i), sanity-check labels/loss and try lr 3e-4 or 3e-3 at the single pilot width. For (ii), try 20% training data or a separately labeled initialization-scale intervention. For (iii), use the common budget extension before calling a width incapable; then try 50% training data to establish that the model can learn the task. If p=31 is uniformly too easy, p=59 is a separate increased-task-size pilot, not an interchangeable replicate. Do not mix these changes into one width-causal claim.

### 4.2 Secondary configuration: feature-learning mechanism test

At fixed width h=64 and a split already shown to permit eventual generalization, compare a normally trainable model, a frozen-feature model (train W2 only), and—if resources allow—a model linearized at initialization. These have different function classes; report that limitation. A failure of frozen features alone does not prove an NTK transition.

For a closer [5]-inspired intervention, use one-hot-target **MSE**, predictor gθ(x)=α[fθ(x)−fθ0(x)], zero weight decay, plain full-batch GD, and α∈{0.5,1,2}. Hold the frozen initial predictor fixed per seed. Set lr=η0/α², selecting a stable η0 at α=1 by training-only stability checks. MSE reduction over classes as well as examples must be fixed and reported. This is a **new adaptation**, not the unread Appendix 8.3 recipe, and grokking is not guaranteed. The lr prescription is justified for the GD/MSE analysis and must not be automatically transferred to AdamW/cross-entropy.

Keep this separate from the primary CE/AdamW width screen. Compare feature learning with and without regularization rather than assuming all mechanisms are interchangeable.

## 5. Evaluation protocol, calibration, and failure definitions

These are proposed safeguards unless explicitly attributed above.

- **Partition semantics:** the benchmark measures completion of missing ordered pairs with shared symbol vocabulary, not out-of-distribution arithmetic or new-modulus generalization. In an ordered-pair split, (a,b) and (b,a) may cross partitions. This is legitimate for that declared protocol but admits commutative counterparts. A separate robustness protocol groups unordered pairs before splitting; it is a harder/different protocol, not the same result. Always report examples per resulting partition and label coverage.
- **Do not tune on test:** tune regime and diagnostics on train/validation, lock choices, then evaluate fixed test checkpoints. A paper-style all-complement diagnostic is possible, but then it is development data and cannot simultaneously be called an untouched test. Do not select the best epoch/seed by test accuracy.
- **Continuous and thresholded metrics:** report train/validation/test CE or MSE (clearly labeled), top-1 accuracy, correct-class margin, logit RMS, per-layer and total parameter norm, and relative parameter displacement. In the primary split, test accuracy changes in increments of 1/481; an apparent jump is not itself a discontinuity in the learned function.
- **Delay definition:** preregister t_train99 and t_val99 as first checkpoints reaching ≥99% accuracy and staying above that level for the next five evaluations. Report both times, their difference/ratio, and raw curves. If a run never fits or never generalizes, report separate failure categories; right-censor a missing generalization event at its budget rather than replacing it by the budget or excluding the seed. Five repeated checkpoints are a proposed persistence convention, not an allowed-paper standard.
- **Scale plots:** show loss and accuracy jointly, against both updates and compute; show raw points before smoothing. [6]'s log-accuracy/loss examples reveal behavior that a linear accuracy plot can obscure. Do not confuse a regression-error threshold with intrinsic classification accuracy; [5] explicitly warns that such accuracy curves can be manipulated by metric choice.
- **Calibration:** the read passages do not establish a shared calibration protocol. For this proposed classification pilot, report uncalibrated NLL and multiclass Brier score; a 10-bin equal-width confidence reliability diagram/ECE is secondary because the held-out set is small. If temperature scaling is used, fit temperature only on validation, apply the same frozen rule to test, and show both raw and calibrated results. Never use calibrated NLL to hide logit-scale effects in the primary mechanistic analysis.
- **Uncertainty:** plot individual seeds, event success fraction, and medians/ranges with censored runs shown. A test set of all remaining pairs is finite-population performance for that task; seed/split uncertainty remains. Do not present a single seed, Gaussian-smoothed threshold, or arbitrary early horizon as a universal phase transition.
- **Optimizer bookkeeping:** [7] establishes that Adam with an L2 loss term is not AdamW. In a common library AdamW convention the pure decay factor is (1−ηλ) per step; record the actual library convention and version. The original [7] writes decay λ separately from base lr in its algorithm, so numerically identical λ values need not be identical implementations. For η=1e-3 and λ=1, the no-gradient norm multiplier after 1,000 updates is approximately exp(−1). The cumulative decay exposure depends on budget and schedule; it is not fixed by quoting λ alone.

## 6. Mechanistic predictions and falsifiable observations

| Hypothesis / source motivation | Proposed diagnostic/intervention | Supporting pattern | What would weaken this interpretation |
|---|---|---|---|
| Fourier structure can form before the accuracy jump [2] | Evaluate the logit tensor L(a,b,c) on the complete grid at fixed checkpoints. Track Fourier power and projected-logit loss. Define frequency selection from training/validation or a preregistered basis, not from final test success. | Structured power/projection performance develops before total held-out accuracy; selective ablation harms predictions more than a matched random removal. | No predictive structure, or random ablations with matched energy are equally damaging. A visually circular embedding alone is insufficient. |
| A useful sum circuit can be masked by other components [2,4] | Predeclare the invariant subspace L(a,b,c)=F(a+b−c); compare its projection and residual over time, and perform matched-energy controls. | Projection improves earlier, residual contribution decays later; removing the projection selectively destroys performance. | Transition occurs without the proposed structure or without selective necessity. An MLP may learn a different circuit. |
| Initialization/norm and regularization can control a delay in some regimes [3,4] | At fixed h, split, and optimizer, separately vary initialization multiplier and decay; log norms, margins and continuous losses. | Appropriate large-scale/weak-decay runs have a longer delay; later function becomes more economical within this parameterization. | Generalization appears at increasing norm or zero decay; this rules out a universal shrinkage requirement, not every efficiency explanation [5]. |
| Delayed feature adaptation is one possible mechanism [5] | Track hidden activation Gram/CKA on a fixed small diagnostic set, parameter displacement, and a fixed-subset empirical-kernel diagnostic. Compare trainable, frozen-feature, and optionally linearized models. | Features/kernel change before late generalization; the matched linearized predictor does not achieve the same improvement. | Frozen/linearized controls generalize equally, or diagnostic changes only follow the transition. Feature movement alone is correlational. |
| Width effects can be mediated by training dynamics [5,6] | Measure a width×time surface, then intervene on output/initialization scale at fixed width in a separately controlled GD/MSE experiment. | Delay shifts at fixed width, or width differences shrink when measured dynamics are matched. | Width differences remain after these controls; that still does not isolate a universal capacity mechanism. |

For the proposed three-dimensional DFT convention, the invariant F(a+b−c) subspace has support k_a=k_b=−k_c modulo p. This is an analyst-designed diagnostic from the algebra, **not a claim that the allowed transformer paper used this exact full-logit test**. Center per-example logits when comparing spectra because softmax is invariant to adding a class-independent constant. Report centered-logit energy and uncertainty, not only a raw power fraction. Fixed sample diagnostics (e.g., 64–128 input pairs) keep kernel/Gram work CPU-sized; distinguish the full multi-output NTK from a trace-kernel proxy.

A degree-2 trigonometric/attention circuit established for a transformer is not automatically a mechanism of a one-hidden-layer ReLU MLP. Projection, frequency ablation, matched-energy random controls, and direct function-preserving interventions are stronger evidence than t-SNE pictures or norm correlations. Diagnostic full-grid labels must not become an additional tuning set.

## 7. Why a width sweep is not a clean capacity-causal experiment

1. Changing h changes parameter count, feature availability, initial aggregate norms, output scale, empirical kernel, per-parameter gradients, optimizer statistics, and cost per update. A fixed initialization *rule* does not match all of these quantities.
2. A fixed update budget compares different compute costs; a fixed FLOP or wall-time budget compares different numbers of updates. Neither alone proves an intrinsic width threshold. Report both views and right-censor delayed runs.
3. Weight decay is coordinate/parameterization-dependent. In a bias-free ReLU network, W1→cW1 and W2→W2/c preserve the represented function for c>0 but change layer norms and generally the penalty. Norm efficiency is meaningful only with an explicit parameterization and matched functional scale. Matching total norm can itself change layerwise scale and feature learning.
4. Width-associated laziness is conditional on parameterization, initialization, optimizer and time scale, as [5] emphasizes. “Wider means faster grokking,” “wider means more feature learning,” and “a bigger model causes the Fourier circuit” are not established by the read evidence.
5. A size-axis transition and a time-axis transition are not the same estimand. [6] reports the former in a particular transformer/division setting; this cannot establish an addition-MLP law, let alone a large-model scaling law.
6. Initial kernel/logit matching and a separate dynamical intervention can narrow explanations but do not hold all width mediators fixed. Treat width as a bundled intervention, report the proposed mediators, and distinguish conditional causal statements from observational associations.

**Minimum defensible claim after a successful pilot:** “Under the stated representation, split, initialization, optimizer and budgets, changing hidden width is associated with a reproducible shift in generalization timing/performance.” A stronger mechanistic claim requires its own matched controls and interventions; no results are claimed here.

## 8. Code availability and unverified details

Code links were seen in originals but **not opened**: [2] page 1, https://neelnanda.io/grokking-paper; [3] page 2, https://github.com/KindXiaoming/Omnigrok; [6] page 3, https://github.com/xanderdavies/unifying-grok-dd; [7] page 1, https://github.com/loshchil/AdamW-and-SGDW. These are availability statements from the papers, not recommendations to browse them under this boundary. Repository contents, commits, dependencies, licenses and CPU compatibility are unverified. No code URL is asserted for sources where one was not viewed.

Unresolved because reading stopped: complete Appendix 8.3 settings in [5], [4]'s detailed appendix protocol, visual confirmation of extracted equations/figures, exact width-grid/split details for [6]'s model-wise sweep, and a demonstrated CPU success region. The proposed pilot is deliberately presented with these limitations.

### Sources (allowlisted originals only)

[1] Alethea Power et al., *Grokking: Generalization Beyond Overfitting on Small Algorithmic Datasets*: https://arxiv.org/abs/2201.02177

[2] Neel Nanda et al., *Progress Measures for Grokking via Mechanistic Interpretability*: https://arxiv.org/abs/2301.05217

[3] Ziming Liu, Eric J. Michaud, and Max Tegmark, *Omnigrok: Grokking Beyond Algorithmic Data*: https://arxiv.org/abs/2210.01117

[4] Vikrant Varma et al., *Explaining Grokking through Circuit Efficiency*: https://arxiv.org/abs/2309.02390

[5] Tanishq Kumar et al., *Grokking as the Transition from Lazy to Rich Training Dynamics*: https://arxiv.org/abs/2310.06110

[6] Xander Davies, Lauro Langosco, and David Krueger, *Unifying Grokking and Double Descent*: https://arxiv.org/abs/2303.06173

[7] Ilya Loshchilov and Frank Hutter, *Decoupled Weight Decay Regularization*: https://arxiv.org/abs/1711.05101

## 9. Exact viewed supporting passages

The following subsection is appended mechanically from **already displayed** extraction text, preserving line breaks and extraction artifacts. Short excerpts substantiate source-specific claims; surrounding source text is in the viewed-text audit. No excerpts were selected from the accidentally displayed bibliography.

### 2201.02177, PDF page 2

```text
All of our experiments used a small transformer trained on datasets of equations of the forma◦b =c,
where each of “a”, “◦”, “b”, “=”, and “c” is a separate token. Details of the operations studied, the
architecture, training hyperparameters and tokenization can be found in Appendix A.1.
```

### 2201.02177, PDF page 2

```text
For larger dataset sizes, the training and validation curves tend to track each other more closely.
```

### 2201.02177, PDF page 4

```text
We found that learning rate had to be tuned in a relatively narrow window for the generalization to
happen (within 1 order of magnitude).
```

### 2301.05217, PDF page 3

```text
Our mainline dataset consists of 30% of the entire set of possible inputs (that is, 30% of the 113 ·
113 pairs of numbers mod P ). We use full batch gradient descent using the AdamW optimizer
(Loshchilov & Hutter, 2017) with learning rate γ = 0.001 and weight decay parameter λ = 1. We
perform 40, 000 epochs of training. As there are only 113 · 113 possible pairs, we evaluate test loss
and accuracy on all pairs of inputs not used for training.
```

### 2301.05217, PDF page 3

```text
where a and b are encoded as P -dimensional one-hot vectors, and = is a special token above which
we read the output c. In our mainline experiment, we take P = 113 and use a one-layer ReLU
transformer, token embeddings with d = 128, learned positional embeddings, 4 attention heads of
dimension d/4 = 32, and n = 512hidden units in the MLP. In other experiments, we vary the depth
and dimension of the model. We did not use LayerNorm or tie our embed/unembed matrices.
```

### 2301.05217, PDF page 2

```text
Using our understanding of the learned algorithm, we construct two progress measures for the mod-
ular addition task— restricted loss, where we ablate every non-key frequency, and excluded loss,
where we instead ablate all key frequencies. Both metrics improve continuously prior to when
grokking occurs. We use these metrics to understand the training dynamics underlying grokking
and find that training can be split into three phases: memorization of the training data; circuit for-
mation, where the network learns a mechanism that generalizes; and cleanup, where weight decay
removes the memorization components. Surprisingly, the sudden transition to perfect test accuracy
in grokking occurs during cleanup, after the generalizing mechanism is learned. These results show
that grokking, rather than being a sudden shift, arises from the gradual amplification of structured
mechanisms encoded in the weights, followed by the later removal of memorizing components.
```

### 2210.01117, PDF page 2

```text
In practice, we perform the constrained minimization by rescaling the model weights back to their
original norm after each unconstrained optimization step.
```

### 2210.01117, PDF page 3

```text
If weight
decay is the only source of regularization, and training loss is negligible after overﬁtting, then weight
decayγ causesw(t)≈ exp(−γt)w0, whenw0 >w c, so it takes timet≈ ln(w0/wc)/γ∝γ−1 to
generalize.
```

### 2210.01117, PDF page 5

```text
With these modiﬁcations to the
training set size and initialization scale, we train a depth-3 width-200 MLP with ReLU activations
with the AdamW optimizer using MSE loss with one-hot targets.
```

### 2309.02390, PDF page 3

```text
This overall explanation relies on the presence of three ingredients:
1. Generalising circuit:There are two families of circuits that achieve good training performance:
a memorising family𝐶memwith poor test performance, and a generalising family𝐶genwith good
test performance.
2. Efficiency:𝐶genis more “efficient” than𝐶mem, that is, it can produce equivalent cross-entropy
loss on the training set with a lower parameter norm.
3. Slow vs fast learning:𝐶genis learned more slowly than𝐶mem, such that during early phases of
training𝐶memis stronger than𝐶gen.
```

### 2309.02390, PDF page 4

```text
treated as a validation of the three ingredients, rather than as a quantitative prediction of the dynamics
of existing examples of grokking. Many
```

### 2309.02390, PDF page 8

```text
Note that the figures show significant variance across random seeds. We speculate that there are
many different circuits implementing the same overall algorithm, but they have different efficiencies,
and the random initialisation determines which one gradient descent finds.
```

### 2309.02390, PDF page 9

```text
Out of 200 runs, at least 6 show
clearsemi-grokkingattheendoftraining. Many
other runs show transient semi-grokking, hover-
ing around middling test accuracy for millions
of epochs, or having multiple plateaus, before
fully generalising.
```

### 2310.06110, PDF page 2

```text
We give simple examples of a two-layer MLP without any weight decay that exhibits grokking
in ways inconsistent with existing theories of grokking.
```

### 2310.06110, PDF page 3

```text
Weight norm
of parameters increases during training (Figure 2(a)), so grokking cannot in general be explained by
theories of weight decay.
```

### 2310.06110, PDF page 13

```text
Further, to maintain
consistent timescales of training, it is important to rescale learning rate as η = η0/α2. This rescal-
ing keeps the initial derivative ddt f |t=0 independent of α and thus the early training dynamics areconsistent across α. Otherwise, large α networks will have too large a learning rate and small α
networks take too long to train.
```

### 2303.06173, PDF page 4

```text
Following the original grokking setting of Power et al. (2022), we train decoder-only transformers
(Vaswani et al., 2017) with causal attention masking on the binary operation of division mod 97
(details in Appendix B). We explore the effects of regulating effective model complexity by varying
parameter-count.
```

### 2303.06173, PDF page 5

```text
Figure 5: Model-wise grokking, with each point a transformer of the corresponding embedding
dimension trained for 400K optimization steps. Lines are smoothed data via a Gaussian ﬁlter.
```

### 2303.06173, PDF page 8

```text
In all of our experiments, we train decoder-only transformer with causal attention masking. Each
residue is encoded as a symbol, and loss and accuracy are only evaluated on the answer part of the
equation. Unless otherwise stated, we use a 2-layer network of width 128, with a single attention
head. We typically train for 400 thousand optimization steps via AdamW (β1 = 0.9,β2 = 0.98),
with learning rate of 1e-3 and weight decay of 1e-5.
```

### 1711.05101, PDF page 3

```text
with decoupled weight decay, only the gradients of the loss function
are adapted (with the weight decay step separated from the adaptive gradient mechanism).
```
