# Official NeurIPS template provenance

Verified/accessed: **2026-11-02 (UTC)**. Actual edition: **NeurIPS 2026**, Fortieth Annual Conference. This is an official published 2026 template, not a renamed 2025 template. No 2025 fallback was necessary. Scope of page-limit verification: **Main Track**; other tracks can have different rules.

## Official source chain

1. https://neurips.cc/Conferences/2026/CallForPapers — HTTP 200; actual "Paper template" link points to the archive below.
2. https://media.neurips.cc/Conferences/NeurIPS2026/Formatting_Instructions_For_NeurIPS_2026.zip — HTTP 200; downloaded verbatim as `Formatting_Instructions_For_NeurIPS_2026.zip`.
3. https://neurips.cc/Conferences/2026/MainTrackHandbook — HTTP 200; independently verifies submission/camera-ready limits, formatting, anonymization, and checklist requirements.
4. Attempted https://neurips.cc/Conferences/2026/PaperInformation/StyleFiles — HTTP 404. This guessed official route is absent; it does **not** mean no 2026 template exists. The actual CFP-linked archive above exists.

No search engine, accepted-paper listing, external template mirror, blog, repository, or unrelated conference material was opened. External links appearing on official pages were not followed. Redirects were restricted to neurips.cc and its subdomains.

## Files downloaded and extracted

The official ZIP contains exactly:
- `neurips_2026.tex` — formatting instructions and example source, identifies itself as "Formatting Instructions For NeurIPS 2026".
- `neurips_2026.sty` — official style file; preserved unchanged.
- `checklist.tex` — official checklist, preserved unchanged; downloaded **inside this ZIP**, not from a guessed standalone checklist URL.

Original official HTML pages, extracted readable text, link metadata, and UTC/status access log (`access_template.json`) are also retained here. No compiled PDF was supplied in the ZIP; none was fabricated or compiled in this task.

## Verified page limit and formatting

**Submission: 9 content pages including figures and tables.**

`neurips_2026.tex`, section 1.1 Style:
> Papers may only be up to {\bf nine} pages long, including figures.

The next sentence excludes additional pages containing acknowledgments, references, checklist, and optional technical appendices from content pages. However, the handbook explicitly says **do not include acknowledgments at submission time** (double-blind anonymity).

Main Track Handbook, Authors → Paper Formatting Instructions:
> The main text of a submitted paper is limited to nine content pages, including all figures and tables. Additional pages containing references, optional technical appendices and mandatory paper checklist do not count as content pages. If your submission is accepted, you will be allowed an additional content page for the camera-ready version. The maximum file size is 50MB.

Thus **accepted camera-ready: 10 content pages**. This extra page is **not** an initial-submission allowance. References, appendices, checklist and content should be combined into one PDF. The official suggested order is content → references → appendices → checklist.

Use `\usepackage{neurips_2026}` or `[main]` for anonymized submission; do not use `final` or `preprint` for submission. `final` is for accepted papers and `preprint` for public non-anonymous preprints. Do not modify style/margins/fonts. Template specifies 10-point text, 11-point leading and a 5.5 by 9 inch text rectangle.

## Checklist

Read `checklist.tex` in full (251 lines). It is mandatory; omission can cause desk rejection. Keep questions, headings and guidelines, replace TODO answers with Yes/No/NA and provide 1–2-sentence justifications with evidence pointers. The checklist does not count toward the content-page limit. Remove only its instruction block when completing a paper, not in this preserved pristine download.

The 16 topics are claims; limitations; theory assumptions/proofs; reproducibility; data/code access; experimental details; statistical significance; compute; ethics; broader impacts; safeguards; asset licenses; new assets; human subjects; IRB/equivalent; and LLM usage. Answers have **not** been completed for the project. Linking policies are not evidence they have been independently reviewed; no linked policy or external discussion was followed.

## Actual-read extent

- CFP: main call text, key dates/key links, template link and track-specific caveat; navigation ignored.
- Official template source: opening track/options comments and formatting instructions through initial citation/anonymization instructions (lines 1–280).
- Checklist: all lines 1–251.
- Handbook: targeted Authors → formatting, anonymity, submission, data/code, checklist and LLM policy text; camera-ready page-limit passage. No accepted-paper listing accessed.
- `.sty`: downloaded/preserved, not audited line by line. No compilation test performed.

## Limitations

This establishes the latest of the user-requested 2026/2025 editions actually published on the directly accessed official pages as of the access date. It is not a claim that other tracks share the Main Track limit. No speculative future edition was sought. Check current track-specific instructions again before a real submission.

## Integrity hashes and full HTTP access log

The tables below are generated from locally downloaded bytes and recorded HTTP results.

| UTC | Requested URL | Status or result | Final URL | Bytes |
|---|---|---|---|---:|
| 2026-11-02T16:08:21.238727+00:00 | https://arxiv.org/abs/2306.05685 | 200 | https://arxiv.org/abs/2306.05685 | 43641 |
| 2026-11-02T16:08:24.875757+00:00 | https://arxiv.org/pdf/2306.05685 | 200 | https://arxiv.org/pdf/2306.05685 | 1580141 |
| 2026-11-02T16:08:28.218097+00:00 | https://arxiv.org/abs/2403.04132 | 200 | https://arxiv.org/abs/2403.04132 | 42506 |
| 2026-11-02T16:08:31.815467+00:00 | https://arxiv.org/pdf/2403.04132 | 200 | https://arxiv.org/pdf/2403.04132 | 1081950 |
| 2026-11-02T16:08:35.122626+00:00 | https://arxiv.org/abs/2011.14999 | 200 | https://arxiv.org/abs/2011.14999 | 43574 |
| 2026-11-02T16:08:38.720256+00:00 | https://arxiv.org/pdf/2011.14999 | 200 | https://arxiv.org/pdf/2011.14999 | 1046828 |
| 2026-11-02T16:08:42.076306+00:00 | https://arxiv.org/abs/2501.17858 | 200 | https://arxiv.org/abs/2501.17858 | 42201 |
| 2026-11-02T16:08:45.666426+00:00 | https://arxiv.org/pdf/2501.17858 | 200 | https://arxiv.org/pdf/2501.17858 | 1267116 |
| 2026-11-02T16:08:49.054415+00:00 | https://arxiv.org/abs/2508.11847v1 | 200 | https://arxiv.org/abs/2508.11847v1 | 40951 |
| 2026-11-02T16:08:52.759179+00:00 | https://arxiv.org/pdf/2508.11847v1 | 200 | https://arxiv.org/pdf/2508.11847v1 | 1729289 |
| 2026-11-02T16:12:46.671574+00:00 | https://neurips.cc/Conferences/2026/CallForPapers | 200 | https://neurips.cc/Conferences/2026/CallForPapers | 53579 |
| 2026-11-02T16:12:48.420298+00:00 | https://neurips.cc/Conferences/2026/PaperInformation/StyleFiles | HTTP Error 404: Not Found | — | — |
| 2026-11-02T16:13:03.584694+00:00 | https://media.neurips.cc/Conferences/NeurIPS2026/Formatting_Instructions_For_NeurIPS_2026.zip | 200 | https://media.neurips.cc/Conferences/NeurIPS2026/Formatting_Instructions_For_NeurIPS_2026.zip | 20259 |
| 2026-11-02T16:13:54.468973+00:00 | https://neurips.cc/Conferences/2026/MainTrackHandbook | 200 | https://neurips.cc/Conferences/2026/MainTrackHandbook | 167185 |

| Local file | SHA-256 |
|---|---|
| artifacts/sources/2011.14999.pdf | b25d1b808fd68bc283c69694dd069b13c95259a762af40e92f4300bb4183ed4a |
| artifacts/sources/2306.05685.pdf | 1574982845157569b85c1214bfa9987000384d7a5e3b5fbdcc5a29afec59cb81 |
| artifacts/sources/2403.04132.pdf | 039bccd60a7d49bfda80ce17ea627654736928eee9a7ee75767a38d04a01562f |
| artifacts/sources/2501.17858.pdf | 90d2df39bab4b94ddbd19633af368fdf265db6fd73e39c5fc88b10b08ae85ae6 |
| artifacts/sources/2508.11847v1.pdf | 3539869811b8dc60da3ebb0486127b5aca1a00b5e0bc468c0813ba1dd4a0f3ef |
| paper/template/Formatting_Instructions_For_NeurIPS_2026.zip | 82473931e3ef710fcd3f4a8cd4119b9de32e56825f90f9e5a6d55f2d01b817d9 |
| paper/template/neurips_2026.tex | cf4cee7991665306d1daaa3985be4feec7f8889d6d072ffa12f99a8e1537d797 |
| paper/template/neurips_2026.sty | c3fc2894e83d2517ca18b66741d6c595986d97957dc08ec08bb2125a7ec4555a |
| paper/template/checklist.tex | 780ba13c480f652dcc42e69ed61a752ce0ea270f15d332d4a45b059dabad84f6 |
