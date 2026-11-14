# Analysis dependency and generated-asset attribution

Recorded by experiment-repo on 2026-11-03 UTC for experiment-repo#9. This is a provenance addendum to the completed study, not a change to its frozen scientific implementation, generated observations, estimates or uncertainty. No external source was retrieved for this record. The supplied environment already contained the packages.

## Installed dependency evidence

`dependency-terms.json` records the actual installed versions, raw license fields, dependency declarations, local source paths and SHA-256/byte counts of the retained texts. `package-terms/` contains their unmodified license/NOTICE/copyright/author files and installed distribution METADATA. Read the full bundled notices for conditions; the short labels below do not replace them or grant any additional rights.

| Asset and measured version | Attribution / locally evidenced terms | Role |
| --- | --- | --- |
| Python 3.11.2, GCC 12.2.0 build | Python Software Foundation and predecessor/contributing rights holders. PSF license agreement and historical license texts in Python LICENSE.txt; Debian copyright file retains additional component and packaging terms. | Interpreter and standard library; exact build string matches both scientific shards' run_metadata.json. GCC identifies the recorded interpreter build, not a redistributed compiler. |
| NumPy 2.4.6 | NumPy Developers and bundled-component authors. Installed metadata reports `BSD-3-Clause AND 0BSD AND MIT AND Zlib AND CC0-1.0`; the main LICENSE and component-specific texts include bundled binary-library notices. | Arrays, random generation and numerical operations. |
| SciPy 1.17.1 | Enthought, Inc., SciPy Developers and bundled-component authors. Main terms are BSD 3-Clause; the retained complete LICENSE also contains bundled binary-library terms and exceptions. A separate integrate/LICENSE_DOP is retained. | Statistical quantiles, Sobol integration, linear algebra and diagnostics. |
| pandas 3.0.6 | AQR Capital Management, Lambda Foundry, PyData Development Team, open-source contributors and bundled-component authors. BSD 3-Clause main terms; additional terms are retained in its full LICENSE. | Tabulation and evidence postprocessing. |
| python-dateutil 3.0.0 | Paul Ganssle, dateutil contributors and historical authors listed in LICENSE. BSD terms apply to all code; the retained text also describes Apache 2.0 coverage for later/relicensed contributions. Metadata says `Dual License`. | Declared pandas runtime dependency. |
| six 1.17.0 | Benjamin Peterson. MIT license text retained. | Declared python-dateutil runtime dependency. |
| tzdata 2026.6 | Paul Ganssle (Google), Stan Ulbrych and contributors. Package metadata says Apache-2.0; its LICENSE and full Apache text are retained. | Declared python-dateutil runtime dependency in this installed version. |

The captured metadata shows the ordinary dependency chain NumPy ← SciPy/pandas; pandas → python-dateutil → six and tzdata. pandas' own conditional tzdata requirement is for Windows/Emscripten; python-dateutil in this environment requires it without that platform restriction. Optional testing, documentation, plotting, parquet and other extras listed in METADATA are not installed requirements of the supplied analysis commands. The scientific runner and postprocessing directly import only the three scientific packages above plus the standard library. All six recorded distribution versions were measured locally; the original run metadata pins the directly used Python/NumPy/SciPy/pandas versions. The transitive versions were captured at this later provenance check, not retrospectively claimed to have been independently logged during each trial.

The NumPy/SciPy bundled-library notices include their own redistribution conditions (including OpenBLAS/LAPACK and GCC-runtime-related notices where supplied). Their full text is preserved; a top-level BSD label must not erase those terms. This delivery contains analysis source/results and these attribution texts, not redistributed dependency wheels, interpreter binaries or a container image. Install dependencies separately under their terms. This local record does not establish the origin or complete license inventory of every operating-system library in the research image. Those image-wide terms remain outside this package-level check. Matplotlib/font/PDF/rendering-tool assets belong to the presentation/report environment and their owners' records, rather than this NumPy/SciPy/pandas analysis-stack inventory.

## Original synthetic assets and terms status

| New asset | Origin and traceability | Terms status |
| --- | --- | --- |
| `analysis/src/compbench/`, scripts, tests, postprocessing and method/proof/design documents | Written by experiment-repo for this study with substantive AI-agent involvement. Scientific generation/audit source is `4d760d511a3105b6d5b33937ff07124e630a64c5`; the complete results/evidence delivery is `d6e2af7327cfd448e1569cda352f22cb142c4a3f`. Mathematical background is attributed separately in the source-checked context; no externally downloaded research-code asset or pretrained model was used. | No explicit project software/document license was specified by the frozen inputs or selected in the delivered analysis. Reuse permission is unspecified, not inferred from repository availability. This record does not introduce a new license grant. Third-party software retains its own terms. |
| Synthetic X/Y observations, saved test cases, fitted ridge coefficients/group scales and trial checkpoints | Generated locally by the supplied code from frozen config/seeds; no human participant, private record, real dataset or third-party training data. Exact config/input/source hashes and seeds are retained per trial and in `results/confirmatory/final_audit.json`. | No third-party dataset access agreement applies. No separate generated-data/model license has been selected; reuse terms are unspecified. Synthetic origin does not itself establish a public-domain dedication. |
| Derived numerical CSV/JSON/NPZ/JSONL/gzip evidence, summaries and numerical audits | Computed from those original synthetic trials by the supplied scripts; inventories and digest links are in the complete final audit and evidence metadata. `core_interim/` and pilot outputs remain identified as historical, not additional confirmatory evidence. | No separate terms were selected for the original result assets; reuse terms are unspecified. This attribution record supplies the known origin and explicitly records the missing license designation. |
| Relayed literature/source-access statements under `provenance/attributed/` | Retained with each position's authorship, scope and retrieval attribution in access-inventory.json. They are source records, not newly authored scientific datasets. | Their source attribution is retained; no blanket relicensing is asserted. Consulted third-party works are not relicensed by the study. |

Presentation figures/tables, manuscript, official template and consulted-literature assets retain their owners' attribution and terms records. This document does not choose their licenses or certify their compliance. No new study dataset acquisition, participant-consent procedure or trained external-model license is involved.

## Local regeneration and checks

From the recorded Python/package environment, run:

```bash
python3 analysis/provenance/capture_package_terms.py
```

The script uses only standard-library local metadata/file access, asserts all recorded versions, and writes the exact original texts plus their digests. It does not run scientific trials, import the scientific implementation, download sources or edit the frozen files. Regeneration changes the capture timestamp; retained text digests should match for the same installed distributions. In a different environment the assertions deliberately fail rather than silently attributing a different version. The retained `dependency-terms.json` is sufficient for checking the bundled texts without having that environment available. Absence of a standalone NOTICE is not treated as proof that no embedded notice or further condition exists; all matching installed license/notice/copyright/author files found in each distribution inventory are captured.
