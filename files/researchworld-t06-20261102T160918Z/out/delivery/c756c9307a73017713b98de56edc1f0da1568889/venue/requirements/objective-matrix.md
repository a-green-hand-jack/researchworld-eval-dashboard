# Objective-first delivery requirements

Authority: venue-repo issue #1 and frozen `/initial-state/inputs/0/{TASK,deliverable,data,resources,starter_literature}.md`. The frozen objective takes precedence over venue conventions and study plans. This is a requirement record, not a claim that the final delivery complies. No conference submission or acceptance is claimed.

## Scope and evidence

| ID | Required outcome / constraint | Evidence needed in delivery | Accountable function |
| --- | --- | --- | --- |
| O01 | Study sensitivity of pairwise-comparison leaderboard rankings to small underlying-data changes; operationalize questions, changes and metrics. | Methods define estimand, perturbation unit/scale and ranking endpoints; experimental evidence answers the question. | plan, analysis, report |
| O02 | Conclusions use real data from at least two distinct evaluation designs, not merely two dataset names. | Dataset provenance, design descriptions and measured results per design; justify any cross-design comparison. | context, plan, analysis, report |
| O03 | Define how modification scale is measured and how datasets are compared, with reasons. | Explicit normalization, denominator, eligibility and comparison limitations. | plan, analysis, report |
| O04 | Conditions and limits accompany conclusions; small or mixed effects are acceptable. | Uncertainty and applicability/limitations tied to evidence. | analysis, report |
| O05 | Public data; CPU only; approximately one week; no paid API needed. | Acquisition/version records, environment and CPU commands; actual runtimes distinguished from planning estimates. | analysis, report |
| O06 | Complete research paper in PDF and LaTeX using latest official ICML, ICLR or NeurIPS template and its main-text page limit. | Buildable source, unmodified official style, rendered PDF, documented page boundaries and venue-rule provenance. | venue, report |
| O07 | Include abstract, introduction, related work, methods, experiments, discussion/limitations and references. | Actual rendered sections; related-work sources must have been read. | context, report |
| O08 | Complete the chosen conference's required paper checklist. | Every official question answered Yes/No/NA honestly with justification and paper/artifact references. | venue questions; report answers with evidence owners |
| O09 | All code and reproduction instructions. | Environment/dependency versions, data acquisition steps and versions, random seeds, exact commands, expected runtime, and script mapping for every figure and table. | analysis, presentation, report |
| O10 | Every numerical study result, figure and table must derive from actual runs in this task, reproducible with supplied code. | Machine-readable run results/provenance and script-to-output mapping; clearly label external cited values and design settings. | analysis, presentation, report |
| O11 | Report failed runs, unexpected findings and abandoned approaches honestly; unfinished experiments stay unfinished. | Methods/limitations or reproduction log distinguish executed, failed, and unexecuted work. | analysis, report |
| O12 | Cite only real literature actually consulted. | Verified bibliography and literature-read provenance; no invented citations. | context, report |
| O13 | Do not search for, infer, access or use the withheld prior paper or its associated/discussing material. Starter literature is expressly allowed. | Restricted literature workflow; if accidentally encountered, stop reading and record what/where/how much in reproduction documentation. Do not identify or infer the prohibited work. | all; context/report record |
| O14 | Keep raw data in working `data/`, outside code repository and paper submission. | Downloader plus source/version/checksum manifest; no raw input data in delivery. | analysis, report |
| O15 | Disclose LLM assistance if used. | Paper disclosure reflects actual assistance (this research organization uses AI assistance). | report |
| O16 | Evaluate at the chosen venue's main-track standard: novelty/positioning, rigor, baselines/controls/ablations as appropriate, uncertainty, evidence, clarity, reproducibility and limitations. | Substantive paper and independent review; formatting compliance alone is insufficient. | all; independent review |

## Data and source requirements

The task supplies fixed public-data snapshots in `data.md`; selection is free, but at least two evaluation designs must be represented. Optional data need not be used. Do not claim rights for assets beyond verified source terms. In particular, the optional `potsawee/chatbot-arena-llm-judges` source has no declared license in the frozen inventory, and WebDev Arena has a separate agreement; neither is automatically cleared by another dataset's license. Preserve selected-source attribution, snapshot, checksums and preprocessing/exclusions.

The frozen source hashes are recorded in `sources/frozen-inputs.sha256`. The approximate CPU runtime in `resources.md` is a planning estimate, not a measurement. The local sandbox limit is stricter than that example configuration; reproducibility instructions should state the actual environment used.

## Ownership boundaries and unresolved verification

Venue supplies format rules, original template/checklist questions, official-source provenance and artifact requirements. Report owns the paper text and final evidence-dependent checklist answers. Analysis owns measured results and runnable study code. Presentation owns generated figures/tables and their provenance. Plan owns delivered-path allocation in `.forgejo/CODEOWNERS`.

NeurIPS 2026 rules and latest available official template were verified as recorded in `venue.md`. Exact paths follow the merged CODEOWNERS allocation in paper-repo (story-repo PR #4) and `venue-artifacts.json`. Final page count, checklist truth, clean reproduction and substantive paper quality require separate verification; never mark them complete on this matrix alone. The context Brief was read and checked against the frozen files before this delivery; no conflict with these venue requirements was found.
