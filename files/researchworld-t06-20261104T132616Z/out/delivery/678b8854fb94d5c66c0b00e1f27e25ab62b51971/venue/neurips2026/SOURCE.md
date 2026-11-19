# NeurIPS 2026 official template (unmodified)

- Downloaded 2026-11-04 from https://media.neurips.cc/Conferences/NeurIPS2026/Formatting_Instructions_For_NeurIPS_2026.zip
  (linked from https://neurips.cc/Conferences/2026/CallForPapers); zip sha256
  `82473931e3ef710fcd3f4a8cd4119b9de32e56825f90f9e5a6d55f2d01b817d9`; members `neurips_2026.sty`,
  `neurips_2026.tex` (instructions + example), `checklist.tex` (paper checklist, 16 questions).
- File checksums: `SHA256SUMS`. Files here are byte-identical to the zip members; the paper copies them
  and edits only its own `.tex`, never the `.sty` (margins/fonts must not change: desk-rejection risk).
- Verified: `latexmk -pdf neurips_2026.tex` builds the example (12 pages) with the TeX Live in the sandbox.
