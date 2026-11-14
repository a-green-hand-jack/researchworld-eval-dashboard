# Final reject-first self-review

## Reject-first assessment
A skeptical reviewer could reject this as a limited statistical case study: its central tools are standard, the real evidence comes from eight fixed prompts on one 600-item cache and an unauthenticated endpoint alias, the real naive interval does not undercover, and the real baseline cannot meaningfully stress false promotion. The replay does not demonstrate prospective audit isolation. These restrict novelty and empirical reach; they do not contradict the paper's explicitly narrowed claims. No exhaustive novelty judgment is possible under the restricted-source protocol, and none is asserted here.

## Verdict
**Evidence-consistent case-study deliverable; no remaining established factual or mathematical blocker found in this bounded review.** This is not a recommendation of conference acceptance or an independent proof certification. No new experiment or implementation repair is required. Human scientific accountability remains necessary before submission, as already disclosed.

## Claim–evidence checks

| Claim | Evidence and result |
|---|---|
| Primary synthetic optimism and undercoverage | `paper_numbers.json`, `tables/numbers.tex`, `tables/primary.tex`, and `synthetic_audit.md` agree: optimism 6.51 pp (MCSE 0.09 pp), naive coverage 83.95%, exact audit 96.60%. The audit identifies `syn_21`: equal p=0.7, latent rho=0.5. |
| Real primary result | `real_summary.csv`, `real_cache_2`, K=8/n=64/m=128: optimism 0.023171354..., naive coverage 0.959, exact 0.9635. Rounded 2.32 pp / 95.90% / 96.35% match the abstract, macros, and primary table. Section 6 explicitly avoids interpreting this as naive undercoverage. |
| Real false promotion | `prompt_summary.csv`: P0 has 493/600 successes; all other prompts have more. Primary nonpositive-effect frequency is 0.0745, consisting of self-comparisons. Zero false promotion is therefore uninformative as a real type-I stress test; Section 6 already says so. Synthetic null rates 10.85% versus 0.10% are separately supported by the synthetic audit. |
| Usage and identity | `inference_usage.json` and `usage_audit.json`: 4,800 completed cells, 40 format failures, 1,168,858 prompt tokens, 1,282,295 completion tokens; 1,292 calls exceed the requested 192, maximum 5,521. Manuscript and post-acquisition deviations agree. Earlier ledger cap language is explicitly superseded, not evidence of an enforced cap. Currency cost and model authentication remain unknown. |
| Delivery | `delivery_verification.json` reports PASS, 14 PDF pages, main text ending on page 8, 4,800 request-hash and score checks, and zero secret matches. These are recorded verification results, not newly rerun checks. Its references-begin field is null; no independent reference-page claim is made. |
| Final card | `report_card.json` matches the macros: P5, selection 87.50%, audit 83.59%, cohort 84.50%; accuracy [77.33,89.17]%, difference [-3.67,9.50] pp, truth +2.33 pp, discordances 6/2. The interval does not license promotion. Investigator-accessible replay is explicitly disclosed. |

## Joint-alpha and mathematical checks
- **Verified directly, not inferred from `evaluate`:** `code/run_experiments.py:129` uses `hg_table(N-n,m,.025)` for report-card accuracy. Lines 130–132 use `.0125` for each discordance marginal and map both targets back to the cohort. Failure budgets are 0.025 + 0.0125 + 0.0125 = 0.05: joint coverage at least 95% under the stated sampling/access contract.
- `code/statistics.py::evaluate` instead uses default 0.05 accuracy intervals and 0.025 per discordance marginal (line 66): separate marginal 95% accuracy and improvement claims, not a guaranteed joint 95% report. The paper distinguishes these correctly. The synthetic audit's conditional warning is not an unresolved report-card defect.
- The fixed-family expected-optimism argument, without-replacement moment bound, conditional tail inversion, affine cohort mapping, and paired Bonferroni argument reveal no blocking gap on inspection. Their assumptions are explicit; replay coverage does not establish prospective access integrity or fresh-population validity.
- Multiplier boundary failure (82.50%), heuristic guard status, unequal audit budgets, and limited B sensitivity are disclosed. Paired datasets do not imply nested Gaussian draws across B; no such nesting claim is made in the paper.

## Minimal fixes — optional, not applied
1. **Small reproducibility clarification:** Section 5 / Table 1 caption names K/n/m but does not explicitly identify the primary synthetic latent correlation. Add: “Primary iid cell: p_j=0.7 for all j, latent rho=0.5 (`syn_21`).” No numerical regeneration is needed.
2. **Small uncertainty clarification:** Table 1's 100.00 ± 0.00 coverage is a correct plug-in MCSE, not certainty of perfect coverage. Optionally add a footnote to that effect; the synthetic audit already supplies exact Monte Carlo intervals.

## Review boundaries
Read all eight requested evidence files, plus the requested experiment implementation, statistical primitives, primary table/macros, prompt summary, and report-card summary. Used prior observation `O-df730b1e46ee1416` only as orientation and rechecked the current alpha code. Followed a compact `paper-review` reject-first/source-consistency review. Local searches found no TODO, FIXME, or literal `\\todo` marker in `paper.tex`. No code interpreter was available; no comprehensive automated citation scan, PDF re-render, test rerun, new proof pipeline, or independent raw-cache recomputation was performed. No web, API, topical discovery search, experiment, or manuscript/code edit occurred. Only this review and the requested plan-update JSON were written.

## Final applied clarifications and local verification
- Added explicit primary iid p=.7 and latent rho=.5. Added exact binomial Monte Carlo coverage intervals to all summaries and clarified zero plug-in MCSE at100% coverage.
- Final verifier now extracts PDF text with pypdf; final main text ends on page8, references begin on page9, total14pages. All4800 request hashes and rescored outcomes pass, selected question IDs/labels are consistent, and no secret matches were found.
- Official table captions moved above tables; coverage-width panels share axes. An initial incorrect failure-panel legend was repaired with explicit plotted handles and visually inspected after regeneration. Final LaTeX has no overfull boxes or undefined citations/references.
- A dedicated paper-review expert dispatch failed with provider overload before yielding an artifact. The completed bounded review above was performed by planner-agent as a fallback, alongside the separate statistical analysis and proof critiques; it is not represented as a completed unavailable expert run.
