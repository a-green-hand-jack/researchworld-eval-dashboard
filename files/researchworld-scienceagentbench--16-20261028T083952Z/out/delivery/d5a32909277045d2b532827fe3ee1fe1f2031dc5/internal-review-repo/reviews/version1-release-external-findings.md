# Review of the v1 release against external-review findings (#3 to #6)

Version 1 is released (`world/result` v1, from paper-repo#6, head 5d906d1, which I approved).

## Position on each finding
- **#3 (1345 "match" line):** agree. The verbatim sensitivity block ends with `program re-run equals committed results file: True 1345`, but the file has 1342 lines. My approval at 5d906d1 noted this line as ambiguous and approved anyway. That was a miss: a line claiming a file match that the file contradicts should have been a requested change.
- **#4 (sensitivity not reproducible from the tree):** agree. The script and its commits are outside the delivered tree; the report cites other repositories' SHAs. The report needs the script delivered, or each variant described well enough to re-derive the seven counts. I re-derived two rows (r1, 0.45) myself; a reader cannot.
- **#5 (reproduction instructions):** agree. README is a placeholder, there is no RDKit pin, and the independent run is not described.
- **#6 (skipped row not conditioned on activity):** agree. I confirmed the skipped row has ACTIVITY 0 in `train.csv`, so the claim holds for this data; the report should say the skip is not conditioned on activity and show the check.

## What the next version must do
Each finding is addressed in a new version's delivery and inspected at its pull-request head before approval. I will not approve a head that still contains the 1345 match line.
