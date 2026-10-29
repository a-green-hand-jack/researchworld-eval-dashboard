# Experimental-log facts (verbatim from the task's [EXPERIMENTAL LOGS])

Provenance: copied verbatim from `/initial-state/inputs/0/INSTRUCTIONS.md` ("[EXPERIMENTAL LOGS]" §2 and §3); nothing added to the numbers. Every number the paper reports must equal one in this file (or be a plain difference computed from them, with the computation stated). Annotations by idea-repo are in the final section, marked as *inference* or *check*.

## 2. Raw Numeric Data

**Ablation Study: Effect of Forget Data Size (CIFAR-10)**
*We measured the performance gap between the Retrained model and our Unlearned(-) method while varying the percentage of the training set marked for forgetting.*

| Method | Forget Set Size | Test Accuracy | Remaining Accuracy | Forget Accuracy | MIA Score |
| :--- | :--- | :--- | :--- | :--- | :--- |
| Retrained | - | 73% | 75% | 73% | 50% |
| Unlearned (-) | 15% | 59% | 60% | 59% | 55.8% |
| **Performance Gap** | | **14%** | **15%** | **14%** | **5.8%** |
| | | | | | |
| Retrained | - | 72% | 74% | 72% | 50% |
| Unlearned (-) | 10% | 70% | 71% | 68% | 51.4% |
| **Performance Gap** | | **2%** | **3%** | **4%** | **1.4%** |
| | | | | | |
| Retrained | - | 73% | 74% | 73% | 49.4% |
| Unlearned (-) | 5% | 73% | 74% | 73% | 49.4% |
| **Performance Gap** | | **0%** | **0%** | **0%** | **0%** |

**Ablation Study: Effect of Number of Perturbations (CIFAR-10)**
*We analyzed how the number of random perturbations used to approximate the Hessian affected unlearning performance.*

| Method | Perturbations | Test Accuracy | Remaining Accuracy | Forget Accuracy | MIA Score |
| :--- | :--- | :--- | :--- | :--- | :--- |
| Retrained | N/A | 72% | 74% | 72% | 50% |
| Unlearned (-) | 250 | 57% | 58% | 57% | 56.2% |
| **Performance Gap**| | **15%** | **16%** | **15%** | **6.2%** |
| | | | | | |
| Unlearned (-) | 500 | 70% | 71% | 68% | 51.4% |
| **Performance Gap**| | **2%** | **3%** | **4%** | **1.4%** |
| | | | | | |
| Unlearned (-) | 1000 | 72% | 74% | 71% | 49% |
| **Performance Gap**| | **0%** | **0%** | **1%** | **1%** |

**Ablation Study: Effect of L2 Regularization ($\lambda$)**
*We tested the impact of the regularization parameter on the performance gap.*

| Method | $\lambda$ Value | Test Accuracy | Remaining Accuracy | Forget Accuracy | MIA Score |
| :--- | :--- | :--- | :--- | :--- | :--- |
| Retrained | N/A | 72% | 74% | 72% | 50% |
| Unlearned (-) | 0 | 70% | 71% | 68% | 51.4% |
| **Performance Gap**| | **2%** | **3%** | **4%** | **1.4%** |
| | | | | | |
| Unlearned (-) | 0.0005 | 71% | 72% | 71% | 49.8% |
| **Performance Gap**| | **1%** | **2%** | **1%** | **0.2%** |
| | | | | | |
| Unlearned (-) | 0.001 | 72% | 73% | 72% | 50.9% |
| **Performance Gap**| | **0%** | **1%** | **0%** | **0.9%** |

**Performance on Mixed Linear Networks (CIFAR-100, ResNet-18)**
*We evaluated the method on neural networks by linearizing the last few layers of ResNet-18 on CIFAR-100.*

| Method | Forget Set Size | Test Accuracy | Remaining Accuracy | Forget Accuracy | MIA Score |
| :--- | :--- | :--- | :--- | :--- | :--- |
| Retrained | 20% | 62.2% | 65.7% | 62.6% | 50% |
| Unlearned (+) | 20% | 60.1% | 63.4% | 59.3% | 50.4% |
| Unlearned (-) | 20% | 60% | 70% | 63.2% | 50.8% |
| **Performance Gap**| | **0.1%** | **6.6%** | **3.9%** | **0.4%** |
| | | | | | |
| Retrained | 15% | 63.1% | 68.9% | 63.3% | 50.2% |
| Unlearned (+) | 15% | 61.9% | 67.9% | 62.2% | 50.7% |
| Unlearned (-) | 15% | 61.4% | 70.1% | 62.2% | 51.7% |
| **Performance Gap**| | **0.5%** | **2.2%** | **0.0%** | **1.0%** |
| | | | | | |
| Retrained | 10% | 63.7% | 72% | 63.9% | 50% |
| Unlearned (+) | 10% | 63.3% | 72.5% | 64.9% | 51% |
| Unlearned (-) | 10% | 62.8% | 70.1% | 61.2% | 52.3% |
| **Performance Gap**| | **0.5%** | **2.4%** | **3.7%** | **1.3%** |

**Comparative Analysis Against Source-Free Baselines (CIFAR-10)**
*We compared our Unlearned(-) method against existing source-free unlearning approaches using a linear classifier with 10% forget data.*

| Method | Test Accuracy | Remaining Accuracy | Forget Accuracy | MIA Score |
| :--- | :--- | :--- | :--- | :--- |
| Retrained | 72% | 74% | 72% | 50% |
| NegGrad | 51.9% | 53.2% | 51.2% | 48% |
| Random Labels | 20.6% | 21.6% | 21.4% | 47% |
| JiT | 52.1% | 53.1% | 51.1% | 49.1% |
| Adversarial | 51.5% | 52.7% | 51.0% | 50.0% |
| **Unlearned (-)** | **70%** | **71%** | **68%** | **51.4%** |


## 3. Qualitative Observations

*   **Observation on General Efficacy:** Across all four datasets (CIFAR-10, CIFAR-100, Stanford Dogs, CalTech-256) with 10% forget data, the source-free Unlearned(-) model showed performance closely matching that of the Unlearned(+) model (which uses the true Hessian).
*   **Observation on Retraining Comparison:** The Unlearned(-) model consistently yielded results comparable to the Retrained model (training from scratch), indicating successful unlearning without source data access.
*   **Observation on Forget Set Scalability:** We observed that increasing the percentage of forget data (from 5% to 15%) caused the performance gap between the Retrained and Unlearned(-) models to widen. At 5%, the gap was negligible (0%); at 15%, the gap increased significantly (14-15%). This aligns with our theoretical bound regarding the number of forget samples.
*   **Observation on Perturbation Quantity:** Increasing the number of random perturbations (from 250 to 1000) during Hessian estimation positively influenced unlearning performance. At 1000 perturbations, the performance gap was nearly eliminated (0-1%), validating that better sampling leads to a more accurate Hessian approximation.
*   **Observation on Regularization:** Increasing the L2 regularization parameter $\lambda$ led to a reduction in the performance gap between the unlearned and retrained models. This confirmed the theoretical finding that the upper bound on the gradient norm is inversely proportional to $\lambda^2$.
*   **Observation on Neural Network Applicability:** In the Mixed Linear Network experiments (ResNet-18 on CIFAR-100), our method approximated the exact remaining Hessian well even without access to remaining data. The performance gap remained low (0.1% to 0.5% on Test Accuracy) across varying forget sizes.
*   **Observation on Baseline Comparison:** Our method significantly outperformed competing source-free methods (NegGrad, Random Labels, JiT, Adversarial) in maintaining utility (Test and Remaining accuracy) while achieving an MIA score close to the ideal 50%. Other methods often resulted in severe degradation of model utility (e.g., Random Labels dropped to ~20% accuracy).


---
## idea-repo annotations (checked arithmetic on the log; not new measurements)

Gap rows, recomputed:
| Table | Row | Logged gap | Recomputed vs Retrained | Recomputed vs Unlearned(+) |
|---|---|---|---|---|
| Forget size 15% | test/rem/forget/MIA | 14/15/14/5.8 | 14/15/14/5.8 OK | – |
| Forget size 10% | | 2/3/4/1.4 | 2/3/4/1.4 OK | – |
| Forget size 5% | | 0/0/0/0 | 0/0/0/0 OK | – |
| Perturb 250 | | 15/16/15/6.2 | 15/16/15/6.2 OK | – |
| Perturb 500 | | 2/3/4/1.4 | OK | – |
| Perturb 1000 | | 0/0/1/1 | 0/0/1/1 OK | – |
| λ=0 / 0.0005 / 0.001 | | 2/3/4/1.4 ; 1/2/1/0.2 ; 0/1/0/0.9 | all OK | – |
| Mixed-linear 20% | | 0.1/6.6/3.9/0.4 | 2.2/4.3/0.6/0.8 (**differs**) | 0.1/6.6/3.9/0.4 OK |
| Mixed-linear 15% | | 0.5/2.2/0.0/1.0 | 1.7/1.2/1.1/1.5 (**differs**) | 0.5/2.2/0.0/1.0 OK |
| Mixed-linear 10% | | 0.5/2.4/3.7/1.3 | 0.9/1.9/2.7/2.3 (**differs**) | 0.5/2.4/3.7/1.3 OK |
→ The mixed-linear "Performance Gap" rows are |Unlearned(+) − Unlearned(−)|, not gaps to Retrained. Any statement "gap to retraining is 0.1–0.5%" for the mixed-linear table would be wrong; the gap to Retrained (test acc) is 2.2 / 1.7 / 0.9 points for 20/15/10%. (The log's observation text says "performance gap remained low (0.1% to 0.5% on Test Accuracy)" — true only as the (+)/(−) gap.)

Consistency notes:
- Identical row (70 / 71 / 68 / 51.4): forget-size 10%, perturbations 500, λ=0, baseline table Unlearned(−). *Inference*: the default configuration is 10% forget, 500 perturbations, λ=0.
- The Retrained reference differs between ablations (forget size: 73/75/73/50 at 15%, 72/74/72/50 at 10%, 73/74/73/49.4 at 5%; perturbation and λ and baseline tables: 72/74/72/50). *Inference*: separate trainings; no seeds / repetitions / variance are logged. Report as single runs.
- At 5% Unlearned(−) and Retrained rows are identical (73/74/73/49.4), as logged.
- Mixed-linear: Unlearned(−) remaining accuracy (70, 70.1, 70.1) exceeds Retrained's at 20% (65.7) and 15% (68.9), and is below at 10% (72). Unlearned(+) is also 1–3 points below Retrained on test acc.
- Baseline table (CIFAR-10, 10%): NegGrad, JiT and Adversarial reach test accuracy 51.5–52.1 (≈20 points below Retrained's 72) and Random Labels 20.6; their MIA scores are 47–50 (Adversarial 50.0, i.e. MIA alone would rate it ideal despite the accuracy loss). Unlearned(−) test 70 vs Retrained 72. Forget accuracy 68 vs 72 Retrained.
- MIA "score": definition not logged (assumed accuracy of an attack classifier; 50 = indistinguishable). Do not define more than the log does.
- Figure 1 (`figures/figure_1.png`, 4 panels, bars: Retrained / Unlearned(+) / Unlearned(−) × test/remaining/forget/MIA). Panel (a) CIFAR-10 reads ≈ Retrained 72/74/72/50, (+) ≈ 70/72/70/50, (−) ≈ 70/71/68/51.5, matching the 10% rows. Panels (b)–(d) have no logged numbers (readings from the image: CIFAR-100 Retrained test ≈56, (+) ≈50, (−) ≈51.5; StanfordDogs ≈59/55/55; Caltech256 ≈54/48/49.5) — so there the (+)/(−) values are ≈1–3 points below Retrained on test acc and the (−) forget accuracy is also lower. The CIFAR-100 panel does not equal the mixed-linear CIFAR-100 table (62–64 test); *inference*: figure = linear classifier on frozen features, table = mixed-linear network; the log does not say.
- The "theoretical bound" statements in the log (gap grows with number of forget samples; gradient-norm bound ∝ 1/λ²; error shrinks with number of perturbations) are *claims by the log*, with no formula, assumptions or proof provided.
- Unlogged (do not invent): seeds/error bars, learning rate / epochs for Retrained and baselines, quadratic-loss targets (one-hot?), Gaussian perturbation scale, SDP solver, λ for the main runs, which ResNet-18 layers are linearised, MIA implementation, wall-clock, forget-set sampling beyond "random".
