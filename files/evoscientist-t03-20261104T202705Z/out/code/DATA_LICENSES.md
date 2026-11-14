# Data licenses and provenance audit

Audit date: **2026-11-04 UTC**. Scope: documentation/provenance only; no implementation, training, experiments, or raw-data downloads. This is an evidence-backed release recommendation, not legal advice.

## Decision summary

| Asset actually present | Verified terms | Raw-data redistribution recommendation |
|---|---|---|
| UCI dataset **144**, Statlog (German Credit Data), DOI **10.24432/C5NC77** | Official dataset page explicitly states **CC BY 4.0**, permitting sharing/adaptation for any purpose with appropriate credit [1]. | **Yes, conditionally:** retain dataset attribution, license identifier/link, source, and modification notice. Do not place it under the project's software license. Full CC legalcode was linked by UCI but not fetched in this restricted audit. |
| OpenML **37**, **diabetes**, **version 1**, file ID **37** | Official API's exact field is **`"licence": "Public"`** [3]. It is not a specific CC/SPDX license or a detailed redistribution grant. | **Downloader only for now.** Do not relabel as CC0, CC BY, MIT, or conclusively public domain. Obtain authoritative clarification of reuse/redistribution terms before bundling the ARFF or row-level derivatives. |
| Census **2018 ACS 1-Year PUMS, Vermont, person records** | Official 2018 documentation establishes a public-use product and explains confidentiality protections [4,5]. **A usable Census copyright/terms-of-use statement was not recovered from the narrowly attempted policy endpoints.** | **Downloader only pending policy verification.** This is an evidence gap, not a finding that Census prohibits redistribution. Do not use Folktables' software license as a data license, or equate “public use” with a verified copyright waiver. |
| **Folktables 0.0.12 software** | Official PyPI release metadata declares classifier **`License :: OSI Approved :: MIT License`**; `info.license` is the empty string and `info.license_expression` is null [6]. | Software metadata only: does **not** license Census records. Full MIT text/notice obligations were not audited through a package archive. |

**Safest immediate supplement/repository:** provide the existing downloader, source identifiers, notices, and checksums; omit raw Pima and ACS files (including the ACS pickle and row-level subsets) until their unresolved terms are addressed. German may be included separately with CC BY attribution. A downloader-only release still requires users to comply with source terms; it is not a license workaround.

## 1. Actual access and reading scope

### Local material inspected

- `/work/sources.md`: entire 198-line acquisition/source record, as requested. Its existing literature citations were not followed or re-fetched.
- `/work/paper.tex`: literal `licens` matches and lines 286–343, covering the appendix acquisition/license paragraph at line 316 and adjacent reproducibility material. This was **not** a full-paper review.
- `/work/get_data.py`: entire 20-line existing downloader, read only; not run or modified.
- `/work/data/manifest.json`: entire manifest. All eight listed data files were re-hashed; all matched the saved byte lengths and SHA-256 values.
- `/work/data/german/german.doc`: first 150 of 175 lines, identifying the source and original/numeric variants. All ZIP members were separately compared byte-for-byte to the local extracted files, without displaying the data rows.
- Local ARFF: checksum and data-row count; no literature/prose review. Local CSV: all rows scanned for dimensions, record type, state and serial-number year only. The local trusted, previously generated pickle was loaded solely to compare its DataFrame to the CSV, not to run an experiment.
- Installed Folktables version metadata and narrowly selected `load_acs.py` downloader/parser lines, including the person/household selector, VT-to-50 mapping, filenames, source URL template, and parser dtypes. Function-versus-module line-scope clarification is appended in the log.

### External access boundary

**No web search, topic-literature search, scholarly page, citation graph, repository research link, or recommendation was requested.** Only the official data/documentation endpoints enumerated below were fetched. Redirect following was disabled; there were no redirects. HTML was parsed locally without JavaScript or external resource loading. Complete saved responses can contain unread navigation or embedded links; their presence is not a claim that they were read or followed.

`/work/data_access_log.jsonl` is append-only for this audit. It records each direct GET with request/final URL, UTC timestamp, status, response-body bytes, SHA-256, and saved path; subsequent `scoped_read` entries distinguish actual displayed excerpts from fetched bytes. Failed and irrelevant policy attempts are retained, not silently omitted. Local-validation events are explicitly marked as non-network events.

| Official endpoint / local snapshot under `/work/official/data_licenses/` | Result | Actual displayed/read scope |
|---|---|---|
| [2] `uci144.json` | HTTP 200 | Dataset/root key names; identity, source URLs, dimensions, DOI, year and creator fields. API has **no license field**; introductory-paper field was not displayed. |
| [1] `uci144.html` | HTTP 200 | Script/style-excluded keyword windows around License, CC BY, Creative Commons and Hofmann; original-vs-numeric description and dataset citation were included in those windows. License/archive link labels and URLs only; no linked pages followed. |
| [3] `openml37.json` | HTTP 200 | Identity/version/status/license/source URL/checksum/creator and related selected metadata. The citation field contained a scholarly URL, transcribed by the metadata display only; **not fetched**. Description and paper URL were not displayed or followed. |
| [4] `acs2018_documentation.html` | HTTP 200 | Selected 2018 documentation link labels/URLs and keyword windows around the 2018 ReadMe/CSV documentation. A first attempted `<main>` extraction was empty; the later window extraction is the actual text read. Some adjacent footer/navigation labels appeared; no such links were followed. |
| [5] `ACS2018_PUMS_README.pdf` | HTTP 200 | 25 pages text-extracted locally; only lines matching CSV/person/psam/Vermont/2018/confidential/public use/PUMS/zip/census.gov were displayed. Not a claim to have read every page in full. No links within the PDF followed. |
| [6] `folktables0.0.12.json` | HTTP 200 | `info.name`, `version`, `license`, `license_expression`, `classifiers`, `author`, `requires_python`; no project/research URLs followed. |
| `census_copyright.html`: `https://www.census.gov/about/policies/copyright.html` | **HTTP 404** | Failure metadata only; not copyright evidence. |
| `census_terms.html`: `https://www.census.gov/about/policies/terms.html` | HTTP 200, **irrelevant** | Title is **“Message Concerning Inappropriate Terms”**, not copyright/terms of use. No copyright/public-domain/permission/license matches were found in the response. It must **not** be cited as a reuse policy. |
| `census_terms_of_use.html`: `https://www.census.gov/about/policies/terms_of_use.html` | **HTTP 404** | Page-not-found title only. |
| `census_copyright_terms.html`: `https://www.census.gov/about/policies/copyright-and-terms-of-use.html` | **HTTP 404** | Page-not-found title only. |

No Creative Commons legalcode, upstream UCI Pima page, JAIR page, GitHub repository, IPUMS page, or raw source archive was fetched. The unsuccessful Census policy attempts cannot establish either a permission or a prohibition.

## 2. UCI German: terms and provenance

### Direct evidence

The official dataset144 page states [1]:

> “This dataset is licensed under a Creative Commons Attribution 4.0 International (CC BY 4.0) license. This allows for the sharing and adaptation of the datasets for any purpose, provided that the appropriate credit is given.”

Its linked archive is exactly:

`https://archive.ics.uci.edu/static/public/144/statlog+german+credit+data.zip`

This is the URL in the local downloader. **The archive URL was read as documentation, not fetched again.** The API independently identifies dataset144 as “Statlog (German Credit Data)”, Hans Hofmann, 1994, 1,000 instances, 20 features, DOI `10.24432/C5NC77` [2]. The API's `data_url` instead points to a repository CSV; that CSV was not fetched and must not be described as the local ZIP source.

The local `german.data` has **1,000 rows and 21 whitespace-separated fields** (20 predictors plus label). The official description and local `german.doc` distinguish it from the Strathclyde-created `german.data-numeric`, which has additional numeric/indicator columns. All four extracted files exactly match their local ZIP entries. Do not confuse dataset144 with another German-credit dataset or pretend the numeric variant was the input merely because it is in the same archive.

### Release notice to supply

> Hans Hofmann (1994), *Statlog (German Credit Data)*, UCI Machine Learning Repository, DOI: 10.24432/C5NC77. Source: https://archive.ics.uci.edu/dataset/144/statlog+german+credit+data. Licensed CC BY 4.0: https://creativecommons.org/licenses/by/4.0/. Raw files are unmodified archive members; describe any subsequently redistributed transformations separately.

UCI links the legalcode at `https://creativecommons.org/licenses/by/4.0/legalcode` (**link observed, not visited**). Before packaging a formal license notice, retain the license link, creator/source credit and change indications, and review that full text if legal completeness is needed. This audit verified UCI's license declaration and its stated sharing/adaptation condition, not every clause or the original depositor's chain of title.

**Provenance limit:** ZIP/extracted equality and manifest equality establish local integrity; no current source-archive checksum was obtained. The source path is corroborated by the official page and existing downloader, not by a fresh server-byte comparison or an audited original acquisition transaction.

## 3. OpenML diabetes: exact version verified; terms underspecified

Official API [3] reports:

```text
id: 37
name: diabetes
version: 1
file_id: 37
licence: Public
status: active
default_target_attribute: class
url: https://openml.org/data/v1/download/37/diabetes.arff
md5_checksum: 3cbaa3e54586aa88cf6aacb4033e4470
creator: Peter D. Turney
collection_date: 1995-03-01
upload_date: 2014-04-06T23:22:13
```

The existing downloader instead uses the legacy official endpoint:

`https://www.openml.org/data/download/37/dataset_37_diabetes.arff`

Neither raw endpoint was fetched in this audit. **The local 37,419-byte ARFF has MD5 `3cbaa3e54586aa88cf6aacb4033e4470`, exactly matching the official dataset37/version1 API.** This independently ties the local content to this OpenML version despite the different endpoint spelling. The file contains **768 data rows**. SHA-256 is recorded below. MD5 is used only for comparison to OpenML's published identity check, not as a modern security guarantee.

The API's `original_data_url` names the historical UCI Pima Indians diabetes page; that URL was not visited. The creator/date fields above are **OpenML metadata**, not independently verified original-study authorship or a license grant. No source terms were inherited from the German dataset144 page.

**Unresolved:** `Public` is the exact platform license string. It does not specify attribution duties, commercial reuse, adaptation, sublicensing or redistribution conditions, and does not by itself prove public-domain status. Do not translate it into a standard license or expand a public-download label into a grant. Keep a downloader/identifier/hash record and request authoritative upstream/OpenML licensing clarification before redistributing this file or a row-preserving derivative.

## 4. ACS2018 Vermont persons: source product verified; copyright policy unresolved

### Product identity and transformations

- Existing acquisition specifies `survey_year='2018'`, `horizon='1-Year'`, `survey='person'`, states `['VT']`.
- Installed software version is **Folktables 0.0.12**, matching the exact PyPI release checked [6]. Its local downloader maps VT to state FIPS **50**, selects `p` for person records, names the extracted file `psam_p50.csv`, and constructs:

  `https://www2.census.gov/programs-surveys/acs/data/pums/2018/1-Year/csv_pvt.zip`

  This URL is **reconstructed from local downloader source, not visited or independently confirmed by a saved original request**. The installed downloader deletes its downloaded archive by default; no original Census ZIP is present in the inspected data manifest.
- Official **2018 ACS 1-year PUMS ReadMe** [5], PDF p. 12, describes the official Census PUMS FTP/HTTPS hierarchy and selecting the year and `1-Year` folder. PDF p. 24 documents post-2017 person CSV names as **`PSAM_P<ST>`**, where ST is the state FIPS code. This independently supports the product/file-type interpretation, not a byte-for-byte archive authentication.
- Local CSV: **6,436 rows × 286 columns**, all `ST=50`, all `RT=P`, and every `SERIALNO` begins `2018`.
- Local `acs2018vt.pkl` is a **derived pandas serialization**, not an original Census distribution file. Re-reading the CSV with the installed loader's dtypes yields **exact DataFrame equality, including values, dtypes, index, row order and column order**, with that pickle. No task filtering/model preprocessing was run during this audit.
- Census documentation distinguishes **person** and **housing-unit** files and explains confidentiality modification of public-use records [5, PDF pp. 3–4]. This is direct Census PUMS, not an IPUMS reconstruction. IPUMS-specific terms were not accessed or imported into this recommendation.

### What the actual documentation does—and does not—establish

The official 2018 documentation labels this a public-use microdata product. The ReadMe explains that variables have been modified to protect respondent confidentiality, including limiting geographic detail. It supports a description such as **“public-use ACS PUMS records released by the U.S. Census Bureau.”** It is **not** the requested copyright/terms-of-use statement.

The attempted Census policy endpoints did not yield usable reuse terms (three 404s and one unrelated page; see access table). Consequently this audit **does not verify a specific Census copyright/public-domain declaration or redistribution conditions**, and does not certify commercial reuse, endorsement/logo rules, or a complete legal clearance. Do not cite `/about/policies/terms.html` as a copyright policy merely because it returned HTTP 200.

**Action before raw release:** obtain and retain the current official Census copyright/terms-of-use statement that applies to Census-produced ACS PUMS; record its exact URL, text, access date, and any third-party-material exceptions. Until then distribute the existing downloader plus source/product identifiers and checksums, not the CSV/pickle. Do not imply that this recommendation is a legal determination that federal data are restricted.

## 5. Folktables software is not the Census data license

Official PyPI metadata for exactly 0.0.12 [6] says:

```text
name: folktables
version: 0.0.12
info.license: ""
info.license_expression: null
info.classifiers includes: License :: OSI Approved :: MIT License
```

Accurate statement: **“Folktables 0.0.12 declares MIT licensing through its PyPI classifier.”** Inaccurate statement: “The ACS data are MIT-licensed because we downloaded them with Folktables.” No wheel/sdist or full MIT license text was downloaded or reviewed. If vendoring software, verify and retain its actual software license/copyright notices separately; merely using the interface does not supply a data redistribution grant.

## 6. Machine-verified local hashes

All entries below were freshly computed and agree with `/work/data/manifest.json`. A hash proves local byte identity, not licensing or source authorization. Derived pickle byte hashes can vary with serialization/library versions even when the underlying table agrees.

| Path relative to `/work/` | Bytes | SHA-256 |
|---|---:|---|
| `data/german.zip` | 29,607 | `e12d9d5def6845c0622634a1cd2ab87fa470668c4298f1ec52a4e403376a435b` |
| `data/german/german.data` | 79,793 | `b21f3d81db8071257d5ff1deaeba1fd4303b62712e6fcc9715c7a86202cb5871` |
| `data/german/german.data-numeric` | 102,000 | `2752b044394958ab6dd193a0b56ca0f0b3a2d8bc7cb8c008e35a5e84bbec02f8` |
| `data/german/german.doc` | 4,679 | `69b92cb551111bc37098698288849c96f0fd87ce81a2e54451ff39aa1e53fe49` |
| `data/german/Index` | 150 | `30cd5a2ef694f379fd65e5835ffd0f8405d6c225c3711a8cc0c8e12f55501e91` |
| `data/pima.arff` | 37,419 | `4eddd5b2b64679e8888348e306520a393d6a28e1ddc9643cfb76fc5d912d6d40` |
| `data/acs/2018/1-Year/psam_p50.csv` | 4,499,009 | `01d8a17f099714462e056fb82768f6278f939b94ea2e629e46e8c7cc84f7a8d1` |
| `data/acs2018vt.pkl` | 14,707,140 | `8738be643662c6222d15d611a66227607442708b9c3ed8cf2061779178fcedd7` |

Machine-readable checks: `/work/official/data_licenses/local_validation.json` (eight file hashes, manifest agreement, ZIP member equality, OpenML MD5 match and ACS identity fields); `local_provenance.json` (CSV/pickle equality, installed-loader source-text hashes, inferred Census URL and limitations). These are audit records, not changes to experiment code or the original data manifest.

### Successful documentation-response SHA-256

Complete response-body hashes, not hashes of the selected reading excerpts:

| Snapshot | SHA-256 |
|---|---|
| `uci144.json` | `d99e40b6b0a348840a03d8fd7a56dd25f4d0cd4b9262c2b3a1dc8e05bf1faef9` |
| `uci144.html` | `c7234ecb710560382687e9eaafb15eb0243843e6c817c9dd8cbcef522ef0a64b` |
| `openml37.json` | `9c5737c190ab2ed1cfcc84bf1c0a281ece11acd3dce065706217d1b0f5e3d2e7` |
| `acs2018_documentation.html` | `bd68c07bbe360f2b7a08227eb82d566ba27e08442f942d91d4955332dccec191` |
| `ACS2018_PUMS_README.pdf` | `ea0f952f72fdb55ca9ce70bfc58685a262a7a4f5d14f9c49924968b74df71a24` |
| `folktables0.0.12.json` | `caeda359e9d6820e9737000700c8b4d1e89afaca47835496cbf569477d6315cc` |

The log additionally records all unsuccessful/irrelevant policy-response hashes, lengths and timestamps. The HTTP-200 irrelevant `census_terms.html` is intentionally excluded from the successful **documentation-evidence** table above.

## 7. Actionable paper / README corrections (not applied)

1. **German:** replace a merely asserted license with the official-page-backed CC BY 4.0 declaration, dataset creator/year/DOI, dataset144 URL and credit/license notice. Distinguish original categorical input from the separately included numeric archive member.
2. **Pima:** replace “the original request lists Pima as public” with **“The official OpenML API identifies diabetes dataset37 version1 and labels its licence ‘Public’; the local ARFF matches the API MD5. Detailed upstream redistribution terms were not established.”** Do not claim public domain or assign a software license.
3. **ACS:** name **2018 ACS 1-Year PUMS Vermont person records**, Census source, and **Folktables 0.0.12 as the interface**. State that the pickle is a local serialization. The source URL is inferred from the inspected downloader; do not describe it as a newly verified original transaction. Separate public-use availability from still-unverified copyright policy.
4. **License completeness:** the existing appendix's blanket “not established” can be narrowed: German is now verified at the official declaration level; OpenML has a verified but underspecified `Public` label; Census copyright terms remain unresolved. Do not change the blanket statement to “all datasets are cleared.”
5. **Artifact claims:** distinguish fresh hashes from acquisition evidence. German has local ZIP/member agreement; OpenML has an independent API MD5 match; ACS has official product documentation, local parser/identity consistency and CSV/pickle equality, but no independent source checksum or retained source ZIP in this audit.
6. **Release packaging:** exclude Pima/ACS raw and row-level derivative files for now; include existing downloader, identifiers, this report, notices and hashes. Do not imply checksums or this review supply missing permissions. Review Census policy and clarify Pima terms before changing that recommendation.

Suggested replacement prose for the appendix/README:

> German Credit is UCI Statlog dataset144 (Hans Hofmann, 1994; DOI 10.24432/C5NC77), declared CC BY 4.0 on its official dataset page. Pima is OpenML diabetes dataset37 version1; its official API labels the licence “Public”, and our local ARFF matches its published MD5, but detailed redistribution terms were not established. ACS uses the U.S. Census Bureau's 2018 ACS 1-Year PUMS Vermont person records, accessed through Folktables 0.0.12; the local pickle is a derived serialization of the saved CSV. Folktables' MIT software classifier does not license the underlying records. Census copyright/terms-of-use verification remains unresolved in this restricted audit. We recommend releasing the downloader and provenance records rather than bundling Pima/ACS raw data pending clarification. See DATA_LICENSES.md for source URLs, reading scope and checksums.

This is **proposed text**, not a claim that a release has already been packaged. `/work/paper.tex`, `/work/sources.md`, existing downloader/experiment code and original data were left unchanged. No README was created or edited.

## Sources actually requested

[1] UCI, *Statlog (German Credit Data)*, official dataset144 page (license, attribution, archive link): https://archive.ics.uci.edu/dataset/144/statlog+german+credit+data

[2] UCI, official dataset144 API (identity/source metadata; no license field): https://archive.ics.uci.edu/api/dataset?id=144

[3] OpenML, official dataset37 JSON API (version, licence string, file URL, MD5): https://www.openml.org/api/v1/json/data/37

[4] U.S. Census Bureau, *2018 PUMS Documentation*: https://www.census.gov/programs-surveys/acs/microdata/documentation/2018.html

[5] U.S. Census Bureau, *2018 ACS 1-Year PUMS Files ReadMe*: https://www2.census.gov/programs-surveys/acs/tech_docs/pums/ACS2018_PUMS_README.pdf

[6] PyPI, official *folktables 0.0.12* JSON release metadata: https://pypi.org/pypi/folktables/0.0.12/json

Failed/irrelevant Census policy attempts are fully enumerated above and in the access log; **none is cited as an established license or copyright policy**.
