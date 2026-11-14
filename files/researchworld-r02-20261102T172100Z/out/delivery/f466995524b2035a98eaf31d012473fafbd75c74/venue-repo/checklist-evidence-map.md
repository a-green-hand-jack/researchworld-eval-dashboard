# Evidence needed to complete the official checklist

This is an authoring aid, not a completed checklist. Paper-repo owns the final manuscript's answers. Copy the official `official/neurips2026/checklist.tex` into the paper's completed-checklist source, preserve all 16 original questions and guidelines, remove the opening instruction block, and replace each answer/justification TODO with supported Yes/No/NA and 1–2 sentences. Yes must cite the actual supporting sections. Check the full official guidelines before answering; the brief evidence descriptions below do not replace them. Honest No or justified NA is permitted and is preferable to fabricated compliance.

| # | Official question heading | Evidence needed / source function |
|---|---|---|
| 1 | Claims | Abstract and introduction agree with the exact measured/theoretical findings and scope; analysis, story and report. |
| 2 | Limitations | Explicit assumptions, failures, synthetic/real-data scope, scaling and generalization limits; analysis and report. No study should claim it has no limitations. |
| 3 | Theory assumptions and proofs | Complete assumptions and correct proofs/derivations for each result. If there are no theoretical results, assess NA using the official rule; analysis. |
| 4 | Experimental result reproducibility | Method and configuration sufficient to reproduce claim-bearing results; analysis and reproduction documentation. |
| 5 | Open access to data and code | Actual accessible delivered code/data or generator, precise environment and commands, mapped to the main results; analysis/presentation/report. The objective requires all code regardless of the conference's weaker option. |
| 6 | Experimental setting/details | Splits, sample sizes, hyperparameters, model/generator/method fitting and calibration choices, seeds and selection procedures; analysis. |
| 7 | Experiment statistical significance | Variability source, replication unit/count, interval/test construction, assumptions, paired comparisons where relevant, meaning of plotted error bars; analysis/presentation. |
| 8 | Experiments compute resources | Actual hardware, memory/storage needs, duration and overall compute including failed/preliminary work; analysis. Separate measured times from estimates. |
| 9 | Code of ethics | Evidence of source/data/asset and research-integrity compliance; every owner. Do not turn lack of evidence into Yes. |
| 10 | Broader impacts | Plausible benefits/risks of reliability claims, limitations of downstream use and negative consequences discussed appropriately; report with study owners. |
| 11 | Safeguards | Determine actual asset risks and applicable safeguards from the study; do not invent a high-risk release or claim nonexistent safeguards. |
| 12 | Licenses for existing assets | Creator credits, URLs, versions, real license/terms for datasets/code/models/other existing assets; analysis/report. No guessed license for CIFAR-10 or task-owned code. |
| 13 | New assets | Delivered generator/code/data/model documentation, limitations and access terms if actually established; analysis/report. New code is an asset even if all observations are synthetic. |
| 14 | Crowdsourcing and research with human subjects | Actual participant involvement, instructions/compensation if applicable. NA only if study has none; study owners. |
| 15 | Institutional review board (IRB) approvals or equivalent for research with human subjects | Actual risk/consent/approval facts if applicable, otherwise supported NA. Never fabricate approval; study owners. |
| 16 | Declaration of LLM usage | Assess whether LLMs/agents are an important, original or nonstandard scientific-method component, versus basic assistance. Describe qualifying use in setup; give a precise justification consistent with the actual research process and handbook; report/study owners. |

Keep a project-wide restricted-source incident statement in the reproducibility instructions (objective requirement, not an extra seventeenth checklist item). This venue position encountered no prohibited research content during its conference-instruction/template retrieval; other owners must supply their own facts before that statement covers the full project.
