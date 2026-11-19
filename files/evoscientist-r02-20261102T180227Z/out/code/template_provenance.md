# Official ICLR template: provenance and page-limit evidence

Verified 2026-11-02 UTC using only the explicitly permitted official `ICLR/Master-Template` repository, its raw files, and repository API. No conference search, third-party template, or NeurIPS fallback was used.

## Latest available release in the permitted repository

**ICLR 2027** is the highest-year template in the retrieved official root directory listing. The repository supplies both `iclr2027.zip` and an `iclr2027/` source directory. This is a statement about the retrieved official repository snapshot, not a claim that all future conference policy changes have been checked elsewhere.

Official locators:

- Repository: https://github.com/ICLR/Master-Template
- Root listing actually fetched: https://api.github.com/repos/ICLR/Master-Template/contents/
- 2027 listing actually fetched: https://api.github.com/repos/ICLR/Master-Template/contents/iclr2027
- Official archive actually fetched: https://raw.githubusercontent.com/ICLR/Master-Template/master/iclr2027.zip
- Official README actually fetched: https://raw.githubusercontent.com/ICLR/Master-Template/master/README.md
- Template source locator, verified through the directory listing and extracted archive: https://raw.githubusercontent.com/ICLR/Master-Template/master/iclr2027/iclr2027_conference.tex
- Style locator, likewise verified: https://raw.githubusercontent.com/ICLR/Master-Template/master/iclr2027/iclr2027_conference.sty

The files live inside `iclr2027/`, not at an assumed repository-root style path. Root-level files named for older years are not evidence of the latest version. The retrieved README merely says “Template and style files for ICLR”; year and policy evidence comes from the listing and actual 2027 source, not the README.

## Saved artifacts and version evidence

- `template/repo_contents.json`: root API evidence.
- `template/README.md`: official repository README.
- `template/iclr2027_contents.json`: official source-directory API evidence.
- `template/iclr2027.zip`: original official archive.
- `template/iclr2027/`: extracted, unmodified official sources:
  - `iclr2027_conference.tex`
  - `iclr2027_conference.sty`
  - `iclr2027_conference.bst`
  - `iclr2027_conference.bib` (official example bibliography, not the research bibliography)
  - `math_commands.tex`
  - `natbib.sty`
  - `fancyhdr.sty`
- `template/integrity_manifest.json`: byte counts, SHA-256, official Git blob SHA, exact raw locators, and hash-verification results for all seven source files.

The archive was fetched at `2026-11-02T18:10:12.246806+00:00`, HTTP 200, 27,376 bytes:

- Archive SHA-256: `eaa8a3306b052faac723a710e3196d140ae24ed031034cad7448f8a0dcc7484bcc`
- Official archive Git blob SHA: `a079db54799d53378169a6e2c4f2105371522181`
- Official 2027 directory Git tree SHA: `413badc001888f7d3277699d80e64f6c8fb38781`
- Template `.tex` Git blob SHA: `c088c541a69898bbb329f86ba3a532254b31816b`
- Template `.sty` Git blob SHA: `f61ad7efce0855557694078c0945e6c33feb8236`

All seven archive-extracted files match the corresponding official directory-listing Git blob hashes, computed with Git's `blob <byte-count>\0<content>` framing. Thus the archive and individual official source tree agree. The `master` URLs are mutable; hashes and saved snapshots, not the URL alone, identify what was consulted. No commit SHA is claimed because a commit-specific endpoint was not fetched.

## Page limit: exact official wording, not inference from old years

In `template/iclr2027/iclr2027_conference.tex`, **line 131**, within “General formatting instructions,” the official text is:

> There will be a strict upper limit of **9 pages** for the main text of the initial submission, with unlimited additional pages for citations. This limit will be expanded to **10 pages** for rebuttal/camera ready.

Therefore, for this retrieved template:

- Initial submission main text: **9 pages**.
- Rebuttal/camera-ready main text: **10 pages**.
- Citations: explicitly allowed unlimited additional pages.
- Appendix: the source includes an `\appendix` section after the bibliography, but does **not** explicitly state an unlimited appendix allowance in the quoted rule. Do not convert “unlimited citations” into a separately verified unlimited-appendix policy. Any further appendix restrictions or later policy changes remain unverified under the access restriction.

Other directly relevant retrieved instructions:

- Lines 13–16 and 49: submission must be anonymous; keep `\iclrfinalcopy` commented for submission.
- Lines 87–89: use current official style files; tweaking them may be grounds for rejection.
- Lines 352–356: do not alter the formatting rectangle or font sizes; pages should be numbered.
- Lines 361–363: use US Letter, not A4.
- Lines 399–413: AI-use statement is **required**, excluded from the page limit, and at most one page; the linked policy itself was not opened. The template specifically asks authors to review AI-assisted work and take responsibility for the final content.
- Lines 415–427: ethics statement is recommended, excluded from the page limit, and at most one page.
- Lines 429–444: reproducibility statement is recommended and excluded from the page limit.

Line numbers refer to this saved `.tex` snapshot and can change upstream. The `.sty` includes inherited historical comments; those are not evidence that the directory is an old release. The current source title and package names explicitly say ICLR 2027.

## Verification boundary

Downloaded and hash-checked the source package; **did not compile** a sample manuscript or test a LaTeX installation. The archive does not include `iclr2027_conference.pdf`, despite mentioning that filename in its prose. The four literature PDFs are independently readable and have been text-extracted; this does not constitute a template compilation test.

All direct HTTP requests are in `access_log.json`. No access to NeurIPS was needed because the official ICLR 2027 template was available.
