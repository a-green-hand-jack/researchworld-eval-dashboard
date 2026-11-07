# Completing the official NeurIPS 2026 checklist

The reference file is `templates/neurips2026/checklist.tex` from the official formatting ZIP. It contains 16 questions, which must be kept verbatim, with their headings and guidelines, in the manuscript's completed copy. Remove only the initial instruction block (between BEGIN/END INSTRUCTIONS); retain the `NeurIPS Paper Checklist` heading. Supply Yes/No/NA and a 1–2 sentence justification for each. This guide supplies evidence targets, not answers.

| # | Official question heading | Evidence the report owner should obtain before answering |
| --- | --- | --- |
| 1 | Claims | Abstract and introduction match measured findings, fixed conditional estimand and scope; distinguish found attack costs from certified minimum costs. |
| 2 | Limitations | Finite snapshots, perturbation scope, estimator conventions, uncertainty limitations, optimization/search limitations and cross-design confounding. |
| 3 | Theory assumptions and proofs | If theory is claimed, state assumptions and complete proof. An empirical paper may answer NA only if it makes no theoretical results; explain analytical approximations separately. |
| 4 | Experimental result reproducibility | Fully specified preprocessing, ranking fit, regularization, tie conventions, target selection, perturbation budgets, baselines and seeds. |
| 5 | Open access to data and code | Complete executable code and exact commands, public pinned acquisition/checksums, environment versions; raw data remains outside delivery. This task requires code even if the venue would tolerate its absence. |
| 6 | Experimental setting/details | Data design, eligibility/exclusions, matched comparisons, optimizer settings, convergence checks and all analysis parameters. |
| 7 | Experiment statistical significance | Define each source of variation, replicate unit/count, aggregation and interval calculation; explain dependence and what uncertainty does/does not cover. |
| 8 | Experiments compute resources | Actual CPU/memory and runtime per experiment/run plus total; distinguish measured runtimes from estimates and include preliminary/failed work. |
| 9 | Code of ethics | Read the applicable ethics guidance; do not assert universal conformity or institutional approval without support. |
| 10 | Broader impacts | Discuss trustworthy evaluation benefits and plausible misuse of leaderboard manipulation methods and safeguards; no required section title. |
| 11 | Safeguards | Assess what is released and its concrete risks; the existence of public preference data alone is not a reason to assert no risks or safeguards. |
| 12 | Licenses for existing assets | Creators, exact versions, source URLs and verified terms for every reused dataset/code/model/template; license not declared is not license inferred. |
| 13 | New assets | Document released study code/results and their usage, limitations and provenance. Do not choose a license on behalf of another owner. |
| 14 | Crowdsourcing and research with human subjects | Distinguish secondary analysis of existing public votes from newly recruited participants; explain applicability rather than inventing participant instructions or compensation. |
| 15 | Institutional review board (IRB) approvals or equivalent for research with human subjects | State actual secondary-data study context; never invent an IRB approval or blanket exemption. If not applicable, justify accurately. |
| 16 | Declaration of LLM usage | Explain actual agent/LLM involvement. Venue NA rules for routine assistance do not remove the objective's separate requirement to disclose LLM assistance. |

The exact question text and fuller official guidelines are authoritative over these shortened evidence targets. A negative or NA answer can be honest and acceptable to the venue, but does not waive a mandatory task requirement. The completed checklist belongs to report; analysis and presentation provide the evidence supporting their respective answers.
