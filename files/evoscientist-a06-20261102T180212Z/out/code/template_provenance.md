# Official ICLR 2027 template provenance and submission requirements

## Scope and as-of determination

- Requested cutoff: **2026-11-02 (UTC)**; GitHub revision lookup used `until=2026-11-02T23:59:59Z`. Saved HTTP response dates are 2026-11-02, approximately 18:12 UTC.
- Selected **ICLR 2027**, satisfying the preference for ICLR 2027 over ICML/NeurIPS 2026. No other conference or topical literature was searched.
- Official repository: https://github.com/ICLR/Master-Template
- Latest repository commit returned at or before the cutoff: **`46ed6f4c6cef5b175dde23639e77d44c3463b230`**, authored and committed **2026-09-01T14:19:09Z**, message **`2027 template`**.
- Immutable selected directory: https://github.com/ICLR/Master-Template/tree/46ed6f4c6cef5b175dde23639e77d44c3463b230/iclr2027
- Revision evidence: https://api.github.com/repos/ICLR/Master-Template/commits?until=2026-11-02T23%3A59%3A59Z&per_page=1
- The pinned repository tree includes 2027 as its newest year. The GitHub Releases endpoint returns only old 2019/2018 releases; therefore the latest available **official yearly template** is the 2027 directory/ZIP, not the stale GitHub release labeled 2019.
- The official 2027 Author Guidelines link directly to the conference-hosted ZIP below. It is **byte-for-byte identical** to the ZIP at the dated GitHub revision. This verifies that the preferred GitHub template is also the template distributed by the official conference instructions.
- No future-dated source was used. Live instruction pages have no HTTP Last-Modified header; their saved contents document what was served on 2026-11-02, not an independently versioned publication history. The template itself is pinned to a pre-cutoff commit.

## Official instruction sources

[1] ICLR 2027 Author Guidelines: https://iclr.cc/Conferences/2027/AuthorGuidelines

[2] ICLR 2027 official style-files download, linked by [1]: https://media.iclr.cc/Conferences/ICLR2027/iclr-2027-style-files.zip

[3] ICLR 2027 AI Policy for Authors: https://iclr.cc/Conferences/2027/AIPolicyForAuthors

[4] ICLR 2027 Call for Papers: https://iclr.cc/Conferences/2027/CallForPapers

[5] Immutable official template source: https://raw.githubusercontent.com/ICLR/Master-Template/46ed6f4c6cef5b175dde23639e77d44c3463b230/iclr2027/iclr2027_conference.tex

[6] Immutable official GitHub ZIP: https://raw.githubusercontent.com/ICLR/Master-Template/46ed6f4c6cef5b175dde23639e77d44c3463b230/iclr2027.zip

## Exact downloaded official files, all in /work root

The following seven files are unmodified official template/support files. Each URL is pinned to the same verified commit.

| Local file | Exact official URL |
|---|---|
| `/work/iclr2027_conference.tex` | https://raw.githubusercontent.com/ICLR/Master-Template/46ed6f4c6cef5b175dde23639e77d44c3463b230/iclr2027/iclr2027_conference.tex |
| `/work/iclr2027_conference.sty` | https://raw.githubusercontent.com/ICLR/Master-Template/46ed6f4c6cef5b175dde23639e77d44c3463b230/iclr2027/iclr2027_conference.sty |
| `/work/iclr2027_conference.bst` | https://raw.githubusercontent.com/ICLR/Master-Template/46ed6f4c6cef5b175dde23639e77d44c3463b230/iclr2027/iclr2027_conference.bst |
| `/work/iclr2027_conference.bib` | https://raw.githubusercontent.com/ICLR/Master-Template/46ed6f4c6cef5b175dde23639e77d44c3463b230/iclr2027/iclr2027_conference.bib |
| `/work/fancyhdr.sty` | https://raw.githubusercontent.com/ICLR/Master-Template/46ed6f4c6cef5b175dde23639e77d44c3463b230/iclr2027/fancyhdr.sty |
| `/work/natbib.sty` | https://raw.githubusercontent.com/ICLR/Master-Template/46ed6f4c6cef5b175dde23639e77d44c3463b230/iclr2027/natbib.sty |
| `/work/math_commands.tex` | https://raw.githubusercontent.com/ICLR/Master-Template/46ed6f4c6cef5b175dde23639e77d44c3463b230/iclr2027/math_commands.tex |

Also saved unchanged:

- `/work/iclr-2027-style-files.zip` — conference-hosted official ZIP [2].
- `/work/iclr2027.zip` — identical official GitHub ZIP [6].
- `/work/iclr2027_AuthorGuidelines.html` — original HTML from [1].
- `/work/iclr2027_AIPolicyForAuthors.html` — original HTML from [3].
- `/work/iclr2027_CallForPapers.html` — original HTML from [4].
- `/work/iclr2027_commit_asof_2026-11-02.json` — official GitHub cutoff query response.
- `/work/iclr2027_repository_tree.json` — official pinned Git tree, including Git blob hashes; source: https://api.github.com/repos/ICLR/Master-Template/git/trees/46ed6f4c6cef5b175dde23639e77d44c3463b230?recursive=1
- `/work/iclr_template_releases.json` — official release metadata; source: https://api.github.com/repos/ICLR/Master-Template/releases?per_page=20

Locally derived documentation/evidence:

- `/work/iclr2027_AuthorGuidelines.txt`, `/work/iclr2027_AIPolicyForAuthors.txt`, `/work/iclr2027_CallForPapers.txt` — readable text extracted from corresponding official HTML, not independent official files.
- `/work/iclr2027_download_manifest.json` — exact URLs, response URLs, byte sizes, SHA-256, HTTP dates, available Last-Modified headers, and Git blob hashes for retrieved files.
- `/work/template_provenance.md` — this report.

**No official `iclr2027_conference.pdf` is present in the selected repository directory or either official ZIP**, despite a reference to that filename in the template prose. No substitute PDF was invented or compiled. The sample `.bib` is retained as part of the official template, not used as literature evidence.

## Official page limits and formatting

The explicit Paper formatting section of [1] says:

> At the time of submission, the main text should be 9 pages or fewer. During the discussion/rebuttal phase and for the camera ready, the page limit will be increased to 10 pages to allow for new results/discussions.

The dated template [5] independently agrees:

> There will be a strict upper limit of 9 pages for the main text of the initial submission, with unlimited additional pages for citations. This limit will be expanded to 10 pages for rebuttal/camera ready.

Apply these rules:

- **Initial submission: at most 9 pages of main text.** Overlength main text can cause desk rejection.
- **Discussion/rebuttal and camera-ready: at most 10 pages of main text.**
- **References: excluded**, unlimited pages.
- **Appendices: unlimited**, after the bibliography; reviewers need not read them. A single paper-plus-supplementary-text PDF is encouraged; a separate supplementary appendix is also permitted by the FAQ.
- **AI use statement: required**, excluded from page count, no more than 1 page according to [5]. Place before references, following the template.
- **Ethics statement: recommended where appropriate**, excluded, no more than 1 page.
- **Reproducibility statement: recommended**, paragraph-long, before references, excluded.
- **Acknowledgments: excluded** according to the guideline FAQ; do not reveal identities during anonymous review.
- Use the actual official style and bibliography style. The template starts with `\documentclass{article}` and `\usepackage{iclr2027_conference,times}`. It uses `\bibliographystyle{iclr2027_conference}`.
- US Letter paper, 10-point text, 11-point vertical spacing, 5.5-inch by 9-inch text area. Do **not** manually change official fonts, margins, text dimensions, or style parameters. Pages should be numbered. These are source instructions, not a newly designed style.
- Leave `\iclrfinalcopy` commented out for anonymous submission; enable only for camera-ready. Anonymize main text, supplement, and code/repository links.

### Official-page inconsistency to avoid

Some camera-ready/FAQ text in [1] calls 10 pages “identical with the submission version.” That wording conflicts with the explicit initial-submission rule on the same page. The Paper formatting section and the pre-cutoff template [5] both unambiguously distinguish **9 initially / 10 rebuttal-camera-ready**. Do not treat the FAQ wording as permission for a 10-page initial submission.

## Required checklist: what is actually required

**No separate mandatory NeurIPS-style paper/reproducibility checklist is specified in the inspected ICLR 2027 author guidelines, official template bundle, or AI author policy.** No such checklist was invented or imported from another conference. This finding is limited to these official sources; OpenReview submission-form fields were not inspected because paper-listing/submission-system browsing was outside the allowed retrieval scope.

The following is a **locally summarized compliance checklist**, not an additional official checklist file:

- [ ] Use unmodified official **2027** style, anonymous submission mode, US Letter, numbered pages.
- [ ] Main text meets **9-page initial** or **10-page rebuttal/camera-ready** limit; apply the exclusions listed above.
- [ ] Main text, supplements, and linked artifacts do not reveal author identities during review.
- [ ] Include the **mandatory AI use statement**, at most 1 page, outside the main-text page count; complete AI disclosures in **both paper and submission form** [3].
- [ ] State which required-disclosure tasks used generative AI, which did not, and which were not applicable. Describe human review/verification of AI-assisted work; authors retain responsibility for all content [3,5].
- [ ] Read and adhere to the ICLR Code of Ethics and explicitly acknowledge it during submission; adhere to the Code of Conduct [1]. These documents were not separately fetched.
- [ ] Meet administrative requirements in [1]: genuine abstract; all authors have OpenReview profiles; author roster fixed after abstract deadline; no more than 20 submissions per author; reciprocal-reviewer requirements or applicable newcomer exemption; no prohibited dual submission.

### AI tasks with required disclosure [3]

The official policy lists:

1. Generate synthetic datasets.
2. Help develop theoretical models or conceptual frameworks.
3. Formulate mathematical claims.
4. Provide critical ingredients for proving mathematical claims.
5. Assist in writing proofs.
6. Propose or refine hypotheses.
7. Design or provide feedback on research methodology or experiments.
8. Implement methods.
9. Assist with translation.
10. Clean and reformat datasets.
11. Support qualitative and thematic data analysis.
12. Interpret results.

The policy separately **recommends** disclosure for tasks including creating/editing software code, drafting/editing paper text, creating figures, suggesting experimental parameters, information searching, and reference formatting. It lists both “implement methods” as required and “create or edit software code” as recommended; preserve this distinction rather than assuming all coding assistance is optional to disclose. The AI-use section itself is mandatory even when the appropriate statement is no use/not applicable.

Recommended but not mandatory paper additions: an ethics statement where relevant, a reproducibility statement pointing to actual methods/data/code/proofs, and anonymous supplementary code. Do not label these as mandatory checklist items.

## Submission timing as of the requested date

Official [1,4] list abstract deadline **September 18, 2026 AoE**, full paper/supplement deadline **September 25, 2026 AoE**. These deadlines have already passed as of 2026-11-02. Thus this is the latest available template, **not an assertion that a new ICLR 2027 submission is still possible**. Reviews are scheduled for November 5; discussion November 5–18; decisions December 16, according to the instructions available at retrieval. No later review, decision, or camera-ready source was accessed.

## Integrity verification and boundaries

- Both ZIPs passed `zipfile.testzip()`.
- Both ZIPs are 39,348 bytes and have SHA-256 **`0d940dfa9398ae99a18f24a85a8a683f367204b6af6d17d2899e60a67102529e`**.
- Every downloaded template/support file and the GitHub ZIP matched its official pinned Git blob SHA-1 (computed using Git's `blob <length>\0<bytes>` convention).
- Every one of the seven template/support files exactly matched the corresponding entry in both ZIPs. Individual SHA-256 values are in `/work/iclr2027_download_manifest.json`.
- Retrieval used Python `urllib` with only direct official ICLR pages, the official ICLR template GitHub API, and raw GitHub files. An initial guessed official `/Conferences/2027/AuthorGuide` URL returned 404; the correct `/AuthorGuidelines` URL was obtained from the official CFP.
- No topical search, proceedings, paper listing, unidentified prior paper, citation graph, or code-agent delegation was used. No linked paper or sample citation destination was opened.
- No scientific manuscript was created or edited, and no scientific style was invented. Official files were downloaded without modification. Compilation was not attempted; this task validates retrieval and integrity, not local TeX-package availability.
