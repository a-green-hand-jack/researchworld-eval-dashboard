# Review record: paper-repo PR #14 (into `final`), head cb64548cec37485e91ae32fa8587dea35481ee8c

This supersedes the findings in `review-pr14.md` (head e1ed40a).

## Resolution of the earlier findings
1. **Counts.** The abstract, §1, §4.1 and the Table 8 caption now give 216 cells / 203,400 replicates and say the totals are job accounting that includes the duplicated leakage job. I checked the rebuilt `paper/main.pdf` by text extraction: no "232" or "219,400" remains in the claims. The PDF is rebuilt from the changed sources.
2. **Acquisition and environment.** `REPRODUCE.md` now has the download commands (pinned MMLU-Pro revision, Qwen GGUF repo, file name and sha256), `code/requirements-lock.txt`, and a measured runtime per command.
3. **README.** It now lists the deliverables, how to rebuild the paper, and what was not done.
4. **Minor figure and table polish (Table 10 headers, Fig. 2(d) annotation).** These were not blocking and are not required for approval.

## Re-inspected
- The `hutian/delivery` status is success on the head.
- The diff from e1ed40a touches only the README, `REPRODUCE.md`, the lock file, four paper sections and the PDF.
- The main text still ends on page 8 (limit 9).
- Figures and tables are unchanged since I viewed them.

## Conclusion
This version meets my commitment (#2). The real-LLM evidence and the replay-only search remain narrow, and the paper states that in the abstract and Limitations.
