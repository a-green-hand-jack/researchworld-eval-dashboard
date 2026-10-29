# Study plan and division of work

Objective: issue #1. Deliverable: a CVPR-2025-format, anonymized, <=8-page (+refs) paper
`template.pdf` built from `template.tex` + `references.bib` (+ `figures/`), on source-free
(instance-level) machine unlearning with a perturbation-based Hessian estimate (SDP) for a Newton update.

## Hard constraints (from the task; the standard every handoff serves)
- Numbers must match the experimental log exactly; no fabrication; weak/negative results reported honestly.
- Literature: real papers only, published <= 2024-11; cite only keys in references.bib.
- Keep template packages / style unchanged; `\cref` for cross refs; figures as `figures/<name>`;
  author block exactly the placeholder given; no other identifying info.
- Page limit 8 (excl. references/appendix). `template.pdf` is what is evaluated: it must compile from the delivered tree.
- Do not use knowledge of any existing published paper on the topic; only the supplied idea + log + figure.

## Division (CODEOWNERS, PR paper-repo#2)
| Path | Owner |
|---|---|
| template.tex, template.pdf, references.bib, cvpr.sty, preamble.tex, ieeenat_fullname.bst | paper-repo |
| figures/ (figure_1.png and any new figure) | figtab-repo |
| tables/ (table sources `tables/*.tex`, `\input` by template.tex) | figtab-repo |
| analysis (no delivered path; feeds paper + figtab) | experiment-repo |
| literature/brief (no delivered path) | idea-repo |

## Questions the paper must answer, and where each is evidenced (log sections)
1. Does source-free Unlearned(-) approximate Unlearned(+) (true retain Hessian) and Retrained? -> Fig. 1 (4 datasets, 10%), mixed-linear table (CIFAR-100).
2. Does it beat source-free baselines (NegGrad, Random Labels, JiT, Adversarial)? -> comparison table (CIFAR-10, 10%).
3. How do gaps scale with forget fraction (5/10/15%)? -> forget-size ablation (gap widens: 0% -> 14-15%; a limitation, state it).
4. Effect of #perturbations (250/500/1000) -> perturbation ablation.
5. Effect of L2 lambda (0/0.0005/0.001) -> lambda ablation.
6. Does it apply beyond linear (linearized last layers of ResNet-18)? -> mixed-linear table.
Theory (idea.md): Hessian-estimation error bound; dependence on #forget samples and lambda. The log supports
these only qualitatively; theory statements must be presented as the idea.md states them and not as proven beyond it.

## Known issues in the log that the analysis must resolve before writing (see experiment-repo issue)
- Mixed-linear "Performance Gap" rows are gaps between Unlearned(-) and Unlearned(+) (e.g. 20%: |60.1-60|=0.1 test,
  |63.4-70|=6.6 remaining), NOT to Retrained, whereas the CIFAR-10 ablation gaps are to Retrained. Must be labelled correctly.
- Remaining accuracy of Unlearned(-) in mixed-linear is *higher* than Retrained (70 vs 65.7 at 20%): report, don't hide.
- The 10% / 500-perturbation / lambda=0 rows are the same run (70/71/68/51.4); the forget-size table's 5% row has Retrained==Unlearned exactly.
- Retrained rows differ between tables (73/75/73/50 vs 72/74/72/50): different runs; say so or tabulate per-experiment.
- Log claims "gap inversely proportional to lambda^2" / "matches theoretical bound": log shows 3 lambda values and a monotone trend only; wording must not overclaim. Baseline MIA values of 47-49% are further from 50 than only some arguments suggest; MIA of Unlearned(-) 51.4 is not "better" than JiT 49.1 / Adversarial 50.0 on MIA alone -- claim is utility-preserving.
- No variance / seeds in the log: no error bars may be invented; state single-run.
