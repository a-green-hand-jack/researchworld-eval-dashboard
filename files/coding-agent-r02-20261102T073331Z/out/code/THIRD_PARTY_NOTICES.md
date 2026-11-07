# Third-party provenance and terms

- NumPy (2.4.6), SciPy (1.17.1), pandas (3.1.0): BSD-3-Clause scientific libraries.
  Their creators and full bundled notices are recorded in installed package
  metadata and the generated `environment-packages.json`.
- Matplotlib (3.11.2): Matplotlib license (PSF-based); plotting only.
- PyMuPDF (2.0): AGPL-3.0 / commercial dual licensing; used only for local reading,
  PDF text checks, and rendering for inspection. No modified library is distributed.
  Scientific calculations do not depend on it. Full metadata is retained in
  `environment-packages.json`; readers should follow its terms for redistribution.
- Additional exploratory installation versions, including scikit-learn and
  requests, are preserved in `requirements-lock.txt`. They are not used by the
  scientific pipeline; no claims depend on them.
- The unmodified official NeurIPS 2026 template and checklist were downloaded
  from `https://media.neurips.cc/Conferences/NeurIPS2026/Formatting_Instructions_For_NeurIPS_2026.zip`,
  linked by `https://neurips.cc/Conferences/2026/CallForPapers`. The archive names
  Roman Garnett and earlier style authors but contains no explicit license file.
  We do not infer a new license for the style. It is included solely as the
  conference-provided formatting asset required to compile this paper. The
  checklist questions and guidelines are retained; the instruction block is
  removed and the answers/justifications filled as the official file directs.
- TeX Live and its LaTeX packages retain their upstream licenses; no TeX binaries
  are redistributed. `environment-system.txt` records the compiler versions.
- The five downloaded starter papers remain copyrighted by their owners. Local
  copies are evidence of reading, not relicensed research assets. The portable
  deliverable archive includes reading notes, exact URLs, and checksums rather
  than scholarly PDF copies. No figures, tables, source code, or experimental
  results were copied from those papers.

No external dataset, pretrained model, remote prediction service, or paid API was
used. Original code is MIT; generated data are CC0 as stated separately.
