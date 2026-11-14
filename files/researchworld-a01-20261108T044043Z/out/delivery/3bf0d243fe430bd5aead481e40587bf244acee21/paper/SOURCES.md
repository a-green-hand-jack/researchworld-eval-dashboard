# Literature consulted for the report

On 2026-11-08 the report position checked title, author list and abstract at the exact original arXiv records below. These support the limited descriptive claims in Related work; no cited-by pages, search results about the forbidden study, or unrelated recommendations were read.

| Citation key | Original record | Content used |
|---|---|---|
| hendrycks2021mmlu | https://arxiv.org/abs/2009.03300 | 57-task MMLU scope |
| suzgun2023bbh | https://arxiv.org/abs/2210.09261 | 23 challenging BIG-Bench tasks |
| liang2023helm | https://arxiv.org/abs/2211.09110 | HELM transparency, scenarios, public outputs |
| dehghani2021lottery | https://arxiv.org/abs/2107.07002 | benchmark task choice changes relative rankings |
| lanctot2025vase | https://arxiv.org/abs/2312.03121 | tasks as voters; ordinal evaluation |
| singh2025illusion | https://arxiv.org/abs/2504.20879 | private testing, selective disclosure and unequal Arena data access |
| zhou2023cheater | https://arxiv.org/abs/2311.01964 | leakage can raise benchmark scores |
| yang2023rephrased | https://arxiv.org/abs/2311.04850 | rephrasing bypasses string decontamination |
| colombo2022best | https://arxiv.org/abs/2202.03799 | social-choice aggregation changes NLP rankings relative to mean |

Chen, Zhang and Hardt, https://arxiv.org/abs/2603.08371, is explicitly allowed by the starter literature. The previous report turn downloaded its original PDF and read the model and results (`/hutian/dl/chen/c.txt` in the research workspace); this turn rechecked that text's introduction/model. The paper distinguishes its strategic post-training equilibrium/protocol question from this study's fixed-table score-allocation calculation. No inference about the forbidden paper's identity is made.

Faliszewski, Hemaspaandra and Hemaspaandra, *How Hard Is Bribery in Elections?*, DOI 10.1613/jair.2676: title and abstract consulted through the exact Crossref DOI record on 2026-11-08. Supports the definition of constructive electoral bribery and setting-dependent complexity; no theorem from that paper is reused.

Brandt et al. (eds.), *Handbook of Computational Social Choice*, DOI 10.1017/CBO9781107446984: title, editors and publisher abstract consulted through the exact Crossref DOI record on 2026-11-08. Cited as general field background; rule definitions and solver validity in this report are stated and checked independently.

The arXiv bibliographic years in refs.bib are the preprint years, which can precede the conference publication years reflected in the internal citation keys. These keys are not displayed as publication years.

Direct literature retrieval used only the named, permitted sources above. The consolidated forbidden-material encounter record is in REPRODUCE.md, section “Forbidden-material record”.

Xia, *Computing the margin of victory for various voting rules*, EC 2012, pp. 982–999, DOI 10.1145/2229012.2229086: on 2026-11-08, consulted the exact-title Crossref metadata and the abstract from the exact DOI record in OpenAlex. The abstract defines margin of victory as the fewest voters whose changed ballots change the winner, and describes its election-robustness/auditing purpose. Used only for that distinction from designated-target score changes. No cited-by, recommendation or general leaderboard-manipulation search was used.
