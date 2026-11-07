# Venue: NeurIPS 2026, main track

Verified 2026-11-02 against https://neurips.cc/Conferences/2026/CallForPapers, the Main Track Handbook
(https://neurips.cc/Conferences/2026/MainTrackHandbook) and the official template zip (see `template/SOURCE.md`).

## Why this venue
`deliverable.md` lets the study pick one of ICML, ICLR, NeurIPS and use "the latest edition's" official template.
- NeurIPS 2026 (40th): CfP and template published; its paper checklist is mandatory (the deliverable names it as the example).
- ICML 2026 (instructions read): 8-page body, unlimited references/appendix; the edition is already past (camera-ready May 2026).
- ICLR 2027: CfP page exists (abstract 18 Sep / paper 25 Sep 2026) and `ICLR/Master-Template` has an `iclr2027` folder, but
  its Author Guide URL answered 404 on 2026-11-02, so its page limit and checklist rules could not be verified. NOT chosen
  for that reason; this cannot be established, not a judgement on quality.
NeurIPS is therefore the one whose rules can be checked in full.

## Requirements (source: template + Handbook; "verifiable" = how to check)
| # | Requirement | How to verify |
|---|---|---|
| V1 | Official `neurips_2026.sty`, unmodified margins/fonts; `\usepackage{neurips_2026}` with NO `final`/`preprint` (anonymous mode, line numbers on) | grep the paper's `.tex`; compare sha256 of `.sty` with `template/neurips_2026.sty` |
| V2 | Main text <= **9 content pages**, figures and tables included. References, acknowledgments, appendices and the checklist do not count | `pdfinfo`, and locate the page where the "References" heading starts in `pdftotext -layout`; content ends on page <= 9 |
| V3 | Order: main text, references, (optional) appendices, then **NeurIPS Paper Checklist** (last; no checklist => desk reject) | pdftotext shows the heading "NeurIPS Paper Checklist" after appendices |
| V4 | Checklist: instruction block deleted, heading kept, questions/guidelines unmodified, every item answered with `\answerYes/\answerNo/\answerNA` plus a 1-2 sentence justification pointing to sections; no `\answerTODO`/`\justificationTODO` left | `grep -c TODO` = 0 in built `.tex` and PDF |
| V5 | Required paper sections (deliverable.md): abstract, introduction, related work, method, experiments, discussion and limitations, references | section headings in the PDF |
| V6 | Anonymity: no author names, no acknowledgments (use the `ack` environment, which hides it), no public repo links; code referenced as anonymous/supplementary | grep for URLs, names |
| V7 | Single PDF <= 50 MB; LaTeX source delivered together with the PDF | file size |
| V8 | LLM/agent use: document in the setup if it is an important, original or non-standard component of the method (here it is not; spell/code assistance needs no disclosure) | one sentence in checklist item on LLM usage |
| V9 | Dataset licences/credit: Stanford3 is CC BY-SA, cite Rossi & Ahmed (AAAI 2015) and Traud, Mucha & Porter (2012); SNAP ego-Facebook has no licence listed, cite McAuley & Leskovec (NIPS 2012) | bibliography, checklist "licenses" item |

## Requirements from `deliverable.md` that sit beside the venue
| # | Requirement | Verify |
|---|---|---|
| D1 | Code + reproduction notes: environment and dependency versions, data acquisition steps and data versions (Stanford3 zip sha256 `b1221e41...20d`, ego-Facebook sha256 `125e84db...7d7`), random seeds, run commands, expected runtime, and a table mapping **every figure and table to the script producing it** | README/repro file exists; every `\includegraphics`/table in the paper appears in the map |
| D2 | Every number/figure/table in the paper comes from a run the shipped code regenerates; failed/abandoned runs and unfinished experiments are reported as such; only real, consulted citations | cross-check by `internal-review-repo` |
| D3 | Prohibited-material rule: the paper that already studied this question, and anything citing/discussing/mirroring it, must not be searched or read. If any such page is met by accident, stop and record what, where and how much in the reproduction notes (write "none encountered" only if true) | section in repro notes |
| D4 | Uncertainty reporting (repeats, CIs or tests), baselines/ablations, stated scope of conclusions, honest limitations | reviewers' criteria; checked in review |
| D5 | Negative or unexpected results reported as such | review |

## Not established / open
- The anonymous-code-link policy for the reviewed artifact: the handbook asks for code as a separate (anonymized) submission; here the code
  lives in the repo, so the paper must say "code in supplementary material" and must not link a named repo.
- Layout inside `paper-repo` (file names) is the plan owner's; see `venue-artifacts.json` once names are settled.
