# Additional direct-source verification notes

## Scope, provenance, and reading boundary — 2026-11-04 UTC

This pass obeyed `/work/research_request.md` and the narrower current request: six supplied exact URLs only, without discovery, web search, citation traversal, related-page retrieval, repository retrieval, or prohibited-paper identity inference. HTTP redirects were disabled. No URL encountered inside these sources was requested. Downloading and offline extraction are not claims of full reading.

Six access attempts were appended to `literature_access.tsv`, preserving its previous bytes. Each response, including the 404 body, is saved under `/work/literature/`, with original URL, access timestamp, HTTP status, byte count and SHA-256 in its adjacent `*.provenance.json`. Consolidated provenance is `/work/artifacts/direct_source_verification_manifest.json`. The original `source_notes.md` was not edited. No experimental code, data or results were edited. The new helper is retrieval/documentation code only.

### Bounded reading record

- [1] PDF: offline extraction reports 58 PDF pages. Read original extracted text lines 1–230 (pages 1–3 and beginning of 4); task-page extract covering pages 5–7; page 8 first 4,200 characters; page 16 contents and following reconstruction paragraph; pages 18, 39, 54–56. Most relevant evidence is §3.1, §B.1, §B.6–B.7 and §E.4–E.6. Remaining pages were not read. No full-paper-reading claim. Offline custom extraction has character/formatting artifacts; no claims depend on corrupted mathematical symbols or missing-value glyphs. The initial planned pdftotext extraction was unavailable; the existing offline extractor was used without modifying it.
- [2] Official ethics HTML: extracted text lines 1–161 displayed. Substantive Code of Ethics is lines 80–112; navigation and further-reading labels are not supporting evidence. No linked items visited.
- [3] Official Census stewardship HTML: extracted lines 1–170 and 211–310 displayed; substantive stewardship text is lines 249–263. No policy sublinks visited.
- [4] Official Census copyright URL: returned HTTP 404. Response saved, but no substantive copyright policy was read or verified; do not cite the error response as permission.
- [5] UCI HTML: extracted lines 1–231 displayed. Supporting evidence is dataset description/format documentation and DOI/license block; not the embedded citation panel.
- [6] OpenML37 JSON: pretty-printed lines 1–52 displayed (including the long description field). Only identifier/version/license/visibility/status and basic dataset-schema metadata are used here. Description references and URLs were not followed. No clinical, demographic, or subject-level conclusions are drawn.

### Incidental exposure / reproducibility caution

Bounded text output incidentally included the UCI page's embedded “Papers Citing this Dataset” panel (approximately extracted lines 169–190), the ethics page's further-reading labels, reference strings within the supplied OpenML description, and 145-character page-start previews of PDF reference pages 14–15 while locating the task section. These areas were not pursued or used as research evidence. This was on-page/local-text exposure, not retrieval of related pages. No entry was investigated, matched, or used to infer any prohibited-paper identity. No assessment is made of whether any incidental entry corresponds to a prohibited work; doing so would itself risk the forbidden inference. No such links were followed. Future bounded readers should mask embedded citation panels and restrict PDF previews to already-authorized sections.

## Actual-read source facts and limits

### [1] Folktables task/data starter

URL: https://arxiv.org/pdf/2108.04884

Title read on PDF page 1: **Retiring Adult: New Datasets for Fair Machine Learning**, Frances Ding, Moritz Hardt, John Miller, Ludwig Schmidt. This is the supplied task/data source, not evidence about SHAP repeat-run reliability.

- **Task:** §3.1 and §B.1 define ACSIncome as `PINCP > 50000`. §3.1 describes filtering to age above 16, at least one usual working hour per week and income at least $100. These are the paper's task definitions, not an audit of the installed folktables 0.0.12 implementation. The paper lists ten ACSIncome features in Table 1; this pass did not read the complete feature codebook.
- **Scope:** §3 describes ACS PUMS, multiple states and years. §3.2 explicitly distinguishes benchmarking algorithms from substantive investigations into inequality. §E.5 warns that small state/subgroup samples can make generalizations highly inaccurate, instructs users not to attempt re-identification, and says substantive investigations should not be based purely on the provided datasets. These are usage/interpretation limitations, not findings about any person or group in this study.
- **Software vs data permissions:** §E.6 says, “The folktables package and data loading code will be available under the MIT license.” It separately states that the data are based on ACS PUMS and governed by Census terms of use. §B.6 likewise says the ACS PUMS data are governed by Census terms of service. This verifies what the paper reports; it does **not** independently verify a current repository LICENSE, a specific package release, or current Census ToU. Do not transfer the reported MIT software license to the underlying data.
- **Unaccessed terms pointer:** The paper gives a Census developers terms-of-service URL, but that URL is not among the six authorized targets and was not accessed. Its contents therefore remain unverified. No ACS public-domain, CC, unrestricted-redistribution, or blanket-compliance claim is supported by this pass.
- **Preprocessing:** §E.4 says released ACS data involve top-coding and imputation and task construction adds preprocessing. These statements are from the paper, not direct verification of the linked Census documentation or repository. Do not describe the benchmark as untouched raw survey responses.
- **Bounded protocol fact:** §B.7's Table 1 protocol uses 1-year 2018 US-wide ACS PUMS, caps each state at 100,000 examples through random subsampling, random 80/20 train/test splitting, zero-mean/unit-variance standardization, and majority-class/logistic-regression/gradient-boosting baselines. Table 1 reports accuracy. This section does not establish a calibration protocol, does not specify the preprocessing-fit boundary, and is not a protocol for SHAP reliability. Any study-specific split, calibration, or uncertainty choices need separate documentation. No reported paper accuracy is used as this study's result.

### [2] Official NeurIPS Code of Ethics

URL: https://neurips.cc/public/EthicsGuidelines

Actual-read requirements relevant to a methodological benchmark paper:

- Data-related provisions apply to **all** datasets, including publicly available data: minimize personally identifiable information; respect defined dataset licenses; assess and communicate representativeness; substantiate broad representation claims. The page says authors should confirm that datasets remain available and warns against discontinued datasets except for audit/critical assessment. An HTTP-successful page alone is not proof of all provenance or consent conditions.
- Authors should transparently communicate known/anticipated consequences, including safety, discrimination in credit/healthcare, bias/fairness and environmental costs. For this study, explanation repeatability should not be presented as proof of correctness, fairness, causal validity or readiness for high-stakes decisions; that is a conservative study-specific application, not a quoted conference rule.
- Communicate dataset/model details, artifact intended uses and limitations; provide appropriate release licenses while respecting upstream terms; protect sensitive data in storage/distribution. Do not relabel third-party data with the study's code license.
- Provide sufficient information to reproduce results, which can include code, data, weights, hyperparameters, environment and compute-resource descriptions. Artifact access should support external scrutiny/auditing.
- The explicit institutional human-participant review requirement is conditional on direct interactions between researchers/technical systems and participants. The page does **not** establish a blanket exemption for secondary public-data studies. No IRB exemption or consent verification is asserted here. Compensation rules apply when research uses human subjects, crowdsourcing or contract work.
- Authors remain subject to applicable legal and institutional requirements. Ethics violations may result in rejection.

**Verification limit:** This page contains no explicit paper-author double-blind/anonymity instructions or AI/LLM-assistance declaration rule. Its reference to data anonymization is not an author-anonymity rule. Consequently, this pass cannot verify the required location, wording, model/version fields, thresholds, or anonymity treatment of an AI declaration. No other conference page was retrieved to fill that gap.

### [3] Official Census data stewardship

URL: https://www.census.gov/about/policies/privacy/data_stewardship.html

The page describes the Bureau's confidentiality duties under Title 13, privacy principles of necessity/openness/respect/confidentiality, statistical safeguards, Disclosure Review Board review and technical security measures. It states, “We do not identify individuals in the data we publish.” Last-revised date displayed: February 25, 2026.

These are statements about the Bureau's stewardship, not a dataset license, a general data-reuse agreement, a guarantee of zero re-identification risk or a researcher IRB exemption. This page does not verify ACS redistribution rights. Keep study outputs at the methodological/aggregate level and do not attempt linkage or re-identification; the latter is also explicit in the folktables datasheet [1].

### [4] Official Census copyright page — unavailable

URL: https://www.census.gov/about/policies/copyright.html

**HTTP 404**, not an accessible copyright policy. No fallback, replacement URL, archive, repository, or search was used. Census copyright/reuse terms remain unverified within the allowed sources. Do not guess a public-domain or other license assertion.

### [5] UCI Statlog German Credit

URL: https://archive.ics.uci.edu/dataset/144/statlog+german+credit+data

The live dataset page explicitly labels the dataset **Creative Commons Attribution 4.0 International (CC BY 4.0)** and says sharing/adaptation are allowed for any purpose with appropriate credit. DOI shown: **10.24432/C5NC77**. The provided citation is Hofmann, H. (1994), *Statlog (German Credit Data)*, UCI Machine Learning Repository. This verifies the repository's license statement; the linked full CC legal text was not opened, so this pass does not claim to enumerate all legal conditions.

The page reports 1,000 instances and 20 features and distinguishes the original categorical/symbolic `german.data` from an edited numeric variant with added indicator variables. Thus “German20” and the numeric variant should not silently be treated as the same feature representation. It documents an asymmetric cost matrix with actual classes as rows and predictions as columns: bad-as-good costs 5 versus good-as-bad 1. These are benchmark documentation facts, not claims about actual borrowers, population representativeness or this study's predictive validity. No new data were downloaded.

### [6] OpenML37 metadata

URL: https://www.openml.org/api/v1/json/data/37

Actual JSON fields: `id = "37"`, `name = "diabetes"`, `version = "1"`, `licence = "Public"`, `visibility = "public"`, `status = "active"`, default target `class`, format ARFF. The description reports 768 instances and eight inputs plus class. Metadata MD5 `3cbaa3e54586aa88cf6aacb4033e4470` is the metadata's stated data checksum, **not** the SHA-256 of our downloaded metadata response. Data files were not retrieved or checksum-verified in this pass.

**License unresolved:** The literal value “Public” and public visibility are not a named legal instrument or a reproduced permission grant. Do not translate them into public domain, CC0, CC BY, MIT, or verified unrestricted reuse. No linked UCI source, citation-policy page, article or data URL was accessed. No historical performance, demographic, medical or subject-level assertions are adopted from the long description.

## Anonymous-paper and AI-involvement implications

### Supported ethics content to include

Document dataset source/version, preprocessing, permissions and unresolved terms, artifact release boundaries, representativeness limitations, compute/environment, and reproducibility details [1–3,5–6]. Discuss misuse risk: repeated explanations of a fixed predictor are not evidence of truthful causal reasons, individual creditworthiness, medical validity or fair treatment. Avoid subject-level disclosure and re-identification; use aggregate methodological reporting. Do not fabricate consent, approval, exemption or legal-compliance statements.

### Practical recommendations, not verified NeurIPS submission rules

For an anonymous submission, use non-identifying author placeholders and artifact packaging and defer identifying acknowledgments as appropriate, but obtain the actual conference instructions before claiming compliance. This pass did not verify the official double-blind policy.

For AI disclosure, the supportable statement about **this pass** is: “AI assistance was used for direct-source retrieval, bounded source reading and synthesis, and provenance/documentation preparation.” If assistance also materially affected research design, implementation, experiments or manuscript drafting, document those roles based on actual records rather than minimizing the declaration to this pass. Do not claim human verification or human oversight unless it occurred. Have responsible authors verify the final account and check official venue requirements for placement, detail and anonymous-review treatment; those requirements are unverified here. This is a factual documentation recommendation, not a claim that the allowed ethics page mandates a particular declaration.

## Sources (exact URLs accessed)

[1] Retiring Adult: New Datasets for Fair Machine Learning: https://arxiv.org/pdf/2108.04884
[2] NeurIPS Code of Ethics / Ethics Guidelines: https://neurips.cc/public/EthicsGuidelines
[3] U.S. Census Bureau, Data Stewardship: https://www.census.gov/about/policies/privacy/data_stewardship.html
[4] Supplied Census copyright endpoint (HTTP 404; not a verified policy): https://www.census.gov/about/policies/copyright.html
[5] UCI Statlog (German Credit Data): https://archive.ics.uci.edu/dataset/144/statlog+german+credit+data
[6] OpenML dataset 37 metadata: https://www.openml.org/api/v1/json/data/37
