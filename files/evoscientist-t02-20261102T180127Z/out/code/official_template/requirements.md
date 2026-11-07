# Verified official template requirements — NeurIPS 2026 main track

Verification date: 2026-11-02 UTC. Selected per the requested preference for NeurIPS 2026. This is the current released 2026 package linked by the official 2026 call for papers on the verification date; no older-year substitution or unofficial mirror was used. The `.sty` identifies itself as `2026-01-29 NeurIPS 2026 submission/camera-ready style file` and comments say last revision January 2026. This identifies the style version, not an independently verified publication timestamp. No cross-conference release-date survey was performed because the preferred 2026 package was available.

## Source chain and original package

1. Requested https://neurips.cc/Conferences/2026/PaperInformation/StyleFiles at 2026-11-02T18:07:09.162141+00:00: HTTP 404. Error body archived as `neurips2026_stylefiles.html.error`; SHA256 `7695a4e7ec9fca30858d026cdf564d2137926bd2cf2c5e7ee0315fa426e77a98`.
2. Read direct official author instructions https://neurips.cc/Conferences/2026/CallForPapers : 200, completed 2026-11-02T18:07:12.090749+00:00, HTML SHA256 `f1e97ffc8591d777da7b48f3680b42a8f210b2b6db3c4cd4d18f217a149f72a0`. Its `Paper template` anchor links the package below.
3. Downloaded exact official package URL https://media.neurips.cc/Conferences/NeurIPS2026/Formatting_Instructions_For_NeurIPS_2026.zip : 200, started 2026-11-02T18:07:39.961057+00:00, completed 2026-11-02T18:07:41.522938+00:00. 20,259 bytes. SHA256 `82473931e3ef710fcd3f4a8cd4119b9de32e56825f90f9e5a6d55f2d01b817d9`.
4. Independently cross-checked official author instructions at https://neurips.cc/Conferences/2026/MainTrackHandbook : 200, completed 2026-11-02T18:07:43.164214+00:00, HTML SHA256 `b237bf53cc2e92d11b2c6c66aea7c8c2a772c7907143f615074f9e19dc373163`.

Archive: `/work/official_template/Formatting_Instructions_For_NeurIPS_2026.zip` (original downloaded bytes, unmodified).

Original extracted files (byte equality with ZIP members verified):

| File | SHA256 |
|---|---|
| `/work/official_template/original_package/neurips_2026.tex` | `cf4cee7991665306d1daaa3985be4feec7f8889d6d072ffa12f99a8e1537d797` |
| `/work/official_template/original_package/neurips_2026.sty` | `c3fc2894e83d2517ca18b66741d6c595986d97957dc08ec08bb2125a7ec4555a` |
| `/work/official_template/original_package/checklist.tex` | `780ba13c480f652dcc42e69ed61a752ce0ea270f15d332d4a45b059dabad84f6` |

`download_manifest.json` preserves exact requested/final URLs, status, UTC timestamps, response headers and hashes. `package_inventory.json` records member sizes and hashes. There is no official PDF or separate checklist ZIP inside this downloaded archive; do not claim one was downloaded or fabricate one. No LaTeX compilation was attempted and no experiment implementation was produced.

## Main content limit and submission packaging

- **Submission: nine content pages**, including figures and tables. Verified both in `neurips_2026.tex`, Style subsection, and handbook, Authors → Paper Formatting Instructions.
- Additional pages for references, optional technical appendices and the **mandatory** checklist do not count. Template also exempts acknowledgments in general, but handbook explicitly prohibits acknowledgments at anonymous submission time.
- **Accepted/camera-ready: one additional content page**, i.e. ten, per handbook. Do not mistakenly use this allowance for initial submission.
- Single PDF, suggested order: paper content, references, technical appendices, checklist. Maximum PDF size **50 MB**. Appendices are part of the same PDF, not separate appendix PDFs; code/data may be a separate supplementary file. Technical appendices have no page limit, but reviewers need not read them and core evidence must stand alone.
- Use the current official `.sty`, unmodified. Submission default/main track: `\usepackage{neurips_2026}` or `[main]`; **omit** `final` and `preprint` during review. Default/main is anonymous with line numbers. `[preprint]` is for nonanonymous online preprints, `[main, final]` only after acceptance. Apply anonymity to supplementary/linked assets too.
- The official style specifies single-column article text, a 5.5-by-9-inch text rectangle, 10-point body text, 11-point leading. Do not shrink margins/fonts to meet the limit.

## Checklist requirements

Primary source: unmodified `original_package/checklist.tex`, especially introductory instructions and all 16 numbered questions. The template ends with `\input{checklist.tex}`.

- **Missing checklist → desk rejection.** It is part of the submission, visible to reviewers, revised if necessary for final publication, and does **not** count toward the nine-page limit.
- Place after references **and after any optional appendices**. This is stated in the checklist and agrees with the handbook's suggested ordering.
- Every question: use `\answerYes{}`, `\answerNo{}`, or `\answerNA{}` and supply a **1–2-sentence justification even for NA**. Explain and point to relevant paper sections for Yes. No/NA alone is generally not a rejection reason if justified; reproduce the source's nuances rather than promising all-Yes answers.
- Delete the initial instruction block in a working manuscript, keep the checklist heading, question/subsection headings, questions/answers and guidelines. Do not change questions; use provided answer macros. Preserve original downloaded files and edit a separate working copy.
- Topics: (1) claims, (2) limitations, (3) theory assumptions/proofs, (4) experimental reproducibility, (5) open data/code, (6) experimental details, (7) statistical significance, (8) compute resources, (9) ethics, (10) broader impacts, (11) safeguards, (12) existing-asset licenses, (13) new assets, (14) crowdsourcing/human subjects, (15) IRB/equivalent, (16) LLM usage declaration.
- For a size/grokking study, especially record: split and initialization randomness; exact hyperparameters and selection procedure; error-bar meaning and calculation; failed/preliminary runs and total compute, not just successful reported runs; hardware/memory/runtime; asset provenance and limitations.
- The checklist does not universally mandate code release, but does require a reasonable avenue for reproducibility. Do not check open-code availability merely because synthetic data can be generated.
- **Autonomous-research relevance:** question 16 asks whether LLM usage is described if it is an important, original, or nonstandard component of core methods. Writing/editing/formatting-only use that does not affect core methodology/scientific rigor/originality is exempt. An autonomous experimentation contribution should assess this explicitly, not automatically call LLM usage NA.

## Independence handling

No instruction-linked papers, resource lists, proceedings, submission platform, repositories, or third-party template mirrors were opened. Incidental bibliography/further-reading/link exposure in source excerpts is logged at `/work/artifacts/literature/independence_audit.md` and not used as research evidence.
