# Access, restriction and failure log

Date: 2026-11-04 UTC. Workspace: `/work`.

## Guardrails applied

- Read `/work/research_request.md` before research/task inspection beyond listing its directory.
- Required memory preflight returned no observations. It was a local memory query, not a literature or web search.
- Read the `paper-navigator` skill for known-paper reading guidance, but did **not** run its search, related-paper, repository-discovery, API or citation-traversal workflows.
- Exact-ID PDF requests only: `2011.14999`, `1703.04730`, `2501.17858`, `2508.11847v1`, `2306.05685`, `2403.04132`, each at `https://arxiv.org/pdf/<supplied-id>`.
- Official template requests only: NeurIPS 2026 CFP, a failed official legacy StyleFiles path, the CFP-linked official 2026 ZIP and official 2026 Main Track Handbook. No generic search engine or third-party source fetch.
- Dependency exception used only for local PDF extraction: standard Debian package indexes/packages via apt. No research content was obtained from dependency resources.
- No links inside the six papers were followed, including GitHub, short URLs, dataset links, citations, subsequent works or blogs. No arXiv abstracts, HTML recommendation sections, conference paper pages or reviews were requested.
- No data, experiment, training or reproduction scripts were created or modified. Shell/Python one-liners were used only to download, extract, render, inspect metadata and audit artifacts. Added files are evidence, original template assets, bibliography and local extraction dependencies.

## Incidental-exposure statement

**No recognized prohibited source was encountered outside the explicitly permitted papers and official conference/template material. No forbidden identity was guessed or sought.** This statement is limited: the identity is intentionally unspecified, so it cannot certify the absence of every possible semantic mention within an explicitly allowed PDF. Explicit starter literature remains permitted under the brief.

Complete permitted PDFs were downloaded and converted, including their reference sections on disk. Substantive reading was restricted to the passages inventoried in `literature_notes.md`. A structural section-heading/page-start locator printed short first-line snippets on reference pages within the permitted PDFs (Broderick PDF pp. 44–49; Koh pp. 10–12; Chiang pp. 9–11; Min pp. 10–12), and incidental nonstarter citation names appeared in permitted body text. None was opened, followed, identified as the forbidden paper, or used as an additional source. Original template example references and official policy links were likewise not followed. There was therefore no recognized prohibited-content encounter triggering the stop rule. If a later stage recognizes prohibited material, it must stop immediately and append its exact location and extent; this log is not permission to investigate identity.

## Successful source evidence

- All six PDFs: successful first direct download; all returned PDF magic bytes and `application/pdf`.
- All six text extractions: successful with local **Poppler pdftotext 25.03.0**, `-layout`.
- Huang v1 PDF p. 9 rendered with local `pdftoppm` and visually read to verify the equation: `/work/artifacts/literature/huang_v1_page09.png`.
- Official NeurIPS 2026 CFP, handbook and template ZIP downloaded successfully. ZIP original retained; all three extracted official members byte-match the archive.
- `source_manifest.json` records URL, final URL, bytes and SHA256 for successfully fetched research/template sources, plus the official 404 outcome. Download logs also live in each source directory. Some original download-log paths are workspace-relative; resolve them against `/work`.

## All failed or blocked operations

1. **Initial extraction capability probe:** `command -v pdftotext` found no binary. It did not corrupt any files; PDF extraction was initially unavailable.
2. **System-install attempt blocked:** `sudo -n apt-get update -qq && sudo -n apt-get install -y -qq poppler-utils` was rejected by the sandbox because sudo is not allowed. No system package installation occurred.
3. **Initial package download failed:** `apt-get download poppler-utils` returned exit 100: `Unable to locate package poppler-utils` because system apt lists were unavailable.
4. **Non-root apt update warning:** updating a workspace-local lists directory succeeded but apt's post-update cleanup emitted `Permission denied` for `/var/cache/apt/archives/partial/*.deb`. The overall command succeeded. This did not prevent local downloads.
5. **First local binary probe failed:** extracted Poppler binary lacked `libpoppler.so.147` (exit 127 from the binary; wrapper command itself returned success).
6. **Second local binary probe failed:** after adding libpoppler147, `libjpeg.so.62` was missing (exit 127).
7. **Third local binary probe failed:** after adding the first set of shared-library dependencies, `libjbig.so.0` was missing (exit 127).
8. **Fourth local binary probe failed:** after adding libjbig0/libgpg-error0, `libsharpyuv.so.0` was missing. The subprocess raised `CalledProcessError`; extraction had not begun in that attempt.
9. **Tool-call invocation mistake:** one parallel wrapper issued three empty `read_file` argument dictionaries; all three were rejected for missing `file_path`. No file was read or written by those calls. Retried with explicit paths using direct calls.
10. **Official template-path failure:** `https://neurips.cc/Conferences/2026/PaperInformation/StyleFiles` returned HTTP 404. No response body was saved or used. Corrected by following the official CFP's exact template link, not by using a mirror or a broad search.

There were **no permitted-paper download failures, no final PDF extraction failures, and no recognized prohibited-page encounters**. No background process, experiment failure or compilation failure is being omitted: no experiments or LaTeX compilation were run.

## Dependency recovery and reproducible extraction

No root privileges were needed. Package lists were placed under `/work/artifacts/dependencies/apt-lists/`; `.deb` originals and extracted binaries/libraries are under `/work/artifacts/dependencies/` and its `poppler/` subtree. Downloaded from standard Debian trixie repositories (including Debian security for libnss3):

`poppler-utils`, `libpoppler147`, `libjpeg62-turbo`, `libgpgmepp6t64`, `libopenjp2-7`, `liblcms2-2`, `libtiff6`, `libnss3`, `libnspr4`, `libgpgme11t64`, `libassuan9`, `libwebp7`, `libdeflate0`, `liblerc4`, `libjbig0`, `libgpg-error0`, `libsharpyuv0`.

The successful extraction command pattern (replace ID with one of the six supplied IDs):

```sh
LD_LIBRARY_PATH=/work/artifacts/dependencies/poppler/usr/lib/x86_64-linux-gnu \
  /work/artifacts/dependencies/poppler/usr/bin/pdftotext -layout \
  /work/artifacts/literature/ID.pdf /work/artifacts/literature/ID.txt
```

This is an artifact-preparation command, not experiment code. Package originals preserve exact downloaded versions. System-installed libraries were also used; this is not asserted to be a portable standalone Poppler distribution.

## Deliberately unverified or incomplete

- No unrestricted novelty search was allowed or attempted.
- No code repository availability, license, API behavior, dataset contents, dataset checksums or experimental result was independently verified beyond the actual source PDFs.
- No full appendix-proof audit was completed.
- No ICML/ICLR comparison was needed after the preferred official NeurIPS 2026 template was found.
- Original checklist TODOs are preserved; answering them for an unperformed research paper would be misleading.
- No manuscript or compiled template PDF was requested in this evidence subtask or produced. Official ZIP contains `.tex`, `.sty`, checklist only, not a PDF/BibTeX/style bundle.
