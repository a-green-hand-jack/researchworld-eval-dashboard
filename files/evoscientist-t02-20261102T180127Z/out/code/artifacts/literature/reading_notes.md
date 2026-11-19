# Allowlisted-paper reading notes

Read on 2026-11-02 UTC. Evidence is limited to the seven user-specified papers. Page numbers below are PDF page numbers, not necessarily printed page labels. No citation graph, recommendations, topical searches, external repositories, or linked papers were consulted. A code link printed in a paper is an author-reported availability claim, not an independently verified repository. Full PDFs and verbatim extracted text are preserved; `*.reading.txt` omit bibliography sections. See `independence_audit.md` for incidental exposure and extraction limitations.

## [P1] 2201.02177 — Grokking: Generalization Beyond Overfitting on Small Algorithmic Datasets

Source: https://arxiv.org/pdf/2201.02177 ; retrieved PDF identifies v1, 6 Jan 2022. Read main text pp. 1–5 and experimental details pp. 6–7. Bibliography excluded from evidence.

### Verified setup and evaluation
- Synthetic binary operation tables. Residues/permutations are individual abstract tokens, not numeric magnitude encodings. A sequence is `x op y = answer`; causal decoder-only transformer; loss and accuracy only on answer.
- Random fraction of all equations is training data; all remaining equations form validation. Modular operations generally use prime 97. Division excludes zero denominators: `0 <= x < 97`, `0 < y < 97`, so 9,312 examples rather than 97². Addition has 9,409 examples. Other tasks include compositions in S5 and polynomial operations.
- Two transformer layers, width 128, four attention heads, about 400,000 non-embedding parameters. This is not the one-layer/no-LayerNorm mechanistic baseline in P2.
- Most experiments: AdamW, learning rate 1e-3, weight decay 1, betas (0.9, 0.98), linear LR warmup over first 10 updates; minibatch `min(512, half the training set)`, 100,000 gradient updates. Three random seeds per dataset size.
- Section 3.1.1 learning-time curves: budget 500,000 updates and seven seeds; report median steps to first 99% validation accuracy. Section 3.1 exceptionally uses Adam **without weight decay**, budget 1,000,000, to emphasize late generalization.
- Figure 1 modular division, 50% training: near-perfect train accuracy before 1,000 steps, near-perfect validation near 1,000,000; very little validation improvement before 100,000. Do not assume this example uses the default AdamW configuration.

### Interpretation and experiment implications
- Dataset size–optimization-time tradeoff is already a central result. Near the generalization boundary, small reductions in data require large extra optimization budgets. The S5 curve around 25–30% training reports 40–50% more median generalization time per one-percentage-point data reduction.
- Weight decay strongly improves data efficiency; learning rate must be in a relatively narrow range. Some operations fail to generalize even at 95% training within the allotted budget. A failed finite run is not proof of impossibility.
- Symmetric operations and architecture can interact. Random ordered-pair splits can expose the reverse `(b,a)` of a held-out commutative example during training; this is part of the historical protocol, not a guarantee of out-of-distribution algorithm learning.
- Code availability was not established from the experimental sections read; no repository inspected. No explicit calibration analysis was established.
- Novelty caveat: delayed generalization, sample-size dependence, weight-decay and learning-rate interventions, and embedding structure are existing findings here.

## [P2] 2301.05217 — Progress Measures for Grokking via Mechanistic Interpretability

Source: https://arxiv.org/pdf/2301.05217 ; PDF v3, 19 Oct 2023, ICLR 2023. Read pp. 1–4, main progress measures pp. 8–9, and structural appendix overview. Related-work statements were not used as additional sources.

### Verified baseline
- Addition mod 113, all 12,769 ordered operand pairs. Random 30% train; evaluate remaining pairs. Input is `a b =` (three tokens), output above `=`. Residues are one-hot tokens.
- One-layer ReLU transformer: residual/token embedding width 128; learned positional embeddings; four heads, each head dimension 32; MLP hidden width 512. No LayerNorm; embedding and unembedding not tied.
- Full-batch AdamW, LR 1e-3, weight decay 1, 40,000 epochs (one update per epoch). Figure 2 uses five seeds; generalization is around 10,000 epochs in the demonstrated runs. Do not import unspecified optimizer details as though verified in Section 3.

### Mechanism and measurements
- Learned solution uses sparse Fourier components and trigonometric addition identities. Fourier ablations, not visualization alone, substantiate the mechanism.
- Restricted loss: 2D DFT of logits over `(a,b)`, retain constant plus directions for final key frequencies, zero other components, recompute loss. Excluded loss removes key-frequency components; measure on training examples to assess remaining memorization performance.
- Their worked model uses five key frequencies. This is a property of that model, not a fixed required count across widths/seeds.
- Also track Fourier-component Gini/sparsity and parameter norm/squared norm. Worked phases: memorization about 0–1.4k epochs; circuit formation 1.4–9.4k; cleanup 9.4–14k. These are illustrative, not universal thresholds.
- Restricted loss can improve and excluded loss worsen before ordinary held-out accuracy changes. Thus a flat accuracy trace does not mean no mechanistic progress.
- **Prospective prediction caveat:** frequencies chosen using the final network yield retrospective diagnostics. They cannot be called online predictors without a training-only/frozen discovery rule and held-out evaluation.
- Author-reported code/interactive figures: `https://neelnanda.io/grokking-paper` (printed p. 1; not visited).
- Novelty caveat: Fourier mechanisms, smooth pre-grokking progress, circuit formation/cleanup, and diagnostic ablation loss are prior results.

## [P3] 2210.01117 — Omnigrok: Grokking Beyond Algorithmic Data

Source: https://arxiv.org/pdf/2210.01117 ; PDF v2, 23 Mar 2023, ICLR 2023. Read main mechanism pp. 1–4, nonalgorithmic-task discussion and Appendix A–C p. 13.

### Verified findings and protocols
- Proposes an LU picture: reduced training loss versus weight norm is L-shaped; reduced test loss is U-shaped. The reduced landscape is estimated by optimizing angular directions while projecting parameters back to fixed norm after updates. This is an optimization-conditioned visualization, not proof of a unique global loss surface.
- Initialization multiplier alpha multiplies default initial weights. Larger initialization can produce delayed generalization; larger datasets can remove the delay; norm constraints can suppress the dramatic delay. For a regularization-dominated radial-decay approximation, time scales inversely with decay strength. This does not establish a universal explanation for every optimizer/task.
- Nonalgorithmic examples: MNIST, IMDb sentiment, QM9 isotropic polarizability. They describe weaker grokking signals in modified setups, not a universal default-training phenomenon.
- Appendix A: MNIST width-200 depth-3 ReLU MLP, MSE, AdamW LR 1e-3, batch size 200. IMDb: 1,000 most frequent words; pad to 500; two-layer LSTM, embedding 64, hidden 128; Adam LR 1e-3, binary cross-entropy; hold out 25%. QM9: two graph-convolution layers with ReLU then linear head; Adam LR 1e-3, MSE; 50/50 train/test split. Do not silently replace these with benchmark-default splits and still label an exact reproduction.
- For transformer reduced-landscape analysis: mod 113, one layer, width 128, four heads, MLP 512/ReLU, LR 1e-3; Appendix B reports an approximate critical training fraction 0.25 under its norm-constrained setup. This value is not universal.
- Author-reported code: `https://github.com/KindXiaoming/Omnigrok` (printed p. 2; not visited).
- Novelty caveat: initialization-norm controls, nonalgorithmic grokking, and train-data-size dependence have already been explored.

## [P4] 2309.02390 — Explaining grokking through circuit efficiency

Source: https://arxiv.org/pdf/2309.02390 ; PDF v1, 5 Sep 2023. Read central explanation pp. 1–4, predictions/evidence pp. 6–10, limitations pp. 11–13, experimental details pp. 16–17, proxy limitations p. 22.

### Mechanistic claim
- Three ingredients: a memorizing and a generalizing circuit both fit training data; generalizing circuits obtain a given logit/loss scale at lower parameter norm; generalizing circuits are learned more slowly.
- With weight decay, more norm-efficient circuits are preferred. Memorizing-circuit efficiency is predicted to worsen with dataset size; generalizing-circuit efficiency is approximately size-independent. A crossing motivates a critical dataset size Dcrit, semi-grokking, and ungrokking.
- This is not a claim that parameter count equals efficiency, nor that Dcrit is a universal architectural constant. They explicitly state weight-decay-free grokking is a limitation of the proposed explanation.

### Verified protocol/results
- Modular addition mod 113, 12,769 equations. Appendix A input is `x op y =` (four tokens); unlike P2, it explicitly includes an operator token. Random train fraction, remaining equations test; final-answer cross-entropy.
- One-layer decoder-only transformer; learned positions, untied embed/unembed; width 128, head dimension 32, four heads, MLP 512. Full-batch AdamW; betas (0.9,0.98), LR 1e-3, weight decay 1 unless varied. Appendix A does not itself state all normalization/activation choices, so do not invent them.
- Efficiency comparison: random training labels to isolate memorization; large train datasets with >95% logit norm in the trigonometric subspace to isolate generalization. Compare correct logits and parameter norms across seed, dataset size, and decay. Seed variance is substantial.
- Ungrokking: train to convergence on the **full** equation table, then continue on smaller subsets. This tests retention/forgetting, not fresh-test generalization: the eventual test inputs were seen during full-table pretraining. Figure 4 varies decay over 0.1,0.5,1,1.5,2; convergence performance roughly insensitive to those values in that setting. Do not extrapolate to zero decay or finite-time invariance.
- Semi-grokking: 10 seeds at each of 20 training sizes evenly spaced 1,500–2,050; 200 runs. Figure 5 reports at least six clear semi-grokking examples; curves extend to tens of millions of epochs. Many intermediate plateaus ultimately become full generalization.
- Appendix A.2: semi-grokking and ungrokking can suggest different boundaries for the same seed; dynamics and initialization alter discovered circuits. Therefore a single history-independent critical-size constant is oversimplified.
- Proxy flaws p. 22: Fourier projections can capture correlated memorization logits and overestimate generalization strength; raw correct logits ignore wrong-class logits. Recommend matched loss or gauge-invariant logit margins, with careful parameterization controls, rather than raw correct-logit/norm ratios alone.
- No source-code availability claim was verified in the sections read. No external code consulted.
- Novelty caveat: critical **training-dataset** size, semi-grokking, ungrokking, and seed/history dependence are existing results, not new proposed discoveries.

## [P5] 2310.06110 — Grokking as the transition from lazy to rich training dynamics

Source: https://arxiv.org/pdf/2310.06110 ; PDF v3, 11 Apr 2024, ICLR 2024. Read pp. 1–7, implementation/controls pp. 13–14, adaptive-optimizer caveat p. 20.

### Verified mechanism and controls
- Demonstrates grokking under vanilla GD, no weight decay, and **increasing** weight norm. Thus weight-norm reduction and Adam-specific anomalies are not necessary conditions in general.
- Explanation: initially poor fixed/kernel features fit train data, then later feature learning improves held-out performance. Key controls are output scale/laziness alpha, initial kernel–target alignment, and a dataset size permitting eventual but not immediate generalization.
- Polynomial toy: isotropic Gaussian inputs with covariance I/D, target `(beta_star dot x)^2/2`; committee machine is `alpha/N * sum_i phi(w_i dot x)`, `phi(h)=h + epsilon*h²/2`, fixed unit readouts. First and second weight moments suffice for its risk decomposition. This is not modular classification or an AdamW theorem.
- Can compare nonlinear training with an initialized linearized/NTK baseline, track kernel–target alignment, weight-moment alignment, and relative parameter movement.
- **Critical implementation detail**, Appendix 8.1 p. 13: use centered predictor `alpha * (f(theta,x) - f(theta0,x))` and scale GD LR as `eta0/alpha²` to equalize initial timescales. Omitting either can turn a laziness study into an initial-logit or learning-rate confound. Do not assume this GD scaling transfers exactly to AdamW.
- Appendix 8.3 pp. 13–14: modular-addition counterexample uses concatenated one-hot inputs of dimension 2p, p-dimensional outputs, one hidden layer width 100, p=23 illustrated, 90% of p² pairs train, 10% test, LR 100, vanilla GD, no weight decay. Context uses MSE; activation and other missing details must not be guessed from this short recipe.
- Appendix 14 p. 20 calls adaptive-optimizer analysis more speculative; their AdamW transformer can deviate from the linearization early despite grokking. The lazy-to-rich transition is a sufficient, not necessary, mechanism in general settings.
- Main text warns regression 'accuracy' can be made dramatic by arbitrary tolerance selection. Always retain continuous held-out loss.
- No repository/code availability verified in the sections read. Exact toy N/D/P values for every plotted run were not established; do not fabricate them.
- Novelty caveat: output scaling, initialization controls, NTK-alignment tests, and GD/no-decay counterexamples are prior work. Width changes can also change laziness, so width alone does not isolate representational capacity.

## [P6] 2303.06173 — Unifying Grokking and Double Descent

Source: https://arxiv.org/pdf/2303.06173 ; PDF v1, 10 Mar 2023; PDF identifies an ML Safety Workshop, NeurIPS 2022 contribution. Read pp. 1–4 and Appendix B p. 8.

### Verified result directly relevant to a size experiment
- Explicitly demonstrates **model-wise grokking** by varying transformer embedding dimension, alongside epoch-wise grokking. Fig. 4 is a size-by-training-step heatmap; Fig. 5 is a fixed long-training-budget cross-section. Therefore merely showing a size-dependent grokking transition is not a defensible novelty claim even within this restricted reading set.
- Dataset: modular division mod 97; symbolic residues; answer-only loss/accuracy. Model: causal decoder-only, default two layers, width 128 unless varied, **one** attention head. Typical budget 400,000 optimization steps; AdamW betas (0.9,0.98), LR 1e-3, weight decay **1e-5**. This differs sharply from the weight-decay-1 baselines.
- Text/figure uses 'epochs' in places while appendix says optimization steps. For a reproduction, explicitly log updates, epochs and examples processed rather than treating them as synonyms. Appendix B as read does not specify batch size, training fraction, or number of seeds for every width; exact reproduction cannot be claimed with invented values.
- Explains double descent/grokking using patterns with different learning speeds/generalization. Main conceptual framework is not a universal theorem equating width and time.
- A simple early division heuristic (`0/b=0`) causes a small early accuracy peak; log-scaled accuracy and loss reveal behavior otherwise missed.
- No repository/code availability verified. Novelty caveat: both data-size tradeoffs (P1) and model-size-by-time effects (this paper) are already in the allowlist.

## [P7] 1711.05101 — Decoupled Weight Decay Regularization (AdamW)

Source: https://arxiv.org/pdf/1711.05101 ; PDF v3, 4 Jan 2019, ICLR 2019. Read pp. 1–3 and experimental comparison pp. 5–8.

### Verified methodological lesson
- For standard SGD, L2 regularization and multiplicative decay can be reparameterized equivalently. For adaptive methods such as Adam, adding `lambda*theta` to the gradient changes the moments/preconditioning and is generally not equivalent to decoupled parameter shrinkage.
- Algorithm 2 separates adaptive gradient update from parameter decay. **Notation/API caveat:** its decay coefficient and schedule convention cannot be assumed identical to a framework keyword. Define the actual one-step update, parameter groups, LR schedule and multiplicative shrinkage; otherwise a nominally identical 'weight decay' can be very different.
- Their non-grokking image classification evidence uses CIFAR-10 and ImageNet32x32, Top-1/Top-5 error as appropriate, with fixed/drop-step/cosine schedules and 100–1,800-epoch budgets. The paper reports approximately 15% relative test-error improvement for AdamW over Adam in its evaluated setups. This is not an expected modular-arithmetic effect size.
- Optimal decay depends on run length; schedule and decay convention must be controlled in size/time comparisons.
- Author-reported experiment code: `https://github.com/loshchil/AdamW-and-SGDW` (p. 1; not visited). Other embedded links/citations were not followed or treated as consulted sources.
- Novelty caveat: decoupled decay is an established baseline, not a proposed new optimization method.

## Cross-paper evaluation safeguards (recommendations, not claimed prior results)

1. Fix one dataset/modulus/tokenization and document intentional changes. Do not combine P2's three-token setup, P4's four-token setup, and P1's two-layer minibatch setup under one 'exact reproduction' label.
2. Distinguish model parameter count, width, norm and training-example count. Report actual parameter counts and the effect of width on initialization/output scale and optimizer updates.
3. Match seeds and splits across widths. For autonomous tuning, reserve a separate validation subset and untouched final test, or explicitly describe results on the historical complement as exploratory. Logged evaluation alone is not training leakage, but using it for model selection makes it validation data.
4. Record train/held-out cross-entropy and accuracy, parameter norms, first and sustained threshold-crossing times, final performance, update count, tokens/examples seen, wall time and estimated compute. Include failed seeds; no-grokking by budget is right-censored, not an infinite threshold or a proven absence.
5. Report step-matched and compute-matched size comparisons separately. More parameters at fixed updates generally use more compute. Avoid selecting the best checkpoint by final-test performance.
6. Analyze seed-level trajectories and success fractions rather than only seed-averaged curves. Narrow phase boundaries and transient semi-grokking can be averaging artifacts.
7. Accuracy and loss are both necessary. No held-out probability-calibration protocol (temperature fitting/ECE/Brier) was established from the sections read. If calibration is added, predeclare the metric and fit any temperature only on validation data; report uncalibrated loss too.
8. Fourier diagnostics and NTK alignment are task/parameterization-dependent and can be expensive. A dense NTK over 12,769 scalar-output inputs alone has about 163 million entries (~0.65 GB float32); a multiclass/Jacobian construction can cost much more. Use a fixed diagnostic subset and report it; do not label a proxy as an exact full NTK.
9. A new contribution would need a sharpened, independently tested question beyond a generic size sweep. This restricted reading cannot certify novelty against unconsulted literature.
