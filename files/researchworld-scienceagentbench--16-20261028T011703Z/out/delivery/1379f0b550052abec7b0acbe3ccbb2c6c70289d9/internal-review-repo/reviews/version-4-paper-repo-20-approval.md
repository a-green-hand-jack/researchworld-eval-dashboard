# Review record: version 4 approved (paper-repo pull request #20, head baf0688)

- Inspected at `baf0688`: `REPORT.md`, `analysis/counts.py`, `analysis/run.log`, `analysis/merged_pairs.tsv`, `analysis/requirements.txt`, and the program and output (both unchanged from version 3).
- Program sha256 `a9da811e…`, output sha256 `91c8c07e…` (1337 lines), `analysis/counts.py` sha256 `1478df65…`, `analysis/requirements.txt` sha256 `77ab7d35…`.
- `analysis/counts.py` on the frozen inputs reproduces the counts-script section of `analysis/run.log`, including the sensitivity table and the merged-pair list.
- The program section of `analysis/run.log` records the exact command and writes to the delivered path, with the output sha256 `91c8c07e…`. I reran the program to a scratch path and got the same bytes.
- Independently verified: 138 of the 1345 kept rows have an inactive at Tanimoto 0.5 or more, and dropping them leaves 1207 rows.
- `analysis/merged_pairs.tsv` lists four canonical groups (9 raw strings) that account for the 5 merged rows; the cause in the report (bond form, hydrogen notation, atom order) matches the pairs.
- The significance claim is reworded to what the report establishes, with no unsourced practice claim.
- Conclusion: approved.
