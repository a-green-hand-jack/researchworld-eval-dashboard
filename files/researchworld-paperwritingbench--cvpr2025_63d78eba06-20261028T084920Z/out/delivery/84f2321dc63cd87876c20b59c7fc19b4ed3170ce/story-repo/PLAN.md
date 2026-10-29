# Study plan: source-free machine unlearning paper (CVPR 2025 template)

Objective (issue #1): write the paper from the supplied idea, experimental log, guidelines and one figure; deliver `template.tex`, `references.bib`, compiled `template.pdf`. Facts come only from the supplied material; literature cutoff 2024-11; anonymous placeholder author; 8 pages main text excluding references/appendix; every cited key real and in `references.bib`; figure only `figures/figure_1.png`.

## Division of work
| Function | Position | Delivers |
|---|---|---|
| context | idea-repo | Brief: claims the idea supports, the method written out (Newton/influence update, perturbation-based Hessian estimation, SDP), the real pre-2024-11 literature to cite with verified bibliographic data (machine unlearning, influence functions/Newton unlearning, zero-shot/source-free unlearning, baselines NegGrad, Random Labels, JiT, Adversarial), and CVPR conventions |
| analysis | experiment-repo | Claim-to-evidence map over the log: which numbers support which claim, gaps computed from the log, and where the log does not support a claim (e.g. 15% forget gap of 14-15%, Mixed Linear remaining-accuracy gaps of 2-7%, inconsistent forget/rem. accuracy across tables, no seeds/error bars, Unlearned(+) absent from linear tables). Recompute every gap. No new numbers beyond the log. |
| presentation | figtab-repo | LaTeX table sources (booktabs, CVPR column widths) for each log table and a caption/placement spec for `figures/figure_1.png` (caption in `figures/info.json`); handed to paper-repo as content |
| venue, report | paper-repo | `template.tex`, `references.bib`, `template.pdf`: anonymity, 8-page limit, compile cleanly, all numbers matching the log |
| review, external-review | internal-review-repo | Check against the objective (log fidelity, citation reality, date cutoff, page limit, anonymity) |

## Delivered paths (`.forgejo/CODEOWNERS` in paper-repo, PR #2)
`template.tex`, `template.pdf`, `references.bib` -> paper-repo. No other delivered paths: tables are inline in `template.tex`; others supply content through their repositories.

## Honesty rules for all positions
Report weak results as weak (large gaps at 15% forget set, fragile with few perturbations). Do not claim theory not present in the idea (state bounds only as the idea/log describe them). Do not invent datasets, seeds, hyperparameters, or compute figures beyond the log (RTX 3090 is stated).

## Order
1. idea-repo brief + bibliography candidates; experiment-repo claim map (parallel).
2. figtab-repo tables; paper-repo drafts using these.
3. paper-repo compiles and opens version PR; internal review.

## Decisions after the Brief (idea-repo#.. / story-repo#4)
- Gap reference: every "Performance Gap" is stated as |Retrained − Unlearned(−)|. The mixed-linear CIFAR-100 log rows are |Unlearned(+) − Unlearned(−)|; the paper recomputes gaps vs Retrained from the table's own values (Brief §5) and says so; no mixed-up definitions.
- Claim wording: "comparable to Retrained" is a CIFAR-10 / small-forget-set claim; figure_1 shows Unlearned(−) ~2-7 points below Retrained on CIFAR-100, Dogs and Caltech-256 — report as such. Unlearned(−) vs Unlearned(+) is the closer match.
- No invented material: SDP explicit form, perturbation scale, theorem proofs, seeds/error bars, MIA protocol stay at the level of idea.md and the log; limitations section says so (one run per setting).
- Page budget: main text = method, figure_1, baseline comparison table, forget-size table, mixed-linear table. Perturbation and lambda ablations go in the main text only if the 8 pages hold, otherwise in the appendix (excluded from the limit, but referenced from the main text).
- Citations only from idea-repo `context/candidate_references.md` (verified); anything else paper-repo verifies itself before use.

## Decisions after the audit (experiment-repo `analysis/`, commit d21428219336)
- Binding reading of the log: `analysis/README.md` sections A (facts), B (claim support), C (disclosures). Gaps are |Unl(−) − Retrained| (CIFAR-10); mixed-linear gaps vs Retrained are 2.2/4.3/0.6/0.8 (20%), 1.7/1.2/1.1/1.5 (15%), 0.9/1.9/2.7/2.3 (10%); the log's 0.1–0.5 test gaps are vs Unl(+) and support only "estimated Hessian ≈ exact Hessian".
- Say "single run, no intervals"; integer CIFAR-10 cells make ≤1 pt differences uninterpretable; the 10% / 500-perturbation / λ=0 rows are one shared configuration, not three runs.
- Failures stay visible: 15% forget set and 250 perturbations; MIA does not separate the baselines (47–50).
- Figure 1: only panel (a) has log numbers; panels (b)–(d) accuracy is 2–7 pts below Retrained, so wording is "comparable in MIA; accuracy within 2–7 pts". The model behind the figure is not stated: do not call it mixed-linear. Pixel read-outs are not measurements.
- Theory: direction only (gap grows with forget size, shrinks with perturbations and λ); no formula such as 1/λ², no "validated bound". No efficiency or single-instance claim.
