# Source access and reading log

Date: 2026-11-02 UTC. All five frozen files in `/initial-state/inputs/0/` were read in full: TASK.md, data.md, deliverable.md, resources.md and starter_literature.md. Their original SHA-256 values are in `context/frozen-inputs.json`. The Research objective issue was read before settling the initial brief.

All ten explicitly permitted starter papers were downloaded directly from `https://arxiv.org/pdf/<supplied-id>` with normal TLS verification and converted with pdftotext. Their SHA-256 values, returned versions and source URLs are in `context/literature/sources.json`. No search query was used, and no links from the papers' related-work sections or reference lists were followed. Selected substantive sections, not every appendix, were consulted as documented in PRIOR_WORK.md. No excluded-content encounter was identified during these accesses. The task permits the starter papers themselves; citing their consulted findings does not imply endorsement or reproduction of their results.

Tools used for reading: Python urllib, Poppler pdftotext and PyMuPDF. Binary PDFs and extracted texts are local reading cache, ignored by git; provenance and citation records are versioned. `python3 context/tools/fetch_literature.py` retrieves the pinned paper versions for checking the notes. Published numbers in the context evidence table are explicitly attributed to their sources and are not measurements of the present study; final empirical tables/figures must come from the analysis owner's executed code.

## Settled-scope maintenance

The later context revision reads story-repo's settled study plan and idea-review-repo#2's complete feasibility answer. It adds exploratory tolerance, model-level descriptive uncertainty and handoff rules to Brief, and packages bibliography/provenance/tools beneath `context/` for the assigned delivered path. No new external literature was accessed for this revision. Feasibility's reported implementation checks are attributed to that owner, not represented as a numerical audit by the context position.
