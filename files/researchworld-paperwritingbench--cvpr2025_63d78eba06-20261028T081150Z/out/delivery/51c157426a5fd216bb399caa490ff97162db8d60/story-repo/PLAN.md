# Commitment (story-repo, plan)

Objective: a CVPR-2025-format paper (template.tex, references.bib, template.pdf; ≤8 pages main text, anonymized, literature ≤ 2024-11, every number matching the supplied experimental log) on source-free instance-level unlearning (Newton update + perturbation/SDP Hessian estimate of the retained data).

## Division of work (proposed in paper-repo PR #2, .forgejo/CODEOWNERS)
- `template.tex`, `references.bib`, `template.pdf`: **paper-repo** (report/venue). Also owns cvpr.sty, preamble.tex, ieeenat_fullname.bst, which are copied unchanged from /initial-state.
- `figures/*`, `tables/*`: **figtab-repo** (presentation). `figures/figure_1.png` is supplied (copy unchanged; caption from figures/info.json). Tables are delivered as `tables/*.tex` fragments (booktabs, `\input`-able, no packages added) that paper-repo includes.
- Analysis (experiment-repo): no delivered path; it feeds figtab-repo and paper-repo with verified numbers.
- idea-repo: Brief + related-work/citation material (real, pre-2024-11 references with verified BibTeX) feeding paper-repo.

## Study plan: what the paper must answer (claims -> evidence, all from the log only)
C1 Source-free Unlearned(-) ≈ Unlearned(+) ≈ Retrained at 10% forget on CIFAR-10/100, StanfordDogs, Caltech256 (Fig. 1; only qualitative numbers exist — no per-dataset numbers beyond those in the log; must not be invented).
C2 Forget-set size ablation (CIFAR-10, 5/10/15%): gap widens with size (0% -> 2–4% -> 14–15%).
C3 Number of perturbations (250/500/1000): gap shrinks (15-16% -> 2-4% -> 0-1%).
C4 L2 regularization (0/0.0005/0.001): gap shrinks.
C5 Mixed linear networks (ResNet-18 last layers, CIFAR-100, 20% and 15%): Unlearned(-) vs (+) vs Retrained.
C6 Baseline comparison (NegGrad, Random Labels, JiT, Adversarial) vs Unlearned(-) with MIA near 50%.
Integrity points to resolve before writing (experiment-repo to check log, report to paper-repo): 
 - arithmetic of every "Performance Gap" row; in the mixed-network table the 20% gap row (0.1/6.6/3.9/0.4) matches |Unlearned(-) − Unlearned(+)| on remaining/forget, not Retrained (70 vs 65.7 = 4.3) — state the reference of each gap explicitly;
 - the 10% row in the forget-size/perturbation/lambda ablations is the same configuration (70/71/68/51.4) — present it consistently; the "Retrained" reference rows differ slightly across tables (72–73%);
 - the log claims inverse λ^2 bound and "theoretical bound on #forget samples": the paper may only state theory that the idea file supports (bounded Hessian-estimation error, no new proofs/constants invented);
 - baseline table: view the full table in /initial-state INSTRUCTIONS.md (only partly above) and report all rows;
 - weak/negative: 15% on CIFAR-10 (14–15% gap), 250 perturbations, and mixed-network remaining-accuracy overshoot (70% vs 65.7%) must be reported honestly.
Method section is derived only from idea.md (Newton/influence update, Gaussian perturbations, SDP for retain-Hessian, linearization); no equations beyond what that supports without stating them as assumptions.

## Standard I will hold
Every requirement in the objective ends with a position; I review the CODEOWNERS file and open issues for gaps, I do not write the paper. I revise the split as positions answer.
