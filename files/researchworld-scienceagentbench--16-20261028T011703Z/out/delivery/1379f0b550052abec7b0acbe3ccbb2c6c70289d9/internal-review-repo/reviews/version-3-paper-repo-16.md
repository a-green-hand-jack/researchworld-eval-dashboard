# Review record: version 3 (paper-repo pull request #16)

- Head inspected: `eea3047` (`main` after PR #15, merged from `report-v3`).
- Inspected: `REPORT.md`, `analysis/counts.py`, `analysis/run.log`, `analysis/requirements.txt`, the program, the output.

## Checks

- Program and output are unchanged from version 2 (program sha256 `a9da811e…`, identical to `8a42fa5`).
- `analysis/counts.py` rerun on the frozen inputs (RDKit 2026.09.1, pinned in `requirements.txt`) reproduces `analysis/run.log` line for line. The main counts, the reconciled Brenk figures (PAINS 121, Brenk 1395, both 80, union 1436, after PAINS 3520, after PAINS and Brenk 2205) and the duplicate counts (7 repeated, 8 surplus, 1345 raw / 1342 distinct raw / 1337 canonical) all match the report.
- Question, claim, significance, output rule and limitations are stated in the report, and the process references are removed.

## Finding (open, requests changes)

The sensitivity section misstates its own results.

1. The range sentence says "kept rows range from 1194 to 1705 (−11% to +27%)". The table in the report gives 1194 to 1603. 1705 is not in the report's table at all, and the "−11% to +27%" follows from that wrong range.
2. The table omits four settings that `analysis/counts.py` computes (`analysis/run.log`): radius 1 at threshold 0.4 (749 / 747), radius 1 at threshold 0.6 (1379 / 1371), radius 3 at threshold 0.4 (1300 / 1294), and radius 3 at threshold 0.6 (1705 / 1686).
3. Over all the settings `counts.py` runs, the kept rows range from 749 to 1705, which is −44% to +27% of the stated 1345. The largest drop is the threshold 0.4 at radius 1 (−44%), not the radius 1 at 0.5 (−11%) the report calls largest.

Fix: list every setting `counts.py` runs in the table, state the range from that table (749 to 1705 kept rows, −44% to +27%), and rewrite the sentence on the largest single moves to match. The stated criteria are not the middle of the range, as the report already says; that conclusion stands.

## Not checkable from this position

- Nothing else. The counts, the run log and the program all reproduced.
