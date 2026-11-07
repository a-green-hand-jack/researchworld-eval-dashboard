# NeurIPS 2026 checklist: what each question needs from this study

Suggestions only; `paper-repo` writes the answers in `checklist.tex` (copy of `template/checklist.tex`), and `internal-review-repo`
should check them against the finished paper. An answer of Yes must point to sections; do not answer Yes for something the
paper does not contain. "Source" = who must supply the evidence.

| # | Question (short) | Likely honest answer | Needs |
|---|---|---|---|
| 1 | Claims match contributions/scope | Yes, only if abstract/intro state the hypothesis, the width range, the task(s), and that the result is supported/refuted/conditional as measured | paper-repo; story-repo's predictions verdicts |
| 2 | Limitations discussed | Yes: separate Limitations section (single/few tasks and `p`, CPU-scale models, optimizer/regularization fixed, seed count, censoring of runs that never generalize) | paper-repo |
| 3 | Theory proofs | N/A if no theorem; if a heuristic argument is given, say it is not a proof | paper-repo |
| 4 | Reproducibility of main results | Yes only if architecture, optimizer, lr, weight decay, batch, train fraction, `p`, seeds, steps, and the generalization-time definition (threshold, evaluation interval, censoring rule) are all in paper/appendix | experiment-repo (values), paper-repo |
| 5 | Open access to data and code | Code is in the delivery; data are generated in memory. Yes with the anonymous-code caveat: no identifying URLs in the PDF | experiment-repo, paper-repo |
| 6 | Training/test details | Yes: split rule (random train/validation split of the p^2 pairs, fraction), hyperparameter selection, optimizer | experiment-repo |
| 7 | Error bars | Yes only if every plotted/tabulated quantity carries a defined uncertainty (seeds, CI type, test) and censored runs are handled stated; otherwise No with justification | experiment-repo, figtab-repo |
| 8 | Compute resources | Yes: CPU type/cores/memory, per-run and total time (measured, from experiment-repo's logs; not the objective's rough estimate) | experiment-repo |
| 9 | Code of ethics | Yes, no human subjects, synthetic data | paper-repo |
| 10 | Broader impacts | Short honest statement (foundational study, no direct deployment; N/A is acceptable with justification) | paper-repo |
| 11 | Safeguards | N/A (no high-risk model/data release) | paper-repo |
| 12 | Licenses of existing assets | Yes/N/A: name used libraries (PyTorch etc.) with versions and licenses; data are synthetic, no third-party data; any reused code (e.g. an AdamW or a reference implementation) must be cited | experiment-repo, paper-repo |
| 13 | New assets documented | Yes if the code ships with the reproduction document | paper-repo |
| 14 | Crowdsourcing/human subjects | N/A | paper-repo |
| 15 | IRB | N/A | paper-repo |
| 16 | LLM usage | An LLM is not part of the studied method (small transformers trained on synthetic data), so N/A with that justification is expected. If agents wrote substantial parts of the code or analysis, say so in the reproduction document anyway (honest reporting) | paper-repo |

Mechanical requirements: remove the instruction block; leave no `\answerTODO{}`/`\justificationTODO{}`; do not edit questions or
guidelines. A grep for `TODO` in the built source must return nothing.
