# Official template provenance — NeurIPS 2026 Main Track

Verified 2026-11-04 UTC. This is a template/evidence bundle, not a completed research paper or submission.

## Decision and authoritative URLs

**Use NeurIPS 2026, Main Track, nine main-text/content pages for submission.** A 2026 official template is actually published; no 2025 fallback is needed. This verifies the preferred NeurIPS 2026 option, not an exhaustive comparison with every ICML/ICLR release. No generic web or paper search was used.

1. Official 2026 Call for Papers: https://neurips.cc/Conferences/2026/CallForPapers
   - Read its title, 2026 call, key dates, and `Key links`.
   - The `Paper template` anchor directly points to the ZIP below; `MainTrackHandbook` points to source 3.
   - Snapshot: `/work/artifacts/template_evidence/neurips2026_cfp.html`; readable extraction: `neurips2026_cfp.txt` in the same directory.
2. **Original official template bundle:** https://media.neurips.cc/Conferences/NeurIPS2026/Formatting_Instructions_For_NeurIPS_2026.zip
   - Saved unchanged: `/work/paper/Formatting_Instructions_For_NeurIPS_2026.zip`.
   - 20,259 bytes; SHA256 `82473931e3ef710fcd3f4a8cd4119b9de32e56825f90f9e5a6d55f2d01b817d9`.
   - Exactly three archive members, extracted unchanged into `/work/paper/`: `neurips_2026.tex`, `neurips_2026.sty`, `checklist.tex`.
   - Byte comparison of all extracted members against the ZIP succeeded.
   - Style header: `2026-01-29 NeurIPS 2026 submission/camera-ready style file`; comment `last revision: January 2026`.
3. Official 2026 Main Track Handbook: https://neurips.cc/Conferences/2026/MainTrackHandbook
   - Read the author-facing paper-format/submission, checklist and author LLM-use passages, plus camera-ready publication passage.
   - Snapshot: `/work/artifacts/template_evidence/neurips2026_handbook.html`; readable extraction: `neurips2026_handbook.txt` in the same directory.
   - Provenance, download outcomes and source SHA256s: `/work/artifacts/template_evidence/download_log.json` and `/work/artifacts/source_manifest.json`.

## Verified page limit and scope

Two independent official artifacts agree:

- `neurips_2026.tex`, §1.1 `Style` (lines 130–131 in the unmodified file): “Papers may only be up to ... nine ... pages long, including figures.” Additional pages containing acknowledgments, references, checklist and optional technical appendices do not count as content pages.
- Handbook, author-facing paper-format passage (readable snapshot lines 188–194): “The main text of a submitted paper is limited to nine content pages, including all figures and tables.” References, optional technical appendices and mandatory checklist do not count. It permits an additional content page **after acceptance**; the camera-ready publication passage explicitly mentions 10 pages. Maximum submission PDF size: 50 MB.

**Operational rule:** budget at most **9 content pages**, including figures and tables; append references, optional technical appendices, then checklist. Do not use the accepted-paper 10-page allowance for an ordinary submission. Do not put acknowledgments in the anonymous submission: the handbook's double-blind instructions expressly exclude them at submission time, despite the general template's page-exemption wording.

The official `neurips_2026.tex` uses `\usepackage{neurips_2026}` by default, equivalent to Main Track. Submission must omit `final` and `preprint`; public non-anonymous preprints may use `preprint`; `final` is for accepted papers only. Do not alter margins, font sizes or the style file. No claims are made here about other tracks' limits.

## Mandatory checklist: preserved, not falsely answered

`/work/paper/checklist.tex` is the **original official 16-item checklist**. Its instructions state that papers missing it will be desk rejected; it does not count against the page limit. It should follow references and optional supplemental material. For a real manuscript:

- Keep heading, questions, subsection/item headings and guidelines; remove only the instruction block as instructed.
- Replace each `\answerTODO{}` with `\answerYes{}`, `\answerNo{}` or `\answerNA{}` and give a 1–2 sentence justification, including for NA. Point to supporting sections when answering Yes.
- Do not modify the questions or invent extra answer macros. Honest No/NA with justification is permitted.

The 16 topics, in official order:
1. Claims.
2. Limitations.
3. Theory assumptions and proofs.
4. Experimental result reproducibility.
5. Open access to data and code.
6. Experimental setting/details.
7. Experiment statistical significance.
8. Experiments compute resources.
9. Code of ethics.
10. Broader impacts.
11. Safeguards.
12. Licenses for existing assets.
13. New assets.
14. Crowdsourcing and research with human subjects.
15. Institutional review board approvals or equivalent.
16. Declaration of LLM usage.

This request produces evidence and an original template, not experiments or a submission: the original checklist intentionally retains its TODOs. It would be incorrect to answer the eventual paper's reproducibility, ethics or empirical questions now. An untouched template is **not** a submission-ready checklist.

The handbook and checklist require substantive/non-standard LLM use in the core method to be described; ordinary editing/basic code help is exempt under the conference policy. The workspace brief is stricter: disclose LLM assistance anyway. These literature notes were prepared by an LLM assistant that downloaded and read the saved sources; no experimental results were generated or verified in this task.

## Bibliography assets

The official ZIP contains **no `.bib` or `.bst`**. Do not claim that such a file was omitted from download or supplied by NeurIPS. Template §4.1 says natbib loads by default and any consistently used reference style is acceptable. Its demonstration bibliography is inline rather than an external mandatory bibliography asset.

`/work/paper/permitted_literature.bib` is a **locally curated, non-official** BibTeX file containing only the six permitted PDFs actually consulted. It records consulted versions, distinguishes publication year from version date, and does not import any reference lists. No custom conference `.bst` is required or supplied. A later manuscript can use a standard TeX-distribution natbib-compatible style (e.g. plainnat); that standard distribution file has not been downloaded here. No TeX compiler or compilation test was needed or performed for this evidence-only request.

## Failures and their interpretation

- Direct official legacy-looking URL `https://neurips.cc/Conferences/2026/PaperInformation/StyleFiles` returned **HTTP 404**. This does **not** show that a 2026 template is unavailable. The official CFP directly links the successfully downloaded 2026 ZIP.
- No CFP, ZIP or handbook download failed. No ICML/ICLR fallback requests were needed.
- PDF-extraction/dependency and tool invocation failures are enumerated in `/work/artifacts/access_and_failure_log.md`.

## Restriction audit

Only the official NeurIPS CFP, handbook and linked template ZIP were successfully fetched for template verification. No proceedings, individual submission/review pages, generic searches, paper citations/cited-by services, template mirrors, Overleaf projects, or third-party summaries were used. Links printed inside official files were not followed. See the shared access log for the exact allowed-paper scope and exposure statement.
