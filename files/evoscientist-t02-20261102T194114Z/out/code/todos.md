# Plan / protocol, before pilots

## Hypothesis: two-clock competition, not scale alone
Increasing hidden width increases capacity to interpolate early, but algorithm acquisition depends on regularization and feature learning. Consequently width may change the lag primarily through the memorization clock rather than by delaying algorithm acquisition. A universal claim that larger models necessarily grok later is falsified if the generalization clock advances or disappears under a regularization intervention.

Directional initial prediction P1 (to test, not assume): under fixed AdamW recipe, wider models fit earlier (T_fit decreases) and T_generalize does not decrease proportionally, so the log lag log(T_generalize/T_fit) grows. P2: removing weight decay should decouple eventual heldout accuracy from width, reducing successful delayed generalization at comparable horizon. P3: freezing hidden features should impair generalization if feature learning is necessary. These are conditional empirical predictions, not a mathematical theorem.

## Stage 1: calibration (exploratory)
Implement CPU two-layer, bias-free MLP with concatenated one-hot input, ReLU or quadratic activation, fullbatch CE, AdamW. Pilot p=31, train fraction .5, widths 32/128, learning rate .003, decay 1; up to 20k updates. Validate data partition, gradient/frozen control and timing. Calibrate architecture/horizon only with seed 0, explicitly keep pilots out of confirmatory summaries. Establish actual grokking baseline rather than pretend exact reproduction of transformer papers.
Success: functioning reproducible curves, interpolation, heldout rise, practical measured cost. If absent try quadratic activation (known algorithm-compatible feature map) then p=23, never hide failed pilot.

## Stage 2: locked width experiment
After pilots lock architecture, p, data fraction, lr, horizon, all initializations; record lock before seeds 1..5. At least 5 paired split/initialization seeds per width. Target widths 8,16,32,64,128,256; horizon chosen from calibration. Primary response restricted log-delay D=log10(max(T_gen,T_fit)/T_fit) only if both observed, plus fixed-horizon classification and censoring. Report T_fit and T_gen separately; no completed-only trend used alone. Prefer restricted time T*=min(T,H), difference log10(T_gen*/T_fit*) for all runs with flags. A non-fit run is not grokking.
Event definition: three consecutive recorded evaluations >=99% train (fit) or >=95% heldout (generalization). Event assigned first evaluation of qualifying triple. Grokking criterion ratio>=3 and initial fit; thresholds 90/95/99% and ratio 2/3/5 sensitivity. No early stopping. All non-events right censored at H.
Uncertainty: seed-level paired bootstrap, width Spearman per seed, 95% bootstrap intervals; descriptive 5-seed binomial intervals. Do not claim samples are independent test pairs.

## Stage 3: controls
At widths 32 and 128 at least 5 paired seeds: zero decay, frozen first layer. Secondary operation modular subtraction and second prime if affordable, plus learning-rate/initialization scaling sensitivity. One factor per experiment. Evaluate fixed train-steps vs elapsed compute separately. Additional controls only after locked main result, clearly exploratory.

## Stage 4: artifacts / analysis / write
Scripts create all tables/figures from saved raw trajectory CSV and JSON configs with seeds, hashes, runtime and package versions. Record failed attempts and protocol amendments. Paper in official ICML 2026 template (8 main pages) with abstract, introduction, related work, methods, experiments, discussion/limitations, references and appendix. Main result narrow to tested MLP family; no general transformer/LLM assertion.
Self-review novelty, censoring, data leakage, matched-seed dependence, width parameterization and norm confounds; fix rather than suppress contradictions.

## Pre-emptive rejection risks
- Width confounds initialization, capacity and dynamics: state conditional recipe; add controlled scaling/frozen-feature intervention.
- Selection bias: pilot seed 0 excluded, lock before new seeds.
- Censoring: no claims that non-event never occurs; show all runs.
- Weak novelty: no claim to first size study; allowed literature already connects model size and interpolation. Contribution is falsifiable, reproducible conditional mechanism audit.
- Evidence scope: no extrapolation beyond modulus, fraction, model/optimizer actually tested.

Commands/artifacts will be appended after implementation. Skills followed: paper-planning, experiment-pipeline; later paper-figures, paper-writing and paper-review. No code-agent delegated; main agent implements and tests directly (unattended setting).
